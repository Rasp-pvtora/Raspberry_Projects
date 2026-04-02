# Automated Rubber Ducky HID Attack Platform

Configure the Raspberry Pi 4's USB-C port to act as a USB HID keyboard using Linux ConfigFS USB Gadget mode. When plugged into a target computer, it executes high-speed scripted keystrokes (DuckyScript payloads). Includes a WiFi Access Point mode so payloads can be edited from a phone or laptop before plugging in. Features a dark-themed web dashboard with real-time execution logging, target OS detection, multiple trigger modes, and a categorized payload library. For **AUTHORIZED penetration testing and IT configuration automation ONLY.**

---

> ## ⚠️ LEGAL DISCLAIMER — READ BEFORE USE
>
> **This tool is intended EXCLUSIVELY for authorized penetration testing, red team engagements, and IT configuration automation where explicit written permission has been obtained from the system owner.**
>
> **Unauthorized use of this tool against systems you do not own or have written authorization to test is ILLEGAL and may violate:**
> - **Computer Fraud and Abuse Act (CFAA)** — United States
> - **Computer Misuse Act 1990** — United Kingdom
> - **§202a–202c StGB** — Germany
> - **Equivalent laws in virtually every jurisdiction worldwide**
>
> **You are solely responsible for ensuring compliance with all applicable local, state, federal, and international laws.** The authors accept NO liability for misuse, damage, or legal consequences arising from the use of this software. By using this tool, you acknowledge that:
>
> 1. You have **written authorization** from the system owner before deploying payloads
> 2. You will use this tool **only in controlled, authorized environments**
> 3. You will maintain **detailed execution logs** for audit and reporting purposes
> 4. You understand the **legal consequences** of unauthorized computer access
>
> **If you are unsure whether your use case is authorized — DO NOT proceed.**

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
  - [USB HID Keyboard Emulation](#usb-hid-keyboard-emulation)
  - [DuckyScript Interpreter](#duckyscript-interpreter)
  - [Payload Library](#payload-library)
  - [Dual-Mode USB](#dual-mode-usb)
  - [Web-Based Payload Editor](#web-based-payload-editor)
  - [Execution Logging](#execution-logging)
  - [Trigger Modes](#trigger-modes)
  - [Target OS Detection](#target-os-detection)
  - [Anti-Detection Notes](#anti-detection-notes)
  - [WiFi Access Point Mode](#wifi-access-point-mode)
- [Authentication](#authentication)
- [Deployment](#deployment)
- [Running the Service](#running-the-service)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
Automated Rubber Ducky HID Attack Platform/
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
│   ├── hid_gadget.py           # ConfigFS USB Gadget HID setup
│   ├── duckyscript.py          # DuckyScript parser & interpreter
│   ├── payload_manager.py      # Payload CRUD, categories, library
│   ├── executor.py             # Keystroke execution engine
│   ├── trigger.py              # Trigger mode manager (GPIO, timed, manual)
│   ├── os_detect.py            # Target OS detection from USB enumeration
│   ├── mass_storage.py         # Dual-mode USB mass storage gadget
│   ├── wifi_ap.py              # WiFi Access Point manager (hostapd)
│   ├── logger.py               # Execution logging with timestamps
│   ├── database.py             # SQLite DB models & helpers
│   ├── auth.py                 # bcrypt auth & session management
│   ├── config.py               # .env loader & config dataclass
│   └── utils.py                # Shared utilities
├── templates/
│   ├── base.html               # Dark theme layout
│   ├── login.html              # Login page
│   ├── dashboard.html          # Main dashboard
│   ├── editor.html             # Payload editor page
│   ├── library.html            # Payload library browser
│   ├── logs.html               # Execution log viewer
│   └── settings.html           # Runtime settings panel
├── static/
│   ├── css/
│   │   └── style.css           # Dark theme styles
│   └── js/
│       ├── dashboard.js        # SocketIO client & live status
│       ├── editor.js           # Payload editor logic (CodeMirror)
│       └── logs.js             # Log viewer real-time updates
├── payloads/
│   ├── recon/                  # Reconnaissance payloads
│   ├── exfiltration/           # Data exfiltration payloads
│   └── configuration/         # IT configuration/automation payloads
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures & mock mode helpers
│   ├── test_duckyscript.py     # DuckyScript parser tests
│   ├── test_executor.py        # Keystroke execution tests
│   ├── test_payload_manager.py # Payload CRUD tests
│   ├── test_trigger.py         # Trigger mode tests
│   ├── test_os_detect.py       # OS detection tests
│   ├── test_auth.py            # Auth & session tests
│   ├── test_api.py             # Dashboard API endpoint tests
│   └── test_logger.py          # Execution logging tests
├── deploy/
│   └── deploy_to_pi.sh         # rsync deploy script (rasp-pi)
├── scripts/
│   ├── setup_usb_gadget.sh     # ConfigFS USB HID gadget setup
│   ├── setup_wifi_ap.sh        # hostapd WiFi AP setup
│   └── install_deps.sh         # OS-level dependency installer
└── docs/
    ├── threat_model.md         # Security threat model
    ├── duckyscript_reference.md # DuckyScript syntax guide
    └── anti_detection.md       # EDR evasion & detection notes
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 | Yes | USB-C port supports OTG/device mode natively |
| USB-C cable | Yes | Data cable (not charge-only) to connect Pi to target |
| MicroSD card (16GB+) | Yes | For OS, payloads, and execution logs |
| Power supply (5V/3A) | Yes | For standalone operation and WiFi AP mode |
| GPIO push button | No | Optional physical trigger ($2) |
| Status LED | No | Optional visual feedback ($1) |

> **Important:** The Pi 4's USB-C port serves dual purpose — it acts as the HID device when plugged into a target AND provides power from the target's USB port. For standalone WiFi AP editing, use the dedicated power supply.

---

## Budget

| Item | Estimated Cost |
|---|---|
| Raspberry Pi 4 (already owned) | $0 |
| USB-C data cable (already owned) | $0 |
| GPIO push button (optional) | ~$2 |
| Status LED (optional) | ~$1 |
| **Total** | **~$0–$3** |

*(Assumes you already have a Raspberry Pi 4, SD card, and USB-C cable.)*

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| Flask | Web dashboard & payload editor framework |
| Flask-SocketIO | Real-time WebSocket for live execution status |
| python-dotenv | `.env` configuration loading |
| bcrypt | Password hashing for dashboard auth |
| Jinja2 | HTML templating (bundled with Flask) |
| configfs (kernel) | USB Gadget mode for HID keyboard emulation |
| libcomposite (kernel) | Composite USB gadget (HID + mass storage) |
| hostapd | WiFi Access Point daemon |
| dnsmasq | DHCP/DNS for WiFi AP clients |
| RPi.GPIO | GPIO button trigger and status LED control |
| gunicorn / eventlet | Production WSGI server with WebSocket support |

---

## Quickstart

```bash
# 1. SSH into the Pi
ssh rasp-pi          # alias for pi@192.168.216.90

# 2. Clone the repo
git clone <repo-url> ~/rubber-ducky && cd ~/rubber-ducky

# 3. Install OS-level dependencies
sudo bash scripts/install_deps.sh

# 4. Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
nano .env              # Set credentials, toggle features

# 6. Set up USB HID gadget
sudo bash scripts/setup_usb_gadget.sh

# 7. (Optional) Set up WiFi Access Point
sudo bash scripts/setup_wifi_ap.sh

# 8. Run the platform
sudo .venv/bin/python -m src.app
# Dashboard at http://192.168.216.90:5000 (or via WiFi AP at 10.0.0.1:5000)

# 9. Plug USB-C into target machine to execute payloads
```

---

## Environment Configuration

All features are toggleable via `.env`. Copy `.env.example` and adjust:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(generate)* | Flask session secret key |
| `ADMIN_USERNAME` | `admin` | Dashboard login username |
| `ADMIN_PASSWORD_HASH` | *(bcrypt hash)* | bcrypt-hashed admin password |
| `DB_PATH` | `data/rubber_ducky.db` | SQLite database file path |
| `ENABLE_HID_GADGET` | `true` | Toggle USB HID keyboard emulation |
| `HID_DEVICE_PATH` | `/dev/hidg0` | HID gadget device file |
| `ENABLE_MASS_STORAGE` | `false` | Toggle dual-mode USB mass storage |
| `MASS_STORAGE_IMAGE` | `data/storage.img` | Mass storage disk image path |
| `MASS_STORAGE_SIZE_MB` | `64` | Mass storage image size in MB |
| `ENABLE_DUCKYSCRIPT` | `true` | Toggle DuckyScript interpreter |
| `DEFAULT_DELAY_MS` | `50` | Default inter-keystroke delay (ms) |
| `ENABLE_PAYLOAD_LIBRARY` | `true` | Toggle payload library feature |
| `PAYLOAD_DIR` | `payloads/` | Directory for payload files |
| `ENABLE_EXECUTION_LOGGING` | `true` | Toggle keystroke execution logging |
| `LOG_KEYSTROKES` | `true` | Log individual keystrokes (detail level) |
| `TRIGGER_MODE` | `manual` | Default trigger: `immediate`, `button`, `timed`, `manual` |
| `TRIGGER_DELAY_SECONDS` | `5` | Delay for timed trigger mode |
| `GPIO_TRIGGER_PIN` | `17` | BCM pin for physical trigger button |
| `GPIO_LED_PIN` | `27` | BCM pin for status LED |
| `ENABLE_GPIO_TRIGGER` | `false` | Toggle GPIO button trigger |
| `ENABLE_STATUS_LED` | `false` | Toggle status LED |
| `ENABLE_OS_DETECTION` | `true` | Toggle target OS detection |
| `ENABLE_WIFI_AP` | `false` | Toggle WiFi Access Point mode |
| `WIFI_AP_SSID` | `DuckyConfig` | WiFi AP network name |
| `WIFI_AP_PASSWORD` | `ducky12345` | WiFi AP password (WPA2) |
| `WIFI_AP_CHANNEL` | `6` | WiFi AP channel |
| `WIFI_AP_IP` | `10.0.0.1` | WiFi AP gateway IP |
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
┌──────────────────────────────────────────────────────────────────────┐
│                        Raspberry Pi 4                                │
│                                                                      │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐  │
│  │  ConfigFS     │───>│  DuckyScript     │───>│  Execution        │  │
│  │  USB Gadget   │    │  Interpreter     │    │  Engine           │  │
│  │  (HID + Mass  │    │  (parser)        │    │  (keystroke       │  │
│  │   Storage)    │    │                  │    │   injection)      │  │
│  └───────┬──────┘    └──────────────────┘    └────────┬──────────┘  │
│          │                                            │              │
│  ┌───────▼──────┐    ┌──────────────────┐    ┌────────▼──────────┐  │
│  │  OS Detection │    │  Trigger Manager │    │  Execution        │  │
│  │  (USB enum)   │    │  ┌────────────┐  │    │  Logger           │  │
│  └──────────────┘    │  │ Immediate  │  │    │  (timestamped     │  │
│                      │  │ Button     │  │    │   keystrokes)     │  │
│  ┌──────────────┐    │  │ Timed      │  │    └────────┬──────────┘  │
│  │  Payload      │    │  │ Manual/Web │  │             │              │
│  │  Library      │    │  └────────────┘  │             │              │
│  │  ┌──────────┐ │    └──────────────────┘             │              │
│  │  │ Recon    │ │                                     │              │
│  │  │ Exfil    │ │    ┌──────────────────┐             │              │
│  │  │ Config   │ │    │  SQLite Database  │<────────────┘              │
│  │  └──────────┘ │    │  (payloads, logs, │                           │
│  └──────────────┘    │   settings)       │                           │
│                      └─────────┬────────┘                           │
│  ┌──────────────┐              │                                     │
│  │  WiFi AP      │    ┌────────▼─────────────────────────────────┐  │
│  │  (hostapd)    │───>│  Flask + SocketIO Web Dashboard          │  │
│  │  10.0.0.1     │    │  - bcrypt auth (rate limit 10/15min)     │  │
│  └──────────────┘    │  - 24h session expiry                     │  │
│                      │  - Dark theme, payload editor              │  │
│  ┌──────────────┐    │  - Live execution status & log viewer     │  │
│  │  GPIO         │    └──────────────────────────────────────────┘  │
│  │  - Button     │                                                   │
│  │  - LED        │                                                   │
│  └──────────────┘                                                   │
│          │                                                           │
│          ▼                                                           │
│    USB-C ──────────> Target Computer (HID keyboard input)            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Features

### USB HID Keyboard Emulation

The Pi 4's USB-C port is configured as a USB HID keyboard using Linux ConfigFS USB Gadget mode (`libcomposite` kernel module). When plugged into a target computer, the target sees a standard USB keyboard — no drivers required.

- ConfigFS gadget created at `/sys/kernel/config/usb_gadget/rubber_ducky/`
- Standard HID keyboard descriptor (boot protocol compatible)
- Writes raw HID reports to `/dev/hidg0`
- Configurable VID/PID to mimic common keyboard vendors
- Hot-pluggable — gadget persists across reconnections

### DuckyScript Interpreter

Full-featured interpreter compatible with Hak5 DuckyScript syntax. Parses `.txt` payload files and translates commands into HID keyboard reports.

- Supported commands: `REM`, `DELAY`, `STRING`, `ENTER`, `GUI`, `ALT`, `CTRL`, `SHIFT`, `TAB`, `ESCAPE`, `CAPSLOCK`, `DELETE`, `INSERT`, `PAGEUP`, `PAGEDOWN`, `HOME`, `END`, `UPARROW`, `DOWNARROW`, `LEFTARROW`, `RIGHTARROW`, `F1`–`F12`, `PRINTSCREEN`, `SCROLLLOCK`, `PAUSE`, `MENU`, `REPEAT`, `DEFAULT_DELAY`
- Variable substitution: `$TARGET_OS`, `$TIMESTAMP`, `$HOSTNAME`
- Conditional execution: `IFOS WINDOWS ... ENDIF`
- Configurable default delay between keystrokes (`DEFAULT_DELAY_MS`)

### Payload Library

Categorized collection of pre-built and custom payloads stored in the filesystem and indexed in SQLite.

| Category | Description | Examples |
|---|---|---|
| **Recon** | System reconnaissance & info gathering | WiFi passwords, system info, installed software |
| **Exfiltration** | Data extraction (authorized testing) | Copy files to mass storage, upload to webhook |
| **Configuration** | IT automation & setup | Install software, configure settings, deploy configs |

- Browse, search, and filter payloads via web dashboard
- Create, edit, duplicate, and delete payloads from the editor
- Import/export payloads as `.txt` files
- Payload metadata: name, description, category, target OS, author, risk level

### Dual-Mode USB

Simultaneously present as both a HID keyboard and USB mass storage device in the same USB session using a composite ConfigFS gadget.

- Mass storage backed by a disk image file (`data/storage.img`)
- Target sees both a keyboard and a removable drive
- Useful for exfiltration payloads that write to the "USB drive"
- Configurable image size (`MASS_STORAGE_SIZE_MB`)
- Toggle independently via `ENABLE_MASS_STORAGE`

### Web-Based Payload Editor

Connect to the Pi's WiFi AP (or via LAN) and edit payloads in a browser-based code editor before plugging into the target.

- Syntax-highlighted DuckyScript editor (CodeMirror integration)
- Real-time syntax validation as you type
- Save, load, and manage payloads from the browser
- Select active payload and trigger mode before deployment
- Preview translated keystrokes before execution
- Mobile-friendly responsive layout for phone editing in the field

### Execution Logging

Every keystroke sent to the target is logged with precise timestamps for penetration testing reports and audit trails.

- Logs stored in `execution_logs` table with microsecond timestamps
- Records: payload name, each keystroke/command, timing, success/failure
- Exportable as CSV or JSON for inclusion in pentest reports
- Real-time log streaming via SocketIO to the dashboard
- Toggle via `ENABLE_EXECUTION_LOGGING`
- Individual keystroke logging via `LOG_KEYSTROKES`

### Trigger Modes

Multiple ways to start payload execution, configurable per-session:

| Mode | Description | Config |
|---|---|---|
| **Immediate** | Execute on USB plug-in (no delay) | `TRIGGER_MODE=immediate` |
| **Button** | Physical GPIO button press to start | `TRIGGER_MODE=button`, `GPIO_TRIGGER_PIN` |
| **Timed** | Execute after configurable delay | `TRIGGER_MODE=timed`, `TRIGGER_DELAY_SECONDS` |
| **Manual** | Trigger from web dashboard UI | `TRIGGER_MODE=manual` |

- Trigger mode selectable at runtime from the dashboard
- Button mode supports single-press (execute once) and hold (abort)
- LED feedback: blinking = waiting, solid = executing, off = idle

### Target OS Detection

Detects the target operating system from USB enumeration metadata to enable OS-specific payload branching.

- Analyzes USB host descriptor requests during enumeration
- Detects: Windows, macOS, Linux, ChromeOS
- Populates `$TARGET_OS` variable for DuckyScript conditionals
- Logged per execution for reporting
- Fallback to `unknown` if detection inconclusive
- Toggle via `ENABLE_OS_DETECTION`

### Anti-Detection Notes

Documentation on how Endpoint Detection and Response (EDR) systems detect HID attacks and strategies for authorized red team engagements.

- Documented in `docs/anti_detection.md`
- Covers: keystroke speed profiling, USB device fingerprinting, behavioral analysis, kernel-level HID monitoring
- Legitimate use: helps defenders understand what to watch for
- Strategies: realistic typing speed, human-like delays, known VID/PID spoofing
- **For defensive awareness only** — understand how security tools detect these attacks

### WiFi Access Point Mode

The Pi creates its own WiFi network using `hostapd` and `dnsmasq`, allowing wireless payload management from any device.

- WPA2-secured access point with configurable SSID and password
- Captive portal redirects to the dashboard at `10.0.0.1:5000`
- Edit payloads from your phone while the Pi is disconnected from any network
- DHCP server assigns IPs to connected clients (`10.0.0.10–10.0.0.50`)
- Toggle via `ENABLE_WIFI_AP`

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
REMOTE_DIR="/home/pi/rubber-ducky"

echo "[*] Deploying to ${PI_HOST}:${REMOTE_DIR}"
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
    --exclude '.git' --exclude 'data/' \
    ./ "${PI_HOST}:${REMOTE_DIR}/"

ssh "${PI_HOST}" "cd ${REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt"
echo "[✓] Deploy complete. Restart the service:"
echo "    ssh ${PI_HOST} 'sudo systemctl restart rubber-ducky'"
```

---

## Running the Service

### Manual

```bash
ssh rasp-pi
cd ~/rubber-ducky
source .venv/bin/activate
sudo .venv/bin/python -m src.app
```

### systemd Service

Create `/etc/systemd/system/rubber-ducky.service`:

```ini
[Unit]
Description=Automated Rubber Ducky HID Attack Platform
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/rubber-ducky
EnvironmentFile=/home/pi/rubber-ducky/.env
ExecStartPre=/bin/bash scripts/setup_usb_gadget.sh
ExecStart=/home/pi/rubber-ducky/.venv/bin/python -m src.app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable rubber-ducky
sudo systemctl start rubber-ducky
sudo journalctl -u rubber-ducky -f    # Follow logs
```

---

## Security Notes

- **Authorized use only** — this tool must ONLY be used with explicit written permission from the target system owner. Unauthorized use is a criminal offense.
- **Run as root** — USB gadget mode and GPIO access require root privileges. The web dashboard inherits root context.
- **Do not expose the dashboard to the internet** — bind to LAN or WiFi AP only.
- **Rotate `SECRET_KEY`** regularly and never commit `.env` to version control.
- **Password hashing** — only bcrypt hashes are stored; plaintext passwords are never persisted.
- **Rate limiting** — protects against brute-force login attempts.
- **Execution logs contain sensitive data** — keystroke logs may contain passwords or tokens typed during testing. Secure log storage and limit retention.
- **WiFi AP security** — change default AP password before field use. WPA2 only.
- **Payload review** — always review payloads before execution. Never run untrusted payloads.
- **Physical security** — the Pi stores payloads and logs; encrypt the SD card for transport.
- **USB VID/PID spoofing** — mimicking another vendor's USB identifiers may violate terms; use only in authorized engagements.

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `/dev/hidg0` not found | USB gadget not configured | Run `sudo bash scripts/setup_usb_gadget.sh` |
| `Permission denied` on `/dev/hidg0` | Not running as root | Run with `sudo` |
| Target doesn't recognize keyboard | Cable is charge-only or Pi not in gadget mode | Use a USB-C data cable; verify `ls /sys/kernel/config/usb_gadget/` |
| Keystrokes not typing on target | Wrong keyboard layout or HID report format | Check target OS keyboard layout; verify HID descriptor |
| WiFi AP not broadcasting | hostapd not running or misconfigured | Check `sudo systemctl status hostapd`; verify `WIFI_AP_SSID` and channel |
| Dashboard not loading | Web dashboard disabled or wrong port | Check `ENABLE_WEB_DASHBOARD=true` and `DASHBOARD_PORT` in `.env` |
| GPIO button not triggering | Wrong pin or pull-up resistor missing | Verify `GPIO_TRIGGER_PIN`; use internal pull-up (`GPIO.PUD_UP`) |
| OS detection shows `unknown` | USB enumeration too fast or unsupported host | Increase enumeration timeout; check USB descriptor logs |
| Slow keystroke execution | `DEFAULT_DELAY_MS` too high | Lower the value; test with target's input buffer capacity |
| `ModuleNotFoundError` | Missing Python dependency | Activate venv and run `pip install -r requirements.txt` |
| `libcomposite` not loaded | Kernel module not enabled | Run `sudo modprobe libcomposite` and add to `/etc/modules` |
| Mass storage not mounting on target | Disk image corrupt or not formatted | Recreate image: `dd if=/dev/zero of=data/storage.img bs=1M count=64 && mkfs.vfat data/storage.img` |

---

## Where to Next

- **Multi-payload chaining** — execute a sequence of payloads in order with conditional branching
- **Encrypted payload storage** — AES-encrypt payloads at rest, decrypt only at execution time
- **Remote trigger via Telegram** — send a message to trigger payload execution remotely
- **Exfiltration over WiFi** — pipe target data back through the Pi's WiFi AP to an attacker machine
- **Rubber Ducky firmware flashing** — flash actual Hak5 Rubber Ducky firmware for comparison testing
- **HID + Ethernet gadget** — add RNDIS/ECM network gadget for network-based exfiltration
- **Payload compilation** — pre-compile DuckyScript to binary HID reports for faster execution
- **Multi-language keyboard layouts** — support international keyboard layouts (AZERTY, QWERTZ, etc.)
- **Replay mode** — record keystrokes from a real keyboard session and replay them
- **Integration with Metasploit** — generate payloads from msfvenom and wrap in DuckyScript
