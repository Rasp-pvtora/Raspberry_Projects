# Task List — LLM-Powered Voice Assistant with Physical Feedback

## Phase 1 — Foundation & Configuration

- [ ] Create project directory structure
- [ ] Create `requirements.txt` with all dependencies
- [ ] Create `.env.default` with all variables and defaults
- [ ] Create `.gitignore` (exclude `data/`, `models/`, `.env`, `__pycache__/`, `venv/`)
- [ ] Implement `config.py` — load `.env`, parse feature flags, validate GPIO pins
- [ ] Implement `database.py` — SQLite schema init (routines, intent_log, gpio_states, sensors, action_history, context_memory, settings, scheduled_jobs)
- [ ] Add parameterized query helpers for all CRUD operations
- [ ] Implement `auth.py` — bcrypt password verification
- [ ] Implement login route with rate limiting (10 req / 15 min / IP)
- [ ] Implement session management (server-side, 24h expiry)
- [ ] Add `@login_required` decorator for protected routes
- [ ] Add CSRF protection to all forms
- [ ] Create Flask + SocketIO skeleton (`app.py`)
- [ ] Set up Jinja2 base template with dark theme sidebar
- [ ] Create `static/css/style.css` (dark theme dashboard)
- [ ] Create `static/js/app.js` (SocketIO client stub)
- [ ] Create `templates/login.html`
- [ ] Toggle auth on/off via `AUTH_ENABLED`

## Phase 2 — Voice Pipeline & Intent Engine

- [ ] Implement `src/pipeline/audio_io.py` — PyAudio device discovery and capture
- [ ] Implement audio capture loop (16kHz, mono, configurable chunk duration)
- [ ] Add mock audio mode (reads from WAV or generates silence)
- [ ] Implement `src/pipeline/wakeword.py` — OpenWakeWord integration
- [ ] Implement configurable wake word and sensitivity
- [ ] Implement `src/pipeline/stt.py` — Whisper.cpp model loading and transcription
- [ ] Add mock transcription mode (returns canned text)
- [ ] Implement `src/pipeline/llm.py` — Ollama client with intent system prompt
- [ ] Design intent system prompt with available intents and JSON output format
- [ ] Implement dynamic system prompt update (new routines → new intents)
- [ ] Implement `src/pipeline/tts.py` — Piper TTS synthesis and playback
- [ ] Implement `intent_engine.py` — parse Ollama JSON output, validate fields
- [ ] Implement confidence scoring and threshold check
- [ ] Implement confirmation flow for low-confidence intents
- [ ] Wire full pipeline: wake → STT → Ollama → intent parse → action/confirm
- [ ] Log all intents to `intent_log` table with timestamps and outcomes
- [ ] Test pipeline end-to-end with mock components
- [ ] Verify USB microphone detection on Pi

## Phase 3 — GPIO & Hardware Control

- [ ] Implement `gpio_controller.py` — relay control (set pin HIGH/LOW)
- [ ] Implement LED control (single flash, pattern flash)
- [ ] Implement buzzer control (single beep, melody for routine complete)
- [ ] Implement mock GPIO mode (`MOCK_GPIO=true` logs actions, no hardware)
- [ ] Implement `sensor_reader.py` — magnetic door sensor reading
- [ ] Implement PIR motion sensor reading
- [ ] Implement light sensor reading (LDR via ADC or digital threshold)
- [ ] Implement `action_executor.py` — map intent to GPIO actions
- [ ] Implement sensor feedback loop — read sensor after action, verify expected state
- [ ] Implement mismatch warning via TTS and dashboard notification
- [ ] Implement `undo_manager.py` — store previous GPIO states per action group
- [ ] Implement undo trigger ("cancel that" intent within `UNDO_TIMEOUT_SEC`)
- [ ] Implement GPIO state persistence to `gpio_states` table
- [ ] Initialize GPIO states from database on startup
- [ ] Test relay + sensor + LED + buzzer on breadboard

## Phase 4 — Routines & Context Memory

