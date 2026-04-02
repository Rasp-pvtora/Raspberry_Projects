# Technical Specification Document — Multi-Language Visual-Audio Translator

## 1. Scope

### In Scope

- Visual mode: Pi Camera capture → OCR (Tesseract/PaddleOCR) → LLM translation → display + TTS
- Audio mode: USB microphone → Whisper STT → LLM translation → display + TTS
- Conversation mode: turn-based bilingual dialogue with automatic language switching
- Document mode: photo/PDF upload → full-page OCR → structured translation
- Phrase book: pre-loaded common travel phrases per language pair
- Glossary support: upload domain-specific CSV/JSON glossary for translation context
- Subtitle overlay: live camera feed with translated text rendered over detected text regions
- TTS auto-play toggle (per-mode)
- Offline language packs: all models stored locally, no internet required
- At least 11 languages: EN, DE, FR, IT, ES, PT, NL, PL, RU, ZH, AR
- Dark-themed Flask + SocketIO web dashboard with auth
- bcrypt authentication with rate limiting and session expiry
- Mock mode for development/testing without hardware
- All features toggled via `.env`
- SQLite for persistence (translation history, sessions, glossaries, settings)
- Deployment via rsync to `rasp-pi` (192.168.216.90)

### Out of Scope

- Cloud-based translation APIs (Google Translate, DeepL, Azure)
- Real-time simultaneous interpretation (overlapping speech)
- Multi-user accounts with role-based access
- Speech diarization (speaker identification)
- Training custom language models
- Non-Linux operating systems
- Commercial licensing or paid features
- Streaming video translation (live video call interpretation)

---

## 2. MVP Features (P0)

| ID | Feature | Priority |
|----|---------|----------|
| P0-1 | Visual mode: camera capture → OCR → LLM translate → display | P0 |
| P0-2 | Audio mode: microphone → Whisper STT → LLM translate → display | P0 |
| P0-3 | TTS output via Piper (toggle auto-play) | P0 |
| P0-4 | LLM-based translation engine (llama-cpp-python, offline) | P0 |
| P0-5 | Language pair selector (source + target) | P0 |
| P0-6 | Web dashboard (dark theme, mode selector, translation display) | P0 |
| P0-7 | Authentication (bcrypt, rate limiting 10/15min, 24h session) | P0 |
| P0-8 | Translation history stored in SQLite | P0 |
| P0-9 | Mock mode (simulated OCR/STT for dev/testing) | P0 |
| P0-10 | Deploy script (rsync to rasp-pi, systemd service) | P0 |

### Nice-to-Have (P1/P2)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| P1-1 | Conversation mode (two-speaker bilingual) | P1 | Requires good VAD or push-to-talk |
| P1-2 | Document mode (PDF/image upload) | P1 | PyMuPDF + OCR pipeline |
| P1-3 | Phrase book browser | P1 | JSON data files per language pair |
| P1-4 | Glossary support (medical, legal, logistics) | P1 | CSV/JSON upload, LLM context injection |
| P1-5 | PaddleOCR as alternative OCR engine | P1 | Higher accuracy for complex scripts |
| P2-1 | Subtitle overlay on live camera feed | P2 | OpenCV text detection + rendering |
| P2-2 | Touchscreen kiosk mode | P2 | Optimized layout for 7" display |
| P2-3 | Translation quality feedback | P2 | Thumbs up/down per translation |

---

## 3. Database Schema

SQLite with WAL mode enabled. All timestamps stored as ISO-8601 UTC.

### Table: `translations`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique translation record ID |
| timestamp | TEXT | NOT NULL | ISO-8601 translation time |
| mode | TEXT | NOT NULL | VISUAL, AUDIO, CONVERSATION, DOCUMENT |
| source_lang | TEXT | NOT NULL | Source language code (e.g., EN) |
| target_lang | TEXT | NOT NULL | Target language code (e.g., DE) |
| source_text | TEXT | NOT NULL | Original extracted/transcribed text |
| translated_text | TEXT | NOT NULL | LLM-translated output |
| ocr_engine | TEXT | | tesseract or paddleocr (visual/document mode) |
| stt_model | TEXT | | Whisper model used (audio mode) |
| glossary_id | INTEGER | FK → glossaries.id | Glossary applied during translation |
| confidence | REAL | | OCR confidence or STT probability |
| processing_ms | INTEGER | | Total pipeline processing time |
| tts_played | INTEGER | DEFAULT 0 | 1 if TTS was played |

