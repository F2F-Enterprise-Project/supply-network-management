"""
Procurement business logic.

Orchestrates the full flow:
  1.  Browse AgNet vendors
  2.  Place order on AgNet
  3.  Build a CIS shipment reservation from the AgNet confirmation
  4.  Register the reservation with CIS
  5.  Persist everything locally
"""

import json
import uuid
from datetime import datetime, timezone

from repository import db
from services import agnet_client, cis_client


# ── Vendor sync ───────────────────────────────────────────────────────────

def sync_vendors():
    """Pull the full vendor list from AgNet and cache locally."""
    vendors_data = agnet_client.get_vendors(include_inactive=True)

    # AgNet may return a list or a wrapper — normalise
    vendors = vendors_data if isinstance(vendors_data, list) else vendors_data.get("vendors", vendors_data.get("items", []))

    conn = db.get_connection()
    cur = conn.cursor()
    saved = []

    for v in vendors:
        vid = v.get("vendorId") or v.get("vendor_id", "")
        name = v.get("vendorName") or v.get("vendor_name") or v.get("name", "")
        vtype = v.get("vendorType") or v.get("vendor_type") or v.get("type", "")
        state = v.get("regState") or v.get("reg_state", "New")
        count = v.get("orderCount") or v.get("order_count", 0)

        cur.execute(
            """INSERT OR REPLACE INTO vendors
               (vendor_id, name, type, reg_state, order_count, updated_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'))""",
            (vid, name, vtype, state, count),
        )

        # Sync manifest items as products
        manifest = v.get("manifest", [])
        for item in manifest:
            pid = item.get("productId") or item.get("product_id", "")
            pname = item.get("productName") or item.get("product_name", "")
            unit = item.get("unit", "kg")
            cat_l3 = ""
            if "category_l3" in item:
                cat_l3 = item["category_l3"]
            elif "categoryL3" in item:
                cat_l3 = item["categoryL3"]
            cur.execute(
                """INSERT OR REPLACE INTO products
                   (product_id, vendor_id, category_id, product_name, unit, updated_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                (pid, vid, cat_l3, pname, unit),
            )

        saved.append({
            "vendor_id": vid, "name": name,
            "type": vtype, "reg_state": state,
            "manifest_items": len(manifest),
        })

    conn.commit()
    return saved


# ── Place procurement order ───────────────────────────────────────────────

def place_order(vendor_id, manifest):
    """
    Full procurement flow:
      1. POST order to AgNet
      2. On success, build CIS reservation
      3. POST reservation to CIS
      4. Store everything locally

    manifest: [{"productId": str, "quantityOrder": int}, ...]

    Returns dict with status and details.
    """
    # Step 1 — AgNet order
    agnet_resp = agnet_client.place_order(vendor_id, manifest)

    order_id = str(uuid.uuid4())
    agnet_order_id = agnet_resp.get("orderId", "")
    status = agnet_resp.get("status", "unknown")

    # Persist the order locally
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO procurement_orders
           (order_id, vendor_id, agnet_order_id, status, total_items, payload_json, result_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            order_id, vendor_id, agnet_order_id, status,
            len(manifest),
            json.dumps({"vendorId": vendor_id, "manifest": manifest}),
            json.dumps(agnet_resp),
        ),
    )

    for item in manifest:
        cur.execute(
            """INSERT INTO order_items
               (item_id, order_id, product_id, quantity_ordered, unit)
               VALUES (?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()), order_id,
                item["productId"], item["quantityOrder"],
                item.get("unit", "kg"),
            ),
        )
    conn.commit()

    # Step 2 — forward to CIS if AgNet accepted
    cis_result = None
    if status == "accepted":
        cis_result = _forward_to_cis(vendor_id, manifest)

    return {
        "order_id": order_id,
        "agnet_order_id": agnet_order_id,
        "agnet_status": status,
        "cis_result": cis_result,
    }


def _forward_to_cis(vendor_id, manifest):
    """Build a CIS reservation payload from the AgNet order and register it."""
    now = datetime.now(timezone.utc).isoformat()
    shipment_id = f"SHIP-SNM-{uuid.uuid4().hex[:8].upper()}"

    # Map AgNet manifest items → CIS reservation items
    # CIS needs: productId, hierarchy (3 strings), productName, quantity, unit
    # We look up product details from local DB to fill hierarchy/name
    conn = db.get_connection()
    cur = conn.cursor()

    cis_items = []
    for item in manifest:
        pid = item["productId"]
        qty = item["quantityOrder"]

        # Try to find product locally for metadata
        row = cur.execute(
            "SELECT product_name, unit, category_id FROM products WHERE product_id = ?",
            (pid,),
        ).fetchone()

        pname = row["product_name"] if row else pid
        unit = row["unit"] if row else item.get("unit", "kg")
        cat = row["category_id"] if row else ""

        cis_items.append({
            "productId": pid,
            "hierarchy": [cat, cat, cat] if cat else ["General", "General", pid],
            "productName": pname,
            "quantity": float(qty),
            "unit": unit,
        })

    cis_resp = cis_client.register_shipment(
        shipment_id=shipment_id,
        vendor_id=vendor_id,
        shipment_date=now,
        items=cis_items,
    )

    # Store shipment locally
    cis_status = cis_resp.get("status", "unknown")
    cur.execute(
        """INSERT OR IGNORE INTO shipments
           (shipment_id, vendor_id, shipment_date, cis_status)
           VALUES (?, ?, ?, ?)""",
        (shipment_id, vendor_id, now, cis_status),
    )
    conn.commit()

    return {"shipment_id": shipment_id, **cis_resp}


# ── Query helpers ─────────────────────────────────────────────────────────

def get_local_vendors():
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM vendors ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def get_local_products(vendor_id=None):
    conn = db.get_connection()
    if vendor_id:
        rows = conn.execute(
            "SELECT * FROM products WHERE vendor_id = ? ORDER BY product_name",
            (vendor_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM products ORDER BY product_name"
        ).fetchall()
    return [dict(r) for r in rows]


def get_orders(limit=50):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM procurement_orders ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_shipments(limit=50):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM shipments ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
