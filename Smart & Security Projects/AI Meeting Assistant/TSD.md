# Technical Specification Document — AI Meeting Assistant

## 1. Project Scope

A fully local, privacy-first AI meeting transcription and summarization system for Raspberry Pi. The system captures audio from a USB microphone array, transcribes speech in real time using Whisper.cpp, optionally identifies speakers via diarization, and generates summaries/action items using a local LLM. A Flask web dashboard with dark theme provides live transcript display, archive search, export, and administration. All processing is on-device — no data leaves the Pi.

**Target hardware:** Raspberry Pi 4 (8 GB) / Pi 5 with USB microphone array.

**Security posture:** Designed for high-security corporate environments where cloud AI is prohibited. Zero network dependency for core functionality.

---

## 2. Feature Tiers

### P0 — MVP (Must Have)

| Feature | Description |
|---|---|
| Real-time transcription | Whisper.cpp tiny/base model, chunked audio pipeline |
| Live transcript display | Flask-SocketIO WebSocket to browser |
| Meeting archive | SQLite with full-text search (FTS5) |
| Web dashboard | Flask dark theme, meeting list/detail/search |
| Authentication | bcrypt hashing, rate limiting (10/15 min), 24h session |
| Export | Markdown export of transcript and metadata |
| Privacy wipe | Secure one-click delete of meeting data |
| Mock mode | Simulated audio and model responses for development |
| Configuration | All features toggleable via `.env` |

### P1 — Nice to Have

| Feature | Description |
|---|---|
| Speaker diarization | Voice ID via resemblyzer or pyannote-audio |
| LLM summarization | TinyLlama/Phi-3 via llama.cpp for meeting summary |
| Action item extraction | LLM-based TODO/decision/follow-up extraction |
| Agenda tracking | Upload agenda, track discussed items vs. pending |
| PDF export | ReportLab-generated PDF summaries |
| Keyword highlighting | Configurable keyword list with visual highlights |
| Multi-language | Whisper 99-language support, auto-detect mode |

---

## 3. Database Schema

```sql
-- Core meeting record
CREATE TABLE meetings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL DEFAULT 'Untitled Meeting',
    started_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at        DATETIME,
    duration_sec    INTEGER,
    language        TEXT DEFAULT 'en',
    agenda_text     TEXT,
    summary         TEXT,
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'completed', 'wiped')),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Transcript segments (one per Whisper chunk)
CREATE TABLE transcripts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id      INTEGER NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    speaker_id      INTEGER REFERENCES speakers(id),
    segment_index   INTEGER NOT NULL,
    start_time_ms   INTEGER NOT NULL,
    end_time_ms     INTEGER NOT NULL,
    text            TEXT NOT NULL,
    confidence      REAL,
    language        TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Full-text search virtual table
CREATE VIRTUAL TABLE transcripts_fts USING fts5(
    text,
    content='transcripts',
    content_rowid='id'
);

-- Action items extracted by LLM
CREATE TABLE action_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id      INTEGER NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    speaker_id      INTEGER REFERENCES speakers(id),
    type            TEXT NOT NULL DEFAULT 'todo'
                    CHECK (type IN ('todo', 'decision', 'followup')),
    description     TEXT NOT NULL,
    assignee        TEXT,
    due_date        TEXT,
    status          TEXT NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'done', 'dismissed')),
    source_segment  INTEGER REFERENCES transcripts(id),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Speaker profiles
CREATE TABLE speakers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    label           TEXT NOT NULL DEFAULT 'Unknown',
    display_name    TEXT,
    voice_embedding BLOB,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Application settings (key-value)
CREATE TABLE settings (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_transcripts_meeting ON transcripts(meeting_id);
CREATE INDEX idx_transcripts_speaker ON transcripts(speaker_id);
CREATE INDEX idx_action_items_meeting ON action_items(meeting_id);
CREATE INDEX idx_action_items_status ON action_items(status);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_started ON meetings(started_at);
```

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Raspberry Pi (Local)                              │
│                                                                             │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────────┐   ┌──────────────┐ │
│  │ USB Mic  │──▶│ audio.py     │──▶│ transcription.py│──▶│ database.py  │ │
│  │ Array    │   │ PyAudio      │   │ Whisper.cpp     │   │ SQLite + FTS │ │
│  └──────────┘   │ 16kHz mono   │   │ Chunked STT     │   └──────┬───────┘ │
│                 └──────────────┘   └────────┬────────┘          │         │
│                                              │                   │         │
│              ┌───────────────────────────────┼───────────────────┤         │
│              │                               │                   │         │
│              ▼                               ▼                   ▼         │
│  ┌──────────────────┐            ┌────────────────┐   ┌────────────────┐  │
│  │ diarization.py   │            │ Flask-SocketIO  │   │ summarizer.py  │  │
│  │ resemblyzer /    │            │ Live WebSocket  │   │ llama.cpp LLM  │  │
│  │ pyannote-audio   │            │ Broadcast       │   │ Summary +      │  │
│  └──────────────────┘            └────────────────┘   │ Action Items   │  │
│                                                        └────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Flask Web Dashboard (Dark Theme)                  │   │
│  │  ┌───────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────────────┐ │   │
│  │  │ Login     │ │ Dashboard   │ │ Archive  │ │ Settings          │ │   │
│  │  │ (bcrypt)  │ │ Live View   │ │ FTS      │ │ .env overrides    │ │   │
│  │  └───────────┘ └─────────────┘ └──────────┘ └───────────────────┘ │   │
│  │  ┌────────────────┐ ┌─────────────┐ ┌──────────────────────────┐  │   │
│  │  │ Agenda Tracker │ │ Export      │ │ Privacy Wipe             │  │   │
│  │  │ (checklist)    │ │ MD / PDF    │ │ (secure overwrite+delete)│  │   │
│  │  └────────────────┘ └─────────────┘ └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Security Layer                                                      │   │
│  │  • bcrypt auth   • Rate limit: 10 req / 15 min   • 24h sessions   │   │
│  │  • CSRF tokens   • Input validation              • Secure delete   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Threat Model

