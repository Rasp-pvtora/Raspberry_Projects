"""Learning mode routes — practice, grading, progress tracking."""

import os
import random

from flask import Blueprint, render_template, jsonify, request

from src.routes.auth import login_required
from src.services.db import update_learning_progress, get_learning_progress

learning_bp = Blueprint("learning", __name__, url_prefix="/learning")

# Default vocabulary per difficulty level
VOCABULARY = {
    "alphabet": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    "words": ["HELLO", "THANK YOU", "PLEASE", "YES", "NO", "SORRY", "HELP", "GOOD", "BAD", "FRIEND"],
    "phrases": ["HOW ARE YOU", "NICE TO MEET YOU", "THANK YOU VERY MUCH", "I NEED HELP", "GOOD MORNING"],
}


@learning_bp.route("/")
@login_required
def learning_page():
    enabled = os.getenv("LEARNING_MODE_ENABLED", "true").lower() == "true"
    return render_template("learning.html", enabled=enabled)


@learning_bp.route("/prompt")
@login_required
def get_prompt():
    """Return a random sign to practice."""
    difficulty = request.args.get("difficulty", "alphabet")
    vocab = VOCABULARY.get(difficulty, VOCABULARY["alphabet"])
    word = random.choice(vocab)
    return jsonify({"word": word, "difficulty": difficulty})


@learning_bp.route("/grade", methods=["POST"])
@login_required
def grade():
    """Grade a practice attempt."""
    data = request.get_json()
    if not data or "expected" not in data or "actual" not in data:
        return jsonify({"error": "Missing expected or actual"}), 400

    expected = data["expected"]
    actual = data["actual"]
    language = os.getenv("SIGN_LANGUAGE", "asl")
    correct = expected.upper() == actual.upper()

    update_learning_progress(expected, language, correct)

    return jsonify({"correct": correct, "expected": expected, "actual": actual})


@learning_bp.route("/progress")
@login_required
def progress():
    language = os.getenv("SIGN_LANGUAGE", "asl")
    return jsonify(get_learning_progress(language))
