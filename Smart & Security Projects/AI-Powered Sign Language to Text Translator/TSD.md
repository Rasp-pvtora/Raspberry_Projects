# TSD — AI-Powered Sign Language to Text Translator

## 1 · Scope

Build a real-time sign language recognition system using MediaPipe hand tracking and LSTM classification on Raspberry Pi. Translate ASL (and other sign languages) gestures into text with sentence-level accumulation, two-hand support, confidence indicators, TTS output, learning mode, and kiosk deployment.

### In scope

| Area | Details |
|---|---|
| **Hand tracking** | MediaPipe Hands — 21 landmarks × 3D per hand |
| **Sign classification** | LSTM/Transformer model on TFLite |
| **Sentence recognition** | Accumulate signs into sentences with pause detection |
| **Two-hand signs** | Dual-hand tracking for complex signs |
| **Multi-language** | ASL, BSL, DGS, LSF with switchable models |
| **Text-to-sign** | Reverse display of sign illustrations |
| **TTS output** | Piper TTS for spoken translation |
| **Learning mode** | Practice and grading system |
| **Kiosk mode** | Public deployment full-screen interface |
| **Web dashboard** | Live feed, recognition display, settings |

### Out of scope

| Area | Reason |
|---|---|
| Full sentence grammar correction | Requires NLP beyond edge capability |
| 3D animated avatar for text-to-sign | Complex 3D rendering; use static images/GIFs |
| Sign language video call | WebRTC integration is a separate project |

---

## 2 · MVP features

### 2.1 — Hand landmark extraction (MediaPipe)

**Priority: P0**

- MediaPipe Hands: 21 landmarks per hand, 3D coordinates (x, y, z).
- Support single and dual hand tracking.
- Extract landmarks per frame → normalize → feed to classifier.

### 2.2 — Sign classification (LSTM)

**Priority: P0**

- LSTM model: input = sequence of 30 frames of landmarks.
- Output: sign label + confidence.
- TFLite runtime for Pi-optimized inference.
- ASL alphabet (26 signs) + 50 common words as MVP vocabulary.

### 2.3 — Sentence builder

**Priority: P0**

- Accumulate recognized signs into a text buffer.
- Pause of `SENTENCE_PAUSE_SEC` → finalize sentence.
- Display building sentence in real time.
- Toggle: `SENTENCE_ENABLED`.

### 2.4 — Web dashboard

**Priority: P0**

**Database schema:**

**Table: `recognition_log`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | Recognition time |
| `sign_label` | TEXT | Recognized sign |
| `confidence` | REAL | Classification confidence |
| `language` | TEXT | Sign language code |
| `sentence` | TEXT | Full sentence (when finalized) |

**Table: `learning_progress`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `sign_label` | TEXT | Sign practiced |
| `language` | TEXT | Sign language |
| `attempts` | INTEGER | Total attempts |
| `correct` | INTEGER | Correct attempts |
| `last_practiced` | DATETIME | Last practice time |

**Table: `settings`**

| Column | Type | Description |
|---|---|---|
| `key` | TEXT PK | Setting name |
| `value` | TEXT | Value (JSON) |
| `updated_at` | DATETIME | Last update |

### 2.5 — Authentication

**Priority: P0**

- bcrypt + session + rate limiting. Kiosk mode bypasses login.

### 2.6 — Mock hardware

**Priority: P0**

- Mock camera with pre-recorded hand landmark sequences.

---

## 3 · Nice-to-have features

### 3.1 — TTS audio output (Piper)

Toggle: `TTS_ENABLED`. Requires speaker hardware.

### 3.2 — Text-to-sign display

Toggle: `TEXT_TO_SIGN_ENABLED`. Requires sign dictionary assets.

### 3.3 — Learning mode

Toggle: `LEARNING_MODE_ENABLED`. Useful for educational deployments.

### 3.4 — Kiosk mode

Toggle: `KIOSK_MODE`. For public service kiosks.

### 3.5 — Additional sign languages (BSL, DGS, LSF)

Requires training separate models per language.

---

## 4 · High-level architecture

```
┌─────────────────────────────────────────────────┐
│         SIGN LANGUAGE TRANSLATOR                │
│                                                 │
│  Camera → MediaPipe Hands → Landmarks           │
│       → LSTM Classifier → Sign + Confidence     │
│       → Sentence Builder → Text output          │
│       → Piper TTS → Audio output (optional)     │
│                                                 │
│  Dashboard ← WebSocket ← Recognition data       │
│  Text-to-Sign → Sign dictionary → Display       │
│  Learning → Prompt → Grade → Progress           │
└─────────────────────────────────────────────────┘
```

