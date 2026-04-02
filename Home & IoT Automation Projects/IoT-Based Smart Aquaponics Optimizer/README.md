# 🐟 IoT-Based Smart Aquaponics Optimizer

A Raspberry Pi–powered aquaponics automation platform combining pH/EC/DO sensors, predictive ammonia prevention, plant health CNN, automated nutrient dosing, fish counting, and solar integration — all managed from a dark-theme web dashboard with InfluxDB + Grafana visualization and per-feature toggle switches.

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
| 1 | **pH Monitoring & Auto-Dosing** — Atlas Scientific pH probe with peristaltic pump pH-up/down | `ENABLE_PH_MONITOR=true` | `true` |
| 2 | **EC (Electrical Conductivity) Monitoring** — Nutrient concentration tracking with alerts | `ENABLE_EC_MONITOR=true` | `true` |
| 3 | **Dissolved Oxygen (DO) Sensor** — Real-time O₂ levels critical for fish health | `ENABLE_DO_MONITOR=true` | `true` |
| 4 | **Water Temperature Control** — DS18B20 probe + heater/chiller relay for thermal regulation | `ENABLE_TEMP_CONTROL=true` | `true` |
| 5 | **Ammonia/Nitrite/Nitrate Prediction** — ML model predicts toxic spikes 6–12h ahead from sensor trends | `ENABLE_AMMONIA_PREDICT=true` | `false` |
| 6 | **Plant Health CNN** — Pi Camera analyzes leaf color/shape for disease, nutrient deficiency detection | `ENABLE_PLANT_HEALTH=true` | `false` |
| 7 | **Fish Counter (Vision)** — OpenCV blob detection counts fish and tracks population trends | `ENABLE_FISH_COUNTER=true` | `false` |
| 8 | **Fish Feeding Auto-Dispenser** — Servo-based automated fish feeder with configurable schedule | `ENABLE_FISH_FEEDER=true` | `true` |
| 9 | **Auto Nutrient Dosing** — Peristaltic pumps for automated macro/micro nutrient delivery | `ENABLE_NUTRIENT_DOSING=true` | `false` |
| 10 | **Grow Light Spectrum & Schedule** — PWM control of LED grow lights with photoperiod scheduling | `ENABLE_GROW_LIGHTS=true` | `true` |
| 11 | **Water Flow Rate Monitoring** — YF-S201 flow sensor tracks circulation pump performance | `ENABLE_FLOW_MONITOR=true` | `true` |
| 12 | **Water Level with Auto Top-Off** — Ultrasonic sensor + solenoid valve for automatic refill | `ENABLE_WATER_LEVEL=true` | `true` |
| 13 | **Air Pump Control** — Relay-controlled aeration with day/night scheduling | `ENABLE_AIR_PUMP=true` | `true` |
| 14 | **Solar Panel Integration** — INA219 monitors solar power generation and battery storage | `ENABLE_SOLAR_MONITOR=true` | `false` |
| 15 | **InfluxDB + Grafana Dashboards** — Time-series storage with professional visualization | `ENABLE_INFLUXDB=true` | `false` |
| 16 | **System Health Score Engine** — 0–100 composite score from all sensor readings | `ENABLE_HEALTH_SCORE=true` | `true` |
| 17 | **Predictive Maintenance Alerts** — Detects pump degradation, sensor drift, filter clogging | `ENABLE_PREDICTIVE_MAINT=true` | `false` |
| 18 | **Multi-Bed / Multi-Tank Support** — Manage up to 4 grow beds and 2 fish tanks independently | `ENABLE_MULTI_SYSTEM=true` | `false` |
| 19 | **Weather API Integration** — Outdoor conditions influence indoor climate decisions | `ENABLE_WEATHER_API=true` | `false` |
| 20 | **Harvest Tracking & Yield Prediction** — Log harvests, predict next yield using growth models | `ENABLE_HARVEST_TRACKING=true` | `false` |

---

## 🎛️ Dashboard Feature Toggles

The web dashboard provides a **Settings → Feature Toggles** page where each feature can be enabled/disabled in real time without restarting the service:

```
┌──────────────────────────────────────────────────────┐
│  ⚙️ Feature Toggles                  [Save All]      │
├──────────────────────────────────────────────────────┤
│  🧪 pH Monitor & Auto-Dosing       [████ ON ]        │
│  ⚡ EC Monitor                     [████ ON ]        │
│  💨 Dissolved Oxygen Monitor       [████ ON ]        │
│  🌡️ Temperature Control            [████ ON ]        │
│  🔮 Ammonia Prediction Engine      [░░░░ OFF]        │
│  🌿 Plant Health CNN               [░░░░ OFF]        │
│  🐠 Fish Counter (Vision)          [░░░░ OFF]        │
│  🍽️ Fish Feeding Dispenser         [████ ON ]        │
│  💧 Auto Nutrient Dosing           [░░░░ OFF]        │
│  💡 Grow Light Control             [████ ON ]        │
│  🌊 Water Flow Monitor             [████ ON ]        │
│  📏 Water Level & Auto Top-Off     [████ ON ]        │
│  🫧 Air Pump Control               [████ ON ]        │
│  ☀️ Solar Panel Monitor             [░░░░ OFF]        │
│  📊 InfluxDB + Grafana             [░░░░ OFF]        │
│  💯 System Health Score            [████ ON ]        │
│  🔧 Predictive Maintenance         [░░░░ OFF]        │
│  🏗️ Multi-Bed / Multi-Tank         [░░░░ OFF]        │
│  🌤️ Weather API Integration        [░░░░ OFF]        │
│  🌾 Harvest Tracking               [░░░░ OFF]        │
└──────────────────────────────────────────────────────┘
```

---

## 🔩 Hardware Requirements

| Component | Model / Spec | Qty | Est. Cost |
|-----------|-------------|-----|-----------|
| Raspberry Pi | 4B (4GB+) or 5 | 1 | $55–80 |
| Atlas Scientific pH Kit | pH probe + EZO circuit (I2C) | 1 | $60–80 |
| Atlas Scientific EC Kit | EC probe + EZO circuit (I2C) | 1 | $60–80 |
| Atlas Scientific DO Kit | DO probe + EZO circuit (I2C) | 1 | $60–80 |
| DS18B20 | Waterproof temperature probe | 2–4 | $3–5 each |
| Pi Camera Module | V2 or V3 | 1 | $25–35 |
| Peristaltic Pumps | 12V dosing pumps (pH/nutrients) | 2–4 | $8–12 each |
| Relay Module | 5V 8-channel | 1 | $6–8 |
| YF-S201 | Water flow sensor | 1 | $5 |
| HC-SR04 | Ultrasonic distance (water level) | 1–2 | $3 each |
| Solenoid Valve | 12V NC (auto top-off) | 1 | $8 |
| Servo Motor | SG90 (fish feeder) | 1 | $3 |
| LED Grow Light | 12V strip with MOSFET dimmer | 1 | $15–25 |
| INA219 Module | Solar power monitor | 1 | $3 |
| Air Pump + Relay | Aquarium air pump | 1 | $8–12 |
| Heater + Relay | Aquarium heater (if cold climate) | 1 | $10–15 |
| 12V Power Supply | For pumps, solenoid, lights | 1 | $10 |
| MicroSD Card | 64GB+ Class 10 (for InfluxDB) | 1 | $10 |
| Power Supply | 5V 3A USB-C (Pi) | 1 | $10 |
| **Total** | | | **$120–280** |

> **Note:** Atlas Scientific kits are professional-grade. Budget alternatives: analog pH/EC modules ($5–10 each) via MCP3008 ADC, with reduced accuracy.

---

## 🔌 Wiring Diagram

