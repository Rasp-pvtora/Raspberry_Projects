"""Recognition routes — recognition feed API and data collection."""

import os
import json
import time

import numpy as np
from flask import Blueprint, jsonify, request

from src.routes.auth import login_required
from src.services.db import log_recognition, get_recognition_history

recognition_bp = Blueprint("recognition", __name__, url_prefix="/api/recognition")


@recognition_bp.route("/history")
@login_required
def history():
    limit = request.args.get("limit", 50, type=int)
    return jsonify(get_recognition_history(limit))


@recognition_bp.route("/collect", methods=["POST"])
@login_required
def collect_data():
    """Save hand landmarks + label for training data collection."""
    if os.getenv("DATA_COLLECTION_ENABLED", "false").lower() != "true":
        return jsonify({"error": "Data collection disabled"}), 403

    data = request.get_json()
    if not data or "landmarks" not in data or "label" not in data:
        return jsonify({"error": "Missing landmarks or label"}), 400

    label = data["label"]
    landmarks = data["landmarks"]

    # Validate
    if not isinstance(label, str) or len(label) > 50:
        return jsonify({"error": "Invalid label"}), 400

    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "training_data", label)
    os.makedirs(data_dir, exist_ok=True)

    filename = f"{int(time.time() * 1000)}.npy"
    filepath = os.path.join(data_dir, filename)
    np.save(filepath, np.array(landmarks, dtype=np.float32))

    return jsonify({"status": "saved", "path": filepath})
