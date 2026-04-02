# Implementation Plan — AI Meeting Assistant

## Phase 1 — Foundation & Audio Pipeline

### Step 1.1 — Project Scaffolding

- [ ] Create directory structure:
  ```
  mkdir -p models/whisper models/llm static/css static/js templates data deploy tests
  ```
- [ ] Create `requirements.txt`:
  ```
  flask>=3.0
  flask-socketio>=5.3
  whispercpp>=0.0.17
  llama-cpp-python>=0.2
  pyannote-audio>=3.1
  resemblyzer>=0.1.3
  pyaudio>=0.2.14
  numpy>=1.26
  reportlab>=4.1
  bcrypt>=4.1
  python-dotenv>=1.0
  eventlet>=0.35
  ```
- [ ] Create `.env.example` with all variables (reference TSD §8)
- [ ] Create `.gitignore` (exclude `data/`, `models/`, `.env`, `__pycache__/`, `venv/`)

### Step 1.2 — Configuration Loader

- [ ] Implement `config.py`:
  - Load `.env` via `python-dotenv`
  - Parse all feature flags as booleans
  - Parse numeric values (port, rate limit, chunk duration)
  - Parse comma-separated lists (`KEYWORD_LIST`)
  - Validate required paths exist (model paths when features enabled)
  - Export a `Config` dataclass or dict for app-wide use

**Checkpoint:** `python -c "from config import Config; c = Config(); print(c)"` prints loaded config.

### Step 1.3 — Database Layer

- [ ] Implement `database.py`:
  - `init_db()` — create tables if not exist (meetings, transcripts, action_items, speakers, settings)
  - `create_meeting(title, language)` → meeting_id
  - `end_meeting(meeting_id)` → update ended_at, duration_sec
  - `insert_segment(meeting_id, text, start_ms, end_ms, speaker_id, confidence)`
  - `get_meeting(meeting_id)` → dict
  - `list_meetings(status, limit, offset)` → list
  - `search_transcripts(query)` → FTS5 results
  - Use parameterized queries (`?` placeholders) throughout

**Checkpoint:** `python -c "from database import init_db; init_db()"` creates `data/meetings.db` with correct schema.

### Step 1.4 — Audio Capture

- [ ] Implement `audio.py`:
  - `list_devices()` — enumerate PyAudio input devices
  - `select_device(index_or_auto)` — pick USB mic by name or index
  - `AudioCapture` class:
    - Opens PyAudio stream (16kHz, mono, int16)
    - Captures audio in chunks of `AUDIO_CHUNK_DURATION_SEC`
    - Pushes chunks to a `queue.Queue`
    - `start()`, `stop()`, `is_running` interface
  - `MockAudioCapture` — generates silence or reads sample WAV

**Checkpoint:** `python audio.py` lists devices and captures 5 seconds of audio to `test.wav`.

### Step 1.5 — Flask Skeleton

- [ ] Implement basic `app.py`:
  - Flask app with SocketIO
  - Load config
  - Initialize database
  - Dark theme base template (`templates/base.html`)
  - Index route redirects to dashboard
- [ ] Create `static/css/style.css` — dark background, light text, card layout
- [ ] Create `static/js/app.js` — SocketIO client connection stub

**Checkpoint:** `python app.py` starts on port 5000, browser shows dark-themed placeholder page.

---

## Phase 2 — Transcription & Live Display

### Step 2.1 — Whisper.cpp Integration

- [ ] Implement `transcription.py`:
  - `TranscriptionEngine` class:
    - `load_model(path, model_size)` — load Whisper GGUF model
    - `transcribe_chunk(audio_np_array)` → `{ text, start_ms, end_ms, confidence, language }`
    - Handle model not found gracefully
  - `MockTranscriptionEngine` — returns canned segments with realistic timing

**Checkpoint:** Feed a WAV file to `TranscriptionEngine`, get text output with timestamps.

### Step 2.2 — Real-Time Pipeline

- [ ] Wire audio capture → transcription → database in `app.py`:
  - Background thread reads from audio queue
  - Passes each chunk to Whisper
  - Stores segment in SQLite
  - Emits segment via SocketIO
- [ ] Implement keyword highlighting (scan text for `KEYWORD_LIST` matches, wrap in `<mark>`)

