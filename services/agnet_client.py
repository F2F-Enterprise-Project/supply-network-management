"""
Client for the AgNet third-party API.

AgNet is the vendor/supplier network.  We use it to:
  - browse available vendors and their product manifests
  - place procurement orders against a vendor
  - view order logs and dashboard summaries

Spec reference: AgNet API Spec (Draft v0.1)
Section 3 endpoint: http://146.190.243.241:8303/api/v1
"""

import requests
import config

TIMEOUT = 15  # seconds


def _headers():
    return {"X-API-Key": config.AGNET_API_KEY}


def _url(path):
    return f"{config.AGNET_BASE_URL}{path}"


# ── Health ────────────────────────────────────────────────────────────────

def health():
    """GET /api/v1/health  (no auth)"""
    resp = requests.get(_url("/health"), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ── Vendors ───────────────────────────────────────────────────────────────

def get_vendors(include_inactive=True):
    """GET /api/v1/vendors — returns all vendors with manifests."""
    params = {"includeInactive": str(include_inactive).lower()}
    resp = requests.get(
        _url("/vendors"),
        headers=_headers(),
        params=params,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_vendor(vendor_id):
    """GET /api/v1/vendors/{vendorId} — single vendor snapshot."""
    resp = requests.get(
        _url(f"/vendors/{vendor_id}"),
        headers=_headers(),
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


# ── Orders ────────────────────────────────────────────────────────────────

def place_order(vendor_id, manifest):
    """
    POST /api/v1/orders — submit order against a single vendor.

    manifest: list of {"productId": str, "quantityOrder": int}
    Returns the AgNet response dict on success, raises on failure.
    """
    payload = {"vendorId": vendor_id, "manifest": manifest}
    resp = requests.post(
        _url("/orders"),
        headers=_headers(),
        json=payload,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


# ── Logs / Dashboard ─────────────────────────────────────────────────────

def get_order_logs():
    """GET /api/v1/logs/orders — accepted and rejected order records."""
    resp = requests.get(
        _url("/logs/orders"),
        headers=_headers(),
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_dashboard():
    """GET /api/v1/dashboard/summary — section dashboard (no auth)."""
    resp = requests.get(_url("/dashboard/summary"), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()
