# Private Auto Parking AI-Monitoring

An AI-driven parking monitoring system using Raspberry Pi cameras for real-time vehicle detection, occupancy tracking, license plate recognition, and violation detection. Features an interactive parking map, entry/exit gate integration via GPIO, multi-camera support, and a real-time web dashboard. A comprehensive solution for managing private parking spaces.

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
7. [Detection pipeline overview](#detection-pipeline-overview)
8. [Feature 1 — Vehicle detection (YOLOv11n)](#feature-1--vehicle-detection-yolov11n)
9. [Feature 2 — Parking occupancy tracking](#feature-2--parking-occupancy-tracking)
10. [Feature 3 — License plate recognition (LPR)](#feature-3--license-plate-recognition-lpr)
11. [Feature 4 — Parking map visualization](#feature-4--parking-map-visualization)
12. [Feature 5 — Entry/exit gate integration](#feature-5--entryexit-gate-integration)
13. [Feature 6 — Violation detection](#feature-6--violation-detection)
14. [Feature 7 — Multi-camera support](#feature-7--multi-camera-support)
15. [Feature 8 — Analytics dashboard](#feature-8--analytics-dashboard)
16. [Feature 9 — Web dashboard](#feature-9--web-dashboard)
17. [Notifications](#notifications)
18. [MQTT / IoT integration](#mqtt--iot-integration)
19. [Authentication](#authentication)
20. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
21. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
22. [Real-world applications](#real-world-applications)
23. [Security notes](#security-notes)
24. [Troubleshooting](#troubleshooting)
25. [Where to next](#where-to-next)

---

## Project structure

```
.
├── app.py                     ← Python entry point (Flask + WebSocket)
├── requirements.txt           ← Python dependencies
├── .env.default               ← Environment variable template (copy to .env)
├── .gitignore                 ← Git ignore rules
├── src/
│   ├── detection/
│   │   ├── vehicle_detector.py ← YOLOv11n vehicle detection
│   │   ├── plate_reader.py     ← License plate recognition (PaddleOCR)
│   │   ├── occupancy_tracker.py ← Zone-based spot occupancy tracking
│   │   └── violation_detector.py ← Parking violation detection
│   ├── camera/
│   │   ├── camera_manager.py   ← Multi-camera management
│   │   ├── picamera_source.py  ← Pi Camera (Picamera2) source
│   │   └── usb_camera_source.py ← USB webcam (OpenCV) source
│   ├── parking/
│   │   ├── parking_map.py      ← Parking spot map and zone definitions
│   │   ├── gate_controller.py  ← GPIO-controlled barrier gate
│   │   └── vehicle_log.py      ← Vehicle entry/exit logging
│   ├── routes/
│   │   ├── auth.py             ← Login / logout routes
│   │   ├── dashboard.py        ← Dashboard API
│   │   ├── parking.py          ← Parking map and occupancy API
│   │   ├── vehicles.py         ← Vehicle log and plate search API
│   │   ├── violations.py       ← Violation management API
│   │   ├── analytics.py        ← Statistics and reports API
│   │   ├── cameras.py          ← Camera management API
│   │   └── settings.py         ← Settings API
│   └── services/
│       ├── event_service.py    ← Event logging and retrieval
│       ├── analytics_service.py ← Occupancy trends, peak hours, reports
│       ├── notification_service.py ← Telegram/email/MQTT alerts
│       ├── system_service.py   ← System info (temp, memory, disk)
│       └── db.py               ← SQLite/PostgreSQL database initialization
├── models/                     ← Detection models (auto-downloaded)
│   └── yolov11n.pt            ← YOLOv11n weights
├── templates/                  ← Jinja2 HTML templates
│   ├── layout.html             ← Base layout with sidebar navigation
│   ├── login.html              ← Login page
│   ├── dashboard.html          ← Overview: occupancy, alerts, stats
│   ├── parking_map.html        ← Interactive parking map (SVG/Canvas)
│   ├── vehicles.html           ← Vehicle log and plate search
│   ├── violations.html         ← Violation list and management
│   ├── analytics.html          ← Charts: occupancy trends, peak hours
│   ├── cameras.html            ← Multi-camera configuration
│   └── settings.html           ← Notification and detection settings
├── static/                     ← Static frontend assets
│   ├── css/style.css           ← Dark theme dashboard stylesheet
│   └── js/
│       ├── main.js             ← WebSocket client for real-time updates
│       ├── dashboard.js        ← Dashboard overview logic
│       ├── parking_map.js      ← Interactive SVG/Canvas parking map
│       ├── vehicles.js         ← Vehicle log logic
│       ├── violations.js       ← Violation management logic
│       ├── analytics.js        ← Chart.js analytics charts
│       └── cameras.js          ← Camera management logic
├── scripts/
│   ├── setup-camera.sh         ← Camera module setup (enable CSI)
│   ├── download-models.sh      ← Download YOLOv11n weights
│   └── setup-paddleocr.sh      ← PaddleOCR installation
├── deploy/
│   └── deploy_to_pi.sh         ← rsync-based deploy script
├── docs/
│   └── threat_model.md         ← Threat model and mitigations
├── tests/                      ← Test directory
├── README.md                   ← This file
├── TSD.md                      ← Technical Specification Description
└── task.md                     ← Engineering checklist
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB+) / Pi 5 | Yes | Pi 5 recommended for multi-camera; 4 GB minimum |
| microSD card (32 GB+) | Yes | For OS, models, and database |
| Pi Camera Module v2/v3 or USB webcam | Yes | At least one camera per zone; wide-angle preferred |
| Power supply (official) | Yes | 5V 3A for Pi 4, 5V 5A for Pi 5 |
| Ethernet or WiFi | Yes | For dashboard access and notifications |
| Pi Camera ribbon cable (long) | Optional | Extended cable for mounting camera above lot |
| Additional cameras | Optional | One per zone or entry/exit point |
| 1-channel relay module | Optional | For barrier gate control (GPIO) |
| Barrier gate motor | Optional | For automated entry/exit gate |

---

## Budget

| Item | Estimated Price (USD) | Notes |
|---|---|---|
| Pi Camera Module v2 (wide-angle) | $25 – $35 | Wide-angle lens covers more area |
| Camera mount + weatherproof enclosure | $10 – $20 | Outdoor installation |
| Extended ribbon cable (1m) | $5 – $8 | For mounting camera away from the Pi |
| **Optional:** Additional USB webcam | $15 – $30 | Per additional zone |
| **Optional:** 1-channel relay module | $2 – $4 | For barrier gate control |
| **Optional:** Barrier gate motor | $50 – $200 | Automatic gate (varies widely) |
| **Total (minimum)** | **~$40 – $63** | One camera + mount + cable |

> **Note:** The Raspberry Pi itself, microSD card, and power supply are not included in the budget above.

---

## Libraries and dependencies

### Python dependencies

| Library | Version | Purpose |
|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | ^3.1.0 | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | ^5.4.0 | WebSocket for real-time parking updates |
| [Jinja2](https://jinja.palletsprojects.com/) | ^3.1.4 | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ^1.0.1 | Load environment variables from `.env` |
| [ultralytics](https://github.com/ultralytics/ultralytics) | ^8.3.0 | YOLOv11n vehicle detection |
| [opencv-python-headless](https://pypi.org/project/opencv-python-headless/) | ^4.10.0 | Video capture and image processing |
| [paddleocr](https://github.com/PaddlePaddle/PaddleOCR) | ^2.8.0 | License plate OCR |
| [paddlepaddle](https://www.paddlepaddle.org.cn/) | ^2.6.0 | PaddlePaddle deep learning framework |
| [numpy](https://numpy.org/) | ^1.26.0 | Array operations for image processing |
| [Pillow](https://python-pillow.org/) | ^10.4.0 | Image manipulation |
| [picamera2](https://github.com/raspberrypi/picamera2) | ^0.3.0 | Pi Camera interface (Pi only) |
| [bcrypt](https://pypi.org/project/bcrypt/) | ^4.2.0 | Password hashing |
| [paho-mqtt](https://pypi.org/project/paho-mqtt/) | ^2.1.0 | MQTT IoT integration |
| [python-telegram-bot](https://python-telegram-bot.org/) | ^21.0 | Telegram Bot notifications |
| [chart.js](https://www.chartjs.org/) | ^4.4.7 | Analytics charts (loaded via CDN) |

### Dev dependencies

| Library | Version | Purpose |
|---|---|---|
| [pytest](https://docs.pytest.org/) | ^8.3.0 | Testing framework |

### System packages (installed on the Pi)

| Package | Purpose |
|---|---|
| `libcamera-apps` | Camera stack for Pi Camera Module |
| `cmake`, `build-essential` | Compiling PaddlePaddle dependencies |
| `libatlas-base-dev` | BLAS library for numpy |
| `Python 3.11+` | Python runtime |

---

## Quickstart — Laptop (development)

**1. Clone the repository**

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/Private Auto Parking AI-Monitoring"
```

**2. Create the `.env` file from the template**

```bash
# Linux / macOS
cp .env.default .env

# Windows
copy .env.default .env
```

Edit `.env` and set your values (at minimum, change `SESSION_SECRET` and `ADMIN_PASSWORD`).

**3. Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

**4. Download the YOLOv11n model**

```bash
bash scripts/download-models.sh
```

**5. Start the development server**

```bash
python app.py
```

**6. Open the dashboard**

Navigate to `http://localhost:5000` in your browser.

- **Username:** `admin` (or whatever you set in `.env`)
- **Password:** `changeme` (or whatever you set in `.env`)

> **Note:** On a laptop, the system uses the built-in webcam (if available). Gate control is simulated. All dashboard features (parking map, vehicles, violations, analytics) work fully with the webcam feed.

---

## Environment configuration (.env)

Copy `.env.default` to `.env` and edit it. **Never commit `.env` to git.**

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Dashboard web server port |
| `HOST` | `0.0.0.0` | Listen address |
| `SESSION_SECRET` | `CHANGE_ME...` | Random string for session encryption |
| `ADMIN_USERNAME` | `admin` | Dashboard login username |
| `ADMIN_PASSWORD` | `changeme` | Dashboard login password |
| `DB_TYPE` | `sqlite` | Database type: `sqlite` or `postgresql` |
| `DB_PATH` | `./data/parking.db` | SQLite database path |
| `CAMERA_SOURCE` | `picamera` | Camera source: `picamera`, `usb`, or device index |
| `CAMERA_RESOLUTION` | `1280x720` | Camera resolution |
| `CAMERA_FPS` | `10` | Target frame rate |
| `DETECTION_CONFIDENCE` | `0.5` | Minimum detection confidence |
| `DETECTION_CLASSES` | `car,truck,motorcycle,bus` | Vehicle classes to detect |
| `LPR_ENABLED` | `true` | Enable license plate recognition |
| `TOTAL_PARKING_SPOTS` | `20` | Total number of parking spots |
| `GATE_ENABLED` | `false` | Enable GPIO barrier gate control |
| `GATE_RELAY_PIN` | `17` | GPIO pin for gate relay |
| `GATE_OPEN_DURATION_SEC` | `10` | How long the gate stays open |
| `VIOLATION_OVERTIME_MIN` | `120` | Minutes after which overtime violation triggers |
| `NOTIFY_TELEGRAM_ENABLED` | `false` | Enable Telegram notifications |
| `NOTIFY_TELEGRAM_TOKEN` | `` | Telegram Bot API token |
| `NOTIFY_TELEGRAM_CHAT_ID` | `` | Telegram chat ID |
| `NOTIFY_MQTT_ENABLED` | `false` | Enable MQTT notifications |
| `NOTIFY_MQTT_BROKER` | `localhost` | MQTT broker address |
| `NOTIFY_MQTT_TOPIC` | `parking/events` | MQTT topic for parking events |

---

## Detection pipeline overview

| Stage | Component | Tool | What it does |
|---|---|---|---|
| **1. Capture** | Camera Manager | Picamera2 / OpenCV | Captures video frames from cameras |
| **2. Detect** | Vehicle Detector | YOLOv11n (ultralytics) | Detects vehicles (car, truck, motorcycle, bus) |
| **3. Track** | Occupancy Tracker | Zone-polygon logic | Maps detections to parking spots |
| **4. Read plate** | Plate Reader | PaddleOCR | Reads license plate text from detected vehicles |
| **5. Log** | Vehicle Log | SQLite/PostgreSQL | Logs entry/exit with plate, timestamp, spot |
| **6. Check violations** | Violation Detector | Rule engine | Checks overtime, unauthorized, no-parking zone |
| **7. Gate** | Gate Controller | GPIO relay | Opens/closes barrier for authorized plates |
| **8. Notify** | Notification Service | Telegram / Email / MQTT | Alerts on violations or events |
| **9. Stream** | WebSocket | Flask-SocketIO | Updates dashboard in real time |

---

## Feature 1 — Vehicle detection (YOLOv11n)

The default detection engine uses YOLOv11n (nano) for real-time vehicle detection.

- **COCO vehicle classes:** car, truck, motorcycle, bus, bicycle.
- **Configurable classes:** Set `DETECTION_CLASSES` in `.env`.
- **Confidence threshold:** Adjust `DETECTION_CONFIDENCE` to filter weak detections.
- **Vehicle type classification:** Distinguish between car, SUV, motorcycle, truck — enforce vehicle-size rules per spot.

---

## Feature 2 — Parking occupancy tracking

Track which spots are occupied and which are free in real time.

- **Zone-based detection:** Each parking spot is defined as a polygon zone on the camera frame.
- **Spot status:** Green (free), Red (occupied), Yellow (reserved/violation).
- **Real-time updates:** Spot status changes instantly when a vehicle enters or leaves.
- **Occupancy count:** Total free/occupied displayed on dashboard.
- **Configurable spots:** Draw spot polygons from the dashboard (see Parking Map).

---

## Feature 3 — License plate recognition (LPR)

Identify vehicles by their license plate for access control and logging.

- **PaddleOCR:** Open-source OCR engine optimized for plate recognition.
- **Pipeline:** YOLOv11n detects vehicle → crop plate region → PaddleOCR reads text.
- **Authorized plates:** Configure a whitelist of plates for auto-gate opening.
- **Vehicle log:** Every entry/exit logged with plate number, timestamp, and duration.
- **Search:** Search vehicle history by plate number from the dashboard.

---

## Feature 4 — Parking map visualization

Interactive SVG/Canvas map of the parking lot on the dashboard.

- **Visual spots:** Each parking spot is a polygon on the map.
- **Color-coded:** Green (free), Red (occupied), Yellow (violation), Gray (disabled).
- **Real-time:** Map updates live as vehicles enter and leave spots.
- **Click to configure:** Click a spot to view details (plate, duration, vehicle type).
- **Draw spots:** Drag-and-drop spot creation from the dashboard — draw polygons on the camera feed to define spot boundaries.
- **Spot labels:** Name/number each spot (e.g., A1, A2, B1, etc.).

---

## Feature 5 — Entry/exit gate integration

GPIO-controlled barrier gate for automated access control.

- **Authorized plates:** Auto-open gate when a whitelisted plate is detected.
- **Unknown vehicles:** Gate stays closed; notification sent to admin.
- **Manual override:** Open/close gate from the dashboard.
- **Relay control:** GPIO pin drives a relay module connected to the barrier motor.
- **Configurable timing:** Gate open duration (`GATE_OPEN_DURATION_SEC`).

---

## Feature 6 — Violation detection

Automatically detect parking violations.

| Violation | How it's detected | Action |
|---|---|---|
| **Overtime** | Vehicle exceeds `VIOLATION_OVERTIME_MIN` in a spot | Notification + violation log |
| **No-parking zone** | Vehicle detected in a marked no-parking area | Notification + violation log |
| **Unauthorized vehicle** | Plate not in whitelist (if whitelist mode enabled) | Notification + gate denied |
| **Wrong spot type** | Large vehicle in compact-only spot | Notification + violation log |

**From the dashboard (Violations page):**
- List of all violations with details.
- Filter by date, violation type, plate.
- Mark violations as resolved.
- Export violation log as CSV/PDF.

---

## Feature 7 — Multi-camera support

Cover the entire parking lot with multiple cameras.

- **One camera per zone:** Each camera monitors a group of parking spots.
- **Independent detection:** Each camera runs its own detection pipeline.
- **Unified dashboard:** All cameras feed into the same parking map and vehicle log.
- **Supported cameras:** Pi Camera (CSI), USB webcams, RTSP/IP cameras.
- **Multi-Pi:** For large lots, use multiple Pis with a shared database (PostgreSQL recommended for multi-Pi setups).

---

## Feature 8 — Analytics dashboard

Occupancy trends, peak hours, and usage statistics with Chart.js.

| Chart/Report | Description |
|---|---|
| **Occupancy over time** | Line chart: spots occupied per hour/day |
| **Peak hours** | Bar chart: busiest hours of the day |
| **Average duration** | Average parking duration per spot or overall |
| **Vehicle type distribution** | Pie chart: cars vs. trucks vs. motorcycles |
| **Monthly report** | Summary table: total entries, average occupancy, violations |
| **CSV/PDF export** | Download reports for external analysis |

---

## Feature 9 — Web dashboard

A real-time web interface for monitoring and managing the parking system.

| Section | Description |
|---|---|
| **Dashboard** | Overview: occupancy count, live alerts, key stats, mini parking map |
| **Parking Map** | Full interactive SVG/Canvas map with real-time spot status |
| **Vehicles** | Vehicle entry/exit log, plate search, duration history |
| **Violations** | Violation list, management, resolution, export |
| **Analytics** | Occupancy trends, peak hours, reports with Chart.js |
| **Cameras** | Multi-camera configuration and live feeds |
| **Settings** | Detection, gate, notifications, spot config, password |

**Real-time features:**
- Parking map updates live via WebSocket.
- New entries/exits and violations appear instantly.
- System stats (CPU, memory, FPS) in the top bar.

---

## Notifications

| Channel | Events | Notes |
|---|---|---|
| **Telegram** | Violations, unauthorized vehicle, lot full | Free, instant, with snapshot |
| **Email** | Daily reports, violation summary | Configurable schedule |
| **MQTT** | All events (entry, exit, violation, occupancy change) | For IoT/Home Assistant |

---

## MQTT / IoT integration

Publish parking events to MQTT for integration with Home Assistant or other IoT platforms.

**Published topics:**

| Topic | Payload | Trigger |
|---|---|---|
| `parking/occupancy` | `{ "total": 20, "occupied": 12, "free": 8 }` | Every occupancy change |
| `parking/entry` | `{ "plate": "AB123CD", "spot": "A1", "time": "..." }` | Vehicle enters |
| `parking/exit` | `{ "plate": "AB123CD", "duration_min": 45, "time": "..." }` | Vehicle leaves |
| `parking/violation` | `{ "type": "overtime", "plate": "AB123CD", "spot": "A1" }` | Violation detected |
| `parking/gate` | `{ "action": "open", "reason": "authorized_plate" }` | Gate action |

---

## Authentication

The web dashboard is protected by session-based authentication.

- Credentials are stored in `.env` (`ADMIN_USERNAME` and `ADMIN_PASSWORD`).
- Login attempts are rate-limited (10 attempts per 15 minutes) to prevent brute-force.
- Sessions expire after 24 hours.
- Passwords can be changed from **Settings → Change Password** in the dashboard.

---

## How to deploy to Raspberry Pi

Your SSH config is already set up at `~/.ssh/config`:

```
Host rasp-pi
    HostName 192.168.216.90
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

**Method A — Use the deploy script (recommended)**

From the project directory on your laptop:

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/ParkingAI
```

This will:
1. Create the remote directory.
2. Rsync all project files (excludes `venv`, `.env`, `.git`, `models/`, `data/`).
3. Create a virtual environment and install dependencies on the Pi.
4. Create `.env` from `.env.default` if it does not exist.

**Method B — Manual rsync**

```bash
rsync -avz --delete \
  --exclude='venv/' \
  --exclude='.env' \
  --exclude='.git/' \
  --exclude='models/' \
  --exclude='data/' \
  ./ \
  rasp-pi:/home/pi/Projects/ParkingAI/

ssh rasp-pi "cd /home/pi/Projects/ParkingAI && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
```

---

## How to run on the Raspberry Pi

**1. SSH into the Pi**

```bash
ssh rasp-pi
```

**2. Go to the project directory**

```bash
cd /home/pi/Projects/ParkingAI
```

**3. Edit the .env file**

```bash
nano .env
```

Set `SESSION_SECRET`, `ADMIN_PASSWORD`, and `TOTAL_PARKING_SPOTS`.

**4. Enable the camera**

```bash
sudo bash scripts/setup-camera.sh
```

**5. Download models**

```bash
bash scripts/download-models.sh
bash scripts/setup-paddleocr.sh
```

**6. Start the parking system**

```bash
source venv/bin/activate
python app.py
```

Access the dashboard at `http://192.168.216.90:5000`.

**7. (Optional) Run as a systemd service**

```bash
sudo nano /etc/systemd/system/parking-ai.service
```

```ini
[Unit]
Description=Private Auto Parking AI-Monitoring
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/ParkingAI
ExecStart=/home/pi/Projects/ParkingAI/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable parking-ai
sudo systemctl start parking-ai
```

---

## Real-world applications

| Application | Who uses it | Why |
|---|---|---|
| **Private parking lot management** | Property owners | Monitor occupancy, detect unauthorized parking, automate gate |
| **Apartment complex parking** | Building managers | Assign spots, enforce rules, track resident vs. guest usage |
| **Small business parking** | Business owners | Customer parking management, overtime detection |
| **Shopping mall parking** | Mall management | Real-time availability display, analytics for peak planning |
| **Gated community** | HOAs | License plate access control, visitor management |
| **Company fleet parking** | Fleet managers | Track vehicle entry/exit, usage patterns |
| **EV charging station** | Charging operators | Monitor which spots have vehicles, detect ICE-ing (non-EV blocking) |
| **Event parking** | Event organizers | Temporary lot monitoring, count available spaces, direct traffic |
| **Education project** | Teachers, students | Computer vision, IoT, database design, web development in one project |

---

## Security notes

- **Change the default password immediately** after first login. Use the Settings page or edit `.env`.
- **Generate a strong `SESSION_SECRET`** — run: `python -c "import secrets; print(secrets.token_hex(32))"`
- **The `.env` file contains sensitive data** (passwords, API tokens). It is in `.gitignore` and should never be committed. Protect it: `chmod 600 .env`
- **License plate data is PII.** Store responsibly. Configure data retention policies. Delete old records on a schedule.
- **Camera feeds should not be publicly accessible.** Authentication protects the dashboard; ensure the Pi is on a trusted network.
- **Rate limiting** is enabled on the login endpoint.
- **Gate GPIO control requires appropriate permissions.** Add the `pi` user to the `gpio` group.
- **MQTT topics may contain PII (plates).** Secure the MQTT broker with authentication.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Camera not detected | Check ribbon cable. Enable camera: `sudo raspi-config`. Test with `libcamera-hello`. |
| Low FPS / slow detection | Reduce resolution. Use Pi 5. Reduce `CAMERA_FPS`. |
| LPR not reading plates | Check camera resolution (plates need ~100px width minimum). Good lighting. Adjust camera angle. |
| PaddleOCR install fails | Run `bash scripts/setup-paddleocr.sh`. Ensure 4 GB+ RAM. Install `cmake build-essential`. |
| Gate relay not working | Check GPIO pin number. Check relay wiring (VCC, IN, GND). Test pin with `gpio write`. |
| Parking map spots misaligned | Re-draw spot polygons from the dashboard camera view. Ensure camera hasn't moved. |
| MQTT not publishing | Check broker is running: `mosquitto -v`. Verify broker address and port in `.env`. |
| Database grows too large | Configure data retention (auto-delete events older than N days). Switch to PostgreSQL for better performance. |
| Dashboard not loading | Check if the server is running. Verify IP and port. Check `python app.py` output. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- See [task.md](task.md) for the engineering checklist with step-by-step implementation tasks.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model and mitigations.