---

## 5 · Security / Threat model

| # | Threat | Mitigation |
|---|---|---|
| T1 | Credential exposure | `.env` in `.gitignore`, `chmod 600` |
| T2 | Brute-force | Rate limiting |
| T3 | Camera privacy | Local only, no cloud |
| T4 | XSS | Jinja2 auto-escaping |
| T5 | Kiosk escape | No admin access in kiosk mode, no URL bar |

---

## 6 · Suggested tech stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Web | Flask 3.1 + SocketIO |
| Hand tracking | MediaPipe 0.10 |
| Classification | TFLite (LSTM) |
| TTS | Piper TTS 1.2 |
| Database | SQLite |
| Frontend | Jinja2 + Chart.js + Socket.IO |

---

## 7 · Development phases

### Phase 1 — Hand tracking and classification

| # | Task | Priority |
|---|---|---|
| 1.1 | Project scaffolding | P0 |
| 1.2 | Camera capture module | P0 |
| 1.3 | MediaPipe hand landmark extraction | P0 |
| 1.4 | LSTM model loading (TFLite) | P0 |
| 1.5 | Sign classification pipeline | P0 |
| 1.6 | Mock hardware | P0 |
| 1.7 | Unit tests | P1 |

### Phase 2 — Sentence building and output

| # | Task | Priority |
|---|---|---|
| 2.1 | Sentence builder with pause detection | P0 |
| 2.2 | Two-hand sign support | P1 |
| 2.3 | Confidence indicator logic | P0 |
| 2.4 | Piper TTS integration | P1 |
| 2.5 | Unit tests | P1 |

### Phase 3 — Web dashboard

| # | Task | Priority |
|---|---|---|
| 3.1 | Flask app + auth | P0 |
| 3.2 | Dashboard: live feed + recognition display | P0 |
| 3.3 | Settings: language, model, TTS, camera | P0 |
| 3.4 | WebSocket real-time landmarks + text | P0 |
| 3.5 | Integration tests | P1 |

### Phase 4 — Advanced features

| # | Task | Priority |
|---|---|---|
| 4.1 | Multi-sign-language support + model swapping | P1 |
| 4.2 | Text-to-sign display | P2 |
| 4.3 | Learning/practice mode | P2 |
| 4.4 | Kiosk mode (full-screen, auto-reset) | P2 |

### Phase 5 — Training and deployment

| # | Task | Priority |
|---|---|---|
| 5.1 | Data collection mode (save landmarks) | P1 |
| 5.2 | Model training script | P1 |
| 5.3 | Deploy script | P0 |
| 5.4 | systemd service | P1 |
| 5.5 | Documentation (threat model, task, plan) | P1 |

---

## 8 · `.env.default` reference

```ini
# ─── General ────────────────────────────────────────────────────
PORT=5000
HOST=0.0.0.0
SESSION_SECRET=CHANGE_ME_TO_A_RANDOM_STRING
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme

# ─── Camera ─────────────────────────────────────────────────────
CAMERA_SOURCE=0
CAMERA_RESOLUTION=640x480

# ─── Recognition ────────────────────────────────────────────────
SIGN_LANGUAGE=asl
MODEL_PATH=./models/asl_lstm.h5
CONFIDENCE_THRESHOLD=0.7
SENTENCE_ENABLED=true
SENTENCE_PAUSE_SEC=2.0
TWO_HAND_ENABLED=true

# ─── Text-to-Sign ──────────────────────────────────────────────
TEXT_TO_SIGN_ENABLED=true

# ─── TTS ────────────────────────────────────────────────────────
TTS_ENABLED=false
TTS_VOICE=en_US-lessac-medium

# ─── Learning Mode ──────────────────────────────────────────────
LEARNING_MODE_ENABLED=true

# ─── Kiosk ──────────────────────────────────────────────────────
KIOSK_MODE=false
KIOSK_TIMEOUT_SEC=60

# ─── Data Collection ────────────────────────────────────────────
DATA_COLLECTION_ENABLED=false
```

---

## 9 · Deliverables

| # | Deliverable | Phase |
|---|---|---|
| D1 | Hand tracking + sign classification pipeline | Phase 1 |
| D2 | Sentence building + TTS output | Phase 2 |
| D3 | Web dashboard with live recognition | Phase 3 |
| D4 | Multi-language, text-to-sign, learning, kiosk | Phase 4 |
| D5 | Training pipeline, deployment, documentation | Phase 5 |
