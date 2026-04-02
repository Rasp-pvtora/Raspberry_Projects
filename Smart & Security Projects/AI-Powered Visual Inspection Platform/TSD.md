# TSD — AI-Powered Visual Inspection Platform

## 1 · Scope

Build a dual-mode visual inspection system for Raspberry Pi: Quality Control (QC) for detecting product defects on a conveyor, and PPE Detection for enforcing safety gear compliance at work zone entry points. Both modes share a common YOLOv8n inference pipeline, web dashboard, GPIO abstraction, alert system, and reporting engine. Modes can run individually or simultaneously, toggled from the dashboard or `.env`.

### In scope

| Area | Details |
|---|---|
| **QC mode** | Defect classification (scratch, dent, discoloration, misalignment, foreign object), GPIO reject, SPC charts, barcode correlation |
| **PPE mode** | Hard hat, vest, goggles, gloves detection; buzzer alarm; barrier gate; worker face ID; zone-based rules |
| **Dual mode** | Both modes running simultaneously on separate cameras or alternating frames |
| **Multi-zone** | Different detection rules per camera/zone |
| **Multi-camera** | Up to 4 cameras managed by one Pi |
| **Night vision** | Pi NoIR + IR LEDs for 24/7 PPE monitoring |
| **SPC** | X-bar and R-charts with control limits and auto-halt |
| **Reporting** | Automated PDF/CSV daily reports for compliance and QC |
| **Training** | On-device image capture, labeling, dataset export, model retraining |
| **OPC-UA** | Industrial data export to SCADA/MES systems |
| **Alerts** | Email, Telegram, webhook, GPIO |
| **Web dashboard** | Live annotated camera feed, mode toggle, charts, reports |
| **Authentication** | Session-based with bcrypt and rate limiting |
| **Mock mode** | Full development on laptop with simulated camera and GPIO |

### Out of scope

| Area | Reason |
|---|---|
| Conveyor belt mechanical design | Mechanical engineering; user provides their own belt or desk |
| Cloud model training | Training happens on-device for small datasets; large-scale training requires external GPU |
| HIPAA/FDA compliance | Regulatory certification is domain-specific; software provides data but certification is external |
| Real-time edge TPU | Google Coral / Hailo accelerators documented as upgrade path |

---

## 2 · MVP features

### 2.1 — YOLOv8n inference engine

**Priority: P0**

- Load YOLOv8n model (`.pt` format) using `ultralytics` library.
- Run inference on camera frames at the configured FPS.
- Return bounding boxes, class labels, and confidence scores.
- Support swapping models at runtime (QC model ↔ PPE model).
- Mock mode: return simulated detections for development.

### 2.2 — QC defect detection

**Priority: P0**

- Detect and classify product defects into configurable categories.
- Log: timestamp, defect class, confidence, bounding box, image snapshot.
- GPIO reject mechanism: activate when defect detected above threshold.
- Toggle: `QC_ENABLED=true/false` in `.env`.

### 2.3 — PPE safety detection

**Priority: P0**

- Detect presence/absence of required safety equipment on persons.
- Compare detected PPE against `PPE_REQUIRED_CLASSES` list.
- Trigger alarm (buzzer GPIO) if required PPE missing.
- Log: timestamp, detected gear, missing gear, person image.
- Time-based enforcement: active only during configured hours.
- Toggle: `PPE_ENABLED=true/false` in `.env`.

### 2.4 — Mode manager

**Priority: P0**

- Coordinate QC and PPE modes based on `MODE` setting.
- `qc`: only QC pipeline runs.
- `ppe`: only PPE pipeline runs.
- `both`: both pipelines run (separate cameras or alternating frames).
- Mode switchable from dashboard without restart.

### 2.5 — Web dashboard

**Priority: P0**

**Database schema:**

**Table: `inspections`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | Detection time |
| `mode` | TEXT | `qc` or `ppe` |
| `camera_id` | INTEGER | Camera source index |
| `zone` | TEXT | Zone name (if zones enabled) |
| `class_label` | TEXT | Detection class (e.g., `scratch`, `hardhat`) |
| `confidence` | REAL | Detection confidence |
| `bbox_x` | REAL | Bounding box X |
| `bbox_y` | REAL | Bounding box Y |
| `bbox_w` | REAL | Bounding box width |
| `bbox_h` | REAL | Bounding box height |
| `action_taken` | TEXT | `reject`, `alarm`, `barrier_closed`, `none` |
| `image_path` | TEXT | Path to snapshot image |
| `barcode` | TEXT | Product barcode (if QC + barcode enabled) |
| `worker_id` | TEXT | Worker name (if PPE + face ID enabled) |

