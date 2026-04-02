# 🚛 CAN Bus & CANopen Communication Hub

A Raspberry Pi–powered CAN bus communication hub using MCP2515 + TJA1050/1051 HAT with SocketCAN, live message viewer, DBC signal decoder, message sender and recorder, CANopen NMT/SDO/PDO management, Object Dictionary browser, bus diagnostics, and CAN↔TCP bridging — all managed from a responsive dark-theme web dashboard with per-feature toggle switches.

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
| 1 | **SocketCAN Auto-Config** — Automatic MCP2515 overlay, interface bring-up (can0), bitrate configuration | `ENABLE_SOCKETCAN_SETUP=true` | `true` |
| 2 | **Live Message Viewer** — Real-time CAN frame display with ID, DLC, data, timestamp, and direction filter | `ENABLE_LIVE_VIEWER=true` | `true` |
| 3 | **DBC Signal Decoder** — Upload DBC files to auto-decode CAN signals into human-readable values and units | `ENABLE_DBC_DECODER=true` | `false` |
| 4 | **Message Sender** — Send arbitrary CAN frames (standard/extended) with hex data builder and repeat mode | `ENABLE_MSG_SENDER=true` | `true` |
| 5 | **Message Recorder** — Record CAN bus traffic to ASC/BLF/CSV files with start/stop and auto-rotate | `ENABLE_RECORDER=true` | `true` |
| 6 | **Message Replay** — Replay recorded CAN logs at original or adjusted timing | `ENABLE_REPLAY=true` | `false` |
| 7 | **CANopen NMT Manager** — Send NMT commands (Start, Stop, Pre-Op, Reset) to nodes and monitor states | `ENABLE_CANOPEN_NMT=true` | `false` |
| 8 | **CANopen SDO Client** — Read/write SDO transfers to any node's Object Dictionary entries | `ENABLE_CANOPEN_SDO=true` | `false` |
| 9 | **CANopen PDO Mapping** — Configure and monitor TPDO/RPDO mappings for real-time process data | `ENABLE_CANOPEN_PDO=true` | `false` |
| 10 | **Object Dictionary Browser** — Upload EDS/DCF files and browse node Object Dictionaries visually | `ENABLE_OD_BROWSER=true` | `false` |
| 11 | **Bus Diagnostics** — Error frame counter, bus load %, bus-off detection, and CAN controller status | `ENABLE_BUS_DIAG=true` | `true` |
| 12 | **CAN↔TCP Bridge** — Forward CAN frames to/from a TCP socket server for remote access | `ENABLE_CAN_TCP_BRIDGE=true` | `false` |
| 13 | **Heartbeat Monitor** — Track CANopen heartbeat (0x700+NodeID) and alert on node timeouts | `ENABLE_HEARTBEAT_MONITOR=true` | `false` |
| 14 | **Message Filtering** — Hardware and software filters by CAN ID range, mask, or DBC signal | `ENABLE_MSG_FILTER=true` | `true` |
| 15 | **Multi-Channel Notifications** — Alerts via Telegram, Slack, email for bus errors, node failures, thresholds | `ENABLE_NOTIFICATIONS=true` | `false` |
| 16 | **Historical Analytics** — Message rate charts, bus load trends, per-ID frequency analysis, error rate graphs | `ENABLE_ANALYTICS=true` | `true` |

---

## 🎛️ Dashboard Feature Toggles

The web dashboard provides a **Settings → Feature Toggles** page where each feature can be enabled/disabled in real time without restarting the service. Toggle state is persisted to `.env` and SQLite.

```
┌──────────────────────────────────────────────────┐
│  ⚙️ Feature Toggles              [Save All]      │
├──────────────────────────────────────────────────┤
│  🔧 SocketCAN Auto-Config      [████ ON ]        │
│  📺 Live Message Viewer        [████ ON ]        │
│  🔓 DBC Signal Decoder         [░░░░ OFF]        │
│  📤 Message Sender             [████ ON ]        │
│  ⏺️ Message Recorder           [████ ON ]        │
│  ▶️ Message Replay             [░░░░ OFF]        │
│  🎛️ CANopen NMT Manager        [░░░░ OFF]        │
│  📝 CANopen SDO Client         [░░░░ OFF]        │
│  🔄 CANopen PDO Mapping        [░░░░ OFF]        │
│  📖 Object Dictionary Browser  [░░░░ OFF]        │
│  🔍 Bus Diagnostics            [████ ON ]        │
│  🌐 CAN↔TCP Bridge             [░░░░ OFF]        │
│  💚 Heartbeat Monitor          [░░░░ OFF]        │
│  🔎 Message Filtering          [████ ON ]        │
│  🔔 Notifications              [░░░░ OFF]        │
│  📊 Analytics                  [████ ON ]        │
└──────────────────────────────────────────────────┘
```
---

## 🔩 Hardware Requirements

