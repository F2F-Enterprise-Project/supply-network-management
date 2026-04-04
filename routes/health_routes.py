"""Health check endpoint — required by CI/CD pipeline."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "supply-network-management"}), 200
