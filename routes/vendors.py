# routes/vendor.py
import os
import requests
from starlette.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from lightapi import RestEndpoint, Field
from datetime import datetime

from config import engine, agnet_base_url


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
