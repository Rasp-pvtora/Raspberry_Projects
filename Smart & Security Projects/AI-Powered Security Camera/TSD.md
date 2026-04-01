# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for **AI-Powered Security Camera**.

---

## 1. Scope

This project builds an AI-powered security camera system on a Raspberry Pi that uses machine learning for object detection, facial recognition, and pet/animal detection. The system reduces false alarms by only triggering notifications for configured detection classes and zones. A web dashboard provides live camera feeds, event timeline with recorded clips, face enrollment, zone drawing, and multi-camera management.

**Key goals:**
- Real-time object detection using YOLOv11n on Raspberry Pi.
- Facial recognition with dashboard-based enrollment (no code changes needed).
- Zone-based detection (inclusion/exclusion polygons drawn on the camera feed).
- Event recording with pre-buffer video clips.
- Multi-camera support from a single dashboard.
- Night vision with Pi NoIR camera and IR LEDs.
- Notifications via Telegram, email, and MQTT.

---

## 2. Minimum Viable Features (MVP)

### 2.1 Detection Pipeline

| Stage | Component | Tool | Description |
|---|---|---|---|
| **Capture** | Camera Manager | Picamera2 / OpenCV | Captures frames from Pi Camera or USB webcam |
| **Detect** | YOLOv11n | ultralytics | Detects objects with bounding boxes (80 COCO classes) |
| **Recognize** | Face Recognizer | face_recognition (dlib) | Matches faces against enrolled database |
| **Zone check** | Zone Manager | Custom polygon logic | Filters detections by inclusion/exclusion zones |
| **Record** | Clip Recorder | OpenCV VideoWriter | Saves event clips with pre-buffer |
| **Notify** | Notification Service | Telegram / Email / MQTT | Sends alerts with snapshots |
| **Log** | Event Service | SQLite | Stores event metadata |
| **Stream** | WebSocket | Flask-SocketIO | Live annotated feed to dashboard |

### 2.2 Detection Models

**YOLOv11n (default):**
- 8–13 FPS on Pi 4/5.
- Very high precision, multi-task (detection, segmentation, pose, OBB).
- Easy development with `ultralytics` library.
- Custom training supported (transfer learning on user datasets).

**TFLite MobileNetV2-SSD (alternative):**
- 15–20 FPS on Pi 4/5.
- Average precision, detection only.
- Native Google Coral Edge TPU support for hardware acceleration.
- Lower memory footprint.

### 2.3 Web Dashboard (Flask + SocketIO + Jinja2)

- **Authentication:** Session-based login with credentials stored in `.env`. Rate-limited login endpoint.
- **Dashboard page:** Live camera feed with detection overlay, alert feed, system stats, FPS counter.
- **Events page:** Chronological timeline, filterable by date/camera/class/face/zone. Video clip playback and snapshot view. Download clips. Enable/disable recording toggle (on/off button).
- **Faces page:** Face enrollment gallery. Upload photos or capture from live feed. Add, remove, update enrolled faces.
- **Zones page:** Draw inclusion/exclusion polygon zones on the live camera feed. Name, toggle, edit, delete zones.
- **Cameras page:** Add and configure multiple cameras (Pi Camera, USB, RTSP). Per-camera resolution, FPS, and detection settings.
- **Settings page:** Detection confidence, classes, notification channels, recording settings, password change.

### 2.4 Facial Recognition and Enrollment

- Upload photos or capture from live feed to enroll faces.
- 128-dimensional face encoding stored in `models/face_encodings.pkl`.
- Real-time matching with configurable tolerance.
- Per-person notification rules (notify on unknown only, or on specific person).

### 2.5 Pet and Animal Detection

- COCO-trained classes: cat, dog, bird, horse, sheep, cow, etc.
- Configurable: ignore pets silently, log separately, or notify.
- Advanced: custom pet classification via transfer learning (train on user photos).

### 2.6 Zone-Based Detection

- Inclusion zones: alert only within this area.
- Exclusion zones: ignore detections in this area.
- Multiple zones per camera with labels and independent rules.
- Drawn interactively on the camera feed from the dashboard.

### 2.7 Multi-Camera Support

- Pi Camera (CSI), USB webcams, RTSP/IP cameras.
- Each camera has an independent detection pipeline.
- Dashboard grid view for simultaneous monitoring.
- Per-camera zones and settings.

### 2.8 Event Timeline with Video Clips

- Pre-buffer recording (default 3 seconds before detection).
- Configurable clip duration (default 10 seconds).
- Auto-rotation of old clips when storage limit is reached.
- Dashboard on/off toggle for recording.
- Event metadata: timestamp, camera, class, confidence, face, zone, snapshot, clip path.

### 2.9 Night Vision

