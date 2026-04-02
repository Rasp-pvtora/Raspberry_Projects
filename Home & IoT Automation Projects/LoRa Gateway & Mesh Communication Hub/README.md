# LoRa Gateway & Mesh Communication Hub

A single Raspberry Pi with one LoRa concentrator HAT operating in **two switchable modes** — selectable live from a dark-themed web dashboard. **Gateway mode** turns the Pi into a full LoRaWAN gateway serving hundreds of low-power sensors at ranges up to 10 km, integrating with ChirpStack (self-hosted) or The Things Network. **Mesh mode** activates Meshtastic for off-grid peer-to-peer encrypted text communication, bridged to the internet via MQTT. Set `LORA_MODE=gateway|mesh|both` in `.env` or switch on the fly from the dashboard — run one mode or **both simultaneously**. Features a live sensor dashboard with charts and alerts, a browser-based Meshtastic chat with GPS node map, MQTT bridge via Mosquitto, emergency broadcast alerts, geofencing, and optional solar power monitoring. Managed through a Flask + SocketIO dark-themed dashboard with bcrypt authentication.

---

**If you find this project useful, consider supporting development:**

**BTC:** `bc1q...`

---

## Table of Contents

- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Libraries & Dependencies](#libraries--dependencies)
- [Quickstart](#quickstart)
- [Environment Configuration](#environment-configuration)
- [System Overview](#system-overview)
- [Dual-Mode Architecture](#dual-mode-architecture)
  - [Gateway Mode (LoRaWAN)](#gateway-mode-lorawan)
  - [Mesh Mode (Meshtastic)](#mesh-mode-meshtastic)
  - [Both Mode (Simultaneous)](#both-mode-simultaneous)
- [Features](#features)
  - [ChirpStack Integration](#chirpstack-integration)
  - [Sensor Dashboard](#sensor-dashboard)
  - [Meshtastic Web Chat](#meshtastic-web-chat)
  - [MQTT Bridge](#mqtt-bridge)
  - [Multi-Channel Gateway](#multi-channel-gateway)
  - [Emergency Alert Broadcast](#emergency-alert-broadcast)
  - [Power Monitoring](#power-monitoring)
  - [Geofencing](#geofencing)
  - [Web Dashboard](#web-dashboard)
- [Authentication](#authentication)
- [Deployment](#deployment)
- [Running the Service](#running-the-service)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
LoRa Gateway & Mesh Communication Hub/
├── README.md                   # This file
├── TSD.md                      # Technical Specification Document
├── task.md                     # Development task checklist
├── implementation_plan.md      # Phased implementation guide
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
├── .env.example                # Environment variable template
├── src/
│   ├── __init__.py
│   ├── app.py                  # Flask app factory & SocketIO init
│   ├── gateway.py              # LoRaWAN gateway mode controller
│   ├── mesh.py                 # Meshtastic mesh mode controller
│   ├── mode_manager.py         # Dual-mode orchestrator & live switching
│   ├── chirpstack.py           # ChirpStack gRPC/REST integration
│   ├── sensors.py              # Sensor data ingestion, storage & alerting
│   ├── chat.py                 # Meshtastic chat message handler
│   ├── mqtt_bridge.py          # Mosquitto MQTT pub/sub bridge
│   ├── gps.py                  # GPS position tracking (gpsd integration)
│   ├── geofence.py             # Geofencing engine (node boundary alerts)
│   ├── emergency.py            # Emergency alert broadcast (mesh priority)
│   ├── power.py                # Solar power monitoring (INA219 / INA260)
│   ├── database.py             # SQLite DB models & helpers
│   ├── auth.py                 # bcrypt auth & session management
│   ├── config.py               # .env loader & config dataclass
│   └── utils.py                # Shared utilities
├── templates/
│   ├── base.html               # Dark theme layout
│   ├── login.html              # Login page
│   ├── dashboard.html          # Main dashboard (mode selector, overview)
│   ├── sensors.html            # Sensor data dashboard (charts, alerts)
│   ├── chat.html               # Meshtastic web chat interface
│   ├── map.html                # GPS node position map view
│   ├── emergency.html          # Emergency alert broadcast page
│   ├── power.html              # Solar power monitoring page
│   └── settings.html           # Runtime settings & mode switching
├── static/
│   ├── css/
│   │   └── style.css           # Dark theme styles
│   └── js/
│       ├── dashboard.js        # SocketIO client & live mode status
│       ├── sensors.js          # Chart.js sensor data visualization
│       ├── chat.js             # Real-time chat SocketIO client
│       ├── map.js              # Leaflet.js GPS node map
│       └── emergency.js        # Emergency alert UI logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures & mock mode helpers
│   ├── test_gateway.py         # LoRaWAN gateway mode tests
│   ├── test_mesh.py            # Meshtastic mesh mode tests
│   ├── test_mode_manager.py    # Mode switching & orchestration tests
│   ├── test_chirpstack.py      # ChirpStack integration tests
│   ├── test_sensors.py         # Sensor ingestion & alerting tests
│   ├── test_chat.py            # Chat message handler tests
│   ├── test_mqtt_bridge.py     # MQTT bridge tests
│   ├── test_gps.py             # GPS tracking tests
│   ├── test_geofence.py        # Geofencing logic tests
│   ├── test_emergency.py       # Emergency broadcast tests
│   ├── test_power.py           # Power monitoring tests
│   ├── test_auth.py            # Auth & session tests
│   ├── test_api.py             # Dashboard API endpoint tests
│   └── test_database.py        # Database CRUD tests
├── deploy/
│   └── deploy_to_pi.sh         # rsync deploy script (rasp-pi)
├── scripts/
│   ├── install_deps.sh         # OS-level dependency installer
│   ├── setup_chirpstack.sh     # ChirpStack Docker stack installer
│   ├── setup_mosquitto.sh      # Mosquitto MQTT broker configuration
│   └── generate_password_hash.sh # Helper to generate bcrypt hash
└── docs/
    ├── mode_switching.md        # Dual-mode architecture & switching guide
    ├── chirpstack_setup.md      # ChirpStack self-hosted setup guide
    ├── antenna_guide.md         # Antenna selection & placement guide
    └── mqtt_topics.md           # MQTT topic hierarchy documentation
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 or 5 | Yes | 2 GB+ RAM recommended for ChirpStack |
| LoRa Concentrator HAT | Yes | RAK2287 + Pi HAT (~$100) or RAK5146 8-channel (~$120) |
| LoRa Antenna (868/915 MHz) | Yes | Matched to regional frequency band, SMA pigtail |
| MicroSD card (32GB+) | Yes | For OS, ChirpStack, database, and logs |
| Power supply (5V/3A) | Yes | Official Pi PSU or PoE HAT |
| LoRa sensor nodes (optional) | No | For testing — RAK WisNode, LHT65, etc. (~$15–25 each) |
| Outdoor enclosure (optional) | No | IP65/IP67 for outdoor gateway deployment (~$20) |
| GPS module (optional) | No | For mesh node positioning; USB or UART GPS receiver |
| INA219/INA260 sensor (optional) | No | For solar power monitoring via I2C |

> **Note:** The RAK2287/5146 concentrators are multi-channel SX1302/SX1303-based modules — they can listen on 8 LoRa channels simultaneously, which is required for proper LoRaWAN gateway operation. Single-channel modules (SX1276) are **not** supported for gateway mode.

---

## Budget

| Item | Estimated Cost |
|---|---|
| Raspberry Pi 4/5 (already owned) | $0 |
| LoRa Concentrator HAT (RAK2287 + Pi HAT or RAK5146) | ~$100–120 |
| LoRa Antenna (868/915 MHz) | ~$10–15 |
| Outdoor enclosure (optional) | ~$20 |
| LoRa sensor nodes for testing (×2) | ~$30–50 |
| **Total** | **~$110–160** |

*(Assumes you already have a Raspberry Pi 4/5 and SD card.)*

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| Flask | Web dashboard framework |
| Flask-SocketIO | Real-time WebSocket for live data & chat |
| python-dotenv | `.env` configuration loading |
| bcrypt | Password hashing for dashboard auth |
| chirpstack-api | ChirpStack gRPC/REST API integration |
| meshtastic | Meshtastic Python API for mesh radio control |
| paho-mqtt | MQTT client for Mosquitto bridge |
| gpsd-py3 | GPS daemon integration for node positioning |
| Jinja2 | HTML template engine (via Flask) |
| eventlet | Async networking for SocketIO |
| gunicorn | Production WSGI server |

---

## Quickstart

```bash
# 1. SSH into the Pi
ssh rasp-pi          # alias for pi@192.168.216.90

# 2. Clone the repo
git clone <repo-url> ~/lora-hub && cd ~/lora-hub

# 3. Install OS-level dependencies
sudo bash scripts/install_deps.sh

# 4. Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 5. (Optional) Install ChirpStack Docker stack
sudo bash scripts/setup_chirpstack.sh

# 6. (Optional) Configure Mosquitto MQTT broker
sudo bash scripts/setup_mosquitto.sh

# 7. Configure environment
cp .env.example .env
nano .env              # Set LORA_MODE, credentials, toggle features

# 8. Initialize database
python -m src.app --init-db

# 9. Start the service
python -m src.app
# Dashboard at http://192.168.216.90:5000
```

---

## Environment Configuration

All features are toggleable via `.env`. Copy `.env.example` and adjust:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(generate)* | Flask session secret key |
| `ADMIN_USERNAME` | `admin` | Dashboard login username |
| `ADMIN_PASSWORD_HASH` | *(bcrypt hash)* | bcrypt-hashed admin password |
| `DB_PATH` | `data/lora_hub.db` | SQLite database file path |
| `LORA_MODE` | `gateway` | Operational mode: `gateway`, `mesh`, or `both` |
| `ENABLE_CHIRPSTACK` | `true` | Toggle ChirpStack LoRaWAN server integration |
| `CHIRPSTACK_API_URL` | `http://localhost:8080` | ChirpStack API endpoint |
| `CHIRPSTACK_API_KEY` | *(generate)* | ChirpStack API token |
| `ENABLE_SENSOR_DASHBOARD` | `true` | Toggle live sensor data charts & alerts |
| `SENSOR_ALERT_THRESHOLD` | `{}` | JSON map of sensor type → threshold (e.g., `{"temperature": 40}`) |
| `ENABLE_MESHTASTIC` | `true` | Toggle Meshtastic mesh mode |
| `MESHTASTIC_DEVICE` | `/dev/ttyUSB0` | Serial port for Meshtastic radio |
| `MESHTASTIC_CHANNEL` | `0` | Default Meshtastic channel index |
| `ENABLE_WEB_CHAT` | `true` | Toggle browser-based Meshtastic chat |
| `ENABLE_MQTT_BRIDGE` | `true` | Toggle MQTT bridge (Mosquitto) |
| `MQTT_BROKER_HOST` | `localhost` | MQTT broker address |
| `MQTT_BROKER_PORT` | `1883` | MQTT broker port |
| `MQTT_USERNAME` | `` | MQTT broker username (optional) |
| `MQTT_PASSWORD` | `` | MQTT broker password (optional) |
| `MQTT_TOPIC_PREFIX` | `lora-hub` | Root MQTT topic prefix |
| `ENABLE_GPS` | `false` | Toggle GPS tracking for mesh nodes |
| `GPSD_HOST` | `localhost` | gpsd daemon address |
| `GPSD_PORT` | `2947` | gpsd daemon port |
| `ENABLE_GEOFENCING` | `false` | Toggle geofencing alerts |
| `GEOFENCE_RADIUS_M` | `1000` | Default geofence radius in meters |
| `GEOFENCE_CENTER_LAT` | `` | Geofence center latitude |
| `GEOFENCE_CENTER_LON` | `` | Geofence center longitude |
| `ENABLE_EMERGENCY_ALERTS` | `true` | Toggle emergency alert broadcast |
| `EMERGENCY_PRIORITY` | `high` | Mesh priority level for emergency messages |
| `ENABLE_POWER_MONITORING` | `false` | Toggle solar power monitoring (INA219/INA260) |
| `POWER_I2C_ADDRESS` | `0x40` | I2C address of power sensor |
| `POWER_LOW_THRESHOLD_V` | `11.5` | Low voltage alert threshold |
| `ENABLE_MULTI_CHANNEL` | `true` | Toggle 8-channel concentrator support |
| `LORA_REGION` | `EU868` | LoRa frequency plan (`EU868`, `US915`, `AS923`, etc.) |
| `CONCENTRATOR_MODEL` | `RAK5146` | Concentrator HAT model (`RAK2287`, `RAK5146`) |
| `ENABLE_WEB_DASHBOARD` | `true` | Toggle web dashboard |
| `DASHBOARD_HOST` | `0.0.0.0` | Dashboard bind address |
| `DASHBOARD_PORT` | `5000` | Dashboard bind port |
| `SESSION_EXPIRY_HOURS` | `24` | Session expiry in hours |
| `RATE_LIMIT` | `10/15min` | Login rate limit (attempts/window) |
| `MOCK_MODE` | `false` | Run without real hardware (dev/test) |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## System Overview

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4/5 — LoRa Hub                                │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                    Mode Manager (LORA_MODE)                              │  │
│  │         ┌──────────────────┬────────────────────┐                       │  │
│  │         │  gateway         │  mesh               │                       │  │
│  │         │  (LoRaWAN)       │  (Meshtastic)       │  ← switchable live   │  │
│  │         └────────┬─────────┴──────────┬──────────┘                       │  │
│  └──────────────────┼───────────────────┼──────────────────────────────────┘  │
│                     │                   │                                      │
│  ┌──────────────────▼──────────┐  ┌─────▼──────────────────┐                 │
│  │  LoRaWAN Gateway Engine      │  │  Meshtastic Controller  │                 │
│  │                              │  │                         │                 │
│  │  ┌────────────────────────┐ │  │  ┌───────────────────┐  │                 │
│  │  │ RAK2287/5146 SX1302/03 │ │  │  │ Meshtastic Radio  │  │                 │
│  │  │ 8-channel concentrator │ │  │  │ Serial /dev/ttyUSB│  │                 │
│  │  │ Packet Forwarder       │ │  │  │ Python API        │  │                 │
│  │  └────────────┬───────────┘ │  │  └─────────┬─────────┘  │                 │
│  │               │             │  │             │            │                 │
│  │  ┌────────────▼───────────┐ │  │  ┌──────────▼────────┐  │                 │
│  │  │ ChirpStack (Docker)    │ │  │  │ Chat Handler      │  │                 │
│  │  │ LoRaWAN Network Server │ │  │  │ GPS Tracker       │  │                 │
│  │  │ Application Server     │ │  │  │ Emergency Alerts  │  │                 │
│  │  │ Gateway Bridge         │ │  │  │ Geofence Engine   │  │                 │
│  │  └────────────┬───────────┘ │  │  └──────────┬────────┘  │                 │
│  └───────────────┼─────────────┘  └─────────────┼───────────┘                 │
│                  │                               │                             │
│  ┌───────────────▼───────────────────────────────▼──────────────────────────┐ │
│  │                         MQTT Bridge (Mosquitto)                           │ │
│  │   Gateway topics: lora-hub/gateway/+/rx  lora-hub/gateway/+/tx           │ │
│  │   Mesh topics:    lora-hub/mesh/chat/#   lora-hub/mesh/position/#        │ │
│  │   Alerts:         lora-hub/alerts/#      lora-hub/power/#                │ │
│  └───────────────────────────────┬──────────────────────────────────────────┘ │
│                                  │                                             │
│  ┌───────────────────────────────▼──────────────────────────────────────────┐ │
│  │                         SQLite Database                                   │ │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────┐  │ │
│  │  │ devices  │ │ sensors  │ │  messages │ │  nodes   │ │   alerts    │  │ │
│  │  └──────────┘ └──────────┘ └───────────┘ └──────────┘ └─────────────┘  │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │ │
│  │  │ geofences    │ │ power_logs   │ │ settings     │                    │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                    │ │
│  └──────────────────────────────┬───────────────────────────────────────────┘ │
│                                 │                                              │
│  ┌──────────────────────────────▼───────────────────────────────────────────┐ │
│  │            Flask + SocketIO Dashboard (dark theme)                        │ │
│  │  - bcrypt auth (rate limit 10/15min, 24h session)                        │ │
│  │  - Mode selector: Gateway | Mesh | Both                                  │ │
│  │  - Sensor data charts & threshold alerts                                 │ │
│  │  - Meshtastic web chat & GPS node map                                    │ │
│  │  - Emergency alert broadcast panel                                       │ │
│  │  - Power monitoring (voltage, current, wattage)                          │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└────────────────────────────┬──────────────────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
   ┌────────▼───────┐  ┌────▼──────────┐  ┌──▼──────────────┐
   │ LoRaWAN Sensors │  │ Meshtastic    │  │ MQTT Subscribers │
   │ (up to 10 km)   │  │ Mesh Nodes    │  │ (Home Assistant, │
   │ temp, humidity,  │  │ (off-grid     │  │  Node-RED, etc.) │
   │ soil, water,     │  │  text chat,   │  │                  │
   │ motion, etc.     │  │  GPS beacons) │  │                  │
   └─────────────────┘  └──────────────┘  └──────────────────┘
```

---

## Dual-Mode Architecture

The hub supports two distinct LoRa operational modes, switchable live from the web dashboard or via the `LORA_MODE` environment variable.

### Gateway Mode (LoRaWAN)

Acts as a full 8-channel LoRaWAN gateway using the RAK2287/5146 concentrator HAT. The Pi runs ChirpStack (self-hosted in Docker) as the LoRaWAN Network Server and Application Server. Hundreds of LoRaWAN sensor nodes can join the network and transmit data at ranges up to 10 km.

- **Packet Forwarder** — SX1302/SX1303 concentrator listens on 8 channels simultaneously
- **ChirpStack** — self-hosted LoRaWAN server (network server + application server + gateway bridge)
- **The Things Network** — optional cloud alternative to ChirpStack
- **Uplink processing** — sensor data decoded, stored, and displayed on dashboard
- **Downlink scheduling** — send commands to devices (actuators, configuration)
- Toggle via `LORA_MODE=gateway` or `LORA_MODE=both`

### Mesh Mode (Meshtastic)

Activates Meshtastic mesh networking for off-grid peer-to-peer encrypted text communication. The Pi bridges mesh messages to the internet via MQTT, enabling users on the local network (or internet) to chat with off-grid Meshtastic nodes.

- **Meshtastic Radio** — connected via serial (`/dev/ttyUSB0` or SPI)
- **Mesh Chat** — peer-to-peer encrypted text messages
- **MQTT Bridge** — mesh messages forwarded to Mosquitto topics for internet relay
- **GPS Positions** — mesh nodes report GPS coordinates, displayed on map
- **Emergency Alerts** — priority broadcast messages to all mesh nodes
- Toggle via `LORA_MODE=mesh` or `LORA_MODE=both`

### Both Mode (Simultaneous)

Runs LoRaWAN gateway and Meshtastic mesh simultaneously. The concentrator HAT handles LoRaWAN traffic while a separate Meshtastic radio (USB or secondary SPI) handles mesh traffic. Both data streams merge into the unified dashboard and MQTT topic hierarchy.

- Requires either: (a) separate Meshtastic USB radio + concentrator HAT, or (b) HAT with dual SPI channels
- Both modes share the MQTT bridge with isolated topic namespaces
- Dashboard shows combined view with mode-specific tabs
- Toggle via `LORA_MODE=both`

---

## Features

### ChirpStack Integration

Self-hosted LoRaWAN network server running in Docker on the Pi. Manages device activation (OTAA/ABP), data decoding, and downlink scheduling.

- Full ChirpStack v4 stack (network server, application server, gateway bridge)
- Device management via ChirpStack API or web UI
- Application-level payload decoders (JavaScript codec)
- Device profiles, service profiles, multi-tenancy
- Integration with sensor dashboard via gRPC/REST API
- Toggle via `ENABLE_CHIRPSTACK`

### Sensor Dashboard

Live visualization of LoRaWAN sensor data with configurable threshold alerts.

- Real-time data ingestion from ChirpStack uplink events
- Chart.js line/bar graphs for temperature, humidity, soil moisture, etc.
- Configurable alert thresholds per sensor type
- Historical data browsing with time-range selector
- Export data as CSV
- Toggle via `ENABLE_SENSOR_DASHBOARD`

### Meshtastic Web Chat

Browser-based chat interface for Meshtastic mesh communication, bridged from the Pi.

- Send/receive text messages to/from off-grid Meshtastic nodes
- Channel selection (primary + secondary channels)
- Message history stored in database
- User nicknames for mesh nodes
- Real-time message delivery via SocketIO
- Toggle via `ENABLE_WEB_CHAT`

### MQTT Bridge

Mosquitto MQTT broker running on the Pi, bridging both LoRaWAN and Meshtastic data to standard MQTT topics.

- **Gateway topics:** `lora-hub/gateway/{device_eui}/rx` (uplink), `lora-hub/gateway/{device_eui}/tx` (downlink)
- **Mesh topics:** `lora-hub/mesh/chat/{channel}`, `lora-hub/mesh/position/{node_id}`
- **Alert topics:** `lora-hub/alerts/{type}`, `lora-hub/power/{metric}`
- Compatible with Home Assistant, Node-RED, Grafana, Telegraf
- Optional TLS encryption for external MQTT clients
- Toggle via `ENABLE_MQTT_BRIDGE`

### Multi-Channel Gateway

Full 8-channel LoRaWAN gateway using SX1302/SX1303 concentrator for production-grade coverage.

- 8 simultaneous receive channels (125 kHz standard LoRa)
- 1 high-bandwidth channel (250/500 kHz)
- SF7–SF12 spreading factor support
- Regional frequency plan support (EU868, US915, AS923, AU915, etc.)
- GPS PPS time synchronization (if GPS module attached)
- Toggle via `ENABLE_MULTI_CHANNEL`

### Emergency Alert Broadcast

Send priority alert messages to all Meshtastic mesh nodes (mesh mode). Alerts bypass normal queuing and are delivered with highest priority.

- Compose alert from web dashboard
- Priority flag forces immediate relay on all mesh nodes
- Alert types: SOS, weather, evacuation, custom
- Alert history log with timestamps and delivery status
- Toggle via `ENABLE_EMERGENCY_ALERTS`

### Power Monitoring

Monitor battery voltage, current draw, and solar panel output when the hub is solar powered. Uses INA219 or INA260 I2C power sensor.

- Real-time voltage, current, and power readings
- Low-voltage alerts (configurable threshold)
- Historical power charts on dashboard
- MQTT publishing for external monitoring
- Toggle via `ENABLE_POWER_MONITORING`

### Geofencing

Alert when mesh nodes leave a defined geographic boundary. Requires GPS-enabled Meshtastic nodes.

- Define circular geofence zones (center + radius)
- Per-node or global geofence rules
- Enter/exit alerts published via MQTT and displayed on dashboard
- Geofence zones displayed on GPS map view
- Toggle via `ENABLE_GEOFENCING`

### Web Dashboard

Dark-themed management interface with live mode switching and real-time data.

- **Mode selector** — switch between Gateway, Mesh, or Both with one click
- **Sensor tab** — live charts, alert indicators, device list
- **Chat tab** — Meshtastic web chat with message history
- **Map tab** — Leaflet.js map with GPS node positions and geofence zones
- **Emergency tab** — alert composer and broadcast history
- **Power tab** — voltage/current/wattage gauges and history
- **Settings tab** — feature toggles, concentrator status, MQTT status
- Real-time updates via SocketIO

---

## Authentication

The web dashboard is protected with bcrypt-hashed password authentication:

- Admin credentials configured via `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` in `.env`
- Generate a password hash: `python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpass', bcrypt.gensalt()).decode())"`
- Login rate limiting: **10 attempts per 15 minutes** per IP (`RATE_LIMIT`)
- Session cookies with **24-hour expiry** (`SESSION_EXPIRY_HOURS`)
- Sessions invalidated on password change or server restart
- All dashboard routes require authentication except `/login`

---

## Deployment

Use the deploy script to push code to the Pi:

```bash
# From development machine
bash deploy/deploy_to_pi.sh
```

The deploy script (`deploy_to_pi.sh`):
```bash
#!/usr/bin/env bash
set -euo pipefail

PI_HOST="rasp-pi"                              # SSH alias -> pi@192.168.216.90
REMOTE_DIR="/home/pi/lora-hub"

echo "[*] Deploying to ${PI_HOST}:${REMOTE_DIR}"
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
    --exclude '.git' --exclude 'data/' \
    ./ "${PI_HOST}:${REMOTE_DIR}/"

ssh "${PI_HOST}" "cd ${REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt"
echo "[✓] Deploy complete."
```

---

## Running the Service

### Manual

```bash
ssh rasp-pi
cd ~/lora-hub
source .venv/bin/activate
python -m src.app
# Dashboard at http://192.168.216.90:5000
```

### systemd Service

Create `/etc/systemd/system/lora-hub.service`:

```ini
[Unit]
Description=LoRa Gateway & Mesh Communication Hub
After=network.target docker.service mosquitto.service
Wants=docker.service mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/lora-hub
EnvironmentFile=/home/pi/lora-hub/.env
ExecStart=/home/pi/lora-hub/.venv/bin/python -m src.app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable lora-hub
sudo systemctl start lora-hub
sudo journalctl -u lora-hub -f    # Follow logs
```

---

## Security Notes

- **Change the `SECRET_KEY`** — generate a strong random string and never commit `.env` to version control.
- **Password hashing** — only bcrypt hashes are stored; plaintext passwords are never persisted.
- **Rate limiting** — protects against brute-force login attempts on the dashboard.
- **MQTT authentication** — configure `MQTT_USERNAME` and `MQTT_PASSWORD` for the Mosquitto broker; do not expose port 1883 without auth.
- **ChirpStack API key** — treat like a password; rotate regularly.
- **Firewall** — restrict dashboard port (5000) and MQTT port (1883) to your local network only.
- **Meshtastic encryption** — mesh messages are encrypted with the channel's PSK; use strong channel keys for sensitive communication.
- **CSRF protection** — all POST forms include CSRF tokens.
- **TLS for MQTT** — enable TLS on Mosquitto if exposing MQTT outside the local network.
- **Antenna safety** — always attach the antenna before powering the concentrator HAT; transmitting without an antenna can damage the radio.

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| Concentrator not detected | SPI not enabled or HAT not seated | Run `sudo raspi-config` → Interface Options → SPI → Enable; reseat HAT; reboot |
| No LoRaWAN uplinks received | Wrong frequency plan or antenna issue | Verify `LORA_REGION` matches your country; check antenna connection |
| ChirpStack web UI not loading | Docker containers not running | Run `docker compose up -d` in ChirpStack directory; check `docker ps` |
| Meshtastic device not found | Wrong serial port | Check `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`; update `MESHTASTIC_DEVICE` |
| MQTT connection refused | Mosquitto not running or wrong port | Run `sudo systemctl start mosquitto`; verify `MQTT_BROKER_PORT` |
| GPS no fix | No GPS module or poor signal | Verify `gpsd` is running; place GPS antenna with sky view |
| Mode switch fails | Conflicting hardware access | Stop current mode cleanly before switching; check logs for lock errors |
| Sensor data not appearing | ChirpStack integration disabled or no devices joined | Check `ENABLE_CHIRPSTACK=true`; verify device activation in ChirpStack UI |
| Chat messages not delivered | Meshtastic radio offline or wrong channel | Check radio connection and `MESHTASTIC_CHANNEL` setting |
| Power readings all zeros | Wrong I2C address or sensor not connected | Verify `POWER_I2C_ADDRESS`; run `i2cdetect -y 1` to scan bus |
| Dashboard not loading | Web dashboard disabled or wrong port | Check `ENABLE_WEB_DASHBOARD=true` and `DASHBOARD_PORT` in `.env` |
| `ModuleNotFoundError` | Missing Python dependency | Activate venv and run `pip install -r requirements.txt` |

---

## Where to Next

- **LoRa relay nodes** — solar-powered LoRa relay stations to extend gateway range beyond 10 km
- **Grafana integration** — push sensor data to InfluxDB + Grafana for advanced dashboards
- **Voice alerts** — text-to-speech emergency alerts on mesh nodes with speakers
- **Satellite backhaul** — bridge Meshtastic mesh to satellite internet (Starlink) for truly remote deployments
- **Multi-gateway mesh** — multiple Pi gateways cooperating across a large area via LoRaWAN roaming
- **Firmware OTA** — over-the-air firmware updates for Meshtastic nodes via mesh
- **Weather station** — dedicated LoRaWAN weather sensor integration with forecast dashboard
- **LoRa-based asset tracking** — combine GPS + LoRa for vehicle/equipment tracking fleet
- **Offline MQTT store-and-forward** — queue MQTT messages when internet drops, replay when restored