**Checkpoint:** Start a meeting, speak into mic, see segments appearing in database and SocketIO events.

### Step 2.3 — Live Transcript Page

- [ ] Create `templates/meeting.html`:
  - SocketIO client listens for `new_segment` events
  - Appends segment to transcript container with timestamp
  - Auto-scrolls to bottom
  - Highlighted keywords rendered in accent color
  - Meeting title and duration timer at top
  - Stop meeting button

**Checkpoint:** Open meeting page, speak, transcript appears live with <2 second latency.

---

## Phase 3 — Dashboard & Authentication

### Step 3.1 — Authentication System

- [ ] Implement `auth.py`:
  - `hash_password(plaintext)` → bcrypt hash
  - `verify_password(plaintext, hash)` → bool
  - `login_required` decorator — checks session, redirects to login
  - Rate limiter — track attempts per IP, block after `RATE_LIMIT_MAX` in `RATE_LIMIT_WINDOW_MIN`
  - Session config: `SESSION_EXPIRY_HOURS` enforced via before_request

**Checkpoint:** Login with correct password succeeds; 11th rapid attempt returns 429.

### Step 3.2 — Login Page

- [ ] Create `templates/login.html`:
  - Username + password form
  - CSRF token
  - Error message display
  - Dark theme consistent with base
- [ ] Implement `/login` POST route (verify bcrypt, set session)
- [ ] Implement `/logout` route (clear session)

**Checkpoint:** Browse to dashboard → redirected to login → enter creds → see dashboard.

### Step 3.3 — Dashboard Pages

- [ ] Create `templates/dashboard.html`:
  - Active meeting card (if any) with live status indicator
  - Recent meetings list (last 10)
  - Quick-start new meeting button
  - System status (mic connected, models loaded)
- [ ] Create meeting detail view:
  - Full transcript timeline with speaker labels and timestamps
  - Meeting metadata (title, duration, language, started/ended)
  - Action items panel (if LLM enabled)
  - Export and privacy-wipe buttons
- [ ] Create `templates/settings.html`:
  - Display current feature flag states
  - Show loaded model paths and sizes

**Checkpoint:** Dashboard shows meeting list, clicking a meeting shows full transcript.

---

## Phase 4 — Archive, Search & Export

### Step 4.1 — Archive & Search

- [ ] Create `templates/archive.html`:
  - Paginated meeting list (10 per page)
  - Search box (FTS5 query)
  - Filter by date range and status
  - Results show snippet with highlighted match
- [ ] Implement `/api/search` route — accepts query, returns FTS results with snippets

**Checkpoint:** Search for a word spoken in a past meeting → results show matching segments.

### Step 4.2 — Export

- [ ] Implement `exporter.py`:
  - `export_markdown(meeting_id)` → Markdown string:
    ```markdown
    # Meeting: {title}
    **Date:** {date} | **Duration:** {duration}
    ## Transcript
    [00:01:23] Speaker 1: ...
    ## Action Items
    - [ ] TODO: ...
    ## Summary
    ...
    ```
  - `export_pdf(meeting_id)` → PDF bytes via ReportLab
- [ ] Add `/meeting/<id>/export/md` and `/meeting/<id>/export/pdf` routes

**Checkpoint:** Download MD and PDF for a completed meeting; content is correct and formatted.

### Step 4.3 — Privacy Wipe

- [ ] Implement `privacy.py`:
  - `secure_delete_file(path)` — overwrite with random bytes, then unlink
  - `wipe_meeting(meeting_id)` — delete transcripts, action items, audio files, set status='wiped'
- [ ] Add wipe button with confirmation modal on meeting detail page
- [ ] Add `/meeting/<id>/wipe` POST route (CSRF protected)

**Checkpoint:** Wipe a meeting → all data gone from DB and filesystem, status shows 'wiped'.

---

## Phase 5 — AI Features (LLM & Diarization)

### Step 5.1 — LLM Integration

- [ ] Implement `summarizer.py`:
  - `SummaryEngine` class:
    - `load_model(path, context_length, threads)` — load GGUF model via llama-cpp-python
    - `generate_summary(transcript_text)` → summary string
    - `extract_action_items(transcript_text)` → list of `{ type, description, assignee }`
  - Prompt templates:
    - Summary: "Summarize the following meeting transcript. Include key discussion points, decisions, and next steps.\n\nTranscript:\n{text}\n\nSummary:"
    - Action items: "Extract all action items from the following meeting transcript. For each item, specify the type (todo/decision/followup), description, and assignee if mentioned.\n\nTranscript:\n{text}\n\nAction Items (JSON):"
  - `MockSummaryEngine` — returns canned summary and action items

