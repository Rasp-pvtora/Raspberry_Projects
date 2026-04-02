# Implementation Plan — LLM-Powered Voice Assistant with Physical Feedback

## Phase 1 — Foundation & GPIO Layer

### Step 1.1 — Project Scaffolding

- [ ] Create directory structure:
  ```
  mkdir -p models/whisper models/wakeword static/css static/js templates data deploy tests
  ```
- [ ] Create `requirements.txt`:
  ```
  flask>=3.0
  flask-socketio>=5.3
  ollama>=0.3
  openwakeword>=0.6
  whispercpp>=0.0.17
  piper-tts>=1.2
  pyaudio>=0.2.14
  RPi.GPIO>=0.7
  wyoming>=1.5
  bcrypt>=4.1
  python-dotenv>=1.0
  schedule>=1.2
  numpy>=1.26
  eventlet>=0.35
  ```
- [ ] Create `.env.default` with all variables (reference TSD §9)
- [ ] Create `.gitignore` (exclude `data/`, `models/`, `.env`, `__pycache__/`, `venv/`)

### Step 1.2 — Configuration Loader

- [ ] Implement `config.py`:
  - Load `.env` via `python-dotenv`
  - Parse all feature flags as booleans (`_ENABLED` variables)
  - Parse numeric values (port, rate limit, pin numbers, thresholds)
  - Parse comma-separated lists (guest permissions)
  - Validate required paths exist (model paths when features enabled)
  - Validate GPIO pin numbers are unique and valid
  - Export a `Config` dataclass for app-wide use

**Checkpoint:** `python -c "from config import Config; c = Config(); print(c)"` prints loaded config.

### Step 1.3 — Database Layer

- [ ] Implement `database.py`:
  - `init_db()` — create all 8 tables if not exist (routines, intent_log, gpio_states, sensors, action_history, settings, guests, scheduled_routines)
  - Create indexes on intent_log, sensors, action_history
  - Routine CRUD: `create_routine()`, `get_routine()`, `list_routines()`, `update_routine()`, `delete_routine()`
  - Intent log: `log_intent()`, `list_intents(limit, offset, filters)`, `search_intents(query)`
  - GPIO states: `get_gpio_state(pin)`, `set_gpio_state(pin, state)`, `list_gpio_states()`
  - Sensors: `log_sensor_reading()`, `get_latest_reading(sensor_type)`, `list_sensor_history()`
  - Action history: `log_action()`, `get_recent_actions(window_sec)`, `mark_reversed(action_id)`
  - Settings: `get_setting(key)`, `set_setting(key, value)`, `list_settings(category)`
  - Guests: `create_guest()`, `get_guest()`, `list_guests()`, `update_guest()`, `delete_guest()`
  - Scheduled routines: CRUD operations
  - Use parameterized queries (`?` placeholders) throughout

**Checkpoint:** `python -c "from database import init_db; init_db()"` creates `data/assistant.db` with correct schema.

### Step 1.4 — GPIO Controller

- [ ] Implement `gpio_controller.py`:
  - `GPIOController` class:
    - `setup()` — configure all pins from `.env` (output for relays/LEDs/buzzer, input for sensors)
    - `relay_on(pin)`, `relay_off(pin)`, `relay_toggle(pin)` — with state tracking
    - `led_flash(pin, duration_ms)` — non-blocking LED flash
    - `buzzer_beep(pattern)` — short beep, long beep, alarm pattern
    - `cleanup()` — reset all pins on shutdown
  - `MockGPIOController` — logs actions to console instead of hardware control
  - Selection based on `GPIO_ENABLED` flag

**Checkpoint:** On Pi: toggle relay → hear click. On laptop: see "MOCK: Relay pin 17 ON" in console.

### Step 1.5 — Sensor Reader

- [ ] Implement `sensor_reader.py`:
  - `SensorReader` class:
    - `read_door()` → `{ state: "locked" | "unlocked", pin, raw }` (reed switch)
    - `read_pir()` → `{ motion: bool, pin, raw }` (PIR sensor)
    - `read_light()` → `{ level: float, pin, raw }` (light sensor)
    - `read_all()` → dict of all sensor readings
  - `MockSensorReader` — returns configurable dummy values
  - Store readings in `sensors` table

