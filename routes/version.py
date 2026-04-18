# routes/version.py
from datetime import datetime, UTC
from starlette.responses import JSONResponse
from lightapi import RestEndpoint, HttpMethod

from config import version


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
