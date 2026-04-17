# app.py
import requests
import config

from config import engine, agnet_base_url, API_MAP
from routes.vendors import Vendor
from routes.categories import Category
from routes.products import Product
from routes.orders import Order
from routes.health import Health
from routes.version import Version
from routes.docs import OpenAPI, SwaggerDocs

app = LightApi(engine=engine)

config.API_MAP = {
    "/api/v1/vendors": Vendor,
    "/api/v1/categories": Category,
    "/api/v1/products": Product,
    "/api/v1/orders": Order,
    "/api/v1/health": Health,
    "/api/v1/version": Version,
    "/openapi.json": OpenAPI,
    "/docs": SwaggerDocs
}

app.register(config.API_MAP)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3005)
