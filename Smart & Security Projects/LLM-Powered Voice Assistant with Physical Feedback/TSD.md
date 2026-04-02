# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for **LLM-Powered Voice Assistant with Physical Feedback** — Version 2 of the AI-Powered Voice Service.

---

## 1. Scope

This project builds a context-aware, hardware-controlling voice assistant on a Raspberry Pi. It combines a local voice pipeline (wake word → STT → LLM → TTS) with an intent-to-action system that controls physical hardware via GPIO. Instead of just conversational AI, the LLM parses natural language into structured intents that trigger relays, LEDs, buzzers, and sensors. Routines allow chained actions ("I'm leaving" → lock door + lights off + alarm on). All features are toggleable via `.env`.

**Key goals:**
- 100% local processing — no cloud, no accounts, no data harvesting.
- Natural language intent control — not rigid commands but flexible understanding.
- Physical feedback — every action confirmed via relay click, LED flash, buzzer beep, and verbal TTS.
- Routine engine — user-defined action sequences editable from the dashboard.
- Persistent context — remembers user preferences across sessions and reboots.
- Multi-room support — Pi Zero 2W satellites via Wyoming protocol.
- All features toggleable via `.env` flags.

---

## 2. Minimum Viable Features (MVP)

### 2.1 Voice Pipeline

