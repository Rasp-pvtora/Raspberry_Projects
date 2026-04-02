# Task List — Multi-Language Visual-Audio Translator

## Phase 1 — Project Foundation & Core Engines

- [ ] **1.1 Initialize project structure**
  - [ ] Create directory tree (`src/`, `templates/`, `static/css/`, `static/js/`, `tests/`, `deploy/`, `scripts/`, `docs/`, `data/models/`, `data/phrasebooks/`, `data/glossaries/`, `data/languages/`)
  - [ ] Create `pyproject.toml` with project metadata
  - [ ] Create `requirements.txt` with all dependencies
  - [ ] Create `.env.example` with all variables and defaults
  - [ ] Create `src/__init__.py`
  - [ ] Create `tests/__init__.py` and `tests/conftest.py`

- [ ] **1.2 Implement configuration loader**
  - [ ] Create `src/config.py` with dataclass for all `.env` variables
  - [ ] Load and validate `.env` using `python-dotenv`
  - [ ] Type conversion for int, float, bool values
  - [ ] Defaults for all optional settings
  - [ ] Feature-toggle helper method (`is_enabled("feature_name")`)

- [ ] **1.3 Implement SQLite database module**
  - [ ] Create `src/database.py` with connection manager
  - [ ] Enable WAL mode on connection
  - [ ] Create `translations` table schema
  - [ ] Create `conversation_sessions` table schema
  - [ ] Create `conversation_turns` table schema
  - [ ] Create `glossaries` table schema
  - [ ] Create `glossary_entries` table schema
  - [ ] Create `phrasebook_usage` table schema
  - [ ] Create `settings` table schema
  - [ ] Implement `init_db()` to create all tables
  - [ ] Implement CRUD helpers for each table
  - [ ] Implement parameterized queries for all DB operations

- [ ] **1.4 Implement OCR engine wrapper**
  - [ ] Create `src/ocr_engine.py`
  - [ ] Implement Tesseract backend via `pytesseract`
  - [ ] Implement PaddleOCR backend (optional, selectable via `OCR_ENGINE`)
  - [ ] Support multi-language OCR (`OCR_LANGUAGES` config)
  - [ ] Return extracted text with confidence scores
  - [ ] Image pre-processing (grayscale, contrast, deskew) via OpenCV/Pillow
  - [ ] Toggle via `ENABLE_VISUAL_MODE`

- [ ] **1.5 Implement STT engine wrapper**
  - [ ] Create `src/stt_engine.py`
  - [ ] Implement Whisper.cpp integration via `whispercpp`
  - [ ] Support model size selection (`WHISPER_MODEL_SIZE`)
  - [ ] Accept audio buffer (numpy array) and return transcription
  - [ ] Return transcription with language detection
  - [ ] Toggle via `ENABLE_AUDIO_MODE`

- [ ] **1.6 Implement TTS engine wrapper**
  - [ ] Create `src/tts_engine.py`
  - [ ] Implement Piper TTS integration
  - [ ] Support multiple language voices (load from `PIPER_MODEL_PATH`)
  - [ ] Generate audio buffer from text
  - [ ] Implement auto-play toggle (`TTS_AUTO_PLAY`)
  - [ ] Toggle via `ENABLE_TTS`

- [ ] **1.7 Implement LLM translation engine**
  - [ ] Create `src/translator.py`
  - [ ] Load GGUF model via `llama-cpp-python`
  - [ ] Implement `translate(text, source_lang, target_lang) -> str`
  - [ ] Structured prompt template for translation
  - [ ] Support glossary context injection (pass glossary terms in prompt)
  - [ ] Support summarization mode for document translation
  - [ ] Configurable temperature, max tokens, context size
  - [ ] Toggle via `ENABLE_TRANSLATION`

- [ ] **1.8 Implement mock mode**
  - [ ] Add mock OCR (return predefined text from images)
  - [ ] Add mock STT (return predefined transcript from audio)
  - [ ] Add mock translation (return echo or simple word replacement)
  - [ ] Add mock TTS (skip audio output, log text)
  - [ ] Conditional activation via `MOCK_MODE=true`

- [ ] **1.9 Write Phase 1 tests**
  - [ ] Test config loader (valid `.env`, missing values, type conversion)
  - [ ] Test database schema creation and CRUD operations
  - [ ] Test OCR engine (mock image → text extraction)
  - [ ] Test STT engine (mock audio → transcription)
  - [ ] Test TTS engine (text → audio buffer generation)
  - [ ] Test translator (text → translated text)
  - [ ] Test mock mode for all engines

---

## Phase 2 — Visual & Audio Mode Integration

