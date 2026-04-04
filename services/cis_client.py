"""
Client for the CIS (Central Inventory System) third-party API.

CIS manages the pooled inventory for the entire F2F platform.
SNM calls CIS to:
  - register incoming vendor shipments as inventory reservations
  - query current pooled inventory levels
  - query shipment history

Spec reference: CIS API Spec (Draft v0.1)
Section 3 endpoint: http://138.197.144.135:8203/api/v1
"""

import requests
import config

TIMEOUT = 15


def _headers():
    return {"X-API-Key": config.CIS_API_KEY}


def _url(path):
    return f"{config.CIS_BASE_URL}{path}"


# ── Health ────────────────────────────────────────────────────────────────

def health():
    """GET /api/v1/health  (no auth)"""
    resp = requests.get(_url("/health"), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ── Vendor Supply (Reservations) ──────────────────────────────────────────

def register_shipment(shipment_id, vendor_id, shipment_date, items):
    """
    POST /api/v1/vendors/reservations

    Registers incoming vendor shipment and upserts catalog/inventory.

    items: list of {
        "productId": str,
        "hierarchy": [str, str, str],   # 3-level category
        "productName": str,
        "quantity": float,
        "unit": "kg" | "l"
    }
    """
    payload = {
        "shipmentId": shipment_id,
        "vendorId": vendor_id,
        "shipmentDate": shipment_date,
        "items": items,
    }
    resp = requests.post(
        _url("/vendors/reservations"),
        headers=_headers(),
        json=payload,
        timeout=TIMEOUT,
    )
    # 409 = duplicate shipment — not an error per se, return it
    if resp.status_code == 409:
        return {"status": "duplicate", **resp.json()}
    resp.raise_for_status()
    return resp.json()


# ── Inventory queries ─────────────────────────────────────────────────────

def get_vendor_inventory(vendor_id=None, product_id=None,
                         page=1, page_size=100):
    """GET /api/v1/vendors/inventory — section inventory snapshot."""
    params = {"page": page, "pageSize": page_size}
    if vendor_id:
        params["vendorId"] = vendor_id
    if product_id:
        params["productId"] = product_id
    resp = requests.get(
        _url("/vendors/inventory"),
        headers=_headers(),
        params=params,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_pooled_inventory(page=1, page_size=100):
    """GET /api/v1/inventory/pooled — fulfillment inventory totals."""
    params = {"page": page, "pageSize": page_size}
    resp = requests.get(
        _url("/inventory/pooled"),
        headers=_headers(),
        params=params,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_shipment_history(vendor_id=None, page=1, page_size=50):
    """GET /api/v1/vendors/shipments — shipment audit trail."""
    params = {"page": page, "pageSize": page_size}
    if vendor_id:
        params["vendorId"] = vendor_id
    resp = requests.get(
        _url("/vendors/shipments"),
        headers=_headers(),
        params=params,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()
