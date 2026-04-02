"""Document comparison routes."""

import os

from flask import Blueprint, render_template, request, jsonify, current_app

from src.routes.auth import login_required
from src.services.db import get_connection

compare_bp = Blueprint("compare", __name__)


@compare_bp.route("/compare")
@login_required
def compare_page():
    return render_template("compare.html")


@compare_bp.route("/compare/run", methods=["POST"])
@login_required
def compare_run():
    enabled = os.getenv("COMPARISON_ENABLED", "true").lower() == "true"
    if not enabled:
        return jsonify({"error": "Comparison is disabled"}), 403

    data = request.json or {}
    doc_id_a = data.get("document_a")
    doc_id_b = data.get("document_b")
    if not doc_id_a or not doc_id_b:
        return jsonify({"error": "Two document IDs required"}), 400

    with get_connection() as conn:
        chunks_a = conn.execute(
            "SELECT content FROM chunks WHERE document_id=? ORDER BY chunk_index", (doc_id_a,)
        ).fetchall()
        chunks_b = conn.execute(
            "SELECT content FROM chunks WHERE document_id=? ORDER BY chunk_index", (doc_id_b,)
        ).fetchall()
        doc_a = conn.execute("SELECT filename FROM documents WHERE id=?", (doc_id_a,)).fetchone()
        doc_b = conn.execute("SELECT filename FROM documents WHERE id=?", (doc_id_b,)).fetchone()

    if not chunks_a or not chunks_b:
        return jsonify({"error": "One or both documents have no chunks"}), 400

    text_a = "\n".join(r["content"][:500] for r in chunks_a[:5])
    text_b = "\n".join(r["content"][:500] for r in chunks_b[:5])

    name_a = doc_a["filename"] if doc_a else "Document A"
    name_b = doc_b["filename"] if doc_b else "Document B"

    prompt = (
        f"Compare the following two documents and provide a structured analysis "
        f"with: 1) Key similarities, 2) Key differences, 3) Contradictions.\n\n"
        f"--- {name_a} ---\n{text_a}\n\n--- {name_b} ---\n{text_b}"
    )

    generator = current_app.config["generator"]
    result = generator.generate_full(prompt)
    return jsonify(result)
