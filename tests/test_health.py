"""Tests for the /health endpoint."""


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_returns_correct_body(client):
    resp = client.get("/health")
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "supply-network-management"
