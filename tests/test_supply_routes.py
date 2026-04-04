"""Tests for /supply/* endpoints."""

from unittest.mock import patch


# ── GET /supply/vendors ───────────────────────────────────────────────────

def test_list_vendors_empty(client):
    resp = client.get("/supply/vendors")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 0
    assert data["vendors"] == []


def test_list_vendors_after_sync(client):
    fake_agnet = [
        {
            "vendorId": "V1",
            "vendorName": "Test Farm",
            "vendorType": "Farm",
            "regState": "Active",
            "orderCount": 0,
            "manifest": [
                {
                    "productId": "PROD-1",
                    "productName": "Carrots",
                    "unit": "kg",
                    "category_l3": "RootVeg",
                },
            ],
        },
    ]
    with patch("services.agnet_client.get_vendors", return_value=fake_agnet):
        resp = client.get("/supply/vendors?sync=true")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 1
    assert data["vendors"][0]["vendor_id"] == "V1"


# ── POST /supply/vendors/sync ─────────────────────────────────────────────

def test_sync_vendors_success(client):
    fake = [
        {
            "vendorId": "V2", "vendorName": "Dairy Co",
            "vendorType": "Dairy", "regState": "New",
            "orderCount": 0, "manifest": [],
        }
    ]
    with patch("services.agnet_client.get_vendors", return_value=fake):
        resp = client.post("/supply/vendors/sync")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["synced"] == 1


def test_sync_vendors_agnet_down(client):
    with patch(
        "services.agnet_client.get_vendors",
        side_effect=Exception("Connection refused"),
    ):
        resp = client.post("/supply/vendors/sync")
    assert resp.status_code == 502


# ── GET /supply/catalog ───────────────────────────────────────────────────

def test_catalog_empty(client):
    resp = client.get("/supply/catalog")
    assert resp.status_code == 200
    assert resp.get_json()["count"] == 0


def test_catalog_after_sync(client):
    fake = [
        {
            "vendorId": "V1", "vendorName": "Farm",
            "vendorType": "Farm", "regState": "Active",
            "orderCount": 0,
            "manifest": [
                {"productId": "P1", "productName": "Apples", "unit": "kg"},
                {"productId": "P2", "productName": "Milk", "unit": "l"},
            ],
        },
    ]
    with patch("services.agnet_client.get_vendors", return_value=fake):
        client.post("/supply/vendors/sync")
    resp = client.get("/supply/catalog")
    assert resp.get_json()["count"] == 2


def test_catalog_filter_by_vendor(client):
    fake = [
        {
            "vendorId": "V1", "vendorName": "Farm",
            "vendorType": "Farm", "regState": "Active",
            "orderCount": 0,
            "manifest": [{"productId": "P1", "productName": "A", "unit": "kg"}],
        },
        {
            "vendorId": "V2", "vendorName": "Dairy",
            "vendorType": "Dairy", "regState": "Active",
            "orderCount": 0,
            "manifest": [{"productId": "P2", "productName": "B", "unit": "l"}],
        },
    ]
    with patch("services.agnet_client.get_vendors", return_value=fake):
        client.post("/supply/vendors/sync")
    resp = client.get("/supply/catalog?vendor_id=V1")
    assert resp.get_json()["count"] == 1


# ── POST /supply/orders ───────────────────────────────────────────────────

def test_place_order_missing_body(client):
    resp = client.post("/supply/orders")
    assert resp.status_code == 400


def test_place_order_missing_vendor(client):
    resp = client.post("/supply/orders", json={"manifest": []})
    assert resp.status_code == 400
    assert "vendorId" in resp.get_json()["error"]


def test_place_order_empty_manifest(client):
    resp = client.post("/supply/orders", json={"vendorId": "V1", "manifest": []})
    assert resp.status_code == 400


def test_place_order_bad_quantity(client):
    resp = client.post("/supply/orders", json={
        "vendorId": "V1",
        "manifest": [{"productId": "P1", "quantityOrder": -1}],
    })
    assert resp.status_code == 400


def test_place_order_missing_product_id(client):
    resp = client.post("/supply/orders", json={
        "vendorId": "V1",
        "manifest": [{"quantityOrder": 5}],
    })
    assert resp.status_code == 400