**Table: `spc_data`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | Sample time |
| `subgroup_index` | INTEGER | SPC subgroup number |
| `defect_count` | INTEGER | Defects in subgroup |
| `sample_size` | INTEGER | Items in subgroup |
| `defect_rate` | REAL | Defect ratio |

**Table: `workers`** (PPE face ID)

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT | Worker name |
| `face_encoding` | BLOB | 128-d face encoding |
| `department` | TEXT | Worker department |
| `enrolled_at` | DATETIME | Enrollment date |

**Table: `daily_reports`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `date` | DATE | Report date |
| `mode` | TEXT | `qc`, `ppe`, or `both` |
| `total_inspected` | INTEGER | Total items/persons |
| `total_defects` | INTEGER | Total defects/violations |
| `defect_rate` | REAL | Defect/violation rate |
| `report_path` | TEXT | Path to generated PDF |

**Table: `settings`**

| Column | Type | Description |
|---|---|---|
| `key` | TEXT PK | Setting name |
| `value` | TEXT | Setting value (JSON) |
| `updated_at` | DATETIME | Last update |

### 2.6 — Authentication

**Priority: P0**

- bcrypt password hashing.
- Rate limiting: 10 attempts / 15 min.
- Session cookies (HttpOnly, SameSite).
- Session expiry: 24 hours.

### 2.7 — Mock hardware

**Priority: P0**

- Simulated camera frames (sample images with embedded defects/PPE).
- Virtual GPIO (log actions to console).
- All dashboard features work identically.

### 2.8 — Deploy script

**Priority: P0**

- `deploy/deploy_to_pi.sh`: rsync + venv + pip install.
- systemd service unit documented in README.

---

## 3 · Nice-to-have features

### 3.1 — OPC-UA export

**Requires:** Industrial SCADA/MES system on the network.

- OPC-UA server on configurable port.
- Real-time inspection nodes.
- Toggle: `OPCUA_ENABLED=true`.

### 3.2 — Worker face identification

**Requires:** Worker enrollment (photo capture or upload).

- `face_recognition` library for encoding and matching.
- Privacy implications: document data handling.
- Toggle: `PPE_FACE_ID_ENABLED=true`.

### 3.3 — Night vision

**Requires:** Pi NoIR Camera Module (~$25) + IR LED ring (~$5–10).

- Auto-switch based on ambient light sensor or time of day.
- Toggle: `NIGHT_VISION_ENABLED=true`.

### 3.4 — Alert channels

**Requires:** Email SMTP credentials, Telegram bot token, or webhook endpoint.

- Configurable per-event type.
- Toggles: `ALERT_EMAIL_ENABLED`, `ALERT_TELEGRAM_ENABLED`, `ALERT_WEBHOOK_ENABLED`.

---

## 4 · High-level architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 AI-POWERED VISUAL INSPECTION PLATFORM           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    MODE MANAGER                          │  │
│  │         MODE = qc | ppe | both                          │  │
│  └─────────────┬────────────────────┬──────────────────────┘  │
│                │                    │                          │
│  ┌─────────────▼──────┐  ┌─────────▼──────────┐              │
│  │   QC PIPELINE      │  │   PPE PIPELINE     │              │
│  │                     │  │                    │              │
│  │ Camera (HQ/close)   │  │ Camera (wide/gate) │              │
│  │ → YOLOv8n (defects) │  │ → YOLOv8n (PPE)   │              │
│  │ → Classify defect   │  │ → Check required   │              │
│  │ → Barcode correlate │  │ → Face ID worker   │              │
│  │ → GPIO reject       │  │ → GPIO alarm/gate  │              │
│  │ → SPC update        │  │ → Compliance log   │              │
│  └─────────┬───────────┘  └────────┬───────────┘              │
│            │                       │                          │
│  ┌─────────▼───────────────────────▼───────────┐              │
│  │              SHARED SERVICES                │              │
│  │                                             │              │
│  │  SQLite DB │ Alert Engine │ Report Generator │              │
│  │  OPC-UA    │ Training     │ System Monitor   │              │
│  └─────────────────────┬───────────────────────┘              │
│                        │                                      │
│  ┌─────────────────────▼───────────────────────┐              │
│  │              WEB DASHBOARD                  │              │
│  │  Flask + SocketIO + Chart.js                │              │
│  │  Live feed │ SPC │ Reports │ Settings       │              │
│  └─────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5 · Security / Threat model