```
Raspberry Pi 4/5 GPIO
┌──────────────────────────────────────────────────┐
│  I2C SDA/SCL ── Atlas pH EZO (0x63)             │
│  I2C SDA/SCL ── Atlas EC EZO (0x64)             │
│  I2C SDA/SCL ── Atlas DO EZO (0x61)             │
│  I2C SDA/SCL ── INA219 Solar (0x40)             │
│  GPIO 4 (1-Wire) ── DS18B20 Temp Probes (bus)   │
│  GPIO 17 ──── Relay CH1: Heater                  │
│  GPIO 27 ──── Relay CH2: Chiller/Fan             │
│  GPIO 22 ──── Relay CH3: Air Pump                │
│  GPIO 23 ──── Relay CH4: Circulation Pump        │
│  GPIO 24 ──── Relay CH5: Solenoid Valve          │
│  GPIO 25 ──── Relay CH6: Peristaltic Pump 1 (pH) │
│  GPIO 5  ──── Relay CH7: Peristaltic Pump 2 (nut)│
│  GPIO 6  ──── Relay CH8: Peristaltic Pump 3      │
│  GPIO 12 (PWM) ── LED Grow Light (MOSFET gate)   │
│  GPIO 13 (PWM) ── Servo Fish Feeder              │
│  GPIO 16 ──── YF-S201 Flow Sensor (pulse)        │
│  GPIO 20 ──── HC-SR04 TRIG (Tank 1)              │
│  GPIO 21 ──── HC-SR04 ECHO (Tank 1)              │
│  CSI Port ──── Pi Camera Module                   │
│  3.3V / 5V ─── Sensor VCC rails                  │
│  GND ────────── Common ground bus                 │
└──────────────────────────────────────────────────┘
```

---

## 💻 Software Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask, Flask-SocketIO |
| Frontend | HTML5, CSS3 (dark theme), JavaScript, Chart.js |
| Database (relational) | SQLite (users, configs, harvests, alerts) |
| Database (time-series) | InfluxDB 2.x (sensor readings) |
| Visualization | Grafana (optional, embedded iframes) |
| Camera | picamera2 / OpenCV |
| Plant Health AI | TensorFlow Lite (MobileNetV2 transfer learning) |
| Fish Counter | OpenCV blob detection / contour analysis |
| Ammonia Prediction | scikit-learn (RandomForest/LSTM on sensor history) |
| Atlas Sensors | atlas-i2c Python library |
| Auth | bcrypt hashing, 10 attempts/15min rate limit, 24h JWT sessions |
| Notifications | python-telegram-bot, slack-sdk, smtplib |
| Scheduling | APScheduler (feeding, dosing, lights) |
| Real-time | WebSocket via Flask-SocketIO |
| Process Manager | systemd service |

---

## 🚀 Installation

### 1. Clone & setup
```bash
ssh rasp-pi
cd /opt
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Home & IoT Automation Projects/IoT-Based Smart Aquaponics Optimizer"
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
nano .env  # Configure sensor addresses, GPIO pins, thresholds
```

### 4. Calibrate sensors
```bash
python3 calibrate_ph.py     # Follow Atlas pH calibration (pH 4, 7, 10)
python3 calibrate_ec.py     # EC dry/wet calibration
python3 calibrate_do.py     # DO atmospheric calibration
```

### 5. Install InfluxDB (optional)
```bash
sudo apt install influxdb2
sudo systemctl enable influxdb2
influx setup  # Create org, bucket, token
```

### 6. Install Grafana (optional)
```bash
sudo apt install grafana
sudo systemctl enable grafana-server
# Configure InfluxDB datasource at http://<pi-ip>:3000
```

### 7. Train plant health model (optional)
```bash
python3 train_plant_model.py --photos data/plant_photos/ --epochs 30
```

### 8. Initialize database & run
```bash
python3 init_db.py
sudo cp deploy/aquaponics.service /etc/systemd/system/
sudo systemctl enable aquaponics && sudo systemctl start aquaponics
```

### 9. Access dashboard
```
https://<raspberry-ip>:5000
Default login: admin / changeme (force-change on first login)
Grafana: http://<raspberry-ip>:3000 (optional)
```

---

## 🔐 Environment Variables

Full `.env.default` template:

```env
# ──────────────────────────────────────
# IoT-Based Smart Aquaponics Optimizer
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
ENABLE_PH_MONITOR=true
ENABLE_EC_MONITOR=true
ENABLE_DO_MONITOR=true
ENABLE_TEMP_CONTROL=true
ENABLE_AMMONIA_PREDICT=false
ENABLE_PLANT_HEALTH=false
ENABLE_FISH_COUNTER=false
ENABLE_FISH_FEEDER=true
ENABLE_NUTRIENT_DOSING=false
ENABLE_GROW_LIGHTS=true
ENABLE_FLOW_MONITOR=true
ENABLE_WATER_LEVEL=true
ENABLE_AIR_PUMP=true
ENABLE_SOLAR_MONITOR=false
ENABLE_INFLUXDB=false
ENABLE_HEALTH_SCORE=true
ENABLE_PREDICTIVE_MAINT=false
ENABLE_MULTI_SYSTEM=false
ENABLE_WEATHER_API=false
ENABLE_HARVEST_TRACKING=false

# Atlas Scientific I2C Addresses
PH_I2C_ADDRESS=0x63
EC_I2C_ADDRESS=0x64
DO_I2C_ADDRESS=0x61

# pH Thresholds & Dosing
PH_TARGET=6.8
PH_TOLERANCE=0.3
PH_CHECK_INTERVAL_SEC=60
PH_DOSE_ML=2
PH_UP_PUMP_GPIO=25
PH_DOWN_PUMP_GPIO=5

# EC Thresholds
EC_TARGET_US=1200
EC_TOLERANCE_US=200
EC_CHECK_INTERVAL_SEC=120

# DO Thresholds
DO_MIN_MG_L=5.0
DO_CRITICAL_MG_L=3.0

# Temperature
TEMP_TARGET_C=24.0
TEMP_TOLERANCE_C=2.0
TEMP_SENSOR_IDS=28-xxxxxxxxxxxx,28-yyyyyyyyyyyy
HEATER_GPIO=17
CHILLER_GPIO=27

# Fish Feeder
FISH_FEED_TIMES=08:00,18:00
FISH_FEED_SERVO_GPIO=13
FISH_FEED_DURATION_SEC=1.5

# Grow Lights
GROW_LIGHT_GPIO=12
LIGHT_ON_TIME=06:00
LIGHT_OFF_TIME=22:00
LIGHT_INTENSITY_PCT=80

# Water Flow
FLOW_SENSOR_GPIO=16
FLOW_LOW_THRESHOLD_LPM=2.0

# Water Level
WATER_TRIG_GPIO=20
WATER_ECHO_GPIO=21
WATER_LOW_THRESHOLD_CM=5
WATER_FULL_CM=30
TOPOFF_SOLENOID_GPIO=24
TOPOFF_MAX_SEC=60

# Air Pump
AIR_PUMP_GPIO=22
AIR_ON_TIME=06:00
AIR_OFF_TIME=22:00

# Nutrient Dosing
NUTRIENT_PUMP1_GPIO=5
NUTRIENT_PUMP2_GPIO=6
NUTRIENT_DOSE_ML=5
NUTRIENT_INTERVAL_HOURS=24

# Solar Monitor
SOLAR_INA219_ADDRESS=0x40

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=
INFLUXDB_ORG=aquaponics
INFLUXDB_BUCKET=sensors

# Weather API
WEATHER_API_KEY=
WEATHER_CITY=
WEATHER_CHECK_INTERVAL_MIN=30

# Plant Health
PLANT_MODEL_PATH=models/plant_model.tflite
PLANT_CHECK_INTERVAL_MIN=60
PLANT_CONFIDENCE_THRESHOLD=70

# Ammonia Prediction
AMMONIA_MODEL_PATH=models/ammonia_predictor.pkl
AMMONIA_PREDICT_HOURS=12

# Health Score Weights
HEALTH_WEIGHT_PH=20
HEALTH_WEIGHT_TEMP=20
HEALTH_WEIGHT_DO=20
HEALTH_WEIGHT_EC=15
HEALTH_WEIGHT_FLOW=15
HEALTH_WEIGHT_LEVEL=10

# Notifications — Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Notifications — Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_TO=

# Database
DB_PATH=data/aquaponics.db
```

---

## 🌐 Web Dashboard

Dark-theme responsive dashboard with real-time WebSocket updates:

