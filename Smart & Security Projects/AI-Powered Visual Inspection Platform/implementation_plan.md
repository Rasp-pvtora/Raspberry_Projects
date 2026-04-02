# Implementation Plan — AI-Powered Visual Inspection Platform

This document provides a phased, step-by-step implementation guide. Each phase focuses on a specific feature area. Complete all steps in order within each phase before moving to the next.

---

## Phase 1 — Core Inference and Camera (Foundation)

**Goal:** Camera captures frames, YOLOv8n runs inference, mode manager routes to correct pipeline.

- [ ] **Step 1.1** — Create project folder structure
  - [ ] Create all directories: `src/inspection/`, `src/hardware/`, `src/ml/`, `src/routes/`, `src/services/`, `models/`, `data/`, `templates/`, `static/css/`, `static/js/`, `scripts/`, `deploy/`, `docs/`, `tests/`
  - [ ] Create `requirements.txt` with pinned versions
  - [ ] Create `.env.default` with all variables documented
  - [ ] Create `.gitignore`
  - [ ] Verify: `pip install -r requirements.txt` succeeds

- [ ] **Step 1.2** — Implement camera capture
  - [ ] Create `src/hardware/camera.py`
  - [ ] Implement `CameraCapture` class: `open()`, `read_frame()`, `release()`
  - [ ] Support OpenCV `VideoCapture(index)` and `VideoCapture(rtsp_url)`
  - [ ] Add configurable resolution and FPS
  - [ ] Test: camera opens and returns frames (or mock frames on laptop)

- [ ] **Step 1.3** — Implement mock hardware
  - [ ] Create `src/hardware/mock_hardware.py`
  - [ ] `MockCamera`: returns sample images from a `tests/fixtures/` directory
  - [ ] `MockGPIO`: logs pin state changes to stdout
  - [ ] Auto-detection: try real hardware first, fall back to mock

- [ ] **Step 1.4** — Implement model loader
  - [ ] Create `src/ml/model_loader.py`
  - [ ] `ModelLoader.load(model_path)` → returns YOLO model object
  - [ ] `ModelLoader.infer(frame)` → returns list of `Detection(bbox, class, confidence)`
  - [ ] `ModelLoader.swap_model(new_path)` → hot-swap model file
  - [ ] Write `scripts/download-models.sh` → downloads YOLOv8n base weights
  - [ ] Test: load model, run inference on a test image, verify detections returned

- [ ] **Step 1.5** — Implement mode manager
  - [ ] Create `src/inspection/mode_manager.py`
  - [ ] Read `MODE` from env: `qc`, `ppe`, `both`
  - [ ] Route frames to QC pipeline, PPE pipeline, or both
  - [ ] Expose `switch_mode(new_mode)` for runtime switching
  - [ ] Test: switch modes, verify correct pipeline receives frames

- [ ] **Step 1.6** — Implement database
  - [ ] Create `src/services/db.py`
  - [ ] Initialize SQLite at `data/inspection.db`
  - [ ] Create tables: `inspections`, `spc_data`, `workers`, `daily_reports`, `settings`
  - [ ] Test: create tables, insert test row, query it back

- [ ] **Step 1.7** — Create Flask app entry point
  - [ ] Create `app.py` with Flask + SocketIO
  - [ ] Load `.env` with python-dotenv
  - [ ] Initialize camera, model loader, mode manager, database
  - [ ] Start background thread for inference loop
  - [ ] Test: `python app.py` starts without errors

- [ ] **Phase 1 checkpoint:** Camera captures → model infers → mode manager routes → database stores → app runs

---

## Phase 2 — Quality Control Pipeline

**Goal:** Detect product defects, classify them, reject defective items, track SPC.

- [ ] **Step 2.1** — Implement QC inspector
  - [ ] Create `src/inspection/qc_inspector.py`
  - [ ] `QCInspector.inspect(frame)` → run QC model, return defects
  - [ ] Map detection class IDs to `QC_DEFECT_CLASSES` names
  - [ ] Save defect snapshot image to `data/snapshots/`
  - [ ] Insert inspection record into `inspections` table
  - [ ] Test: pass mock frame with defect → verify detection + DB insert

- [ ] **Step 2.2** — Implement GPIO reject
  - [ ] Create `src/hardware/gpio_controller.py`
  - [ ] `GPIOController.activate_reject()` → pulse `QC_REJECT_GPIO_PIN` HIGH
  - [ ] Configurable pulse duration (ms)
  - [ ] Check `QC_REJECT_ENABLED` before activating
  - [ ] Test: defect detected → GPIO pin pulsed (or logged in mock mode)

