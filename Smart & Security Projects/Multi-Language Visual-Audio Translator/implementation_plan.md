# Implementation Plan — Multi-Language Visual-Audio Translator

## Phase 1 — Project Foundation & Core Engines

**Goal:** Scaffold the project, configure environment loading, set up the database, and build the OCR, STT, TTS, and LLM translation engines with mock mode.

- [ ] **Step 1.1 — Initialize Project Structure**
  - [ ] Create directory tree:
    ```
    src/, templates/, static/css/, static/js/, tests/, deploy/, scripts/, docs/,
    data/models/, data/phrasebooks/, data/glossaries/, data/languages/
    ```
  - [ ] Create `pyproject.toml` with project name, version, Python ≥3.11, and entry point `src.app`
  - [ ] Create `requirements.txt`:
    ```
    flask
    flask-socketio
    eventlet
    pytesseract
    whispercpp
    llama-cpp-python
    piper-tts
    opencv-python-headless
    pyaudio
    Pillow
    PyMuPDF
    bcrypt
    python-dotenv
    gunicorn
    pytest
    pytest-cov
    ```
  - [ ] Create `.env.example` with all variables and documented defaults (see TSD §8)
  - [ ] Create `src/__init__.py` (empty)
  - [ ] Create `tests/__init__.py` (empty) and `tests/conftest.py` with shared fixtures

- [ ] **Step 1.2 — Configuration Loader**
  - [ ] Create `src/config.py`
  - [ ] Define `@dataclass class Config` with all `.env` fields and proper types
  - [ ] Implement `load_config()` — reads `.env` via `dotenv_values()`, applies defaults
  - [ ] Convert string values to `int`, `float`, `bool` as needed
  - [ ] Add `is_enabled(feature: str) -> bool` helper for toggle checks
  - [ ] Write `tests/test_config.py` — test loading, defaults, type conversion, missing keys

- [ ] **Step 1.3 — SQLite Database Module**
  - [ ] Create `src/database.py`
  - [ ] Implement `get_connection(db_path)` with WAL mode pragma
  - [ ] Implement `init_db(conn)` — creates all 7 tables (see TSD §3)
  - [ ] Implement CRUD functions:
    - `insert_translation(conn, data)` / `get_translations(conn, filters)`
    - `create_conversation_session(conn, lang_a, lang_b)` / `end_session(conn, session_id)`
    - `insert_conversation_turn(conn, data)` / `get_session_turns(conn, session_id)`
    - `insert_glossary(conn, data)` / `get_glossaries(conn)`
    - `insert_glossary_entries(conn, glossary_id, entries)` / `get_glossary_entries(conn, glossary_id)`
    - `log_phrasebook_usage(conn, data)`
    - `get_setting(conn, key)` / `set_setting(conn, key, value)`
  - [ ] Use parameterized queries for all DB operations
  - [ ] Write `tests/test_database.py` — test schema creation, all CRUD ops, WAL mode

- [ ] **Step 1.4 — OCR Engine Wrapper**
  - [ ] Create `src/ocr_engine.py`
  - [ ] Implement `OCREngine` class:
    - `__init__(config)` — select backend (tesseract or paddleocr)
    - `extract_text(image) -> dict` — return `{text, confidence, language, regions[]}`
    - Pre-process image: grayscale conversion, contrast enhancement, deskew
    - `regions` contains bounding boxes for subtitle overlay
  - [ ] Tesseract backend: use `pytesseract.image_to_data()` for detailed output
  - [ ] PaddleOCR backend: use `PaddleOCR().ocr()` for alternative engine
  - [ ] Configurable languages via `OCR_LANGUAGES`
  - [ ] Toggle via `ENABLE_VISUAL_MODE` (return empty result when disabled)
  - [ ] Write `tests/test_ocr.py` — test with sample images, language config, disabled mode

- [ ] **Step 1.5 — STT Engine Wrapper**
  - [ ] Create `src/stt_engine.py`
  - [ ] Implement `STTEngine` class:
    - `__init__(config)` — load Whisper model from `WHISPER_MODEL_PATH`
    - `transcribe(audio_buffer: np.ndarray) -> dict` — return `{text, language, probability}`
    - Model size controlled by `WHISPER_MODEL_SIZE`
  - [ ] Accept 16kHz mono float32 numpy array
  - [ ] Include auto language detection from Whisper
  - [ ] Toggle via `ENABLE_AUDIO_MODE` (return empty result when disabled)
  - [ ] Write `tests/test_stt.py` — test with mock audio data, language detection, disabled mode