- [ ] **2.1 Implement camera module**
  - [ ] Create `src/camera.py`
  - [ ] Implement Pi Camera capture via `picamera2` + OpenCV
  - [ ] Support configurable resolution (`CAMERA_RESOLUTION`)
  - [ ] Support configurable rotation (`CAMERA_ROTATION`)
  - [ ] Implement single-frame capture for visual mode
  - [ ] Implement continuous frame stream for subtitle overlay
  - [ ] Graceful fallback when camera unavailable (mock mode)

- [ ] **2.2 Implement audio module**
  - [ ] Create `src/audio.py`
  - [ ] Implement microphone recording via `pyaudio`
  - [ ] Configurable sample rate (`AUDIO_SAMPLE_RATE`)
  - [ ] Configurable chunk duration (`AUDIO_CHUNK_DURATION`)
  - [ ] Implement speaker playback for TTS output
  - [ ] Configurable input/output device (`AUDIO_INPUT_DEVICE`, `AUDIO_OUTPUT_DEVICE`)
  - [ ] Graceful fallback when audio device unavailable (mock mode)

- [ ] **2.3 Build visual mode pipeline**
  - [ ] Capture frame from camera
  - [ ] Run OCR engine on captured frame
  - [ ] Send extracted text to LLM translator
  - [ ] Display source text + translated text
  - [ ] Optionally speak translation via TTS
  - [ ] Store translation record in database

- [ ] **2.4 Build audio mode pipeline**
  - [ ] Record audio chunk from microphone
  - [ ] Run STT engine on audio buffer
  - [ ] Send transcribed text to LLM translator
  - [ ] Display source text + translated text
  - [ ] Optionally speak translation via TTS
  - [ ] Store translation record in database

- [ ] **2.5 Implement translation history persistence**
  - [ ] Save all translations to `translations` table
  - [ ] Include mode, language pair, source/translated text, engine info
  - [ ] Track processing time (ms)
  - [ ] Track TTS play status
  - [ ] Implement history retrieval (paginated, filterable by mode/language)

- [ ] **2.6 Write Phase 2 tests**
  - [ ] Test camera capture (mock picamera2)
  - [ ] Test audio recording and playback (mock pyaudio)
  - [ ] Test visual mode pipeline end-to-end (mock hardware)
  - [ ] Test audio mode pipeline end-to-end (mock hardware)
  - [ ] Test translation history CRUD

---

## Phase 3 — Web Dashboard & Authentication

- [ ] **3.1 Implement Flask app factory**
  - [ ] Create `src/app.py` with `create_app()` factory
  - [ ] Initialize Flask-SocketIO with eventlet
  - [ ] Register blueprints/routes
  - [ ] Integrate config and database initialization
  - [ ] Start engines in background threads
  - [ ] Implement `__main__` entry point

- [ ] **3.2 Implement authentication**
  - [ ] Create `src/auth.py`
  - [ ] Implement bcrypt password verification
  - [ ] Implement login route (`POST /login`)
  - [ ] Implement logout route (`POST /logout`)
  - [ ] Implement rate limiting (10 attempts per 15 minutes per IP)
  - [ ] Implement session with 24-hour expiry
  - [ ] Implement `@login_required` decorator for all protected routes
  - [ ] Read `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` from config

- [ ] **3.3 Create dark theme templates and CSS**
  - [ ] Create `templates/base.html` with dark theme layout
  - [ ] Create `static/css/style.css` with dark color scheme
  - [ ] Responsive layout for desktop and tablet
  - [ ] Navigation bar with mode tabs and logout button

- [ ] **3.4 Build login page**
  - [ ] Create `templates/login.html`
  - [ ] Username and password form with CSRF token
  - [ ] Error message display for failed login
  - [ ] Rate limit warning display

- [ ] **3.5 Build main dashboard page**
  - [ ] Create `templates/dashboard.html`
  - [ ] Mode selector tabs (Visual, Audio, Conversation, Document)
  - [ ] Language pair selector (source + target dropdowns)
  - [ ] Translation history feed (recent translations)
  - [ ] Status indicators (camera, microphone, models loaded)

- [ ] **3.6 Build visual mode page**
  - [ ] Create `templates/visual.html`
  - [ ] Camera preview panel
  - [ ] Capture button
  - [ ] OCR result panel (source text)
  - [ ] Translation result panel (translated text)
  - [ ] TTS play/stop button

- [ ] **3.7 Build audio mode page**
  - [ ] Create `templates/audio.html`
  - [ ] Record button (push-to-talk)
  - [ ] Recording indicator (waveform or timer)
  - [ ] Transcription result panel (source text)
  - [ ] Translation result panel (translated text)
  - [ ] TTS play/stop button

