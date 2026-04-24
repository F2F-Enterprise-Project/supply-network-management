import unittest.mock as mock

def test_get_products_returns_list(client):
    # Mocking the external AgNet call
    with mock.patch("routes.products.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "vendorId": "AGNET-V-1",
                    "availableManifest": [
                        {
                            "productId": "AGNET-P-1",
                            "productName": "External Apple",
                            "unit": "kg"
                        }
                    ]
                }
            ]
        }
        mock_response.raise_for_status = mock.Mock()
        mock_get.return_value = mock_response

        resp = client.get("/api/v1/products")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "results" in data
        
        # Verify that the mocked external product is present
        results = data["results"]
        assert any(p["product_id"] == "AGNET-P-1" for p in results)