- Pi NoIR Camera Module (no IR filter) + IR LED board.
- GPIO-controlled IR LEDs (`IR_GPIO_PIN`).
- Auto-switch based on ambient light (frame brightness analysis).
- Manual toggle from dashboard.

### 2.10 Notifications

- **Telegram:** Bot API with snapshot image, detection details, timestamp.
- **Email:** SMTP with HTML email, snapshot attachment.
- **MQTT:** JSON payload to configurable topic (Home Assistant integration).
- Per-class and per-zone notification rules.

### 2.11 Environment Configuration

- All configuration via `.env` file (created from `.env.default` template).
- `.env` is in `.gitignore` and never committed.
- Settings page provides a web-based editor.

### 2.12 Deployment

- `deploy/deploy_to_pi.sh` script: rsync files to the Pi, create venv, install dependencies.
- `scripts/setup-camera.sh` for CSI camera enablement.
- `scripts/setup-ir.sh` for IR LED board configuration.
- `scripts/download-models.sh` for model downloads.
- Systemd service file for auto-start.

---

## 3. Nice-to-Have Features

These features require paid third-party services, additional hardware investment, or substantially more complexity.

### 3.1 Hardware Acceleration

- **Google Coral USB Accelerator** (~$60–75): Push TFLite inference to 50+ FPS. Requires converting models to TFLite + Edge TPU format.
- **Raspberry Pi AI HAT+** (Pi 5 only, ~$70): Hailo-8L NPU with 13 TOPS. Native integration with Picamera2 pipeline.
- **Intel Neural Compute Stick 2** (~$70): OpenVINO model support, 20–30 FPS.

### 3.2 Cloud Object Storage

- Upload event clips and snapshots to AWS S3, Google Cloud Storage, or Backblaze B2 for off-site backup.
- Requires cloud account and incurs storage costs.

### 3.3 Advanced Analytics Dashboard

- Detection heatmaps (where detections occur most frequently).
- Trend charts (detections per hour/day/week).
- Export reports as CSV/PDF.

### 3.4 Pose Estimation

- YOLOv11n supports pose estimation (body keypoints).
- Could be used for fall detection (elderly care) or activity recognition.
- Requires additional inference model and logic.

### 3.5 License Plate Recognition

- Integrate PaddleOCR or an LPR-specific model for vehicle plate reading.
- Useful for driveway/parking monitoring.
- Requires OCR model and additional training for regional plates.

---

## 4. High-Level Architecture

```
                      ┌────────────────────────────────────────────────────┐
                      │            Raspberry Pi                            │
                      │                                                    │
  Browser ─HTTP────► │  Flask (port 5000)                                  │
  Browser ──WS─────► │  ├── Session auth + rate limiting                   │
                      │  ├── Jinja2 templates (dashboard, events, etc.)    │
                      │  ├── REST API (/api/events, /api/faces, etc.)      │
                      │  ├── SocketIO (live video stream + alerts)         │
                      │  └── Static files (/static)                        │
                      │                                                    │
                      │  Detection Pipeline:                                │
                      │  ┌──────────────────────────────────────────┐      │
                      │  │ Camera → YOLOv11n (detect)               │      │
                      │  │       → face_recognition (identify)      │      │
                      │  │       → Zone Manager (filter)            │      │
                      │  │       → Clip Recorder (record)           │      │
                      │  │       → Notification Service (alert)     │      │
                      │  │       → Event Service (log to SQLite)    │      │
                      │  │       → WebSocket (stream to dashboard)  │      │
                      │  └──────────────────────────────────────────┘      │
                      │                                                    │
                      │  Camera Sources:                                    │
                      │  ├── Pi Camera (CSI via Picamera2)                 │
                      │  ├── USB Webcam (OpenCV VideoCapture)              │
                      │  └── RTSP/IP Camera (OpenCV network stream)        │
                      │                                                    │
                      │  Storage:                                           │
                      │  ├── SQLite database (events metadata)             │
                      │  ├── clips/ directory (event video clips)          │
                      │  └── models/ (YOLO weights, face encodings)        │
                      │                                                    │
                      │  Night Vision:                                      │
                      │  ├── Pi NoIR Camera (no IR filter)                 │
                      │  └── IR LED board (GPIO-controlled)                │
                      └────────────────────────────────────────────────────┘
```

---

## 5. Security and Threat Model

