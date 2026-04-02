# Task List — AI-Powered Visual Inspection Platform

## Phase 1 — Core Inference and Camera

- [ ] **1.1 Project scaffolding**
  - [ ] Create folder structure (`src/`, `models/`, `data/`, `templates/`, `static/`, `scripts/`, `deploy/`, `docs/`, `tests/`)
  - [ ] Create `requirements.txt` with all dependencies
  - [ ] Create `.env.default` with all configuration variables
  - [ ] Create `.gitignore` (exclude `venv/`, `.env`, `data/`, `models/training_data/`)
  - [ ] Create `app.py` entry point with Flask + SocketIO

- [ ] **1.2 Camera capture module**
  - [ ] Implement `src/hardware/camera.py` — Pi Camera and USB camera capture
  - [ ] Support configurable resolution and FPS (`CAMERA_RESOLUTION`, `CAMERA_FPS`)
  - [ ] Support camera index or RTSP URL (`CAMERA_SOURCE`)
  - [ ] Add second camera support (`CAMERA_2_ENABLED`, `CAMERA_2_SOURCE`)
  - [ ] Handle camera disconnection gracefully (auto-reconnect)

- [ ] **1.3 YOLOv8n model loader**
  - [ ] Implement `src/ml/model_loader.py` — load `.pt` model via ultralytics
  - [ ] Run inference on a frame, return detections (bbox, class, confidence)
  - [ ] Support model swapping (QC model ↔ PPE model)
  - [ ] Filter detections by confidence threshold
  - [ ] Write `scripts/download-models.sh` — download pre-trained models

- [ ] **1.4 Mock hardware**
  - [ ] Implement `src/hardware/mock_hardware.py`
  - [ ] Simulated camera: return sample frames with embedded defects/PPE
  - [ ] Virtual GPIO: log pin state changes to console
  - [ ] Auto-detect hardware: if camera not available, switch to mock

- [ ] **1.5 Mode manager**
  - [ ] Implement `src/inspection/mode_manager.py`
  - [ ] Support modes: `qc`, `ppe`, `both`
  - [ ] Route camera frames to correct pipeline(s)
  - [ ] Allow runtime mode switching (via API endpoint)

- [ ] **1.6 Database initialization**
  - [ ] Implement `src/services/db.py` — create SQLite tables
  - [ ] Tables: `inspections`, `spc_data`, `workers`, `daily_reports`, `settings`

- [ ] **1.7 Unit tests — Phase 1**
  - [ ] Test model loader with mock model
  - [ ] Test camera capture with mock frames
  - [ ] Test mode manager switching

## Phase 2 — QC Pipeline

- [ ] **2.1 QC defect detection**
  - [ ] Implement `src/inspection/qc_inspector.py`
  - [ ] Run QC model on camera frames
  - [ ] Classify defects into configurable categories
  - [ ] Log results to `inspections` table
  - [ ] Save snapshot images of detected defects

- [ ] **2.2 GPIO reject mechanism**
  - [ ] Implement reject trigger in `src/hardware/gpio_controller.py`
  - [ ] Activate servo/solenoid on `QC_REJECT_GPIO_PIN` when defect detected
  - [ ] Configurable rejection delay (travel time compensation)
  - [ ] Toggle via `QC_REJECT_ENABLED`

- [ ] **2.3 Barcode/QR correlation**
  - [ ] Implement `src/hardware/barcode_reader.py` using pyzbar
  - [ ] Detect barcode in camera frame before/after inspection
  - [ ] Link barcode to inspection result in database
  - [ ] Toggle via `QC_BARCODE_ENABLED`

- [ ] **2.4 SPC calculations**
  - [ ] Implement `src/services/spc_service.py`
  - [ ] Calculate X-bar and R-chart values per subgroup
  - [ ] Compute UCL, LCL, CL
  - [ ] Detect out-of-control conditions
  - [ ] Auto-halt line if defect rate > `QC_AUTO_HALT_DEFECT_RATE`
  - [ ] Toggle via `QC_SPC_ENABLED`

- [ ] **2.5 Unit tests — Phase 2**
  - [ ] Test QC inspector with mock detections
  - [ ] Test SPC calculations with known data
  - [ ] Test barcode correlation

## Phase 3 — PPE Pipeline

- [ ] **3.1 PPE detection**
  - [ ] Implement `src/inspection/ppe_inspector.py`
  - [ ] Detect PPE classes on persons
  - [ ] Compare against `PPE_REQUIRED_CLASSES`
  - [ ] Log compliance/violation to database

- [ ] **3.2 GPIO alarm**
  - [ ] Buzzer on `PPE_ALARM_GPIO_PIN` when non-compliant
  - [ ] LED traffic light: green (compliant) / red (violation)
  - [ ] Toggle via `PPE_ALARM_ENABLED`

- [ ] **3.3 Access barrier**
  - [ ] Servo-controlled barrier on `PPE_BARRIER_GPIO_PIN`
  - [ ] Gate opens only when all required PPE detected
  - [ ] Configurable open duration
  - [ ] Toggle via `PPE_BARRIER_ENABLED`

