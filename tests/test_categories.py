def test_get_categories_returns_list(client):
    resp = client.get("/api/v1/categories")
    assert resp.status_code == 200
    assert "results" in resp.json()

def test_create_category_success(client):
    payload = {
        "category_id": "TEST-CAT-01",
        "category_name": "Test Category",
        "level": 1
    }
    resp = client.post("/api/v1/categories", json=payload)
    assert resp.status_code == 200
    
    # Verify we can fetch it
    resp_get = client.get("/api/v1/categories")
    results = resp_get.json().get("results", [])
    assert any(c["category_id"] == "TEST-CAT-01" for c in results)
