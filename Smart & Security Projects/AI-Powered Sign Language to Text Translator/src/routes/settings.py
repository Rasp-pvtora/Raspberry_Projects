"""Settings routes — language, model, TTS, camera, kiosk configuration."""

import os

from flask import Blueprint, render_template, jsonify, request

from src.routes.auth import login_required
from src.services.language_service import LanguageService
from src.services.db import get_setting, set_setting

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")

language_service = LanguageService()


@settings_bp.route("/")
@login_required
def settings_page():
    return render_template("settings.html", languages=language_service.list_languages())


@settings_bp.route("/api/languages")
@login_required
def api_languages():
    return jsonify(language_service.list_languages())


@settings_bp.route("/api/language", methods=["POST"])
@login_required
def set_language():
    data = request.get_json()
    if not data or "language" not in data:
        return jsonify({"error": "Missing language"}), 400

    try:
        model_path = language_service.switch_language(data["language"])
        set_setting("sign_language", data["language"])
        return jsonify({"language": data["language"], "model_path": model_path})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@settings_bp.route("/api/update", methods=["POST"])
@login_required
def update_settings():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    allowed_keys = {
        "confidence_threshold", "sentence_enabled", "sentence_pause_sec",
        "two_hand_enabled", "tts_enabled", "tts_voice",
        "kiosk_mode", "kiosk_timeout_sec", "data_collection_enabled",
    }

    updated = {}
    for key, value in data.items():
        if key in allowed_keys:
            set_setting(key, str(value))
            updated[key] = value

    return jsonify({"updated": updated})