**Checkpoint:** On Pi: cover door sensor → `read_door()` returns "locked". On laptop: mock returns configured state.

### Step 1.6 — Flask Skeleton & Auth

- [ ] Implement basic `app.py`:
  - Flask app with SocketIO
  - Load config, init database
  - Register routes and SocketIO events
  - Dark theme base template with sidebar navigation
- [ ] Create `static/css/style.css` — dark background, card layout, accent colors for GPIO states
- [ ] Create `static/js/app.js` — SocketIO client connection, GPIO state rendering
- [ ] Implement `auth.py`:
  - `hash_password(plaintext)` → bcrypt hash
  - `verify_password(plaintext, hash)` → bool
  - `login_required` decorator — checks session, redirects to login
  - Rate limiter — track attempts per IP, block after `RATE_LIMIT_MAX` in `RATE_LIMIT_WINDOW_MIN`
  - Session config: `SESSION_EXPIRY_HOURS` enforced via `before_request`
  - CSRF token generation and validation
- [ ] Create `templates/base.html` — dark theme with sidebar (Dashboard, Routines, Intents, Sensors, Settings, Guests)
- [ ] Create `templates/login.html` — username + password form

**Checkpoint:** `python app.py` starts on port 5000. Login with correct password → dark-themed dashboard stub. 11th rapid login → 429.

---

## Phase 2 — Voice Pipeline & Intent Engine

### Step 2.1 — Audio Capture

- [ ] Implement audio subsystem in `voice_pipeline.py`:
  - `AudioCapture` class:
    - Opens PyAudio stream (16kHz, mono, int16)
    - Configurable device selection (`AUDIO_INPUT_DEVICE`)
    - Pushes audio chunks to a queue
    - `start()`, `stop()`, `is_running` interface
  - `MockAudioCapture` — generates silence or reads sample WAV

**Checkpoint:** `python voice_pipeline.py` lists audio devices, captures 5 seconds to `test.wav`.

### Step 2.2 — Wake Word + STT

- [ ] Integrate OpenWakeWord:
  - Load model (`WAKEWORD_MODEL`)
  - Continuous listening on audio stream
  - Trigger on configurable sensitivity (`WAKEWORD_SENSITIVITY`)
  - After trigger: capture audio for a configurable duration (until silence)
- [ ] Integrate Whisper.cpp:
  - Load model (`STT_MODEL_PATH`)
  - Transcribe captured audio buffer → text string
  - Language from `STT_LANGUAGE`

**Checkpoint:** Say wake word → microphone captures speech → Whisper returns transcription text.

### Step 2.3 — Ollama Intent Engine

- [ ] Implement `intent_engine.py`:
  - `IntentEngine` class:
    - `__init__(ollama_host, model, registered_intents)` — connect to Ollama
    - `parse_intent(text)` → `{ intent, confidence, params, raw_text }`
    - System prompt template:
      ```
      You are a smart home intent parser. Given the user's voice command,
      return a JSON object with: intent, confidence (0.0-1.0), params.
      Registered intents: {intent_list}
      If no intent matches, return: { "intent": "unknown", "confidence": 0.0 }
      Respond ONLY with valid JSON.
      ```
    - Parse JSON response, validate schema
    - Handle malformed LLM output gracefully (retry once, then fallback)
  - `MockIntentEngine` — returns canned intents based on keyword matching

**Checkpoint:** Send "I'm leaving" → get `{ "intent": "leaving_routine", "confidence": 0.9+ }`.

### Step 2.4 — Confidence & Confirmation

- [ ] Implement confidence check in pipeline:
  - Confidence ≥ threshold → execute immediately
  - Confidence < threshold → TTS asks: "Did you mean [action]? Say yes or no."
  - Wait for second voice capture → STT → check for yes/no
  - Yes → execute. No → cancel and apologize.
- [ ] Implement unknown intent fallback:
  - Pass to Ollama as a regular chat query (v1 behavior)
  - Return conversational response via TTS

**Checkpoint:** Mumble an unclear command → assistant asks for confirmation → say "yes" → action executes.

### Step 2.5 — Full Pipeline Wiring

