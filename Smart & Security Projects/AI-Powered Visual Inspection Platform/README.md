# AI-Powered Visual Inspection Platform

A modular, camera-based real-time inspection system for Raspberry Pi with two switchable operational modes: **Quality Control (QC)** for detecting product defects on a conveyor line, and **PPE Detection** for enforcing safety gear compliance (hard hats, high-vis vests, goggles) at work zone entry points. Both modes share the same YOLOv8n inference pipeline and can run individually or simultaneously. Includes a web dashboard for live inspection feed, defect classification, statistical process control (SPC), compliance reporting, and GPIO-driven reject/alert mechanisms.

🪙 **Donations are Welcome!**
If you find this project helpful, you can support my work with a small donation.
₿ Bitcoin donation: `bc1q...`

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Budget](#budget)
4. [Libraries and dependencies](#libraries-and-dependencies)
5. [Quickstart — Laptop (development)](#quickstart--laptop-development)
6. [Environment configuration (.env)](#environment-configuration-env)
7. [System overview — Dual-mode architecture](#system-overview--dual-mode-architecture)
8. [Mode 1 — Quality Control (QC)](#mode-1--quality-control-qc)
9. [Mode 2 — PPE Detection](#mode-2--ppe-detection)
10. [Feature — Defect classification](#feature--defect-classification)
11. [Feature — Multi-zone inspection](#feature--multi-zone-inspection)
12. [Feature — GPIO reject mechanism (QC)](#feature--gpio-reject-mechanism-qc)
13. [Feature — Access gate integration (PPE)](#feature--access-gate-integration-ppe)
14. [Feature — Statistical Process Control (SPC)](#feature--statistical-process-control-spc)
15. [Feature — Compliance reporting](#feature--compliance-reporting)
16. [Feature — Worker identification (PPE)](#feature--worker-identification-ppe)
17. [Feature — Multi-camera support](#feature--multi-camera-support)
18. [Feature — Night vision](#feature--night-vision)
19. [Feature — Training pipeline](#feature--training-pipeline)
20. [Feature — Barcode/QR correlation (QC)](#feature--barcodeqr-correlation-qc)
21. [Feature — OPC-UA export](#feature--opc-ua-export)
22. [Feature — Web dashboard](#feature--web-dashboard)
23. [Authentication](#authentication)
24. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
25. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
26. [Security notes](#security-notes)
27. [Troubleshooting](#troubleshooting)
28. [Where to next](#where-to-next)

---

## Project structure

```
.
├── app.py                     ← Python entry point (Flask + inference loop)
├── requirements.txt           ← Python dependencies
├── .env.default               ← Environment variable template (copy to .env)
├── .gitignore                 ← Git ignore rules
├── src/
│   ├── inspection/
│   │   ├── qc_inspector.py    ← Quality Control defect detection
│   │   ├── ppe_inspector.py   ← PPE safety gear detection
│   │   ├── mode_manager.py    ← Dual-mode coordinator (QC, PPE, both)
│   │   └── zone_manager.py    ← Multi-zone inspection configuration
│   ├── hardware/
│   │   ├── camera.py          ← Camera capture (Pi Camera, USB, multi-cam)
│   │   ├── gpio_controller.py ← GPIO: reject servo, barrier, buzzer, LEDs
│   │   ├── barcode_reader.py  ← Barcode/QR code detection (pyzbar)
│   │   └── mock_hardware.py   ← Mock hardware for development
│   ├── ml/
│   │   ├── model_loader.py    ← YOLOv8n model loading and inference
│   │   ├── trainer.py         ← On-device training pipeline
│   │   └── face_recognizer.py ← Worker identification (PPE mode)
│   ├── routes/
│   │   ├── auth.py            ← Login / logout routes
│   │   ├── dashboard.py       ← Dashboard API
│   │   ├── inspection.py      ← Inspection data and live feed API
│   │   ├── reports.py         ← Compliance and SPC report API
│   │   ├── training.py        ← Training pipeline API
│   │   └── settings.py        ← Settings API
│   └── services/
│       ├── spc_service.py     ← Statistical Process Control calculations
│       ├── report_service.py  ← PDF/CSV report generation
│       ├── alert_service.py   ← Alert channels (email, Telegram, webhook, GPIO)
│       ├── opcua_service.py   ← OPC-UA data export
│       ├── db.py              ← SQLite database initialization
│       └── system_service.py  ← System info (temp, memory, disk)
├── models/
│   ├── qc_defect.pt           ← QC defect detection model (YOLOv8n)
│   ├── ppe_safety.pt          ← PPE detection model (YOLOv8n)
│   └── training_data/         ← Captured training images
├── data/
│   └── inspection.db          ← SQLite database for inspection data
├── templates/                 ← Jinja2 HTML templates
│   ├── layout.html            ← Base layout with sidebar navigation
│   ├── login.html             ← Login page
│   ├── dashboard.html         ← Live inspection feed + stats
│   ├── qc.html                ← QC-specific dashboard
│   ├── ppe.html               ← PPE-specific dashboard
│   ├── reports.html           ← SPC charts and compliance reports
│   ├── training.html          ← Model training interface
│   └── settings.html          ← Mode selection, zones, alerts
├── static/
│   ├── css/style.css          ← Dark theme stylesheet
│   └── js/
│       ├── main.js            ← WebSocket client for real-time feed
│       ├── dashboard.js       ← Live feed + detection overlay
│       ├── spc.js             ← SPC chart logic (Chart.js)
│       └── training.js        ← Training interface logic
├── scripts/
│   ├── setup-camera.sh        ← Camera configuration
│   ├── download-models.sh     ← Download pre-trained YOLOv8n models
│   └── setup-opcua.sh         ← OPC-UA server setup
├── deploy/
│   └── deploy_to_pi.sh        ← rsync-based deploy script
├── docs/
│   └── threat_model.md        ← Threat model and mitigations
├── tests/
├── README.md
├── TSD.md
├── task.md
└── implementation_plan.md
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB+) / Pi 5 | Yes | Pi 5 recommended for dual-mode; 4 GB minimum |
| microSD card (32 GB+) | Yes | For OS, models, and inspection data |
| Pi Camera Module v3 / HQ Camera | Yes | HQ Camera recommended for QC close-up inspection |
| C/CS-mount lens | QC mode | Close-up lens for small part inspection |
| Power supply (official) | Yes | 5V 3A for Pi 4, 5V 5A for Pi 5 |
| Ethernet or WiFi | Yes | For dashboard access |

### QC Mode hardware

| Component | Required | Notes |
|---|---|---|
| Servo motor (SG90 / MG996R) | Optional | Reject mechanism to push defective items |
| Conveyor belt motor + driver | Optional | For automated inspection line |
| LED ring light | Recommended | Consistent illumination for inspection |
| Barcode scanner (camera-based) | Optional | Uses pyzbar on the same camera |

### PPE Mode hardware

| Component | Required | Notes |
|---|---|---|
| USB camera (wide-angle) | Optional | Wide FOV for entry point monitoring |
| Buzzer module | Optional | Audio alarm for non-compliance |
| LED traffic light module | Optional | Red/green entry indicator |
| Servo / barrier motor | Optional | GPIO-controlled access barrier |
| Pi NoIR Camera + IR LEDs | Optional | Night vision capability |

---

## Budget

| Item | Estimated Price (USD) | Notes |
|---|---|---|
| Pi HQ Camera Module | $50 | 12.3 MP, C/CS-mount for QC mode |
| C-mount 16mm lens | $25 | Close-up inspection lens |
| **Alternative:** Pi Camera Module v3 | $25 – $30 | Standard camera for PPE mode |
| SG90 servo (reject arm) | $3 | QC reject mechanism |
| Buzzer module | $2 | PPE alarm |
| LED traffic light module | $5 | Red/green entry indicator |
| LED ring light | $8 – $12 | Consistent illumination for QC |
| Conveyor belt + motor kit | $25 – $40 | Optional: motorized inspection line |
| **Optional:** Pi NoIR Camera + IR LEDs | $30 – $35 | Night vision for PPE |
| **Optional:** Second USB camera | $15 – $25 | Multi-camera setup |
| **Total (QC mode minimum)** | **~$80 – $90** | HQ Camera + lens + ring light + servo |
| **Total (PPE mode minimum)** | **~$30 – $40** | Pi Camera v3 + buzzer + LED |
| **Total (dual mode)** | **~$110 – $135** | Both cameras + all peripherals |

> **Note:** The Raspberry Pi, microSD card, and power supply are not included above.

---

## Libraries and dependencies

### Python dependencies

| Library | Version | Purpose |
|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | ^3.1.0 | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | ^5.4.0 | WebSocket for real-time video feed |
| [Jinja2](https://jinja.palletsprojects.com/) | ^3.1.4 | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ^1.0.1 | Load environment variables from `.env` |
| [ultralytics](https://docs.ultralytics.com/) | ^8.3.0 | YOLOv8 object detection framework |
| [opencv-python-headless](https://pypi.org/project/opencv-python-headless/) | ^4.10.0 | Image processing and camera capture |
| [numpy](https://numpy.org/) | ^1.26.0 | Numerical operations |
| [Pillow](https://python-pillow.org/) | ^10.4.0 | Image manipulation |
| [pyzbar](https://pypi.org/project/pyzbar/) | ^0.1.9 | Barcode / QR code detection |
| [face-recognition](https://pypi.org/project/face-recognition/) | ^1.3.0 | Worker identification (PPE mode) |
| [reportlab](https://pypi.org/project/reportlab/) | ^4.2.0 | PDF report generation |
| [bcrypt](https://pypi.org/project/bcrypt/) | ^4.2.0 | Password hashing |
| [requests](https://requests.readthedocs.io/) | ^2.32.0 | Webhook and Telegram alerts |
| [opcua](https://pypi.org/project/opcua/) | ^0.98.0 | OPC-UA server (optional) |
| [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) | ^0.7.1 | GPIO control |
| [chart.js](https://www.chartjs.org/) | ^4.4.7 | Dashboard charts (CDN) |

### Dev dependencies

| Library | Version | Purpose |
|---|---|---|
| [pytest](https://docs.pytest.org/) | ^8.3.0 | Testing framework |

### System packages (Pi)

| Package | Purpose |
|---|---|
| `libzbar0` | Barcode/QR code library (pyzbar dependency) |
| `libopencv-dev` | OpenCV system dependencies |
| `Python 3.11+` | Python runtime |

---

## Quickstart — Laptop (development)

**1. Clone and navigate**

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/AI-Powered Visual Inspection Platform"
```

**2. Create `.env` from template**

```bash
cp .env.default .env    # Linux/macOS
copy .env.default .env  # Windows
```

**3. Virtual environment and dependencies**

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

**4. Download pre-trained models**

```bash
bash scripts/download-models.sh
```

**5. Start the server**

```bash
python app.py
```

**6. Open dashboard** → `http://localhost:5000`

> On a laptop, the system runs in mock mode with simulated camera frames and GPIO.

---

## Environment configuration (.env)

Copy `.env.default` to `.env`. **Never commit `.env` to git.**

### General

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Web server port |
| `HOST` | `0.0.0.0` | Listen address |
| `SESSION_SECRET` | `CHANGE_ME...` | Session encryption key |
| `ADMIN_USERNAME` | `admin` | Dashboard login |
| `ADMIN_PASSWORD` | `changeme` | Dashboard password |

### Mode control

| Variable | Default | Description |
|---|---|---|
| `MODE` | `both` | Operating mode: `qc`, `ppe`, `both` |
| `QC_ENABLED` | `true` | Enable Quality Control mode |
| `PPE_ENABLED` | `true` | Enable PPE Detection mode |

### Camera

| Variable | Default | Description |
|---|---|---|
| `CAMERA_SOURCE` | `0` | Camera index or RTSP URL |
| `CAMERA_RESOLUTION` | `640x480` | Capture resolution |
| `CAMERA_FPS` | `15` | Frames per second |
| `CAMERA_2_ENABLED` | `false` | Enable second camera |
| `CAMERA_2_SOURCE` | `1` | Second camera index |
| `NIGHT_VISION_ENABLED` | `false` | Enable IR/NoIR camera mode |

### QC settings

| Variable | Default | Description |
|---|---|---|
| `QC_MODEL_PATH` | `./models/qc_defect.pt` | YOLOv8 QC model path |
| `QC_CONFIDENCE_THRESHOLD` | `0.5` | Min detection confidence (0.0–1.0) |
| `QC_DEFECT_CLASSES` | `scratch,dent,discoloration,misalignment,foreign_object` | Defect categories |
| `QC_REJECT_ENABLED` | `true` | Enable GPIO reject mechanism |
| `QC_REJECT_GPIO_PIN` | `17` | Servo/solenoid reject pin |
| `QC_BARCODE_ENABLED` | `false` | Enable barcode/QR correlation |
| `QC_SPC_ENABLED` | `true` | Enable Statistical Process Control |
| `QC_SPC_SAMPLE_SIZE` | `25` | SPC subgroup sample size |
| `QC_AUTO_HALT_DEFECT_RATE` | `0.05` | Auto-halt if defect rate exceeds 5% |

### PPE settings

| Variable | Default | Description |
|---|---|---|
| `PPE_MODEL_PATH` | `./models/ppe_safety.pt` | YOLOv8 PPE model path |
| `PPE_CONFIDENCE_THRESHOLD` | `0.6` | Min detection confidence |
| `PPE_CLASSES` | `hardhat,vest,goggles,gloves` | PPE classes to detect |
| `PPE_REQUIRED_CLASSES` | `hardhat,vest` | Required PPE for entry |
| `PPE_ALARM_ENABLED` | `true` | Enable buzzer on non-compliance |
| `PPE_ALARM_GPIO_PIN` | `27` | Buzzer GPIO pin |
| `PPE_BARRIER_ENABLED` | `false` | Enable access gate barrier |
| `PPE_BARRIER_GPIO_PIN` | `22` | Barrier servo GPIO pin |
| `PPE_FACE_ID_ENABLED` | `false` | Enable worker identification |
| `PPE_ENFORCEMENT_START` | `07:00` | Enforcement start time |
| `PPE_ENFORCEMENT_END` | `18:00` | Enforcement end time |

### Zones

| Variable | Default | Description |
|---|---|---|
| `ZONES_ENABLED` | `false` | Enable multi-zone inspection |
| `ZONE_CONFIG_PATH` | `./config/zones.json` | Zone configuration file |

### Alerts

| Variable | Default | Description |
|---|---|---|
| `ALERT_EMAIL_ENABLED` | `false` | Enable email alerts |
| `ALERT_TELEGRAM_ENABLED` | `false` | Enable Telegram alerts |
| `ALERT_WEBHOOK_ENABLED` | `false` | Enable webhook alerts |
| `ALERT_WEBHOOK_URL` | `` | Webhook endpoint URL |

### OPC-UA

| Variable | Default | Description |
|---|---|---|
| `OPCUA_ENABLED` | `false` | Enable OPC-UA server |
| `OPCUA_PORT` | `4840` | OPC-UA server port |

### Training

| Variable | Default | Description |
|---|---|---|
| `TRAINING_CAPTURE_ENABLED` | `false` | Enable training image capture |
| `TRAINING_DATA_DIR` | `./models/training_data` | Training image directory |

### Reports

| Variable | Default | Description |
|---|---|---|
| `REPORT_AUTO_DAILY` | `true` | Generate daily reports automatically |
| `REPORT_OUTPUT_DIR` | `./data/reports` | Report output directory |

---

## System overview — Dual-mode architecture

This platform runs **two detection modes on a shared inference pipeline**:

| Mode | Camera | Model | Detects | GPIO Action |
|---|---|---|---|---|
| **QC** (Quality Control) | Close-up (HQ Camera) | `qc_defect.pt` | Product defects | Reject servo |
| **PPE** (Safety Compliance) | Wide-angle (entry gate) | `ppe_safety.pt` | Safety gear | Buzzer + barrier |

**Mode selection (from dashboard or `.env`):**

- `MODE=qc` → only QC mode runs.
- `MODE=ppe` → only PPE mode runs.
- `MODE=both` → both modes run simultaneously (requires 2 cameras or alternating frames).

**Why dual mode?** Both share:
- The same YOLOv8n inference engine.
- The same web dashboard framework.
- The same GPIO abstraction layer.
- The same alert system (email, Telegram, webhook).
- The same reporting engine.

The only differences are the trained model weights and the GPIO actions triggered on detection.

**Processing pipeline:**

```
Camera frame → YOLOv8n inference → Detections
    → QC path: classify defect category → log → GPIO reject
    → PPE path: check required gear → log → GPIO alarm/barrier
    → Dashboard: annotated frame via WebSocket
    → Database: SQLite log for SPC/reports
```

---

## Mode 1 — Quality Control (QC)

Inspects products on a conveyor line for visual defects.

- Camera captures each item as it passes the inspection zone.
- YOLOv8n detects and classifies defect types.
- If defect detected → GPIO activates reject mechanism (servo arm pushes item off the belt).
- All results logged: timestamp, product barcode (if enabled), defect class, confidence, image.
- SPC charts track defect rates over time. Auto-halt if rate exceeds threshold.

**Detection classes (configurable):**
- Scratch
- Dent
- Discoloration
- Misalignment
- Foreign object

---

## Mode 2 — PPE Detection

Monitors workers at entry points for required safety equipment.

- Camera at entry gate captures workers as they approach.
- YOLOv8n detects safety gear: hard hat, high-vis vest, safety goggles, gloves.
- If required PPE is missing → buzzer alarm + log incident.
- If barrier enabled → gate stays closed until all required PPE is detected.
- Optional: face recognition identifies the specific worker for compliance tracking.

**PPE classes (configurable):**
- Hard hat
- High-vis vest
- Safety goggles
- Gloves

**Zone-based rules:** Different zones can require different PPE combinations. Edit `config/zones.json`:
```json
{
  "zones": [
    { "name": "Warehouse", "camera": 0, "required": ["hardhat", "vest"] },
    { "name": "Lab", "camera": 1, "required": ["goggles", "gloves"] }
  ]
}
```

---

## Feature — Defect classification

Not just pass/fail — the system categorizes defects by type.

- Each defect is classified into its category (scratch, dent, etc.).
- Dashboard shows defect distribution pie chart.
- Pareto chart: which defect type is most common.
- Drill down by time period, product batch, or production line.
- Enable/disable: `QC_ENABLED=true` + `QC_DEFECT_CLASSES` in `.env`.

---

## Feature — Multi-zone inspection

Define multiple inspection regions within a single camera frame or across multiple cameras.

- Each zone has its own detection rules and PPE requirements.
- Zones are defined as rectangular ROIs (Region of Interest) on the camera frame.
- Configure via `config/zones.json` or the dashboard Settings page.
- Enable/disable: `ZONES_ENABLED=true` in `.env`.

---

## Feature — GPIO reject mechanism (QC)

Automatic physical rejection of defective items.

- When a defect is detected above the confidence threshold, a GPIO pin triggers.
- Supported mechanisms: servo arm (push), solenoid (kick), pneumatic valve.
- Configurable delay: time between detection and rejection (accounts for item travel distance).
- Enable/disable: `QC_REJECT_ENABLED=true` in `.env`.

---

## Feature — Access gate integration (PPE)

Physical access control based on PPE compliance.

- GPIO-controlled barrier: gate opens only when required PPE is detected.
- Traffic light: green = compliant, red = non-compliant.
- Buzzer: audible alert on non-compliance.
- Configurable timeout: gate stays open for X seconds after compliance detected.
- Enable/disable: `PPE_BARRIER_ENABLED=true` in `.env`.

---

## Feature — Statistical Process Control (SPC)

Real-time SPC charts for QC mode on the dashboard.

- **X-bar chart:** Average defect rate per subgroup (sample of 25 items).
- **R-chart:** Range of defect rate variation.
- **Control limits:** Upper Control Limit (UCL), Lower Control Limit (LCL), Center Line (CL).
- **Out-of-control alerts:** If a data point exceeds UCL → alert triggered.
- **Auto-halt:** If defect rate exceeds `QC_AUTO_HALT_DEFECT_RATE` → halt the line (GPIO).
- Enable/disable: `QC_SPC_ENABLED=true` in `.env`.

---

## Feature — Compliance reporting

Automated daily, weekly, and monthly reports.

- **QC reports:** Defect rate, defect distribution, SPC summary, items inspected, items rejected.
- **PPE reports:** Total entries, compliant %, violations by zone, repeat offenders.
- **Export formats:** PDF (ReportLab) and CSV.
- **Auto-generation:** Daily report at midnight if `REPORT_AUTO_DAILY=true`.
- **Manual:** Generate from dashboard Reports page.

---

## Feature — Worker identification (PPE)

Combine PPE detection with face recognition.

- Uses `face_recognition` library to identify workers.
- Enroll workers from the dashboard (capture face from camera or upload photo).
- Log which specific worker was non-compliant.
- Track repeat offenders across shifts.
- Enable/disable: `PPE_FACE_ID_ENABLED=true` in `.env`.

---

## Feature — Multi-camera support

One Pi manages up to 4 cameras.

- **QC mode:** High-angle + side-angle cameras for multi-perspective inspection.
- **PPE mode:** Multiple entry points monitored simultaneously.
- **Dual mode:** Camera 0 for QC, Camera 1 for PPE.
- Enable/disable: `CAMERA_2_ENABLED=true` in `.env`.

---

## Feature — Night vision

24/7 monitoring with Pi NoIR Camera + IR illumination.

- Pi NoIR Camera module removes the IR filter.
- IR LED ring provides illumination invisible to the human eye.
- Auto-switch: detect ambient light level, toggle IR mode.
- Primarily for PPE mode (outdoor/low-light entry points).
- Enable/disable: `NIGHT_VISION_ENABLED=true` in `.env`.

---

## Feature — Training pipeline

Capture training images from the Pi camera and retrain the model.

- **Capture mode:** Dashboard button saves the current frame as a training image.
- **Labeling:** Simple web-based bounding box annotation tool in the dashboard.
- **Export:** Generate YOLO-format dataset from labeled images.
- **Retrain:** Trigger model retraining from the dashboard (runs on-device for small datasets, or export for external training).
- Enable/disable: `TRAINING_CAPTURE_ENABLED=true` in `.env`.

---

## Feature — Barcode/QR correlation (QC)

Link inspection results to product identifiers.

- Uses `pyzbar` to detect barcodes/QR codes from the same camera frame.
- Each inspection result is tagged with the product's barcode.
- Query: "Show me all defects for batch XYZ-123."
- Enable/disable: `QC_BARCODE_ENABLED=true` in `.env`.

---

## Feature — OPC-UA export

Send inspection data to factory MES/SCADA systems.

- The Pi runs an OPC-UA server with inspection data nodes.
- Real-time nodes: current defect rate, last inspection result, line status (running/halted).
- Historical data: accessible via OPC-UA Historical Access.
- Compatible with industrial SCADA systems (Siemens, Rockwell, Schneider).
- Enable/disable: `OPCUA_ENABLED=true` in `.env`.

---

## Feature — Web dashboard

| Page | Description |
|---|---|
| **Dashboard** | Live camera feed with detection overlays, current mode indicator, defect/compliance counters |
| **QC** | QC-specific: defect classification, SPC charts, reject counter, line status |
| **PPE** | PPE-specific: compliance rate, violation log, worker ID feed, zone status |
| **Reports** | Generate/view PDF and CSV reports: daily/weekly/monthly |
| **Training** | Capture images, label, export, retrain models |
| **Settings** | Mode selection (QC/PPE/both), zone config, alert channels, GPIO pins, camera settings |

**Real-time features:**
- Annotated video feed via WebSocket (bounding boxes + labels + confidence).
- Live counters: items inspected, defects found, compliance rate.
- Mode toggle: switch between QC, PPE, or both from the dashboard.

---

## Authentication

- Session-based login with bcrypt password hashing.
- Rate limiting: 10 attempts per 15 minutes per IP.
- Session expiry: 24 hours.
- Password changeable from Settings page.

---

## How to deploy to Raspberry Pi

SSH config at `~/.ssh/config`:

```
Host rasp-pi
    HostName 192.168.216.90
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

**Deploy script:**

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/VisualInspection
```

**Manual:**

```bash
rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' --exclude='data/' --exclude='models/training_data/' \
  ./ rasp-pi:/home/pi/Projects/VisualInspection/
```

---

## How to run on the Raspberry Pi

```bash
ssh rasp-pi
cd /home/pi/Projects/VisualInspection
nano .env   # Set SESSION_SECRET, ADMIN_PASSWORD, MODE
sudo bash scripts/setup-camera.sh
bash scripts/download-models.sh
source venv/bin/activate
python app.py
```

Access: `http://192.168.216.90:5000`

**systemd service:**

```ini
[Unit]
Description=Visual Inspection Platform
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/VisualInspection
ExecStart=/home/pi/Projects/VisualInspection/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

---

## Security notes

- Change the default password immediately.
- Generate a strong `SESSION_SECRET`: `python -c "import secrets; print(secrets.token_hex(32))"`
- `.env` contains sensitive data — never commit. Protect: `chmod 600 .env`
- Face recognition data (enrolled workers) is stored locally. Handle according to privacy regulations.
- OPC-UA port should be firewalled if exposed to external networks.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Camera not detected | `ls /dev/video*`. Enable camera: `sudo raspi-config` → Interface → Camera. |
| Low FPS | Reduce resolution: `CAMERA_RESOLUTION=320x240`. Use Pi 5 for better performance. |
| Model not loading | Run `bash scripts/download-models.sh`. Check model path in `.env`. |
| False detections | Increase confidence threshold: `QC_CONFIDENCE_THRESHOLD=0.7`. |
| GPIO not working | Add `pi` to gpio group: `sudo usermod -aG gpio pi`. Check pin numbers. |
| Barcode not reading | Ensure `libzbar0` installed: `sudo apt install libzbar0`. |
| Night vision too dark | Increase IR LED count or move closer. Check NoIR camera is installed (not standard). |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification.
- See [task.md](task.md) for the engineering checklist.
- See [implementation_plan.md](implementation_plan.md) for the phased implementation guide.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model.