- [ ] **Step 1.6 — TTS Engine Wrapper**
  - [ ] Create `src/tts_engine.py`
  - [ ] Implement `TTSEngine` class:
    - `__init__(config)` — discover available Piper voice models in `PIPER_MODEL_PATH`
    - `synthesize(text, language) -> bytes` — return WAV audio buffer
    - `get_available_voices() -> list` — list supported languages
    - `play(audio_buffer)` — play audio through speaker (via pyaudio)
  - [ ] Auto-select voice model based on target language
  - [ ] Implement auto-play logic: if `TTS_AUTO_PLAY=true`, call `play()` after synthesis
  - [ ] Toggle via `ENABLE_TTS` (skip synthesis when disabled)
  - [ ] Write `tests/test_tts.py` — test synthesis, voice selection, auto-play, disabled mode

- [ ] **Step 1.7 — LLM Translation Engine**
  - [ ] Create `src/translator.py`
  - [ ] Implement `Translator` class:
    - `__init__(config)` — load GGUF model via `llama_cpp.Llama(model_path=...)`
    - `translate(text, source_lang, target_lang, glossary=None) -> str`
    - `summarize_and_translate(text, source_lang, target_lang) -> str` (document mode)
  - [ ] Translation prompt template:
    ```
    Translate the following text from {source_lang} to {target_lang}.
    {glossary_context}
    Text: {text}
    Translation:
    ```
  - [ ] Glossary context injection:
    ```
    Use these domain-specific terms:
    - {source_term} → {target_term}
    ...
    ```
  - [ ] Configurable: `LLM_CONTEXT_SIZE`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`
  - [ ] Toggle via `ENABLE_TRANSLATION` (return original text when disabled)
  - [ ] Write `tests/test_translator.py` — test translation, summarization, glossary injection, disabled mode

- [ ] **Step 1.8 — Mock Mode**
  - [ ] Add `MockOCREngine` — returns predefined text based on image filename/hash
  - [ ] Add `MockSTTEngine` — returns predefined transcript (cycles through sample phrases)
  - [ ] Add `MockTranslator` — returns `"[MOCK] {source_text}"` prefixed output
  - [ ] Add `MockTTSEngine` — logs text, returns silence buffer
  - [ ] Activate via `MOCK_MODE=true` in config; engine factory returns mock instances
  - [ ] Write `tests/test_mock.py` — test all mock engines

**Checkpoint:** All four core engines functional (OCR, STT, TTS, Translator). Config and DB fully tested. Mock mode allows development without hardware.

---

## Phase 2 — Visual & Audio Mode Integration

**Goal:** Build camera and microphone modules, wire them into complete input → process → output pipelines.

- [ ] **Step 2.1 — Camera Module**
  - [ ] Create `src/camera.py`
  - [ ] Implement `Camera` class:
    - `__init__(config)` — initialize picamera2 with `CAMERA_RESOLUTION` and `CAMERA_ROTATION`
    - `capture_frame() -> np.ndarray` — capture single frame (for visual mode)
    - `start_stream(callback)` — continuous frame stream (for subtitle overlay)
    - `stop_stream()` — stop continuous capture
    - `is_available() -> bool` — check if camera is accessible
  - [ ] Implement `MockCamera` for `MOCK_MODE` — returns sample images from `data/`
  - [ ] Graceful error handling: return informative error if camera unavailable

- [ ] **Step 2.2 — Audio Module**
  - [ ] Create `src/audio.py`
  - [ ] Implement `AudioIO` class:
    - `__init__(config)` — initialize pyaudio with `AUDIO_SAMPLE_RATE`, device config
    - `record(duration_sec) -> np.ndarray` — record audio chunk from microphone
    - `play(audio_buffer: bytes)` — play WAV audio through speaker
    - `is_mic_available() -> bool` — check microphone accessibility
    - `is_speaker_available() -> bool` — check speaker accessibility
  - [ ] Implement `MockAudioIO` for `MOCK_MODE` — returns sample audio data
  - [ ] Support continuous recording with callback (for conversation mode)

- [ ] **Step 2.3 — Visual Mode Pipeline**
  - [ ] Wire: `camera.capture_frame()` → `ocr_engine.extract_text(frame)` → `translator.translate(text)` → emit result via SocketIO → optionally `tts_engine.synthesize()` + `audio.play()`
  - [ ] Track total processing time (ms) per pipeline run
  - [ ] Emit intermediate status events: "Capturing...", "Extracting text...", "Translating...", "Speaking..."
  - [ ] Handle empty OCR result gracefully (display "No text detected")

- [ ] **Step 2.4 — Audio Mode Pipeline**
  - [ ] Wire: `audio.record()` → `stt_engine.transcribe(buffer)` → `translator.translate(text)` → emit result via SocketIO → optionally `tts_engine.synthesize()` + `audio.play()`
  - [ ] Track total processing time (ms) per pipeline run
  - [ ] Emit intermediate status events: "Recording...", "Transcribing...", "Translating...", "Speaking..."
  - [ ] Handle empty STT result gracefully (display "No speech detected")

- [ ] **Step 2.5 — Translation History Persistence**
  - [ ] After each successful pipeline run, call `insert_translation(conn, data)`
  - [ ] Store: mode, language pair, source/translated text, engine info, confidence, processing_ms
  - [ ] Implement `get_recent_translations(conn, limit=50)` for dashboard feed
  - [ ] Implement `get_translations_by_mode(conn, mode, limit)` for filtered views

- [ ] **Step 2.6 — Phase 2 Tests**
  - [ ] `tests/test_camera.py` — capture frame (mock picamera2), stream start/stop, unavailable
  - [ ] `tests/test_audio.py` — record (mock pyaudio), playback, device unavailable
  - [ ] Test visual mode pipeline end-to-end (all mock engines)
  - [ ] Test audio mode pipeline end-to-end (all mock engines)
  - [ ] Test translation history insertion and retrieval

**Checkpoint:** Both visual and audio mode pipelines work end-to-end. Translation history persisted. All hardware interactions mockable.

---

## Phase 3 — Web Dashboard & Authentication

**Goal:** Build the authenticated dark-themed web dashboard with real-time SocketIO updates.

- [ ] **Step 3.1 — Flask App Factory**
  - [ ] Create `src/app.py`:
    - `create_app(config)` factory pattern
    - Initialize Flask-SocketIO with eventlet mode
    - Register route handlers
    - Initialize database on startup
    - Initialize engines (OCR, STT, TTS, Translator) on startup
    - Implement `__main__` block to run the app
  - [ ] Toggle dashboard via `ENABLE_WEB_DASHBOARD`

- [ ] **Step 3.2 — Authentication Module**
  - [ ] Create `src/auth.py`:
    - `verify_password(plaintext, bcrypt_hash) -> bool`
    - `login_user(session, username)` — set session data with expiry timestamp
    - `logout_user(session)` — clear session
    - `is_authenticated(session) -> bool` — check session validity and expiry
    - `login_required(f)` — decorator redirecting to `/login`
  - [ ] Route `GET /login` — render login form
  - [ ] Route `POST /login` — verify credentials, rate limit check, set session
  - [ ] Route `POST /logout` — clear session, redirect to login
  - [ ] Rate limiter: store attempt counts per IP in memory dict with 15-min window
  - [ ] Session expiry: check `SESSION_EXPIRY_HOURS` (default 24h) on each request

- [ ] **Step 3.3 — Dark Theme Templates & CSS**
  - [ ] Create `templates/base.html`:
    - HTML5 boilerplate with dark background (`#1a1a2e`)
    - Navigation bar (app title, mode tabs, language selector, logout)
    - Content block, script block
    - SocketIO client script
  - [ ] Create `static/css/style.css`:
    - Dark palette: background `#1a1a2e`, cards `#16213e`, text `#e0e0e0`, accent `#0f3460`
    - Mode tab styling (active/inactive)
    - Translation panels (source panel, target panel)
    - Form inputs, buttons, dropdowns
    - Responsive grid layout

