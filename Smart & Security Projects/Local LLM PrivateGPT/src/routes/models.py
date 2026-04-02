"""Model management routes — list, pull, switch, info."""

import os

from flask import Blueprint, render_template, request, jsonify

from src.routes.auth import login_required
from src.services.model_service import ModelService

models_bp = Blueprint("models", __name__)
_service = ModelService()


@models_bp.route("/models")
@login_required
def models_page():
    return render_template("models.html")


@models_bp.route("/models/list")
@login_required
def models_list():
    enabled = os.getenv("MODEL_MANAGEMENT_ENABLED", "true").lower() == "true"
    if not enabled:
        return jsonify({"error": "Model management is disabled"}), 403
    models = _service.list_models()
    active = _service.get_active_model()
    return jsonify({"models": models, "active": active})


@models_bp.route("/models/pull", methods=["POST"])
@login_required
def models_pull():
    enabled = os.getenv("MODEL_MANAGEMENT_ENABLED", "true").lower() == "true"
    if not enabled:
        return jsonify({"error": "Model management is disabled"}), 403
    name = request.json.get("name", "").strip()
    if not name:
        return jsonify({"error": "Model name required"}), 400
    # Pull is streamed via SocketIO in a real implementation; here return acknowledgement.
    return jsonify({"message": f"Pull started for {name}"})


@models_bp.route("/models/switch", methods=["POST"])
@login_required
def models_switch():
    enabled = os.getenv("MODEL_MANAGEMENT_ENABLED", "true").lower() == "true"
    if not enabled:
        return jsonify({"error": "Model management is disabled"}), 403
    name = request.json.get("name", "").strip()
    if not name:
        return jsonify({"error": "Model name required"}), 400
    _service.switch_model(name)
    return jsonify({"message": f"Switched to {name}", "active": name})


@models_bp.route("/models/<name>/info")
@login_required
def models_info(name: str):
    info = _service.model_info(name)
    return jsonify(info)
