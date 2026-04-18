# routes/products.py
import os
import requests
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from lightapi import RestEndpoint, Field

from config import engine, agnet_base_url


class Product(RestEndpoint):
    product_id: str = Field(primary_key=True)
    vendor_id: str = Field(foreign_key="vendors.vendor_id")
    category_id: str = Field(foreign_key="categorys.category_id")
    product_name: str = Field(max_length=100)
    unit: str = Field()
    # added to match the products from agnet
    quantity_available: int = Field(default=0)

    def queryset(self, request):
        return select(Product)

    def list(self, request):
        with Session(engine) as session:
            qs = self.queryset(request)
            local_products = list(session.execute(qs).scalars().all())

        agnet_url = f"{agnet_base_url}/vendors"
        api_key = os.getenv("AGNET_SECTION_KEY")

        external_products = []
        try:
            response = requests.get(
                agnet_url,
                headers={"X-API-Key": api_key},
                timeout=5
            )
            response.raise_for_status()
            external_data = response.json()

            for vendor in external_data.get("items", []):
                for item in vendor.get("availableManifest", []):
                    external_products.append(Product(
                        product_id=item.get("productId"),
                        vendor_id=vendor.get("vendorId"),
                        category_id=None,
                        product_name=item.get("productName"),
                        unit=item.get("unit"),
                    ))

        except Exception as e:
            print(f"AgNet Integration Error: {e}")

        combined_list = local_products + external_products

        data = []
        for p in combined_list:
            data.append({
                "product_id": p.product_id,
                "vendor_id": p.vendor_id,
                "product_name": p.product_name,
                "unit": p.unit,
            })

        return JSONResponse({"results": data})

    class Meta:
        table_name = "products"
        endpoint = "/api/v1/products"
