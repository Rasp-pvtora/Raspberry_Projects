"""Local LLM PrivateGPT — Flask + SocketIO entry point."""

import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_socketio import SocketIO

# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Flask application factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "CHANGE_ME_TO_A_RANDOM_STRING")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_FILE_SIZE_MB", 50)) * 1024 * 1024

socketio = SocketIO(app, async_mode="threading")

# ---------------------------------------------------------------------------
# Initialise core services
# ---------------------------------------------------------------------------
from src.services.db import init_db  # noqa: E402
from src.services.vector_store import VectorStore  # noqa: E402
from src.ingestion.embedder import Embedder  # noqa: E402
from src.rag.retriever import Retriever  # noqa: E402
from src.rag.generator import Generator  # noqa: E402

init_db()

vector_store = VectorStore()
embedder = Embedder()
retriever = Retriever(embedder=embedder, vector_store=vector_store)
generator = Generator()

# Store shared objects on app so routes can access them
app.config["vector_store"] = vector_store
app.config["embedder"] = embedder
app.config["retriever"] = retriever
app.config["generator"] = generator
app.config["socketio"] = socketio

# ---------------------------------------------------------------------------
# Register route blueprints
# ---------------------------------------------------------------------------
from src.routes.auth import auth_bp  # noqa: E402
from src.routes.dashboard import dashboard_bp  # noqa: E402
from src.routes.documents import documents_bp  # noqa: E402
from src.routes.chat import chat_bp  # noqa: E402
from src.routes.models import models_bp  # noqa: E402
from src.routes.compare import compare_bp  # noqa: E402
from src.routes.api import api_bp  # noqa: E402
from src.routes.settings import settings_bp  # noqa: E402

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(models_bp)
app.register_blueprint(compare_bp)
app.register_blueprint(api_bp)
app.register_blueprint(settings_bp)


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("dashboard.dashboard_page"))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    socketio.run(app, host=host, port=port, debug=debug)