- [ ] Wire all components in `voice_pipeline.py`:
  - `VoicePipeline` class:
    - Orchestrates: wake → capture → STT → intent → route → action → sensor → TTS → speaker
    - Background thread runs the main loop
    - Emits SocketIO events at each stage (for dashboard status)
  - Route intent to routine engine or single action based on intent type

**Checkpoint:** Full loop on Pi: say "Hey Jarvis, turn on the lights" → lights relay toggles → TTS confirms.

---

## Phase 3 — Routine Engine & Action Execution

### Step 3.1 — Routine Engine

- [ ] Implement `routine_engine.py`:
  - `RoutineEngine` class:
    - `load_routines()` — fetch all active routines from DB
    - `execute_routine(name)` — execute steps in order with configurable delay
    - `execute_step(step)` — map step to GPIO action
    - `abort_routine()` — stop mid-execution
  - Step format (JSON):
    ```json
    { "action": "relay_on", "pin": 17, "label": "Lock door", "delay_ms": 500 }
    ```
- [ ] Seed built-in routines on first run

**Checkpoint:** `execute_routine("leaving")` → relay clicks in sequence → LED flash → buzzer beep.

### Step 3.2 — Sensor Feedback

- [ ] After each routine completes:
  - Read all relevant sensors
  - Build confirmation text: "Door locked ✓. Lights off ✓. No motion ✓."
  - Log sensor readings to `sensors` table
  - Include failed confirmations: "Warning: door sensor not responding."

**Checkpoint:** Execute "leaving" → sensor feedback text matches actual hardware state.

### Step 3.3 — TTS Response

- [ ] Integrate Piper TTS:
  - Load model (`TTS_MODEL_PATH`)
  - Synthesize confirmation text → audio
  - Play through speaker (`AUDIO_OUTPUT_DEVICE`)
- [ ] Build response text template:
  - Success: "Done. [sensor confirmations]."
  - Partial: "Done, but [warnings]."
  - Error: "Sorry, [error description]."

**Checkpoint:** Execute routine → hear spoken confirmation with sensor results through speaker.

### Step 3.4 — Undo Manager

- [ ] Implement `undo_manager.py`:
  - `UndoManager` class:
    - `record_action(action)` — push to stack with timestamp and reverse operation
    - `can_undo()` → bool (within time window, stack not empty)
    - `undo_last()` → execute reverse of last action
    - `expire_actions()` — remove actions older than `UNDO_WINDOW_SEC`
  - Reverse operations: `relay_on` ↔ `relay_off`, LED clears, buzzer stops
- [ ] Register "cancel that" / "undo" as a voice intent

**Checkpoint:** Lock door → within 10s say "Cancel that" → door unlocks → TTS: "Undone. Door unlocked."

### Step 3.5 — Context Memory

- [ ] Implement `context_memory.py`:
  - `ContextMemory` class:
    - `remember(key, value)` — store in settings table (category=preference)
    - `recall(key)` → value
    - `get_context_prompt()` → string for LLM system prompt injection
    - `forget(key)` — delete from settings
    - `prune()` — enforce `CONTEXT_MEMORY_MAX_ENTRIES`
  - Voice commands: "Remember that I like the lights dim" → stored
  - Injected into Ollama system prompt on each request

**Checkpoint:** "Remember I prefer dim lights" → next session, "I'm home" routine sets lights to dim.

---

## Phase 4 — Web Dashboard

### Step 4.1 — Dashboard Page

- [ ] Create `templates/dashboard.html`:
  - Pipeline status indicator (listening / processing / speaking / idle)
  - GPIO state cards (relay on/off with green/red indicators)
  - Sensor readings cards (door, PIR, light) with last-updated time
  - Recent intent log (last 10 intents with confidence badges)
  - System stats (CPU temp, memory, disk, Ollama model loaded)
- [ ] SocketIO events:
  - `pipeline_status` — broadcast current stage
  - `gpio_update` — broadcast on state change
  - `sensor_update` — broadcast on new reading
  - `new_intent` — broadcast on intent parsed

**Checkpoint:** Execute a voice command → dashboard updates in real-time: pipeline status, GPIO, sensor, intent log.

