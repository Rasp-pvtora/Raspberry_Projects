# Implementation Plan — AI-Powered Sign Language to Text Translator

---

## Phase 1 — Hand Tracking and Classification (Foundation)

**Goal:** Camera captures hands, MediaPipe extracts landmarks, LSTM classifies signs.

- [ ] **Step 1.1** — Create project structure and dependencies
  - [ ] All directories created
  - [ ] `requirements.txt` with pinned versions
  - [ ] `.env.default` with all variables
  - [ ] Verify: `pip install` succeeds

- [ ] **Step 1.2** — Camera capture module
  - [ ] `src/hardware/camera.py` — OpenCV VideoCapture
  - [ ] Configurable source, resolution
  - [ ] Test: frames captured or mock returned

- [ ] **Step 1.3** — MediaPipe hand landmark extraction
  - [ ] `src/recognition/hand_tracker.py`
  - [ ] Initialize MediaPipe Hands with `max_num_hands=2`
  - [ ] Extract 21 landmarks per hand per frame
  - [ ] Normalize: translate to wrist origin, scale to unit size
  - [ ] Test: input image with hand → 21 valid landmarks

- [ ] **Step 1.4** — LSTM sign classifier
  - [ ] `src/recognition/sign_classifier.py`
  - [ ] Load `.h5` or `.tflite` model
  - [ ] Buffer 30 frames of normalized landmarks
  - [ ] When buffer full: classify → return (label, confidence)
  - [ ] Filter below `CONFIDENCE_THRESHOLD`
  - [ ] Test: known sequence → correct label with expected confidence

- [ ] **Step 1.5** — Mock hardware and database
  - [ ] Mock camera returns pre-saved frames
  - [ ] SQLite tables created
  - [ ] Test: full pipeline runs with mock → classification stored in DB

- [ ] **Phase 1 checkpoint:** Camera → MediaPipe → LSTM → Sign label in database

---

## Phase 2 — Sentence Building and Audio Output

**Goal:** Accumulate individual signs into sentences, output via TTS.

- [ ] **Step 2.1** — Sentence builder
  - [ ] `src/recognition/sentence_builder.py`
  - [ ] Buffer recognized signs
  - [ ] Pause detection (no sign for `SENTENCE_PAUSE_SEC`)
  - [ ] On pause: finalize sentence, store in DB
  - [ ] Test: sequence of signs + pause → complete sentence

- [ ] **Step 2.2** — Two-hand extension
  - [ ] Extend classifier input to 126 features when 2 hands detected
  - [ ] Fall back to 63 features for single hand
  - [ ] Test: two-hand sign correctly classified

- [ ] **Step 2.3** — Confidence display
  - [ ] Confidence value passed to frontend
  - [ ] Below threshold: display retry prompt
  - [ ] Test: low-confidence → prompt shown

- [ ] **Step 2.4** — Piper TTS integration
  - [ ] `src/services/tts_service.py`
  - [ ] On sentence finalization: synthesize and play audio
  - [ ] Match voice language to sign language setting
  - [ ] Test: sentence finalized → audio plays

- [ ] **Phase 2 checkpoint:** Signs → Sentence → Audio output

---

## Phase 3 — Web Dashboard

**Goal:** Real-time web interface with hand skeleton, text display, settings.

- [ ] **Step 3.1** — Authentication
  - [ ] Login/logout with bcrypt
  - [ ] Rate limiting
  - [ ] Kiosk bypass
  - [ ] Test: login flow, rate limit

- [ ] **Step 3.2** — Dashboard page
  - [ ] Live camera feed with hand skeleton canvas overlay
  - [ ] Current sign label + confidence bar
  - [ ] Building sentence text
  - [ ] WebSocket push for real-time data
  - [ ] Test: signs appear in browser in real time

- [ ] **Step 3.3** — Settings page
  - [ ] Language dropdown (ASL/BSL/DGS/LSF)
  - [ ] TTS toggle, voice selector
  - [ ] Camera, kiosk, threshold settings
  - [ ] Test: change language → model swaps

- [ ] **Phase 3 checkpoint:** Dashboard shows live recognition with all controls

---

## Phase 4 — Advanced Features

**Goal:** Multi-language, text-to-sign, learning mode, kiosk.

- [ ] **Step 4.1** — Multi-language model swapping
  - [ ] `src/services/language_service.py`
  - [ ] Auto-download models per language
  - [ ] Hot-swap model on language change
  - [ ] Test: switch ASL → BSL → correct model loaded

- [ ] **Step 4.2** — Text-to-sign display
  - [ ] `src/recognition/text_to_sign.py`
  - [ ] Load sign dictionary images
  - [ ] Input text → display sign images sequentially
  - [ ] Test: type "hello" → H-E-L-L-O signs displayed

- [ ] **Step 4.3** — Learning mode
  - [ ] `templates/learning.html` with practice UI
  - [ ] Show word → user signs → classify → grade
  - [ ] Store progress in DB
  - [ ] Test: complete a practice session, progress saved

- [ ] **Step 4.4** — Kiosk mode
  - [ ] `templates/kiosk.html` — full-screen, no nav
  - [ ] Auto-reset timer
  - [ ] Test: inactivity → screen resets

- [ ] **Phase 4 checkpoint:** All modes working, multi-language functional

---

## Phase 5 — Training and Deployment

**Goal:** Data collection, model training, production deployment.

- [ ] **Step 5.1** — Data collection
  - [ ] Record landmarks + label on button press
  - [ ] Save to `data/training_data/`
  - [ ] Test: collect 10 samples, verify saved

- [ ] **Step 5.2** — Training script
  - [ ] `scripts/train-model.sh`
  - [ ] Load data, train LSTM, export TFLite
  - [ ] Test: train on sample data, model file created

- [ ] **Step 5.3** — Deployment
  - [ ] `deploy/deploy_to_pi.sh`
  - [ ] systemd service
  - [ ] Test: deploy to Pi, service starts, dashboard accessible

- [ ] **Step 5.4** — Documentation
  - [ ] `docs/threat_model.md`
  - [ ] Review all markdown files
  - [ ] Test: all links work, no broken references

- [ ] **Phase 5 checkpoint:** Model trainable, deployed on Pi, all docs complete