| Component | Model / Spec | Qty | Est. Cost |
|-----------|-------------|-----|-----------|
| Raspberry Pi | 4B (2GB+) or 5 | 1 | $45–75 |
| CAN HAT | Waveshare RS485 CAN HAT or PiCAN2/3 (MCP2515 + TJA1050) | 1 | $15–30 |
| CAN Termination Resistor | 120Ω (if not built into HAT) | 1–2 | $0.50 |
| CAN Cable | DB9 or screw-terminal to CAN bus | 1 | $5–10 |
| MicroSD Card | 32GB+ Class 10 | 1 | $8 |
| Power Supply | 5V 3A USB-C | 1 | $10 |
| CAN Test Node (optional) | Arduino + MCP2515 module for testing | 1 | $10–15 |
| **Total** | | | **$85–150** |

---

## 🔌 Wiring Diagram

```
Raspberry Pi 4/5 + CAN HAT (SPI)
┌──────────────────────────────────────────┐
│                                          │
│  SPI Interface (Pi → MCP2515):           │
│  GPIO 8  (CE0) ──── MCP2515 CS          │
│  GPIO 10 (MOSI) ─── MCP2515 SI          │
│  GPIO 9  (MISO) ─── MCP2515 SO          │
│  GPIO 11 (SCLK) ─── MCP2515 SCK         │
│  GPIO 25 (INT)  ─── MCP2515 INT         │
│  3.3V ──────────── MCP2515 VCC          │
│  GND ───────────── MCP2515 GND          │
│                                          │
│  MCP2515 → TJA1050/1051 Transceiver:    │
│  TXCAN ──── TJA1050 TXD                 │
│  RXCAN ──── TJA1050 RXD                 │
│                                          │
│  CAN Bus Connection:                     │
│  TJA1050 CANH ──── CAN_H (bus)          │
│  TJA1050 CANL ──── CAN_L (bus)          │
│  120Ω resistor between CANH and CANL    │
│  (termination at each end of bus)        │
│                                          │
└──────────────────────────────────────────┘
```

---

## 💻 Software Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask, Flask-SocketIO |
| Frontend | HTML5, CSS3 (dark theme), JavaScript, Chart.js |
| Database | SQLite (messages, recordings, nodes, settings) |
| CAN Driver | SocketCAN (kernel), can-utils (candump/cansend/cangen) |
| CAN Library | python-can (bus abstraction) |
| CANopen | canopen (Python CANopen library) |
| DBC Parser | cantools (DBC/KCD signal decoding) |
| Auth | bcrypt hashing, 10 attempts/15min rate limit, 24h JWT sessions |
| Notifications | python-telegram-bot, slack-sdk, smtplib |
| Real-time | WebSocket via Flask-SocketIO |
| Process Manager | systemd service |

---

## 🚀 Installation

### 1. Clone & setup
```bash
ssh rasp-pi  # SSH alias for 192.168.216.90
cd /opt
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Hardware & Networking Projects/CAN Bus & CANopen Communication Hub"
```

### 2. Enable SPI and CAN overlay
```bash
# Add to /boot/config.txt (or /boot/firmware/config.txt on newer Pi OS)
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25
dtoverlay=spi-bcm2835-overlay
# Reboot
sudo reboot
```

### 3. Install SocketCAN tools
```bash
sudo apt update
sudo apt install -y can-utils
```

### 4. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Configure environment
```bash
cp .env.default .env
nano .env  # Edit CAN bitrate, features, etc.
```

### 6. Bring up CAN interface
```bash
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up
# Verify: candump can0
```

### 7. Initialize database
```bash
python3 init_db.py
```

### 8. Run as service
```bash
sudo cp deploy/can-hub.service /etc/systemd/system/
sudo systemctl enable can-hub
sudo systemctl start can-hub
```

### 9. Access dashboard
```
https://<raspberry-ip>:5000
Default login: admin / changeme (force-change on first login)
```

---

## 🔐 Environment Variables

Full `.env.default` template:

```env
# ──────────────────────────────────────
# CAN Bus & CANopen Communication Hub
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
ENABLE_SOCKETCAN_SETUP=true
ENABLE_LIVE_VIEWER=true
ENABLE_DBC_DECODER=false
ENABLE_MSG_SENDER=true
ENABLE_RECORDER=true
ENABLE_REPLAY=false
ENABLE_CANOPEN_NMT=false
ENABLE_CANOPEN_SDO=false
ENABLE_CANOPEN_PDO=false
ENABLE_OD_BROWSER=false
ENABLE_BUS_DIAG=true
ENABLE_CAN_TCP_BRIDGE=false
ENABLE_HEARTBEAT_MONITOR=false
ENABLE_MSG_FILTER=true
ENABLE_NOTIFICATIONS=false
ENABLE_ANALYTICS=true

# CAN Interface
CAN_INTERFACE=can0
CAN_BITRATE=500000
CAN_OSCILLATOR=8000000
CAN_INTERRUPT_GPIO=25
CAN_FD_ENABLED=false
CAN_FD_DBITRATE=2000000

# DBC
DBC_UPLOAD_DIR=data/dbc/
DBC_AUTO_LOAD=true

# Recorder
RECORD_OUTPUT_DIR=data/recordings/
RECORD_FORMAT=asc
RECORD_MAX_SIZE_MB=100
RECORD_AUTO_ROTATE=true

# CAN↔TCP Bridge
TCP_BRIDGE_HOST=0.0.0.0
TCP_BRIDGE_PORT=29536
TCP_BRIDGE_MAX_CLIENTS=5

# CANopen
CANOPEN_NODE_ID=1
CANOPEN_EDS_DIR=data/eds/
CANOPEN_HEARTBEAT_INTERVAL_MS=1000

# Bus Diagnostics
DIAG_POLL_INTERVAL_SEC=1
BUS_LOAD_ALERT_PCT=80
ERROR_FRAME_ALERT_COUNT=100

# Message Filtering
FILTER_ACCEPT_ALL=true
FILTER_ID_WHITELIST=
FILTER_ID_BLACKLIST=
FILTER_ID_MASK=0x7FF

# Notifications — Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Notifications — Slack
SLACK_WEBHOOK_URL=

# Notifications — Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_TO=

# Database
DB_PATH=data/can_hub.db
```

---

## 🌐 Web Dashboard

Dark-theme responsive dashboard with real-time WebSocket updates:

| Page | Description |
|------|-------------|
| **Dashboard** | CAN bus status, message rate, bus load gauge, error count, node map |
| **Live Viewer** | Real-time CAN frame stream with ID/DLC/data columns, pause/filter |
| **DBC Decoder** | Upload DBC files, view decoded signals with names and units |
| **Message Sender** | Build and send CAN frames with hex editor, repeat mode |
| **Recorder** | Start/stop recording, list saved files, download recordings |
| **Replay** | Load recording file, play back at original or scaled speed |
| **CANopen** | NMT control panel, SDO read/write, PDO mapping viewer |
| **Object Dictionary** | Tree view of node OD entries from EDS/DCF files |
| **Diagnostics** | Error frame counters, bus load chart, controller state |
| **Analytics** | Message rate trends, per-ID frequency, bus load history |
| **Settings** | Feature toggles, CAN config, bitrate, notifications, users |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate and receive JWT |
| `GET` | `/api/can/status` | CAN interface status (up/down, bitrate, bus load) |
| `POST` | `/api/can/setup` | Configure and bring up CAN interface |
| `POST` | `/api/can/send` | Send a CAN frame |
| `GET` | `/api/can/messages` | Recent CAN messages (paginated) |
| `POST` | `/api/can/filter` | Set message filter (ID range, mask) |
| `GET` | `/api/dbc` | List loaded DBC files |
| `POST` | `/api/dbc/upload` | Upload a DBC file |
| `GET` | `/api/dbc/decode/<msg_id>` | Decode a message using loaded DBC |
| `POST` | `/api/recorder/start` | Start recording CAN traffic |
| `POST` | `/api/recorder/stop` | Stop recording |
| `GET` | `/api/recorder/files` | List recording files |
| `GET` | `/api/recorder/download/<file>` | Download recording file |
| `POST` | `/api/replay/start` | Start replaying a recording |
| `POST` | `/api/replay/stop` | Stop replay |
| `GET` | `/api/canopen/nodes` | List discovered CANopen nodes |
| `POST` | `/api/canopen/nmt` | Send NMT command to node |
| `POST` | `/api/canopen/sdo/read` | SDO read (node, index, subindex) |
| `POST` | `/api/canopen/sdo/write` | SDO write (node, index, subindex, value) |
| `GET` | `/api/canopen/pdo/<node_id>` | Get PDO mappings for node |
| `GET` | `/api/canopen/od/<node_id>` | Get Object Dictionary for node |
| `POST` | `/api/canopen/eds/upload` | Upload EDS/DCF file for a node |
| `GET` | `/api/diag` | Bus diagnostics (error counters, bus load) |
| `GET` | `/api/analytics/summary` | Message rate and bus load analytics |
| `GET` | `/api/bridge/status` | TCP bridge connection status |
| `GET` | `/api/settings/features` | Get all feature toggle states |
| `PUT` | `/api/settings/features` | Update feature toggles via dashboard |

---

## 💰 Budget Estimate

| Tier | Components | Cost |
|------|-----------|------|
| **Basic** | Pi 4 + Waveshare CAN HAT + CAN cable | ~$85 |
| **Standard** | + PiCAN2 (MCP2515+TJA1050) + DB9 adapter + termination | ~$110 |
| **Full** | + Arduino CAN test node + extra transceivers + breadboard | ~$150 |

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🪙 Donations

If you find this project helpful, you can support my work:

₿ **Bitcoin:** `bc1q...`