- [ ] Implement `routine_engine.py` — load routines from database
- [ ] Implement routine execution (sequential actions with configurable delays)
- [ ] Create default routines (Leaving, Goodnight, Movie time, Good morning, Emergency)
- [ ] Implement routine CRUD API (`/api/routines`)
- [ ] Implement `context_memory.py` — store user preferences in SQLite
- [ ] Implement preference retrieval for LLM system prompt injection
- [ ] Implement max entry limit with oldest-entry pruning
- [ ] Implement `scheduler.py` — background thread with `schedule` library
- [ ] Implement scheduled job persistence in `scheduled_jobs` table
- [ ] Implement voice-triggered schedule creation ("Turn off lights at 11 PM")
- [ ] Implement `guest_manager.py` — intent filtering by allowed list
- [ ] Implement guest mode toggle via `.env`
- [ ] Implement `emotion_detector.py` — stress keyword detection in transcribed text
- [ ] Implement emergency routine trigger on urgency detection
- [ ] Test routine execution with all default routines
- [ ] Test scheduled job creation and execution

## Phase 5 — Web Dashboard

- [ ] Create `templates/dashboard.html` — live pipeline status
- [ ] Implement recent intent feed (last 20 intents with confidence and outcome)
- [ ] Implement real-time GPIO state display via SocketIO
- [ ] Implement sensor readings display (door, PIR, light)
- [ ] Implement system stats display (CPU temp, memory, Ollama model info)
- [ ] Create `templates/routines.html` — routine list and editor
- [ ] Implement routine create/edit form with action picker
- [ ] Implement routine delete with confirmation modal
- [ ] Implement routine test button (execute now)
- [ ] Create `templates/gpio.html` — pin state display
- [ ] Implement manual toggle switches for each relay
- [ ] Implement pin configuration display
- [ ] Create `templates/history.html` — searchable intent log
- [ ] Implement intent log pagination
- [ ] Implement filters (intent type, confidence range, date range, outcome)
- [ ] Create `templates/settings.html` — configuration editor
- [ ] Implement Ollama model selection (list installed models)
- [ ] Implement audio device selection
- [ ] Implement feature toggle switches
- [ ] Implement SocketIO events for live GPIO state updates
- [ ] Implement SocketIO events for live intent feed
- [ ] Implement SocketIO events for sensor reading updates

## Phase 6 — Integration, Deployment & Testing

- [ ] Implement `src/wyoming/server.py` — Wyoming protocol server
- [ ] Implement `src/wyoming/satellite.py` — Pi Zero satellite handler
- [ ] Implement `src/wyoming/discovery.py` — multi-room device discovery
- [ ] Test Wyoming satellite connection with Pi Zero 2W
- [ ] Create `deploy/deploy_to_pi.sh` — rsync + Ollama install + service restart
- [ ] Create systemd service file (`deploy/voice-assistant-v2.service`)
- [ ] Add Content-Security-Policy headers
- [ ] Add X-Content-Type-Options and X-Frame-Options headers
- [ ] Audit all routes for input validation and sanitization
- [ ] Audit all database queries for parameterized statements
- [ ] Verify Jinja2 auto-escaping is enabled
- [ ] Add structured logging (file + console)
- [ ] Add error handling for audio device disconnection
- [ ] Add error handling for Ollama connection failure
- [ ] Add error handling for GPIO access errors
- [ ] Add health check endpoint (`/api/health`)
- [ ] Write unit tests for `intent_engine.py`
- [ ] Write unit tests for `action_executor.py`
- [ ] Write unit tests for `routine_engine.py`
- [ ] Write unit tests for `gpio_controller.py` (mock mode)
- [ ] Write unit tests for `auth.py`
- [ ] Write unit tests for `database.py`
- [ ] Write unit tests for `undo_manager.py`
- [ ] Write unit tests for `context_memory.py`
- [ ] Write integration test: voice → intent → GPIO → sensor → confirmation
- [ ] Performance benchmark: end-to-end latency on Pi 4 (target: <5 sec)
- [ ] Performance benchmark: Ollama inference time (target: <3 sec)
- [ ] Memory profiling under sustained use (1 hour)
- [ ] Test deploy script end-to-end
- [ ] Verify service starts on boot
- [ ] Final `README.md` review
- [ ] Final `.env.default` review — all variables documented