- [ ] **3.8 Implement SocketIO real-time updates**
  - [ ] Emit `translation_result` events with source + translated text
  - [ ] Emit `ocr_progress` events during visual mode processing
  - [ ] Emit `stt_progress` events during audio mode processing
  - [ ] Emit `tts_status` events (playing, stopped)
  - [ ] Client-side SocketIO handlers in `static/js/` modules

- [ ] **3.9 Build settings panel**
  - [ ] Create `templates/settings.html`
  - [ ] Language configuration (default source/target)
  - [ ] TTS auto-play toggle
  - [ ] OCR engine selector
  - [ ] Translation history (view, clear)
  - [ ] Current configuration display

- [ ] **3.10 Write Phase 3 tests**
  - [ ] Test login (valid credentials, invalid credentials, rate limiting)
  - [ ] Test session expiry (24-hour window)
  - [ ] Test protected route access (authenticated vs unauthenticated)
  - [ ] Test dashboard data API endpoints
  - [ ] Test SocketIO event emission

---

## Phase 4 — Conversation & Document Modes

- [ ] **4.1 Implement conversation controller**
  - [ ] Create `src/conversation.py`
  - [ ] Implement session management (start, end, resume)
  - [ ] Implement turn-based flow (Speaker A → translate → Speaker B → translate)
  - [ ] Implement language switching per speaker
  - [ ] Support push-to-talk via SocketIO events
  - [ ] Auto-TTS in target language after each turn
  - [ ] Store session and turns in database

- [ ] **4.2 Build conversation mode page**
  - [ ] Create `templates/conversation.html`
  - [ ] Dual-panel layout (Speaker A left, Speaker B right)
  - [ ] Push-to-talk button per speaker
  - [ ] Live transcript display per speaker
  - [ ] Translated text display per speaker
  - [ ] Session controls (start, end, clear)
  - [ ] Turn indicator (whose turn to speak)

- [ ] **4.3 Implement conversation persistence**
  - [ ] Create conversation session on start
  - [ ] Record each turn with speaker, source/translated text, timestamps
  - [ ] Update turn count on session
  - [ ] End session records `ended_at`
  - [ ] Support session history retrieval

- [ ] **4.4 Implement document processor**
  - [ ] Create `src/document.py`
  - [ ] Implement PDF page extraction via PyMuPDF
  - [ ] Implement image extraction from PDF pages
  - [ ] Run OCR on each page/image
  - [ ] Send extracted text to LLM for structured translation
  - [ ] Support multi-page documents
  - [ ] Return per-page results

- [ ] **4.5 Build document upload page**
  - [ ] Create `templates/document.html`
  - [ ] File upload form (drag-and-drop + file picker)
  - [ ] File type and size validation (client-side + server-side)
  - [ ] Upload progress indicator
  - [ ] Per-page OCR + translation results display
  - [ ] Download translated document option (text file)

- [ ] **4.6 Implement file validation**
  - [ ] Validate file extension against `ALLOWED_EXTENSIONS`
  - [ ] Validate file size against `MAX_UPLOAD_SIZE_MB`
  - [ ] Validate file content type (magic bytes)
  - [ ] Process files in memory (no disk persistence)
  - [ ] Reject oversized or invalid files with clear error messages

- [ ] **4.7 Write Phase 4 tests**
  - [ ] Test conversation session lifecycle (start, turns, end)
  - [ ] Test turn-based language switching
  - [ ] Test conversation persistence (DB records)
  - [ ] Test document PDF extraction (mock PyMuPDF)
  - [ ] Test document image OCR pipeline
  - [ ] Test file validation (valid types, invalid types, oversized)
  - [ ] Test multi-page document processing

---

## Phase 5 — Phrase Book, Glossary & Subtitle Overlay

- [ ] **5.1 Implement phrase book manager**
  - [ ] Create `src/phrasebook.py`
  - [ ] Load JSON phrase book files from `PHRASEBOOK_DIR`
  - [ ] Support categories (greetings, directions, medical, legal, food, transport)
  - [ ] Implement `get_phrases(lang_pair, category) -> list`
  - [ ] Implement `search_phrases(lang_pair, query) -> list`
  - [ ] Track usage in `phrasebook_usage` table
  - [ ] Toggle via `ENABLE_PHRASEBOOK`

- [ ] **5.2 Create phrase book data files**
  - [ ] Create `data/phrasebooks/en_de.json` (English → German)
  - [ ] Create `data/phrasebooks/en_fr.json` (English → French)
  - [ ] Create `data/phrasebooks/en_es.json` (English → Spanish)
  - [ ] Each file: 50+ phrases across 6 categories
  - [ ] Structure: `{ "category": [ { "id": "...", "source": "...", "target": "..." } ] }`

- [ ] **5.3 Build phrase book page**
  - [ ] Create `templates/phrasebook.html`
  - [ ] Language pair selector
  - [ ] Category filter tabs
  - [ ] Phrase list (source text, translation, TTS play button)
  - [ ] Search/filter bar
  - [ ] Toggle via `ENABLE_PHRASEBOOK`