- [ ] **Step 2.3** — Implement barcode reader
  - [ ] Create `src/hardware/barcode_reader.py`
  - [ ] Use pyzbar to detect barcodes in the camera frame
  - [ ] Return barcode value or None
  - [ ] Link barcode to inspection record
  - [ ] Check `QC_BARCODE_ENABLED`
  - [ ] Test: frame with barcode → barcode decoded → linked to inspection

- [ ] **Step 2.4** — Implement SPC service
  - [ ] Create `src/services/spc_service.py`
  - [ ] Collect defect counts per subgroup (`QC_SPC_SAMPLE_SIZE`)
  - [ ] Calculate X-bar, R-chart, UCL, LCL, CL
  - [ ] Detect out-of-control (point above UCL)
  - [ ] If defect rate > `QC_AUTO_HALT_DEFECT_RATE`: trigger halt alert
  - [ ] Store SPC data in `spc_data` table
  - [ ] Check `QC_SPC_ENABLED`
  - [ ] Test: feed known defect sequence → verify SPC values correct

- [ ] **Phase 2 checkpoint:** Frame → QC model → classify defect → reject GPIO → barcode link → SPC update → DB log

---

## Phase 3 — PPE Detection Pipeline

**Goal:** Detect safety gear, enforce compliance, alarm on violations.

- [ ] **Step 3.1** — Implement PPE inspector
  - [ ] Create `src/inspection/ppe_inspector.py`
  - [ ] `PPEInspector.inspect(frame)` → run PPE model, return detections
  - [ ] Compare detected PPE classes against `PPE_REQUIRED_CLASSES`
  - [ ] Return compliance status: `compliant` or `violation` + list of missing PPE
  - [ ] Insert into `inspections` table
  - [ ] Test: mock frame with missing hardhat → violation detected

- [ ] **Step 3.2** — Implement GPIO alarm + barrier
  - [ ] Buzzer on `PPE_ALARM_GPIO_PIN` when violation detected
  - [ ] LED traffic light: green = compliant, red = violation
  - [ ] Barrier servo on `PPE_BARRIER_GPIO_PIN`: open on compliance, closed otherwise
  - [ ] Check `PPE_ALARM_ENABLED`, `PPE_BARRIER_ENABLED`
  - [ ] Test: violation → buzzer fires + barrier stays closed

- [ ] **Step 3.3** — Implement time-based enforcement
  - [ ] Parse `PPE_ENFORCEMENT_START` and `PPE_ENFORCEMENT_END`
  - [ ] During hours: enforce (alarm + barrier)
  - [ ] Outside hours: log only, no alarm
  - [ ] Test: set enforcement window, verify alarm only during window

- [ ] **Step 3.4** — Implement worker face identification
  - [ ] Create `src/ml/face_recognizer.py`
  - [ ] `enroll_worker(name, face_image)` → compute 128-d encoding, store in `workers` table
  - [ ] `identify_worker(frame)` → match face against enrolled encodings
  - [ ] Link identified worker to violation log
  - [ ] Check `PPE_FACE_ID_ENABLED`
  - [ ] Test: enroll test face → run frame with that face → worker identified

- [ ] **Phase 3 checkpoint:** Frame → PPE model → compliance check → alarm/barrier → face ID → DB log

---

## Phase 4 — Web Dashboard

**Goal:** Real-time web interface with live feed, charts, mode control.

- [ ] **Step 4.1** — Authentication
  - [ ] Create `src/routes/auth.py` — login(), logout()
  - [ ] bcrypt hash verification
  - [ ] Rate limiting: track IP attempts, block after 10 in 15 min
  - [ ] Session cookie with `SESSION_SECRET`
  - [ ] Create `templates/login.html`
  - [ ] Test: login with correct/incorrect credentials, rate limit test

- [ ] **Step 4.2** — Layout and navigation
  - [ ] Create `templates/layout.html` — sidebar with links to all pages
  - [ ] Create `static/css/style.css` — dark theme
  - [ ] Responsive sidebar for mobile
  - [ ] Test: pages render with layout

- [ ] **Step 4.3** — Dashboard page (live feed)
  - [ ] Create `templates/dashboard.html`
  - [ ] WebSocket connection for live annotated frames
  - [ ] Create `static/js/dashboard.js` — draw bounding boxes on canvas
  - [ ] Mode indicator, real-time counters
  - [ ] Test: frames appear in browser with detection overlays

- [ ] **Step 4.4** — QC page
  - [ ] Create `templates/qc.html`
  - [ ] Create `static/js/spc.js` — Chart.js SPC charts
  - [ ] Defect classification pie chart
  - [ ] Pareto chart
  - [ ] Reject counter, line status
  - [ ] Test: charts render with data from DB