| # | Threat | Mitigation |
|---|---|---|
| T1 | Credential exposure | `.env` in `.gitignore`, `chmod 600` |
| T2 | Brute-force login | Rate limiting: 10/15 min |
| T3 | Session hijacking | Strong `SESSION_SECRET`, HttpOnly, SameSite cookies |
| T4 | XSS | Jinja2 auto-escaping |
| T5 | SQL injection | Parameterized queries |
| T6 | Unauthorized GPIO control | All endpoints require auth |
| T7 | Face data privacy | Local storage only, enrollment requires auth, deletion available |
| T8 | OPC-UA network exposure | Firewall OPC-UA port, local network only |
| T9 | Model poisoning via training | Training requires admin auth, model versioning |
| T10 | Camera feed interception | Local network, HTTPS available via nginx reverse proxy |

---

## 6 · Suggested tech stack

### Backend

| Component | Technology | Justification |
|---|---|---|
| Language | Python 3.11+ | Best ML/CV ecosystem |
| Web framework | Flask 3.1 + SocketIO | Lightweight, real-time capable |
| ML inference | Ultralytics YOLOv8n | State-of-art detection, optimized for edge |
| Computer vision | OpenCV 4.10 | Frame capture, preprocessing |
| Face recognition | face_recognition 1.3 | dlib-based, good accuracy |
| Barcode | pyzbar 0.1.9 | Cross-platform barcode/QR |
| Database | SQLite | Zero-config file-based |
| Reports | ReportLab 4.2 | PDF generation |
| GPIO | RPi.GPIO | Standard Pi GPIO |
| OPC-UA | python-opcua | Industrial protocol |
| Auth | bcrypt + Flask sessions | Password hashing |

### Frontend

| Component | Technology |
|---|---|
| Templates | Jinja2 |
| Charts | Chart.js 4 (CDN) |
| WebSocket | Socket.IO client (CDN) |
| Styling | Custom CSS (dark theme) |

---

## 7 · Development phases

### Phase 1 — Core inference and camera

| # | Task | Priority |
|---|---|---|
| 1.1 | Project scaffolding | P0 |
| 1.2 | Camera capture module (Pi Camera, USB, multi-cam) | P0 |
| 1.3 | YOLOv8n model loader and inference | P0 |
| 1.4 | Mock hardware (simulated camera + GPIO) | P0 |
| 1.5 | Mode manager (QC/PPE/both) | P0 |
| 1.6 | Unit tests | P1 |

### Phase 2 — QC pipeline

| # | Task | Priority |
|---|---|---|
| 2.1 | QC defect detection and classification | P0 |
| 2.2 | GPIO reject mechanism | P0 |
| 2.3 | Barcode/QR correlation | P1 |
| 2.4 | SPC calculations and auto-halt | P1 |
| 2.5 | Unit tests | P1 |

### Phase 3 — PPE pipeline

| # | Task | Priority |
|---|---|---|
| 3.1 | PPE detection and compliance check | P0 |
| 3.2 | GPIO alarm (buzzer + LED) | P0 |
| 3.3 | Access barrier integration | P1 |
| 3.4 | Time-based enforcement | P1 |
| 3.5 | Worker face identification | P2 |
| 3.6 | Unit tests | P1 |

### Phase 4 — Web dashboard

| # | Task | Priority |
|---|---|---|
| 4.1 | Flask app + auth + layout | P0 |
| 4.2 | Dashboard: live feed with overlays | P0 |
| 4.3 | QC page: SPC charts, defect stats | P0 |
| 4.4 | PPE page: compliance rate, violation log | P0 |
| 4.5 | Settings: mode toggle, zones, alerts | P0 |
| 4.6 | Reports page: generate/view PDF/CSV | P1 |
| 4.7 | Training page: capture, label, retrain | P2 |
| 4.8 | WebSocket real-time feed | P0 |

