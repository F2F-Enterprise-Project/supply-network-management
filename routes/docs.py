# routes/docs.py
from starlette.responses import JSONResponse, HTMLResponse
from lightapi import RestEndpoint, HttpMethod

import config
from config import version

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

        for path, endpoint_cls in config.API_MAP.items():

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