- [ ] **5.4 Implement glossary loader**
  - [ ] Create `src/glossary.py`
  - [ ] Parse CSV glossary files (`source_term,target_term`)
  - [ ] Parse JSON glossary files
  - [ ] Store glossary metadata in `glossaries` table
  - [ ] Store individual entries in `glossary_entries` table
  - [ ] Implement `get_glossary_terms(glossary_id) -> list`
  - [ ] Validate entry count against `MAX_GLOSSARY_ENTRIES`
  - [ ] Toggle via `ENABLE_GLOSSARY`

- [ ] **5.5 Integrate glossary into translation**
  - [ ] Load active glossary terms for current language pair
  - [ ] Inject glossary terms into LLM translation prompt
  - [ ] Format: "Use these domain-specific terms: {term_a} → {term_b}, ..."
  - [ ] Verify glossary terms appear in translation output

- [ ] **5.6 Build glossary management UI**
  - [ ] Add glossary section to settings page
  - [ ] Upload glossary file (CSV/JSON)
  - [ ] List all uploaded glossaries (name, domain, language pair, entry count)
  - [ ] Delete glossary
  - [ ] Activate/deactivate glossary per translation session

- [ ] **5.7 Implement subtitle overlay**
  - [ ] Create `src/subtitle.py`
  - [ ] Implement text region detection via OpenCV (EAST or contour-based)
  - [ ] Run OCR on detected text regions
  - [ ] Translate detected text via LLM
  - [ ] Render translated text overlay on camera frame
  - [ ] Stream processed frames to dashboard via SocketIO
  - [ ] Toggle via `ENABLE_SUBTITLE_OVERLAY`

- [ ] **5.8 Write Phase 5 tests**
  - [ ] Test phrase book loading (valid JSON, missing file, categories)
  - [ ] Test phrase search and filtering
  - [ ] Test glossary CSV/JSON parsing
  - [ ] Test glossary DB storage and retrieval
  - [ ] Test glossary integration in translation prompt
  - [ ] Test subtitle text detection (mock OpenCV)
  - [ ] Test subtitle overlay rendering

---

## Phase 6 — Deployment & Documentation

- [ ] **6.1 Create deploy script**
  - [ ] Create `deploy/deploy_to_pi.sh`
  - [ ] rsync project to `rasp-pi` (pi@192.168.216.90)
  - [ ] Exclude `.venv`, `__pycache__`, `.git`, `data/models/`
  - [ ] Remote `pip install -r requirements.txt`
  - [ ] Print restart instructions

- [ ] **6.2 Create model download script**
  - [ ] Create `scripts/download_models.sh`
  - [ ] Download Whisper model (configurable size)
  - [ ] Download LLM GGUF model
  - [ ] Download Piper TTS voice models for supported languages
  - [ ] Verify checksums after download
  - [ ] Print summary of downloaded models

- [ ] **6.3 Create OS dependency installer**
  - [ ] Create `scripts/install_deps.sh`
  - [ ] Install Tesseract OCR and language packs
  - [ ] Install PortAudio for PyAudio
  - [ ] Install libcamera for Pi Camera
  - [ ] Install Python venv and dev headers
  - [ ] Handle apt update and error cases
  - [ ] Print success/failure summary

- [ ] **6.4 Write systemd service unit**
  - [ ] Create service file for `visual-audio-translator`
  - [ ] Configure `After=network-online.target`
  - [ ] Configure restart on failure with 10s delay
  - [ ] Document enable/start commands in README

- [ ] **6.5 Write threat model document**
  - [ ] Create `docs/threat_model.md`
  - [ ] Document all threat vectors and mitigations
  - [ ] Include data flow diagram
  - [ ] Include trust boundary analysis
  - [ ] Security recommendations for deployment

- [ ] **6.6 Final integration testing**
  - [ ] Test visual mode end-to-end on real Pi hardware
  - [ ] Test audio mode end-to-end with real microphone
  - [ ] Test conversation mode with two speakers
  - [ ] Test document mode with real PDF
  - [ ] Test phrase book browsing and TTS
  - [ ] Test glossary upload and glossary-aware translation
  - [ ] Test subtitle overlay with live camera
  - [ ] Test systemd service lifecycle (start, stop, restart, crash recovery)
  - [ ] Test dashboard under load (multiple concurrent clients)

- [ ] **6.7 Finalize documentation**
  - [ ] Update README with final usage instructions
  - [ ] Verify all `.env` variables documented
  - [ ] Update TSD with any changes from implementation
  - [ ] Update task.md with completion status
  - [ ] Review and update troubleshooting table