- [ ] **Step 3.4 — Login Page**
  - [ ] Create `templates/login.html` extending base
  - [ ] Centered login card with username/password fields
  - [ ] CSRF token hidden field
  - [ ] Flash message area for errors ("Invalid credentials", "Rate limited")

- [ ] **Step 3.5 — Dashboard Page**
  - [ ] Create `templates/dashboard.html` extending base
  - [ ] Mode selector cards (Visual, Audio, Conversation, Document — each links to mode page)
  - [ ] Language pair selector (source + target dropdowns)
  - [ ] Recent translation history feed (scrollable list)
  - [ ] System status summary (camera, mic, models loaded, engines active)

- [ ] **Step 3.6 — Visual Mode Page**
  - [ ] Create `templates/visual.html` extending base
  - [ ] Camera preview panel (live or last capture)
  - [ ] "Capture & Translate" button
  - [ ] Source text panel (OCR result with confidence indicator)
  - [ ] Translated text panel (LLM output)
  - [ ] TTS play/stop button
  - [ ] Processing status indicator

- [ ] **Step 3.7 — Audio Mode Page**
  - [ ] Create `templates/audio.html` extending base
  - [ ] Record button (push-to-talk style, hold or toggle)
  - [ ] Recording indicator (duration timer, waveform visualization)
  - [ ] Source text panel (Whisper transcript)
  - [ ] Translated text panel (LLM output)
  - [ ] TTS play/stop button
  - [ ] Processing status indicator

