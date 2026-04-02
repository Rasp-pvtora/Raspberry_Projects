# LLM-Powered Voice Assistant with Physical Feedback

**Version 2** of the [Set Up AI-Powered Voice Service](../Set%20Up%20AI-Powered%20Voice%20Service/README.md). Instead of just talking, this assistant controls hardware. When you say "I'm leaving," the Pi uses Ollama (running Llama 3 locally) to understand the intent and triggers GPIOs: lock the door relay, turn off lights relay, arm the alarm. Context-aware smart home control that understands natural language instead of rigid commands. Includes Wyoming Protocol for multi-room voice satellites.

🪙 **Donations are Welcome!**
If you find this project helpful, you can support my work with a small donation.
₿ Bitcoin donation: `bc1q...`

---

## v1 vs v2 — What Changed

This project is a ground-up evolution of the original AI-Powered Voice Service. The core voice pipeline remains (wake word → STT → LLM → TTS), but v2 adds a full intent-to-action layer with physical hardware feedback.

| Aspect | v1 (Voice Service) | v2 (Physical Feedback) |
|---|---|---|
| **LLM engine** | llama.cpp (TinyLlama) | Ollama (Llama 3 / Phi-3) |
| **Primary purpose** | Voice Q&A, chat | Smart home intent control |
| **GPIO integration** | Optional skill | Core feature |
| **Routines** | None | "I'm leaving" → lock + lights off + alarm on |
| **Intent system** | None | LLM → intent parser → action executor |
| **Physical feedback** | None | LED confirmation, buzzer, relay sounds |
| **Context memory** | Per-session | Persistent (remembers preferences) |
| **Web framework** | FastAPI + WebSocket | Flask + Flask-SocketIO |
| **Multi-room** | Wyoming optional | Wyoming first-class with Pi Zero satellites |
| **Undo support** | None | "Cancel that" reverses last action within 10 sec |
| **Scheduled actions** | None | Cron-style routines ("Turn off lights at 11 PM") |
| **Guest mode** | None | Limited voice access per user |
| **Emotion detection** | None | Stress/urgency → emergency routine |

