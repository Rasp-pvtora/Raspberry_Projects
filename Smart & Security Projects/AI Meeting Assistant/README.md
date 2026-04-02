# AI Meeting Assistant

A fully local, privacy-first AI meeting transcription and summarization system for Raspberry Pi. Uses a high-quality USB microphone array and OpenAI's Whisper (tiny/base model via whisper.cpp) for real-time transcription. A local LLM (TinyLlama/Phi-3 via llama.cpp) generates meeting summaries and extracts action items. All processing happens on-device — no audio leaves the room. Designed for high-security corporate meetings where cloud-based AI is prohibited.

> **Privacy guarantee:** Zero network dependency. No audio, transcript, or summary ever leaves the device. One-click privacy wipe erases all traces of a meeting.

---

### Support This Project

If you find this project useful, consider supporting development:

**Bitcoin:** `bc1q...`

---

## Table of Contents

- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Libraries](#libraries)
- [Quickstart](#quickstart)
- [Environment Variables](#environment-variables)
- [System Overview](#system-overview)
- [Features](#features)
  - [Real-Time Transcription](#real-time-transcription)
  - [Speaker Diarization](#speaker-diarization)
  - [Live Transcript Display](#live-transcript-display)
  - [Action Item Extraction](#action-item-extraction)
  - [Meeting Summary Generation](#meeting-summary-generation)
  - [Meeting Summary Export](#meeting-summary-export)
  - [Keyword Highlighting](#keyword-highlighting)
  - [Multi-Language Transcription](#multi-language-transcription)
  - [Recording Archive](#recording-archive)
  - [Agenda Tracking](#agenda-tracking)
  - [Privacy Wipe](#privacy-wipe)
- [Authentication & Security](#authentication--security)
- [Deployment](#deployment)
- [Running with systemd](#running-with-systemd)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
AI Meeting Assistant/
├── README.md                   # This file
├── TSD.md                      # Technical specification document
├── task.md                     # Task checklist by phase
├── implementation_plan.md      # Step-by-step implementation guide
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── app.py                      # Flask application entry point
├── config.py                   # Configuration loader (.env)
├── auth.py                     # Authentication (bcrypt, sessions)
├── transcription.py            # Whisper.cpp transcription engine
├── diarization.py              # Speaker diarization module
├── summarizer.py               # LLM summary & action item extraction
├── audio.py                    # Audio capture & processing (PyAudio)
├── database.py                 # SQLite database models & queries
├── exporter.py                 # Markdown/PDF export
├── agenda.py                   # Agenda upload & tracking
├── privacy.py                  # Privacy wipe (secure delete)
├── deploy/
│   └── deploy_to_pi.sh         # SCP deploy script
├── models/
│   ├── whisper/                # Whisper.cpp model files (tiny/base)
│   └── llm/                    # TinyLlama/Phi-3 GGUF model files
├── static/
│   ├── css/
│   │   └── style.css           # Dark theme dashboard styles
│   └── js/
│       └── app.js              # SocketIO client & UI logic
├── templates/
│   ├── base.html               # Base template (dark theme)
│   ├── login.html              # Login page
│   ├── dashboard.html          # Main dashboard
│   ├── meeting.html            # Live meeting view
│   ├── archive.html            # Meeting archive & search
│   └── settings.html           # Settings page
├── data/
│   └── meetings.db             # SQLite database (auto-created)
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_transcription.py
    ├── test_diarization.py
    ├── test_summarizer.py
    ├── test_auth.py
    └── test_database.py
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (8 GB) / Pi 5 | **Yes** | 8 GB RAM strongly recommended for LLM inference |
| USB Microphone Array | **Yes** | ReSpeaker Mic Array v2.0 or Jabra Speak 410 |
| MicroSD Card (32 GB+) | **Yes** | Class 10 / A2 recommended for database I/O |
| Power Supply (5V 3A+) | **Yes** | Official Pi PSU recommended |
| HDMI Display / Tablet | Optional | For live transcript display in meeting room |
| Ethernet Cable | Optional | Wired connection for dashboard access on LAN |

---

## Budget

| Item | Cost |
|---|---|
| ReSpeaker Mic Array v2.0 | ~$25 |
| Jabra Speak 410 (alternative) | ~$80 |
| **Total** | **~$25–80** (Pi & SD card assumed owned) |

---

## Libraries

| Library | Purpose |
|---|---|
| `Flask` | Web dashboard framework |
| `Flask-SocketIO` | WebSocket support for live transcript |
| `whispercpp` | Python bindings for Whisper.cpp (speech-to-text) |
| `llama-cpp-python` | Python bindings for llama.cpp (LLM inference) |
| `pyannote-audio` | Speaker diarization (who is speaking) |
| `resemblyzer` | Lightweight alternative for speaker diarization |
| `pyaudio` | Audio capture from USB microphone |
| `numpy` | Audio signal processing |
| `reportlab` | PDF export for meeting summaries |
| `bcrypt` | Password hashing for authentication |
| `python-dotenv` | Load environment variables from `.env` |
| `Jinja2` | HTML templating (bundled with Flask) |

---

## Quickstart

### 1. Clone & Deploy

```bash
# From your development machine
scp -r . rasp-pi:~/ai-meeting-assistant/
ssh rasp-pi
cd ~/ai-meeting-assistant
```

### 2. System Dependencies

```bash
sudo apt update && sudo apt install -y \
  python3-pip python3-venv portaudio19-dev \
  libatlas-base-dev libopenblas-dev ffmpeg \
  cmake build-essential
```

### 3. Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Download Models

```bash
# Whisper tiny model (for Pi 4) or base model (for Pi 5)
mkdir -p models/whisper models/llm
wget -O models/whisper/ggml-tiny.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin

# TinyLlama for summarization (Q4_K_M quantized)
wget -O models/llm/tinyllama-1.1b-chat.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### 5. Configure

```bash
cp .env.example .env
nano .env    # Edit as needed — all features are toggleable
```

### 6. Initialize & Run

```bash
python app.py
# Dashboard: http://192.168.216.90:5000
```

---

## Environment Variables

All features are toggleable via `.env`. Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `change-me-in-production` | Flask session secret key |
| `FLASK_HOST` | `0.0.0.0` | Bind address |
| `FLASK_PORT` | `5000` | Bind port |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |
| `AUTH_ENABLED` | `true` | Enable bcrypt authentication |
| `AUTH_USERNAME` | `admin` | Dashboard login username |
| `AUTH_PASSWORD_HASH` | *(bcrypt hash)* | Bcrypt-hashed password |
| `SESSION_EXPIRY_HOURS` | `24` | Session expiry in hours |
| `RATE_LIMIT_MAX` | `10` | Max requests per rate-limit window |
| `RATE_LIMIT_WINDOW_MIN` | `15` | Rate-limit window in minutes |
| `TRANSCRIPTION_ENABLED` | `true` | Enable real-time transcription |
| `WHISPER_MODEL_PATH` | `models/whisper/ggml-tiny.bin` | Path to Whisper GGUF model |
| `WHISPER_MODEL_SIZE` | `tiny` | Whisper model size (`tiny` or `base`) |
| `WHISPER_LANGUAGE` | `en` | Transcription language (or `auto` for detection) |
| `DIARIZATION_ENABLED` | `false` | Enable speaker diarization |
| `DIARIZATION_BACKEND` | `resemblyzer` | Backend: `pyannote` or `resemblyzer` |
| `PYANNOTE_AUTH_TOKEN` | `` | HuggingFace token (if using pyannote) |
| `LLM_ENABLED` | `false` | Enable LLM summary & action extraction |
| `LLM_MODEL_PATH` | `models/llm/tinyllama-1.1b-chat.Q4_K_M.gguf` | Path to LLM GGUF model |
| `LLM_CONTEXT_LENGTH` | `2048` | LLM context window size |
| `LLM_THREADS` | `4` | CPU threads for LLM inference |
| `LIVE_DISPLAY_ENABLED` | `true` | Enable live transcript via WebSocket |
| `ACTION_ITEMS_ENABLED` | `false` | Enable action item extraction (requires LLM) |
| `SUMMARY_ENABLED` | `false` | Enable meeting summary generation (requires LLM) |
| `EXPORT_ENABLED` | `true` | Enable Markdown/PDF export |
| `KEYWORD_HIGHLIGHT_ENABLED` | `true` | Enable keyword highlighting in transcript |
| `KEYWORD_LIST` | `budget,deadline,action,decision` | Comma-separated highlight keywords |
| `ARCHIVE_ENABLED` | `true` | Enable recording archive with FTS |
| `AGENDA_TRACKING_ENABLED` | `false` | Enable agenda upload & tracking |
| `PRIVACY_WIPE_ENABLED` | `true` | Enable one-click privacy wipe |
| `AUDIO_DEVICE_INDEX` | `auto` | PyAudio device index (or `auto`) |
| `AUDIO_SAMPLE_RATE` | `16000` | Audio sample rate in Hz |
| `AUDIO_CHANNELS` | `1` | Audio channels (1 = mono) |
| `AUDIO_CHUNK_DURATION_SEC` | `5` | Chunk duration for streaming transcription |
| `DB_PATH` | `data/meetings.db` | SQLite database path |
| `MOCK_MODE` | `false` | Use mock audio/models for development |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        AI Meeting Assistant                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌───────────────┐    ┌────────────────────┐     │
│  │ USB Mic     │───▶│ Audio Capture  │───▶│ Whisper.cpp        │     │
│  │ Array       │    │ (PyAudio)      │    │ (Transcription)    │     │
│  └─────────────┘    └───────────────┘    └────────┬───────────┘     │
│                                                    │                 │
│                               ┌────────────────────┼──────────┐     │
│                               │                    │          │     │
│                               ▼                    ▼          ▼     │
│                    ┌──────────────┐    ┌──────────────┐  ┌───────┐ │
│                    │ Diarization  │    │ Live Display │  │SQLite │ │
│                    │ (Speaker ID) │    │ (WebSocket)  │  │Archive│ │
│                    └──────────────┘    └──────────────┘  └───────┘ │
│                                                                      │
│                    ┌──────────────────────────────────────┐         │
│                    │ LLM Engine (llama.cpp)               │         │
│                    │  ├─ Action Item Extraction           │         │
│                    │  ├─ Meeting Summary Generation       │         │
│                    │  └─ Keyword/Topic Detection          │         │
│                    └──────────────────────────────────────┘         │
│                                                                      │
│                    ┌──────────────────────────────────────┐         │
│                    │ Flask Dashboard (Dark Theme)         │         │
│                    │  ├─ Live Meeting View                │         │
│                    │  ├─ Archive & Search                 │         │
│                    │  ├─ Export (Markdown / PDF)          │         │
│                    │  ├─ Agenda Tracking                  │         │
│                    │  └─ Privacy Wipe                     │         │
│                    └──────────────────────────────────────┘         │
│                                                                      │
│                    ┌──────────────────────────────────────┐         │
│                    │ Auth: bcrypt | Rate Limit: 10/15min  │         │
│                    │ Session: 24h expiry | HTTPS ready    │         │
│                    └──────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Features

### Real-Time Transcription

Uses Whisper.cpp (tiny or base model) for on-device speech-to-text. Audio is captured in configurable chunks (`AUDIO_CHUNK_DURATION_SEC`) from the USB microphone and fed to Whisper for near real-time transcription. The tiny model runs comfortably on Pi 4; the base model is recommended for Pi 5.

- Toggle: `TRANSCRIPTION_ENABLED=true`
- Model: `WHISPER_MODEL_PATH`, `WHISPER_MODEL_SIZE`

### Speaker Diarization

Identifies who is speaking using voice embeddings. Supports two backends:

- **resemblyzer** — lightweight, no API key needed, good for ≤5 speakers
- **pyannote-audio** — more accurate, requires HuggingFace token

Each transcript segment is tagged with a speaker label (Speaker 1, Speaker 2, etc.). Speaker profiles can optionally be named in the dashboard.

- Toggle: `DIARIZATION_ENABLED=true`
- Backend: `DIARIZATION_BACKEND=resemblyzer|pyannote`

### Live Transcript Display

Streams the live transcript to any connected browser via Flask-SocketIO WebSocket. Connect an HDMI display or tablet in the meeting room to show a real-time scrolling transcript. Supports multiple simultaneous viewers.

- Toggle: `LIVE_DISPLAY_ENABLED=true`
- Endpoint: `ws://192.168.216.90:5000/socket.io`

### Action Item Extraction

After transcription, the local LLM parses the transcript to extract TODOs, decisions, follow-ups, and assignments. Results are stored in the `action_items` database table and displayed on the dashboard.

- Toggle: `ACTION_ITEMS_ENABLED=true` (requires `LLM_ENABLED=true`)

### Meeting Summary Generation

When a meeting ends, the LLM generates a concise summary including key discussion points, decisions made, and next steps. Summaries are stored alongside the transcript in the archive.

- Toggle: `SUMMARY_ENABLED=true` (requires `LLM_ENABLED=true`)

### Meeting Summary Export

Export meeting transcripts and summaries as:

- **Markdown** — clean, portable, version-controllable
- **PDF** — generated with ReportLab, suitable for email distribution

- Toggle: `EXPORT_ENABLED=true`

### Keyword Highlighting

Configurable keyword list for highlighting important terms in the live transcript and archive view. Useful for flagging project names, deadlines, budget numbers, and decision keywords.

- Toggle: `KEYWORD_HIGHLIGHT_ENABLED=true`
- Keywords: `KEYWORD_LIST=budget,deadline,action,decision`

### Multi-Language Transcription

Whisper supports 99 languages. Set the language code or use `auto` for automatic language detection. Mixed-language meetings are supported when set to `auto`.

- Config: `WHISPER_LANGUAGE=en` (or `auto`, `de`, `fr`, `ja`, etc.)

### Recording Archive

All meetings are stored in SQLite with full-text search (FTS5). Search across all transcripts by keyword, date range, speaker, or action item status. Archive view in the dashboard provides browse, search, and playback functionality.

- Toggle: `ARCHIVE_ENABLED=true`
- Database: `DB_PATH=data/meetings.db`

### Agenda Tracking

Upload a meeting agenda (text or Markdown) before the meeting. The system tracks which agenda items have been discussed based on keyword matching in the transcript. Dashboard shows a checklist view with discussed/pending status.

- Toggle: `AGENDA_TRACKING_ENABLED=true`

### Privacy Wipe

One-click secure deletion of all data associated with a specific meeting: audio recordings, transcripts, summaries, action items, and any exported files. Uses secure overwrite before deletion. Essential for classified or sensitive meetings.

- Toggle: `PRIVACY_WIPE_ENABLED=true`

---

## Authentication & Security

- **bcrypt password hashing** — passwords are never stored in plaintext
- **Rate limiting** — 10 requests per 15-minute window per IP (configurable)
- **Session management** — server-side sessions with 24-hour expiry
- **CSRF protection** — enabled on all form submissions
- **Auth toggle** — disable for trusted LAN environments (`AUTH_ENABLED=false`)

Generate a password hash:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```

Set the hash in `.env`:

```
AUTH_PASSWORD_HASH=$2b$12$...your-hash...
```

---

## Deployment

### Deploy via SCP

```bash
# From development machine
scp -r . rasp-pi:~/ai-meeting-assistant/
```

### Deploy Script

```bash
chmod +x deploy/deploy_to_pi.sh
./deploy/deploy_to_pi.sh
```

The deploy script:
1. Syncs project files to `rasp-pi` (192.168.216.90)
2. Installs/updates Python dependencies
3. Downloads models if not present
4. Restarts the systemd service

---

## Running with systemd

Create the service file:

```bash
sudo nano /etc/systemd/system/ai-meeting-assistant.service
```

```ini
[Unit]
Description=AI Meeting Assistant
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ai-meeting-assistant
Environment=PATH=/home/pi/ai-meeting-assistant/venv/bin:/usr/bin
ExecStart=/home/pi/ai-meeting-assistant/venv/bin/python app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-meeting-assistant
sudo systemctl start ai-meeting-assistant
sudo systemctl status ai-meeting-assistant
```

Access the dashboard: `http://192.168.216.90:5000`

---

## Security Notes

- **All processing is local.** No audio, transcript, or model data leaves the Raspberry Pi.
- **No internet required** after initial setup (model downloads).
- **USB microphone only** — no wireless audio to intercept.
- **SQLite database** is stored locally; encrypt the SD card for additional protection (`LUKS`).
- **Privacy wipe** securely overwrites data before deletion — not just `rm`.
- **Bind to LAN only** — do not expose port 5000 to the internet without a reverse proxy and TLS.
- **Update regularly** — `pip install --upgrade` and `sudo apt upgrade` for security patches.
- **Physical security** — lock the Pi in a secure location; anyone with SD card access has the data.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `No audio device found` | Check USB mic is connected: `arecord -l`. Set `AUDIO_DEVICE_INDEX` manually. |
| `Whisper model not found` | Verify `WHISPER_MODEL_PATH` points to a valid `.bin` file. Re-download if corrupted. |
| `LLM out of memory` | Use `tiny` Whisper model and reduce `LLM_CONTEXT_LENGTH`. Close other processes. |
| `WebSocket not connecting` | Check firewall allows port 5000. Verify `FLASK_HOST=0.0.0.0`. |
| `Transcription too slow` | Switch to `tiny` model. Increase `AUDIO_CHUNK_DURATION_SEC` to 10. |
| `Speaker diarization inaccurate` | Ensure mic array is centered. Try switching `DIARIZATION_BACKEND`. |
| `Permission denied on audio` | Add user to `audio` group: `sudo usermod -aG audio pi` |
| `Database locked` | Only one writer at a time with SQLite. Restart the service. |
| `bcrypt import error` | Install system dependency: `sudo apt install libffi-dev && pip install bcrypt` |
| `PDF export fails` | Install ReportLab: `pip install reportlab`. Check disk space. |

---

## Where to Next

- **Multi-room support** — run multiple instances on separate Pis, aggregate via central dashboard
- **Custom speaker enrollment** — register speaker voices for named identification
- **Email integration** — auto-send meeting summary to attendees after meeting ends
- **Calendar sync** — pull meeting metadata from CalDAV / Google Calendar
- **Ollama backend** — swap llama.cpp for Ollama for easier model management
- **GPU acceleration** — Coral USB accelerator or Pi 5 with AI HAT for faster inference
- **Real-time translation** — live subtitle translation to secondary language
- **Slack / Teams webhook** — post meeting summary to channel automatically
- **Voice commands** — "summarize so far", "mark action item" via wake word
- **Fine-tuned models** — train on your organization's vocabulary for better accuracy
