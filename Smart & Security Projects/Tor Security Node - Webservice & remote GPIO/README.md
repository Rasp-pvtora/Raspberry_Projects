# Tor Security Node — Webservice & Remote GPIO

An all-in-one Tor security node with a web-based dashboard for Raspberry Pi. Host a .onion website, monitor system health, manage a Tor WiFi access point, and control GPIO pins — all from a single web interface.

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Libraries and dependencies](#libraries-and-dependencies)
4. [Quickstart — Laptop (development)](#quickstart--laptop-development)
5. [Environment configuration (.env)](#environment-configuration-env)
6. [Features overview](#features-overview)
7. [Feature 1 — Tor Hidden Service (.onion website)](#feature-1--tor-hidden-service-onion-website)
8. [Feature 2 — System monitor and file browser](#feature-2--system-monitor-and-file-browser)
9. [Feature 3 — Tor access point with GPIO control](#feature-3--tor-access-point-with-gpio-control)
10. [Authentication](#authentication)
11. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
12. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
13. [Real-world applications](#real-world-applications)
14. [Security notes](#security-notes)
15. [Troubleshooting](#troubleshooting)
16. [Where to next](#where-to-next)

---

## Project structure

```
.
├── server.js                ← Node.js entry point (Express + WebSocket)
├── package.json             ← Dependencies and scripts
├── .env.default             ← Environment variable template (copy to .env)
├── .gitignore               ← Git ignore rules
├── src/
│   ├── middleware/
│   │   └── auth.js          ← Session-based authentication middleware
│   ├── routes/
│   │   ├── auth.js          ← Login / logout routes
│   │   ├── system.js        ← System monitoring API
│   │   ├── tor.js           ← Tor hidden service management API
│   │   ├── access-point.js  ← Tor access point API
│   │   ├── gpio.js          ← GPIO read/write API
│   │   ├── files.js         ← File browser API
│   │   └── settings.js      ← Settings / .env management API
│   └── services/
│       ├── system-service.js  ← System info (temp, memory, disk, processes)
│       ├── tor-service.js     ← Tor daemon and hidden service management
│       ├── ap-service.js      ← Access point (hostapd, dnsmasq, iptables)
│       └── gpio-service.js   ← GPIO pin control (onoff library)
├── views/                   ← EJS templates (server-side rendered)
│   ├── layout.ejs           ← Base layout with sidebar navigation
│   ├── login.ejs            ← Login page
│   ├── dashboard.ejs        ← Main dashboard with real-time charts
│   ├── tor-website.ejs      ← Tor hidden service management
│   ├── system.ejs           ← System monitor
│   ├── access-point.ejs     ← Tor access point control
│   ├── gpio.ejs             ← GPIO pin map and control
│   ├── file-browser.ejs     ← Filesystem navigator
│   └── settings.ejs         ← Settings and password management
├── public/                  ← Static frontend assets
│   ├── css/style.css        ← Dark theme dashboard stylesheet
│   └── js/
│       ├── main.js          ← WebSocket client for real-time stats
│       ├── dashboard.js     ← Dashboard page logic + Chart.js
│       ├── system.js        ← System monitor page logic
│       ├── tor.js           ← Tor website page logic
│       ├── gpio.js          ← GPIO control page logic
│       ├── files.js         ← File browser page logic
│       └── ap.js            ← Access point page logic
├── website/                 ← Sample .onion website (3 pages)
│   ├── index.html           ← Home page
│   ├── contact.html         ← Contact page
│   ├── price.html           ← Pricing page
│   └── css/style.css        ← Sample website stylesheet
├── scripts/
│   ├── setup-tor.sh         ← Tor hidden service setup script
│   └── setup-ap.sh          ← Tor access point setup script
├── deploy/
│   └── deploy_to_pi.sh      ← rsync-based deploy script
├── docs/
│   └── threat_model.md      ← Threat model and mitigations
├── tests/                   ← Test directory
├── README.md                ← This file
├── TSD.md                   ← Technical Specification Description
└── task.md                  ← Engineering checklist
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 3B+ / 4 / 5 | Yes | Built-in WiFi for access point; Pi 4 recommended |
| microSD card (16 GB+) | Yes | For the OS and project files |
| Ethernet cable | Yes | Upstream internet connection (required for Tor AP mode) |
| Power supply (official) | Yes | 5V 3A for Pi 4/5 |
| USB WiFi adapter | Optional | For travel router mode (WiFi-to-WiFi) |

---

## Libraries and dependencies

### Runtime dependencies

| Library | Version | Purpose |
|---|---|---|
| [express](https://expressjs.com/) | ^4.21.2 | Web framework and API routing |
| [ejs](https://ejs.co/) | ^3.1.10 | Server-side HTML templating |
| [express-session](https://www.npmjs.com/package/express-session) | ^1.18.1 | Session-based authentication |
| [dotenv](https://www.npmjs.com/package/dotenv) | ^16.4.7 | Load environment variables from `.env` |
| [helmet](https://helmetjs.github.io/) | ^8.0.0 | HTTP security headers |
| [express-rate-limit](https://www.npmjs.com/package/express-rate-limit) | ^7.5.0 | Rate limiting for login endpoint |
| [bcrypt](https://www.npmjs.com/package/bcrypt) | ^5.1.1 | Password hashing |
| [ws](https://www.npmjs.com/package/ws) | ^8.18.0 | WebSocket server for real-time system stats |
| [systeminformation](https://systeminformation.io/) | ^5.23.8 | Cross-platform system info (fallback on non-Pi) |
| [onoff](https://www.npmjs.com/package/onoff) | ^6.0.3 | Raspberry Pi GPIO control |
| [multer](https://www.npmjs.com/package/multer) | ^1.4.5-lts.1 | File upload handling |
| [chart.js](https://www.chartjs.org/) | ^4.4.7 | Real-time charts (loaded via CDN) |

### Dev dependencies

| Library | Version | Purpose |
|---|---|---|
| [jest](https://jestjs.io/) | ^29.7.0 | Testing framework |
| [nodemon](https://nodemon.io/) | ^3.1.9 | Auto-restart on file changes during development |
| [supertest](https://www.npmjs.com/package/supertest) | ^7.0.0 | HTTP assertion library for testing |

### System packages (installed on the Pi)

| Package | Purpose |
|---|---|
| `tor` | Tor daemon for hidden service and transparent proxy |
| `nginx` | Web server for .onion site (localhost-only) |
| `hostapd` | WiFi access point daemon |
| `dnsmasq` | DHCP server for the access point |
| `iptables-persistent` | Persist iptables rules across reboots |
| `Node.js 18+` | JavaScript runtime |

---

## Quickstart — Laptop (development)

**1. Clone the repository**

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/Tor Security Node - Webservice & remote GPIO"
```

**2. Create the `.env` file from the template**

```bash
# Linux / macOS
cp .env.default .env

# Windows
copy .env.default .env
```

Edit `.env` and set your values (at minimum, change `SESSION_SECRET` and `ADMIN_PASSWORD`).

**3. Install dependencies**

```bash
npm install
```

**4. Start the development server**

```bash
npm run dev
```

**5. Open the dashboard**

Navigate to `http://localhost:3000` in your browser.

- **Username:** `admin` (or whatever you set in `.env`)
- **Password:** `changeme` (or whatever you set in `.env`)

> **Note:** On a laptop (non-Pi), GPIO will run in mock mode and Tor/AP features will show as "not active" since the system services are not present. The dashboard, system monitor, file browser, and settings pages work fully.

---

## Environment configuration (.env)

Copy `.env.default` to `.env` and edit it. **Never commit `.env` to git.**

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | Dashboard web server port |
| `HOST` | `0.0.0.0` | Listen address (`0.0.0.0` = all interfaces) |
| `SESSION_SECRET` | `CHANGE_ME...` | Random string for session encryption. Generate with: `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"` |
| `ADMIN_USERNAME` | `admin` | Dashboard login username |
| `ADMIN_PASSWORD` | `changeme` | Dashboard login password |
| `TOR_HIDDEN_SERVICE_DIR` | `/var/lib/tor/tor-security-node` | Tor hidden service directory |
| `TOR_WEBSITE_DIR` | `./website` | Path to the website files served via .onion |
| `TOR_CONTROL_PORT` | `9051` | Tor control port |
| `TOR_SOCKS_PORT` | `9050` | Tor SOCKS proxy port |
| `AP_INTERFACE` | `wlan0` | WiFi interface for access point |
| `AP_SSID` | `TorSecurityNode` | Access point WiFi name |
| `AP_PASSPHRASE` | `changeme123` | Access point WPA2 password (min 8 chars) |
| `AP_SUBNET` | `10.3.141` | Subnet for AP clients |
| `AP_UPSTREAM_INTERFACE` | `eth0` | Upstream internet interface |
| `TOR_TRANSPORT_PORT` | `9040` | Tor transparent proxy port |
| `TOR_DNS_PORT` | `5353` | Tor DNS port |
| `GPIO_ENABLED` | `true` | Enable GPIO features (set `false` on non-Pi) |
| `FILE_BROWSER_ROOT` | `/home/pi` | Root directory for the file browser |

---

## Features overview

The dashboard has a sidebar with seven sections:

| Page | Description |
|---|---|
| **Dashboard** | Overview with real-time temperature, memory, CPU charts, and Tor/AP status |
| **Tor Website** | Start/stop Tor hidden service, view .onion address, edit website files |
| **System Monitor** | Temperature, memory, disk, network, running processes, service management |
| **Tor Access Point** | Enable/disable Tor WiFi hotspot with one click |
| **GPIO Control** | Interactive 40-pin header diagram, configure pins, toggle outputs, read inputs |
| **File Browser** | Navigate the Pi's filesystem graphically, preview files |
| **Settings** | Change password, edit all .env variables from the UI |

---

## Feature 1 — Tor Hidden Service (.onion website)

Host a website accessible only through the Tor network.

**How it works:**

1. The `scripts/setup-tor.sh` script installs Tor and Nginx on the Pi.
2. Nginx serves the `website/` folder on `127.0.0.1:80` (localhost only — not accessible from the internet).
3. Tor creates a Hidden Service that maps a `.onion` address to `127.0.0.1:80`.
4. Visitors access the site using Tor Browser at your `.onion` address.

**From the dashboard:**

- **Start / Stop / Restart** the Tor service.
- **Configure torrc** — writes the hidden service config to `/etc/tor/torrc`.
- **View your .onion address** with a copy-to-clipboard button.
- **Edit website files** directly in the browser — select a file, edit, save.

**Sample website included:**

The `website/` folder contains a three-page demo site (Home, Contact, Pricing) with a dark theme. Replace these files with your own content.

---

## Feature 2 — System monitor and file browser

**System Monitor:**

- **Real-time stats** — CPU temperature, memory usage, and CPU load update live via WebSocket (no page refresh).
- **Charts** — Temperature and memory history plotted with Chart.js.
- **Host info** — Hostname, platform, kernel, CPU model.
- **Network** — All interfaces with IP and MAC addresses.
- **Disk usage** — Mounted filesystems with size, used, and available space.
- **Process manager** — Top 20 processes by CPU usage.
- **Service manager** — Start, stop, restart `tor`, `nginx`, `hostapd`, `dnsmasq` directly from the UI.

**File Browser:**

- Graphical directory navigator rooted at `FILE_BROWSER_ROOT`.
- Breadcrumb navigation, file size, modification date.
- Preview text files directly in the browser.
- Path traversal protection — cannot navigate above the configured root.

---

## Feature 3 — Tor access point with GPIO control

**Tor Access Point:**

- One-click button to **activate** a Tor WiFi hotspot:
  - Creates WiFi hotspot on `wlan0` with `hostapd`.
  - Assigns IPs to clients via `dnsmasq`.
  - Redirects all TCP traffic through Tor's transparent proxy.
  - Routes DNS through Tor's DNS resolver.
  - Blocks UDP (Tor only supports TCP).
- Shows service status (hostapd, dnsmasq, tor) and connected client count.
- One-click **stop** to disable everything.

**GPIO Control:**

- **Interactive 40-pin header diagram** showing all physical pins, color-coded by type (power, ground, GPIO).
- Click a GPIO pin to select it, then configure as **input** or **output**.
- **Toggle outputs** (HIGH/LOW) with a button click.
- **Read input values** in real time.
- **Release pins** when done.
- On non-Pi hardware, GPIO runs in **mock mode** — the interface works but values are simulated.

---

## Authentication

The web dashboard is protected by session-based authentication.

- Credentials are stored in `.env` (`ADMIN_USERNAME` and `ADMIN_PASSWORD`).
- Login attempts are rate-limited (10 attempts per 15 minutes) to prevent brute-force.
- Sessions expire after 24 hours.
- Passwords can be changed from **Settings → Change Password** in the dashboard.
- All `.env` variables can be edited from the Settings page.

---

## How to deploy to Raspberry Pi

Your SSH config is already set up at `~/.ssh/config`:

```
Host rasp-pi
    HostName 192.168.216.90
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

**Method A — Use the deploy script (recommended)**

From the project directory on your laptop:

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/TorSecurityNode
```

This will:
1. Create the remote directory.
2. Rsync all project files (excludes `node_modules`, `.env`, `.git`).
3. Run `npm install --production` on the Pi.
4. Create `.env` from `.env.default` if it does not exist.

**Method B — Manual rsync**

```bash
rsync -avz --delete \
  --exclude='node_modules/' \
  --exclude='.env' \
  --exclude='.git/' \
  ./ \
  rasp-pi:/home/pi/Projects/TorSecurityNode/

ssh rasp-pi "cd /home/pi/Projects/TorSecurityNode && npm install --production"
```

---

## How to run on the Raspberry Pi

**1. SSH into the Pi**

```bash
ssh rasp-pi
```

**2. Go to the project directory**

```bash
cd /home/pi/Projects/TorSecurityNode
```

**3. Edit the .env file**

```bash
nano .env
```

Set `SESSION_SECRET` to a random string and change `ADMIN_PASSWORD`.

**4. Start the dashboard**

```bash
node server.js
```

Access it from your browser at `http://192.168.216.90:3000`.

**5. (Optional) Set up Tor Hidden Service**

```bash
sudo bash scripts/setup-tor.sh
```

**6. (Optional) Set up Tor Access Point**

```bash
sudo bash scripts/setup-ap.sh
```

**7. (Optional) Run as a systemd service**

```bash
sudo nano /etc/systemd/system/tor-security-node.service
```

```ini
[Unit]
Description=Tor Security Node Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/TorSecurityNode
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable tor-security-node
sudo systemctl start tor-security-node
```

---

## Real-world applications

| Application | Who uses it | Why |
|---|---|---|
| **Journalist safe house node** | Journalists, whistleblowers | Host a secure drop site (.onion) for sources to submit documents anonymously, while monitoring the Pi remotely |
| **Privacy kiosk for events** | Event organizers, security conferences | Set up a Tor WiFi hotspot at conferences so attendees browse anonymously; monitor usage from the dashboard |
| **Home IoT security gateway** | Privacy-conscious homeowners | Route smart home traffic through Tor, control GPIO-connected relays (door locks, lights) securely via the dashboard |
| **Penetration testing lab** | Security researchers | Host honeypot .onion sites, monitor who connects, control test equipment via GPIO |
| **Education & cyber-security training** | Teachers, students | Hands-on lab for learning about Tor, network security, Linux system administration, and IoT in one device |
| **Remote sensor station** | Field researchers | Deploy a Pi in a remote location; read sensors (GPIO), monitor system health, and communicate data over Tor for anonymity |
| **Censorship circumvention node** | Activists in restrictive countries | Provide a Tor access point for a household/office; host information on a .onion site that cannot be censored |
| **Small business secure communication hub** | Small businesses | Host a private .onion site for internal communications that cannot be intercepted or accessed externally |
| **Emergency response coordination** | Disaster relief teams, NGOs | Deploy a portable Tor node with WiFi AP for teams in areas with compromised or surveilled infrastructure |
| **Diplomatic secure outpost** | Embassies, diplomatic staff | Provide secure, anonymous internet access and a private .onion site for sensitive diplomatic communications |
| **Underground library / censorship-resistant publishing** | Authors, publishers, archivists | Host a digital library on the dark web making books, research, and documents available in countries with content restrictions |

---

## Security notes

- **Change the default password immediately** after first login. Use the Settings page or edit `.env`.
- **Generate a strong `SESSION_SECRET`** — run: `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`
- **The `.env` file contains sensitive data.** It is in `.gitignore` and should never be committed. Protect it with file permissions: `chmod 600 .env`
- **Rate limiting** is enabled on the login endpoint (10 attempts per 15 minutes).
- **Helmet** sets security headers (CSP, X-Frame-Options, etc.) on all responses.
- **File browser** is restricted to `FILE_BROWSER_ROOT` with path traversal protection.
- **GPIO access requires root on the Pi.** Run the app with appropriate permissions or add the `pi` user to the `gpio` group.
- **Tor Hidden Service keys** in `/var/lib/tor/tor-security-node/` must be protected. Anyone with these keys can impersonate your `.onion` site.
- **The web dashboard itself is NOT served via Tor** — it runs on the local network. Access it only from trusted networks.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Dashboard not loading | Check if the server is running. Verify the Pi's IP and port. Check `node server.js` output for errors. |
| Login fails | Verify credentials in `.env`. Check rate limiting (wait 15 min or restart server). |
| GPIO shows "not available" | Install `onoff`: `npm install onoff`. Ensure GPIO is enabled on the Pi. |
| Tor status shows "Stopped" | Run `sudo systemctl status tor`. Run `sudo bash scripts/setup-tor.sh` for initial setup. |
| No .onion address | Tor needs time to generate keys. Wait 30–60 seconds. Check `sudo cat /var/lib/tor/tor-security-node/hostname`. |
| Access point not starting | Check `sudo systemctl status hostapd`. Verify `wlan0` is not connected to another network. |
| File browser shows "Path traversal denied" | The requested path is outside `FILE_BROWSER_ROOT`. Edit `.env` to adjust. |
| WebSocket disconnects | The browser may be on a different network. Ensure the WebSocket URL matches the server. |
| `npm install` fails on Pi | Ensure Node.js 18+ is installed: `node --version`. Install via NodeSource: `curl -fsSL https://deb.nodesource.com/setup_18.x \| sudo bash -` |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- See [task.md](task.md) for the engineering checklist with step-by-step implementation tasks.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model and mitigations.
