"""Tests for the AgNet API client (all HTTP calls mocked)."""

import pytest
import requests
from unittest.mock import patch, MagicMock
from services import agnet_client


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
    payload = {"status": "ok", "service": "agnet", "section": "Section 3"}
    with patch("requests.get", return_value=_mock_response(payload)):
        result = agnet_client.health()
    assert result["status"] == "ok"


# ── get_vendors ───────────────────────────────────────────────────────────

def test_get_vendors_returns_list():
    payload = [{"vendorId": "V1", "vendorName": "Farm", "manifest": []}]
    with patch("requests.get", return_value=_mock_response(payload)):
        result = agnet_client.get_vendors()
    assert isinstance(result, list)
    assert result[0]["vendorId"] == "V1"


def test_get_vendors_passes_include_inactive():
    with patch("requests.get", return_value=_mock_response([])) as mock_get:
        agnet_client.get_vendors(include_inactive=False)
    call_kwargs = mock_get.call_args
    assert call_kwargs.kwargs["params"]["includeInactive"] == "false"


def test_get_vendors_raises_on_http_error():
    with patch("requests.get", return_value=_mock_response({}, 403)):
        with pytest.raises(requests.HTTPError):
            agnet_client.get_vendors()


# ── get_vendor ────────────────────────────────────────────────────────────

def test_get_vendor_single():
    payload = {"vendorId": "V1", "vendorName": "Farm", "manifest": []}
    with patch("requests.get", return_value=_mock_response(payload)):
        result = agnet_client.get_vendor("V1")
    assert result["vendorId"] == "V1"


# ── place_order ───────────────────────────────────────────────────────────

def test_place_order_accepted():
    payload = {
        "status": "accepted",
        "orderId": "ORD-001",
        "vendorId": "V1",
        "orderCount": 1,
    }
    manifest = [{"productId": "P1", "quantityOrder": 5}]
    with patch("requests.post", return_value=_mock_response(payload)):
        result = agnet_client.place_order("V1", manifest)
    assert result["status"] == "accepted"
    assert result["orderId"] == "ORD-001"


def test_place_order_sends_correct_payload():
    mock_resp = _mock_response({"status": "accepted"})
    manifest = [{"productId": "P1", "quantityOrder": 3}]
    with patch("requests.post", return_value=mock_resp) as mock_post:
        agnet_client.place_order("VEND-1", manifest)
    body = mock_post.call_args.kwargs["json"]
    assert body["vendorId"] == "VEND-1"
    assert body["manifest"] == manifest


def test_place_order_raises_on_400():
    with patch("requests.post", return_value=_mock_response({}, 400)):
        with pytest.raises(requests.HTTPError):
            agnet_client.place_order("V1", [{"productId": "P1", "quantityOrder": 1}])


# ── get_order_logs ────────────────────────────────────────────────────────

def test_get_order_logs():
    payload = {"orders": []}
    with patch("requests.get", return_value=_mock_response(payload)):
        result = agnet_client.get_order_logs()
    assert "orders" in result


# ── get_dashboard ─────────────────────────────────────────────────────────

def test_get_dashboard():
    payload = {"totalVendors": 7, "recentOrders": []}
    with patch("requests.get", return_value=_mock_response(payload)):
        result = agnet_client.get_dashboard()
    assert result["totalVendors"] == 7