- [ ] **3.4 Time-based enforcement**
  - [ ] Only enforce during `PPE_ENFORCEMENT_START` to `PPE_ENFORCEMENT_END`
  - [ ] Outside hours: log but don't alarm

- [ ] **3.5 Worker face identification**
  - [ ] Implement `src/ml/face_recognizer.py`
  - [ ] Enroll workers (capture or upload face photo)
  - [ ] Match detected face against enrolled database
  - [ ] Log worker name with violation
  - [ ] Toggle via `PPE_FACE_ID_ENABLED`

- [ ] **3.6 Unit tests — Phase 3**
  - [ ] Test PPE inspector with mock detections
  - [ ] Test compliance check logic
  - [ ] Test time-based enforcement

## Phase 4 — Web Dashboard

- [ ] **4.1 Flask app + auth**
  - [ ] Set up Flask with Jinja2 templates
  - [ ] Implement `src/routes/auth.py` — login, logout, session
  - [ ] bcrypt password hashing
  - [ ] Rate limiting on login
  - [ ] Session expiry (24 hours)

- [ ] **4.2 Dashboard page**
  - [ ] `templates/dashboard.html` — live camera feed with detection overlays
  - [ ] Current mode indicator (QC / PPE / Both)
  - [ ] Real-time counters: inspected, defects, compliance rate
  - [ ] System info: CPU temp, memory, uptime

- [ ] **4.3 QC page**
  - [ ] `templates/qc.html` — QC-specific stats
  - [ ] Defect classification pie chart
  - [ ] Pareto chart (most common defects)
  - [ ] SPC X-bar and R-charts
  - [ ] Reject counter and line status

- [ ] **4.4 PPE page**
  - [ ] `templates/ppe.html` — PPE-specific stats
  - [ ] Compliance rate gauge
  - [ ] Violation log (table with images)
  - [ ] Zone status (if zones enabled)
  - [ ] Worker identification feed (if face ID enabled)

- [ ] **4.5 Settings page**
  - [ ] `templates/settings.html`
  - [ ] Mode toggle (QC / PPE / Both)
  - [ ] Zone configuration
  - [ ] Alert channel configuration
  - [ ] GPIO pin settings
  - [ ] Camera settings
  - [ ] Password change

- [ ] **4.6 Reports page**
  - [ ] `templates/reports.html`
  - [ ] Generate PDF/CSV reports on demand
  - [ ] View generated reports
  - [ ] Filter by date, mode, zone

- [ ] **4.7 Training page**
  - [ ] `templates/training.html`
  - [ ] Capture current frame as training image
  - [ ] Simple bounding box annotation tool
  - [ ] Export YOLO dataset
  - [ ] Trigger model retraining

- [ ] **4.8 WebSocket real-time feed**
  - [ ] SocketIO server pushing annotated frames
  - [ ] Client-side: draw bounding boxes + labels on canvas
  - [ ] Real-time counter updates

## Phase 5 — Advanced Features

- [ ] **5.1 Multi-zone inspection**
  - [ ] Implement `src/inspection/zone_manager.py`
  - [ ] Load zone config from `config/zones.json`
  - [ ] Apply zone-specific rules to detections
  - [ ] Toggle via `ZONES_ENABLED`

- [ ] **5.2 Multi-camera support**
  - [ ] Support up to 4 cameras
  - [ ] Assign cameras to modes/zones
  - [ ] Dashboard: camera selector dropdown

- [ ] **5.3 Night vision**
  - [ ] Support Pi NoIR Camera module
  - [ ] Auto-switch based on ambient light or time
  - [ ] Toggle via `NIGHT_VISION_ENABLED`

- [ ] **5.4 Alert channels**
  - [ ] Implement `src/services/alert_service.py`
  - [ ] Email alerts (SMTP)
  - [ ] Telegram bot alerts
  - [ ] Webhook (HTTP POST)
  - [ ] GPIO buzzer alerts
  - [ ] Per-event-type alert routing

- [ ] **5.5 OPC-UA export**
  - [ ] Implement `src/services/opcua_service.py`
  - [ ] OPC-UA server with inspection data nodes
  - [ ] Real-time: defect rate, line status, last result
  - [ ] Toggle via `OPCUA_ENABLED`

## Phase 6 — Deployment and Polish

- [ ] **6.1 Deploy script**
  - [ ] Write `deploy/deploy_to_pi.sh`
  - [ ] rsync project files
  - [ ] Create venv + install deps on Pi
  - [ ] Create `.env` from `.env.default` if not exists

- [ ] **6.2 systemd service**
  - [ ] Document systemd unit in README
  - [ ] Test auto-start on boot

- [ ] **6.3 Automated daily reports**
  - [ ] Implement scheduler for nightly report generation
  - [ ] Toggle via `REPORT_AUTO_DAILY`

- [ ] **6.4 Documentation**
  - [ ] Write `docs/threat_model.md`
  - [ ] Review README.md
  - [ ] Review TSD.md

- [ ] **6.5 End-to-end testing**
  - [ ] Test QC pipeline with mock camera → detection → reject → log → SPC
  - [ ] Test PPE pipeline with mock camera → detection → alarm → log
  - [ ] Test dual mode
  - [ ] Test dashboard WebSocket feed
  - [ ] Test report generation