| Page | Description |
|------|-------------|
| **Dashboard** | System health score (0–100), sensor gauges, quick-action buttons |
| **Water Chemistry** | pH, EC, DO real-time graphs with threshold bands |
| **Temperature** | Multi-probe temperature chart with heater/chiller status |
| **Fish Tank** | Fish count, feeding schedule, live camera feed |
| **Grow Beds** | Plant health status, nutrient levels, grow light schedule |
| **Water System** | Flow rate, water level, air pump, top-off status |
| **Dosing Control** | Manual/auto dosing controls, dosing history log |
| **Solar & Energy** | Solar generation, battery charge, energy consumption |
| **Predictions** | Ammonia forecast, yield prediction, maintenance schedule |
| **Harvest Log** | Record harvests, view yield trends, crop planning |
| **Grafana** | Embedded InfluxDB Grafana dashboards (iframe) |
| **Alerts** | Active alerts with acknowledge, notification preferences |
| **Settings** | Feature toggles, sensor calibration, GPIO config, schedules |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate and receive JWT |
| `GET` | `/api/sensors/current` | All current sensor readings |
| `GET` | `/api/sensors/ph/history?hours=24` | pH time-series data |
| `GET` | `/api/sensors/ec/history?hours=24` | EC time-series data |
| `GET` | `/api/sensors/do/history?hours=24` | DO time-series data |
| `GET` | `/api/sensors/temp/history?hours=24` | Temperature time-series |
| `GET` | `/api/water/flow` | Current flow rate |
| `GET` | `/api/water/level` | Current water level |
| `POST` | `/api/water/topoff` | Trigger manual top-off |
| `POST` | `/api/dosing/ph-up` | Manual pH-up dose |
| `POST` | `/api/dosing/ph-down` | Manual pH-down dose |
| `POST` | `/api/dosing/nutrients` | Manual nutrient dose |
| `GET` | `/api/dosing/log` | Dosing history |
| `POST` | `/api/fish/feed` | Trigger fish feeding |
| `GET` | `/api/fish/count` | Current fish count |
| `GET` | `/api/fish/feed-log` | Feeding history |
| `GET` | `/api/plants/health` | Plant health assessment |
| `GET` | `/api/lights/status` | Grow light current state |
| `PUT` | `/api/lights/schedule` | Update light schedule |
| `PUT` | `/api/lights/intensity` | Set light intensity % |
| `GET` | `/api/health-score` | System health score (0–100) |
| `GET` | `/api/predictions/ammonia` | Ammonia prediction data |
| `GET` | `/api/predictions/yield` | Yield prediction data |
| `GET` | `/api/solar/status` | Solar power status |
| `GET` | `/api/weather` | Current weather data |
| `POST` | `/api/harvest/log` | Record a harvest |
| `GET` | `/api/harvest/history` | Harvest history + trends |
| `GET` | `/api/alerts` | Active alerts |
| `PUT` | `/api/alerts/<id>/acknowledge` | Acknowledge alert |
| `GET` | `/api/maintenance/schedule` | Predictive maintenance tasks |
| `GET` | `/api/settings/features` | Get all feature toggle states |
| `PUT` | `/api/settings/features` | Update feature toggles via dashboard |
| `GET` | `/api/analytics/export?format=csv` | Export all data as CSV |

---

## 💰 Budget Estimate

| Tier | Components | Cost |
|------|-----------|------|
| **Basic** | Pi 4 + DS18B20 + Relays + Servo feeder + HC-SR04 + Flow sensor | ~$120 |
| **Standard** | + Atlas pH kit + Grow LEDs + Air pump + Dosing pumps + Camera | ~$200 |
| **Professional** | + Atlas EC + DO kits + INA219 + InfluxDB + Grafana + Solenoid | ~$280 |

> Budget option: Replace Atlas Scientific kits with analog modules (DFRobot pH ~$30, analog EC ~$25) + MCP3008 ADC (~$5). Reduces total by $100–150 but with lower accuracy.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🪙 Donations

If you find this project helpful, you can support my work:

₿ **Bitcoin:** `bc1q...`
