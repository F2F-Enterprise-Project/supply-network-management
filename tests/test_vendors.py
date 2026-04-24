import unittest.mock as mock

def test_get_vendors_with_mock(client):
    with mock.patch("routes.vendors.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "vendorId": "EXT-VEND-1",
                    "vendorName": "External Vendor 1",
                    "vendorType": "Farm",
                    "regState": "Active",
                    "orderCount": 5,
                    "lastOrder": "2023-10-10T10:00:00Z"
                }
            ]
        }
        mock_response.raise_for_status = mock.Mock()
        mock_get.return_value = mock_response

        resp = client.get("/api/v1/vendors")
        assert resp.status_code == 200
        
        data = resp.json()
        assert isinstance(data, list)
        assert any(v["vendor_id"] == "EXT-VEND-1" for v in data)

def test_create_vendor_success(client):
    payload = {
        "vendor_id": "LOCAL-VEND-1",
        "name": "Local Vendor",
        "type": "Distributor",
        "reg_state": "Active"
    }
    resp = client.post("/api/v1/vendors", json=payload)
    assert resp.status_code == 200

def test_create_vendor_integrity_error(client):
    payload = {
        "vendor_id": "LOCAL-VEND-DUP",
        "name": "Duplicate Vendor",
        "type": "Distributor",
        "reg_state": "Active"
    }
    # Create first time
    resp1 = client.post("/api/v1/vendors", json=payload)
    assert resp1.status_code == 200
    
    # Create second time with same ID
    resp2 = client.post("/api/v1/vendors", json=payload)
    assert resp2.status_code == 400
    assert "error" in resp2.json()
