# 🐶 Smart Pet Feeder & Health Monitor

A Raspberry Pi–powered automated pet feeding and health monitoring system with facial recognition for multi-pet households, weight tracking, behavioral health alerts, and a responsive dark-theme web dashboard with per-feature toggle switches.

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
| 1 | **Scheduled & On-Demand Feeding** — Cron-based auto-dispense + manual feed from dashboard/app | `ENABLE_SCHEDULED_FEEDING=true` | `true` |
| 2 | **Portion Size Control** — Calibrated servo rotation for precise gram-based portions | `ENABLE_PORTION_CONTROL=true` | `true` |
| 3 | **Pet Facial Recognition** — Pi Camera identifies which pet is at the bowl using TFLite model | `ENABLE_PET_RECOGNITION=true` | `false` |
| 4 | **Multi-Pet Profiles** — Individual feeding schedules, portion sizes, and dietary restrictions per pet | `ENABLE_MULTI_PET=true` | `false` |
| 5 | **RFID Collar Tag Anti-Theft Feeding** — RC522 reads collar tags to authorize feeding per pet | `ENABLE_RFID_FEEDING=true` | `false` |
| 6 | **Pet Weight Tracking** — HX711 load cell under bowl tracks weight trends over time | `ENABLE_WEIGHT_TRACKING=true` | `false` |
| 7 | **Eating Speed Analysis** — Monitors bowl weight decrease rate and triggers slow-feed mode | `ENABLE_EATING_ANALYSIS=true` | `false` |
| 8 | **Behavioral Health Alerts** — Detects missed meals, overeating, weight anomalies; sends alerts | `ENABLE_HEALTH_ALERTS=true` | `true` |
| 9 | **Water Level Monitoring** — Ultrasonic sensor tracks water bowl level with auto-refill alerts | `ENABLE_WATER_MONITOR=true` | `true` |
| 10 | **Food Hopper Level Sensor** — IR proximity sensor monitors remaining food in hopper | `ENABLE_HOPPER_MONITOR=true` | `true` |
| 11 | **Treat Launcher Mini-Game** — Remote-controlled servo launcher for interactive play | `ENABLE_TREAT_LAUNCHER=true` | `false` |
| 12 | **Medication Dispenser** — Secondary servo dispenses medication at scheduled times | `ENABLE_MEDICATION=true` | `false` |
| 13 | **Live Camera Feed** — MJPEG stream with IR night vision to watch pets remotely | `ENABLE_LIVE_CAMERA=true` | `true` |
| 14 | **Two-Way Audio** — Microphone + speaker for remote pet interaction | `ENABLE_TWO_WAY_AUDIO=true` | `false` |
| 15 | **Activity/Motion Detection** — PIR sensor detects pet activity near feeder | `ENABLE_MOTION_DETECT=true` | `false` |
| 16 | **Feeding Analytics & Vet Export** — Historical charts + CSV/PDF export for veterinarian visits | `ENABLE_ANALYTICS=true` | `true` |

---

## 🎛️ Dashboard Feature Toggles

The web dashboard provides a **Settings → Feature Toggles** page where each feature can be enabled/disabled in real time without restarting the service:

```
┌──────────────────────────────────────────────────┐
│  ⚙️ Feature Toggles              [Save All]      │
├──────────────────────────────────────────────────┤
│  🍽️ Scheduled Feeding          [████ ON ]        │
│  ⚖️ Portion Control            [████ ON ]        │
│  🐾 Pet Facial Recognition     [░░░░ OFF]        │
│  👥 Multi-Pet Profiles         [░░░░ OFF]        │
│  📡 RFID Anti-Theft Feeding    [░░░░ OFF]        │
│  ⚖️ Weight Tracking            [░░░░ OFF]        │
│  🍴 Eating Speed Analysis      [░░░░ OFF]        │
│  🚨 Health Alerts              [████ ON ]        │
│  💧 Water Level Monitor        [████ ON ]        │
│  📦 Hopper Level Monitor       [████ ON ]        │
│  🎯 Treat Launcher             [░░░░ OFF]        │
│  💊 Medication Dispenser       [░░░░ OFF]        │
│  📷 Live Camera                [████ ON ]        │
│  🔊 Two-Way Audio              [░░░░ OFF]        │
│  🏃 Motion Detection           [░░░░ OFF]        │
│  📊 Analytics & Export         [████ ON ]        │
└──────────────────────────────────────────────────┘
```

---

## 🔩 Hardware Requirements