| Stage | Component | Model/Tool | Description |
|---|---|---|---|
| **Wake word** | [OpenWakeWord](https://github.com/dscripka/openWakeWord) | Pre-trained models | Continuous listening for configurable wake phrase |
| **Speech-to-Text** | [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) | `tiny` / `base` / `small` | Converts spoken audio to text; runs on CPU |
| **LLM** | [Ollama](https://ollama.com) | Llama 3 / Phi-3 | Parses text into structured intents; runs locally |
| **Text-to-Speech** | [Piper TTS](https://github.com/rhasspy/piper) | 30+ language voices | Speaks action confirmations; real-time on Pi 4 |
| **Audio I/O** | PyAudio | USB mic + speaker | Audio capture and playback |
| **Orchestration** | Flask + Flask-SocketIO | Python service | Pipeline coordination, web dashboard, real-time updates |

- **Pipeline flow:** Mic → OpenWakeWord → Whisper (STT) → Ollama (intent) → Action Executor → GPIO + Piper (TTS) → Speaker.
- **Intent output format:** `{ "intent": "leaving", "confidence": 0.92, "entities": {"room": "all"} }`
- **Configurable models:** All models configurable via `.env`. Swap Ollama model, Whisper size, TTS voice.

### 2.2 Intent Engine

- Ollama LLM receives transcribed text + system prompt listing available intents.
- System prompt dynamically updated with current routines and GPIO mappings.
- Output is structured JSON: intent name, confidence score, extracted entities.
- Confidence threshold (`INTENT_CONFIDENCE_THRESHOLD`) — below threshold, ask for confirmation via TTS.
- Intent history logged to SQLite with timestamps and outcomes.

### 2.3 Routine Engine

- Named sequences of GPIO actions stored in SQLite.
- Default routines: Leaving, Goodnight, Movie time, Good morning, Emergency.
- Each action has a configurable delay (default 500 ms between steps).
- Routines editable from the web dashboard (create, edit, delete, reorder).
- Routines triggerable by voice, dashboard, or scheduler.

### 2.4 GPIO Physical Feedback

- **Relays:** 4-channel module for door lock, lights, alarm, spare.
- **LEDs:** Green LED blinks once per completed action.
- **Buzzer:** Short beep for single action; melody for completed routine.
- **Verbal:** Piper TTS speaks confirmation ("Door locked. Lights off. Alarm armed.").
- **Mock mode:** `MOCK_GPIO=true` logs actions without hardware access (for development).

### 2.5 Sensor Feedback Loop

- After executing an action, read the corresponding sensor to verify:
  - Door relay ON → magnetic sensor reads CLOSED → "Door locked ✓"
  - Lights relay OFF → light sensor reads LOW → "Lights off ✓"
- Mismatch triggers a warning via TTS and dashboard notification.
- Sensors: magnetic door sensor (GPIO), PIR motion (GPIO), light level (ADC/LDR).

### 2.6 Web Dashboard (Flask + SocketIO + Jinja2)

- **Authentication:** bcrypt password hash stored in `.env`. Rate-limited login (10 attempts / 15 min). Session expiry 24 hours.
- **Layout:** Dark-themed sidebar navigation.
- **Dashboard page:**
  - Live pipeline status (listening / transcribing / thinking / executing / speaking).
  - Recent intent log with confidence scores and outcomes.
  - GPIO pin states (real-time via SocketIO).
  - Sensor readings (door, PIR, light level).
  - System stats (CPU temp, memory, Ollama model loaded).
- **Routines page:**
  - List all routines with action sequence preview.
  - Create/edit routine with action picker and ordering.
  - Delete routine with confirmation.
  - Test routine (execute now) button.
- **GPIO page:**
  - Real-time pin state display (HIGH/LOW with color indicators).
  - Manual toggle switches for each relay.
  - Pin configuration display.
- **History page:**
  - Searchable intent log with timestamps.
  - Filter by intent type, confidence range, date.
  - Action outcome (success/fail/undone).
- **Settings page:**
  - All `.env` variables editable.
  - Ollama model selection (list installed models).
  - Audio device selection.
  - Feature toggle switches.

### 2.7 Undo Command

- "Cancel that" / "Undo" reverses last action within `UNDO_TIMEOUT_SEC` (default 10).
- Undo stack stores previous GPIO states before each action group.
- Only the most recent action group is undoable.
- TTS confirms: "Undone. Door unlocked, lights back on."

### 2.8 Persistent Context Memory

- Stores user preferences in SQLite (`context_memory` table).
- Examples: "I like dim lights for movies", "Don't lock the back door at night".
- LLM receives relevant context entries in its system prompt.
- Configurable max entries (`CONTEXT_MEMORY_MAX_ENTRIES`); oldest pruned.

### 2.9 Environment Configuration

- All configuration via `.env` file (created from `.env.default` template).
- `.env` is in `.gitignore` — never committed.
- Every feature toggleable: `INTENT_ENABLED`, `ROUTINE_ENABLED`, `SENSOR_ENABLED`, `WYOMING_ENABLED`, `GUEST_MODE_ENABLED`, `EMOTION_DETECTION_ENABLED`, `UNDO_ENABLED`, `CONTEXT_MEMORY_ENABLED`, `SCHEDULER_ENABLED`.

### 2.10 Deployment

- `deploy/deploy_to_pi.sh`: rsync to `rasp-pi` (SSH alias at `192.168.216.90`), install deps, install Ollama, pull model, restart service.
- Systemd service file for auto-start on boot.

---

## 3. Nice-to-Have Features

### 3.1 Multi-Room Satellites (Wyoming Protocol)

- Pi Zero 2W devices as voice satellites with mic + speaker.
- Wyoming protocol for audio streaming to main hub.
- Room-aware intent routing (voice from bedroom → bedroom lights).
- Requires additional Pi Zero + mic/speaker per room.

### 3.2 Scheduled Routines

- Voice-triggered: "Turn off lights at 11 PM" creates a cron job.
- Dashboard-configured: time picker → routine → recurrence.
- `schedule` library running in background thread.
- Persisted in SQLite, survives restarts.

### 3.3 Guest Mode

- Limited voice access for unrecognized users.
- `GUEST_ALLOWED_INTENTS` restricts accessible actions.
- Blocks door locks, alarm, routines, settings.

### 3.4 Emotion & Urgency Detection

- LLM analyzes text for stress indicators ("help", "emergency", "hurry").
- Audio amplitude analysis for raised voice detection.
- Triggers `EMERGENCY_ROUTINE` when detected.

### 3.5 Voice Enrollment / Speaker ID

- Speaker embedding to identify household members.
- Per-user preferences and access levels.
- Requires training samples per speaker.

### 3.6 Camera Integration

- Combine with AI-Powered Security Camera project.
- "Who's at the door?" queries answered via camera feed analysis.

---

## 4. Database Schema

### 4.1 `routines` Table

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT NOT NULL | Routine name ("leaving", "goodnight") |
| `description` | TEXT | Human-readable description |
| `actions` | TEXT (JSON) | Ordered list of actions: `[{"pin": 17, "state": "HIGH", "delay_ms": 500}, ...]` |
| `is_default` | BOOLEAN | Whether this is a system default routine |
| `created_at` | DATETIME | Creation timestamp |
| `updated_at` | DATETIME | Last modification timestamp |

### 4.2 `intent_log` Table

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | When the intent was processed |
| `raw_text` | TEXT | Original transcribed text |
| `intent` | TEXT | Parsed intent name |
| `confidence` | REAL | LLM confidence score (0.0 – 1.0) |
| `entities` | TEXT (JSON) | Extracted entities |
| `action_taken` | TEXT | Description of action executed |
| `outcome` | TEXT | "success", "failed", "undone", "confirmed", "rejected" |
| `room` | TEXT | Source room (if multi-room enabled) |

### 4.3 `gpio_states` Table

| Column | Type | Description |
|---|---|---|
| `pin` | INTEGER PK | GPIO pin number |
| `label` | TEXT | Human-readable name ("door_lock", "living_lights") |
| `state` | TEXT | "HIGH" or "LOW" |
| `type` | TEXT | "relay", "led", "buzzer", "sensor" |
| `last_changed` | DATETIME | Last state change timestamp |

### 4.4 `sensors` Table

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `pin` | INTEGER | GPIO pin number |
| `label` | TEXT | Sensor name ("door_sensor", "pir_motion") |
| `type` | TEXT | "magnetic", "pir", "light", "temperature" |
| `last_value` | TEXT | Last reading |
| `last_read` | DATETIME | Last reading timestamp |
| `expected_state` | TEXT | Expected value after action (for feedback loop) |

### 4.5 `action_history` Table

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | When the action was executed |
| `intent_log_id` | INTEGER FK | Reference to `intent_log.id` |
| `pin` | INTEGER | GPIO pin acted upon |
| `previous_state` | TEXT | State before action (for undo) |
| `new_state` | TEXT | State after action |
| `sensor_confirmed` | BOOLEAN | Whether sensor verified the action |
| `undone` | BOOLEAN | Whether this action was later undone |

### 4.6 `context_memory` Table

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `key` | TEXT | Preference category ("movie_lights", "morning_routine") |
| `value` | TEXT | Remembered value or preference |
| `source_text` | TEXT | Original user utterance that set this |
| `created_at` | DATETIME | When the preference was recorded |
| `last_used` | DATETIME | When last included in LLM context |
| `use_count` | INTEGER | How many times referenced |

### 4.7 `settings` Table

| Column | Type | Description |
|---|---|---|
| `key` | TEXT PK | Setting name |
| `value` | TEXT | Setting value |
| `updated_at` | DATETIME | Last modification |

### 4.8 `scheduled_jobs` Table

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `routine_id` | INTEGER FK | Reference to `routines.id` |
| `cron_expression` | TEXT | Schedule ("0 23 * * *" for 11 PM daily) |
| `description` | TEXT | "Turn off lights at 11 PM" |
| `enabled` | BOOLEAN | Active/inactive toggle |
| `created_at` | DATETIME | Creation timestamp |
| `last_run` | DATETIME | Last execution time |

---

## 5. High-Level Architecture

```
                      ┌─────────────────────────────────────────────────────────┐
                      │            Raspberry Pi 4/5                              │
                      │                                                         │
  Browser ─HTTP────► │  Flask + SocketIO (port 5000)                             │
  Browser ──WS─────► │  ├── Session auth (bcrypt) + rate limiting                │
                      │  ├── Jinja2 templates (dashboard, routines, GPIO, etc.)  │
                      │  ├── REST API (/api/routines, /api/gpio, /api/history)   │
                      │  ├── WebSocket (live GPIO states, intent feed)           │
                      │  └── Static files (/static)                              │
                      │                                                         │
                      │  Voice Pipeline:                                         │
                      │  ┌──────────────────────────────────────────────────┐    │
                      │  │ Mic → OpenWakeWord → Whisper.cpp (STT)          │    │
                      │  │     → Ollama (intent parse) → Intent Router      │    │
                      │  │     → Action Executor → GPIO + Piper TTS → Spkr │    │
                      │  └──────────────────────────────────────────────────┘    │
                      │                                                         │
                      │  Intent System:                                          │
                      │  ├── intent_engine.py    → LLM → structured JSON        │
                      │  ├── routine_engine.py   → named action sequences       │
                      │  ├── action_executor.py  → GPIO pin control             │
                      │  ├── undo_manager.py     → reverse last action          │
                      │  └── scheduler.py        → cron-style timed routines    │
                      │                                                         │
                      │  Hardware Layer:                                          │
                      │  ├── gpio_controller.py  → relays, LEDs, buzzer         │
                      │  ├── sensor_reader.py    → door, PIR, light sensors     │
                      │  └── context_memory.py   → persistent preferences       │
                      │                                                         │
                      │  Wyoming Protocol (port 10400):                          │
                      │  └── Multi-room satellite management                    │
                      │                                                         │
                      │  Ollama (port 11434):                                    │
                      │  └── Llama 3 / Phi-3 model server                       │
                      └─────────────────────────────────────────────────────────┘

                      Wyoming Satellites:
                      ┌──────────┐  ┌──────────┐  ┌──────────┐
                      │ Pi Zero  │  │ Pi Zero  │  │ Pi Zero  │
                      │ Room 1   │  │ Room 2   │  │ Garage   │
                      │ Mic+Spkr │  │ Mic+Spkr │  │ Mic+Spkr │
                      └──────────┘  └──────────┘  └──────────┘
```

### Intent Processing Flow

```
 "I'm heading out"
       │
       ▼
 Ollama LLM (system prompt with available intents)
       │
       ▼
 { "intent": "leaving", "confidence": 0.94, "entities": {} }
       │
       ▼
 Confidence ≥ 0.7?  ──YES──►  Routine Lookup ("leaving")
       │                              │
       NO                             ▼
       │                    Action Sequence:
       ▼                    1. Pin 17 HIGH (door lock)    → sensor check
 TTS: "Did you mean        2. Pin 27 LOW  (lights off)   → sensor check
  lock up and leave?"       3. Pin 22 HIGH (alarm on)     → sensor check
       │                    4. Pin 23 flash (LED confirm)
       ▼                    5. Pin 24 beep  (buzzer)
 Wait for "yes"/"no"              │
                                  ▼
                           Save to action_history (for undo)
                                  │
                                  ▼
                           TTS: "Done. Door locked, lights off, alarm armed."
```

---

## 6. Security and Threat Model

**Primary assets:**
- Dashboard credentials and session tokens.
- GPIO pin access (controls physical locks, alarms, lights).
- Intent history (voice interaction patterns).
- Context memory (user preferences and habits).
- Ollama model files.
- `.env` file (passwords, pin mappings).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Brute-force login | Rate limiting (10 attempts / 15 min); bcrypt hash with salt |
| Session hijacking | `httpOnly`, `sameSite` cookies; strong session secret |
| Unauthorized GPIO access | `GPIO_ENABLED` flag; auth required for dashboard; confidence threshold for voice |
| Malicious voice commands | Confidence threshold; confirmation for low-confidence intents; guest mode restrictions |
| Accidental actions | Undo command within 10 sec; sensor verification feedback loop |
| Replay attacks (voice) | Wake word required before each command; session-based processing |
| Wyoming abuse | Firewall Wyoming port to local network; satellite authentication |
| `.env` exposure | In `.gitignore`; `chmod 600` on Pi |
| XSS via intent log | HTML-escape all user text in Jinja2 templates (auto-escaping enabled) |
| GPIO pin misconfiguration | Validation at startup; mock mode for testing |
| Physical security (relay access) | Relay modules should be in a locked enclosure |

---

## 7. Suggested Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| Backend | Python 3.11+ / Flask | Mature, extensive GPIO/ML ecosystem |
| Real-time | Flask-SocketIO + eventlet | Live GPIO states, intent feed |
| Templating | Jinja2 | Server-side rendering, no build step |
| LLM | Ollama (Llama 3 / Phi-3) | Managed model runtime, HTTP API, hot-swap models |
| Wake word | OpenWakeWord | Runs on Pi CPU, customizable, no cloud |
| STT | Whisper.cpp (whispercpp bindings) | C++ optimized, runs on Pi CPU |
| TTS | Piper TTS | Designed for Pi, real-time, 30+ languages |
| GPIO | RPi.GPIO | Standard Pi GPIO library |
| Audio | PyAudio | Standard Python audio I/O |
| Wyoming | wyoming Python package | Multi-room voice protocol |
| Auth | bcrypt + Flask sessions | Single-user device auth |
| Scheduling | schedule | Lightweight cron-like scheduling |
| Database | SQLite | Zero-config, file-based, sufficient for single-device |
| Config | python-dotenv | `.env` file loading |
| CSS | Custom dark theme | Lightweight, no framework dependency |

---

## 8. Development Phases

### Phase 1 — Foundation & Configuration (Week 1)

1. Initialize project structure, `requirements.txt`, `.env.default`, `.gitignore`.
2. Implement `config.py` — load `.env`, parse feature flags, validate pins.
3. Implement `database.py` — SQLite schema (all 8 tables), CRUD functions.
4. Implement `auth.py` — bcrypt verification, session management, rate limiting.
5. Create Flask skeleton (`app.py`) with SocketIO, dark theme base template.
6. Create login page, dashboard placeholder.

### Phase 2 — Voice Pipeline & Intent Engine (Week 1–2)

1. Implement `src/pipeline/audio_io.py` — mic capture, speaker playback.
2. Implement `src/pipeline/wakeword.py` — OpenWakeWord integration.
3. Implement `src/pipeline/stt.py` — Whisper.cpp transcription.
4. Implement `src/pipeline/llm.py` — Ollama client with intent system prompt.
5. Implement `src/pipeline/tts.py` — Piper TTS synthesis.
6. Implement `intent_engine.py` — parse Ollama JSON output, validate intent, score confidence.
7. Wire full pipeline: wake → STT → Ollama → intent → TTS confirmation.

### Phase 3 — GPIO & Hardware Control (Week 2)

1. Implement `gpio_controller.py` — relay, LED, buzzer abstraction with mock mode.
2. Implement `sensor_reader.py` — magnetic, PIR, light sensor reading.
3. Implement `action_executor.py` — execute intent → GPIO pin changes.
4. Implement sensor feedback loop — read sensor after action, verify state.
5. Implement `undo_manager.py` — store previous states, reverse on "cancel that".
6. Test relay + sensor + LED + buzzer on breadboard.

### Phase 4 — Routines & Context Memory (Week 2–3)

1. Implement `routine_engine.py` — load/save routines, execute sequence with delays.
2. Create default routines (Leaving, Goodnight, Movie time, Good morning, Emergency).
3. Implement `context_memory.py` — store/retrieve user preferences.
4. Implement `scheduler.py` — cron-style timed routine execution.
5. Implement `guest_manager.py` — intent filtering by access level.
6. Implement `emotion_detector.py` — stress keyword detection, emergency trigger.

### Phase 5 — Web Dashboard (Week 3)

1. Build dashboard page (live status, recent intents, GPIO states, sensors).
2. Build routines page (CRUD with action picker and ordering).
3. Build GPIO page (real-time pin states, manual toggles).
4. Build history page (searchable intent log with filters).
5. Build settings page (env editor, model selection, feature toggles).
6. Implement SocketIO events for live GPIO state and intent feed updates.

### Phase 6 — Integration, Deployment & Testing (Week 3–4)

1. Implement Wyoming protocol server for multi-room satellites.
2. Create `deploy/deploy_to_pi.sh` with Ollama installation.
3. Create systemd service file.
4. Write unit tests (intent engine, action executor, GPIO controller, auth, database).
5. Write integration test (full voice → intent → action → sensor → confirmation flow).
6. Security audit (headers, input validation, parameterized queries, CSRF).
7. Performance test on Pi 4/5 (end-to-end latency target: <5 sec).
8. Final documentation review.

---

## 9. `.env.default` Block

```bash
# ============================================================
# LLM-Powered Voice Assistant with Physical Feedback
# Environment Configuration
# Copy this file to .env and customize
# ============================================================

# --- Server ---
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=change-me-to-a-random-64-char-string

# --- Authentication ---
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=                    # Generate: python -c "import bcrypt; print(bcrypt.hashpw(b'yourpass', bcrypt.gensalt()).decode())"
RATE_LIMIT_MAX=10
RATE_LIMIT_WINDOW_MIN=15
SESSION_EXPIRY_HOURS=24

# --- Voice Pipeline ---
WAKEWORD_ENABLED=true
WAKEWORD_MODEL=hey_jarvis
WAKEWORD_SENSITIVITY=0.5
WHISPER_MODEL_SIZE=base
WHISPER_LANGUAGE=en
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
PIPER_VOICE=en_US-lessac-medium
TTS_ENABLED=true

# --- Intent Engine ---
INTENT_ENABLED=true
INTENT_CONFIDENCE_THRESHOLD=0.7
INTENT_CONFIRM_BELOW_THRESHOLD=true

# --- GPIO ---
GPIO_ENABLED=true
MOCK_GPIO=false
RELAY_DOOR_PIN=17
RELAY_LIGHTS_PIN=27
RELAY_ALARM_PIN=22
LED_CONFIRM_PIN=23
BUZZER_PIN=24

# --- Sensors ---
SENSOR_ENABLED=true
DOOR_SENSOR_PIN=25
PIR_SENSOR_PIN=5
LIGHT_SENSOR_PIN=6

# --- Routines ---
ROUTINE_ENABLED=true
SCHEDULER_ENABLED=true

# --- Multi-Room (Wyoming) ---
WYOMING_ENABLED=false
WYOMING_PORT=10400

# --- Context Memory ---
CONTEXT_MEMORY_ENABLED=true
CONTEXT_MEMORY_MAX_ENTRIES=500

# --- Guest Mode ---
GUEST_MODE_ENABLED=false
GUEST_ALLOWED_INTENTS=lights,temperature,time

# --- Emotion Detection ---
EMOTION_DETECTION_ENABLED=false
EMERGENCY_ROUTINE=emergency

# --- Undo ---
UNDO_ENABLED=true
UNDO_TIMEOUT_SEC=10

# --- Database ---
DATABASE_PATH=data/voice_assistant.db

# --- Audio ---
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default
```

---

## 10. Deliverables

| Deliverable | Description |
|---|---|
| `README.md` | Full project documentation with v1 vs v2 comparison |
| `TSD.md` | This technical specification |
| `task.md` | Engineering task checklist by phase |
| `implementation_plan.md` | Step-by-step implementation guide |
| `requirements.txt` | Python dependencies |
| `.env.default` | Environment variable template |
| `.gitignore` | Git ignore rules |
| `app.py` | Flask + SocketIO entry point |
| `config.py` | Configuration loader |
| `auth.py` | Authentication system |
| `intent_engine.py` | LLM intent parser |
| `action_executor.py` | GPIO action executor |
| `routine_engine.py` | Routine manager |
| `gpio_controller.py` | GPIO abstraction layer |
| `sensor_reader.py` | Sensor reading and verification |
| `context_memory.py` | Persistent preference memory |
| `scheduler.py` | Timed routine scheduler |
| `undo_manager.py` | Undo last action |
| `guest_manager.py` | Guest access control |
| `emotion_detector.py` | Urgency/stress detection |
| `database.py` | SQLite schema and queries |
| `deploy/deploy_to_pi.sh` | Deployment script |
| `templates/` | Jinja2 HTML templates (dark theme) |
| `static/` | CSS and JavaScript assets |
| `tests/` | Unit and integration tests |
