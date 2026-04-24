def test_get_vendors_returns_list(client):
    resp = client.get("/api/v1/vendors")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)