### Step 4.2 — Routines Page

- [ ] Create `templates/routines.html`:
  - List all routines (name, description, step count, active/inactive)
  - Add routine button → modal/form with name, description, trigger phrase
  - Edit routine → step editor (add/remove/reorder steps with drag)
  - Delete routine → confirmation dialog
  - Test-run button → execute routine from browser (API call)
- [ ] Implement API routes:
  - `GET /api/routines` — list all
  - `POST /api/routines` — create
  - `PUT /api/routines/<id>` — update
  - `DELETE /api/routines/<id>` — delete
  - `POST /api/routines/<id>/run` — test-run

**Checkpoint:** Create a custom routine "Test" from dashboard → test-run → relays toggle.

### Step 4.3 — Intent Log Page

- [ ] Create `templates/intents.html`:
  - Paginated table (timestamp, raw text, intent, confidence, actions, sensor confirm)
  - Confidence badge: green (≥0.8), yellow (0.5–0.8), red (<0.5)
  - Search box (full-text search on raw_text)
  - Filters: date range, intent type, confidence range, user type (owner/guest)

**Checkpoint:** Search "leaving" → all "leaving" intents shown with actions and sensor data.

### Step 4.4 — Sensors Page

- [ ] Create `templates/sensors.html`:
  - Real-time sensor cards with SocketIO updates
  - Door: locked/unlocked with icon
  - PIR: motion/no motion with last-triggered time
  - Light: level bar or numeric value
  - Historical chart (last 24h readings) if data available

**Checkpoint:** Cover door sensor → dashboard instantly shows "Locked" with timestamp.

### Step 4.5 — Settings & Guests Pages

- [ ] Create `templates/settings.html`:
  - Display all current `.env` values (grouped by category)
  - Editable fields for non-sensitive values
  - Ollama model management (list installed, pull new)
  - Audio device selection dropdowns
  - Wake word configuration
- [ ] Create `templates/guests.html`:
  - Guest list (name, permissions, active status)
  - Add/edit/delete guest
  - Permission toggles (checkboxes for each permission type)

**Checkpoint:** Add a guest user from dashboard → guest has limited voice access.

---

## Phase 5 — Advanced Features

### Step 5.1 — Scheduled Routines

- [ ] Implement `scheduler.py`:
  - `RoutineScheduler` class:
    - `load_schedules()` — fetch from `scheduled_routines` table
    - `start()` — background thread running `schedule` library loop
    - `add_schedule(routine_id, cron_expr)` — register new schedule
    - `remove_schedule(schedule_id)` — unregister
    - `get_next_runs()` → list of upcoming scheduled routines
  - Integrate with routine engine for execution
- [ ] Add scheduled routine management to Routines page
- [ ] Implement "schedule" voice intent: "Turn off lights at 11 PM" → creates schedule

**Checkpoint:** Schedule "Goodnight at 11 PM" → at 23:00 routine executes automatically.

### Step 5.2 — Guest Mode

- [ ] Implement `guest_mode.py`:
  - `GuestManager` class:
    - `check_permission(guest_name, intent)` → allowed/denied
    - `get_guest_by_voice()` → optional voice identification (stretch)
    - `filter_intents(guest_name, intent_list)` → allowed intents only
  - Denied intents → TTS: "Sorry, you don't have permission to do that."

**Checkpoint:** Guest says "Lock the door" with permission denied → assistant refuses.

### Step 5.3 — Wyoming Protocol

- [ ] Implement Wyoming server:
  - Listen on `WYOMING_PORT` for satellite connections
  - Receive audio stream from satellite → feed to voice pipeline
  - Return TTS audio to satellite
  - Tag intents with source room
- [ ] Test with Pi Zero 2W satellite (mic + speaker + OpenWakeWord)

**Checkpoint:** Satellite in Room 2: say command → main Pi processes → TTS plays on Room 2 speaker.

### Step 5.4 — Emotion Detection

- [ ] Implement emotion analysis in `intent_engine.py`:
  - Add emotion cues to LLM system prompt
  - Parse urgency field from LLM response
  - Urgency "high" → skip confirmation → execute emergency routine
  - Add `emotion` field to intent log

