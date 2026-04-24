import pytest
import unittest.mock as mock
import requests

def test_order_missing_manifest(client):
    resp = client.post("/api/v1/orders", json={})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "manifest is required" in data["error"]["message"]

@mock.patch("routes.orders.requests.get")
def test_order_agnet_unreachable(mock_get, client):
    # Simulate AgNet being down during inventory check
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection Refused")
    
    payload = {
        "manifest": [
            {"productId": "PROD-1", "quantity": 10}
        ]
    }
    resp = client.post("/api/v1/orders", json=payload)
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "AGNET_UNREACHABLE"

@mock.patch("routes.orders.requests.get")
def test_order_insufficient_stock(mock_get, client):
    # Mock inventory check to return nothing available externally
    mock_response = mock.Mock()
    mock_response.json.return_value = {"items": []}
    mock_response.raise_for_status = mock.Mock()
    mock_get.return_value = mock_response

    payload = {
        "manifest": [
            {"productId": "NONEXISTENT-PROD", "quantity": 9999}
        ]
    }
    
    # We expect 400 insufficient stock since neither local nor AgNet has this much
    resp = client.post("/api/v1/orders", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "INSUFFICIENT_STOCK"
    assert len(data["error"]["details"]) > 0
    assert data["error"]["details"][0]["productId"] == "NONEXISTENT-PROD"

@mock.patch("routes.orders.requests.post")
@mock.patch("routes.orders.requests.get")
def test_order_successful_fulfillment(mock_get, mock_post, client):
    # Mock external inventory showing sufficient stock
    mock_get_resp = mock.Mock()
    mock_get_resp.json.return_value = {
        "items": [
            {
                "vendorId": "EXT-VEND-1",
                "regState": "Active",
                "availableManifest": [
                    {
                        "productId": "COMMON-PROD",
                        "quantityAvailable": 100,
                        "unit": "kg"
                    }
                ]
            }
        ]
    }
    mock_get_resp.raise_for_status = mock.Mock()
    mock_get.return_value = mock_get_resp

    # Mock external order submission success
    mock_post_resp = mock.Mock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {"orderId": "EXT-ORD-123"}
    mock_post.return_value = mock_post_resp

    payload = {
        "manifest": [
            {"productId": "COMMON-PROD", "quantity": 10}
        ]
    }

    resp = client.post("/api/v1/orders", json=payload)
    
    # Should be successfully accepted
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "accepted"
    assert "order_id" in data
