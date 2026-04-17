# routes/orders.py
import uuid
import os
import requests
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from lightapi import RestEndpoint, Field, HttpMethod

from config import engine, agnet_base_url
from routes.vendors import Vendor
from routes.products import Product


class InventoryException(Exception):
    def __init__(self, errors):
        self.errors = errors


class Order(RestEndpoint, HttpMethod.POST):
    order_id: str = Field(primary_key=True, default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str = Field(max_length=100)
    status: str = Field(max_length=50)
    manifest_json: str = Field()

    def create(self, data):
        manifest = data.get("manifest")

        if not manifest:
            return JSONResponse(
                {"error": {"code": "VALIDATION_ERROR", "message": "manifest is required"}},
                status_code=400
            )

        inventory = self.build_inventory()

        try:
            self.check_inventory(manifest, inventory)
        except InventoryException as e:
            return JSONResponse(
                {"error": {"code": "INSUFFICIENT_STOCK", "message": "Insufficient stock for one or more items", "details": e.errors}},
                status_code=400
            )

        local_manifest, agnet_manifest = self.order_fulfillment(manifest, inventory)

        agnet_responses = []
        api_key = os.getenv("AGNET_SECTION_KEY")

        for agnet_order in agnet_manifest:
            try:
                response = requests.post(
                    f"{agnet_base_url}/orders",
                    headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                    json=agnet_order,
                    timeout=5
                )
                agnet_responses.append({
                    "vendorId": agnet_order["vendorId"],
                    "status": response.status_code,
                    "data": response.json()
                })
            except Exception as e:
                return JSONResponse(
                    {"error": {"code": "AGNET_UNREACHABLE", "message": str(e)}},
                    status_code=503
                )

        with Session(engine) as session:
            for local_order in local_manifest:
                vendor_id = local_order["vendorId"]
                for item in local_order["manifest"]:
                    product = session.execute(
                        select(Product).where(
                            Product.product_id == item["productId"],
                            Product.vendor_id == vendor_id
                        )
                    ).scalar_one_or_none()

                    if product:
                        product.quantity_available -= item["quantity"]

                vendor = session.execute(
                    select(Vendor).where(Vendor.vendor_id == vendor_id)
                ).scalar_one_or_none()

                if vendor:
                    vendor.order_count += 1
                    vendor.last_order = datetime.now(UTC)

            session.commit()

        return JSONResponse({
            "status": "accepted",
            "agnetResponses": agnet_responses,
            "localManifest": local_manifest,
            "agnetManifest": agnet_manifest
        })

    def build_inventory(self):
        inventory = []

        # Local products
        with Session(engine) as session:
            local_products = session.execute(
                select(Product, Vendor)
                .join(Vendor, Product.vendor_id == Vendor.vendor_id)
                .where(Vendor.reg_state.in_(["New", "Active"]))
            ).all()

            for product, vendor in local_products:
                inventory.append({
                    "productId": product.product_id,
                    "vendorId": vendor.vendor_id,
                    "quantity": product.quantity_available,
                    "unit": product.unit,
                    "source": "local"
                })

        # AgNet products
        api_key = os.getenv("AGNET_SECTION_KEY")
        try:
            response = requests.get(
                f"{agnet_base_url}/vendors",
                headers={"X-API-Key": api_key},
                timeout=5
            )
            response.raise_for_status()
            for vendor in response.json().get("items", []):
                if vendor.get("regState") not in ("New", "Active"):
                    continue
                for item in vendor.get("availableManifest", []):
                    inventory.append({
                        "productId": item.get("productId"),
                        "vendorId": vendor.get("vendorId"),
                        "quantity": item.get("quantityAvailable"),
                        "unit": item.get("unit"),
                        "source": "agnet"
                    })
        except Exception as e:
            print(f"AgNet Integration Error: {e}")

        return inventory

    def check_inventory(self, manifest, inventory):
        errors = []

        for item in manifest:
            product_id = item.get("productId")
            quantity_needed = item.get("quantity")

            suppliers = [i for i in inventory if i["productId"] == product_id]
            total_available = sum(i["quantity"] for i in suppliers)

            if total_available < quantity_needed:
                errors.append({
                    "productId": product_id,
                    "quantityNeeded": quantity_needed,
                    "quantityAvailable": total_available
                })

        if errors:
            raise InventoryException(errors)

    def order_fulfillment(self, manifest, inventory):
        local_plan = []
        agnet_plan = []

        for item in manifest:
            product_id = item.get("productId")
            quantity_needed = item.get("quantity")

            suppliers = [i for i in inventory if i["productId"] == product_id]
            total_available = sum(i["quantity"] for i in suppliers)

            portions = []
            for supplier in suppliers:
                weight = supplier["quantity"] / total_available
                portion = round(weight * quantity_needed)
                portions.append({
                    "productId": product_id,
                    "vendorId": supplier["vendorId"],
                    "quantity": portion,
                    "unit": supplier["unit"],
                    "source": supplier["source"]
                })

            # Give remainder to largest supplier to ensure total always matches
            total_assigned = sum(p["quantity"] for p in portions)
            difference = quantity_needed - total_assigned
            if difference != 0:
                largest = max(portions, key=lambda p: p["quantity"])
                largest["quantity"] += difference

            for portion in portions:
                if portion["source"] == "local":
                    local_plan.append(portion)
                else:
                    agnet_plan.append(portion)

        # Group agnet portions by vendor
        grouped_agnet = {}
        for portion in agnet_plan:
            vendor_id = portion["vendorId"]
            if vendor_id not in grouped_agnet:
                grouped_agnet[vendor_id] = []
            grouped_agnet[vendor_id].append({
                "productId": portion["productId"],
                "quantityOrder": portion["quantity"]
            })

        agnet_manifest = [
            {"vendorId": vid, "manifest": items}
            for vid, items in grouped_agnet.items()
        ]

        # Group local portions by vendor
        grouped_local = {}
        for portion in local_plan:
            vendor_id = portion["vendorId"]
            if vendor_id not in grouped_local:
                grouped_local[vendor_id] = []
            grouped_local[vendor_id].append({
                "productId": portion["productId"],
                "quantity": portion["quantity"],
                "unit": portion["unit"]
            })

        local_manifest = [
            {"vendorId": vid, "manifest": items}
            for vid, items in grouped_local.items()
        ]

        return local_manifest, agnet_manifest

    class Meta:
        table_name = "orders"
        endpoint = "/api/v1/orders"