### Table: `conversation_sessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique session ID |
| started_at | TEXT | NOT NULL | ISO-8601 session start |
| ended_at | TEXT | | ISO-8601 session end |
| lang_a | TEXT | NOT NULL | Speaker A language code |
| lang_b | TEXT | NOT NULL | Speaker B language code |
| turn_count | INTEGER | DEFAULT 0 | Number of conversation turns |

### Table: `conversation_turns`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique turn ID |
| session_id | INTEGER | FK → conversation_sessions.id, NOT NULL | Parent session |
| timestamp | TEXT | NOT NULL | ISO-8601 turn time |
| speaker | TEXT | NOT NULL | A or B |
| source_text | TEXT | NOT NULL | Original spoken text |
| translated_text | TEXT | NOT NULL | Translated output |
| source_lang | TEXT | NOT NULL | Language spoken |
| target_lang | TEXT | NOT NULL | Language translated to |
| processing_ms | INTEGER | | Pipeline processing time |

### Table: `glossaries`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique glossary ID |
| name | TEXT | NOT NULL | Glossary name (e.g., "Medical EN→DE") |
| domain | TEXT | | Domain category (medical, legal, logistics) |
| source_lang | TEXT | NOT NULL | Source language code |
| target_lang | TEXT | NOT NULL | Target language code |
| entry_count | INTEGER | DEFAULT 0 | Number of term pairs |
| file_path | TEXT | NOT NULL | Path to glossary file |
| uploaded_at | TEXT | NOT NULL | ISO-8601 upload time |

### Table: `glossary_entries`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique entry ID |
| glossary_id | INTEGER | FK → glossaries.id, NOT NULL | Parent glossary |
| source_term | TEXT | NOT NULL | Term in source language |
| target_term | TEXT | NOT NULL | Translated term |

### Table: `phrasebook_usage`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique usage record ID |
| timestamp | TEXT | NOT NULL | ISO-8601 usage time |
| lang_pair | TEXT | NOT NULL | Language pair (e.g., "en_de") |
| category | TEXT | NOT NULL | Phrase category (greetings, medical, etc.) |
| phrase_id | TEXT | NOT NULL | Phrase identifier within the file |
| tts_played | INTEGER | DEFAULT 0 | 1 if TTS was triggered |

### Table: `settings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | TEXT | PK | Setting name |
| value | TEXT | | Setting value (JSON-encoded) |
| updated_at | TEXT | NOT NULL | ISO-8601 last update time |

---