| Threat | Impact | Mitigation |
|---|---|---|
| Unauthorized dashboard access | Data exposure | bcrypt auth, rate limiting, session expiry |
| Session hijacking | Impersonation | Secure cookies, 24h expiry, server-side sessions |
| Brute-force login | Account compromise | Rate limit: 10 attempts / 15 min per IP |
| CSRF attacks | Unauthorized actions | CSRF tokens on all forms |
| SQL injection | Data breach | Parameterized queries only (SQLite `?` placeholders) |
| XSS in transcript display | Script injection | Jinja2 auto-escaping, Content-Security-Policy headers |
| Physical SD card theft | Full data exposure | LUKS disk encryption recommended, privacy wipe |
| Audio eavesdropping | Privacy breach | USB-only mic (no wireless), LAN-only dashboard |
| Model supply chain | Malicious model | Verify model checksums after download |
| Denial of service | Service outage | Rate limiting, resource limits in systemd |
| Stale data exposure | Privacy violation | Privacy wipe with secure overwrite |
| Unencrypted network traffic | Data interception | Nginx reverse proxy with TLS (Let's Encrypt) |

---

## 6. Tech Stack

| Layer | Technology |
|---|---|
| Hardware | Raspberry Pi 4 (8 GB) / Pi 5, USB Mic Array |
| OS | Raspberry Pi OS (64-bit, Bookworm) |
| Runtime | Python 3.11+ |
| Web Framework | Flask 3.x + Flask-SocketIO |
| WebSocket | python-socketio (eventlet or gevent) |
| Templates | Jinja2 (dark theme) |
| STT Engine | Whisper.cpp via `whispercpp` Python bindings |
| LLM Engine | llama.cpp via `llama-cpp-python` |
| Diarization | resemblyzer (default) / pyannote-audio (optional) |
| Audio Capture | PyAudio + numpy |
| Database | SQLite 3 with FTS5 |
| Auth | bcrypt + Flask sessions |
| PDF Export | ReportLab |
| Config | python-dotenv (`.env` file) |
| Process Manager | systemd |
| Deployment | SCP / rsync to `rasp-pi` (192.168.216.90) |

---

## 7. Implementation Phases

### Phase 1 — Foundation & Audio Pipeline

- Project scaffolding (directory structure, `.env`, config loader)
- SQLite database initialization with schema
- PyAudio capture from USB microphone array
- Audio chunking and buffering (configurable chunk duration)
- Mock mode for development without hardware
- Basic Flask app skeleton with dark theme

### Phase 2 — Transcription & Live Display

- Whisper.cpp integration (model loading, chunked inference)
- Real-time transcription pipeline (audio → Whisper → text)
- Transcript storage in SQLite with timestamps
- Flask-SocketIO WebSocket server
- Live transcript page with auto-scroll
- Keyword highlighting in live feed

### Phase 3 — Dashboard & Authentication

- bcrypt authentication (login page, session management)
- Rate limiting middleware (10 req / 15 min / IP)
- Session expiry (24 hours)
- Dashboard home (active meeting, recent meetings)
- Meeting detail view (transcript timeline, metadata)
- Settings page (runtime config overrides)

### Phase 4 — Archive, Search & Export

- Full-text search (FTS5) across all transcripts
- Archive browse view with pagination and filters
- Markdown export (transcript + metadata + action items)
- PDF export via ReportLab
- Privacy wipe (secure overwrite + cascade delete)
- Multi-language transcription selector

### Phase 5 — AI Features (LLM & Diarization)

- llama.cpp integration (model loading, prompt templates)
- Meeting summary generation (post-meeting LLM pass)
- Action item extraction (TODO, decision, follow-up parsing)
- Speaker diarization integration (resemblyzer default)
- Speaker labeling in transcript segments
- Agenda upload and discussed-item tracking

### Phase 6 — Hardening & Deployment

- systemd service configuration
- Deploy script (`deploy_to_pi.sh`)
- CSRF protection on all forms
- Content-Security-Policy headers
- Input validation and sanitization audit
- Error handling and logging
- Performance profiling (Pi 4 benchmarks)
- Documentation finalization

---

## 8. Default Environment Configuration

```ini
# .env.default — AI Meeting Assistant

# --- Flask ---
SECRET_KEY=change-me-in-production
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false

# --- Authentication ---
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=
SESSION_EXPIRY_HOURS=24
RATE_LIMIT_MAX=10
RATE_LIMIT_WINDOW_MIN=15

# --- Transcription (Whisper.cpp) ---
TRANSCRIPTION_ENABLED=true
WHISPER_MODEL_PATH=models/whisper/ggml-tiny.bin
WHISPER_MODEL_SIZE=tiny
WHISPER_LANGUAGE=en

# --- Speaker Diarization ---
DIARIZATION_ENABLED=false
DIARIZATION_BACKEND=resemblyzer
PYANNOTE_AUTH_TOKEN=

# --- LLM (llama.cpp) ---
LLM_ENABLED=false
LLM_MODEL_PATH=models/llm/tinyllama-1.1b-chat.Q4_K_M.gguf
LLM_CONTEXT_LENGTH=2048
LLM_THREADS=4

# --- Features ---
LIVE_DISPLAY_ENABLED=true
ACTION_ITEMS_ENABLED=false
SUMMARY_ENABLED=false
EXPORT_ENABLED=true
KEYWORD_HIGHLIGHT_ENABLED=true
KEYWORD_LIST=budget,deadline,action,decision
ARCHIVE_ENABLED=true
AGENDA_TRACKING_ENABLED=false
PRIVACY_WIPE_ENABLED=true

# --- Audio ---
AUDIO_DEVICE_INDEX=auto
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_CHUNK_DURATION_SEC=5

# --- Database ---
DB_PATH=data/meetings.db

# --- Development ---
MOCK_MODE=false
```

---

## 9. Deliverables

| Deliverable | Format | Description |
|---|---|---|
| `app.py` | Python | Flask application entry point with SocketIO |
| `config.py` | Python | `.env` loader, feature flags, validation |
| `auth.py` | Python | bcrypt auth, rate limiting, session management |
| `audio.py` | Python | PyAudio capture, chunking, mock mode |
| `transcription.py` | Python | Whisper.cpp wrapper, streaming transcription |
| `diarization.py` | Python | Speaker ID via resemblyzer / pyannote |
| `summarizer.py` | Python | llama.cpp wrapper, summary + action extraction |
| `database.py` | Python | SQLite schema, CRUD, FTS queries |
| `exporter.py` | Python | Markdown + PDF export |
| `agenda.py` | Python | Agenda parsing, discussed-item tracking |
| `privacy.py` | Python | Secure overwrite + cascade delete |
| `templates/` | HTML/Jinja2 | Dark theme dashboard pages |
| `static/` | CSS/JS | Styles + SocketIO client |
| `deploy/deploy_to_pi.sh` | Bash | SCP deploy + service restart |
| `tests/` | Python | Unit + integration tests |
| `requirements.txt` | Text | Pinned Python dependencies |
| `.env.example` | Text | Environment variable template |
| `README.md` | Markdown | Full project documentation |