- [ ] **Step 4.5** — PPE page
  - [ ] Create `templates/ppe.html`
  - [ ] Compliance rate gauge
  - [ ] Violation log table with thumbnails
  - [ ] Zone status panel
  - [ ] Test: compliance data displays correctly

- [ ] **Step 4.6** — Settings page
  - [ ] Create `templates/settings.html`
  - [ ] Mode toggle (QC / PPE / Both) with runtime switch
  - [ ] All `.env` toggleable settings editable
  - [ ] Password change form
  - [ ] Test: change mode from dashboard, verify pipeline switches

- [ ] **Step 4.7** — Reports page
  - [ ] Create `templates/reports.html`
  - [ ] Implement `src/services/report_service.py` — PDF/CSV generation
  - [ ] Generate button, date filter, download links
  - [ ] Test: generate report, verify PDF content

- [ ] **Step 4.8** — Training page
  - [ ] Create `templates/training.html`
  - [ ] Capture frame button → save to training directory
  - [ ] Basic bounding box annotation (canvas click-drag)
  - [ ] Export YOLO dataset format
  - [ ] Test: capture + label + export workflow

- [ ] **Phase 4 checkpoint:** All pages render, live feed works, mode switchable, reports generate

---

## Phase 5 — Advanced Features

**Goal:** Multi-zone, multi-camera, night vision, alerts, OPC-UA.

- [ ] **Step 5.1** — Multi-zone inspection
  - [ ] Create `src/inspection/zone_manager.py`
  - [ ] Load `config/zones.json`
  - [ ] Apply per-zone detection rules
  - [ ] Dashboard: zone selector, per-zone stats
  - [ ] Test: 2 zones with different rules → correct enforcement per zone

- [ ] **Step 5.2** — Multi-camera
  - [ ] Support up to 4 cameras in camera module
  - [ ] Assign cameras to zones/modes in config
  - [ ] Dashboard: camera tabs/dropdown
  - [ ] Test: 2 cameras active, correct feed per tab

- [ ] **Step 5.3** — Night vision
  - [ ] Support Pi NoIR camera detection
  - [ ] IR LED GPIO control (on/off based on ambient light)
  - [ ] Dashboard toggle
  - [ ] Test: toggle night vision, verify IR activation

- [ ] **Step 5.4** — Alert channels
  - [ ] Create `src/services/alert_service.py`
  - [ ] Email via SMTP (check `ALERT_EMAIL_ENABLED`)
  - [ ] Telegram via Bot API (check `ALERT_TELEGRAM_ENABLED`)
  - [ ] Webhook HTTP POST (check `ALERT_WEBHOOK_ENABLED`)
  - [ ] Settings page: test alert button per channel
  - [ ] Test: trigger alert, verify delivery via each channel

- [ ] **Step 5.5** — OPC-UA server
  - [ ] Create `src/services/opcua_service.py`
  - [ ] Start OPC-UA server on `OPCUA_PORT`
  - [ ] Expose nodes: defect_rate, line_status, last_inspection
  - [ ] Check `OPCUA_ENABLED`
  - [ ] Test: connect OPC-UA client, read nodes

- [ ] **Phase 5 checkpoint:** Zones work, multi-cam works, alerts fire, OPC-UA serves data

---

## Phase 6 — Deployment and Polish

**Goal:** Production-ready deployment, automated reports, documentation.

- [ ] **Step 6.1** — Deploy script
  - [ ] Write `deploy/deploy_to_pi.sh`
  - [ ] rsync with correct excludes
  - [ ] Remote venv creation + pip install
  - [ ] Create `.env` from `.env.default` if missing
  - [ ] Test: deploy to Pi, verify app starts

- [ ] **Step 6.2** — systemd service
  - [ ] Create service unit file (documented in README)
  - [ ] Enable + start service
  - [ ] Test: reboot Pi → service auto-starts

- [ ] **Step 6.3** — Automated daily reports
  - [ ] Implement scheduled report generation (midnight)
  - [ ] Check `REPORT_AUTO_DAILY`
  - [ ] Test: simulate midnight trigger, verify report generated

- [ ] **Step 6.4** — Documentation
  - [ ] Write `docs/threat_model.md`
  - [ ] Final review of README.md, TSD.md, task.md
  - [ ] Verify all `.env` variables documented

- [ ] **Step 6.5** — End-to-end testing
  - [ ] QC full pipeline: camera → detect → reject → SPC → report
  - [ ] PPE full pipeline: camera → detect → alarm → barrier → face ID → report
  - [ ] Dual mode: both pipelines simultaneously
  - [ ] Dashboard: all pages, real-time feed, mode switching
  - [ ] Deploy + systemd lifecycle test

- [ ] **Phase 6 checkpoint:** App deployed on Pi, auto-starts, reports generate, all docs complete