def test_place_order_success(client):
    agnet_resp = {
        "status": "accepted",
        "orderId": "ORD-123",
        "vendorId": "V1",
        "orderCount": 1,
    }
    cis_resp = {"status": "accepted", "vendorId": "V1", "inventoryItemsUpdated": 1}

    with patch("services.agnet_client.place_order", return_value=agnet_resp), \
         patch("services.cis_client.register_shipment", return_value=cis_resp):
        resp = client.post("/supply/orders", json={
            "vendorId": "V1",
            "manifest": [{"productId": "PROD-1", "quantityOrder": 10}],
        })

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["agnet_status"] == "accepted"
    assert data["cis_result"]["status"] == "accepted"


def test_place_order_agnet_rejected(client):
    agnet_resp = {"status": "rejected", "orderId": "ORD-X"}
    with patch("services.agnet_client.place_order", return_value=agnet_resp):
        resp = client.post("/supply/orders", json={
            "vendorId": "V1",
            "manifest": [{"productId": "P1", "quantityOrder": 5}],
        })
    data = resp.get_json()
    assert data["agnet_status"] == "rejected"
    assert data["cis_result"] is None


def test_place_order_agnet_down(client):
    with patch(
        "services.agnet_client.place_order",
        side_effect=Exception("timeout"),
    ):
        resp = client.post("/supply/orders", json={
            "vendorId": "V1",
            "manifest": [{"productId": "P1", "quantityOrder": 5}],
        })
    assert resp.status_code == 502


# ── GET /supply/orders ────────────────────────────────────────────────────

def test_list_orders_empty(client):
    resp = client.get("/supply/orders")
    assert resp.status_code == 200
    assert resp.get_json()["count"] == 0


def test_list_orders_after_placing(client):
    agnet_resp = {"status": "accepted", "orderId": "ORD-1"}
    cis_resp = {"status": "accepted", "inventoryItemsUpdated": 1}
    with patch("services.agnet_client.place_order", return_value=agnet_resp), \
         patch("services.cis_client.register_shipment", return_value=cis_resp):
        client.post("/supply/orders", json={
            "vendorId": "V1",
            "manifest": [{"productId": "P1", "quantityOrder": 5}],
        })
    resp = client.get("/supply/orders")
    assert resp.get_json()["count"] == 1


# ── GET /supply/shipments ─────────────────────────────────────────────────

def test_list_shipments_empty(client):
    resp = client.get("/supply/shipments")
    assert resp.status_code == 200
    assert resp.get_json()["count"] == 0


def test_list_shipments_after_order(client):
    agnet_resp = {"status": "accepted", "orderId": "ORD-2"}
    cis_resp = {"status": "accepted", "inventoryItemsUpdated": 1}
    with patch("services.agnet_client.place_order", return_value=agnet_resp), \
         patch("services.cis_client.register_shipment", return_value=cis_resp):
        client.post("/supply/orders", json={
            "vendorId": "V1",
            "manifest": [{"productId": "P1", "quantityOrder": 5}],
        })
    resp = client.get("/supply/shipments")
    assert resp.get_json()["count"] == 1


# ── GET /supply/inventory ─────────────────────────────────────────────────

def test_inventory_proxies_to_cis(client):
    fake = {"page": 1, "pageSize": 100, "total": 2, "hasNext": False, "items": []}
    with patch("services.cis_client.get_pooled_inventory", return_value=fake):
        resp = client.get("/supply/inventory")
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 2


def test_inventory_cis_down(client):
    with patch(
        "services.cis_client.get_pooled_inventory",
        side_effect=Exception("refused"),
    ):
        resp = client.get("/supply/inventory")
    assert resp.status_code == 502


# ── GET /supply/dashboard ─────────────────────────────────────────────────

def test_dashboard_proxies_to_agnet(client):
    fake = {"totalVendors": 5}
    with patch("services.agnet_client.get_dashboard", return_value=fake):
        resp = client.get("/supply/dashboard")
    assert resp.status_code == 200
    assert resp.get_json()["totalVendors"] == 5


def test_dashboard_agnet_down(client):
    with patch(
        "services.agnet_client.get_dashboard",
        side_effect=Exception("down"),
    ):
        resp = client.get("/supply/dashboard")
    assert resp.status_code == 502
