# PLC Replacement with OpenPLC

Install OpenPLC Runtime on the Raspberry Pi to turn its GPIOs into an **IEC 61131-3 compliant Programmable Logic Controller**. Program using industry-standard languages — Ladder Logic (LD), Structured Text (ST), and Function Block Diagram (FBD) — via OpenPLC Editor. Includes ScadaBR for SCADA visualization, Modbus TCP/RTU communication, industrial I/O expansion via MCP23017, fail-safe watchdog timers, a pre-built program library (traffic light, motor start/stop, tank level, conveyor belt), OPC-UA integration, and data logging to SQLite. Managed through a dark-themed Flask web dashboard with bcrypt authentication.

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
- [Features](#features)
  - [OpenPLC Runtime on Pi GPIO](#openplc-runtime-on-pi-gpio)
  - [IEC 61131-3 Programming Languages](#iec-61131-3-programming-languages)
  - [ScadaBR SCADA Visualization](#scadabr-scada-visualization)
  - [Modbus TCP/RTU Communication](#modbus-tcprtu-communication)
  - [I/O Expansion (MCP23017)](#io-expansion-mcp23017)
  - [Fail-Safe Watchdog Timers](#fail-safe-watchdog-timers)
  - [Program Library](#program-library)
  - [OPC-UA Server](#opc-ua-server)
  - [Data Logging](#data-logging)
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
PLC Replacement with OpenPLC/
├── README.md                   # This file
├── TSD.md                      # Technical Specification Document
├── task.md                     # Development task checklist
├── implementation_plan.md      # Phased implementation guide
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
├── .env.example                # Environment variable template
├── src/
│   ├── __init__.py
│   ├── app.py                  # Flask app factory & web dashboard
│   ├── plc_runtime.py          # OpenPLC Runtime bridge & GPIO mapping
│   ├── modbus_handler.py       # Modbus TCP/RTU master/slave handler
│   ├── io_expansion.py         # MCP23017 I2C I/O expansion driver
│   ├── watchdog.py             # Fail-safe watchdog timer manager
│   ├── program_library.py      # Pre-built PLC program manager
│   ├── opcua_server.py         # OPC-UA server integration
│   ├── data_logger.py          # SQLite data logging engine
│   ├── scada_bridge.py         # ScadaBR integration & data exchange
│   ├── database.py             # SQLite DB models & helpers
│   ├── auth.py                 # bcrypt auth & session management
│   ├── config.py               # .env loader & config dataclass
│   └── utils.py                # Shared utilities
├── templates/
│   ├── base.html               # Dark theme layout
│   ├── login.html              # Login page
│   ├── dashboard.html          # Main monitoring dashboard
│   ├── io_monitor.html         # Real-time I/O state viewer
│   ├── programs.html           # PLC program management page
│   ├── modbus.html             # Modbus configuration page
│   ├── alarms.html             # Alarm history & active alarms
│   ├── data_logs.html          # Data log viewer with charts
│   └── settings.html           # Runtime settings panel
├── static/
│   ├── css/
│   │   └── style.css           # Dark theme styles
│   └── js/
│       ├── dashboard.js        # SocketIO client & live I/O updates
│       ├── charts.js           # Data logging chart rendering
│       └── modbus.js           # Modbus config UI logic
├── programs/
│   ├── traffic_light.st        # Traffic light sequencer (Structured Text)
│   ├── motor_start_stop.st     # Motor start/stop with interlock
│   ├── tank_level.st           # Tank level control with PID
│   └── conveyor_belt.st        # Conveyor belt with sensor logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures & mock mode helpers
│   ├── test_plc_runtime.py     # Runtime bridge tests
│   ├── test_modbus.py          # Modbus communication tests
│   ├── test_io_expansion.py    # MCP23017 driver tests
│   ├── test_watchdog.py        # Watchdog timer tests
│   ├── test_opcua.py           # OPC-UA server tests
│   ├── test_data_logger.py     # Data logging tests
│   ├── test_auth.py            # Auth & session tests
│   ├── test_api.py             # Dashboard API endpoint tests
│   └── test_database.py        # Database CRUD tests
├── deploy/
│   └── deploy_to_pi.sh         # rsync deploy script (rasp-pi)
├── scripts/
│   ├── install_openplc.sh      # OpenPLC Runtime installer
│   ├── install_scadabr.sh      # ScadaBR installer
│   ├── install_deps.sh         # OS-level dependency installer
│   └── generate_password_hash.sh # Helper to generate bcrypt hash
└── docs/
    ├── wiring_guide.md         # GPIO & relay wiring diagrams
    ├── modbus_reference.md     # Modbus register map documentation
    └── program_guide.md        # PLC programming quick-start guide
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 or 5 | Yes | Runs OpenPLC Runtime on GPIO |
| Relay module (4/8-channel) | Yes | Switches for outputs (motors, solenoids, lights) |
| Optocoupled input module | Yes | Isolated digital inputs from field devices |
| Sensors (temp, level, proximity) | Yes | Process variable inputs |
| MicroSD card (16GB+) | Yes | OS, OpenPLC, programs, data logs |
| Power supply (5V/3A) | Yes | Clean isolated power recommended |
| MCP23017 I/O expander (optional) | No | Additional 16 GPIO pins via I2C |
| PiXtend HAT (optional) | No | Industrial-grade I/O with analog channels (~$100) |
| DIN rail case (optional) | No | Industrial enclosure for panel mounting |

---

## Budget

| Item | Estimated Cost |
|---|---|
| Raspberry Pi 4/5 (already owned) | $0 |
| Relay module (4/8-channel) | ~$5–10 |
| Optocoupled input module | ~$8–12 |
| Sensors (temp, level, proximity) | ~$5–15 |
| PiXtend HAT (optional) | ~$100 |
| DIN rail case (optional) | ~$10 |
| **Total (basic)** | **~$25–50** |
| **Total (professional with PiXtend)** | **~$140** |

*(Assumes you already have a Raspberry Pi and SD card.)*

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| OpenPLC Runtime | IEC 61131-3 PLC runtime engine on Pi GPIO |
| ScadaBR | SCADA visualization and HMI |
| python-opcua | OPC-UA server for industrial integration |
| pymodbus | Modbus TCP/RTU master/slave communication |
| smbus2 | I2C interface for MCP23017 I/O expansion |
| RPi.GPIO | Direct GPIO access and watchdog management |
| Flask | Web dashboard framework |
| Flask-SocketIO | Real-time I/O state updates via WebSocket |
| bcrypt | Password hashing for dashboard auth |
| python-dotenv | `.env` configuration loading |
| SQLite3 | Data logging and state persistence (stdlib) |

---

## Quickstart

```bash
# 1. SSH into the Pi
ssh rasp-pi          # alias for pi@192.168.216.90

# 2. Clone the repo
git clone <repo-url> ~/openplc-pi && cd ~/openplc-pi

# 3. Install OpenPLC Runtime & OS dependencies
sudo bash scripts/install_openplc.sh
sudo bash scripts/install_deps.sh

# 4. (Optional) Install ScadaBR
sudo bash scripts/install_scadabr.sh

# 5. Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 6. Configure environment
cp .env.example .env
nano .env              # Set credentials, toggle features, configure Modbus

# 7. Initialize database
python3 -c "from src.database import init_db; init_db()"

# 8. Upload a PLC program
# Use OpenPLC Editor on your PC to create .st files, then copy to programs/

# 9. Start the service
sudo .venv/bin/python -m src.app

# Dashboard: http://192.168.216.90:5000
# OpenPLC Runtime: http://192.168.216.90:8080
# ScadaBR: http://192.168.216.90:9090
```

---

## Environment Configuration

All features are `.env` toggleable. See `.env.example` for the full variable reference, or TSD §8 for detailed documentation.

Key toggles:

| Variable | Default | Description |
|---|---|---|
| `ENABLE_OPENPLC_RUNTIME` | `true` | OpenPLC Runtime GPIO bridge |
| `ENABLE_SCADABR` | `true` | ScadaBR SCADA integration |
| `ENABLE_MODBUS_TCP` | `true` | Modbus TCP master/slave |
| `ENABLE_MODBUS_RTU` | `false` | Modbus RTU serial communication |
| `ENABLE_IO_EXPANSION` | `false` | MCP23017 I2C GPIO expansion |
| `ENABLE_WATCHDOG` | `true` | Fail-safe watchdog timers |
| `ENABLE_OPCUA` | `false` | OPC-UA server |
| `ENABLE_DATA_LOGGING` | `true` | SQLite data logging |
| `ENABLE_PROGRAM_LIBRARY` | `true` | Pre-built PLC program library |
| `ENABLE_WEB_DASHBOARD` | `true` | Flask monitoring dashboard |
| `MOCK_MODE` | `false` | Simulated I/O for dev/testing |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4/5 — OpenPLC Controller                  │
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  OpenPLC Runtime  │    │  PLC Programs     │    │  Modbus Handler  │   │
│  │  ┌────────────┐  │    │  ┌────────────┐  │    │  ┌────────────┐  │   │
│  │  │ IEC 61131  │  │<──>│  │ Ladder (LD)│  │    │  │ TCP Master │  │   │
│  │  │ Scan Cycle │  │    │  │ ST         │  │    │  │ TCP Slave  │  │   │
│  │  │ GPIO Map   │  │    │  │ FBD        │  │    │  │ RTU Master │  │   │
│  │  └────────────┘  │    │  └────────────┘  │    │  │ RTU Slave  │  │   │
│  └────────┬─────────┘    └──────────────────┘    │  └────────────┘  │   │
│           │                                       └────────┬─────────┘   │
│  ┌────────▼──────────────────────────────────────────────────────────┐   │
│  │                        GPIO / I/O Layer                            │   │
│  │  ┌─────────┐  ┌────────────┐  ┌───────────────┐  ┌────────────┐ │   │
│  │  │ Pi GPIO │  │ MCP23017   │  │ Relay Modules │  │ Opto Input │ │   │
│  │  │ (native)│  │ (I2C exp.) │  │ (4/8 ch.)     │  │ Modules    │ │   │
│  │  └─────────┘  └────────────┘  └───────────────┘  └────────────┘ │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  OPC-UA Server    │    │  Data Logger      │    │  Watchdog Timer  │   │
│  │  python-opcua     │    │  SQLite logging   │    │  Fail-safe       │   │
│  │  Tag browsing     │    │  5s interval      │    │  output disable  │   │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘   │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │              SQLite Database (WAL mode)                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐│   │
│  │  │io_states │ │data_logs │ │programs  │ │alarms  │ │settings  ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘ └──────────┘│   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  Flask + SocketIO Dashboard (dark theme)                          │   │
│  │  - bcrypt auth (rate limit 10/15min, 24h session)                 │   │
│  │  - Real-time I/O monitoring, program management                   │   │
│  │  - Alarm viewer, data log charts, Modbus config                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────┐                                                   │
│  │  ScadaBR (SCADA)  │                                                   │
│  │  :9090 web UI     │                                                   │
│  │  Modbus polling   │                                                   │
│  │  HMI screens      │                                                   │
│  └──────────────────┘                                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### OpenPLC Runtime on Pi GPIO

The OpenPLC Runtime runs directly on the Pi, mapping its physical GPIO pins to IEC 61131-3 I/O addresses. The runtime executes PLC programs in a deterministic scan cycle — read inputs → execute logic → write outputs → repeat. Toggle via `ENABLE_OPENPLC_RUNTIME`.

### IEC 61131-3 Programming Languages

Write PLC programs using industry-standard languages:

- **Ladder Logic (LD)** — graphical relay logic, familiar to electricians
- **Structured Text (ST)** — Pascal-like textual language for complex logic
- **Function Block Diagram (FBD)** — graphical dataflow programming

Use OpenPLC Editor (desktop app) to write, compile, and upload programs to the Pi.

### ScadaBR SCADA Visualization

ScadaBR provides a full SCADA/HMI system for monitoring and controlling the PLC. Polls I/O via Modbus, renders custom HMI screens, logs historical data, and generates alarm notifications. Toggle via `ENABLE_SCADABR`.

### Modbus TCP/RTU Communication

Full Modbus master/slave implementation using `pymodbus`:

- **TCP Master** — poll remote Modbus slave devices on the network
- **TCP Slave** — expose Pi I/O as Modbus registers to remote masters
- **RTU Master** — communicate with serial RS-485/RS-232 devices
- **RTU Slave** — expose I/O over serial to SCADA systems

Toggle independently via `ENABLE_MODBUS_TCP` and `ENABLE_MODBUS_RTU`.

### I/O Expansion (MCP23017)

Expand the Pi's GPIO beyond native pins using MCP23017 chips over I2C. Each chip adds 16 GPIO pins (8 on Port A + 8 on Port B). Stack up to 8 chips for 128 additional I/O points. Toggle via `ENABLE_IO_EXPANSION`.

### Fail-Safe Watchdog Timers

Hardware and software watchdog protection ensures outputs go to a safe state if the PLC program hangs or crashes. Configurable timeout (default 5 seconds). All outputs drive to predefined safe states (typically OFF). Toggle via `ENABLE_WATCHDOG`.

### Program Library

Pre-built PLC programs for common industrial scenarios:

| Program | File | Description |
|---|---|---|
| Traffic Light | `programs/traffic_light.st` | Red/Yellow/Green sequencer with pedestrian crossing |
| Motor Start/Stop | `programs/motor_start_stop.st` | 3-phase motor with interlock, overload, and emergency stop |
| Tank Level | `programs/tank_level.st` | PID level control with high/low alarms and pump management |
| Conveyor Belt | `programs/conveyor_belt.st` | Multi-zone conveyor with sensor-based jam detection |

Toggle via `ENABLE_PROGRAM_LIBRARY`.

### OPC-UA Server

Expose PLC I/O states and data as OPC-UA tags using `python-opcua`. Enables integration with industrial software (FactoryTalk, Ignition, WinCC). Browse tags, read real-time values, write setpoints. Toggle via `ENABLE_OPCUA`.

### Data Logging

Log all I/O states and process values to SQLite at configurable intervals (default 5 seconds). Query historical data for trending, export as CSV. Automatic log rotation based on configurable retention days. Toggle via `ENABLE_DATA_LOGGING`.

### Web Dashboard

Dark-themed Flask + SocketIO dashboard for real-time monitoring:

- Live I/O state display with color-coded indicators
- PLC program upload and management
- Modbus device configuration
- Alarm history and active alarm viewer
- Data log charts with time-range selection
- System settings panel

---

## Authentication

- **bcrypt** password hashing with configurable work factor
- **Rate limiting:** 10 failed attempts per 15-minute window
- **Session expiry:** 24 hours (configurable via `SESSION_EXPIRY_HOURS`)
- Login required for all dashboard pages and API endpoints
- CSRF protection on all forms

---

## Deployment

```bash
# Deploy from development machine to Pi
bash deploy/deploy_to_pi.sh

# The script:
# 1. rsync project files to rasp-pi:~/openplc-pi/
# 2. SSH in and install dependencies
# 3. Restart the systemd service
```

### systemd Service

```ini
[Unit]
Description=OpenPLC Pi Controller Dashboard
After=network.target openplc.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/openplc-pi
Environment=PATH=/home/pi/openplc-pi/.venv/bin
ExecStart=/home/pi/openplc-pi/.venv/bin/python -m src.app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo cp docs/openplc-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now openplc-dashboard
```

---

## Running the Service

```bash
# Development (with auto-reload)
source .venv/bin/activate
python -m src.app

# Production
sudo systemctl start openplc-dashboard

# Check status
sudo systemctl status openplc-dashboard

# View logs
journalctl -u openplc-dashboard -f
```

---

## Security Notes

- Dashboard binds to `0.0.0.0` by default for LAN access — restrict via `DASHBOARD_HOST` if needed
- All passwords stored as bcrypt hashes, never plaintext
- Use a firewall to restrict access to dashboard port (5000), OpenPLC (8080), and ScadaBR (9090)
- Change default credentials in `.env` before deployment
- Rate limiting mitigates brute-force login attempts
- CSRF tokens protect all state-changing operations
- SQLite uses parameterized queries (no SQL injection)
- Watchdog ensures fail-safe output states on software failure

---

## Troubleshooting

| Issue | Solution |
|---|---|
| OpenPLC Runtime not starting | Check `sudo systemctl status openplc` — verify installation with `scripts/install_openplc.sh` |
| GPIO pins not responding | Ensure `RPi.GPIO` installed, running as root, pins not claimed by other services |
| MCP23017 not detected | Run `i2cdetect -y 1` — check wiring and I2C address (0x20–0x27) |
| Modbus connection refused | Verify `MODBUS_TCP_PORT` not blocked by firewall, slave device reachable |
| ScadaBR not connecting | Ensure Modbus slave is running on Pi, check ScadaBR data source config |
| Watchdog tripping unexpectedly | Increase `WATCHDOG_TIMEOUT_SEC` or check PLC scan cycle time |
| Data logs growing too large | Reduce `LOG_INTERVAL_SEC` or decrease `LOG_RETENTION_DAYS` |
| OPC-UA clients can't connect | Verify `OPCUA_PORT` open, check endpoint URL matches config |
| Dashboard login fails | Re-generate password hash: `bash scripts/generate_password_hash.sh` |

---

## Where to Next

- Connect real sensors and actuators to the relay/input modules
- Build custom HMI screens in ScadaBR for your specific process
- Write application-specific PLC programs in OpenPLC Editor
- Integrate with existing SCADA systems via Modbus or OPC-UA
- Add PiXtend HAT for professional-grade analog I/O
- Implement redundant Pi controllers for high-availability setups