## 4. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Raspberry Pi                                     │
│                                                                             │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐    │
│  │ Pi Camera   │────>│              INPUT LAYER                        │    │
│  │ Module v3   │     │                                                 │    │
│  └─────────────┘     │  ┌───────────────┐    ┌──────────────────────┐ │    │
│                      │  │ OCR Engine    │    │ STT Engine           │ │    │
│  ┌─────────────┐     │  │ (Tesseract /  │    │ (Whisper.cpp)        │ │    │
│  │ USB         │────>│  │  PaddleOCR)   │    │ - tiny/base/small    │ │    │
│  │ Microphone  │     │  └───────┬───────┘    └──────────┬───────────┘ │    │
│  └─────────────┘     │          │                       │             │    │
│                      └──────────┼───────────────────────┼─────────────┘    │
│                                 │                       │                  │
│                      ┌──────────▼───────────────────────▼─────────────┐    │
│                      │           TRANSLATION LAYER                    │    │
│                      │                                                │    │
│                      │  ┌─────────────────────────────────────────┐   │    │
│                      │  │ LLM Translator (llama-cpp-python)       │   │    │
│                      │  │ - Language detection                    │   │    │
│                      │  │ - Translation with glossary context     │   │    │
│                      │  │ - Summarization (document mode)         │   │    │
│                      │  └─────────────────┬───────────────────────┘   │    │
│                      │                    │                           │    │
│                      │  ┌─────────────────▼───────────────────────┐   │    │
│                      │  │ Glossary Manager                        │   │    │
│                      │  │ - Load domain glossaries                │   │    │
│                      │  │ - Inject terms into LLM prompt          │   │    │
│                      │  └─────────────────────────────────────────┘   │    │
│                      └────────────────────┬───────────────────────────┘    │
│                                           │                                │
│                      ┌────────────────────▼───────────────────────────┐    │
│                      │           OUTPUT LAYER                         │    │
│                      │                                                │    │
│                      │  ┌──────────────┐    ┌──────────────────────┐  │    │
│                      │  │ Display      │    │ Piper TTS Engine     │  │    │
│                      │  │ (Dashboard)  │    │ - Auto-play toggle   │  │    │
│                      │  └──────────────┘    └──────────┬───────────┘  │    │
│                      │                                  │             │    │
│                      │  ┌──────────────┐    ┌──────────▼───────────┐  │    │
│                      │  │ Subtitle     │    │ Speaker              │  │    │
│                      │  │ Overlay      │    │ (3.5mm / USB)        │  │    │
│                      │  └──────────────┘    └──────────────────────┘  │    │
│                      └────────────────────────────────────────────────┘    │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SQLite Database                                                    │   │
│  │  translations | conversation_sessions | conversation_turns          │   │
│  │  glossaries   | glossary_entries      | phrasebook_usage | settings │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Flask + SocketIO Dashboard                                         │   │
│  │  - bcrypt auth (rate limit 10/15min, 24h session)                  │   │
│  │  - Dark theme, mode tabs, language pair selector                   │   │
│  │  - Real-time translation, conversation view, document results      │   │
│  │  - Phrase book browser, glossary manager, settings panel           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Threat Model

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| Brute-force login to dashboard | Unauthorized access | Medium | bcrypt hashing, rate limiting (10/15min), session expiry (24h) |
| Session hijacking (cookie theft) | Impersonate admin | Low | Secure cookie flags, `SECRET_KEY` rotation, session expiry |
| CSRF on translation actions | Unauthorized operations | Medium | CSRF tokens on all forms, SameSite cookie attribute |
| SQLite injection via form input | Data corruption/exfiltration | Low | Parameterized queries, input validation |
| Malicious file upload (document mode) | Code execution, DoS | Medium | File type validation, size limits, in-memory processing, no shell exec |
| Denial of service on dashboard | Service unavailable | Low | Rate limiting, bind to LAN only |
| Malicious .env modification | Feature disabling, config theft | Medium | File permissions (600), deploy via rsync only |
| Glossary file injection | LLM prompt manipulation | Medium | Sanitize glossary entries, validate CSV/JSON format |
| LLM prompt injection via OCR/STT | Manipulate translation output | Low | Sanitize extracted text before LLM prompt, structured prompt templates |
| Physical device theft | Data exposure | Medium | Disk encryption, strong admin password |
| Microphone eavesdropping | Privacy violation | Low | Audio processed in memory only, no persistent recording |
| Camera privacy | Unintended image capture | Low | Camera activated only on user action, no background recording |

---

## 6. Tech Stack

| Layer | Technology | Version / Notes |
|-------|-----------|-----------------|
| Language | Python 3.11+ | Type hints throughout |
| Web framework | Flask | 3.x with app factory pattern |
| Real-time | Flask-SocketIO | eventlet async mode |
| OCR (primary) | pytesseract | Tesseract 5.x backend |
| OCR (alternative) | PaddleOCR | Optional, higher accuracy for complex scripts |
| STT | whispercpp | Whisper.cpp Python bindings |
| LLM | llama-cpp-python | GGUF quantized models (Q4_K_M) |
| TTS | piper-tts | Offline neural TTS |
| Camera | picamera2 + OpenCV | Pi Camera Module v3 |
| Image processing | opencv-python-headless | Text region detection, subtitle overlay |
| Audio capture | pyaudio | Microphone recording & speaker playback |
| Image manipulation | Pillow | Pre-processing for OCR |
| PDF extraction | PyMuPDF (fitz) | PDF page rendering & text extraction |
| Auth | bcrypt | Password hashing |
| Config | python-dotenv | `.env` loader |
| Database | SQLite3 | WAL mode, stdlib `sqlite3` |
| Templates | Jinja2 | Bundled with Flask |
| CSS | Custom dark theme | No framework |
| Deployment | rsync + systemd | SSH alias `rasp-pi` |
| Testing | pytest + pytest-cov | Mocking with unittest.mock |

---

## 7. Development Phases

### Phase 1 — Project Foundation & Core Engines

**Goal:** Scaffold the project, set up configuration, database, and build the OCR, STT, TTS, and translation engines.

| # | Task | Deliverable |
|---|------|-------------|
| 1.1 | Initialize project structure (dirs, `pyproject.toml`, `requirements.txt`) | Repo skeleton |
| 1.2 | Implement `.env` config loader with dataclass validation | `src/config.py` |
| 1.3 | Implement SQLite database module with schema (WAL mode) | `src/database.py` |
| 1.4 | Implement OCR engine wrapper (Tesseract + optional PaddleOCR) | `src/ocr_engine.py` |
| 1.5 | Implement STT engine wrapper (Whisper.cpp) | `src/stt_engine.py` |
| 1.6 | Implement TTS engine wrapper (Piper) | `src/tts_engine.py` |
| 1.7 | Implement LLM translation engine (llama-cpp-python) | `src/translator.py` |
| 1.8 | Implement mock mode (simulated OCR/STT/translation) | Mock paths in engines |
| 1.9 | Write unit tests for all engines | `tests/` |

