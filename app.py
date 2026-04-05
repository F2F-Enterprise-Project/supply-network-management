import uuid
from DatabaseHandler import DatabaseHandler
from sqlalchemy import create_engine
from lightapi import LightApi, RestEndpoint, Field
from datetime import datetime


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

    class Meta:
        table_name = "vendors"
        endpoint = "/vendors"


class Category(RestEndpoint):
    category_id: str = Field(primary_key=True)
    parent_category_id: str = Field(foreign_key="categories.category_id", nullable=True)
    category_name: str = Field(max_length=100)
    level: int = Field()

    class Meta:
        table_name = "categories"
        endpoint = "/categories"


class Product(RestEndpoint):
    product_id: str = Field(primary_key=True)
    vendor_id: str = Field(foreign_key="vendors.vendor_id")
    category_id: str = Field(foreign_key="categories.category_id")
    product_name: str = Field(max_length=100)
    unit: str = Field()

    class Meta:
        table_name = "products"
        endpoint = "/products"


class Shipment(RestEndpoint):
    shipment_id: str = Field(primary_key=True)
    vendor_id: str = Field(foreign_key="vendors.vendor_id")
    shipment_date: datetime = Field(default_factory=datetime.now)

    class Meta:
        table_name = "shipments"
        endpoint = "/shipments"


class ShipmentLot(RestEndpoint):
    lot_id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    shipment_id: str = Field(foreign_key="shipments.shipment_id")
    product_id: str = Field(foreign_key="products.product_id")
    quantity_on_hand: float = Field()
    unit: str = Field()
    last_restocked_date: datetime = Field(default_factory=datetime.now)

    class Meta:
        table_name = "shipment_lots"
        endpoint = "/shipment-lots"


engine = create_engine("sqlite:///supplynetwork.db", connect_args={"check_same_thread": False})

app = LightApi(engine=engine)
app.register({
    "/vendors": Vendor,
    "/categories": Category,
    "/products": Product,
    "/shipments": Shipment,
    "/shipment-lots": ShipmentLot
})

if __name__ == "__main__":
    DatabaseHandler.setup_tables()
    app.run(host="0.0.0.0", port=8000)
