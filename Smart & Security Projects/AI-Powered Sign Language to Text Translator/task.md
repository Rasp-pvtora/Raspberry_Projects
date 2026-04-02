# Task List — AI-Powered Sign Language to Text Translator

## Phase 1 — Hand Tracking and Classification

- [ ] **1.1 Project scaffolding**
  - [ ] Create folder structure
  - [ ] Create `requirements.txt`
  - [ ] Create `.env.default`
  - [ ] Create `.gitignore`
  - [ ] Create `app.py` entry point

- [ ] **1.2 Camera capture**
  - [ ] Implement `src/hardware/camera.py`
  - [ ] Support Pi Camera and USB webcam
  - [ ] Configurable resolution and FPS

- [ ] **1.3 MediaPipe hand tracking**
  - [ ] Implement `src/recognition/hand_tracker.py`
  - [ ] Extract 21 landmarks (x, y, z) per hand
  - [ ] Support dual-hand tracking
  - [ ] Normalize landmarks (relative to wrist, scale-invariant)
  - [ ] Return landmark array per frame

- [ ] **1.4 LSTM sign classifier**
  - [ ] Implement `src/recognition/sign_classifier.py`
  - [ ] Load TFLite LSTM model
  - [ ] Buffer 30 frames of landmarks
  - [ ] Classify sequence → sign label + confidence
  - [ ] Filter by `CONFIDENCE_THRESHOLD`

- [ ] **1.5 Mock hardware**
  - [ ] Implement `src/hardware/mock_hardware.py`
  - [ ] Mock camera: return pre-recorded frames
  - [ ] Auto-detect: real camera or mock

- [ ] **1.6 Database**
  - [ ] Implement `src/services/db.py`
  - [ ] Tables: `recognition_log`, `learning_progress`, `settings`

- [ ] **1.7 Unit tests**
  - [ ] Test landmark extraction with sample images
  - [ ] Test classifier with known landmark sequences
  - [ ] Test confidence filtering

## Phase 2 — Sentence Building and Output

- [ ] **2.1 Sentence builder**
  - [ ] Implement `src/recognition/sentence_builder.py`
  - [ ] Accumulate sign labels into text buffer
  - [ ] Detect pause → finalize sentence
  - [ ] Punctuation inference from pause duration
  - [ ] Toggle via `SENTENCE_ENABLED`

- [ ] **2.2 Two-hand support**
  - [ ] Extend classifier for 126-feature input (both hands)
  - [ ] Auto-detect one-hand vs two-hand signs
  - [ ] Toggle via `TWO_HAND_ENABLED`

- [ ] **2.3 Confidence indicator**
  - [ ] Return confidence score with each classification
  - [ ] Color coding: green / yellow / red
  - [ ] Below threshold: "Please sign again"

- [ ] **2.4 Piper TTS**
  - [ ] Implement `src/services/tts_service.py`
  - [ ] Speak finalized sentence via Piper
  - [ ] Match TTS language to sign language
  - [ ] Toggle via `TTS_ENABLED`

- [ ] **2.5 Unit tests**
  - [ ] Test sentence accumulation and pause detection
  - [ ] Test TTS output

## Phase 3 — Web Dashboard

- [ ] **3.1 Flask app + auth**
  - [ ] Session-based login with bcrypt
  - [ ] Rate limiting
  - [ ] Kiosk bypass

- [ ] **3.2 Dashboard page**
  - [ ] Live camera feed with hand skeleton overlay
  - [ ] Recognized sign label + confidence bar
  - [ ] Building sentence display
  - [ ] System stats

- [ ] **3.3 Settings page**
  - [ ] Sign language selector dropdown
  - [ ] Model path, confidence threshold
  - [ ] TTS toggle and voice selector
  - [ ] Camera settings
  - [ ] Kiosk settings

- [ ] **3.4 WebSocket**
  - [ ] Push landmarks + recognition data in real time
  - [ ] Client draws hand skeleton on canvas

- [ ] **3.5 Integration tests**
  - [ ] Test dashboard renders with mock data
  - [ ] Test WebSocket connection

## Phase 4 — Advanced Features

- [ ] **4.1 Multi-sign-language**
  - [ ] Implement `src/services/language_service.py`
  - [ ] Model file per language (asl_lstm.h5, bsl_lstm.h5, etc.)
  - [ ] Switch model when language changed
  - [ ] Dashboard dropdown for language

- [ ] **4.2 Text-to-sign**
  - [ ] Implement `src/recognition/text_to_sign.py`
  - [ ] Load sign dictionary (images/GIFs per word)
  - [ ] Input text → display corresponding sign images
  - [ ] Toggle via `TEXT_TO_SIGN_ENABLED`

- [ ] **4.3 Learning mode**
  - [ ] Create `templates/learning.html`
  - [ ] Implement `src/routes/learning.py`
  - [ ] Show word → user signs → grade correct/incorrect
  - [ ] Track progress in `learning_progress` table
  - [ ] Difficulty levels: alphabet → words → phrases
  - [ ] Toggle via `LEARNING_MODE_ENABLED`

- [ ] **4.4 Kiosk mode**
  - [ ] Create `templates/kiosk.html`
  - [ ] Full-screen, no navigation
  - [ ] Auto-reset after `KIOSK_TIMEOUT_SEC`
  - [ ] Large fonts, high contrast
  - [ ] Toggle via `KIOSK_MODE`

## Phase 5 — Training and Deployment

- [ ] **5.1 Data collection**
  - [ ] Save hand landmarks + label to training directory
  - [ ] Dashboard button to record samples
  - [ ] Toggle via `DATA_COLLECTION_ENABLED`

- [ ] **5.2 Model training script**
  - [ ] Write `scripts/train-model.sh`
  - [ ] Load collected landmarks, train LSTM
  - [ ] Export to TFLite format
  - [ ] Validate accuracy on test set

- [ ] **5.3 Deploy script**
  - [ ] Write `deploy/deploy_to_pi.sh`
  - [ ] rsync + venv + pip install

- [ ] **5.4 systemd service**
  - [ ] Document service unit in README
  - [ ] Test auto-start

- [ ] **5.5 Documentation**
  - [ ] Write `docs/threat_model.md`
  - [ ] Final review of all docs
