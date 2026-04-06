import uuid
import os
import requests
from DatabaseHandler import DatabaseHandler
from starlette.responses import JSONResponse
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from lightapi import LightApi, RestEndpoint, Field, HttpMethod
from datetime import datetime, UTC

engine = create_engine("sqlite:///supplynetwork.db", connect_args={"check_same_thread": False})

is_agnet_up = False
agnet_base_url = "http://146.190.243.241:8303/api/v1"
version = "0.2.1"


class Vendor(RestEndpoint):
    """
    Vendor model that is also:
    - SQLAlchemy table
    - Pydantic schema
    - REST endpoint
    """
    vendor_id: str = Field(primary_key=True, index=True)
    name: str = Field(max_length=100)
    type: str = Field(max_length=100)
    reg_state: str = Field(max_length=100)
    order_count: int = Field(default=0)
    last_order: datetime = Field(default_factory=datetime.now)

    def queryset(self, request):
        return select(Vendor)

    def list(self, request):
        with Session(engine) as session:
            qs = self.queryset(request)
            local_vendors = list(session.execute(qs).scalars().all())

        agnet_url = f"{agnet_base_url}/vendors"
        api_key = os.getenv("AGNET_SECTION_KEY")

        external_vendors = []
        try:
            if is_agnet_up:
                response = requests.get(
                    agnet_url,
                    headers={"X-API-Key": api_key},
                    timeout=5
                )
                response.raise_for_status()
                external_data = response.json()

                for item in external_data.get("items", []):
                    external_vendors.append(Vendor(
                        vendor_id=item.get("vendorId"),
                        name=item.get("vendorName"),
                        type=item.get("vendorType"),
                        reg_state=item.get("regState"),
                        order_count=item.get("orderCount", 0),
                        last_order=item.get("lastOrder")
                    ))
        except Exception as e:

            print(f"AgNet Integration Error: {e}")

        combined_list = local_vendors + external_vendors

        data = []
        for v in combined_list:
            last_order_val = v.last_order
            if hasattr(last_order_val, 'isoformat'):
                last_order_val = last_order_val.isoformat()

            data.append({
                "vendor_id": v.vendor_id,
                "name": v.name,
                "type": v.type,
                "reg_state": v.reg_state,
                "order_count": v.order_count,
                "last_order": last_order_val
            })

        return JSONResponse(data)

    class Meta:
        table_name = "vendors"
        endpoint = "/api/v1/vendors"


class Category(RestEndpoint):
    category_id: str = Field(primary_key=True)
    parent_category_id: str = Field(foreign_key="categories.category_id", nullable=True)
    category_name: str = Field(max_length=100)
    level: int = Field()

    class Meta:
        table_name = "categories"
        endpoint = "/api/v1/categories"


class Product(RestEndpoint):
    product_id: str = Field(primary_key=True)
    vendor_id: str = Field(foreign_key="vendors.vendor_id")
    category_id: str = Field(foreign_key="categories.category_id")
    product_name: str = Field(max_length=100)
    unit: str = Field()

    class Meta:
        table_name = "products"
        endpoint = "/api/v1/products"


class Shipment(RestEndpoint):
    shipment_id: str = Field(primary_key=True)
    vendor_id: str = Field(foreign_key="vendors.vendor_id")
    shipment_date: datetime = Field(default_factory=datetime.now)

    class Meta:
        table_name = "shipments"
        endpoint = "/api/v1/shipments"


class ShipmentLot(RestEndpoint):
    lot_id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    shipment_id: str = Field(foreign_key="shipments.shipment_id")
    product_id: str = Field(foreign_key="products.product_id")
    quantity_on_hand: float = Field()
    unit: str = Field()
    last_restocked_date: datetime = Field(default_factory=datetime.now)

    class Meta:
        table_name = "shipment_lots"
        endpoint = "/api/v1/shipment-lots"


class Health(RestEndpoint, HttpMethod.GET):

    def list(self, request):
        utc_now = datetime.now(UTC)
        timestamp_str = utc_now.strftime('%Y-%m-%dT%H:%M:%SZ')
        data = {
            "status": "ok",
            "service": "supplynetwork",
            "section": "Section 3",
            "timeUtc": timestamp_str
        }

        return JSONResponse(data)

    class Meta:
        endpoint = "/api/v1/health"


class Version(RestEndpoint, HttpMethod.GET):

    def list(self, request):
        utc_now = datetime.now(UTC)
        timestamp_str = utc_now.strftime('%Y-%m-%dT%H:%M:%SZ')
        data = {
            "version": version,
            "timeUtc": timestamp_str
        }

        return JSONResponse(data)

    class Meta:
        endpoint = "/api/v1/version"


app = LightApi(engine=engine)
app.register({
    "/api/v1/vendors": Vendor,
    "/api/v1/categories": Category,
    "/api/v1/products": Product,
    "/api/v1/shipments": Shipment,
    "/api/v1/shipment-lots": ShipmentLot,
    "/api/v1/health": Health,
    "/api/v1/version": Version,
})

if __name__ == "__main__":
    DatabaseHandler.setup_tables()

    response = requests.get(f"{agnet_base_url}/health")
    if response.status_code == 200:
        is_agnet_up = True

    app.run(host="0.0.0.0", port=8000)