**Why Ollama instead of llama.cpp?** Ollama provides a managed model runtime with hot-swapping, GPU acceleration, and a stable HTTP API. It handles model downloads, quantization, and context management — removing the need for manual GGUF file management.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Hardware Requirements](#hardware-requirements)
3. [Budget](#budget)
4. [Libraries and Dependencies](#libraries-and-dependencies)
5. [Quickstart — Laptop (Development)](#quickstart--laptop-development)
6. [Environment Configuration (.env)](#environment-configuration-env)
7. [Voice Pipeline Overview](#voice-pipeline-overview)
8. [Feature 1 — Intent Understanding](#feature-1--intent-understanding)
9. [Feature 2 — Routine Engine](#feature-2--routine-engine)
10. [Feature 3 — GPIO Physical Feedback](#feature-3--gpio-physical-feedback)
11. [Feature 4 — Multi-Room Satellites](#feature-4--multi-room-satellites)
12. [Feature 5 — Sensor Feedback Loop](#feature-5--sensor-feedback-loop)
13. [Feature 6 — Confidence Scoring & Confirmation](#feature-6--confidence-scoring--confirmation)
14. [Feature 7 — Guest Mode](#feature-7--guest-mode)
15. [Feature 8 — Scheduled Routines](#feature-8--scheduled-routines)
16. [Feature 9 — Emotion & Urgency Detection](#feature-9--emotion--urgency-detection)
17. [Feature 10 — Undo Command](#feature-10--undo-command)
18. [Feature 11 — Persistent Context Memory](#feature-11--persistent-context-memory)
19. [Feature 12 — Web Dashboard](#feature-12--web-dashboard)
20. [Authentication & Security](#authentication--security)
21. [Deployment](#deployment)
22. [Running with systemd](#running-with-systemd)
23. [Security Notes](#security-notes)
24. [Troubleshooting](#troubleshooting)
25. [Where to Next](#where-to-next)

---

## Project Structure

```
LLM-Powered Voice Assistant with Physical Feedback/
├── README.md                       # This file
├── TSD.md                          # Technical specification document
├── task.md                         # Task checklist by phase
├── implementation_plan.md          # Step-by-step implementation guide
├── requirements.txt                # Python dependencies
├── .env.default                    # Environment variable template
├── .gitignore                      # Git ignore rules
├── app.py                          # Flask + SocketIO entry point
├── config.py                       # Configuration loader (.env)
├── auth.py                         # Authentication (bcrypt, sessions)
├── intent_engine.py                # LLM intent parser (Ollama)
├── action_executor.py              # GPIO action executor
├── routine_engine.py               # Routine manager (sequences of actions)
├── gpio_controller.py              # GPIO abstraction (relays, LEDs, buzzer)
├── sensor_reader.py                # Sensor feedback (door, PIR, light)
├── context_memory.py               # Persistent context memory
├── scheduler.py                    # Scheduled routine runner
├── guest_manager.py                # Guest mode access control
├── emotion_detector.py             # Urgency/stress detection
├── undo_manager.py                 # Undo last action within timeout
├── database.py                     # SQLite database models & queries
├── deploy/
│   └── deploy_to_pi.sh             # SCP deploy script
├── models/
│   ├── whisper/                     # Whisper.cpp model files
│   └── wakeword/                    # OpenWakeWord models
├── src/
│   ├── pipeline/
│   │   ├── wakeword.py              # OpenWakeWord wake word detection
│   │   ├── stt.py                   # Whisper.cpp speech-to-text
│   │   ├── llm.py                   # Ollama LLM client
│   │   ├── tts.py                   # Piper TTS text-to-speech
│   │   └── audio_io.py              # Microphone input and speaker output
│   ├── wyoming/
│   │   ├── server.py                # Wyoming protocol server
│   │   ├── satellite.py             # Pi Zero satellite handler
│   │   └── discovery.py             # Multi-room device discovery
│   └── routes/
│       ├── auth.py                  # Login / logout routes
│       ├── dashboard.py             # Dashboard API
│       ├── routines.py              # Routine CRUD API
│       ├── gpio.py                  # GPIO status API
│       ├── settings.py              # Settings API
│       └── history.py               # Intent history API
├── static/
│   ├── css/
│   │   └── style.css                # Dark theme dashboard styles
│   └── js/
│       └── app.js                   # SocketIO client & UI logic
├── templates/
│   ├── base.html                    # Base template (dark theme)
│   ├── login.html                   # Login page
│   ├── dashboard.html               # Main dashboard
│   ├── routines.html                # Routine editor
│   ├── gpio.html                    # GPIO status & manual control
│   ├── history.html                 # Intent log history
│   └── settings.html                # Configuration page
├── tests/
│   ├── test_intent_engine.py
│   ├── test_action_executor.py
│   ├── test_routine_engine.py
│   ├── test_gpio_controller.py
│   ├── test_auth.py
│   └── test_database.py
└── data/
    └── voice_assistant.db           # SQLite database (auto-created)
```

---

## Hardware Requirements

| Component | Purpose | Required |
|---|---|---|
| Raspberry Pi 4 (8 GB) or Pi 5 | Main controller, runs Ollama + voice pipeline | Yes |
| USB microphone | Voice input | Yes |
| Speaker (3.5 mm or USB) | TTS audio output | Yes |
| Relay module (4-channel) | Door lock, lights, alarm control | Yes |
| LED indicators | Visual confirmation of actions | Yes |
| Buzzer (active/passive) | Audio confirmation beeps | Yes |
| Magnetic door sensor | Feedback: confirm door locked/unlocked | Recommended |
| PIR motion sensor | Presence detection, security routines | Recommended |
| Light sensor (LDR) | Ambient light detection for smart lighting | Optional |
| Solenoid lock | Physical door lock control | Optional |
| Pi Zero 2W + mic + speaker | Multi-room satellite (per room) | Optional |
| MicroSD 64 GB+ | OS + models + database | Yes |

---

## Budget

| Item | Cost (USD) |
|---|---|
| Relay module 4-channel | $4 – $6 |
| Magnetic door sensor | ~$3 |
| PIR motion sensor | ~$3 |
| Buzzer | ~$2 |
| LEDs (pack) | ~$2 |
| USB microphone | $8 – $15 |
| Speaker | $5 – $10 |
| Solenoid lock (optional) | $15 – $25 |
| **Total (minimum)** | **~$27 – $41** |
| **Total (with solenoid)** | **~$42 – $66** |

> Pi 4/5 board, power supply, and SD card costs not included (assumed already owned from v1).

---

## Libraries and Dependencies

| Library | Purpose |
|---|---|
| `flask` | Web framework |
| `flask-socketio` | Real-time WebSocket for dashboard |
| `ollama` | Python client for Ollama LLM |
| `openwakeword` | Wake word detection |
| `whispercpp` | Speech-to-text (Whisper.cpp bindings) |
| `piper-tts` | Text-to-speech |
| `pyaudio` | Audio capture and playback |
| `RPi.GPIO` | GPIO control (relays, LEDs, buzzer) |
| `wyoming` | Wyoming protocol for multi-room |
| `bcrypt` | Password hashing |
| `python-dotenv` | Environment variable loading |
| `schedule` | Cron-style scheduled routines |
| `jinja2` | HTML templating |
| `eventlet` | SocketIO async backend |

---

## Quickstart — Laptop (Development)

```bash
# Clone and enter project
cd "Smart & Security Projects/LLM-Powered Voice Assistant with Physical Feedback"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install Ollama (https://ollama.com)
# Pull default model
ollama pull llama3

# Copy environment template
cp .env.default .env
# Edit .env — set MOCK_GPIO=true for laptop dev

# Initialize database
python -c "from database import init_db; init_db()"

# Start the assistant
python app.py
# Dashboard: http://localhost:5000
```

> **Note:** On a laptop without GPIO, set `MOCK_GPIO=true` in `.env`. All GPIO actions will be logged but not executed.

---

## Environment Configuration (.env)

Copy `.env.default` to `.env` and customize. All features are toggleable:

```bash
# === Server ===
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=change-me-to-random-string

# === Authentication ===
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=$2b$12$...     # bcrypt hash
RATE_LIMIT_MAX=10
RATE_LIMIT_WINDOW_MIN=15
SESSION_EXPIRY_HOURS=24

# === Voice Pipeline ===
WAKEWORD_ENABLED=true
WAKEWORD_MODEL=hey_jarvis
WAKEWORD_SENSITIVITY=0.5
WHISPER_MODEL_SIZE=base
WHISPER_LANGUAGE=en
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
PIPER_VOICE=en_US-lessac-medium
TTS_ENABLED=true

# === Intent Engine ===
INTENT_ENABLED=true
INTENT_CONFIDENCE_THRESHOLD=0.7
INTENT_CONFIRM_BELOW_THRESHOLD=true

# === GPIO ===
GPIO_ENABLED=true
MOCK_GPIO=false
RELAY_DOOR_PIN=17
RELAY_LIGHTS_PIN=27
RELAY_ALARM_PIN=22
LED_CONFIRM_PIN=23
BUZZER_PIN=24

# === Sensors ===
SENSOR_ENABLED=true
DOOR_SENSOR_PIN=25
PIR_SENSOR_PIN=5
LIGHT_SENSOR_PIN=6

# === Routines ===
ROUTINE_ENABLED=true
SCHEDULER_ENABLED=true

# === Multi-Room ===
WYOMING_ENABLED=false
WYOMING_PORT=10400

# === Context Memory ===
CONTEXT_MEMORY_ENABLED=true
CONTEXT_MEMORY_MAX_ENTRIES=500

# === Guest Mode ===
GUEST_MODE_ENABLED=false
GUEST_ALLOWED_INTENTS=lights,temperature,time

# === Emotion Detection ===
EMOTION_DETECTION_ENABLED=false
EMERGENCY_ROUTINE=emergency

# === Undo ===
UNDO_ENABLED=true
UNDO_TIMEOUT_SEC=10

# === Database ===
DATABASE_PATH=data/voice_assistant.db

# === Audio ===
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default
```

---

## Voice Pipeline Overview

```
 Microphone
     │
     ▼
 OpenWakeWord (wake word detection)
     │  "Hey Jarvis"
     ▼
 Whisper.cpp (speech-to-text)
     │  "I'm leaving the house"
     ▼
 Ollama LLM (intent understanding)
     │  { intent: "leaving_routine", confidence: 0.92 }
     ▼
 Intent Router
     │
     ├── confidence ≥ threshold → Action Executor
     │                               │
     │                               ├── Relay: lock door ✓
     │                               ├── Relay: lights off ✓
     │                               ├── Relay: alarm on ✓
     │                               ├── LED: green flash ✓
     │                               └── Buzzer: confirm beep ✓
     │
     └── confidence < threshold → Piper TTS → "Did you mean lock up and leave?"
                                      │
                                      ▼
                                   Speaker
```

The key difference from v1: after Ollama processes the text, instead of generating a conversational reply, the LLM outputs a **structured intent** that maps to physical hardware actions. Piper TTS provides verbal confirmation: _"Done. Door locked, lights off, alarm armed."_

---

## Feature 1 — Intent Understanding

The LLM parses natural language into structured intents:

```
User:   "I'm heading out"
LLM:    { "intent": "leaving", "confidence": 0.94, "entities": {} }
Action: Execute "leaving" routine → lock door + lights off + arm alarm
```

```
User:   "Turn on the living room lights"
LLM:    { "intent": "lights_on", "confidence": 0.89, "entities": {"room": "living_room"} }
Action: Set RELAY_LIGHTS_PIN HIGH
```

The intent system uses a structured JSON output format with the Ollama API. The LLM's system prompt contains the list of available intents and their descriptions, updated dynamically based on configured routines and GPIO mappings.

---

## Feature 2 — Routine Engine

Routines are named sequences of GPIO actions, editable from the dashboard:

| Routine Name | Actions |
|---|---|
| **Leaving** | Lock door → lights off → alarm on → buzzer beep |
| **Goodnight** | Lock door → lights off → night light on (dim LED) |
| **Movie time** | Lights off → lamp on (relay 3) |
| **Emergency** | All lights on → alarm on → unlock door |
| **Good morning** | Alarm off → lights on → unlock door |

Each action in a routine executes sequentially with a configurable delay (default 500 ms between steps). Routines are stored in the SQLite database and can be created, edited, and deleted from the web dashboard.

---

## Feature 3 — GPIO Physical Feedback

Every hardware action provides multi-modal confirmation:

- **Relay click:** The physical relay click sound confirms the action.
- **LED flash:** Green LED blinks once per completed action.
- **Buzzer:** Short beep for single action, melody for completed routine.
- **Verbal:** Piper TTS speaks "Door locked. Lights off. Alarm armed."

---

## Feature 4 — Multi-Room Satellites

Using the Wyoming protocol, Pi Zero 2W devices act as voice satellites:

```
 ┌──────────────────────────────────┐
 │  Pi 4/5 (Main Hub)               │
 │  Ollama + Whisper + Piper + GPIO │
 │  Wyoming Server (port 10400)     │
 └──────────┬───────────────────────┘
            │ Wyoming TCP
    ┌───────┼───────────┐
    │       │           │
 ┌──▼──┐ ┌──▼──┐ ┌──────▼──────┐
 │Zero │ │Zero │ │ Zero        │
 │Room1│ │Room2│ │ Garage      │
 │Mic+ │ │Mic+ │ │ Mic+Speaker │
 │Spkr │ │Spkr │ │ +PIR sensor │
 └─────┘ └─────┘ └─────────────┘
```

Each satellite runs OpenWakeWord locally for instant wake detection. Audio is streamed to the main hub for processing. The hub knows which room the command came from and can apply room-aware logic.

---

## Feature 5 — Sensor Feedback Loop

After executing an action, the system reads sensors to confirm:

```
Action:   Lock door (relay ON)
Sensor:   Magnetic door sensor reads CLOSED
Feedback: "Door locked ✓"

Action:   Lights off (relay OFF)
Sensor:   Light sensor reads LOW
Feedback: "Lights off ✓"
```

If a sensor reading contradicts the expected state (e.g., door sensor reads OPEN after lock command), the system alerts the user: _"Warning: door sensor still reads open. Please check manually."_

---

## Feature 6 — Confidence Scoring & Confirmation

The LLM returns a confidence score with each intent. Below the threshold (`INTENT_CONFIDENCE_THRESHOLD`, default 0.7):

```
User:   "mmph the door"
LLM:    { "intent": "lock_door", "confidence": 0.45 }
TTS:    "Did you mean lock the door? Say yes to confirm."
User:   "Yes"
Action: Lock door
```

This prevents accidental execution of misunderstood commands.

---

## Feature 7 — Guest Mode

When `GUEST_MODE_ENABLED=true`, unrecognized voices (or a specific wake word like "Hey Guest") get limited access:

- **Allowed:** Lights, temperature queries, time
- **Blocked:** Door locks, alarm, routines, settings
- **Configurable:** `GUEST_ALLOWED_INTENTS` comma-separated list

---

## Feature 8 — Scheduled Routines

Voice-triggered or dashboard-configured schedules:

```
User:   "Turn off the lights at 11 PM"
System: Creates scheduled job → lights off at 23:00 daily
TTS:    "Got it. Lights will turn off at 11 PM every day."
```

The scheduler runs in a background thread using the `schedule` library. Scheduled jobs persist in the database and survive restarts.

---

## Feature 9 — Emotion & Urgency Detection

When `EMOTION_DETECTION_ENABLED=true`, the LLM analyzes the user's text for urgency indicators:

- **Stress keywords:** "help", "emergency", "hurry", "break in"
- **Urgency patterns:** Repeated commands, raised voice (amplitude analysis)
- **Action:** Triggers the `EMERGENCY_ROUTINE` (all lights on, alarm on, unlock doors for escape)

---

## Feature 10 — Undo Command

Within `UNDO_TIMEOUT_SEC` (default 10 seconds) of any action:

```
User:   "Cancel that" / "Undo" / "Never mind"
System: Reverses last action (re-reads GPIO states, flips them back)
TTS:    "Undone. Door unlocked, lights back on."
```

The undo stack stores the previous GPIO states before each action. Only the most recent action group can be undone.

---

## Feature 11 — Persistent Context Memory

The assistant remembers user preferences across sessions:

```
User:   "I like the lights dim when watching movies"
Memory: Stores { preference: "movie_lights", value: "dim" }

Next time:
User:   "Movie time"
System: Executes movie routine + sets lights to dim (remembered preference)
```

Context memory is stored in the SQLite database with a configurable max entry count (`CONTEXT_MEMORY_MAX_ENTRIES`). Oldest entries are pruned when the limit is reached.

---

## Feature 12 — Web Dashboard

Dark-themed Flask + SocketIO dashboard:

- **Dashboard page:** Live pipeline status, recent intents, GPIO states, sensor readings, system stats
- **Routines page:** Create/edit/delete routines with drag-and-drop action ordering
- **GPIO page:** Real-time GPIO pin states with manual toggle switches
- **History page:** Searchable intent log with timestamps, confidence scores, and action outcomes
- **Settings page:** All `.env` variables editable, model selection, audio device config

---

## Authentication & Security

- **bcrypt** password hashing with salted hash stored in `.env`
- **Rate limiting:** 10 login attempts per 15 minutes per IP
- **Session expiry:** 24 hours
- **CSRF protection** on all forms
- **Toggleable:** `AUTH_ENABLED=false` disables auth for local-only setups
- **Security headers:** CSP, X-Content-Type-Options, X-Frame-Options

---

## Deployment

```bash
# From your development machine
./deploy/deploy_to_pi.sh
```

The deploy script:
1. Syncs files to `rasp-pi` (SSH alias for `192.168.216.90`) via rsync
2. Creates/updates Python virtual environment
3. Installs dependencies
4. Copies `.env.default` to `.env` if not present
5. Installs and starts Ollama service
6. Pulls the configured LLM model
7. Restarts the systemd service

---

## Running with systemd

```bash
# On the Pi
sudo cp deploy/voice-assistant-v2.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable voice-assistant-v2
sudo systemctl start voice-assistant-v2

# Check status
sudo systemctl status voice-assistant-v2
journalctl -u voice-assistant-v2 -f
```

---

## Security Notes

- All processing is **100% local** — no cloud, no data exfiltration.
- Ollama runs locally; no API keys required.
- GPIO access requires explicit `GPIO_ENABLED=true`.
- The `.env` file contains credentials — set `chmod 600 .env` on the Pi.
- Wyoming port should be firewalled to the local network only.
- Guest mode restricts physical hardware access for unrecognized users.
- Intent confidence threshold prevents accidental actions from misheard commands.
- Undo command provides a safety net for incorrect actions.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Ollama not responding | Check `systemctl status ollama`; ensure model is pulled (`ollama list`) |
| GPIO permission denied | Run with `sudo` or add user to `gpio` group |
| No audio input | Check `arecord -l` for USB mic; set correct device in `.env` |
| Relay not clicking | Check wiring; verify pin number in `.env`; test with `gpio_controller.py` directly |
| Sensor reading wrong | Check pull-up/pull-down resistor configuration; verify pin assignment |
| Intent confidence always low | Try a larger model (`ollama pull llama3:8b`); refine system prompt |
| Wyoming satellites not connecting | Check firewall; verify `WYOMING_PORT` matches on hub and satellite |
| "Cancel that" not working | Must be within `UNDO_TIMEOUT_SEC` of last action |
| High latency | Reduce Whisper model size; use Pi 5 for faster inference |

---

## Where to Next

- **Home Assistant integration:** Expose intents as HA entities via Wyoming protocol.
- **Voice enrollment:** Speaker identification to distinguish household members.
- **Camera integration:** Combine with the [AI-Powered Security Camera](../AI-Powered%20Security%20Camera/README.md) for "Who's at the door?" queries.
- **Energy monitoring:** Track relay on-time for power consumption estimates.
- **Custom wake words:** Train personalized wake words with OpenWakeWord.
