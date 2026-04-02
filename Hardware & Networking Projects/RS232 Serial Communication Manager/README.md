# 📡 RS232 Serial Communication Manager

> **A multi-port RS232/UART serial communication dashboard for Raspberry Pi** — manage multiple serial ports simultaneously with hex/ASCII views, Modbus RTU templates, message macros, CRC calculators, auto-response rules, serial↔TCP bridging, protocol analysis, and a dark-themed web interface with real-time data plotting.

---

## 📑 Table of Contents
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Hardware Requirements](#-hardware-requirements)
- [Software Requirements](#-software-requirements)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [API Endpoints](#-api-endpoints)
- [WebSocket Events](#-websocket-events)
- [Web Dashboard](#-web-dashboard)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Budget Estimate](#-budget-estimate)
- [License](#-license)

---

## 🌟 Features

Every feature can be toggled ON/OFF via `.env` **and** the web dashboard Settings page (toggle switches with bidirectional sync).

| # | Feature | `.env` Toggle | Default |
|---|---------|---------------|---------|
| 1 | **Auto Port Detection** — scan `/dev/ttyUSB*`, `/dev/ttyS*`, `/dev/ttyAMA*` with device identification | `ENABLE_AUTO_DETECT=true` | ✅ ON |
| 2 | **Multi-Port Support** — open, configure, and manage up to 8 serial ports simultaneously | `ENABLE_MULTI_PORT=true` | ✅ ON |
| 3 | **Hex / ASCII Dual View** — side-by-side hex dump and ASCII text with synchronized scrolling | `ENABLE_HEX_VIEW=true` | ✅ ON |
| 4 | **Message Builder with CRC** — construct frames with header/payload/CRC (CRC-8, CRC-16, CRC-32, Modbus CRC) | `ENABLE_MSG_BUILDER=true` | ✅ ON |
| 5 | **Modbus RTU Templates** — pre-built function code templates (FC01–FC06, FC15, FC16) with address calculator | `ENABLE_MODBUS_RTU=true` | ✅ ON |
| 6 | **Auto-Response Rules** — pattern-matching rules that automatically send replies to incoming messages | `ENABLE_AUTO_RESPONSE=true` | ✅ ON |
| 7 | **Serial ↔ TCP Bridge** — expose serial ports as TCP sockets for remote access (RFC 2217 compatible) | `ENABLE_TCP_BRIDGE=true` | ✅ ON |
| 8 | **Real-Time Data Plotting** — Chart.js live graphs for numeric data streams (voltage, temperature, etc.) | `ENABLE_DATA_PLOTTING=true` | ✅ ON |
| 9 | **Message Macros** — save, name, and quick-send frequently used command sequences | `ENABLE_MACROS=true` | ✅ ON |
| 10 | **REST API** — full API for all serial operations (open/close/read/write/config) | `ENABLE_REST_API=true` | ✅ ON |
| 11 | **Protocol Analyzer** — decode common protocols (Modbus RTU, NMEA 0183, custom frame parsers) | `ENABLE_PROTOCOL_ANALYZER=true` | ✅ ON |
| 12 | **Session Recording** — record all TX/RX data to timestamped log files (binary + text) | `ENABLE_SESSION_RECORDING=true` | ✅ ON |
| 13 | **Port Profiles** — save/load complete port configuration profiles (baud, parity, stop bits, flow control) | `ENABLE_PORT_PROFILES=true` | ✅ ON |
| 14 | **Notifications** — Telegram, Slack, and email alerts for disconnect, error, and pattern-match events | `ENABLE_NOTIFICATIONS=true` | ✅ ON |
| 15 | **Connection Statistics** — bytes TX/RX, error counts, uptime, throughput graphs per port | `ENABLE_CONN_STATS=true` | ✅ ON |
| 16 | **Scripting Engine** — Python scripting console for custom serial automation sequences | `ENABLE_SCRIPTING=true` | ❌ OFF |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Web Dashboard (Flask)                  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│  │Ports │ │Hex/  │ │Modbus│ │Macros│ │Plot  │         │
│  │List  │ │ASCII │ │RTU   │ │Panel │ │View  │         │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘         │
│     └────────┴────────┴────────┴────────┘               │
│                    WebSocket (real-time)                 │
├─────────────────────────────────────────────────────────┤
│                    Flask + SocketIO                      │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐               │
│  │Port      │ │Protocol   │ │TCP Bridge│               │
│  │Manager   │ │Analyzer   │ │Server    │               │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘               │
│       └──────────────┴────────────┘                     │
│              pyserial (Serial I/O)                       │
├─────────────────────────────────────────────────────────┤
│  /dev/ttyUSB0  /dev/ttyUSB1  /dev/ttyS0  /dev/ttyAMA0  │
│    USB-RS232     USB-RS232     UART        GPIO UART    │
│    (MAX3232)     (FTDI)       (on-board)   (Pi header)  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Hardware Requirements

| Component | Purpose | Est. Cost |
|-----------|---------|-----------|
| Raspberry Pi 3B+/4B/5 | Main controller | $35–$80 |
| USB-to-RS232 adapter (FTDI/CH340) | Serial port connection | $5–$15 each |
| MAX3232 module (3.3V↔RS232) | Level shifting for GPIO UART | $2–$5 |
| Serial Pi Plus HAT (optional) | Direct RS232 on GPIO header | $15–$25 |
| DB9 cables / connectors | Physical connections | $3–$8 |
| MicroSD card (16GB+) | OS + data storage | $8–$15 |

> ⚠️ **Pi UART is 3.3V** — connecting directly to RS232 (±12V) will damage the Pi. Always use MAX3232 or USB adapter.

### Wiring — USB Adapter (Recommended)
```
USB-RS232 Adapter ──USB──► Raspberry Pi USB Port
         └── DB9 ──────► Target RS232 Device
```

### Wiring — GPIO UART with MAX3232
```
Pi GPIO14 (TXD) ──► MAX3232 T1IN ──► DB9 Pin 3 (TX)
Pi GPIO15 (RXD) ◄── MAX3232 R1OUT ◄── DB9 Pin 2 (RX)
Pi GND ──────────── MAX3232 GND ──── DB9 Pin 5 (GND)
Pi 3.3V ─────────── MAX3232 VCC
```

---

## 💻 Software Requirements

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.11+ | Runtime |
| Flask | 3.1.x | Web framework |
| Flask-SocketIO | 5.3.x | WebSocket support |
| pyserial | 3.5.x | Serial I/O |
| crcmod | 1.7.x | CRC calculations |
| SQLite | 3.x | Database (built-in) |
| Chart.js | 4.x | Data plotting (CDN) |
| bcrypt | 4.2.x | Password hashing |
| PyJWT | 2.9.x | JWT authentication |
| python-telegram-bot | 21.x | Telegram notifications |

---

## 🚀 Quick Start

```bash
# 1. Clone and enter project
cd "Hardware & Networking Projects/RS232 Serial Communication Manager"

# 2. Create virtual environment
python3 -m venv venv && source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Enable UART on Raspberry Pi (GPIO UART)
sudo raspi-config  # → Interface Options → Serial Port → Yes

# 5. Configure environment
cp .env.example .env
nano .env

# 6. Initialize database
python3 src/init_db.py

# 7. Launch application
python3 src/app.py

# 8. Open dashboard
# http://<raspberry-pi-ip>:5000
```

### Deploy as System Service
```bash
chmod +x deploy/deploy_to_pi.sh
./deploy/deploy_to_pi.sh
# Access: http://<pi-ip>:5000
```

---

## ⚙️ Environment Variables

```env
# ── Server ───────────────────────────────────
HOST=0.0.0.0
PORT=5000
SECRET_KEY=change-me-to-random-secret
DEBUG=false
LOG_LEVEL=INFO

# ── Database ─────────────────────────────────
DB_PATH=data/serial_manager.db

# ── Authentication ───────────────────────────
ADMIN_USER=admin
ADMIN_PASS=change-me
JWT_EXPIRY_HOURS=24
LOGIN_RATE_LIMIT=10/15m

# ── Serial Defaults ─────────────────────────
DEFAULT_BAUD_RATE=9600
DEFAULT_DATA_BITS=8
DEFAULT_PARITY=N
DEFAULT_STOP_BITS=1
DEFAULT_FLOW_CONTROL=none
DEFAULT_TIMEOUT_SEC=1
MAX_PORTS=8

# ── Feature Toggles ─────────────────────────
ENABLE_AUTO_DETECT=true
ENABLE_MULTI_PORT=true
ENABLE_HEX_VIEW=true
ENABLE_MSG_BUILDER=true
ENABLE_MODBUS_RTU=true
ENABLE_AUTO_RESPONSE=true
ENABLE_TCP_BRIDGE=true
ENABLE_DATA_PLOTTING=true
ENABLE_MACROS=true
ENABLE_REST_API=true
ENABLE_PROTOCOL_ANALYZER=true
ENABLE_SESSION_RECORDING=true
ENABLE_PORT_PROFILES=true
ENABLE_NOTIFICATIONS=true
ENABLE_CONN_STATS=true
ENABLE_SCRIPTING=false

# ── TCP Bridge ───────────────────────────────
TCP_BRIDGE_BASE_PORT=9000
TCP_BRIDGE_MAX_CLIENTS=10
TCP_BRIDGE_TIMEOUT_SEC=300

# ── Modbus RTU ───────────────────────────────
MODBUS_DEFAULT_SLAVE_ID=1
MODBUS_RESPONSE_TIMEOUT_MS=1000
MODBUS_MAX_RETRIES=3

# ── Session Recording ───────────────────────
RECORDING_DIR=data/recordings
RECORDING_FORMAT=both
RECORDING_MAX_SIZE_MB=100
RECORDING_RETENTION_DAYS=30

# ── Data Plotting ────────────────────────────
PLOT_MAX_POINTS=500
PLOT_REFRESH_MS=200
PLOT_NUMERIC_REGEX=[-+]?\d*\.?\d+

# ── Scripting Engine ─────────────────────────
SCRIPT_DIR=data/scripts
SCRIPT_TIMEOUT_SEC=30
SCRIPT_SANDBOX=true

# ── Notifications ────────────────────────────
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SLACK_WEBHOOK_URL=
SMTP_SERVER=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
ALERT_EMAIL_TO=

# ── Protocol Analyzer ───────────────────────
PROTOCOL_MODBUS_ENABLED=true
PROTOCOL_NMEA_ENABLED=true
CUSTOM_PARSER_DIR=config/parsers
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login → JWT token |
| `POST` | `/api/auth/logout` | Invalidate session |

### Port Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ports` | List all detected serial ports |
| `GET` | `/api/ports/:id` | Get port details & status |
| `POST` | `/api/ports/:id/open` | Open port with config |
| `POST` | `/api/ports/:id/close` | Close port |
| `PUT` | `/api/ports/:id/config` | Update port settings |
| `GET` | `/api/ports/:id/stats` | Connection statistics |

### Data Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ports/:id/send` | Send data (hex or ASCII) |
| `POST` | `/api/ports/:id/send-file` | Send file contents to port |
| `GET` | `/api/ports/:id/buffer` | Read receive buffer |
| `DELETE` | `/api/ports/:id/buffer` | Clear receive buffer |

### Modbus RTU
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/modbus/read-coils` | FC01 — Read Coils |
| `POST` | `/api/modbus/read-discrete` | FC02 — Read Discrete Inputs |
| `POST` | `/api/modbus/read-holding` | FC03 — Read Holding Registers |
| `POST` | `/api/modbus/read-input` | FC04 — Read Input Registers |
| `POST` | `/api/modbus/write-coil` | FC05 — Write Single Coil |
| `POST` | `/api/modbus/write-register` | FC06 — Write Single Register |
| `POST` | `/api/modbus/write-coils` | FC15 — Write Multiple Coils |
| `POST` | `/api/modbus/write-registers` | FC16 — Write Multiple Registers |

### TCP Bridge
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/bridge` | List active TCP bridges |
| `POST` | `/api/bridge` | Create serial↔TCP bridge |
| `DELETE` | `/api/bridge/:id` | Destroy bridge |
| `GET` | `/api/bridge/:id/clients` | List connected TCP clients |

### Macros
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/macros` | List saved macros |
| `POST` | `/api/macros` | Create macro |
| `PUT` | `/api/macros/:id` | Update macro |
| `DELETE` | `/api/macros/:id` | Delete macro |
| `POST` | `/api/macros/:id/execute` | Execute macro on port |

### Auto-Response Rules
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/auto-response` | List rules |
| `POST` | `/api/auto-response` | Create rule |
| `PUT` | `/api/auto-response/:id` | Update rule |
| `DELETE` | `/api/auto-response/:id` | Delete rule |

### Port Profiles
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/profiles` | List port profiles |
| `POST` | `/api/profiles` | Save current config as profile |
| `POST` | `/api/profiles/:id/apply` | Apply profile to port |
| `DELETE` | `/api/profiles/:id` | Delete profile |

### Session Recording
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/recording/:port/start` | Start recording |
| `POST` | `/api/recording/:port/stop` | Stop recording |
| `GET` | `/api/recording` | List recordings |
| `GET` | `/api/recording/:id/download` | Download recording file |
| `DELETE` | `/api/recording/:id` | Delete recording |

### Protocol Analyzer
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/protocol/parsers` | List available protocol parsers |
| `POST` | `/api/protocol/decode` | Decode raw bytes with parser |
| `POST` | `/api/protocol/encode` | Encode structured data to bytes |

### Scripting
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/scripts` | List saved scripts |
| `POST` | `/api/scripts` | Save script |
| `POST` | `/api/scripts/:id/run` | Execute script |
| `POST` | `/api/scripts/eval` | Execute inline script |
| `DELETE` | `/api/scripts/:id` | Delete script |

### Settings & Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/settings/features` | Get all feature toggle states |
| `PUT` | `/api/settings/features` | Update feature toggles |

---

## 🔌 WebSocket Events

### Client → Server
| Event | Payload | Description |
|-------|---------|-------------|
| `open_port` | `{port, baud, parity, ...}` | Open serial port |
| `close_port` | `{port}` | Close serial port |
| `send_data` | `{port, data, encoding}` | Send data (hex/ascii) |
| `start_recording` | `{port}` | Start recording session |
| `stop_recording` | `{port}` | Stop recording |
| `toggle_feature` | `{feature, enabled}` | Toggle feature flag |

### Server → Client
| Event | Payload | Description |
|-------|---------|-------------|
| `serial_data` | `{port, hex, ascii, timestamp}` | Incoming serial data |
| `port_opened` | `{port, config}` | Port opened confirmation |
| `port_closed` | `{port}` | Port closed confirmation |
| `port_error` | `{port, error}` | Serial port error |
| `port_detected` | `{port, description}` | New port detected |
| `port_removed` | `{port}` | Port disconnected |
| `modbus_response` | `{port, fc, data}` | Modbus response decoded |
| `bridge_client` | `{bridge_id, client, event}` | TCP bridge client event |
| `plot_data` | `{port, value, timestamp}` | Numeric value for plotting |
| `protocol_decoded` | `{port, protocol, decoded}` | Protocol frame decoded |
| `stats_update` | `{port, tx, rx, errors}` | Connection statistics |
| `feature_toggled` | `{feature, enabled}` | Feature state changed |
| `notification` | `{type, message}` | Alert notification |

---

## 🖥️ Web Dashboard

Dark-themed responsive interface with the following pages:

| Page | Path | Description |
|------|------|-------------|
| **Login** | `/login` | bcrypt auth with rate limiting |
| **Dashboard** | `/` | Port overview, quick status, system health |
| **Port Manager** | `/ports` | Open/close/configure ports, view details |
| **Terminal** | `/terminal` | Hex/ASCII dual view, send/receive console |
| **Modbus RTU** | `/modbus` | Function code templates, register viewer |
| **Macros** | `/macros` | Manage and execute message macros |
| **Data Plot** | `/plotting` | Real-time Chart.js graphs |
| **TCP Bridge** | `/bridge` | Serial↔TCP bridge management |
| **Recordings** | `/recordings` | Session recording playback/download |
| **Protocol** | `/protocol` | Protocol analyzer & decoder |
| **Scripts** | `/scripts` | Scripting console (when enabled) |
| **Settings** | `/settings` | Feature toggles, notifications, system config |

---

## 🔒 Security

- **Authentication**: bcrypt-hashed passwords, JWT sessions (24h default)
- **Rate limiting**: 10 login attempts per 15 minutes
- **Input validation**: All serial data validated/encoded before transmission
- **TCP bridge**: Optional IP whitelist, max client limits, timeout enforcement
- **Scripting sandbox**: Restricted `exec()` with timeout and limited imports
- **No direct shell access**: All port operations go through pyserial API

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port not detected | Check USB connection, run `ls /dev/ttyUSB*` |
| Permission denied | Add user to `dialout` group: `sudo usermod -aG dialout $USER` |
| GPIO UART not working | Enable UART in `raspi-config`, disable serial console |
| Garbled data | Verify baud rate, parity, stop bits match remote device |
| TCP bridge timeout | Increase `TCP_BRIDGE_TIMEOUT_SEC` |
| Modbus CRC error | Check slave ID, verify wiring, try lower baud rate |
| MAX3232 no output | Verify 3.3V supply, check TX/RX not swapped |

---

## 💰 Budget Estimate

| Tier | Components | Cost |
|------|-----------|------|
| **Minimal** | Pi 3B+ + 1× USB-RS232 adapter | ~$45 |
| **Standard** | Pi 4B + 2× USB-RS232 + MAX3232 module | ~$75 |
| **Full** | Pi 4B + Serial Pi HAT + 2× USB-RS232 + adapters + cables | ~$120 |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