| Component | Model / Spec | Qty | Est. Cost |
|-----------|-------------|-----|-----------|
| Raspberry Pi | 4B (2GB+) or 5 | 1 | $45–75 |
| Pi Camera Module | V2 or V3 (IR night vision) | 1 | $25–35 |
| Servo Motor (Food) | MG996R continuous rotation | 1 | $5–8 |
| Servo Motor (Treat) | SG90 micro servo | 1 | $3 |
| Servo Motor (Medication) | SG90 micro servo | 1 | $3 |
| HX711 + Load Cell | 5kg strain gauge kit | 1 | $6–10 |
| HC-SR04 | Ultrasonic distance (water level) | 1 | $3 |
| IR Proximity Sensor | E18-D80NK (hopper level) | 1 | $4 |
| MFRC522 | RFID reader + collar tags | 1 | $5–8 |
| PIR Motion Sensor | HC-SR501 | 1 | $2 |
| USB Microphone | Mini USB mic | 1 | $5 |
| Speaker | 3W mini speaker + PAM8403 amp | 1 | $4 |
| IR LED Array | Night illumination | 1 | $3 |
| DHT22 | Food area temperature monitoring | 1 | $4–6 |
| MicroSD Card | 32GB+ Class 10 | 1 | $8 |
| Power Supply | 5V 3A USB-C | 1 | $10 |
| 3D-Printed Housing | Hopper + funnel + bowl mount | 1 | DIY |
| **Total** | | | **$75–140** |

---

## 🔌 Wiring Diagram

```
Raspberry Pi 4/5 GPIO
┌─────────────────────────────────────────┐
│  GPIO 12 (PWM) ── Servo Food Dispenser  │
│  GPIO 13 (PWM) ── Servo Treat Launcher  │
│  GPIO 19 (PWM) ── Servo Medication      │
│  GPIO 5  ──────── HX711 DT (Load Cell)  │
│  GPIO 6  ──────── HX711 SCK             │
│  GPIO 23 ──────── HC-SR04 TRIG (Water)  │
│  GPIO 24 ──────── HC-SR04 ECHO (Water)  │
│  GPIO 25 ──────── IR Prox (Hopper)      │
│  GPIO 17 ──────── PIR Motion Sensor     │
│  GPIO 4  ──────── DHT22 Data            │
│  GPIO 18 ──────── IR LED Control        │
│  SPI MOSI ─────── MFRC522 MOSI          │
│  SPI MISO ─────── MFRC522 MISO          │
│  SPI SCLK ─────── MFRC522 SCK           │
│  SPI CE0  ─────── MFRC522 SDA           │
│  GPIO 22 ──────── MFRC522 RST           │
│  CSI Port ─────── Pi Camera Module      │
│  USB Port ─────── USB Microphone        │
│  3.5mm / GPIO ─── Speaker + PAM8403     │
│  3.3V / 5V ───── Sensor VCC rails       │
│  GND ──────────── Common ground bus     │
└─────────────────────────────────────────┘
```

---

## 💻 Software Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask, Flask-SocketIO |
| Frontend | HTML5, CSS3 (dark theme), JavaScript, Chart.js |
| Database | SQLite (pets, feedings, weights, settings) |
| Camera | picamera2 / OpenCV |
| Pet Recognition | TensorFlow Lite (MobileNetV2 transfer learning) |
| RFID | mfrc522 (SPI) |
| Load Cell | HX711 Python library |
| Auth | bcrypt hashing, 10 attempts/15min rate limit, 24h JWT sessions |
| Notifications | python-telegram-bot, slack-sdk, smtplib |
| Audio | PyAudio (mic) + pygame (speaker) |
| Real-time | WebSocket via Flask-SocketIO |
| Process Manager | systemd service |

---

## 🚀 Installation

### 1. Clone & setup
```bash
ssh rasp-pi
cd /opt
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Home & IoT Automation Projects/Smart Pet Feeder & Health Monitor"
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
nano .env
```

### 4. Calibrate load cell
```bash
python3 calibrate_scale.py  # Follow on-screen instructions with known weight
```

### 5. Train pet recognition (optional)
```bash
python3 train_pet_model.py --photos data/pet_photos/ --epochs 20
```

### 6. Initialize database & run
```bash
python3 init_db.py
sudo cp deploy/pet-feeder.service /etc/systemd/system/
sudo systemctl enable pet-feeder && sudo systemctl start pet-feeder
```

### 7. Access dashboard
```
https://<raspberry-ip>:5000
Default login: admin / changeme (force-change on first login)
```

---

## 🔐 Environment Variables

Full `.env.default` template:

