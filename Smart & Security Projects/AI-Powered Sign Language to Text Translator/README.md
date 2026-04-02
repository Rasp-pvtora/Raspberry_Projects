# AI-Powered Sign Language to Text Translator

A real-time sign language recognition system for Raspberry Pi that uses MediaPipe hand landmark tracking and a custom-trained LSTM model to translate American Sign Language (ASL) gestures into text. Supports sentence-level recognition, multi-sign-language systems (ASL, BSL, DGS, LSF), two-way communication with text-to-sign display, confidence indicators, and a learning/training mode. Designed for accessibility kiosks in public services, with an optional kiosk interface and Piper TTS audio output.

🪙 **Donations are Welcome!**
If you find this project helpful, you can support my work with a small donation.
₿ Bitcoin donation: `bc1q...`

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Budget](#budget)
4. [Libraries and dependencies](#libraries-and-dependencies)
5. [Quickstart — Laptop (development)](#quickstart--laptop-development)
6. [Environment configuration (.env)](#environment-configuration-env)
7. [System overview](#system-overview)
8. [Feature — Real-time hand tracking (MediaPipe)](#feature--real-time-hand-tracking-mediapipe)
9. [Feature — Sign classification (LSTM)](#feature--sign-classification-lstm)
10. [Feature — Sentence-level recognition](#feature--sentence-level-recognition)
11. [Feature — Two-hand sign recognition](#feature--two-hand-sign-recognition)
12. [Feature — Multi-sign-language support](#feature--multi-sign-language-support)
13. [Feature — Two-way communication (text-to-sign)](#feature--two-way-communication-text-to-sign)
14. [Feature — Confidence indicator](#feature--confidence-indicator)
15. [Feature — TTS audio output (Piper)](#feature--tts-audio-output-piper)
16. [Feature — Learning/training mode](#feature--learningtraining-mode)
17. [Feature — Kiosk mode](#feature--kiosk-mode)
18. [Feature — Web dashboard](#feature--web-dashboard)
19. [Authentication](#authentication)
20. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
21. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
22. [Security notes](#security-notes)
23. [Troubleshooting](#troubleshooting)
24. [Where to next](#where-to-next)

---

## Project structure

```
.
├── app.py                     ← Python entry point (Flask + recognition loop)
├── requirements.txt           ← Python dependencies
├── .env.default               ← Environment variable template
├── .gitignore
├── src/
│   ├── recognition/
│   │   ├── hand_tracker.py    ← MediaPipe hand landmark extraction
│   │   ├── sign_classifier.py ← LSTM/Transformer sign classification
│   │   ├── sentence_builder.py ← Accumulate signs into sentences
│   │   └── text_to_sign.py   ← Reverse: text → animated sign display
│   ├── hardware/
│   │   ├── camera.py          ← Camera capture
│   │   └── mock_hardware.py   ← Mock camera for development
│   ├── routes/
│   │   ├── auth.py            ← Login / logout
│   │   ├── dashboard.py       ← Dashboard API
│   │   ├── recognition.py     ← Recognition feed API
│   │   ├── learning.py        ← Learning mode API
│   │   └── settings.py        ← Settings API
│   └── services/
│       ├── tts_service.py     ← Piper TTS for spoken output
│       ├── language_service.py ← Multi-language sign model management
│       ├── db.py              ← SQLite database
│       └── system_service.py  ← System info
├── models/
│   ├── asl_lstm.h5            ← Trained ASL LSTM model
│   ├── bsl_lstm.h5            ← BSL model (optional)
│   ├── sign_dictionary/       ← Text-to-sign image/animation assets
│   └── piper/                 ← Piper TTS voice models
├── data/
│   ├── sign_language.db       ← SQLite database
│   └── training_data/         ← Collected training hand landmarks
├── templates/
│   ├── layout.html
│   ├── login.html
│   ├── dashboard.html         ← Live recognition + text display
│   ├── learning.html          ← Learning/practice mode
│   ├── kiosk.html             ← Full-screen kiosk interface
│   └── settings.html
├── static/
│   ├── css/style.css
│   └── js/
│       ├── main.js
│       ├── dashboard.js       ← Hand landmark overlay + text feed
│       ├── learning.js        ← Learning mode UI
│       └── kiosk.js           ← Kiosk auto-reset logic
├── scripts/
│   ├── setup-camera.sh
│   ├── download-models.sh
│   └── train-model.sh        ← Train LSTM from collected data
├── deploy/
│   └── deploy_to_pi.sh
├── docs/
│   └── threat_model.md
├── tests/
├── README.md
├── TSD.md
├── task.md
└── implementation_plan.md
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB+) / Pi 5 | Yes | Pi 5 recommended for real-time MediaPipe |
| microSD card (32 GB+) | Yes | OS + models |
| Pi Camera Module v3 / USB webcam | Yes | 720p+ for hand landmark detection |
| Power supply (official) | Yes | 5V 3A / 5V 5A |

### Kiosk deployment (optional)

| Component | Required | Notes |
|---|---|---|
| Touchscreen (7" / 10") | Optional | For kiosk public deployment |
| Speaker (3.5mm or USB) | Optional | TTS audio output |
| Case / enclosure | Optional | Kiosk housing |

---

## Budget

| Item | Estimated Price (USD) | Notes |
|---|---|---|
| Pi Camera Module v3 | $25 – $30 | Standard camera for hand tracking |
| **Alternative:** USB webcam (720p+) | $15 – $25 | Logitech C270 or similar |
| **Optional:** 7" touchscreen | $40 – $60 | Official Pi 7" or Waveshare |
| **Optional:** 3.5mm speaker | $5 – $10 | For TTS output |
| **Optional:** Kiosk case | $15 – $30 | 3D-printed or commercial |
| **Total (minimum)** | **~$0 – $30** | Pi Camera (if not already owned) |
| **Total (kiosk setup)** | **~$55 – $120** | Camera + touchscreen + speaker + case |

---

## Libraries and dependencies

### Python dependencies

| Library | Version | Purpose |
|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | ^3.1.0 | Web framework |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | ^5.4.0 | WebSocket real-time feed |
| [mediapipe](https://mediapipe.dev/) | ^0.10.14 | Hand landmark detection (21 landmarks × 3D) |
| [tensorflow-lite-runtime](https://www.tensorflow.org/lite) | ^2.14.0 | LSTM model inference (lightweight) |
| [opencv-python-headless](https://pypi.org/project/opencv-python-headless/) | ^4.10.0 | Camera capture and image processing |
| [numpy](https://numpy.org/) | ^1.26.0 | Landmark data processing |
| [piper-tts](https://github.com/rhasspy/piper) | ^1.2.0 | Text-to-speech output |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ^1.0.1 | Environment configuration |
| [bcrypt](https://pypi.org/project/bcrypt/) | ^4.2.0 | Password hashing |
| [Jinja2](https://jinja.palletsprojects.com/) | ^3.1.4 | HTML templates |

### Dev dependencies

| Library | Version | Purpose |
|---|---|---|
| [pytest](https://docs.pytest.org/) | ^8.3.0 | Testing |
| [tensorflow](https://www.tensorflow.org/) | ^2.16.0 | Model training (laptop/desktop only) |
| [keras](https://keras.io/) | ^3.0.0 | LSTM model building |

---

## Quickstart — Laptop (development)

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/AI-Powered Sign Language to Text Translator"
cp .env.default .env
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
bash scripts/download-models.sh
python app.py
```

Open `http://localhost:5000`. On a laptop with a webcam, hand tracking works. The LSTM model classifies signs in real time.

---

## Environment configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Web server port |
| `HOST` | `0.0.0.0` | Listen address |
| `SESSION_SECRET` | `CHANGE_ME...` | Session encryption key |
| `ADMIN_USERNAME` | `admin` | Login username |
| `ADMIN_PASSWORD` | `changeme` | Login password |
| `CAMERA_SOURCE` | `0` | Camera index |
| `CAMERA_RESOLUTION` | `640x480` | Capture resolution |
| `SIGN_LANGUAGE` | `asl` | Active sign language: `asl`, `bsl`, `dgs`, `lsf` |
| `MODEL_PATH` | `./models/asl_lstm.h5` | LSTM model path |
| `CONFIDENCE_THRESHOLD` | `0.7` | Min classification confidence |
| `SENTENCE_ENABLED` | `true` | Enable sentence-level recognition |
| `SENTENCE_PAUSE_SEC` | `2.0` | Pause duration to finalize sentence |
| `TWO_HAND_ENABLED` | `true` | Enable two-hand sign recognition |
| `TEXT_TO_SIGN_ENABLED` | `true` | Enable reverse text-to-sign display |
| `TTS_ENABLED` | `false` | Enable Piper TTS spoken output |
| `TTS_VOICE` | `en_US-lessac-medium` | Piper voice model |
| `LEARNING_MODE_ENABLED` | `true` | Enable learning/practice mode |
| `KIOSK_MODE` | `false` | Enable full-screen kiosk mode |
| `KIOSK_TIMEOUT_SEC` | `60` | Auto-reset after inactivity |
| `DATA_COLLECTION_ENABLED` | `false` | Collect hand landmarks for training |

---

## System overview

```
Camera frame → MediaPipe Hands → 21 landmarks (x, y, z) per hand
    → LSTM classifier → Sign label + confidence
    → Sentence builder → Accumulate signs → Full sentence
    → Display: on-screen text + optional TTS audio
    → Dashboard: WebSocket real-time feed
```

| Stage | Component | Tool |
|---|---|---|
| **1. Capture** | Camera | OpenCV |
| **2. Track** | Hand landmarks | MediaPipe Hands (21 × 3D per hand) |
| **3. Classify** | Sign recognition | LSTM / Transformer (TFLite) |
| **4. Sentence** | Accumulation | Custom logic (pause = sentence end) |
| **5. Output** | Text display | WebSocket → dashboard canvas |
| **6. Audio** | TTS (optional) | Piper TTS |
| **7. Reverse** | Text-to-sign | Pre-rendered sign dictionary |

---

## Feature — Real-time hand tracking (MediaPipe)

MediaPipe Hands detects 21 3D landmarks per hand in real time.

- **21 landmarks:** Wrist, thumb (4 joints), index (4), middle (4), ring (4), pinky (4).
- **3D coordinates:** x, y, z per landmark (63 values per hand, 126 for two hands).
- **Performance:** ~15–20 FPS on Pi 4, ~25–30 FPS on Pi 5.
- **Visualization:** Hand skeleton overlaid on camera feed in the dashboard.
- **Dual hand:** MediaPipe supports simultaneous tracking of both hands.

---

## Feature — Sign classification (LSTM)

A sequence model classifies hand landmark sequences into sign labels.

- **Input:** Sequence of N frames of landmark coordinates (e.g., 30 frames = ~2 seconds).
- **Architecture:** LSTM (2 layers, 64 units) → Dense → Softmax over sign vocabulary.
- **Vocabulary:** ASL alphabet (26 letters) + common words/phrases (configurable).
- **Output:** Sign label + confidence score.
- **TFLite:** Model converted to TFLite for optimized Pi inference.

---

## Feature — Sentence-level recognition

Not just individual signs — accumulate signs into coherent sentences.

- Signs are buffered as the user signs continuously.
- A pause of `SENTENCE_PAUSE_SEC` seconds (default: 2.0) finalizes the sentence.
- Punctuation inferred from pause length (short pause = comma, long pause = period).
- Sentence displayed on screen as it builds (word by word).
- Toggle: `SENTENCE_ENABLED=true/false`.

---

## Feature — Two-hand sign recognition

Some signs require both hands.

- MediaPipe tracks both hands simultaneously.
- 126 input features (63 per hand) when both hands visible.
- Model trained on both single-hand and dual-hand signs.
- Automatic: if one hand visible → single-hand model features. If both → dual-hand features.
- Toggle: `TWO_HAND_ENABLED=true/false`.

---

## Feature — Multi-sign-language support

Switch between sign language systems from the dashboard.

| Language | Code | Signs |
|---|---|---|
| American Sign Language | `asl` | Default |
| British Sign Language | `bsl` | Two-handed alphabet |
| German Sign Language (DGS) | `dgs` | Deutsche Gebärdensprache |
| French Sign Language (LSF) | `lsf` | Langue des Signes Française |

- Each language has its own LSTM model file.
- Switch from Settings page or `SIGN_LANGUAGE` in `.env`.
- Model auto-loads when language changed.

---

## Feature — Two-way communication (text-to-sign)

Display animated sign illustrations for the hearing person's response.

- Type text → the system displays the corresponding sign language illustrations.
- Pre-rendered sign dictionary: images or animated GIFs for each sign.
- Useful in kiosk mode for two-way communication at service desks.
- Toggle: `TEXT_TO_SIGN_ENABLED=true/false`.

---

## Feature — Confidence indicator

Live bar showing recognition confidence per sign.

- Confidence bar displayed next to the recognized sign label.
- If confidence < threshold → prompt user: "Please sign again more clearly."
- Color-coded: green (high), yellow (medium), red (low).

---

## Feature — TTS audio output (Piper)

Speak the recognized text aloud.

- Uses Piper TTS for fast local synthesis.
- Each completed sentence is spoken through the speaker.
- Multi-language TTS voices match the sign language (English TTS for ASL, German for DGS, etc.).
- Toggle: `TTS_ENABLED=true/false`.

---

## Feature — Learning/training mode

Practice sign language with the Pi as a tutor.

- The system shows a word → the user signs it → the Pi grades correctness.
- Progress tracking: which signs mastered, which need practice.
- Difficulty levels: alphabet → common words → phrases → sentences.
- Data collection: optionally save hand landmarks for model retraining.
- Toggle: `LEARNING_MODE_ENABLED=true/false`.

---

## Feature — Kiosk mode

Full-screen, touch-friendly interface for public deployment.

- Large fonts, high contrast, minimal UI.
- Auto-reset after `KIOSK_TIMEOUT_SEC` seconds of inactivity.
- No login required in kiosk mode (read-only, no settings access).
- Two panels: camera feed (left) + recognized text (right).
- Toggle: `KIOSK_MODE=true/false`.

---

## Feature — Web dashboard

| Page | Description |
|---|---|
| **Dashboard** | Live camera feed with hand skeleton overlay, recognized signs, sentence builder, confidence bar |
| **Learning** | Practice mode: sign prompts, grading, progress tracking |
| **Kiosk** | Full-screen two-panel interface (camera + text) |
| **Settings** | Sign language selector, model management, TTS config, camera settings, kiosk config |

---

## Authentication

- Session-based with bcrypt hashing.
- Rate limiting: 10 attempts / 15 min.
- Session expiry: 24 hours.
- Kiosk mode bypasses login (read-only access).

---

## How to deploy to Raspberry Pi

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/SignLanguage
```

---

## How to run on the Raspberry Pi

```bash
ssh rasp-pi
cd /home/pi/Projects/SignLanguage
nano .env
sudo bash scripts/setup-camera.sh
bash scripts/download-models.sh
source venv/bin/activate
python app.py
```

Access: `http://192.168.216.90:5000`

**systemd service:**

```ini
[Unit]
Description=Sign Language Translator
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/SignLanguage
ExecStart=/home/pi/Projects/SignLanguage/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

---

## Security notes

- Change the default password immediately.
- Generate a strong `SESSION_SECRET`.
- `.env` in `.gitignore`, `chmod 600 .env`.
- Camera feed is local only (no cloud).
- Kiosk mode has no admin access.
- See [docs/threat_model.md](docs/threat_model.md).

---

## Troubleshooting

| Problem | Solution |
|---|---|
| No hand detected | Ensure good lighting. Camera must see full hand. Distance: 30–60 cm. |
| Low accuracy | Increase `CONFIDENCE_THRESHOLD`. Use better lighting. Retrain model with more data. |
| Slow FPS | Reduce resolution. Use Pi 5. Close other processes. |
| Wrong sign language | Change `SIGN_LANGUAGE` in `.env` or Settings page. |
| TTS not working | Check speaker: `aplay -l`. Enable TTS: `TTS_ENABLED=true`. |
| MediaPipe not installing | Install deps: `sudo apt install libgl1-mesa-glx`. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification.
- See [task.md](task.md) for the engineering checklist.
- See [implementation_plan.md](implementation_plan.md) for the phased implementation guide.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model.
