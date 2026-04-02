"""Document upload, listing, deletion, re-indexing routes."""

import os
import hashlib

from flask import (
    Blueprint, render_template, request, jsonify, current_app,
)
from werkzeug.utils import secure_filename

from src.routes.auth import login_required
from src.services.db import get_connection
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import Chunker

documents_bp = Blueprint("documents", __name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 50)) * 1024 * 1024
ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "pdf,docx,txt,csv,md").split(","))


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def _run_ingestion(doc_id: int, file_path: str, filename: str):
    """Load, chunk, embed, and store a document."""
    vector_store = current_app.config["vector_store"]
    embedder = current_app.config["embedder"]

    loader = DocumentLoader()
    doc = loader.load(file_path)
    chunker = Chunker()

    all_texts = []
    all_metas = []
    chunk_rows = []

    for page in doc.pages:
        chunks = chunker.chunk(page.text, document_id=doc_id, page_number=page.page_number)
        for chunk in chunks:
            all_texts.append(chunk.text)
            all_metas.append({
                "document_id": doc_id,
                "filename": filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
            })
            chunk_rows.append(chunk)

    # Embed
    embeddings = embedder.embed(all_texts)

    # Store in ChromaDB
    chroma_ids = vector_store.add(all_texts, embeddings.tolist(), all_metas)

    # Store in SQLite
    with get_connection() as conn:
        for chunk, cid in zip(chunk_rows, chroma_ids):
            conn.execute(
                "INSERT INTO chunks (document_id, chunk_index, content, page_number, char_offset, token_count, chroma_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (doc_id, chunk.chunk_index, chunk.text, chunk.page_number,
                 chunk.char_offset, chunk.token_count, cid),
            )
        conn.execute(
            "UPDATE documents SET chunk_count=?, page_count=?, status='ready', indexed_at=CURRENT_TIMESTAMP WHERE id=?",
            (len(chunk_rows), doc.page_count, doc_id),
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@documents_bp.route("/documents")
@login_required
def documents_page():
    return render_template("documents.html")


@documents_bp.route("/documents/list")
@login_required
def documents_list():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY uploaded_at DESC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@documents_bp.route("/documents/upload", methods=["POST"])
@login_required
def documents_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename or not _allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    filename = secure_filename(file.filename)
    # Extra path-traversal guard
    if ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"error": "Invalid filename"}), 400

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, filename)
    file.save(file_path)

    # Check size after save
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        os.remove(file_path)
        return jsonify({"error": "File exceeds maximum size"}), 400

    checksum = _sha256(file_path)

    # Deduplication check
    with get_connection() as conn:
        duplicate = conn.execute(
            "SELECT id, filename FROM documents WHERE checksum=?", (checksum,)
        ).fetchone()

    if duplicate:
        warning = f"Duplicate of '{duplicate['filename']}' (id={duplicate['id']})"
    else:
        warning = None

    ext = filename.rsplit(".", 1)[1].lower()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO documents (filename, file_type, file_size, file_path, checksum, status) "
            "VALUES (?, ?, ?, ?, ?, 'processing')",
            (filename, ext, os.path.getsize(file_path), file_path, checksum),
        )
        doc_id = cur.lastrowid

    try:
        _run_ingestion(doc_id, file_path, filename)
    except Exception as exc:
        with get_connection() as conn:
            conn.execute("UPDATE documents SET status='error' WHERE id=?", (doc_id,))
        return jsonify({"error": str(exc), "document_id": doc_id}), 500

    result = {"message": "Document uploaded and indexed", "document_id": doc_id}
    if warning:
        result["warning"] = warning
    return jsonify(result), 201


@documents_bp.route("/documents/<int:doc_id>", methods=["DELETE"])
@login_required
def documents_delete(doc_id: int):
    vector_store = current_app.config["vector_store"]

    with get_connection() as conn:
        doc = conn.execute("SELECT file_path FROM documents WHERE id=?", (doc_id,)).fetchone()
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        # Delete file
        if os.path.isfile(doc["file_path"]):
            os.remove(doc["file_path"])

        # Delete from DB (cascade deletes chunks)
        conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))

    # Delete from ChromaDB
    vector_store.delete(doc_id)

    return jsonify({"message": "Document deleted"})


@documents_bp.route("/documents/<int:doc_id>/reindex", methods=["POST"])
@login_required
def documents_reindex(doc_id: int):
    vector_store = current_app.config["vector_store"]

    with get_connection() as conn:
        doc = conn.execute("SELECT file_path, filename FROM documents WHERE id=?", (doc_id,)).fetchone()
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        # Clear old chunks
        conn.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))

    vector_store.delete(doc_id)

    try:
        _run_ingestion(doc_id, doc["file_path"], doc["filename"])
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({"message": "Document re-indexed"})
