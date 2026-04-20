from unittest.mock import patch


def test_retrieve_products_from_snc(client):
    """
    Verifies PII can retrieve a unified list of products from both
    local storage and the AgNet supplier API.
    """

    mock_agnet_data = {
        "items": [{
            "vendorId": "AGNET-VEND-001",
            "vendorName": "External Farm",
            "regState": "Active",
            "availableManifest": [{
                "productId": "EXT-PROD-99",
                "productName": "External Apples",
                "unit": "kg",
                "quantityAvailable": 100
            }]
        }]
    }

    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_agnet_data

        response = client.get("/api/v1/products")

        assert response.status_code == 200
        data = response.json()

        assert "results" in data

        external_item = next(p for p in data["results"] if p["product_id"] == "EXT-PROD-99")
        assert external_item["vendor_id"] == "AGNET-VEND-001"
        assert external_item["unit"] == "kg"
