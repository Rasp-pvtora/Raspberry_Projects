# 📡 WiFi Extender & Access Point Manager

A Raspberry Pi–powered WiFi access point and network extender that bridges Ethernet to wireless, with automatic hostapd + dnsmasq configuration, connected-client monitoring, bandwidth tracking, MAC filtering, captive portal, QoS traffic shaping, and scheduled WiFi — all managed from a responsive dark-theme web dashboard with per-feature toggle switches.

---

## 📋 Table of Contents
- [Features](#-features)
- [Dashboard Feature Toggles](#-dashboard-feature-toggles)
- [Hardware Requirements](#-hardware-requirements)
- [Network Architecture](#-network-architecture)
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
| 1 | **hostapd + dnsmasq Auto-Setup** — One-click AP provisioning with automatic interface detection and config generation | `ENABLE_AUTO_SETUP=true` | `true` |
| 2 | **SSID & Password Management** — Change WiFi name, password, encryption (WPA2/WPA3), and hidden SSID from dashboard | `ENABLE_SSID_MANAGER=true` | `true` |
| 3 | **Connected Client List** — Real-time view of all connected devices with hostname, MAC, IP, signal strength, and uptime | `ENABLE_CLIENT_LIST=true` | `true` |
| 4 | **Bandwidth Monitoring** — Per-client and total bandwidth usage tracking with Chart.js graphs | `ENABLE_BANDWIDTH_MONITOR=true` | `true` |
| 5 | **MAC Address Filtering** — Whitelist or blacklist mode to allow/block specific devices | `ENABLE_MAC_FILTER=true` | `false` |
| 6 | **Captive Portal** — Custom landing page for new connections with terms acceptance or password gate | `ENABLE_CAPTIVE_PORTAL=true` | `false` |
| 7 | **QoS Traffic Shaping** — Per-client upload/download speed limits using tc (traffic control) | `ENABLE_QOS=true` | `false` |
| 8 | **Scheduled WiFi On/Off** — Time-based WiFi availability (e.g., disable at night, enable on weekdays) | `ENABLE_WIFI_SCHEDULE=true` | `false` |
| 9 | **Auto Channel Selection** — Automatic WiFi channel selection based on interference scan | `ENABLE_AUTO_CHANNEL=true` | `true` |
| 10 | **DNS Configuration** — Custom upstream DNS servers (Cloudflare, Google, Pi-Hole, custom) | `ENABLE_DNS_CONFIG=true` | `true` |
| 11 | **Dual-Band Support** — Simultaneous 2.4GHz and 5GHz AP on supported WiFi adapters | `ENABLE_DUAL_BAND=true` | `false` |
| 12 | **VPN Tunnel Passthrough** — Route all AP traffic through WireGuard or OpenVPN tunnel | `ENABLE_VPN_PASSTHROUGH=true` | `false` |
| 13 | **Multi-Channel Notifications** — Alerts via Telegram, Slack, email for new connections, bandwidth caps, rogue devices | `ENABLE_NOTIFICATIONS=true` | `false` |
| 14 | **Client Connection History** — Historical log of all device connections/disconnections with timestamps | `ENABLE_CONNECTION_LOG=true` | `true` |
| 15 | **Network Health Dashboard** — Internet uptime, latency, packet loss, and DNS resolution monitoring | `ENABLE_HEALTH_MONITOR=true` | `true` |

---

## 🎛️ Dashboard Feature Toggles

The web dashboard provides a **Settings → Feature Toggles** page where each feature can be enabled/disabled in real time without restarting the service. Toggle state is persisted to `.env` and SQLite.

┌──────────────────────────────────────────────────┐
│  ⚙️ Feature Toggles              [Save All]      │
├──────────────────────────────────────────────────┤
│  🔧 Auto-Setup                 [████ ON ]         │
│  📛 SSID Manager               [████ ON ]         │
│  👥 Client List                [████ ON ]         │
│  📊 Bandwidth Monitor          [████ ON ]         │
│  🛡️ MAC Filtering              [░░░░ OFF]         │
│  🌐 Captive Portal             [░░░░ OFF]         │
│  ⚡ QoS Traffic Shaping         [░░░░ OFF]         │
│  🕐 WiFi Schedule              [░░░░ OFF]         │
│  📡 Auto Channel               [████ ON ]         │
│  🔗 DNS Configuration          [████ ON ]         │
│  📻 Dual-Band                  [░░░░ OFF]         │
│  🔒 VPN Passthrough            [░░░░ OFF]         │
│  🔔 Notifications              [░░░░ OFF]         │
│  📋 Connection Log             [████ ON ]         │
│  💚 Health Monitor             [████ ON ]         │
└──────────────────────────────────────────────────┘

---

## 🔩 Hardware Requirements

| Component | Model / Spec | Qty | Est. Cost |
|-----------|-------------|-----|-----------|
| Raspberry Pi | 4B (2GB+) or 5 | 1 | $45–75 |
| WiFi Adapter (external) | Dual-band USB (RT5572/RTL8812AU) for dual-band | 0–1 | $15–25 |
| Ethernet Cable | Cat5e/Cat6 to router | 1 | $3–5 |
| MicroSD Card | 32GB+ Class 10 | 1 | $8 |
| Power Supply | 5V 3A USB-C | 1 | $10 |
| Case | Passive cooling recommended | 1 | $8–15 |
| **Total** | | | **$66–130** |

> **Note:** The Raspberry Pi 4/5 has onboard WiFi (2.4GHz & 5GHz). An external USB adapter is only needed for dual-band simultaneous operation or for better range/throughput.

---

## 🌐 Network Architecture

```
                    ┌──────────────┐
     Internet ─────►│  ISP Router  │
                    │ 192.168.1.1  │
                    └──────┬───────┘
                           │ Ethernet (eth0)
                    ┌──────┴───────┐
                    │ Raspberry Pi │
                    │   AP Manager │
                    │  10.0.0.1    │
                    ├──────────────┤
                    │  wlan0 (AP)  │──── 2.4 GHz clients
                    │  wlan1 (AP)  │──── 5 GHz clients (dual-band)
                    └──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          📱 Phone    💻 Laptop    🖥️ Desktop
         10.0.0.10   10.0.0.11   10.0.0.12
```

---

## 💻 Software Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask, Flask-SocketIO |
| Frontend | HTML5, CSS3 (dark theme), JavaScript, Chart.js |
| Database | SQLite (clients, bandwidth, logs, settings) |
| Access Point | hostapd (WiFi AP daemon) |
| DHCP/DNS | dnsmasq (DHCP + DNS forwarder) |
| Traffic Control | tc + iptables (QoS, NAT, filtering) |
| VPN | WireGuard / OpenVPN (optional passthrough) |
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
cd "Raspberry_Projects/Hardware & Networking Projects/WiFi Extender & Access Point Manager"
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install system dependencies
```bash
sudo apt update
sudo apt install -y hostapd dnsmasq iptables iw wireless-tools
sudo systemctl stop hostapd dnsmasq  # Will be managed by our app
```

### 4. Configure environment
```bash
cp .env.default .env
nano .env  # Edit variables for your setup
```

### 5. Initialize database
```bash
python3 init_db.py
```

### 6. Run initial AP setup
```bash
sudo python3 setup_ap.py  # Configures hostapd, dnsmasq, iptables
```

### 7. Run as service
```bash
sudo cp deploy/wifi-extender.service /etc/systemd/system/
sudo systemctl enable wifi-extender
sudo systemctl start wifi-extender
```

### 8. Access dashboard
```
http://10.0.0.1:5000  (from WiFi clients)
https://<raspberry-ip>:5000  (from Ethernet network)
Default login: admin / changeme (force-change on first login)
```

---

## 🔐 Environment Variables

Full `.env.default` template:

```env
# ──────────────────────────────────────
# WiFi Extender & Access Point Manager
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
ENABLE_AUTO_SETUP=true
ENABLE_SSID_MANAGER=true
ENABLE_CLIENT_LIST=true
ENABLE_BANDWIDTH_MONITOR=true
ENABLE_MAC_FILTER=false
ENABLE_CAPTIVE_PORTAL=false
ENABLE_QOS=false
ENABLE_WIFI_SCHEDULE=false
ENABLE_AUTO_CHANNEL=true
ENABLE_DNS_CONFIG=true
ENABLE_DUAL_BAND=false
ENABLE_VPN_PASSTHROUGH=false
ENABLE_NOTIFICATIONS=false
ENABLE_CONNECTION_LOG=true
ENABLE_HEALTH_MONITOR=true

# Access Point — Primary (2.4 GHz)
AP_INTERFACE=wlan0
AP_SSID=RaspberryPi-AP
AP_PASSWORD=ChangeMe123!
AP_CHANNEL=6
AP_HW_MODE=g
AP_WPA=2
AP_HIDDEN=0
AP_COUNTRY_CODE=US
AP_MAX_CLIENTS=20

# Access Point — Secondary (5 GHz, dual-band)
AP2_INTERFACE=wlan1
AP2_SSID=RaspberryPi-AP-5G
AP2_PASSWORD=ChangeMe123!
AP2_CHANNEL=36
AP2_HW_MODE=a

# Network
AP_SUBNET=10.0.0.0/24
AP_GATEWAY=10.0.0.1
DHCP_RANGE_START=10.0.0.10
DHCP_RANGE_END=10.0.0.200
DHCP_LEASE_TIME=12h
ETH_INTERFACE=eth0

# DNS
DNS_PRIMARY=1.1.1.1
DNS_SECONDARY=8.8.8.8

# MAC Filtering
MAC_FILTER_MODE=whitelist
MAC_WHITELIST_FILE=config/mac_whitelist.txt
MAC_BLACKLIST_FILE=config/mac_blacklist.txt

# QoS
QOS_DEFAULT_DOWN_KBPS=10000
QOS_DEFAULT_UP_KBPS=5000

# Captive Portal
CAPTIVE_PORTAL_TITLE=Welcome
CAPTIVE_PORTAL_MESSAGE=Accept terms to connect
CAPTIVE_PORTAL_PASSWORD=

# WiFi Schedule
WIFI_ON_TIME=07:00
WIFI_OFF_TIME=23:00
WIFI_SCHEDULE_DAYS=mon,tue,wed,thu,fri,sat,sun

# VPN Passthrough
VPN_TYPE=wireguard
VPN_CONFIG_PATH=/etc/wireguard/wg0.conf

# Auto Channel
CHANNEL_SCAN_INTERVAL_MIN=60

# Health Monitor
HEALTH_PING_TARGET=1.1.1.1
HEALTH_CHECK_INTERVAL_SEC=30

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
DB_PATH=data/wifi_extender.db
```

---

## 🌐 Web Dashboard

Dark-theme responsive dashboard with real-time WebSocket updates:

| Page | Description |
|------|-------------|
| **Dashboard** | AP status, connected clients count, bandwidth graph, internet health |
| **Client List** | Real-time table of connected devices with hostname, MAC, IP, signal, bandwidth |
| **Bandwidth** | Per-client and total bandwidth charts (upload/download), historical trends |
| **MAC Filter** | Whitelist/blacklist management, add/remove by MAC, import/export |
| **Captive Portal** | Preview and customize the captive portal landing page |
| **QoS** | Per-client speed limit configuration, traffic prioritization rules |
| **Schedule** | WiFi on/off schedule calendar with day-of-week and time pickers |
| **DNS** | Upstream DNS configuration, custom DNS entries, query log |
| **Network Health** | Internet uptime chart, latency graph, packet loss monitor |
| **Connection Log** | Historical connection/disconnection events with search/filter |
| **Settings** | Feature toggles, SSID/password, channel, AP config, user management |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate and receive JWT |
| `GET` | `/api/ap/status` | AP status (running/stopped, SSID, channel, clients) |
| `POST` | `/api/ap/restart` | Restart hostapd + dnsmasq |
| `PUT` | `/api/ap/config` | Update SSID, password, channel, encryption |
| `GET` | `/api/clients` | List connected clients with signal/bandwidth |
| `GET` | `/api/clients/<mac>` | Single client details |
| `POST` | `/api/clients/<mac>/disconnect` | Force disconnect a client |
| `GET` | `/api/bandwidth` | Total and per-client bandwidth stats |
| `GET` | `/api/bandwidth/history?hours=24` | Historical bandwidth data |
| `GET` | `/api/mac-filter` | Get whitelist/blacklist |
| `POST` | `/api/mac-filter` | Add MAC to whitelist/blacklist |
| `DELETE` | `/api/mac-filter/<mac>` | Remove MAC from filter |
| `PUT` | `/api/mac-filter/mode` | Switch whitelist ↔ blacklist mode |
| `GET` | `/api/qos/rules` | Get QoS rules for all clients |
| `PUT` | `/api/qos/rules/<mac>` | Set speed limit for client |
| `GET` | `/api/schedule` | Get WiFi schedule |
| `PUT` | `/api/schedule` | Update WiFi on/off schedule |
| `GET` | `/api/dns` | Get DNS configuration |
| `PUT` | `/api/dns` | Update upstream DNS servers |
| `GET` | `/api/health` | Network health (latency, uptime, packet loss) |
| `GET` | `/api/connections/log` | Paginated connection history |
| `GET` | `/api/channels/scan` | Scan WiFi channels and interference |
| `GET` | `/api/settings/features` | Get all feature toggle states |
| `PUT` | `/api/settings/features` | Update feature toggles via dashboard |

---

## 💰 Budget Estimate

| Tier | Components | Cost |
|------|-----------|------|
| **Basic** | Pi 4 + Ethernet cable (single-band, onboard WiFi) | ~$66 |
| **Standard** | + USB WiFi adapter for better range | ~$90 |
| **Full** | + Dual-band USB adapter + case + cooling | ~$130 |

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🪙 Donations

If you find this project helpful, you can support my work:

₿ **Bitcoin:** `bc1q...`
