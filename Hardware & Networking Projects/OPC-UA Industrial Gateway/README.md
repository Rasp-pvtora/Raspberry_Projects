# 🏭 OPC-UA Industrial Gateway

A Raspberry Pi–powered OPC-UA server and industrial gateway using opcua-asyncio, with GPIO/CAN/RS232/Modbus data source plugins, dynamic node creation, address space browser, historical data access, alarms & conditions, certificate-based security, Node-RED integration, and REST API proxy — all managed from a responsive dark-theme web dashboard with per-feature toggle switches.

---

## 📋 Table of Contents
- [Features](#-features)
- [Dashboard Feature Toggles](#-dashboard-feature-toggles)
- [Hardware Requirements](#-hardware-requirements)
- [System Architecture](#-system-architecture)
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
| 1 | **OPC-UA Server (opcua-asyncio)** — Full-featured OPC-UA server with configurable endpoint, security, and namespace | `ENABLE_OPCUA_SERVER=true` | `true` |
| 2 | **GPIO Data Source Plugin** — Publish Raspberry Pi GPIO pin states as OPC-UA variables with configurable polling | `ENABLE_GPIO_SOURCE=true` | `true` |
| 3 | **CAN Bus Data Source Plugin** — Bridge CAN/CANopen signals to OPC-UA address space via MCP2515 HAT | `ENABLE_CAN_SOURCE=true` | `false` |
| 4 | **RS232 Serial Data Source Plugin** — Map RS232 serial data to OPC-UA variables via MAX3232 or USB adapter | `ENABLE_RS232_SOURCE=true` | `false` |
| 5 | **Modbus TCP/RTU Data Source Plugin** — Read/write Modbus registers and coils mapped to OPC-UA nodes | `ENABLE_MODBUS_SOURCE=true` | `false` |
| 6 | **Dynamic Node Creation** — Create, modify, and delete OPC-UA nodes at runtime from the dashboard | `ENABLE_DYNAMIC_NODES=true` | `true` |
| 7 | **Address Space Browser** — Visual tree-view explorer of the OPC-UA address space with node attributes | `ENABLE_AS_BROWSER=true` | `true` |
| 8 | **Historical Data Access (HDA)** — Store and expose time-series data for OPC-UA historical read requests | `ENABLE_HDA=true` | `true` |
| 9 | **Alarms & Conditions** — Configurable alarm limits per node with OPC-UA alarm object notifications | `ENABLE_ALARMS=true` | `false` |
| 10 | **Certificate Security** — X.509 certificate generation, trust management, and security policy configuration | `ENABLE_CERT_SECURITY=true` | `true` |
| 11 | **Node-RED Integration** — Embedded Node-RED instance with node-red-contrib-opcua for visual flow programming | `ENABLE_NODERED=true` | `false` |
| 12 | **REST API Proxy** — Mirror OPC-UA address space via REST/JSON for non-OPC-UA clients | `ENABLE_REST_PROXY=true` | `true` |
| 13 | **CODESYS Runtime Info** — Display CODESYS runtime status and variable mapping hints on dashboard | `ENABLE_CODESYS_INFO=true` | `false` |
| 14 | **Data Source Mapping Editor** — Drag-and-drop mapping UI to connect data sources → OPC-UA nodes | `ENABLE_MAPPING_EDITOR=true` | `true` |
| 15 | **Multi-Channel Notifications** — Alerts via Telegram, Slack, email for alarms, node failures, server errors | `ENABLE_NOTIFICATIONS=true` | `false` |
| 16 | **Server Diagnostics** — Session count, subscription stats, publish rate, memory usage, uptime monitoring | `ENABLE_DIAGNOSTICS=true` | `true` |
| 17 | **Historical Analytics Dashboard** — Trend charts, data export, alarm history, and data source health overview | `ENABLE_ANALYTICS=true` | `true` |

---

## 🎛️ Dashboard Feature Toggles

The web dashboard provides a **Settings → Feature Toggles** page where each feature can be enabled/disabled in real time without restarting the service. Toggle state is persisted to `.env` and SQLite.
```
┌──────────────────────────────────────────────────┐
│  ⚙️ Feature Toggles              [Save All]      │
├──────────────────────────────────────────────────┤
│  🖥️ OPC-UA Server               [████ ON ]         │
│  📌 GPIO Data Source            [████ ON ]         │
│  🚛 CAN Bus Source              [░░░░ OFF]         │
│  🔌 RS232 Serial Source         [░░░░ OFF]         │
│  📡 Modbus TCP/RTU Source       [░░░░ OFF]         │
│  ➕ Dynamic Node Creation       [████ ON ]         │
│  🌳 Address Space Browser       [████ ON ]         │
│  📈 Historical Data Access      [████ ON ]         │
│  ⚠️ Alarms & Conditions         [░░░░ OFF]         │
│  🔐 Certificate Security        [████ ON ]         │
│  🔴 Node-RED Integration        [░░░░ OFF]         │
│  🌐 REST API Proxy              [████ ON ]         │
│  🏗️ CODESYS Info                [░░░░ OFF]         │
│  🔗 Data Source Mapping         [████ ON ]         │
│  🔔 Notifications               [░░░░ OFF]         │
│  🔍 Server Diagnostics          [████ ON ]         │
│  📊 Analytics                   [████ ON ]         │
└──────────────────────────────────────────────────┘
```
---

## 🔩 Hardware Requirements

| Component | Model / Spec | Qty | Est. Cost |
|-----------|-------------|-----|-----------|
| Raspberry Pi | 4B (4GB+) or 5 | 1 | $55–80 |
| CAN HAT (optional) | Waveshare RS485 CAN HAT (MCP2515 + TJA1050) | 0–1 | $15–30 |
| RS232 Adapter (optional) | Serial Pi Plus HAT or USB-to-RS232 (MAX3232) | 0–1 | $8–15 |
| Modbus RTU Adapter (optional) | USB-to-RS485 dongle | 0–1 | $8–12 |
| GPIO Sensors | DHT22, buttons, LEDs (for GPIO source demo) | 1–4 | $2–6 each |
| MicroSD Card | 32GB+ Class 10 | 1 | $8 |
| Power Supply | 5V 3A USB-C | 1 | $10 |
| **Total** | | | **$75–175** |

> **Note:** Only the Raspberry Pi + MicroSD are required. All data source plugins (CAN, RS232, Modbus) are optional and depend on your use case.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SCADA / HMI Client                       │
│                  (UaExpert, Prosys, CODESYS)                 │
└──────────────┬──────────────────────────────────────────────┘
               │ OPC-UA Binary (opc.tcp://pi:4840)
┌──────────────┴──────────────────────────────────────────────┐
│                   Raspberry Pi OPC-UA Gateway                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            opcua-asyncio Server (Port 4840)           │   │
│  │                                                       │   │
│  │  Namespace 0: OPC-UA Standard                         │   │
│  │  Namespace 2: Pi Gateway (dynamic nodes)              │   │
│  │                                                       │   │
│  │  Address Space:                                       │   │
│  │  ├── GPIO/                                            │   │
│  │  │   ├── Pin4_Temperature (22.5 °C)                   │   │
│  │  │   └── Pin17_Button (true)                          │   │
│  │  ├── CAN/                                             │   │
│  │  │   ├── EngineRPM (3500 rpm)                         │   │
│  │  │   └── Coolant_Temp (85 °C)                         │   │
│  │  ├── Serial/                                          │   │
│  │  │   └── RS232_Weight (42.7 kg)                       │   │
│  │  └── Modbus/                                          │   │
│  │      ├── Holding_40001 (1234)                         │   │
│  │      └── Coil_00001 (true)                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐               │
│  │  GPIO  │ │  CAN   │ │ RS232  │ │ Modbus │               │
│  │ Plugin │ │ Plugin │ │ Plugin │ │ Plugin │               │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘               │
│      │          │          │          │                      │
│   RPi.GPIO   MCP2515    MAX3232   RS485 dongle              │
│              SocketCAN  /dev/ttyS0 pymodbus                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Web Dashboard (Flask :5000) + REST Proxy + Node-RED  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

Pipeline: **Sensors/GPIO → Python Source Plugin → OPC-UA Address Space → SCADA/HMI Client**

---

## 💻 Software Stack

| Layer | Technology |
|-------|-----------|
| OPC-UA Server | opcua-asyncio (Python asyncio OPC-UA) |
| Backend | Python 3.11+, Flask, Flask-SocketIO |
| Frontend | HTML5, CSS3 (dark theme), JavaScript, Chart.js |
| Database | SQLite (nodes, history, alarms, settings, users) |
| GPIO | RPi.GPIO / gpiozero |
| CAN | python-can, SocketCAN, cantools (DBC) |
| Serial | pyserial (/dev/ttyS0 or /dev/ttyUSB0) |
| Modbus | pymodbus (TCP + RTU) |
| Node-RED | node-red, node-red-contrib-opcua |
| Auth | bcrypt hashing, 10 attempts/15min rate limit, 24h JWT sessions |
| OPC-UA Security | X.509 certificates, Basic256Sha256, SignAndEncrypt |
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
cd "Raspberry_Projects/Hardware & Networking Projects/OPC-UA Industrial Gateway"
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
nano .env  # Edit OPC-UA endpoint, data sources, security
```

### 4. Generate OPC-UA certificates (optional, recommended)
```bash
python3 scripts/generate_certs.py
```

### 5. Initialize database
```bash
python3 init_db.py
```

### 6. Install Node-RED (optional)
```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
npm install -g node-red-contrib-opcua
```

### 7. Run as service
```bash
sudo cp deploy/opcua-gateway.service /etc/systemd/system/
sudo systemctl enable opcua-gateway
sudo systemctl start opcua-gateway
```

### 8. Access
```
OPC-UA endpoint: opc.tcp://<raspberry-ip>:4840
Web dashboard:   https://<raspberry-ip>:5000
Default login:   admin / changeme (force-change on first login)
```

---

## 🔐 Environment Variables

Full `.env.default` template:

```env
# ──────────────────────────────────────
# OPC-UA Industrial Gateway
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
ENABLE_OPCUA_SERVER=true
ENABLE_GPIO_SOURCE=true
ENABLE_CAN_SOURCE=false
ENABLE_RS232_SOURCE=false
ENABLE_MODBUS_SOURCE=false
ENABLE_DYNAMIC_NODES=true
ENABLE_AS_BROWSER=true
ENABLE_HDA=true
ENABLE_ALARMS=false
ENABLE_CERT_SECURITY=true
ENABLE_NODERED=false
ENABLE_REST_PROXY=true
ENABLE_CODESYS_INFO=false
ENABLE_MAPPING_EDITOR=true
ENABLE_NOTIFICATIONS=false
ENABLE_DIAGNOSTICS=true
ENABLE_ANALYTICS=true

# OPC-UA Server
OPCUA_ENDPOINT=opc.tcp://0.0.0.0:4840/ua/server
OPCUA_SERVER_NAME=RaspberryPi OPC-UA Gateway
OPCUA_NAMESPACE=urn:raspberry:opcua:gateway
OPCUA_SECURITY_POLICY=Basic256Sha256
OPCUA_SECURITY_MODE=SignAndEncrypt
OPCUA_CERT_PATH=certs/server_cert.pem
OPCUA_KEY_PATH=certs/server_key.pem
OPCUA_TRUST_DIR=certs/trusted/

# GPIO Data Source
GPIO_POLL_INTERVAL_MS=1000
GPIO_PIN_CONFIG=config/gpio_sources.json

# CAN Data Source
CAN_INTERFACE=can0
CAN_BITRATE=500000
CAN_DBC_PATH=config/can.dbc

# RS232 Data Source
RS232_PORT=/dev/ttyS0
RS232_BAUDRATE=9600
RS232_PARITY=N
RS232_DATABITS=8
RS232_STOPBITS=1

# Modbus Data Source
MODBUS_HOST=127.0.0.1
MODBUS_PORT=502
MODBUS_UNIT_ID=1
MODBUS_POLL_INTERVAL_MS=500

# Historical Data Access
HDA_RETENTION_DAYS=90
HDA_SAMPLE_INTERVAL_MS=1000
HDA_MAX_POINTS_PER_READ=10000

# Alarms
ALARM_CHECK_INTERVAL_SEC=1
ALARM_SEVERITY_MAP=config/alarm_config.json

# Node-RED
NODERED_PORT=1880
NODERED_FLOW_DIR=data/nodered_flows/

# CODESYS Info
CODESYS_RUNTIME_HOST=127.0.0.1
CODESYS_RUNTIME_PORT=11740

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
DB_PATH=data/opcua_gateway.db
```

---

## 🌐 Web Dashboard

Dark-theme responsive dashboard with real-time WebSocket updates:

| Page | Description |
|------|-------------|
| **Dashboard** | OPC-UA server status, active sessions, data source health, alarm summary |
| **Address Space** | Tree-view OPC-UA node browser with attributes, values, references |
| **Data Sources** | Status cards for GPIO/CAN/RS232/Modbus plugins with live values |
| **Mapping Editor** | Drag-and-drop data source → OPC-UA node mapping interface |
| **Node Manager** | Create, edit, delete OPC-UA nodes and folders dynamically |
| **Historical Data** | Time-series charts, date-range queries, data export |
| **Alarms** | Active alarm list, alarm history, severity configuration |
| **Certificates** | Upload/trust/reject client certificates, generate server cert |
| **Node-RED** | Embedded Node-RED editor iframe (when enabled) |
| **Diagnostics** | Server metrics: sessions, subscriptions, publish rate, memory |
| **Analytics** | Trend lines, alarm frequency, data source uptime, export |
| **Settings** | Feature toggles, OPC-UA config, data source settings, users |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate and receive JWT |
| `GET` | `/api/opcua/status` | Server status (running, sessions, subscriptions) |
| `POST` | `/api/opcua/start` | Start OPC-UA server |
| `POST` | `/api/opcua/stop` | Stop OPC-UA server |
| `GET` | `/api/nodes` | Browse address space (tree or flat) |
| `GET` | `/api/nodes/<node_id>` | Get node details (attributes, value, references) |
| `POST` | `/api/nodes` | Create new OPC-UA node |
| `PUT` | `/api/nodes/<node_id>` | Update node value or attributes |
| `DELETE` | `/api/nodes/<node_id>` | Delete node from address space |
| `GET` | `/api/sources` | List all data source plugins and status |
| `GET` | `/api/sources/gpio` | GPIO source status and pin values |
| `GET` | `/api/sources/can` | CAN source status and signal values |
| `GET` | `/api/sources/serial` | RS232 source status and data |
| `GET` | `/api/sources/modbus` | Modbus source status and register values |
| `GET` | `/api/mappings` | List data source → node mappings |
| `POST` | `/api/mappings` | Create new mapping |
| `DELETE` | `/api/mappings/<id>` | Remove mapping |
| `GET` | `/api/history/<node_id>` | Historical data for a node (from, to, limit) |
| `GET` | `/api/alarms` | Active and historical alarms |
| `POST` | `/api/alarms/config` | Configure alarm limits for a node |
| `PUT` | `/api/alarms/<id>/ack` | Acknowledge alarm |
| `GET` | `/api/certs` | List trusted certificates |
| `POST` | `/api/certs/upload` | Upload client certificate |
| `POST` | `/api/certs/generate` | Generate new server certificate |
| `GET` | `/api/diag` | Server diagnostics (sessions, memory, uptime) |
| `GET` | `/api/analytics/summary` | Aggregated analytics data |
| `GET` | `/api/rest/<path>` | REST proxy — read OPC-UA node by browse path |
| `PUT` | `/api/rest/<path>` | REST proxy — write OPC-UA node value |
| `GET` | `/api/settings/features` | Get all feature toggle states |
| `PUT` | `/api/settings/features` | Update feature toggles via dashboard |

---

## 💰 Budget Estimate

| Tier | Components | Cost |
|------|-----------|------|
| **Basic** | Pi 4 (4GB) + GPIO sensors + MicroSD | ~$75 |
| **Standard** | + CAN HAT or RS232 adapter + Modbus dongle | ~$120 |
| **Full** | + All adapters + multiple sensors + industrial setup | ~$175 |

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🪙 Donations

If you find this project helpful, you can support my work:

₿ **Bitcoin:** `bc1q...`
