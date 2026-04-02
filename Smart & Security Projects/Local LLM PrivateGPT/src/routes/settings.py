"""Settings routes — config display, password change, CSV export."""

import os

import bcrypt
from flask import Blueprint, render_template, request, jsonify, Response

from src.routes.auth import login_required, _hash_password, _cached_hash
from src.services.export_service import ExportService
import src.routes.auth as auth_module

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html")


@settings_bp.route("/settings/password", methods=["POST"])
@login_required
def settings_password():
    data = request.get_json(silent=True) or {}
    new_password = data.get("new_password", "").strip()
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    auth_module._cached_hash = _hash_password(new_password)
    return jsonify({"message": "Password updated (runtime only — update .env for persistence)"})


@settings_bp.route("/settings/export")
@login_required
def settings_export():
    enabled = os.getenv("EXPORT_ENABLED", "true").lower() == "true"
    if not enabled:
        return jsonify({"error": "Export is disabled"}), 403

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    csv_content = ExportService.export_qa_history(start_date, end_date)

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=qa_history.csv"},
    )


@settings_bp.route("/settings/config")
@login_required
def settings_config():
    """Return current configuration (read-only, secrets masked)."""
    config = {
        "PORT": os.getenv("PORT", "5000"),
        "HOST": os.getenv("HOST", "0.0.0.0"),
        "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "llama3:8b-q4_0"),
        "OLLAMA_TEMPERATURE": os.getenv("OLLAMA_TEMPERATURE", "0.3"),
        "OLLAMA_MAX_TOKENS": os.getenv("OLLAMA_MAX_TOKENS", "512"),
        "RAG_ENABLED": os.getenv("RAG_ENABLED", "true"),
        "CHUNK_SIZE": os.getenv("CHUNK_SIZE", "1000"),
        "CHUNK_OVERLAP": os.getenv("CHUNK_OVERLAP", "200"),
        "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        "RETRIEVAL_TOP_K": os.getenv("RETRIEVAL_TOP_K", "5"),
        "RERANKING_ENABLED": os.getenv("RERANKING_ENABLED", "true"),
        "MAX_FILE_SIZE_MB": os.getenv("MAX_FILE_SIZE_MB", "50"),
        "ALLOWED_EXTENSIONS": os.getenv("ALLOWED_EXTENSIONS", "pdf,docx,txt,csv,md"),
    }
    return jsonify(config)
