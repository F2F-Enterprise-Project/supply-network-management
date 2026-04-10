import uuid
import os
import requests
from starlette.responses import JSONResponse, HTMLResponse
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from lightapi import LightApi, RestEndpoint, Field, HttpMethod
from datetime import datetime, UTC

engine = create_engine("sqlite:///supplynetwork.db", connect_args={"check_same_thread": False})

agnet_base_url = "http://146.190.243.241:8303/api/v1"
version = "0.2.1"
API_MAP = ""


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
            if hasattr(last_order_val, 'strftime'):
                last_order_val = last_order_val.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # added to format agnet response with global standards
            elif isinstance(last_order_val, str):
                parsed = datetime.fromisoformat(last_order_val)
                last_order_val = parsed.strftime('%Y-%m-%dT%H:%M:%SZ')
            
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
    parent_category_id: str = Field(foreign_key="categorys.category_id", nullable=True)
    category_name: str = Field(max_length=100)
    level: int = Field()

    class Meta:
        table_name = "categories"
        endpoint = "/api/v1/categories"


class Product(RestEndpoint):
    product_id: str = Field(primary_key=True)
    vendor_id: str = Field(foreign_key="vendors.vendor_id")
    category_id: str = Field(foreign_key="categorys.category_id")
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


class OpenAPI(RestEndpoint, HttpMethod.GET):
    def list(self, request):
        schema = {
            "openapi": "3.1.0",
            "info": {
                "title": "F2F SNM API",
                "version": version,
                "description": "Gateway for AgNet and CIS service integrations."
            },
            "paths": {},
            "components": {"schemas": {}}
        }

        for path, endpoint_cls in API_MAP.items():

            if endpoint_cls in [OpenAPI, SwaggerDocs]:
                continue

            model_name = endpoint_cls.__name__
            methods = endpoint_cls._allowed_methods

            read_schema = endpoint_cls.__schema_read__.model_json_schema()
            create_schema = endpoint_cls.__schema_create__.model_json_schema()

            schema["components"]["schemas"][f"{model_name}Read"] = read_schema
            schema["components"]["schemas"][f"{model_name}Create"] = create_schema

            schema["paths"][path] = {}

            if 'GET' in methods:
                schema["paths"][path]["get"] = {
                    "summary": f"List {model_name} records",
                    "responses": {
                        "200": {
                            "description": "A list of records",
                            "content": {"application/json": {"schema": {
                                "type": "array",
                                "items": {"$ref": f"#/components/schemas/{model_name}Read"}
                            }}}
                        }
                    }
                }

            if 'POST' in methods:
                schema["paths"][path]["post"] = {
                    "summary": f"Create new {model_name}",
                    "requestBody": {
                        "content": {"application/json": {"schema": {
                            "$ref": f"#/components/schemas/{model_name}Create"
                        }}}
                    },
                    "responses": {"201": {"description": "Created successfully"}}
                }

        return JSONResponse(schema)

    class Meta:
        endpoint = "/openapi.json"


class SwaggerDocs(RestEndpoint, HttpMethod.GET):
    def list(self, request):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
            <title>F2F SNM API Docs</title>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
            <script>
                const ui = SwaggerUIBundle({
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                    presets: [SwaggerUIBundle.presets.apis],
                    layout: "BaseLayout"
                })
            </script>
        </body>
        </html>
        """
        return HTMLResponse(html)

    class Meta:
        endpoint = "/docs"


app = LightApi(engine=engine)

API_MAP = {
    "/api/v1/vendors": Vendor,
    "/api/v1/categories": Category,
    "/api/v1/products": Product,
    "/api/v1/shipments": Shipment,
    "/api/v1/shipment-lots": ShipmentLot,
    "/api/v1/health": Health,
    "/api/v1/version": Version,
    "/openapi.json": OpenAPI,
    "/docs": SwaggerDocs
}

app.register(API_MAP)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3005)
