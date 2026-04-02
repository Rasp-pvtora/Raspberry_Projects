"""Public REST API — POST /api/ask."""

import os
import functools

from flask import Blueprint, request, jsonify, current_app

api_bp = Blueprint("api", __name__)


def _api_key_required(f):
    """Check X-API-Key header if API_KEY is configured."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        api_key = os.getenv("API_KEY", "")
        if api_key:
            provided = request.headers.get("X-API-Key", "")
            if provided != api_key:
                return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return wrapper


@api_bp.route("/api/ask", methods=["POST"])
@_api_key_required
def api_ask():
    enabled = os.getenv("API_ENABLED", "true").lower() == "true"
    if not enabled:
        return jsonify({"error": "API endpoint is disabled"}), 403

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Missing 'question' field"}), 400

    model_override = data.get("model")
    retriever = current_app.config["retriever"]
    generator = current_app.config["generator"]

    chunks = retriever.retrieve(question)
    result = generator.generate_full(question, chunks, model=model_override)

    return jsonify(result)
