"""Tests for the CIS API client (all HTTP calls mocked)."""

import pytest
import requests
from unittest.mock import patch, MagicMock
from services import cis_client


def _mock_response(json_data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    if status_code >= 400:
        mock.raise_for_status.side_effect = requests.HTTPError(response=mock)
    return mock


# ── health ────────────────────────────────────────────────────────────────

def test_health_ok():
    payload = {"status": "ok", "service": "cis", "section": "Section 3"}
    with patch("requests.get", return_value=_mock_response(payload)):
        result = cis_client.health()
    assert result["status"] == "ok"


# ── register_shipment ─────────────────────────────────────────────────────

def test_register_shipment_accepted():
    payload = {"status": "accepted", "vendorId": "V1", "inventoryItemsUpdated": 2}
    items = [
        {
            "productId": "P1",
            "hierarchy": ["Produce", "Fruit", "Apples"],
            "productName": "Apples",
            "quantity": 50.0,
            "unit": "kg",
        }
    ]
    with patch("requests.post", return_value=_mock_response(payload)):
        result = cis_client.register_shipment("SHIP-001", "V1", "2026-04-04T00:00:00Z", items)
    assert result["status"] == "accepted"
    assert result["inventoryItemsUpdated"] == 2


def test_register_shipment_sends_correct_payload():
    mock_resp = _mock_response({"status": "accepted", "inventoryItemsUpdated": 1})
    items = [{"productId": "P1", "hierarchy": ["A", "B", "C"],
               "productName": "Test", "quantity": 10.0, "unit": "kg"}]
    with patch("requests.post", return_value=mock_resp) as mock_post:
        cis_client.register_shipment("SHIP-X", "VEND-1", "2026-04-04T00:00:00Z", items)
    body = mock_post.call_args.kwargs["json"]
    assert body["shipmentId"] == "SHIP-X"
    assert body["vendorId"] == "VEND-1"
    assert len(body["items"]) == 1


def test_register_shipment_duplicate_409():
    payload = {"error": {"code": "DUPLICATE_SHIPMENT", "message": "Already processed"}}
    with patch("requests.post", return_value=_mock_response(payload, 409)):
        result = cis_client.register_shipment("SHIP-DUP", "V1", "2026-04-04T00:00:00Z", [])
    assert result["status"] == "duplicate"


def test_register_shipment_raises_on_500():
    with patch("requests.post", return_value=_mock_response({}, 500)):
        with pytest.raises(requests.HTTPError):
            cis_client.register_shipment("SHIP-X", "V1", "2026-04-04T00:00:00Z", [])


# ── get_vendor_inventory ──────────────────────────────────────────────────

def test_get_vendor_inventory():
    payload = {"page": 1, "pageSize": 100, "total": 1, "hasNext": False, "items": [
        {"productId": "P1", "quantityOnHand": 100.0, "unit": "kg"}
    ]}
    with patch("requests.get", return_value=_mock_response(payload)):
        result = cis_client.get_vendor_inventory()
    assert result["total"] == 1
    assert result["items"][0]["productId"] == "P1"


def test_get_vendor_inventory_with_filters():
    mock_resp = _mock_response({"page": 1, "pageSize": 100, "total": 0,
                                 "hasNext": False, "items": []})
    with patch("requests.get", return_value=mock_resp) as mock_get:
        cis_client.get_vendor_inventory(vendor_id="V1", product_id="P1")
    params = mock_get.call_args.kwargs["params"]
    assert params["vendorId"] == "V1"
    assert params["productId"] == "P1"


# ── get_pooled_inventory ──────────────────────────────────────────────────

def test_get_pooled_inventory():
    payload = {"page": 1, "pageSize": 100, "total": 3, "hasNext": False, "items": []}
    with patch("requests.get", return_value=_mock_response(payload)):
        result = cis_client.get_pooled_inventory()
    assert result["total"] == 3


def test_get_pooled_inventory_raises_on_401():
    with patch("requests.get", return_value=_mock_response({}, 401)):
        with pytest.raises(requests.HTTPError):
            cis_client.get_pooled_inventory()


# ── get_shipment_history ──────────────────────────────────────────────────

def test_get_shipment_history():
    payload = {"page": 1, "pageSize": 50, "total": 0, "hasNext": False, "items": []}
    with patch("requests.get", return_value=_mock_response(payload)):
        result = cis_client.get_shipment_history()
    assert result["total"] == 0


def test_get_shipment_history_with_vendor_filter():
    mock_resp = _mock_response({"page": 1, "pageSize": 50,
                                 "total": 0, "hasNext": False, "items": []})
    with patch("requests.get", return_value=mock_resp) as mock_get:
        cis_client.get_shipment_history(vendor_id="V1")
    params = mock_get.call_args.kwargs["params"]
    assert params["vendorId"] == "V1"
