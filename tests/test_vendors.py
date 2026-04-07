def test_get_vendors_returns_list(client):
    resp = client.get("/api/v1/vendors")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_categories_returns_list(client):
    resp = client.get("/api/v1/categories")
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_get_products_returns_list(client):
    resp = client.get("/api/v1/products")
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_get_shipments_returns_list(client):
    resp = client.get("/api/v1/shipments")
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_get_shipment_lots_returns_list(client):
    resp = client.get("/api/v1/shipment-lots")
    assert resp.status_code == 200
    assert "results" in resp.json()