```env
# ──────────────────────────────────────
# Smart Pet Feeder & Health Monitor
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
ENABLE_SCHEDULED_FEEDING=true
ENABLE_PORTION_CONTROL=true
ENABLE_PET_RECOGNITION=false
ENABLE_MULTI_PET=false
ENABLE_RFID_FEEDING=false
ENABLE_WEIGHT_TRACKING=false
ENABLE_EATING_ANALYSIS=false
ENABLE_HEALTH_ALERTS=true
ENABLE_WATER_MONITOR=true
ENABLE_HOPPER_MONITOR=true
ENABLE_TREAT_LAUNCHER=false
ENABLE_MEDICATION=false
ENABLE_LIVE_CAMERA=true
ENABLE_TWO_WAY_AUDIO=false
ENABLE_MOTION_DETECT=false
ENABLE_ANALYTICS=true

# Feeding
DEFAULT_PORTION_GRAMS=50
FEED_TIMES=08:00,18:00
SLOW_FEED_THRESHOLD_G_PER_SEC=5

# GPIO Pins
SERVO_FOOD_GPIO=12
SERVO_TREAT_GPIO=13
SERVO_MEDICATION_GPIO=19
HX711_DT_GPIO=5
HX711_SCK_GPIO=6
ULTRASONIC_TRIG_GPIO=23
ULTRASONIC_ECHO_GPIO=24
HOPPER_IR_GPIO=25
PIR_GPIO=17
DHT22_GPIO=4
IR_LED_GPIO=18
RFID_RST_GPIO=22

# Load Cell
LOAD_CELL_CALIBRATION_FACTOR=420.5
LOAD_CELL_OFFSET=8340

# Water Level
WATER_LOW_THRESHOLD_CM=3
WATER_FULL_CM=15

# Hopper
HOPPER_LOW_THRESHOLD=true
HOPPER_REFILL_ALERT=true

# Pet Recognition
PET_MODEL_PATH=models/pet_model.tflite
PET_CONFIDENCE_THRESHOLD=70

# Notifications — Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Notifications — Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_TO=

# Health Alerts
MISSED_MEAL_THRESHOLD_HOURS=4
WEIGHT_CHANGE_ALERT_PCT=10
OVEREATING_MULTIPLIER=1.5

# Medication
MEDICATION_TIMES=09:00
MEDICATION_PORTION_MG=250

# Camera
CAMERA_RESOLUTION=1280x720
CAMERA_FPS=15

# Audio
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_VOLUME=80

# Database
DB_PATH=data/petfeeder.db
```

---

## 🌐 Web Dashboard

Dark-theme responsive dashboard with real-time WebSocket updates:

| Page | Description |
|------|-------------|
| **Dashboard** | Pet status cards, next feed countdown, quick-feed buttons |
| **Pet Profiles** | Add/edit pets with photo, diet, portion, schedule |
| **Feeding Log** | Timestamped feeding history per pet with portion details |
| **Weight Chart** | Historical weight graph per pet with trend line |
| **Health Alerts** | Active alerts (missed meals, weight anomalies, low water) |
| **Live Camera** | MJPEG stream + two-way audio controls |
| **Treat Game** | Manual treat launcher with camera view |
| **Analytics** | Feeding patterns, consumption charts, vet export buttons |
| **Settings** | Feature toggles, GPIO config, notification setup, calibration |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate and receive JWT |
| `GET` | `/api/pets` | List all pet profiles |
| `POST` | `/api/pets` | Create pet profile |
| `PUT` | `/api/pets/<id>` | Update pet profile |
| `DELETE` | `/api/pets/<id>` | Delete pet profile |
| `POST` | `/api/feed/now` | Trigger immediate feeding |
| `GET` | `/api/feed/schedule` | Get feeding schedule |
| `PUT` | `/api/feed/schedule` | Update feeding schedule |
| `GET` | `/api/feed/log` | Feeding history (paginated) |
| `GET` | `/api/weight/<pet_id>` | Weight history for a pet |
| `GET` | `/api/water/level` | Current water level |
| `GET` | `/api/hopper/level` | Current hopper fill level |
| `POST` | `/api/treat/launch` | Fire treat launcher |
| `POST` | `/api/medication/dispense` | Dispense medication |
| `GET` | `/api/health/alerts` | Active health alerts |
| `GET` | `/api/analytics/summary` | Feeding analytics JSON |
| `GET` | `/api/analytics/export?format=csv` | Export vet report |
| `GET` | `/api/settings/features` | Get all feature toggle states |
| `PUT` | `/api/settings/features` | Update feature toggles via dashboard |
| `GET` | `/api/camera/stream` | Authenticated MJPEG stream |

---

## 💰 Budget Estimate

| Tier | Components | Cost |
|------|-----------|------|
| **Basic** | Pi 4 + Servo + Camera + HC-SR04 | ~$75 |
| **Standard** | + HX711 + RFID + PIR + DHT22 + Hopper sensor | ~$105 |
| **Full** | + Treat servo + Medication servo + Mic + Speaker + IR LEDs | ~$140 |

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🪙 Donations

If you find this project helpful, you can support my work:

₿ **Bitcoin:** `bc1q...`
