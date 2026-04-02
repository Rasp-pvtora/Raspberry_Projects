# 🧾 GPIO Data Logger & Pin Manager

A Raspberry Pi–powered GPIO data logging and pin management system with a configurable pin assignment file, multi-format data storage (CSV/JSON/SQLite), analog ADC support via MCP3008, threshold alerting, and real-time Chart.js visualization — all managed from a responsive dark-theme web dashboard with per-feature toggle switches.

---

## 📋 Table of Contents
- [Features](#-features)
- [Dashboard Feature Toggles](#-dashboard-feature-toggles)
- [Hardware Requirements](#-hardware-requirements)
- [Wiring Diagram](#-wiring-diagram)
- [Software Stack](#-software-stack)
- [Installation](#-installation)
- [Environment Variables](#-environment-variables)
- [Pin Configuration File](#-pin-configuration-file)
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
| 1 | **Pin Configuration File** — JSON file where operator names and activates/deactivates each pin (e.g., "PIN 4 = Sensor Temperature B100") | `ENABLE_PIN_CONFIG=true` | `true` |
| 2 | **Web Dashboard Pin Manager** — Visual GPIO layout to assign, rename, enable/disable pins with drag-and-drop grouping | `ENABLE_PIN_MANAGER=true` | `true` |
| 3 | **Multi-Format Logging (CSV)** — Log sensor readings to CSV files with configurable rotation | `ENABLE_CSV_LOGGING=true` | `true` |
| 4 | **Multi-Format Logging (JSON)** — Log sensor readings to newline-delimited JSON files | `ENABLE_JSON_LOGGING=true` | `false` |
| 5 | **SQLite Database Logging** — Store all readings in SQLite with full query and aggregation support | `ENABLE_SQLITE_LOGGING=true` | `true` |
| 6 | **Configurable Polling Intervals** — Per-pin polling rate from 100ms to 1h with scheduler | `ENABLE_CUSTOM_POLLING=true` | `true` |
| 7 | **MCP3008 ADC Analog Support** — Read analog sensors (temperature, light, moisture) via SPI MCP3008 | `ENABLE_ADC=true` | `false` |
| 8 | **Threshold Alerts** — Per-pin configurable high/low thresholds with multi-channel notifications | `ENABLE_THRESHOLD_ALERTS=true` | `true` |
| 9 | **Real-Time Chart.js Visualization** — Live-updating line/bar/gauge charts per pin on the dashboard | `ENABLE_LIVE_CHARTS=true` | `true` |
| 10 | **Data Retention & Rotation** — Automatic purging of logs older than configurable days with archive export | `ENABLE_DATA_RETENTION=true` | `true` |
| 11 | **CSV/JSON/SQLite Export** — One-click export of filtered data in any format via API or dashboard | `ENABLE_DATA_EXPORT=true` | `true` |
| 12 | **Pin Grouping & Labels** — Group related pins into named groups (e.g., "Kitchen Sensors", "Garage") | `ENABLE_PIN_GROUPS=true` | `false` |
| 13 | **Edge-Triggered Logging** — Capture only state changes (rising/falling edge) instead of continuous polling | `ENABLE_EDGE_LOGGING=true` | `false` |
| 14 | **Historical Analytics Dashboard** — Aggregated min/max/avg statistics, heatmaps, and trend line charts | `ENABLE_ANALYTICS=true` | `true` |

---

## 🎛️ Dashboard Feature Toggles

The web dashboard provides a **Settings → Feature Toggles** page where each feature can be enabled/disabled in real time without restarting the service. Toggle state is persisted to `.env` and SQLite.

┌──────────────────────────────────────────────────┐
│  ⚙️ Feature Toggles              [Save All]      │
├──────────────────────────────────────────────────┤
│  📌 Pin Configuration File     [████ ON ]         │
│  🖥️ Web Pin Manager            [████ ON ]         │
│  📄 CSV Logging                [████ ON ]         │
│  📋 JSON Logging               [░░░░ OFF]         │
│  🗃️ SQLite Logging             [████ ON ]         │
│  ⏱️ Custom Polling              [████ ON ]         │
│  📡 MCP3008 ADC                [░░░░ OFF]         │
│  ⚠️ Threshold Alerts            [████ ON ]         │
│  📈 Live Charts                [████ ON ]         │
│  🗑️ Data Retention             [████ ON ]         │
│  📥 Data Export                [████ ON ]         │
│  🏷️ Pin Grouping               [░░░░ OFF]         │
│  ⚡ Edge-Triggered Logging      [░░░░ OFF]         │
│  📊 Analytics                  [████ ON ]         │
└──────────────────────────────────────────────────┘

---

## 🔩 Hardware Requirements

| Component | Model / Spec | Qty | Est. Cost |
|-----------|-------------|-----|-----------|
| Raspberry Pi | 4B (2GB+) or 5 | 1 | $45–75 |
| MCP3008 ADC | 10-bit 8-channel SPI | 1 | $3–5 |
| DHT22 Sensor | Temperature + humidity | 1–4 | $4–6 each |
| LDR Photoresistor | Light level (analog via MCP3008) | 1–2 | $1 each |
| Soil Moisture Sensor | Capacitive (analog) | 1–2 | $3 each |
| Push Button | Momentary (digital input test) | 2–4 | $0.50 each |
| PIR Motion Sensor | HC-SR501 (digital) | 1 | $2 |
| LED Indicators | Status LEDs (output test) | 4 | $0.20 each |
| Breadboard + Jumpers | Solderless prototyping | 1 set | $5 |
| MicroSD Card | 32GB+ Class 10 | 1 | $8 |
| Power Supply | 5V 3A USB-C | 1 | $10 |
| **Total** | | | **$75–120** |

---

## 🔌 Wiring Diagram

```
Raspberry Pi 4/5 GPIO
┌──────────────────────────────────────────┐
│  GPIO 4  ──── DHT22 Data (pin config)   │
│  GPIO 17 ──── Push Button 1             │
│  GPIO 27 ──── Push Button 2             │
│  GPIO 22 ──── PIR Motion Sensor         │
│  GPIO 23 ──── LED Status 1              │
│  GPIO 24 ──── LED Status 2              │
│  GPIO 25 ──── Relay / Actuator          │
│                                          │
│  SPI (MCP3008 ADC):                      │
│  GPIO 8  ──── MCP3008 CS (CE0)          │
│  GPIO 10 ──── MCP3008 MOSI             │
│  GPIO 9  ──── MCP3008 MISO             │
│  GPIO 11 ──── MCP3008 CLK              │
│  MCP3008 CH0 ── Soil Moisture Sensor    │
│  MCP3008 CH1 ── LDR Photoresistor      │
│  MCP3008 CH2 ── TMP36 Temperature       │
│                                          │
│  3.3V / 5V ── Sensor VCC rails          │
│  GND ──────── Common ground bus         │
└──────────────────────────────────────────┘
```

---

## 💻 Software Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask, Flask-SocketIO |
| Frontend | HTML5, CSS3 (dark theme), JavaScript, Chart.js |
| Database | SQLite (readings, pins, settings, users) |
| ADC Driver | spidev + MCP3008 bit-bang / adafruit-circuitpython-mcp3xxx |
| GPIO | RPi.GPIO / gpiozero |
| Auth | bcrypt hashing, 10 attempts/15min rate limit, 24h JWT sessions |
| Notifications | python-telegram-bot, slack-sdk, pymsteams, smtplib |
| Real-time | WebSocket via Flask-SocketIO |
| Process Manager | systemd service |
| Data Formats | CSV (csv module), JSON (json), SQLite (sqlite3) |

---

## 🚀 Installation

### 1. Clone & setup
```bash
ssh rasp-pi  # SSH alias for 192.168.216.90
cd /opt
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Hardware & Networking Projects/GPIO Data Logger & Pin Manager"
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

### 4. Configure pin assignments
```bash
cp pins.default.json pins.json
nano pins.json  # Assign names and enable/disable pins
```

### 5. Initialize database
```bash
python3 init_db.py
```

### 6. Run as service
```bash
sudo cp deploy/gpio-logger.service /etc/systemd/system/
sudo systemctl enable gpio-logger
sudo systemctl start gpio-logger
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
# GPIO Data Logger & Pin Manager
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
ENABLE_PIN_CONFIG=true
ENABLE_PIN_MANAGER=true
ENABLE_CSV_LOGGING=true
ENABLE_JSON_LOGGING=false
ENABLE_SQLITE_LOGGING=true
ENABLE_CUSTOM_POLLING=true
ENABLE_ADC=false
ENABLE_THRESHOLD_ALERTS=true
ENABLE_LIVE_CHARTS=true
ENABLE_DATA_RETENTION=true
ENABLE_DATA_EXPORT=true
ENABLE_PIN_GROUPS=false
ENABLE_EDGE_LOGGING=false
ENABLE_ANALYTICS=true

# Pin Configuration
PIN_CONFIG_PATH=pins.json
DEFAULT_POLL_INTERVAL_MS=1000
MIN_POLL_INTERVAL_MS=100
MAX_POLL_INTERVAL_MS=3600000

# MCP3008 ADC
ADC_SPI_BUS=0
ADC_SPI_DEVICE=0
ADC_VREF=3.3
ADC_CHANNELS=8

# Threshold Alerts
ALERT_COOLDOWN_SEC=300

# Data Retention
RETENTION_DAYS=90
ARCHIVE_BEFORE_DELETE=true
ARCHIVE_PATH=data/archive/

# CSV Logging
CSV_OUTPUT_DIR=data/csv/
CSV_ROTATION_HOURS=24
CSV_MAX_FILES=365

# JSON Logging
JSON_OUTPUT_DIR=data/json/

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

# Database
DB_PATH=data/gpio_logger.db
```

---

## 📌 Pin Configuration File

The `pins.json` file defines which GPIO pins are active, their names, types, and polling intervals:

```json
{
  "version": 1,
  "pins": [
    {
      "gpio": 4,
      "name": "Sensor Temperature B100",
      "type": "digital_input",
      "enabled": true,
      "poll_interval_ms": 2000,
      "group": "Kitchen Sensors",
      "thresholds": { "high": null, "low": null }
    },
    {
      "gpio": 17,
      "name": "Front Door Button",
      "type": "digital_input",
      "enabled": true,
      "poll_interval_ms": 100,
      "edge_trigger": "rising",
      "group": "Door Controls"
    },
    {
      "gpio": 23,
      "name": "Status LED Green",
      "type": "digital_output",
      "enabled": true,
      "default_state": 0
    },
    {
      "adc_channel": 0,
      "name": "Garden Soil Moisture",
      "type": "analog_input",
      "enabled": true,
      "poll_interval_ms": 5000,
      "unit": "%",
      "formula": "round((1 - value / 1023) * 100, 1)",
      "thresholds": { "high": 80, "low": 20 },
      "group": "Garden Sensors"
    },
    {
      "adc_channel": 1,
      "name": "Room Light Level",
      "type": "analog_input",
      "enabled": false,
      "poll_interval_ms": 10000,
      "unit": "lux"
    }
  ]
}
```

Pin types supported: `digital_input`, `digital_output`, `analog_input` (MCP3008), `pwm_output`

---

## 🌐 Web Dashboard

Dark-theme responsive dashboard with real-time WebSocket updates:

| Page | Description |
|------|-------------|
| **Dashboard** | Overview cards per pin group, live values, status indicators |
| **Pin Manager** | Visual GPIO header layout, assign/rename/enable pins, set polling |
| **Live Charts** | Real-time Chart.js line graphs per pin or pin group |
| **Data Browser** | Searchable/filterable table of all logged readings |
| **Analytics** | Min/max/avg statistics, heatmaps, trend lines, comparison charts |
| **Alerts** | Threshold configuration, alert history, notification routing |
| **Export** | Date-range picker, format selector (CSV/JSON/SQLite), download |
| **Settings** | Feature toggles, GPIO config, notification setup, user management |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate and receive JWT |
| `GET` | `/api/pins` | List all configured pins with current values |
| `GET` | `/api/pins/<gpio>` | Get single pin details and latest reading |
| `PUT` | `/api/pins/<gpio>` | Update pin config (name, enabled, polling) |
| `POST` | `/api/pins` | Add new pin to configuration |
| `DELETE` | `/api/pins/<gpio>` | Remove pin from configuration |
| `GET` | `/api/pins/<gpio>/readings` | Paginated readings for a pin |
| `GET` | `/api/groups` | List all pin groups |
| `POST` | `/api/groups` | Create new pin group |
| `PUT` | `/api/groups/<id>` | Update group name/pins |
| `GET` | `/api/readings` | All readings (filterable by pin, date, group) |
| `GET` | `/api/analytics/summary` | Aggregated stats (min/max/avg per pin) |
| `GET` | `/api/analytics/heatmap` | Heatmap data (hour × day matrix) |
| `GET` | `/api/export` | Export data (query params: format, pins, from, to) |
| `GET` | `/api/alerts` | List alert history |
| `POST` | `/api/alerts/thresholds` | Configure pin thresholds |
| `GET` | `/api/settings/features` | Get all feature toggle states |
| `PUT` | `/api/settings/features` | Update feature toggles via dashboard |
| `GET` | `/api/adc/channels` | List MCP3008 ADC channel status |
| `POST` | `/api/pins/<gpio>/output` | Set digital output pin HIGH/LOW |

---

## 💰 Budget Estimate

| Tier | Components | Cost |
|------|-----------|------|
| **Basic** | Pi 4 + DHT22 + Buttons + LEDs | ~$75 |
| **Standard** | + MCP3008 + Soil Moisture + LDR + PIR | ~$95 |
| **Full** | + Multiple DHT22 + Extra analog sensors + Breadboard kit | ~$120 |

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🪙 Donations

If you find this project helpful, you can support my work:

₿ **Bitcoin:** `bc1q...`
