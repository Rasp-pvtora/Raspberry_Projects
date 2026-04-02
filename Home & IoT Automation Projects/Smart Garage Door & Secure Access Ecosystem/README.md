# 🚪 Smart Garage Door & Secure Access Ecosystem

A comprehensive Raspberry Pi–powered garage access system combining ALPR camera recognition, geofencing, voice control, and multi-notification channels — all managed from a responsive dark-theme web dashboard with per-feature toggle switches.

---

## 📋 Table of Contents
- [Features](#-features)
- [Dashboard Feature Toggles](#-dashboard-feature-toggles)
- [Hardware Requirements](#-hardware-requirements)
- [Wiring Diagram](#-wiring-diagram)
- [Software Stack](#-software-stack)
- [Installation](#-installation)
- [Environment Variables](#-environment-variables)
- [Web Dashboard](#-web-dashboard)
- [API Endpoints](#-api-endpoints)
- [Budget Estimate](#-budget-estimate)
- [License](#-license)
- [Donations](#-donations)

---

## 🌟 Features

Every feature is independently toggleable both via `.env` and the web dashboard:

| # | Feature | `.env` Variable | Default |
|---|---------|----------------|---------|
| 1 | **ALPR Auto-Open** — Camera reads license plates and auto-opens for whitelisted vehicles using OpenALPR/Tesseract | `ENABLE_ALPR=true` | `true` |
| 2 | **Geofencing Auto-Trigger** — Phone GPS proximity triggers door open/close via companion API | `ENABLE_GEOFENCING=true` | `false` |
| 3 | **Delivery / Courier Temporary Access** — Generate time-limited one-time codes for delivery drivers | `ENABLE_DELIVERY_MODE=true` | `false` |
| 4 | **Multi-Channel Notifications** — Alerts via Telegram, Teams, Slack, email, and push notifications | `ENABLE_NOTIFICATIONS=true` | `true` |
| 5 | **Vacation Mode** — Randomized open/close simulation to mimic occupancy while away | `ENABLE_VACATION_MODE=true` | `false` |
| 6 | **Tamper & Forced-Entry Detection** — Vibration + magnetic sensors trigger alarm and instant notification | `ENABLE_TAMPER_DETECTION=true` | `true` |
| 7 | **Voice Control Integration** — Google Home, Alexa, or local Whisper-based voice commands | `ENABLE_VOICE_CONTROL=true` | `false` |
| 8 | **Night-Mode IR Camera** — Infrared camera with motion-triggered recording after dark | `ENABLE_NIGHT_CAMERA=true` | `true` |
| 9 | **Garage Climate Monitoring** — Temperature, humidity, and CO sensor readings displayed on dashboard | `ENABLE_CLIMATE_MONITOR=true` | `false` |
| 10 | **Multi-Door Support** — Independent control for up to 4 garage doors/gates from single Pi | `ENABLE_MULTI_DOOR=true` | `false` |
| 11 | **Guest Access with Time-Limited Codes** — Web-generated QR or PIN codes valid for configurable duration | `ENABLE_GUEST_ACCESS=true` | `false` |
| 12 | **Battery Backup / UPS Monitoring** — INA219 sensor tracks UPS status and sends low-battery alerts | `ENABLE_UPS_MONITOR=true` | `false` |
| 13 | **Auto-Close Timer** — Configurable countdown to auto-close door if left open | `ENABLE_AUTO_CLOSE=true` | `true` |
| 14 | **Historical Analytics Dashboard** — Open/close events, peak usage times, weekly/monthly charts | `ENABLE_ANALYTICS=true` | `true` |
| 15 | **Emergency Quick-Lock** — Physical panic button + app button locks all doors immediately | `ENABLE_EMERGENCY_LOCK=true` | `true` |

---

## 🎛️ Dashboard Feature Toggles

The web dashboard provides a **Settings → Feature Toggles** page where each feature can be enabled/disabled in real time without restarting the service. Toggle state is persisted to `.env` and SQLite.

```
┌──────────────────────────────────────────────────┐
│  ⚙️ Feature Toggles              [Save All]      │
├──────────────────────────────────────────────────┤
│  🚗 ALPR Auto-Open            [████ ON ]         │
│  📍 Geofencing Auto-Trigger   [░░░░ OFF]         │
│  📦 Delivery Mode             [░░░░ OFF]         │
│  🔔 Notifications             [████ ON ]         │
│  🏖️ Vacation Mode             [░░░░ OFF]         │
│  🚨 Tamper Detection          [████ ON ]         │
│  🎙️ Voice Control             [░░░░ OFF]         │
│  🌙 Night Camera              [████ ON ]         │
│  🌡️ Climate Monitor           [░░░░ OFF]         │
│  🚪 Multi-Door                [░░░░ OFF]         │
│  🔑 Guest Access              [░░░░ OFF]         │
│  🔋 UPS Monitor               [░░░░ OFF]         │
│  ⏱️ Auto-Close Timer           [████ ON ]         │
│  📊 Analytics                  [████ ON ]         │
│  🆘 Emergency Lock            [████ ON ]         │
└──────────────────────────────────────────────────┘
```

---

## 🔩 Hardware Requirements

| Component | Model / Spec | Qty | Est. Cost |
|-----------|-------------|-----|-----------|
| Raspberry Pi | 4B (2GB+) or 5 | 1 | $45–75 |
| Pi Camera Module | V2 or V3 (IR-capable) | 1 | $25–35 |
| Relay Module | 5V 2-channel (SRD-05VDC) | 1 | $3–5 |
| Magnetic Reed Switch | Door open/close sensor | 1–4 | $2–4 each |
| Vibration Sensor | SW-420 or piezo | 1 | $2 |
| DHT22 Sensor | Temperature + humidity | 1 | $4–6 |
| MQ-7 CO Sensor | Carbon monoxide (optional) | 1 | $5 |
| INA219 Module | UPS current/voltage monitor | 1 | $3 |
| IR LED Array | Night illumination (if no IR cam) | 1 | $5 |
| UPS HAT | PiSugar or similar | 1 | $20–35 |
| Servo / Linear Actuator | Door mechanism (if not relay) | 1 | $10–20 |
| MicroSD Card | 32GB+ Class 10 | 1 | $8 |
| Power Supply | 5V 3A USB-C | 1 | $10 |
| **Total** | | | **$85–145** |

---

## 🔌 Wiring Diagram

```
Raspberry Pi 4/5 GPIO
┌─────────────────────────────────────┐
│  GPIO 17 ──── Relay IN1 (Door 1)   │
│  GPIO 27 ──── Relay IN2 (Door 2)   │
│  GPIO 22 ──── Reed Switch (Door 1) │
│  GPIO 23 ──── Reed Switch (Door 2) │
│  GPIO 24 ──── SW-420 Vibration     │
│  GPIO 25 ──── Emergency Button     │
│  GPIO 4  ──── DHT22 Data           │
│  I2C SDA ──── INA219 SDA           │
│  I2C SCL ──── INA219 SCL           │
│  CSI Port ─── Pi Camera Module     │
│  3.3V / 5V ── Sensor VCC rails     │
│  GND ──────── Common ground bus    │
└─────────────────────────────────────┘
```

---

## 💻 Software Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask, Flask-SocketIO |
| Frontend | HTML5, CSS3 (dark theme), JavaScript, Chart.js |
| Database | SQLite (events, users, settings) |
| ALPR Engine | OpenALPR / Tesseract OCR |
| Camera | picamera2 / OpenCV |
| Auth | bcrypt hashing, 10 attempts/15min rate limit, 24h JWT sessions |
| Notifications | python-telegram-bot, slack-sdk, pymsteams, smtplib |
| Voice | Whisper (local) / Google Assistant SDK / Alexa Skills Kit |
| Real-time | WebSocket via Flask-SocketIO |
| Process Manager | systemd service |

---

## 🚀 Installation

### 1. Clone & setup
```bash
ssh rasp-pi  # SSH alias for 192.168.216.90
cd /opt
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Home & IoT Automation Projects/Smart Garage Door & Secure Access Ecosystem"
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.default .env
nano .env  # Edit variables for your setup
```

### 4. Initialize database
```bash
python3 init_db.py
```

### 5. Run as service
```bash
sudo cp deploy/garage-door.service /etc/systemd/system/
sudo systemctl enable garage-door
sudo systemctl start garage-door
```

### 6. Access dashboard
```
https://<raspberry-ip>:5000
Default login: admin / changeme (force-change on first login)
```

---

## 🔐 Environment Variables

Full `.env.default` template:

```env
# ──────────────────────────────────────
# Smart Garage Door & Secure Access
# ──────────────────────────────────────

# Server
HOST=0.0.0.0
PORT=5000
SECRET_KEY=change-me-to-random-string
DEBUG=false

# Authentication
AUTH_MAX_ATTEMPTS=10
AUTH_LOCKOUT_MINUTES=15
AUTH_SESSION_HOURS=24

# Feature Toggles (all overridable via dashboard)
ENABLE_ALPR=true
ENABLE_GEOFENCING=false
ENABLE_DELIVERY_MODE=false
ENABLE_NOTIFICATIONS=true
ENABLE_VACATION_MODE=false
ENABLE_TAMPER_DETECTION=true
ENABLE_VOICE_CONTROL=false
ENABLE_NIGHT_CAMERA=true
ENABLE_CLIMATE_MONITOR=false
ENABLE_MULTI_DOOR=false
ENABLE_GUEST_ACCESS=false
ENABLE_UPS_MONITOR=false
ENABLE_AUTO_CLOSE=true
ENABLE_ANALYTICS=true
ENABLE_EMERGENCY_LOCK=true

# ALPR
ALPR_CONFIDENCE_THRESHOLD=75
ALPR_REGION=eu
ALPR_CHECK_INTERVAL_SEC=2

# Geofencing
GEOFENCE_RADIUS_METERS=50
GEOFENCE_API_KEY=

# Notifications — Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Notifications — Slack
SLACK_WEBHOOK_URL=

# Notifications — Teams
TEAMS_WEBHOOK_URL=

# Notifications — Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_TO=

# Auto-Close
AUTO_CLOSE_DELAY_SEC=300

# Vacation Mode
VACATION_MIN_INTERVAL_MIN=60
VACATION_MAX_INTERVAL_MIN=240

# Camera
CAMERA_RESOLUTION=1280x720
CAMERA_FPS=15
NIGHT_IR_GPIO=18

# GPIO Pins
RELAY_DOOR1_GPIO=17
RELAY_DOOR2_GPIO=27
REED_DOOR1_GPIO=22
REED_DOOR2_GPIO=23
VIBRATION_GPIO=24
EMERGENCY_BTN_GPIO=25
DHT22_GPIO=4

# UPS Monitor
UPS_I2C_ADDRESS=0x40
UPS_LOW_BATTERY_PCT=15

# Database
DB_PATH=data/garage.db
```

---

## 🌐 Web Dashboard

Dark-theme responsive dashboard with real-time WebSocket updates:

| Page | Description |
|------|-------------|
| **Dashboard** | Door status cards, last 10 events, quick-action buttons |
| **Live Camera** | MJPEG stream with ALPR overlay boxes |
| **Access Log** | Searchable table of all open/close events with plate photos |
| **Guest Codes** | Generate, revoke, and monitor temporary access codes |
| **Analytics** | Charts: daily usage, peak hours, month-over-month trends |
| **Climate** | Real-time temperature, humidity, CO graphs |
| **Settings** | Feature toggles, GPIO config, notification setup, user management |
| **Emergency** | One-click lock-all, alarm trigger, instant notification blast |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate and receive JWT |
| `GET` | `/api/doors` | List all doors with current status |
| `POST` | `/api/doors/<id>/open` | Open specific door |
| `POST` | `/api/doors/<id>/close` | Close specific door |
| `POST` | `/api/doors/lock-all` | Emergency lock all doors |
| `GET` | `/api/events` | Paginated event history |
| `GET` | `/api/alpr/whitelist` | List whitelisted plates |
| `POST` | `/api/alpr/whitelist` | Add plate to whitelist |
| `DELETE` | `/api/alpr/whitelist/<plate>` | Remove plate |
| `POST` | `/api/guest/generate` | Create temporary access code |
| `GET` | `/api/climate` | Current climate readings |
| `GET` | `/api/analytics/summary` | Usage analytics JSON |
| `GET` | `/api/settings/features` | Get all feature toggle states |
| `PUT` | `/api/settings/features` | Update feature toggles via dashboard |
| `GET` | `/api/ups/status` | Battery/UPS status |

---

## 💰 Budget Estimate

| Tier | Components | Cost |
|------|-----------|------|
| **Basic** | Pi 4 + Relay + Reed Switch + Camera | ~$85 |
| **Standard** | + DHT22 + Vibration + IR LEDs + UPS HAT | ~$115 |
| **Full** | + CO sensor + INA219 + Multi-door relays + Servo | ~$145 |

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🪙 Donations

If you find this project helpful, you can support my work:

₿ **Bitcoin:** `bc1q...`