### Phase 5 — Advanced features

| # | Task | Priority |
|---|---|---|
| 5.1 | Multi-zone inspection | P1 |
| 5.2 | Multi-camera support | P1 |
| 5.3 | Night vision (NoIR + IR) | P2 |
| 5.4 | Alert channels (email, Telegram, webhook) | P1 |
| 5.5 | OPC-UA export | P2 |

### Phase 6 — Deployment and polish

| # | Task | Priority |
|---|---|---|
| 6.1 | Deploy script | P0 |
| 6.2 | systemd service | P1 |
| 6.3 | Automated daily reports | P1 |
| 6.4 | Threat model document | P1 |
| 6.5 | End-to-end testing | P1 |

---

## 8 · `.env.default` reference

```ini
# ─── General ────────────────────────────────────────────────────
PORT=5000
HOST=0.0.0.0
SESSION_SECRET=CHANGE_ME_TO_A_RANDOM_STRING
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme

# ─── Mode Control ───────────────────────────────────────────────
MODE=both
QC_ENABLED=true
PPE_ENABLED=true

# ─── Camera ─────────────────────────────────────────────────────
CAMERA_SOURCE=0
CAMERA_RESOLUTION=640x480
CAMERA_FPS=15
CAMERA_2_ENABLED=false
CAMERA_2_SOURCE=1
NIGHT_VISION_ENABLED=false

# ─── QC Settings ────────────────────────────────────────────────
QC_MODEL_PATH=./models/qc_defect.pt
QC_CONFIDENCE_THRESHOLD=0.5
QC_DEFECT_CLASSES=scratch,dent,discoloration,misalignment,foreign_object
QC_REJECT_ENABLED=true
QC_REJECT_GPIO_PIN=17
QC_BARCODE_ENABLED=false
QC_SPC_ENABLED=true
QC_SPC_SAMPLE_SIZE=25
QC_AUTO_HALT_DEFECT_RATE=0.05

# ─── PPE Settings ───────────────────────────────────────────────
PPE_MODEL_PATH=./models/ppe_safety.pt
PPE_CONFIDENCE_THRESHOLD=0.6
PPE_CLASSES=hardhat,vest,goggles,gloves
PPE_REQUIRED_CLASSES=hardhat,vest
PPE_ALARM_ENABLED=true
PPE_ALARM_GPIO_PIN=27
PPE_BARRIER_ENABLED=false
PPE_BARRIER_GPIO_PIN=22
PPE_FACE_ID_ENABLED=false
PPE_ENFORCEMENT_START=07:00
PPE_ENFORCEMENT_END=18:00

# ─── Zones ──────────────────────────────────────────────────────
ZONES_ENABLED=false
ZONE_CONFIG_PATH=./config/zones.json

# ─── Alerts ─────────────────────────────────────────────────────
ALERT_EMAIL_ENABLED=false
ALERT_EMAIL_SMTP_HOST=
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=
ALERT_EMAIL_PASSWORD=
ALERT_EMAIL_RECIPIENT=
ALERT_TELEGRAM_ENABLED=false
ALERT_TELEGRAM_BOT_TOKEN=
ALERT_TELEGRAM_CHAT_ID=
ALERT_WEBHOOK_ENABLED=false
ALERT_WEBHOOK_URL=

# ─── OPC-UA ─────────────────────────────────────────────────────
OPCUA_ENABLED=false
OPCUA_PORT=4840

# ─── Training ───────────────────────────────────────────────────
TRAINING_CAPTURE_ENABLED=false
TRAINING_DATA_DIR=./models/training_data

# ─── Reports ────────────────────────────────────────────────────
REPORT_AUTO_DAILY=true
REPORT_OUTPUT_DIR=./data/reports
```

---

## 9 · Deliverables

| # | Deliverable | Phase |
|---|---|---|
| D1 | Core inference engine + camera + mode manager | Phase 1 |
| D2 | QC defect detection with reject mechanism and SPC | Phase 2 |
| D3 | PPE detection with alarm and compliance logging | Phase 3 |
| D4 | Web dashboard with live feed, charts, and controls | Phase 4 |
| D5 | Multi-zone, multi-camera, night vision, alerts, OPC-UA | Phase 5 |
| D6 | Deployment script, reports, documentation | Phase 6 |
