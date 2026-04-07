def test_health_returns_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "supplynetwork"
    assert data["section"] == "Section 3"
    assert "timeUtc" in data


def test_version_returns_version(client):
    resp = client.get("/api/v1/version")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert "timeUtc" in data


def test_openapi_schema(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["openapi"] == "3.1.0"
    assert "paths" in data


def test_swagger_docs(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert b"swagger" in resp.content.lower()
