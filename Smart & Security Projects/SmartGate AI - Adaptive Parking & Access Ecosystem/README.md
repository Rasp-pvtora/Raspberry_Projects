# 🏷️ SmartGate AI — Adaptive Parking & Access Ecosystem

> **The intelligent bridge between physical parking infrastructure and digital enterprise presence.**

SmartGate AI is a professional-grade integration of **Edge AI**, **IoT**, and **Enterprise collaboration tools** (Microsoft Teams / Google Workspace) built on a Raspberry Pi. It transforms standard parking areas into dynamic, self-optimizing resources by bridging the physical world (cameras, gates, NFC) with digital presence (Home Office status, Meeting status). The system maximizes parking efficiency, automates EV charging billing, and provides real-time HR attendance tracking — all from a single dashboard.

### 🪙 Donations are Welcome!
If you find this project helpful, you can support my work with a small donation.

₿ Bitcoin donation: bc1q...

---

## 📑 Table of Contents

- [Features](#-features)
- [Hardware Requirements](#-hardware-requirements)
- [Budget](#-budget)
- [Wiring & Connections](#-wiring--connections)
- [Software & Libraries](#-software--libraries)
- [Quick Start](#-quick-start)
- [Configuration (.env)](#%EF%B8%8F-configuration-env)
- [System Architecture](#-system-architecture)
- [Core Workflows](#-core-workflows)
- [Dashboard](#-dashboard)
- [Authentication & Security](#-authentication--security)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Features

All features are independently **.env toggleable** for granular testing and deployment:

| # | Feature | Toggle | Description |
|---|---------|--------|-------------|
| 1 | **ALPR Entry/Exit** | `ENABLE_ALPR` | Automatic License Plate Recognition via Pi camera using PaddleOCR/EasyOCR |
| 2 | **Dual-Pin Gate Trigger** | *(always on)* | Pin 1: Visual confirmation (LED/Screen) · Pin 2: Relay for gate motor |
| 3 | **NFC/RFID Backup** | `ENABLE_NFC_BACKUP` | RC522 reader for residential badge or emergency manual override |
| 4 | **Teams Status Integration** | `ENABLE_TEAMS_INTEGRATION` | Microsoft Graph API checks user presence (Available/InMeeting/Away/Offline) |
| 5 | **Google Calendar Integration** | `ENABLE_GOOGLE_INTEGRATION` | Google Calendar/Workspace API checks WFH events and availability |
| 6 | **Multi-Language Bot Notifications** | `ENABLE_WHATSAPP_BOT` / `ENABLE_TELEGRAM_BOT` | "Are you in Home Office today?" via Teams, WhatsApp, or Telegram |
| 7 | **Dynamic Spot Reallocation** | `ENABLE_SHARED_SPOTS` | Free reserved spots when owner confirms Home Office / Sick / Vacation |
| 8 | **Shift & Schedule Logic** | `ENABLE_SHIFT_LOGIC` | User A: Mon/Fri, User B: Tue–Thu. Morning/Evening/Night shift authorization |
| 9 | **EV Charging & Billing** | `ENABLE_EV_BILLING` | Camera monitors EV bays → logs session duration → payroll deduction |
| 10 | **Guest Plate Pre-Registration** | `ENABLE_GUEST_MANAGEMENT` | Employees register visitor plates for time-limited one-time access |
| 11 | **HR Time-Tracking** | `ENABLE_HR_TIMETRACKING` | Entry/exit timestamps → "Time at Work" → CSV/PDF export for payroll |
| 12 | **Parking Violation Detection** | `ENABLE_VIOLATION_DETECTION` | AI detects wrong-spot, double-parking, disabled-zone violations |
| 13 | **Emergency Vehicle Auto-Open** | `ENABLE_EMERGENCY_VEHICLE` | Priority plate DB for ambulance/fire — auto-open without delay |
| 14 | **Night-Mode IR Camera** | `ENABLE_NIGHT_MODE` | NoIR camera + IR illuminator for 24/7 ALPR |
| 15 | **Heatmap Analytics** | `ENABLE_HEATMAP_ANALYTICS` | Time-series occupancy heatmap (hour/day/week patterns) |
| 16 | **PDF/Excel HR Reports** | `ENABLE_PDF_REPORTS` | Monthly auto-generated attendance summaries per cost center |
| 17 | **GDPR Compliance** | `ENABLE_GDPR_PURGE` | Auto-purge plate logs after configurable retention period |
| 18 | **Sound Deterrent** | `ENABLE_SOUND_ALERT` | Buzzer on unauthorized plate or tailgating detection |
| 19 | **Multi-Gate Topology** | `ENABLE_MULTI_GATE` | N entrance/exit Pi nodes reporting to central server |
| 20 | **LDAP/Azure AD Sync** | `ENABLE_LDAP_SYNC` | Auto-import employees, plates, Teams IDs from corporate directory |
| 21 | **REST API** | `ENABLE_REST_API` | Documented endpoints for third-party ERP/HR integration |
| 22 | **QR Visitor Pass** | `ENABLE_QR_VISITOR` | Employees generate time-limited QR codes for guests |

---

## 🔧 Hardware Requirements

| Component | Purpose | Qty |
|-----------|---------|-----|
| Raspberry Pi 4 Model B (4GB+) | Main controller | 1+ (per gate) |
| RPi HQ Camera / USB Webcam | ALPR at entrance | 1 |
| RPi Camera Module v2 (optional) | EV station monitoring | 1 |
| NFC/RFID RC522 Module | Badge backup access | 1 |
| 2-Channel Relay Module (5V) | Gate motor + secondary trigger | 1 |
| High-Brightness LEDs (R/G/Y) | Visual gate status | 3 |
| Active Buzzer Module | Unauthorized alert | 1 |
| 7" HDMI Touchscreen (optional) | Gate-side status display | 1 |
| NoIR Camera + IR LEDs (optional) | Night-mode ALPR | 1 |
| External SSD/HDD (500GB+) | MySQL data + plate images | 1 |
| PoE HAT or 5V/3A PSU | Power supply | 1 |

---

## 💰 Budget

| Item | Est. Cost |
|------|-----------|
| Raspberry Pi 4 (4GB) | $55 |
| RPi HQ Camera + Lens | $50–75 |
| RC522 NFC Module | $4 |
| 2-Channel Relay | $4 |
| LEDs + Resistors + Buzzer | $5 |
| 7" Touchscreen (optional) | $60 |
| NoIR Camera + IR LEDs (optional) | $30 |
| External SSD 500GB | $40 |
| Cables, Case, Misc | $15 |
| **Total (Core)** | **~$133–148** |
| **Total (Full)** | **~$263–308** |

---

## 🔌 Wiring & Connections

```
Raspberry Pi 4 GPIO
├── GPIO 17 ──► LED Green (Authorized — Access Granted)
├── GPIO 27 ──► LED Red (Unauthorized — Access Denied)
├── GPIO 22 ──► LED Yellow (Pending Verification)
├── GPIO 23 ──► Relay CH1 IN (Gate Motor Trigger)
├── GPIO 24 ──► Relay CH2 IN (Secondary Lock / Barrier)
├── GPIO 25 ──► Active Buzzer (Unauthorized Alert)
│
├── SPI Bus (RC522 NFC/RFID)
│   ├── GPIO 8  (CE0/SDA)
│   ├── GPIO 11 (SCLK)
│   ├── GPIO 10 (MOSI)
│   ├── GPIO 9  (MISO)
│   └── GPIO 25 (RST) — shared or GPIO 6
│
├── CSI Connector ──► RPi HQ Camera (ALPR)
├── USB Port ──► USB Webcam (EV Station / Backup)
├── HDMI ──► 7" Touchscreen (Gate Display)
└── USB/SATA ──► External SSD (Database Storage)
```

---

## 📦 Software & Libraries

| Library | Purpose |
|---------|---------|
| `flask` / `fastapi` | Web backend & REST API |
| `flask-socketio` | Real-time dashboard updates |
| `opencv-python-headless` | Camera capture & image processing |
| `paddleocr` / `easyocr` | License plate text recognition |
| `ultralytics` (YOLOv8) | Vehicle detection & plate localization |
| `mfrc522` | NFC/RFID RC522 reader |
| `RPi.GPIO` / `gpiozero` | LED, relay, buzzer control |
| `mysql-connector-python` | MySQL database operations |
| `msal` | Microsoft Graph API (Teams presence) |
| `google-api-python-client` | Google Calendar/Workspace API |
| `python-telegram-bot` | Telegram bot notifications |
| `bcrypt` | Password hashing |
| `python-dotenv` | .env configuration loading |
| `apscheduler` | Scheduled jobs (reports, GDPR purge, sync) |
| `reportlab` / `openpyxl` | PDF/Excel report generation |
| `pyzbar` | QR code reading for visitor passes |
| `numpy` | Image processing support |
| `jinja2` | HTML templating |

---

## 🚀 Quick Start

```bash
# 1. SSH into your Raspberry Pi
ssh rasp-pi    # alias for 192.168.216.90

# 2. Clone repository
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/SmartGate AI - Adaptive Parking & Access Ecosystem"

# 3. Create virtual environment
python3 -m venv venv && source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install MySQL
sudo apt install mariadb-server -y
sudo mysql_secure_installation

# 6. Initialize database
python3 init_db.py

# 7. Configure environment
cp .env.default .env
nano .env   # Set your API keys, DB credentials, feature toggles

# 8. Enable SPI for NFC
sudo raspi-config  # Interface Options → SPI → Enable
sudo reboot

# 9. Start SmartGate AI
python3 app.py
# Dashboard: https://<pi-ip>:5000
```

---

## ⚙️ Configuration (.env)

See `TSD.md` for the complete `.env.default` template. Key sections:

```ini
# === Core ===
APP_SECRET_KEY=change-me-to-random-64-chars
ADMIN_USER=admin
ADMIN_PASS_HASH=$2b$12$...   # bcrypt hash

# === Database ===
DB_HOST=localhost
DB_NAME=smartgate
DB_USER=smartgate_user
DB_PASS=change-me

# === Feature Toggles (true/false) ===
ENABLE_ALPR=true
ENABLE_NFC_BACKUP=true
ENABLE_TEAMS_INTEGRATION=false
ENABLE_GOOGLE_INTEGRATION=false
ENABLE_EV_BILLING=false
ENABLE_HR_TIMETRACKING=true
# ... (22 toggleable features — see TSD.md)

# === Microsoft Teams ===
TEAMS_TENANT_ID=
TEAMS_CLIENT_ID=
TEAMS_CLIENT_SECRET=

# === GPIO Pins ===
PIN_LED_GREEN=17
PIN_LED_RED=27
PIN_LED_YELLOW=22
PIN_RELAY_GATE=23
PIN_RELAY_LOCK=24
PIN_BUZZER=25
```

---

## 🏗️ System Architecture

```
                    ┌──────────────────────────────────────┐
                    │           Web Dashboard              │
                    │   (Flask + SocketIO + SVG Map)       │
                    │  🔴 Occupied  🟢 Free  🟡 Pending   │
                    │  ⚪ Reserved  📊 Analytics  📋 HR    │
                    └──────────────┬───────────────────────┘
                                   │ REST / WebSocket
                    ┌──────────────▼───────────────────────┐
                    │         Application Server            │
                    │  Flask/FastAPI + APScheduler           │
                    │  ┌─────────┬─────────┬──────────┐    │
                    │  │  ALPR   │  NFC    │ Teams/   │    │
                    │  │ Engine  │ Reader  │ Google   │    │
                    │  └────┬────┴────┬────┴─────┬────┘    │
                    └───────┼─────────┼──────────┼─────────┘
                            │         │          │
              ┌─────────────▼──┐  ┌───▼───┐  ┌──▼──────────────┐
              │  Pi Camera     │  │ RC522 │  │ MS Graph API    │
              │  (OpenCV +     │  │ SPI   │  │ Google API      │
              │   PaddleOCR)   │  └───────┘  │ Telegram/WA API │
              └────────────────┘             └─────────────────┘
                            │
              ┌─────────────▼──────────────────────────────┐
              │              GPIO Output                    │
              │  LED Green │ LED Red │ Relay Gate │ Buzzer  │
              └────────────────────────────────────────────┘
                            │
              ┌─────────────▼──────────────────────────────┐
              │           MySQL Database                    │
              │  employees │ plates │ spots │ access_logs   │
              │  ev_sessions │ shifts │ guests │ settings   │
              └────────────────────────────────────────────┘
```

---

## 🔄 Core Workflows

### Workflow 1: Vehicle Entry
```
Camera Frame → YOLOv8 (detect plate region) → PaddleOCR (read text)
  → DB Lookup (authorized?)
    ├── YES → GPIO: Green LED + Relay Open → Log entry timestamp
    │         → Dashboard: Spot → 🔴 RED (alias)
    │         → If HR tracking: Start work timer
    └── NO  → GPIO: Red LED + Buzzer → Log unauthorized attempt
              → Dashboard: Alert notification
              → If guest DB match: Temporary access
```

### Workflow 2: Teams/Google Status Check (Scheduled)
```
APScheduler (every 15 min) → For each reserved spot with no car:
  → MS Graph API: Get user presence
    ├── "Available" / "InACall" → Spot = 🟡 YELLOW
    │   → Send bot message: "Home Office today? Free your spot?"
    │     ├── Reply "Yes, free it" → Spot = 🟢 GREEN (available)
    │     └── Reply "No, coming" → Spot = ⚪ GREY (reserved)
    ├── "Away" / "BeRightBack" → Spot = ⚪ GREY (commuting)
    └── "Offline" → Spot = ⚪ GREY (offline)
```

### Workflow 3: EV Charging Billing
```
EV Camera → Detect plate in charging bay
  → Start billing timer in DB
  → When plate leaves bay → Stop timer
  → Calculate kWh × rate → Add to employee payroll record
  → If non-DB plate in EV bay → Alert supervisor immediately
```

### Workflow 4: HR Time Tracking
```
Entry log (ALPR) → Start "at work" timer
  → If exit during work hours:
    ├── Short (<30 min) → "Break" status
    └── Long (>30 min) → Alert: Early departure notification
  → End of day: Calculate total hours → CSV/DB
  → Monthly: Auto-generate PDF attendance report
```

---

## 📊 Dashboard

The web dashboard is the central control hub:

- **Real-Time SVG Parking Map** — Color-coded spots with employee aliases
- **Gate Live Feed** — Camera stream with ALPR overlay
- **EV Station Monitor** — Charging session durations and billing
- **Access Log Table** — Searchable, filterable entry/exit history
- **Guest Management** — Register visitor plates with expiry
- **Shift Calendar** — Visual schedule for shared-spot assignments
- **HR Reports** — Daily/weekly/monthly attendance charts
- **Heatmap Analytics** — Parking density patterns
- **Settings Panel** — Feature toggles, GPIO config, API keys
- **Dark theme** enabled by default

---

## 🔐 Authentication & Security

- **bcrypt** password hashing for dashboard login
- **Rate limiting**: 10 attempts per 15 minutes
- **Session expiry**: 24 hours
- **HTTPS**: Self-signed or Let's Encrypt TLS
- **CSRF protection** on all forms
- **API key auth** for REST endpoints
- **GDPR**: Configurable data retention and auto-purge
- **Audit log**: All admin actions recorded

---

## 📡 Deployment

```bash
# Production with gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --certfile cert.pem --keyfile key.pem app:app

# Or with systemd service
sudo cp deploy/smartgate.service /etc/systemd/system/
sudo systemctl enable smartgate
sudo systemctl start smartgate

# Database backup (cron)
echo "0 2 * * * mysqldump smartgate | gzip > /backup/smartgate_$(date +\%F).sql.gz" | crontab -
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| ALPR not detecting plates | Check camera focus, lighting. Try `ALPR_CONFIDENCE_THRESHOLD=0.5` |
| NFC not reading | Verify SPI enabled: `ls /dev/spidev*`. Check wiring |
| Teams API 401 | Refresh `TEAMS_CLIENT_SECRET`. Check Azure AD app permissions |
| Gate relay not triggering | Test: `python3 -c "import RPi.GPIO as G; G.setmode(G.BCM); G.setup(23,G.OUT); G.output(23,1)"` |
| Dashboard slow | Check MySQL indices: `EXPLAIN SELECT ...`. Enable connection pooling |
| EV billing inaccurate | Calibrate `EV_CAMERA_POLL_INTERVAL_SEC` to match your camera FPS |

---

## 📄 License

This project is open source under the [MIT License](../../LICENSE).

---

> **SmartGate AI** — *Turning empty reserved spots into shared resources, one Teams status at a time.*
