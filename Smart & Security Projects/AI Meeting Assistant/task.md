# Task List — AI Meeting Assistant

## Phase 1 — Foundation & Audio Pipeline

- [ ] Create project directory structure
- [ ] Create `requirements.txt` with all dependencies
- [ ] Create `.env.example` with all variables and defaults
- [ ] Implement `config.py` — load `.env`, parse feature flags, validate paths
- [ ] Implement `database.py` — SQLite schema init (meetings, transcripts, action_items, speakers, settings)
- [ ] Create FTS5 virtual table for transcript search
- [ ] Add database migration/versioning support
- [ ] Implement `audio.py` — PyAudio device discovery and selection
- [ ] Implement audio capture loop (16kHz, mono, configurable chunk duration)
- [ ] Implement audio buffering and chunk queue
- [ ] Add mock audio mode (reads from sample WAV or generates silence)
- [ ] Create basic Flask app skeleton (`app.py`)
- [ ] Set up Jinja2 base template with dark theme
- [ ] Create `static/css/style.css` (dark theme dashboard)
- [ ] Create `static/js/app.js` (client-side SocketIO stub)
- [ ] Verify USB microphone detection on Pi

## Phase 2 — Transcription & Live Display

- [ ] Implement `transcription.py` — load Whisper.cpp model
- [ ] Implement chunked transcription pipeline (audio buffer → Whisper → text)
- [ ] Store transcript segments in SQLite with timestamps and segment index
- [ ] Add confidence score tracking per segment
- [ ] Add mock transcription mode (returns canned text)
- [ ] Set up Flask-SocketIO server in `app.py`
- [ ] Implement WebSocket event: broadcast new transcript segment
- [ ] Create `templates/meeting.html` — live transcript page
- [ ] Implement auto-scroll and new-segment animation
- [ ] Implement keyword highlighting (configurable `KEYWORD_LIST`)
- [ ] Add language selection support (`WHISPER_LANGUAGE`)
- [ ] Test real-time latency on Pi 4 with tiny model

## Phase 3 — Dashboard & Authentication

- [ ] Implement `auth.py` — bcrypt password verification
- [ ] Implement login route and `templates/login.html`
- [ ] Implement session management (server-side, 24h expiry)
- [ ] Add `@login_required` decorator for protected routes
- [ ] Implement rate limiting middleware (10 req / 15 min / IP)
- [ ] Add CSRF protection to all forms
- [ ] Create `templates/dashboard.html` — home page (active meeting, recent list)
- [ ] Create meeting detail view (full transcript timeline, metadata)
- [ ] Create `templates/settings.html` — runtime config display
- [ ] Add start/stop meeting controls on dashboard
- [ ] Add meeting title and metadata editing
- [ ] Toggle auth on/off via `AUTH_ENABLED`

## Phase 4 — Archive, Search & Export

- [ ] Implement archive list view with pagination
- [ ] Implement full-text search across transcripts (FTS5)
- [ ] Add search filters: date range, language, status
- [ ] Create `templates/archive.html` — browse and search view
- [ ] Implement `exporter.py` — Markdown export (transcript + summary + action items)
- [ ] Implement PDF export via ReportLab
- [ ] Add export download routes (per-meeting)
- [ ] Implement `privacy.py` — secure overwrite before delete
- [ ] Add cascade delete (meeting → transcripts → action items)
- [ ] Add privacy wipe button on meeting detail page
- [ ] Add privacy wipe confirmation dialog
- [ ] Implement multi-language selector in meeting start flow

## Phase 5 — AI Features (LLM & Diarization)

- [ ] Implement `summarizer.py` — load llama.cpp model
- [ ] Design LLM prompt template for meeting summary
- [ ] Implement meeting summary generation (post-meeting)
- [ ] Design LLM prompt template for action item extraction
- [ ] Implement action item extraction (TODO, decision, follow-up)
- [ ] Store action items in database with type, assignee, status
- [ ] Add action item display on meeting detail page
- [ ] Add action item status toggle (open/done/dismissed)
- [ ] Implement `diarization.py` — resemblyzer speaker embedding
- [ ] Implement speaker segmentation in audio pipeline
- [ ] Tag transcript segments with speaker labels
- [ ] Add speaker profile management (rename labels)
- [ ] Implement `agenda.py` — upload agenda text/Markdown
- [ ] Implement agenda-to-keyword mapping
- [ ] Track discussed vs. pending agenda items
- [ ] Add agenda checklist view on meeting page
- [ ] Add pyannote-audio backend as alternative diarizer

## Phase 6 — Hardening & Deployment

- [ ] Create `deploy/deploy_to_pi.sh` — SCP + service restart
- [ ] Create systemd service file template
- [ ] Add Content-Security-Policy headers
- [ ] Audit all routes for input validation
- [ ] Audit all database queries for parameterized statements
- [ ] Add structured logging (file + console)
- [ ] Add error handling for audio device disconnection
- [ ] Add error handling for model loading failure
- [ ] Add error handling for disk full / database write failure
- [ ] Performance benchmark: transcription latency on Pi 4
- [ ] Performance benchmark: LLM summary generation time on Pi 4
- [ ] Memory profiling under sustained meeting (60 min)
- [ ] Write unit tests for `transcription.py`
- [ ] Write unit tests for `auth.py`
- [ ] Write unit tests for `database.py`
- [ ] Write unit tests for `summarizer.py`
- [ ] Write integration test: full meeting flow (start → transcribe → stop → export)
- [ ] Update `README.md` with final instructions
- [ ] Final `.env.example` review — all variables documented
