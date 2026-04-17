# routes/health.py
from datetime import datetime, UTC
from starlette.responses import JSONResponse
from lightapi import RestEndpoint, HttpMethod

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