- [ ] **Step 3.8 — SocketIO Real-time Events**
  - [ ] Server emits:
    - `translation_result` — `{source_text, translated_text, source_lang, target_lang, mode}`
    - `pipeline_status` — `{stage: "capturing"|"ocr"|"stt"|"translating"|"tts", progress: %}`
    - `tts_status` — `{playing: bool}`
    - `error` — `{message, mode}`
  - [ ] Create `static/js/dashboard.js` — SocketIO connection, mode routing
  - [ ] Create `static/js/visual.js` — capture button, DOM updates for visual mode
  - [ ] Create `static/js/audio.js` — record button, DOM updates for audio mode
  - [ ] Handle reconnection and error states gracefully

- [ ] **Step 3.9 — Settings Panel**
  - [ ] Create `templates/settings.html` extending base
  - [ ] Route `GET /settings` — render settings page
  - [ ] Default language pair configuration
  - [ ] TTS auto-play toggle
  - [ ] OCR engine selector (tesseract / paddleocr)
  - [ ] Translation history view and clear button
  - [ ] Display current `.env` feature toggles (read-only)

- [ ] **Step 3.10 — Phase 3 Tests**
  - [ ] `tests/test_auth.py` — login, logout, invalid creds, rate limiting, session expiry
  - [ ] `tests/test_api.py` — dashboard route (auth required), mode pages, settings routes
  - [ ] Test CSRF protection on forms
  - [ ] Test SocketIO event emission

**Checkpoint:** Fully functional dark-themed dashboard with visual and audio mode pages, auth, settings, and real-time SocketIO updates. All routes protected by bcrypt auth with rate limiting.

---

## Phase 4 — Conversation & Document Modes

**Goal:** Implement real-time conversation mode for two speakers and document upload/translation.

- [ ] **Step 4.1 — Conversation Controller**
  - [ ] Create `src/conversation.py`
  - [ ] Implement `ConversationManager` class:
    - `start_session(lang_a, lang_b) -> session_id`
    - `end_session(session_id)`
    - `process_turn(session_id, speaker, audio_buffer) -> dict`
      - STT on audio → detect source lang → translate to other speaker's lang → TTS
      - Return `{speaker, source_text, translated_text, source_lang, target_lang}`
    - `get_session_history(session_id) -> list[Turn]`
  - [ ] Turn management: alternate between Speaker A and Speaker B
  - [ ] Language pair from `CONVERSATION_LANG_A` and `CONVERSATION_LANG_B`
  - [ ] Toggle via `ENABLE_CONVERSATION_MODE`