### Phase 2 — Visual & Audio Mode Integration

**Goal:** Build the camera and microphone pipelines connecting input → processing → output.

| # | Task | Deliverable |
|---|------|-------------|
| 2.1 | Implement camera module (capture, preview, streaming) | `src/camera.py` |
| 2.2 | Implement audio module (mic recording, speaker playback) | `src/audio.py` |
| 2.3 | Build visual mode pipeline (camera → OCR → translate → display + TTS) | Pipeline integration |
| 2.4 | Build audio mode pipeline (mic → STT → translate → display + TTS) | Pipeline integration |
| 2.5 | Implement translation history persistence | `src/database.py` |
| 2.6 | Write integration tests for both pipelines | `tests/` |

### Phase 3 — Web Dashboard & Authentication

**Goal:** Build the dark-themed web dashboard with real-time updates and secure auth.

| # | Task | Deliverable |
|---|------|-------------|
| 3.1 | Implement Flask app factory with SocketIO | `src/app.py` |
| 3.2 | Implement bcrypt auth with rate limiting (10/15min) and session (24h) | `src/auth.py` |
| 3.3 | Create dark-theme base template and CSS | `templates/`, `static/` |
| 3.4 | Build login page | `templates/login.html` |
| 3.5 | Build dashboard page (mode selector, language pair selector) | `templates/dashboard.html` |
| 3.6 | Build visual mode page (camera view, OCR result, translation) | `templates/visual.html` |
| 3.7 | Build audio mode page (record button, transcript, translation) | `templates/audio.html` |
| 3.8 | Implement SocketIO events for real-time translation display | `src/app.py`, `static/js/` |
| 3.9 | Build settings panel (feature toggles, language config) | `templates/settings.html` |
| 3.10 | Write auth and API tests | `tests/` |

### Phase 4 — Conversation & Document Modes

**Goal:** Implement conversation mode and document upload/translation.

| # | Task | Deliverable |
|---|------|-------------|
| 4.1 | Implement conversation controller (turn management, language switching) | `src/conversation.py` |
| 4.2 | Build conversation mode page (dual-panel, push-to-talk) | `templates/conversation.html` |
| 4.3 | Implement conversation session and turn persistence | `src/database.py` |
| 4.4 | Implement document processor (PDF/image → OCR → translate) | `src/document.py` |
| 4.5 | Build document upload page (file picker, progress, results) | `templates/document.html` |
| 4.6 | Implement file validation and size limits | `src/document.py` |
| 4.7 | Write conversation and document mode tests | `tests/` |

### Phase 5 — Phrase Book, Glossary & Subtitle Overlay

**Goal:** Add phrase book browser, glossary support, and subtitle overlay.

| # | Task | Deliverable |
|---|------|-------------|
| 5.1 | Implement phrase book manager (load JSON, browse by category) | `src/phrasebook.py` |
| 5.2 | Create phrase book data files for 3+ language pairs | `data/phrasebooks/` |
| 5.3 | Build phrase book page (category browser, TTS play buttons) | `templates/phrasebook.html` |
| 5.4 | Implement glossary loader (CSV/JSON parse, DB storage) | `src/glossary.py` |
| 5.5 | Integrate glossary into LLM translation prompt | `src/translator.py` |
| 5.6 | Build glossary management UI (upload, list, delete) | `templates/settings.html` |
| 5.7 | Implement subtitle overlay (OpenCV text detection + rendering) | `src/subtitle.py` |
| 5.8 | Write phrase book, glossary, and subtitle tests | `tests/` |

### Phase 6 — Deployment & Documentation

**Goal:** Finalize deploy pipeline, systemd service, and all documentation.

| # | Task | Deliverable |
|---|------|-------------|
| 6.1 | Create deploy script (rsync to rasp-pi) | `deploy/deploy_to_pi.sh` |
| 6.2 | Create model download script | `scripts/download_models.sh` |
| 6.3 | Create OS dependency installer script | `scripts/install_deps.sh` |
| 6.4 | Write systemd service unit file | Documentation in README |
| 6.5 | Write threat model document | `docs/threat_model.md` |
| 6.6 | Final integration testing on Raspberry Pi hardware | Test report |
| 6.7 | Update README with final instructions | `README.md` |

