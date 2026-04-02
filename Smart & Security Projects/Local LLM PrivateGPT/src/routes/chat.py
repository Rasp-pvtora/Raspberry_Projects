"""Chat routes — Q&A page and WebSocket handler."""

import json
import uuid

from flask import Blueprint, render_template, current_app, session
from flask_socketio import emit

from src.routes.auth import login_required
from src.services.db import get_connection
from src.rag.conversation import ConversationMemory

chat_bp = Blueprint("chat", __name__)

_conversation_memory = ConversationMemory()


@chat_bp.route("/chat")
@login_required
def chat_page():
    return render_template("chat.html")


@chat_bp.route("/chat/conversations")
@login_required
def chat_conversations():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
    return {"conversations": [dict(r) for r in rows]}


@chat_bp.route("/chat/conversations/<int:conv_id>/messages")
@login_required
def chat_messages(conv_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT role, content, citations, created_at FROM messages WHERE conversation_id=? ORDER BY created_at",
            (conv_id,),
        ).fetchall()
    return {"messages": [dict(r) for r in rows]}


def register_socket_events(socketio):
    """Register SocketIO event handlers (called from app.py context)."""

    @socketio.on("ask")
    def handle_ask(data):
        question = data.get("question", "").strip()
        conv_id = data.get("conversation_id")

        if not question:
            emit("answer_token", {"token": "[Please enter a question]", "done": True})
            return

        retriever = current_app.config["retriever"]
        generator = current_app.config["generator"]

        # Create or reuse conversation
        if not conv_id:
            with get_connection() as conn:
                cur = conn.execute(
                    "INSERT INTO conversations (session_id, title, model_used) VALUES (?, ?, ?)",
                    (session.get("sid", str(uuid.uuid4())), question[:80], generator.model),
                )
                conv_id = cur.lastrowid
            emit("conversation_created", {"conversation_id": conv_id})

        # Retrieve relevant chunks
        emit("status", {"message": "Searching documents..."})
        chunks = retriever.retrieve(question)

        # Get conversation history
        history = _conversation_memory.get_context(str(conv_id))

        # Stream answer
        emit("status", {"message": "Generating answer..."})
        full_answer = ""
        for token in generator.generate(question, chunks, history):
            full_answer += token
            emit("answer_token", {"token": token, "done": False})
        emit("answer_token", {"token": "", "done": True})

        # Build citations
        citations = []
        for chunk in chunks:
            meta = chunk.metadata or {}
            citations.append({
                "document": meta.get("filename", "Unknown"),
                "page": meta.get("page_number", 0),
                "passage": chunk.text[:300],
            })

        emit("citations", {"citations": citations})

        # Store in DB
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'user', ?)",
                (conv_id, question),
            )
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content, citations, model_used) VALUES (?, 'assistant', ?, ?, ?)",
                (conv_id, full_answer, json.dumps(citations), generator.model),
            )
            conn.execute(
                "UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (conv_id,),
            )

        # Update memory
        _conversation_memory.add(str(conv_id), "user", question)
        _conversation_memory.add(str(conv_id), "assistant", full_answer)