- [ ] **Step 4.2 — Conversation Mode Page**
  - [ ] Create `templates/conversation.html` extending base
  - [ ] Dual-panel layout:
    - Left panel: Speaker A (language label, transcript, translation, push-to-talk button)
    - Right panel: Speaker B (language label, transcript, translation, push-to-talk button)
  - [ ] Session controls: Start Session, End Session, Clear History
  - [ ] Turn indicator highlight (active speaker's panel glows)
  - [ ] Scrollable conversation history (alternating turns)
  - [ ] Create `static/js/conversation.js` — SocketIO events for turns, session management

- [ ] **Step 4.3 — Conversation Persistence**
  - [ ] On `start_session()`: insert into `conversation_sessions` table
  - [ ] On each turn: insert into `conversation_turns` table, increment `turn_count`
  - [ ] On `end_session()`: update `ended_at` timestamp
  - [ ] API route `GET /api/conversation/<session_id>` — return session with all turns

- [ ] **Step 4.4 — Document Processor**
  - [ ] Create `src/document.py`
  - [ ] Implement `DocumentProcessor` class:
    - `process(file_data, filename, source_lang, target_lang) -> list[PageResult]`
    - For PDF: use `fitz.open()` to iterate pages, render each as image, run OCR
    - For images: run OCR directly
    - Send extracted text per page to translator
    - `summarize_and_translate()` for full-document summary
  - [ ] `PageResult`: `{page_num, source_text, translated_text, confidence, processing_ms}`
  - [ ] Toggle via `ENABLE_DOCUMENT_MODE`

- [ ] **Step 4.5 — Document Upload Page**
  - [ ] Create `templates/document.html` extending base
  - [ ] File upload form with drag-and-drop zone
  - [ ] Client-side validation: file type (`ALLOWED_EXTENSIONS`), file size (`MAX_UPLOAD_SIZE_MB`)
  - [ ] Upload progress bar
  - [ ] Per-page result cards: page number, source text (collapsible), translated text
  - [ ] "Download as Text" button — export all translations as `.txt`
  - [ ] Create `static/js/document.js` — upload handling, progress, result display

- [ ] **Step 4.6 — File Validation & Security**
  - [ ] Server-side validation in `POST /upload`:
    - Check file extension against `ALLOWED_EXTENSIONS`
    - Check Content-Length against `MAX_UPLOAD_SIZE_MB`
    - Validate file magic bytes (JPEG: `FF D8`, PNG: `89 50`, PDF: `%PDF`)
    - Process in memory using `io.BytesIO` — no disk writes
    - Sanitize filename (strip path components, restrict characters)
  - [ ] Return `400` with clear error message for invalid files

- [ ] **Step 4.7 — Phase 4 Tests**
  - [ ] `tests/test_conversation.py`:
    - Test session lifecycle (start, turns, end)
    - Test turn processing (STT → translate → TTS)
    - Test language switching per speaker
    - Test session history retrieval
  - [ ] `tests/test_document.py`:
    - Test PDF page extraction (mock PyMuPDF)
    - Test image OCR pipeline
    - Test multi-page processing
    - Test file validation (valid, invalid extension, oversized, invalid magic bytes)

**Checkpoint:** Conversation mode supports real-time bilingual dialogue. Document mode handles PDF/image upload with per-page translation. All input validated securely.

---

## Phase 5 — Phrase Book, Glossary & Subtitle Overlay

**Goal:** Add phrase book browser, domain glossary support, and live subtitle overlay.

- [ ] **Step 5.1 — Phrase Book Manager**
  - [ ] Create `src/phrasebook.py`
  - [ ] Implement `PhrasebookManager` class:
    - `__init__(config)` — scan `PHRASEBOOK_DIR` for JSON files
    - `get_language_pairs() -> list[str]` — available pairs (e.g., `["en_de", "en_fr"]`)
    - `get_categories(lang_pair) -> list[str]` — categories in a phrase book
    - `get_phrases(lang_pair, category) -> list[Phrase]` — phrases for a category
    - `search(lang_pair, query) -> list[Phrase]` — search across all categories
  - [ ] `Phrase`: `{id, source, target, category}`
  - [ ] Log phrase access to `phrasebook_usage` table
  - [ ] Toggle via `ENABLE_PHRASEBOOK`

- [ ] **Step 5.2 — Phrase Book Data Files**
  - [ ] Create `data/phrasebooks/en_de.json`:
    ```json
    {
      "greetings": [{"id": "g1", "source": "Hello", "target": "Hallo"}, ...],
      "directions": [...],
      "medical": [...],
      "legal": [...],
      "food": [...],
      "transport": [...]
    }
    ```
  - [ ] Create `data/phrasebooks/en_fr.json` (same structure, French translations)
  - [ ] Create `data/phrasebooks/en_es.json` (same structure, Spanish translations)
  - [ ] At least 50 phrases per file across 6 categories

- [ ] **Step 5.3 — Phrase Book Page**
  - [ ] Create `templates/phrasebook.html` extending base
  - [ ] Language pair dropdown selector
  - [ ] Category tab/filter bar
  - [ ] Phrase cards: source text, arrow, target text, TTS play button (for target text)
  - [ ] Search bar with live filtering
  - [ ] Route `GET /phrasebook` — render page
  - [ ] Route `GET /api/phrasebook/<lang_pair>/<category>` — return JSON phrases
  - [ ] Route `POST /api/phrasebook/tts` — synthesize and return audio for a phrase

- [ ] **Step 5.4 — Glossary Loader**
  - [ ] Create `src/glossary.py`
  - [ ] Implement `GlossaryManager` class:
    - `upload_glossary(name, domain, source_lang, target_lang, file_data) -> int`
      - Parse CSV or JSON
      - Validate entry count ≤ `MAX_GLOSSARY_ENTRIES`
      - Store metadata in `glossaries` table, entries in `glossary_entries`
      - Return glossary ID
    - `get_glossaries() -> list[Glossary]`
    - `get_entries(glossary_id) -> list[Entry]`
    - `delete_glossary(glossary_id)`
    - `get_terms_for_translation(source_lang, target_lang) -> list[Entry]`
      - Return all entries from active glossaries matching the language pair
  - [ ] Toggle via `ENABLE_GLOSSARY`

- [ ] **Step 5.5 — Glossary Integration in Translation**
  - [ ] In `Translator.translate()`:
    - If glossary terms provided, build context string:
      ```
      Use these domain-specific terms in your translation:
      - {source_term} → {target_term}
      - ...
      ```
    - Insert context into prompt before the text to translate
  - [ ] Limit injected terms to top 50 most relevant (by frequency or exact match in source text)
  - [ ] Test that glossary terms appear correctly in output

- [ ] **Step 5.6 — Glossary Management UI**
  - [ ] Add to `templates/settings.html`:
    - Glossary section with upload form (name, domain, language pair, file)
    - Table of uploaded glossaries (name, domain, lang pair, entries, uploaded date)
    - Delete button per glossary
    - Active/inactive toggle per glossary
  - [ ] Route `POST /settings/glossary/upload` — handle file upload and parsing
  - [ ] Route `POST /settings/glossary/<id>/delete` — delete glossary
  - [ ] Route `POST /settings/glossary/<id>/toggle` — activate/deactivate

- [ ] **Step 5.7 — Subtitle Overlay**
  - [ ] Create `src/subtitle.py`
  - [ ] Implement `SubtitleEngine` class:
    - `__init__(config, ocr_engine, translator)` — store references to engines
    - `process_frame(frame: np.ndarray) -> np.ndarray`:
      - Detect text regions in frame (OpenCV EAST text detector or contour-based)
      - Crop each region, run OCR
      - Translate detected text
      - Render translated text over original regions (semi-transparent background + text)
      - Return annotated frame
    - `start(camera, callback)` — continuous processing loop
    - `stop()`
  - [ ] Render overlay: black semi-transparent rectangle behind text, white bold text
  - [ ] Cache recent translations to avoid re-translating identical text across frames
  - [ ] Toggle via `ENABLE_SUBTITLE_OVERLAY` (requires `ENABLE_VISUAL_MODE`)
  - [ ] Stream annotated frames to dashboard via SocketIO (JPEG encoding)

- [ ] **Step 5.8 — Phase 5 Tests**
  - [ ] `tests/test_phrasebook.py`:
    - Test loading JSON files, listing pairs, listing categories
    - Test phrase retrieval, search
    - Test missing file handling, malformed JSON
  - [ ] `tests/test_glossary.py`:
    - Test CSV upload and parsing
    - Test JSON upload and parsing
    - Test DB storage and retrieval
    - Test entry count limit enforcement
    - Test language pair filtering
    - Test deletion
  - [ ] `tests/test_subtitle.py`:
    - Test text region detection (mock OpenCV)
    - Test OCR on cropped regions
    - Test overlay rendering
    - Test translation caching

**Checkpoint:** Phrase book browsable with TTS play. Glossary upload/management working with LLM integration. Subtitle overlay renders translated text on live camera feed.

---

## Phase 6 — Deployment & Documentation

**Goal:** Finalize deployment pipeline, systemd integration, model download, and all documentation.

- [ ] **Step 6.1 — Deploy Script**
  - [ ] Create `deploy/deploy_to_pi.sh`:
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    PI_HOST="rasp-pi"
    REMOTE_DIR="/home/pi/visual-audio-translator"
    rsync -avz --exclude '.venv' --exclude '__pycache__' \
        --exclude '*.pyc' --exclude '.git' --exclude 'data/models/' \
        ./ "${PI_HOST}:${REMOTE_DIR}/"
    ssh "${PI_HOST}" "cd ${REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt"
    echo "[✓] Deploy complete. Restart: sudo systemctl restart visual-audio-translator"
    ```
  - [ ] Make executable (`chmod +x`)
  - [ ] Note: models are excluded (too large for rsync); download directly on Pi

- [ ] **Step 6.2 — Model Download Script**
  - [ ] Create `scripts/download_models.sh`:
    - Download Whisper model (base by default, configurable via argument)
    - Download LLM GGUF model (Mistral 7B Q4_K_M or similar)
    - Download Piper TTS voice models for EN, DE, FR, ES, IT, PT, NL, PL, RU, ZH, AR
    - Verify file integrity (SHA256 checksum)
    - Create `data/models/` directory structure
    - Print summary of downloaded files with sizes
  - [ ] Make executable (`chmod +x`)
  - [ ] Accept `--whisper-size` and `--llm-model` arguments for customization

- [ ] **Step 6.3 — OS Dependency Installer**
  - [ ] Create `scripts/install_deps.sh`:
    - `sudo apt update`
    - `sudo apt install -y tesseract-ocr tesseract-ocr-deu tesseract-ocr-fra tesseract-ocr-ita tesseract-ocr-spa tesseract-ocr-por tesseract-ocr-nld tesseract-ocr-pol tesseract-ocr-rus tesseract-ocr-chi-sim tesseract-ocr-ara`
    - `sudo apt install -y portaudio19-dev python3-venv python3-dev libcamera-dev`
    - Verify Tesseract installation: `tesseract --version`
    - Print summary
  - [ ] Make executable (`chmod +x`)

- [ ] **Step 6.4 — systemd Service**
  - [ ] Create service unit (documented in README):
    ```ini
    [Unit]
    Description=Multi-Language Visual-Audio Translator
    After=network-online.target
    Wants=network-online.target

    [Service]
    Type=simple
    User=pi
    WorkingDirectory=/home/pi/visual-audio-translator
    EnvironmentFile=/home/pi/visual-audio-translator/.env
    ExecStart=/home/pi/visual-audio-translator/.venv/bin/python -m src.app
    Restart=on-failure
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```
  - [ ] Commands: `daemon-reload`, `enable`, `start`, `journalctl -f`

- [ ] **Step 6.5 — Threat Model Document**
  - [ ] Create `docs/threat_model.md`:
    - Trust boundaries (LAN, Pi, camera, microphone, uploaded files, LLM)
    - Data flow diagram (input → OCR/STT → LLM → TTS → output)
    - Threat vectors table (brute force, CSRF, file upload attacks, prompt injection, eavesdropping)
    - Mitigation strategies for each threat
    - Privacy considerations (camera, microphone, uploaded documents)
    - Security recommendations for deployment

- [ ] **Step 6.6 — Integration Testing on Hardware**
  - [ ] Test visual mode: capture real document → OCR → translate → display + TTS
  - [ ] Test audio mode: speak into microphone → STT → translate → display + TTS
  - [ ] Test conversation mode: two speakers with real microphone, alternating turns
  - [ ] Test document mode: upload real PDF → per-page translation
  - [ ] Test phrase book: browse, TTS play for each phrase
  - [ ] Test glossary: upload CSV → verify terms in translation output
  - [ ] Test subtitle overlay: live camera with text → translated overlay
  - [ ] Test all 11 language pairs (at least one translation per language)
  - [ ] Test systemd service (start, stop, restart, crash recovery)
  - [ ] Test dashboard under 3+ concurrent browser sessions

- [ ] **Step 6.7 — Documentation Finalization**
  - [ ] Review and update `README.md` with any implementation changes
  - [ ] Verify all `.env` variables match actual code usage
  - [ ] Update `TSD.md` with final architecture and any schema changes
  - [ ] Mark completed tasks in `task.md`
  - [ ] Ensure troubleshooting table covers all known issues

**Checkpoint:** Project fully deployed on Pi, running as systemd service, all documentation complete and accurate. All modes tested with real hardware. Offline operation verified.