**Primary assets:**
- Dashboard credentials and session tokens.
- Face enrollment data (biometric information).
- Recorded video clips (private footage).
- Notification tokens (Telegram bot, SMTP, MQTT).
- `.env` file (contains passwords and API keys).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Brute-force login | Rate limiting (10 attempts per 15 min); strong password |
| Session hijacking | `httpOnly`, `sameSite` cookies; strong session secret |
| Unauthorized camera access | Authentication required for all endpoints; no public stream |
| Face data theft | Stored locally only; file permissions; no cloud upload |
| Video clip exposure | `clips/` protected by authentication; auto-rotation; `.gitignore` |
| XSS via event metadata | HTML-escape all detection labels and user input in templates |
| Path traversal in clip download | `path.resolve()` + `startsWith` check against clips directory |
| Notification token leak | Tokens in `.env` only; masked in Settings API; `chmod 600 .env` |
| Camera feed MITM | Use HTTPS (reverse proxy with nginx/caddy); local network only |
| Malicious file upload (face photos) | Validate image format and size; resize on upload |

See [docs/threat_model.md](docs/threat_model.md) for the complete analysis.

---

## 6. Suggested Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| Backend | Python 3.11+ / Flask | Mature, simple, great ML ecosystem |
| Real-time | Flask-SocketIO | WebSocket for live video and alerts |
| Templating | Jinja2 | Server-side rendering, no build step |
| Detection | ultralytics (YOLOv11n) | State-of-the-art, few lines to train/detect |
| Face recognition | face_recognition (dlib) | Simple API, proven accuracy |
| Video | OpenCV + Picamera2 | Standard video pipeline for Pi |
| Database | SQLite | Lightweight, zero-config, sufficient for event logs |
| Notifications | Telegram Bot API, SMTP, MQTT | Free channels, widely supported |
| Auth | Session-based + bcrypt | Simple, single-user device auth |
| CSS | Custom dark theme | Lightweight, no framework dependency |

---

## 7. Development Phases & Concrete Steps

### Phase A — Project scaffold and camera (Week 1)

1. Initialize Python project with `requirements.txt` and virtual environment.
2. Create `.env.default` template and `.gitignore`.
3. Implement Flask server with Jinja2 layout and sidebar navigation.
4. Implement session-based authentication.
5. Create dark-themed CSS and login page.
6. Implement camera manager (Picamera2 + OpenCV USB fallback).
7. Implement WebSocket live stream (annotated frames to browser).
8. Build Dashboard page with live feed.

### Phase B — Detection pipeline (Week 1–2)

1. Integrate YOLOv11n via ultralytics (download model, run inference).
2. Implement detection overlay (bounding boxes, labels, confidence).
3. Implement face recognizer (face_recognition library, encoding storage).
4. Build Faces page with enrollment UI (upload + capture from feed).
5. Implement pet/animal detection (COCO class filtering).
6. Create `scripts/download-models.sh`.

### Phase C — Zones and recording (Week 2)

1. Implement zone manager (polygon inclusion/exclusion zones).
2. Build Zones page with canvas-based zone drawing on live feed.
3. Implement clip recorder (pre-buffer, event trigger, storage rotation).
4. Implement event service (SQLite: log events with metadata).
5. Build Events page (timeline, filters, clip playback, on/off toggle).
6. Implement storage manager (auto-delete old clips, disk usage tracking).

### Phase D — Notifications and multi-camera (Week 2–3)

1. Implement Telegram notification (Bot API, snapshot + details).
2. Implement email notification (SMTP, HTML email, snapshot attachment).
3. Implement MQTT notification (JSON payload).
4. Implement multi-camera support (independent pipelines per camera).
5. Build Cameras page (add, configure, remove cameras; grid view).
6. Implement per-camera zones and settings.

### Phase E — Night vision and polish (Week 3)

1. Implement IR LED GPIO control (auto-switch based on brightness).
2. Create `scripts/setup-camera.sh` and `scripts/setup-ir.sh`.
3. Implement night vision dashboard toggle.
4. Build Settings page (detection, notifications, recording, password).
5. Write deployment script `deploy/deploy_to_pi.sh`.
6. Create systemd service file.
7. Test on Raspberry Pi 4 and Pi 5.

### Phase F — Documentation (Week 3–4)

1. Write `README.md` with full setup guide.
2. Write `TSD.md` (this document).
3. Write `task.md` engineering checklist.
4. Write `docs/threat_model.md`.
5. End-to-end testing on Pi.

---

## 8. Deliverables

- Full working security camera with YOLOv11n object detection on Raspberry Pi.
- Facial recognition with dashboard-based face enrollment.
- Pet/animal detection using COCO-trained model.
- Zone-based detection (inclusion/exclusion polygons).
- Multi-camera support from a single dashboard.
- Event timeline with pre-buffer video clips and on/off toggle.
- Night vision with Pi NoIR camera and GPIO-controlled IR LEDs.
- Notifications via Telegram, email, and MQTT.
- Web dashboard with live stream, events, faces, zones, cameras, and settings.
- Setup scripts for camera, IR, and model downloads.
- Deploy script for Raspberry Pi (SSH alias: `rasp-pi` at `192.168.216.90`).
- `README.md`, `TSD.md`, `task.md`, `docs/threat_model.md`.
