# Multi-Language Visual-Audio Translator

A dual-mode translation station for Raspberry Pi: **Visual mode** captures text from documents and signs via Pi Camera → Tesseract/PaddleOCR extracts text → local LLM translates and summarizes → output displayed on screen + spoken via Piper TTS. **Audio mode** captures speech via microphone → Whisper STT → LLM translates → displayed + spoken in the target language. Both modes operate from a single dark-themed Flask web dashboard with real-time SocketIO updates. Includes **Conversation mode** for two people speaking different languages — each hears the other's words translated into their own language. Designed for airports, hospitals, logistics centers, and anywhere foreigners need to communicate across language barriers.

---

**If you find this project useful, consider supporting development:**

**BTC:** `bc1q...`

---

## Table of Contents

- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Libraries & Dependencies](#libraries--dependencies)
- [Quickstart](#quickstart)
- [Environment Configuration](#environment-configuration)
- [System Overview](#system-overview)
- [Features](#features)
  - [Visual Mode (Camera → OCR → Translate)](#visual-mode-camera--ocr--translate)
  - [Audio Mode (Microphone → STT → Translate)](#audio-mode-microphone--stt--translate)
  - [Conversation Mode](#conversation-mode)
  - [Document Mode](#document-mode)
  - [Phrase Book](#phrase-book)
  - [Glossary Support](#glossary-support)
  - [Subtitle Overlay](#subtitle-overlay)
  - [TTS Auto-Play Toggle](#tts-auto-play-toggle)
  - [Offline Language Packs](#offline-language-packs)
  - [Web Dashboard](#web-dashboard)
- [Supported Languages](#supported-languages)
- [Authentication](#authentication)
- [Deployment](#deployment)
- [Running the Service](#running-the-service)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
Multi-Language Visual-Audio Translator/
├── README.md                       # This file
├── TSD.md                          # Technical Specification Document
├── task.md                         # Development task checklist
├── implementation_plan.md          # Phased implementation guide
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Project metadata
├── .env.example                    # Environment variable template
├── src/
│   ├── __init__.py
│   ├── app.py                      # Flask app factory & SocketIO init
│   ├── ocr_engine.py               # Tesseract / PaddleOCR wrapper
│   ├── stt_engine.py               # Whisper STT wrapper
│   ├── tts_engine.py               # Piper TTS wrapper
│   ├── translator.py               # LLM-based translation (llama-cpp)
│   ├── camera.py                   # Pi Camera capture & streaming
│   ├── audio.py                    # Microphone capture & playback
│   ├── conversation.py             # Conversation mode controller
│   ├── document.py                 # Document mode (PDF/image → OCR)
│   ├── phrasebook.py               # Pre-loaded phrase book manager
│   ├── glossary.py                 # Domain-specific glossary loader
│   ├── subtitle.py                 # Subtitle overlay on camera feed
│   ├── database.py                 # SQLite DB models & helpers
│   ├── auth.py                     # bcrypt auth & session management
│   ├── config.py                   # .env loader & config dataclass
│   └── utils.py                    # Shared utilities
├── templates/
│   ├── base.html                   # Dark theme layout
│   ├── login.html                  # Login page
│   ├── dashboard.html              # Main dashboard (mode selector)
│   ├── visual.html                 # Visual mode page
│   ├── audio.html                  # Audio mode page
│   ├── conversation.html           # Conversation mode page
│   ├── document.html               # Document upload & translation page
│   ├── phrasebook.html             # Phrase book browser
│   └── settings.html               # Runtime settings panel
├── static/
│   ├── css/
│   │   └── style.css               # Dark theme styles
│   └── js/
│       ├── dashboard.js            # SocketIO client & mode switching
│       ├── visual.js               # Visual mode UI logic
│       ├── audio.js                # Audio mode UI logic
│       ├── conversation.js         # Conversation mode UI logic
│       └── document.js             # Document upload handling
├── data/
│   ├── models/                     # Offline LLM, Whisper, Piper models
│   ├── phrasebooks/                # JSON phrase book files per language pair
│   ├── glossaries/                 # Domain glossary CSV/JSON files
│   └── languages/                  # Tesseract language packs
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures & mock helpers
│   ├── test_ocr.py                 # OCR engine tests
│   ├── test_stt.py                 # STT engine tests
│   ├── test_tts.py                 # TTS engine tests
│   ├── test_translator.py          # Translation logic tests
│   ├── test_conversation.py        # Conversation mode tests
│   ├── test_document.py            # Document mode tests
│   ├── test_phrasebook.py          # Phrase book tests
│   ├── test_glossary.py            # Glossary tests
│   ├── test_auth.py                # Auth & session tests
│   └── test_api.py                 # Dashboard API endpoint tests
├── deploy/
│   └── deploy_to_pi.sh             # rsync deploy script (rasp-pi)
├── scripts/
│   ├── download_models.sh          # Download all offline models
│   └── install_deps.sh             # OS-level dependency installer
└── docs/
    └── threat_model.md             # Security threat model
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (8GB) or Pi 5 | Yes | 8GB RAM recommended for local LLM inference |
| Pi Camera Module v3 | Yes | Visual mode + subtitle overlay |
| USB Microphone | Yes | Audio mode + conversation mode |
| Speaker (3.5mm or USB) | Yes | TTS audio output |
| MicroSD card (64GB+) | Yes | OS + offline language models |
| Power supply | Yes | 5V/3A for Pi 4, 5V/5A for Pi 5 |
| Touchscreen display (optional) | No | For kiosk deployment |

> **Important:** 8GB RAM is recommended for running Whisper + LLM + TTS concurrently. 4GB works for lighter models but may require sequential processing.

---

## Budget

| Item | Estimated Cost |
|---|---|
| Pi Camera Module v3 | $25–30 |
| USB Microphone | $8–15 |
| Speaker (3.5mm / USB) | $5–10 |
| **Total** | **~$38–55** |

*(Assumes you already have a Raspberry Pi, SD card, and power supply.)*

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| Flask | Web framework |
| Flask-SocketIO | Real-time WebSocket communication |
| eventlet | Async worker for SocketIO |
| pytesseract | OCR via Tesseract |
| PaddleOCR (optional) | Alternative high-accuracy OCR engine |
| whispercpp | Speech-to-text (Whisper.cpp bindings) |
| llama-cpp-python | Local LLM inference for translation |
| piper-tts | Offline text-to-speech |
| opencv-python-headless | Camera capture & image processing |
| pyaudio | Microphone capture & speaker playback |
| Pillow | Image manipulation |
| PyMuPDF (fitz) | PDF text and image extraction |
| bcrypt | Password hashing |
| python-dotenv | `.env` configuration loader |
| Jinja2 | HTML templating (bundled with Flask) |
| gunicorn | Production WSGI server |
| pytest / pytest-cov | Testing framework |

Install all dependencies:

```bash
pip install -r requirements.txt
```

OS-level dependencies (run on the Pi):

```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-deu tesseract-ocr-fra \
    tesseract-ocr-ita tesseract-ocr-spa tesseract-ocr-por tesseract-ocr-nld \
    tesseract-ocr-pol tesseract-ocr-rus tesseract-ocr-chi-sim tesseract-ocr-ara \
    portaudio19-dev python3-venv python3-dev libcamera-dev
```

---

## Quickstart

```bash
# 1. Clone and enter project
cd Multi-Language\ Visual-Audio\ Translator/

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env
nano .env   # Set ADMIN_PASSWORD_HASH, SECRET_KEY, language preferences

# 5. Download offline models
bash scripts/download_models.sh

# 6. Run the application
python -m src.app
```

Open `http://<pi-ip>:5000` in your browser. Log in with your configured admin credentials.

---

## Environment Configuration

All features are toggled via `.env`. See `.env.example` for the full reference with defaults and documentation. Key sections:

| Section | Key Variables |
|---|---|
| Flask & Security | `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` |
| Database | `DB_PATH` |
| Visual Mode | `ENABLE_VISUAL_MODE`, `OCR_ENGINE`, `OCR_LANGUAGES` |
| Audio Mode | `ENABLE_AUDIO_MODE`, `WHISPER_MODEL_PATH`, `WHISPER_MODEL_SIZE` |
| Translation | `ENABLE_TRANSLATION`, `LLM_MODEL_PATH`, `DEFAULT_SOURCE_LANG`, `DEFAULT_TARGET_LANG` |
| TTS | `ENABLE_TTS`, `TTS_AUTO_PLAY`, `PIPER_MODEL_PATH` |
| Conversation Mode | `ENABLE_CONVERSATION_MODE` |
| Document Mode | `ENABLE_DOCUMENT_MODE`, `MAX_UPLOAD_SIZE_MB` |
| Phrase Book | `ENABLE_PHRASEBOOK`, `PHRASEBOOK_DIR` |
| Glossary | `ENABLE_GLOSSARY`, `GLOSSARY_DIR` |
| Subtitle Overlay | `ENABLE_SUBTITLE_OVERLAY` |
| Dashboard | `DASHBOARD_HOST`, `DASHBOARD_PORT`, `SESSION_EXPIRY_HOURS` |
| Development | `MOCK_MODE`, `LOG_LEVEL` |

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Raspberry Pi                                    │
│                                                                         │
│  ┌──────────────┐    ┌─────────────────┐    ┌────────────────────────┐  │
│  │ Pi Camera    │───>│  OCR Engine     │───>│  LLM Translator        │  │
│  │ Module v3    │    │  (Tesseract /   │    │  (llama-cpp-python)    │  │
│  └──────────────┘    │  PaddleOCR)     │    │  - Translate           │  │
│                      └─────────────────┘    │  - Summarize           │  │
│  ┌──────────────┐    ┌─────────────────┐    │  - Glossary-aware      │  │
│  │ USB          │───>│  STT Engine     │───>└──────────┬─────────────┘  │
│  │ Microphone   │    │  (Whisper.cpp)  │               │                │
│  └──────────────┘    └─────────────────┘               │                │
│                                                        │                │
│                      ┌─────────────────┐    ┌──────────▼─────────────┐  │
│                      │  Piper TTS      │<───│  Output Controller     │  │
│  ┌──────────────┐    │  Engine         │    │  - Display text        │  │
│  │ Speaker      │<───│                 │    │  - Speak translation   │  │
│  └──────────────┘    └─────────────────┘    │  - Subtitle overlay    │  │
│                                              └──────────┬─────────────┘  │
│                                                         │                │
│  ┌──────────────────────────────────────────────────────▼─────────────┐  │
│  │            SQLite Database                                         │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐               │  │
│  │  │translations  │ │sessions      │ │glossaries   │               │  │
│  │  └──────────────┘ └──────────────┘ └─────────────┘               │  │
│  │  ┌──────────────┐ ┌──────────────┐                               │  │
│  │  │phrasebooks   │ │settings      │                               │  │
│  │  └──────────────┘ └──────────────┘                               │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Flask + SocketIO Web Dashboard                                    │  │
│  │  - bcrypt auth (rate limit 10/15min, 24h session)                 │  │
│  │  - Dark theme, mode selector (Visual / Audio / Conversation)      │  │
│  │  - Real-time translation display + TTS controls                   │  │
│  │  - Document upload, phrase book browser, glossary manager         │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### Visual Mode (Camera → OCR → Translate)

Captures an image from the Pi Camera Module v3, runs OCR via Tesseract or PaddleOCR to extract text, sends text to the local LLM for translation, and displays the result on the dashboard. Optionally speaks the translation aloud via Piper TTS. Ideal for reading signs, menus, forms, and documents in foreign languages.

- Toggle: `ENABLE_VISUAL_MODE=true`
- Configurable OCR engine: `OCR_ENGINE=tesseract` or `OCR_ENGINE=paddleocr`
- Multi-language OCR: `OCR_LANGUAGES=eng+deu+fra`

### Audio Mode (Microphone → STT → Translate)

Records speech from the USB microphone, transcribes using Whisper.cpp locally, translates via LLM, and displays + speaks the result. Works fully offline. Designed for real-time spoken translation.

- Toggle: `ENABLE_AUDIO_MODE=true`
- Whisper model size: `WHISPER_MODEL_SIZE=base` (tiny/base/small/medium)

### Conversation Mode

Enables two speakers with different languages to converse in real time. Speaker A talks → Whisper transcribes → LLM translates to Speaker B's language → TTS speaks. Then Speaker B responds and the cycle reverses. Turn-based with push-to-talk or voice activity detection.

- Toggle: `ENABLE_CONVERSATION_MODE=true`
- Configurable language pair: `CONVERSATION_LANG_A`, `CONVERSATION_LANG_B`

### Document Mode

Upload a photo or PDF document. PyMuPDF extracts pages, OCR runs on each page, and the LLM provides a structured translation of the full document. Supports multi-page documents.

- Toggle: `ENABLE_DOCUMENT_MODE=true`
- Max upload size: `MAX_UPLOAD_SIZE_MB=20`
- Supported formats: JPEG, PNG, PDF

### Phrase Book

Pre-loaded common travel phrases for each supported language pair. Browse by category (greetings, directions, medical, legal, food, transport). Each phrase shows the original text, translation, and a TTS play button.

- Toggle: `ENABLE_PHRASEBOOK=true`
- Data directory: `PHRASEBOOK_DIR=data/phrasebooks/`
- JSON files per language pair (e.g., `en_de.json`, `en_fr.json`)

### Glossary Support

Upload domain-specific glossary files (CSV/JSON) for medical, legal, or logistics terminology. The LLM uses the glossary during translation to ensure correct domain-specific terms.

- Toggle: `ENABLE_GLOSSARY=true`
- Data directory: `GLOSSARY_DIR=data/glossaries/`
- Format: CSV with `source_term,target_term` columns or JSON

### Subtitle Overlay

Live camera mode with translated text overlaid directly on detected text regions in the video feed. OpenCV detects text bounding boxes, OCR extracts text, LLM translates, and the translated text is rendered over the original.

- Toggle: `ENABLE_SUBTITLE_OVERLAY=true`
- Requires visual mode enabled

### TTS Auto-Play Toggle

Choose whether translations are automatically spoken aloud or only displayed as text. Per-mode toggle available from the dashboard.

- Toggle: `TTS_AUTO_PLAY=true`

### Offline Language Packs

All models (Whisper, LLM, Piper TTS, Tesseract language data) are stored locally. No internet connection required after initial setup. Download models once via `scripts/download_models.sh`.

### Web Dashboard

Dark-themed Flask + SocketIO dashboard with:
- Mode selector (Visual / Audio / Conversation / Document)
- Real-time translation display with source and target text panels
- Language pair selector dropdown
- TTS play/stop controls
- Translation history log
- Phrase book browser
- Glossary management
- Settings panel

---

## Supported Languages

| Code | Language |
|---|---|
| EN | English |
| DE | German |
| FR | French |
| IT | Italian |
| ES | Spanish |
| PT | Portuguese |
| NL | Dutch |
| PL | Polish |
| RU | Russian |
| ZH | Chinese (Simplified) |
| AR | Arabic |

> Language support depends on available Tesseract data, Whisper model, Piper TTS voices, and LLM capability. Additional languages can be added by downloading the corresponding model files.

---

## Authentication

- **bcrypt** hashed admin password stored in `.env` as `ADMIN_PASSWORD_HASH`
- Rate limiting: **10 login attempts per 15 minutes** per IP
- Session expiry: **24 hours**
- All dashboard routes protected by `@login_required` decorator
- CSRF tokens on all forms
- Secure cookie flags (`HttpOnly`, `SameSite`)

Generate a password hash:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```

---

## Deployment

### Deploy to Raspberry Pi

```bash
bash deploy/deploy_to_pi.sh
```

This uses `rsync` to push files to `rasp-pi` (pi@192.168.216.90), excluding `.venv`, `__pycache__`, `.git`, and `data/models/` (models should be downloaded directly on the Pi).

### systemd Service

```ini
[Unit]
Description=Multi-Language Visual-Audio Translator
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/visual-audio-translator
EnvironmentFile=/home/pi/visual-audio-translator/.env
ExecStart=/home/pi/visual-audio-translator/.venv/bin/python -m src.app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo cp visual-audio-translator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable visual-audio-translator
sudo systemctl start visual-audio-translator
sudo journalctl -u visual-audio-translator -f
```

---

## Running the Service

```bash
# Development
python -m src.app

# Production
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 'src.app:create_app()'
```

---

## Security Notes

- Bind dashboard to LAN only (`DASHBOARD_HOST=0.0.0.0` with firewall rules)
- Use strong `SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_hex(32))"`
- Set file permissions on `.env` to `600` (owner read/write only)
- Uploaded documents are processed in memory and not stored permanently
- All database queries use parameterized statements
- Rate limiting protects against brute-force login attempts
- No external API calls — all processing runs locally on the Pi

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| Camera not detected | libcamera not configured | Run `sudo raspi-config` → Interface → Camera → Enable |
| OCR returns empty text | Wrong language pack | Install Tesseract language: `sudo apt install tesseract-ocr-<lang>` |
| Whisper model fails to load | Insufficient RAM | Use smaller model (`WHISPER_MODEL_SIZE=tiny`) or add swap |
| TTS no audio output | Wrong audio device | Check `aplay -l`, set `AUDIO_OUTPUT_DEVICE` in `.env` |
| LLM translation slow | Model too large for Pi | Use quantized model (Q4_K_M) or smaller parameter count |
| Microphone not working | Permission or device issue | Check `arecord -l`, ensure user is in `audio` group |
| Upload fails | File too large | Increase `MAX_UPLOAD_SIZE_MB` in `.env` |
| Login rate limited | Too many attempts | Wait 15 minutes or restart the service |
| SocketIO disconnects | eventlet timeout | Check `LOG_LEVEL=DEBUG` for connection errors |
| PDF extraction blank | Scanned PDF (image-only) | Document mode falls back to OCR on embedded images |

---

## Where to Next

- Add more language pairs by downloading additional Tesseract data and Piper voices
- Build a kiosk mode with touchscreen-optimized layout
- Add translation quality scoring and user feedback
- Integrate external translation APIs as fallback (DeepL, Google Translate)
- Add multi-user support with per-user language preferences
- Implement translation memory (TM) for repeated phrases
- Build a mobile-friendly responsive dashboard variant
