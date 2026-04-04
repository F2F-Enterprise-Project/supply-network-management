"""
Supply & Network Management — Flask Application Entry Point.

Endpoints:
  GET  /health                  → Health check
  GET  /supply/vendors          → List vendors (local cache)
  POST /supply/vendors/sync     → Pull vendors from AgNet
  GET  /supply/vendors/<id>     → Single vendor detail
  GET  /supply/catalog          → Product catalog
  POST /supply/orders           → Place procurement order (AgNet → CIS)
  GET  /supply/orders           → Order history
  GET  /supply/shipments        → Shipment history
  GET  /supply/inventory        → CIS pooled inventory
  GET  /supply/dashboard        → AgNet dashboard
"""

from flask import Flask
import config
from repository.db import init_db
from routes.health_routes import health_bp
from routes.supply_routes import supply_bp


def create_app(db_path=None):
    """Application factory — also used by tests."""
    app = Flask(__name__)
    app.config["TESTING"] = db_path == ":memory:"

    init_db(db_path or config.DATABASE_PATH)

    app.register_blueprint(health_bp)
    app.register_blueprint(supply_bp)

    @app.teardown_appcontext
    def shutdown(exc):  # noqa: ARG001
        pass  # DB connection is module-level; closed on process exit

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=config.PORT, debug=False)
