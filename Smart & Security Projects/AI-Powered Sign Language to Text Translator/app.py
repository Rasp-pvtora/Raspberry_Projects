"""Flask entry point — AI-Powered Sign Language to Text Translator."""

import os
import threading

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_socketio import SocketIO

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "CHANGE_ME_TO_A_RANDOM_STRING")

socketio = SocketIO(app, async_mode="eventlet")

# ─── Register blueprints ───────────────────────────────────────
from src.routes.auth import auth_bp          # noqa: E402
from src.routes.dashboard import dashboard_bp  # noqa: E402
from src.routes.recognition import recognition_bp  # noqa: E402
from src.routes.learning import learning_bp  # noqa: E402
from src.routes.settings import settings_bp  # noqa: E402

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(recognition_bp)
app.register_blueprint(learning_bp)
app.register_blueprint(settings_bp)

# ─── Database init ─────────────────────────────────────────────
from src.services.db import init_db  # noqa: E402
init_db()

# ─── Recognition pipeline (background thread) ─────────────────
from src.recognition.hand_tracker import HandTracker  # noqa: E402
from src.recognition.sign_classifier import SignClassifier  # noqa: E402
from src.recognition.sentence_builder import SentenceBuilder  # noqa: E402
from src.hardware.camera import Camera  # noqa: E402
from src.services.tts_service import TTSService  # noqa: E402

camera = Camera()
hand_tracker = HandTracker()
sign_classifier = SignClassifier()
sentence_builder = SentenceBuilder()
tts_service = TTSService()

recognition_running = False


def recognition_loop():
    """Main recognition loop — runs in a background thread."""
    global recognition_running
    recognition_running = True

    while recognition_running:
        frame = camera.get_frame()
        if frame is None:
            continue

        landmarks, annotated_frame = hand_tracker.process_frame(frame)
        if landmarks is None:
            socketio.emit("frame", {"frame": camera.encode_frame(annotated_frame)})
            continue

        result = sign_classifier.classify(landmarks)
        if result:
            label, confidence = result
            sentence_builder.add_sign(label, confidence)

            socketio.emit("recognition", {
                "label": label,
                "confidence": confidence,
                "sentence": sentence_builder.get_current_sentence(),
            })

        finalized = sentence_builder.check_pause()
        if finalized:
            socketio.emit("sentence", {"sentence": finalized})
            if os.getenv("TTS_ENABLED", "false").lower() == "true":
                tts_service.speak(finalized)

        socketio.emit("frame", {"frame": camera.encode_frame(annotated_frame)})
        socketio.sleep(0.01)


@app.route("/")
def index():
    kiosk = os.getenv("KIOSK_MODE", "false").lower() == "true"
    if kiosk:
        return redirect(url_for("dashboard.kiosk"))
    return redirect(url_for("dashboard.dashboard_page"))


@socketio.on("connect")
def handle_connect():
    global recognition_running
    if not recognition_running:
        socketio.start_background_task(recognition_loop)


@socketio.on("disconnect")
def handle_disconnect():
    pass


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    socketio.run(app, host=host, port=port, debug=False)
