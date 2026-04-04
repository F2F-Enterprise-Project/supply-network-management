"""
Supply & Network Management API routes.

All endpoints under /supply/*.
"""

from flask import Blueprint, jsonify, request
from services import procurement_service, agnet_client, cis_client

supply_bp = Blueprint("supply", __name__, url_prefix="/supply")


# ── Vendors ───────────────────────────────────────────────────────────────

@supply_bp.route("/vendors", methods=["GET"])
def list_vendors():
    """Return locally cached vendors.  ?sync=true to pull from AgNet first."""
    if request.args.get("sync", "").lower() == "true":
        try:
            procurement_service.sync_vendors()
        except Exception as exc:
            return jsonify({"error": str(exc)}), 502
    vendors = procurement_service.get_local_vendors()
    return jsonify({"count": len(vendors), "vendors": vendors}), 200


@supply_bp.route("/vendors/sync", methods=["POST"])
def sync_vendors():
    """Force-pull vendor data from AgNet into local DB."""
    try:
        result = procurement_service.sync_vendors()
        return jsonify({"synced": len(result), "vendors": result}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@supply_bp.route("/vendors/<vendor_id>", methods=["GET"])
def get_vendor(vendor_id):
    """Get single vendor — tries local cache, falls back to AgNet live."""
    try:
        data = agnet_client.get_vendor(vendor_id)
        return jsonify(data), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


# ── Catalog ───────────────────────────────────────────────────────────────

@supply_bp.route("/catalog", methods=["GET"])
def list_catalog():
    """Return locally cached products.  ?vendor_id=X to filter."""
    vid = request.args.get("vendor_id")
    products = procurement_service.get_local_products(vendor_id=vid)
    return jsonify({"count": len(products), "products": products}), 200


# ── Orders ────────────────────────────────────────────────────────────────

@supply_bp.route("/orders", methods=["POST"])
def place_order():
    """
    Place a procurement order.

    Body:
    {
      "vendorId": "NORTHFIELD-HARVEST-FARMS",
      "manifest": [
        {"productId": "PROD-CARROTS", "quantityOrder": 12},
        {"productId": "PROD-ONIONS",  "quantityOrder": 4}
      ]
    }
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body required"}), 400

    vendor_id = body.get("vendorId")
    manifest = body.get("manifest")

    if not vendor_id:
        return jsonify({"error": "vendorId is required"}), 400
    if not manifest or not isinstance(manifest, list):
        return jsonify({"error": "manifest must be a non-empty list"}), 400

    for item in manifest:
        if "productId" not in item:
            return jsonify({"error": "Each manifest item needs productId"}), 400
        if "quantityOrder" not in item:
            return jsonify({"error": "Each manifest item needs quantityOrder"}), 400
        if not isinstance(item["quantityOrder"], int) or item["quantityOrder"] <= 0:
            return jsonify({"error": "quantityOrder must be a positive integer"}), 400

    try:
        result = procurement_service.place_order(vendor_id, manifest)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@supply_bp.route("/orders", methods=["GET"])
def list_orders():
    """Return local procurement order history."""
    limit = request.args.get("limit", 50, type=int)
    orders = procurement_service.get_orders(limit=limit)
    return jsonify({"count": len(orders), "orders": orders}), 200


# ── Shipments ─────────────────────────────────────────────────────────────

@supply_bp.route("/shipments", methods=["GET"])
def list_shipments():
    """Return local shipment records."""
    limit = request.args.get("limit", 50, type=int)
    shipments = procurement_service.get_shipments(limit=limit)
    return jsonify({"count": len(shipments), "shipments": shipments}), 200


# ── Inventory (from CIS) ─────────────────────────────────────────────────

@supply_bp.route("/inventory", methods=["GET"])
def get_inventory():
    """Proxy to CIS pooled inventory endpoint."""
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 100, type=int)
    try:
        data = cis_client.get_pooled_inventory(page=page, page_size=page_size)
        return jsonify(data), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


# ── AgNet Dashboard (pass-through) ───────────────────────────────────────

@supply_bp.route("/dashboard", methods=["GET"])
def agnet_dashboard():
    """Proxy to AgNet dashboard summary."""
    try:
        data = agnet_client.get_dashboard()
        return jsonify(data), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502