---

## 8. `.env.default` Reference

```ini
# ─── Flask & Security ──────────────────────────────────────
SECRET_KEY=change-me-to-a-random-string
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...  # bcrypt hash of your password

# ─── Database ──────────────────────────────────────────────
DB_PATH=data/translator.db

# ─── Visual Mode (OCR) ────────────────────────────────────
ENABLE_VISUAL_MODE=true
OCR_ENGINE=tesseract
OCR_LANGUAGES=eng+deu+fra
CAMERA_RESOLUTION=1920x1080
CAMERA_ROTATION=0

# ─── Audio Mode (STT) ─────────────────────────────────────
ENABLE_AUDIO_MODE=true
WHISPER_MODEL_PATH=data/models/whisper-base.bin
WHISPER_MODEL_SIZE=base
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_DURATION=5
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default

# ─── Translation (LLM) ────────────────────────────────────
ENABLE_TRANSLATION=true
LLM_MODEL_PATH=data/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
LLM_CONTEXT_SIZE=2048
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.1
DEFAULT_SOURCE_LANG=EN
DEFAULT_TARGET_LANG=DE

# ─── TTS ───────────────────────────────────────────────────
ENABLE_TTS=true
TTS_AUTO_PLAY=true
PIPER_MODEL_PATH=data/models/piper/
PIPER_SPEAKER=default

# ─── Conversation Mode ────────────────────────────────────
ENABLE_CONVERSATION_MODE=true
CONVERSATION_LANG_A=EN
CONVERSATION_LANG_B=DE
CONVERSATION_INPUT_MODE=push_to_talk

# ─── Document Mode ────────────────────────────────────────
ENABLE_DOCUMENT_MODE=true
MAX_UPLOAD_SIZE_MB=20
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf

# ─── Phrase Book ──────────────────────────────────────────
ENABLE_PHRASEBOOK=true
PHRASEBOOK_DIR=data/phrasebooks/

# ─── Glossary ─────────────────────────────────────────────
ENABLE_GLOSSARY=true
GLOSSARY_DIR=data/glossaries/
MAX_GLOSSARY_ENTRIES=5000

# ─── Subtitle Overlay ────────────────────────────────────
ENABLE_SUBTITLE_OVERLAY=false

# ─── Web Dashboard ────────────────────────────────────────
ENABLE_WEB_DASHBOARD=true
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
SESSION_EXPIRY_HOURS=24
RATE_LIMIT=10/15min

# ─── Development ──────────────────────────────────────────
MOCK_MODE=false
LOG_LEVEL=INFO
```

---

## 9. Deliverables

| # | Deliverable | Format | Notes |
|---|-------------|--------|-------|
| 1 | OCR engine wrapper (Tesseract + PaddleOCR) | Python module | `src/ocr_engine.py` |
| 2 | STT engine wrapper (Whisper.cpp) | Python module | `src/stt_engine.py` |
| 3 | TTS engine wrapper (Piper) | Python module | `src/tts_engine.py` |
| 4 | LLM translation engine | Python module | `src/translator.py` |
| 5 | Camera module | Python module | `src/camera.py` |
| 6 | Audio module (mic + speaker) | Python module | `src/audio.py` |
| 7 | Conversation mode controller | Python module | `src/conversation.py` |
| 8 | Document processor (PDF/image) | Python module | `src/document.py` |
| 9 | Phrase book manager | Python module | `src/phrasebook.py` |
| 10 | Glossary loader & manager | Python module | `src/glossary.py` |
| 11 | Subtitle overlay engine | Python module | `src/subtitle.py` |
| 12 | SQLite database layer | Python module | `src/database.py` |
| 13 | Flask + SocketIO web dashboard | Python + HTML/JS/CSS | `src/app.py`, `templates/`, `static/` |
| 14 | bcrypt auth with rate limiting | Python module | `src/auth.py` |
| 15 | Configuration loader | Python module | `src/config.py` |
| 16 | Model download script | Bash | `scripts/download_models.sh` |
| 17 | OS dependency installer | Bash | `scripts/install_deps.sh` |
| 18 | Deploy script | Bash | `deploy/deploy_to_pi.sh` |
| 19 | systemd service unit | INI | Documented in README |
| 20 | Test suite (≥80% coverage) | pytest | `tests/` |
| 21 | Threat model | Markdown | `docs/threat_model.md` |
| 22 | Phrase book data files | JSON | `data/phrasebooks/` |
| 23 | README & TSD | Markdown | Root-level docs |
