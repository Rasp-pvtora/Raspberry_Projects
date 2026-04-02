"""Dashboard routes — overview stats and system info."""

from flask import Blueprint, render_template, current_app, jsonify

from src.routes.auth import login_required
from src.services.db import get_connection
from src.services.system_service import get_system_info

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html")


@dashboard_bp.route("/dashboard/stats")
@login_required
def dashboard_stats():
    with get_connection() as conn:
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        conv_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        msg_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        recent = conn.execute(
            "SELECT content, role, created_at FROM messages ORDER BY created_at DESC LIMIT 10"
        ).fetchall()

    system = get_system_info()
    vector_store = current_app.config.get("vector_store")
    embedding_count = vector_store.count() if vector_store else 0

    return jsonify({
        "documents": doc_count,
        "chunks": chunk_count,
        "conversations": conv_count,
        "messages": msg_count,
        "embeddings": embedding_count,
        "system": system,
        "recent_activity": [
            {"content": r["content"][:120], "role": r["role"], "created_at": r["created_at"]}
            for r in recent
        ],
    })