**Checkpoint:** Pass a sample transcript → get reasonable summary and action items list.

### Step 5.2 — Diarization

- [ ] Implement `diarization.py`:
  - `DiarizationEngine` class:
    - `init(backend)` — load resemblyzer or pyannote
    - `process_chunk(audio_np)` → speaker_label
    - `get_speaker_embedding(audio_np)` → embedding vector
  - Speaker profile storage in `speakers` table
  - `MockDiarizationEngine` — alternates between Speaker 1 and Speaker 2

**Checkpoint:** Diarize a multi-speaker audio → segments tagged with different speaker labels.

### Step 5.3 — Agenda Tracking

- [ ] Implement `agenda.py`:
  - `parse_agenda(text)` → list of agenda items
  - `check_discussed(agenda_items, transcript_segments)` → list with discussed=True/False
  - Upload route `/meeting/<id>/agenda` (POST, plain text or Markdown)
- [ ] Add agenda checklist UI on meeting page (discussed items checked off)

**Checkpoint:** Upload agenda → start meeting → discussed items auto-check as keywords appear.

---

## Phase 6 — Hardening & Deployment

### Step 6.1 — Security Hardening

- [ ] Add `Content-Security-Policy` header to all responses
- [ ] Add `X-Content-Type-Options: nosniff` header
- [ ] Add `X-Frame-Options: DENY` header
- [ ] Audit all user inputs for sanitization (meeting titles, search queries, agenda text)
- [ ] Verify all SQL uses parameterized queries
- [ ] Verify Jinja2 auto-escaping is enabled on all templates
- [ ] Test rate limiter under load

**Checkpoint:** Security headers present on all responses; injection attempts blocked.

### Step 6.2 — Error Handling & Logging

- [ ] Add structured logging to all modules (Python `logging` module)
- [ ] Log to file (`data/app.log`) and console
- [ ] Handle audio device disconnection gracefully (pause meeting, notify UI)
- [ ] Handle model load failure (disable feature, show warning)
- [ ] Handle disk full (stop recording, alert user)
- [ ] Add health check endpoint (`/api/health`)

**Checkpoint:** Disconnect mic during meeting → UI shows warning, meeting pauses.

### Step 6.3 — Deployment

- [ ] Create `deploy/deploy_to_pi.sh`:
  ```bash
  #!/bin/bash
  REMOTE="rasp-pi"
  REMOTE_DIR="~/ai-meeting-assistant"
  rsync -avz --exclude='venv' --exclude='data' --exclude='.env' \
    . ${REMOTE}:${REMOTE_DIR}/
  ssh ${REMOTE} "cd ${REMOTE_DIR} && source venv/bin/activate && pip install -r requirements.txt"
  ssh ${REMOTE} "sudo systemctl restart ai-meeting-assistant"
  ```
- [ ] Create systemd service file
- [ ] Test deploy script end-to-end
- [ ] Verify service starts on boot

**Checkpoint:** Run deploy script → service restarts on Pi → dashboard accessible at `http://192.168.216.90:5000`.

### Step 6.4 — Testing & Documentation

- [ ] Write unit tests for `transcription.py` (mock model, verify pipeline)
- [ ] Write unit tests for `auth.py` (bcrypt, rate limiter, session expiry)
- [ ] Write unit tests for `database.py` (CRUD, FTS, cascade delete)
- [ ] Write unit tests for `summarizer.py` (mock LLM, verify parsing)
- [ ] Write integration test: full meeting lifecycle
- [ ] Run all tests on Pi hardware
- [ ] Performance benchmark: transcription latency (target: <3s per 5s chunk)
- [ ] Performance benchmark: LLM summary time (target: <60s for 30-min meeting)
- [ ] Memory profile: 60-minute meeting stays under 6 GB RSS
- [ ] Final review of `README.md`, `TSD.md`, all docstrings
- [ ] Verify `.env.example` has all variables with comments

**Checkpoint:** All tests pass on Pi. README accurately reflects final implementation.