**Checkpoint:** Say "Help! Someone's at the door!" urgently → emergency routine triggers without confirmation.

---

## Phase 6 — Hardening & Deployment

### Step 6.1 — Security Hardening

- [ ] Add `Content-Security-Policy` header to all responses
- [ ] Add `X-Content-Type-Options: nosniff` header
- [ ] Add `X-Frame-Options: DENY` header
- [ ] Audit all user inputs for sanitization (routine names, guest names, search queries)
- [ ] Verify all SQL uses parameterized queries
- [ ] Verify Jinja2 auto-escaping is enabled on all templates
- [ ] Test rate limiter under load

**Checkpoint:** Security headers present on all responses; injection attempts blocked.

### Step 6.2 — Error Handling & Logging

- [ ] Add structured logging to all modules (Python `logging` module)
- [ ] Log to file (`data/app.log`) and console
- [ ] Handle Ollama server unreachable (disable intent engine, use fallback responses)
- [ ] Handle GPIO pin conflict / permission denied (log warning, disable GPIO)
- [ ] Handle audio device disconnection (pause pipeline, notify UI)
- [ ] Handle sensor read failure (log warning, skip confirmation for that sensor)
- [ ] Handle disk full (stop logging to DB, alert user)
- [ ] Add health check endpoint (`/api/health`)

**Checkpoint:** Kill Ollama → assistant says "Sorry, I can't process commands right now." Dashboard shows Ollama status: offline.

### Step 6.3 — Deployment

- [ ] Create `deploy/deploy_to_pi.sh`:
  ```bash
  #!/bin/bash
  REMOTE="rasp-pi"
  REMOTE_DIR="~/voice-assistant-v2"
  rsync -avz --exclude='venv' --exclude='data' --exclude='.env' --exclude='models' \
    . ${REMOTE}:${REMOTE_DIR}/
  ssh ${REMOTE} "cd ${REMOTE_DIR} && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  ssh ${REMOTE} "command -v ollama || curl -fsSL https://ollama.com/install.sh | sh"
  ssh ${REMOTE} "ollama pull llama3"
  ssh ${REMOTE} "cd ${REMOTE_DIR} && [ ! -f .env ] && cp .env.default .env"
  ssh ${REMOTE} "sudo cp ${REMOTE_DIR}/deploy/voice-assistant-v2.service /etc/systemd/system/"
  ssh ${REMOTE} "sudo systemctl daemon-reload && sudo systemctl enable voice-assistant-v2 && sudo systemctl restart voice-assistant-v2"
  echo "Deployed. Dashboard: http://192.168.216.90:5000"
  ```
- [ ] Create systemd service file (`deploy/voice-assistant-v2.service`)
- [ ] Test deploy script end-to-end
- [ ] Verify service starts on boot

**Checkpoint:** Run deploy script → service restarts on Pi → dashboard accessible at `http://192.168.216.90:5000`.

### Step 6.4 — Testing

- [ ] Write unit tests for `intent_engine.py` (mock Ollama, verify JSON parsing, confidence)
- [ ] Write unit tests for `routine_engine.py` (mock GPIO, verify step execution order)
- [ ] Write unit tests for `gpio_controller.py` (mock mode, verify state tracking)
- [ ] Write unit tests for `undo_manager.py` (verify time window, reverse operations)
- [ ] Write unit tests for `auth.py` (bcrypt, rate limiter, session expiry)
- [ ] Write unit tests for `context_memory.py` (store, recall, prune)
- [ ] Write integration test: full pipeline (voice → intent → routine → GPIO → sensor → TTS)
- [ ] Run all tests on Pi hardware
- [ ] Performance benchmark: intent parsing latency (target: <3s on Pi 4)
- [ ] Performance benchmark: full pipeline round-trip (target: <8s on Pi 4)
- [ ] Memory profile: sustained usage stays under 6 GB RSS on 8 GB Pi 4
- [ ] Test all 5 built-in routines on hardware with sensor verification
- [ ] Final review of `README.md`, `TSD.md`, all `.env.default` variables

**Checkpoint:** All tests pass on Pi. Full pipeline executes in under 8 seconds. All routines work with sensor confirmation.
