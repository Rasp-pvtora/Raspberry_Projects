# Rogue Access Point Detector

A WiFi security scanner for Raspberry Pi that uses a secondary USB WiFi adapter in monitor mode to continuously scan for Evil Twin attacks, unauthorized access points, and deauthentication floods. Features baseline AP learning, MAC vendor lookup (OUI), deauth flood detection, GPS tagging for mobile war-driving, multi-channel alert system, SIEM integration, and a real-time dark-themed web dashboard showing the wireless landscape with threat alerts. Portable mode supports battery-powered Pi Zero 2W for walk-around audits.

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
  - [Continuous Background Scanning](#continuous-background-scanning)
  - [Baseline AP Learning](#baseline-ap-learning)
  - [Evil Twin Detection](#evil-twin-detection)
  - [Deauthentication Flood Detection](#deauthentication-flood-detection)
  - [MAC Vendor Lookup (OUI)](#mac-vendor-lookup-oui)
  - [GPS Tagging](#gps-tagging)
  - [Alert Channels](#alert-channels)
  - [SIEM Integration](#siem-integration)
  - [Portable Mode](#portable-mode)
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
Rogue Access Point Detector/
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
│   ├── scanner.py              # Core scanning engine (scapy)
│   ├── detector.py             # Evil twin & deauth detection logic
│   ├── baseline.py             # Baseline AP learning & comparison
│   ├── oui_lookup.py           # MAC vendor resolution (manuf)
│   ├── gps_handler.py          # GPS integration (gpsd-py3)
│   ├── alerts.py               # Alert dispatcher (email, Telegram, webhook, GPIO)
│   ├── siem.py                 # Syslog forwarding for SIEM
│   ├── database.py             # SQLite DB models & helpers
│   ├── auth.py                 # bcrypt auth & session management
│   ├── config.py               # .env loader & config dataclass
│   └── utils.py                # Shared utilities
├── templates/
│   ├── base.html               # Dark theme layout
│   ├── login.html              # Login page
│   ├── dashboard.html          # Main dashboard
│   └── settings.html           # Runtime settings panel
├── static/
│   ├── css/
│   │   └── style.css           # Dark theme styles
│   └── js/
│       ├── dashboard.js        # SocketIO client & Chart.js graphs
│       └── charts.js           # Chart configuration helpers
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures & mock mode helpers
│   ├── test_scanner.py         # Scanner unit tests
│   ├── test_detector.py        # Detection logic tests
│   ├── test_baseline.py        # Baseline learning tests
│   ├── test_alerts.py          # Alert channel tests
│   ├── test_auth.py            # Auth & session tests
│   └── test_api.py             # Dashboard API endpoint tests
├── deploy/
│   └── deploy_to_pi.sh         # rsync deploy script (rasp-pi)
├── scripts/
│   ├── setup_monitor_mode.sh   # Enable monitor mode on USB adapter
│   └── install_deps.sh         # OS-level dependency installer
└── docs/
    └── threat_model.md         # Security threat model
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 or 5 | Yes | Pi Zero 2W for portable mode |
| Monitor-mode USB WiFi adapter | Yes | Alfa AWUS036ACH recommended (802.11ac, dual-band) |
| USB GPS dongle | No | For war-driving / GPS tagging (e.g., VK-162 G-Mouse) |
| MicroSD card (32GB+) | Yes | For OS and database storage |
| Power supply / battery pack | Yes | 5V/3A for Pi 4/5; battery pack for portable mode |

> **Important:** The built-in Pi WiFi stays on the home network. The USB adapter is dedicated to monitor-mode scanning.

---

## Budget

| Item | Estimated Cost |
|---|---|
| Monitor-mode USB WiFi adapter (Alfa AWUS036ACH) | $30–40 |
| USB GPS dongle (optional) | ~$15 |
| **Total** | **~$30–55** |

*(Assumes you already have a Raspberry Pi, SD card, and power supply.)*

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| Flask | Web dashboard framework |
| Flask-SocketIO | Real-time WebSocket push to dashboard |
| scapy | Packet capture & 802.11 frame parsing |
| manuf | MAC address OUI vendor lookup |
| gpsd-py3 | GPS daemon client for location tagging |
| bcrypt | Password hashing for dashboard auth |
| python-dotenv | `.env` configuration loading |
| requests | Outbound HTTP for Telegram/webhook alerts |
| Jinja2 | HTML templating (bundled with Flask) |
| Chart.js | Client-side charting (CDN or vendored) |
| gunicorn / eventlet | Production WSGI server with WebSocket support |

---

## Quickstart

```bash
# 1. SSH into the Pi
ssh rasp-pi          # alias for pi@192.168.216.90

# 2. Clone the repo
git clone <repo-url> ~/rogue-ap-detector && cd ~/rogue-ap-detector

# 3. Install OS-level dependencies
sudo apt update && sudo apt install -y aircrack-ng gpsd gpsd-clients python3-venv python3-dev

# 4. Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 5. Enable monitor mode on USB adapter
sudo bash scripts/setup_monitor_mode.sh wlan1

# 6. Configure environment
cp .env.example .env
nano .env              # Set credentials, toggle features

# 7. Initialize baseline (first run learns known APs)
sudo .venv/bin/python -m src.app --learn-baseline

# 8. Run the scanner + dashboard
sudo .venv/bin/python -m src.app
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
| `DB_PATH` | `data/rogue_ap.db` | SQLite database file path |
| `MONITOR_INTERFACE` | `wlan1mon` | Monitor-mode interface name |
| `SCAN_INTERVAL` | `10` | Seconds between scan cycles |
| `CHANNEL_HOP_INTERVAL` | `0.5` | Seconds per channel during hopping |
| `SCAN_BANDS` | `both` | Bands to scan: `2.4`, `5`, or `both` |
| `ENABLE_EVIL_TWIN_DETECTION` | `true` | Toggle evil twin detection |
| `ENABLE_DEAUTH_DETECTION` | `true` | Toggle deauth flood detection |
| `DEAUTH_THRESHOLD` | `10` | Deauth frames/sec to trigger alert |
| `ENABLE_BASELINE_LEARNING` | `true` | Toggle baseline AP learning |
| `BASELINE_AUTO_LEARN` | `false` | Auto-learn new APs (dangerous in prod) |
| `ENABLE_OUI_LOOKUP` | `true` | Toggle MAC vendor resolution |
| `ENABLE_GPS` | `false` | Toggle GPS tagging |
| `GPS_HOST` | `127.0.0.1` | gpsd host |
| `GPS_PORT` | `2947` | gpsd port |
| `ENABLE_ALERTS` | `true` | Master toggle for all alerts |
| `ENABLE_EMAIL_ALERTS` | `false` | Toggle email alerts |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | `` | SMTP username |
| `SMTP_PASS` | `` | SMTP password |
| `ALERT_EMAIL_TO` | `` | Recipient email |
| `ENABLE_TELEGRAM_ALERTS` | `false` | Toggle Telegram alerts |
| `TELEGRAM_BOT_TOKEN` | `` | Telegram bot API token |
| `TELEGRAM_CHAT_ID` | `` | Telegram chat ID |
| `ENABLE_WEBHOOK_ALERTS` | `false` | Toggle generic webhook alerts |
| `WEBHOOK_URL` | `` | Webhook endpoint URL |
| `ENABLE_GPIO_BUZZER` | `false` | Toggle GPIO buzzer on threat |
| `GPIO_BUZZER_PIN` | `18` | BCM pin number for buzzer |
| `ENABLE_SIEM` | `false` | Toggle Syslog forwarding |
| `SIEM_HOST` | `127.0.0.1` | Syslog server host |
| `SIEM_PORT` | `514` | Syslog server port |
| `SIEM_PROTOCOL` | `udp` | Syslog protocol (`udp` or `tcp`) |
| `ENABLE_PORTABLE_MODE` | `false` | Battery-aware portable mode |
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
┌─────────────────────────────────────────────────────────────────┐
│                     Raspberry Pi 4/5                            │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  USB WiFi    │───>│  Scanner     │───>│  Detector        │  │
│  │  (monitor)   │    │  Engine      │    │  (evil twin,     │  │
│  │  wlan1mon    │    │  (scapy)     │    │   deauth, rogue) │  │
│  └──────────────┘    └──────┬───────┘    └────────┬─────────┘  │
│                             │                     │             │
│  ┌──────────────┐    ┌──────▼───────┐    ┌────────▼─────────┐  │
│  │  USB GPS     │───>│  Baseline    │    │  Alert           │  │
│  │  (optional)  │    │  Manager     │    │  Dispatcher      │  │
│  └──────────────┘    └──────┬───────┘    │  ┌─────────────┐ │  │
│                             │            │  │ Email        │ │  │
│  ┌──────────────┐    ┌──────▼───────┐    │  │ Telegram    │ │  │
│  │  SQLite DB   │<───│  OUI Lookup  │    │  │ Webhook     │ │  │
│  │  (data/)     │    │  (manuf)     │    │  │ GPIO Buzzer │ │  │
│  └──────┬───────┘    └──────────────┘    │  └─────────────┘ │  │
│         │                                └──────────────────┘  │
│  ┌──────▼────────────────────────────┐                         │
│  │  Flask + SocketIO Dashboard       │──> Browser (dark theme) │
│  │  (bcrypt auth, rate limiting)     │                         │
│  └──────┬────────────────────────────┘                         │
│         │                                                      │
│  ┌──────▼───────┐                                              │
│  │  SIEM/Syslog │──> Wazuh / Splunk                            │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

### Continuous Background Scanning

The scanner engine uses scapy to capture 802.11 beacon, probe-response, and management frames on the monitor-mode interface. It performs channel hopping across 2.4 GHz (channels 1–14) and 5 GHz (channels 36–165) bands based on `SCAN_BANDS`. Each scan cycle collects all visible APs with SSID, BSSID, channel, signal strength, encryption type, and timestamp.

- Configurable scan interval (`SCAN_INTERVAL`) and channel dwell time (`CHANNEL_HOP_INTERVAL`)
- Runs as a background thread alongside the web dashboard
- All discovered APs are persisted to SQLite and pushed via SocketIO

### Baseline AP Learning

On first run (or via `--learn-baseline` flag), the scanner records all currently visible APs as the "known good" baseline. Subsequent scans compare against this baseline and raise alerts for any new or modified APs.

- Stores baseline in `baseline_aps` table with SSID, BSSID, channel, encryption
- Alerts on new BSSID, changed encryption, or channel migration
- Manual approve/reject of new APs via dashboard settings panel
- `BASELINE_AUTO_LEARN=true` silently adds new APs (use only in trusted environments)

### Evil Twin Detection

Detects rogue APs impersonating legitimate networks by looking for SSIDs that match baseline entries but have different BSSIDs or weaker/different encryption.

- Compares discovered SSID+BSSID+encryption against baseline entries
- Flags mismatches as `EVIL_TWIN` threat type with severity `HIGH`
- Reports the legitimate AP alongside the suspect for side-by-side comparison
- Real-time alert via all enabled channels

### Deauthentication Flood Detection

Monitors for 802.11 deauthentication and disassociation frames that indicate an active attack. When the rate exceeds `DEAUTH_THRESHOLD` frames per second, the system raises a `DEAUTH_FLOOD` alert.

- Counts deauth/disassoc frames per source MAC per second
- Identifies the attacker MAC and target BSSID
- Severity: `CRITICAL` — deauth floods often precede evil twin attacks
- OUI lookup on attacker MAC to identify hardware vendor

### MAC Vendor Lookup (OUI)

Every discovered BSSID is resolved to its hardware manufacturer using the IEEE OUI database via the `manuf` library. This helps identify suspicious devices (e.g., consumer routers where enterprise gear is expected).

- Offline OUI database — no internet required
- Vendor field stored in `access_points` table and displayed on dashboard
- Periodic OUI database updates via `manuf.manuf.MacParser().refresh()`

### GPS Tagging

When a USB GPS dongle is connected and `ENABLE_GPS=true`, each scan event and threat is tagged with latitude, longitude, and altitude. Enables mobile war-driving and mapping rogue AP locations.

- Connects to `gpsd` daemon via `gpsd-py3`
- GPS coordinates stored in `scan_events` and `threats` tables
- Dashboard map view plots APs by location (when GPS data available)
- Graceful fallback when GPS has no fix or is disconnected

### Alert Channels

When a threat is detected, the alert dispatcher sends notifications through all enabled channels:

| Channel | Config | Description |
|---|---|---|
| **Email** | `ENABLE_EMAIL_ALERTS` | SMTP email with threat details |
| **Telegram** | `ENABLE_TELEGRAM_ALERTS` | Bot message with formatted threat summary |
| **Webhook** | `ENABLE_WEBHOOK_ALERTS` | JSON POST to arbitrary endpoint |
| **GPIO Buzzer** | `ENABLE_GPIO_BUZZER` | Physical buzzer pulse on threat detection |

- Each channel toggleable independently
- Alert includes: threat type, severity, SSID, BSSID, vendor, timestamp, GPS (if available)
- Rate limiting on alerts to prevent spam during sustained attacks

### SIEM Integration

Forwards threat events as structured Syslog messages (RFC 5424) to a remote SIEM collector (Wazuh, Splunk, etc.) when `ENABLE_SIEM=true`.

- Supports UDP and TCP transport
- CEF-formatted messages for easy parsing
- Includes all threat metadata (type, severity, SSID, BSSID, vendor, GPS)
- Configurable facility and severity mapping

### Portable Mode

When `ENABLE_PORTABLE_MODE=true`, the scanner optimizes for battery-powered operation on a Pi Zero 2W:

- Reduces scan frequency to conserve power
- Disables web dashboard (logs to file and database only)
- Shorter channel dwell times for faster sweeps
- GPS tagging for walk-around war-driving
- Status LED blink patterns for headless operation

### Web Dashboard

A dark-themed Flask + SocketIO dashboard provides real-time visibility into the wireless landscape:

- **Live AP table** — all discovered APs with SSID, BSSID, channel, signal, vendor, status
- **Threat feed** — chronological list of detected threats with severity badges
- **Signal chart** — Chart.js line graph of AP signal strength over time
- **Channel utilization** — bar chart of AP distribution across channels
- **Baseline management** — approve/reject/reset baseline APs
- **Settings panel** — runtime toggle of features without restart
- Real-time updates via SocketIO (no page refresh needed)

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
REMOTE_DIR="/home/pi/rogue-ap-detector"

echo "[*] Deploying to ${PI_HOST}:${REMOTE_DIR}"
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
    --exclude '.git' --exclude 'data/' \
    ./ "${PI_HOST}:${REMOTE_DIR}/"

ssh "${PI_HOST}" "cd ${REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt"
echo "[✓] Deploy complete. Restart the service:"
echo "    ssh ${PI_HOST} 'sudo systemctl restart rogue-ap-detector'"
```

---

## Running the Service

### Manual

```bash
ssh rasp-pi
cd ~/rogue-ap-detector
source .venv/bin/activate
sudo .venv/bin/python -m src.app
```

### systemd Service

Create `/etc/systemd/system/rogue-ap-detector.service`:

```ini
[Unit]
Description=Rogue Access Point Detector
After=network-online.target gpsd.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/rogue-ap-detector
EnvironmentFile=/home/pi/rogue-ap-detector/.env
ExecStartPre=/bin/bash scripts/setup_monitor_mode.sh wlan1
ExecStart=/home/pi/rogue-ap-detector/.venv/bin/python -m src.app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable rogue-ap-detector
sudo systemctl start rogue-ap-detector
sudo journalctl -u rogue-ap-detector -f    # Follow logs
```

---

## Security Notes

- **Run scanner as root** — monitor mode and raw packet capture require root privileges. The web dashboard binds to a non-privileged port but inherits root context.
- **Do not expose the dashboard to the internet** — bind to LAN only or use a reverse proxy with TLS.
- **Rotate `SECRET_KEY`** regularly and never commit `.env` to version control.
- **Password hashing** — only bcrypt hashes are stored; plaintext passwords are never persisted.
- **Rate limiting** — protects against brute-force login attempts.
- **Monitor mode legality** — passive monitoring is legal in most jurisdictions; active scanning/injection is not. This tool is passive only.
- **OUI database** — ships offline; no data leaves the Pi during normal operation.
- **GPS data** — location data is stored locally; ensure physical security of the Pi.

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `No monitor interface found` | USB adapter not in monitor mode | Run `sudo bash scripts/setup_monitor_mode.sh wlan1` |
| `Permission denied` on scan | Not running as root | Run with `sudo` or as the `root` user |
| `wlan1` not detected | Adapter not plugged in or driver missing | Check `lsusb`, install `rtl8812au` driver for Alfa adapters |
| No APs found | Wrong interface or antenna issue | Verify `iwconfig wlan1mon` shows monitor mode; check antenna connection |
| Dashboard not loading | Web dashboard disabled or wrong port | Check `ENABLE_WEB_DASHBOARD=true` and `DASHBOARD_PORT` in `.env` |
| GPS shows no fix | GPS dongle needs sky view | Move outdoors or near a window; check `cgps` for satellite lock |
| Telegram alerts not sending | Invalid bot token or chat ID | Test with `curl` to Telegram API; verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` |
| High CPU usage | Scan interval too short | Increase `SCAN_INTERVAL` and `CHANNEL_HOP_INTERVAL` |
| Database locked errors | Concurrent write contention | Ensure single scanner instance; use WAL mode for SQLite |
| `ModuleNotFoundError` | Missing Python dependency | Activate venv and run `pip install -r requirements.txt` |

---

## Where to Next

- **Map visualization** — integrate Leaflet.js to plot rogue APs on a real map using GPS data
- **Client probing analysis** — track probe request frames to identify devices searching for known networks
- **802.11w detection** — detect APs that do/don't support Protected Management Frames
- **Automated deauth source triangulation** — use multiple Pi nodes to triangulate attacker position
- **Historical trending** — long-term AP population graphs to detect slow-burn rogue deployments
- **Mobile app** — React Native companion app for receiving alerts on the go
- **Integration with Kismet** — pipe Kismet GPSD/JSON output into the detector for extended metadata
- **Multi-sensor mesh** — network multiple Pis for campus-wide coverage with centralized dashboard
