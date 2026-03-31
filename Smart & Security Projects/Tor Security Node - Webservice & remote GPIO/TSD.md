# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for **Tor Security Node — Webservice & Remote GPIO**.

---

## 1. Scope

This project provides a unified web-based dashboard running on a Raspberry Pi that combines three major capabilities into one security-focused appliance:

1. **Tor Hidden Service hosting** — serve a website accessible exclusively via the Tor network (.onion address).
2. **System monitoring and file management** — real-time system health, process management, service control, and graphical file browser.
3. **Tor Access Point with GPIO control** — one-click Tor WiFi hotspot and interactive hardware pin control.

The dashboard is built with Node.js (Express), uses EJS for server-side rendering, and communicates in real time via WebSocket. Authentication, rate limiting, and security headers protect the interface.

---

## 2. Minimum Viable Features (MVP)

### 2.1 Web Dashboard (Node.js + Express + EJS)

- **Authentication:** Session-based login with credentials stored in `.env`. Rate-limited login endpoint (10 attempts per 15 min). Password changeable from the Settings page.
- **HTTPS support:** Native self-signed TLS certificate, auto-generated on first start. Set `HTTPS_ENABLED=true` in `.env`. Also supports custom cert/key files.
- **Layout:** Dark-themed sidebar navigation with pages for Dashboard, Tor Website, System Monitor, Access Point, GPIO, File Browser, and Settings.
- **Real-time data:** WebSocket server (ws/wss) pushes system stats (temperature, memory, CPU) to the browser every 2 seconds. Chart.js renders live temperature and memory history graphs.
- **Settings page:** Edit all `.env` variables from the web interface. Changes are written to the `.env` file and take effect immediately (or on restart for some variables).

### 2.2 Feature 1 — Tor Hidden Service

- Install and configure Tor to expose a v3 Hidden Service.
- Serve a sample three-page website (Home, Contact, Pricing) via Nginx on `127.0.0.1:80`.
- Dashboard controls: start/stop/restart Tor, configure torrc, view .onion address (copy button).
- Website file editor: list website files, edit content, save directly from the dashboard.
- Setup script (`scripts/setup-tor.sh`) for automated installation.

### 2.3 Feature 2 — System Monitor and File Browser

- **System stats:** CPU temperature (from sysfs or `systeminformation`), memory usage, CPU load averages, uptime.
- **Host info:** Hostname, platform, architecture, kernel version, CPU model and core count.
- **Network:** All interfaces with IP and MAC addresses.
- **Disk usage:** Mounted filesystems with size, used, available, and percentage.
- **Process list:** Top 20 processes by CPU, with PID, user, CPU%, MEM%, and command.
- **Service manager:** Start/stop/restart `tor`, `nginx`, `hostapd`, `dnsmasq` from the dashboard. Restricted to these four services for safety.
- **File browser:** Navigate the Pi's filesystem from `FILE_BROWSER_ROOT`. Directory listing with icons, sizes, and modification dates. File preview for text files (max 1 MB). Path traversal protection.

### 2.4 Feature 3 — Tor Access Point and GPIO Control

- **Tor Access Point:**
  - One-click start: writes hostapd.conf, dnsmasq.conf, configures iptables for Tor transparent proxy, starts all services.
  - One-click stop: stops services and flushes iptables rules.
  - Status panel: shows hostapd/dnsmasq/tor status and connected client count.
  - **Captive portal:** When `CAPTIVE_PORTAL_ENABLED=true`, devices connecting to the WiFi are automatically redirected to the dashboard login page (HTTP port 80 → dashboard port). This allows users to open the web-app automatically when they connect to the AP.
  - Setup script (`scripts/setup-ap.sh`) for permanent system-level installation.

- **WiFi-to-WiFi Travel Mode:**
  - "Search WiFi-2-WiFi USB Adapter" button scans for connected USB WiFi interfaces.
  - Scan available upstream WiFi networks via the USB adapter.
  - Select an upstream network, enter password, and start travel mode.
  - The USB adapter connects to the upstream WiFi; the built-in wlan0 becomes the Tor AP.
  - Travel mode status panel shows upstream connection state and AP status.

- **GPIO Control:**
  - Pin layout loaded from JSON preset files (`gpio-presets/` directory).
  - Default preset: Raspberry Pi 4 Model B (`rpi4b.json`). Configurable via `GPIO_PRESET_FILE` in `.env`.
  - Available presets: Pi 4B, Pi 3B+, Pi 5, Pi Zero 2 W.
  - Presets contain pin layout, alt functions, and optional default pin configurations.
  - "Apply Preset Defaults" button auto-configures default pins from the preset.
  - Color-coded 40-pin header, configure as input or output, toggle, read, release.
  - Mock mode on non-Pi hardware for development.

### 2.5 Environment Configuration

- All configuration via `.env` file (created from `.env.default` template).
- `.env` is in `.gitignore` and never committed.
- `.env.default` is committed as a reference with documentation for each variable.
- Settings page provides a web-based editor for all `.env` variables.

### 2.6 Deployment

- `deploy/deploy_to_pi.sh` script: rsync files to the Pi (via `rasp-pi` SSH alias at `192.168.216.90`), install npm dependencies, create `.env` from template.
- Systemd service file for auto-start on boot.

---

## 3. Nice-to-Have Features

These features require paid third-party services or significantly more complexity.

- **VPN integration for the Access Point:**
  - Route AP traffic through VPN → Tor (or VPN alone). Requires a paid VPN subscription (e.g., Mullvad, ProtonVPN).

- **Dynamic DNS for remote dashboard access:**
  - Access the dashboard from outside the home network. Some DDNS services are free, others are paid.

- **Cloud monitoring:**
  - Forward Grafana dashboards or alerts to Grafana Cloud (paid tier) for remote visibility.

- **Tor Bridge / obfs4 obfuscation:**
  - Support for Tor bridges to bypass censorship in restrictive networks.

- **Multi-user support:**
  - Multiple dashboard accounts with role-based access (admin vs. read-only).

---

## 4. High-level Architecture

```
                      ┌──────────────────────────────────────────────┐
                      │            Raspberry Pi                      │
                      │                                              │
  Browser ─HTTP/S───► │  Express (port 3000, HTTP or HTTPS)          │
  Browser ──WS/S────► │  ├── Session auth + rate limiting            │
                      │  ├── HTTPS native (selfsigned / custom cert) │
                      │  ├── EJS views (dashboard, system, etc.)     │
                      │  ├── REST API (/api/system, /api/tor, etc.)  │
                      │  ├── WebSocket (live system stats)           │
                      │  └── Static files (/public)                  │
                      │                                              │
                      │  Services Layer:                              │
                      │  ├── system-service  → sysfs, /proc, os      │
                      │  ├── tor-service     → systemctl tor, torrc  │
                      │  ├── ap-service      → hostapd, dnsmasq, ipt │
                      │  │    ├── captive portal (HTTP→dashboard)    │
                      │  │    └── travel mode (USB WiFi upstream)    │
                      │  └── gpio-service    → onoff + JSON presets  │
                      │                                              │
                      │  Tor Hidden Service:                          │
                      │  ├── Tor daemon → .onion address              │
                      │  └── Nginx (127.0.0.1:80) → website/         │
                      │                                              │
                      │  Tor Access Point:                            │
                      │  ├── hostapd (wlan0 WiFi hotspot)            │
                      │  ├── dnsmasq (DHCP for AP clients)           │
                      │  ├── iptables → Tor TransPort/DNS            │
                      │  └── captive portal → auto-open dashboard    │
                      │                                              │
                      │  GPIO:                                        │
                      │  ├── 40-pin header (read/write via onoff)    │
                      │  └── Presets: rpi4b / rpi3b+ / rpi5 / zero2w │
                      └──────────────────────────────────────────────┘
```

---

## 5. Security and Threat Model

**Primary assets:**
- Dashboard credentials and session tokens.
- Tor Hidden Service private key (`.onion` identity).
- GPIO pin access (can control physical hardware).
- System-level access (service management, file browser).
- `.env` file (contains passwords and secrets).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Brute-force login | Rate limiting (10 attempts per 15 min); strong password in `.env` |
| Session hijacking | `httpOnly`, `sameSite`, session secret; native HTTPS with `secure` cookie flag |
| Path traversal in file browser | `path.resolve()` + startsWith check against `FILE_BROWSER_ROOT` |
| Path traversal in website editor | Same protection: resolved path must start with `TOR_WEBSITE_DIR` |
| Service injection via service manager | Whitelist of allowed services (`tor`, `nginx`, `hostapd`, `dnsmasq`) |
| XSS via user input | Helmet CSP headers; EJS auto-escaping; Content-Type-Options nosniff |
| Unauthorized GPIO access | Authentication required for all API endpoints |
| `.env` exposure | In `.gitignore`; chmod 600 recommended; masked in Settings API |
| Tor Hidden Service key theft | Protected by file permissions (`debian-tor` user, `chmod 700`) |
| Network sniffing of dashboard | Native HTTPS support (self-signed or custom cert); `secure` cookie flag |
| Physical access to the Pi | Physical security; consider full-disk encryption |

See [docs/threat_model.md](docs/threat_model.md) for the complete analysis.

---

## 6. Suggested Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| Backend | Node.js 18+ / Express 4 | Lightweight, event-driven, perfect for real-time WebSocket |
| Templating | EJS | Simple, no build step, server-side rendering |
| Real-time | ws (WebSocket) | Low-overhead bidirectional communication |
| Charts | Chart.js (CDN) | Lightweight, responsive, no build required |
| Auth | express-session + bcrypt | Simple session-based auth suited for single-user device |
| Security | helmet + express-rate-limit | Industry-standard Express security middleware |
| TLS | selfsigned | Auto-generate self-signed certificates for native HTTPS |
| GPIO | onoff | Proven Node.js GPIO library for Raspberry Pi |
| System info | sysfs + os module + systeminformation | Native for Pi, fallback for development |
| CSS | Custom dark theme | No framework dependency, lightweight |
| Tor | System tor package | Standard Tor daemon |
| Web server | Nginx | Lightweight, serves .onion site on localhost |
| AP | hostapd + dnsmasq | Standard Linux WiFi AP and DHCP |
| Networking | iptables | Transparent Tor proxying |

---

## 7. Development Phases & Concrete Steps

### Phase A — Project scaffold and dashboard (Week 1)

1. Initialize Node.js project with `package.json` and dependencies.
2. Create `.env.default` template and `.gitignore`.
3. Implement Express server with EJS layout and sidebar navigation.
4. Implement session-based authentication (login, logout, middleware).
5. Create the dark-themed CSS and login page.
6. Implement WebSocket server for real-time system stats.
7. Build the Dashboard page with Chart.js graphs.

### Phase B — System monitor and file browser (Week 1–2)

1. Implement `system-service.js` (temperature, memory, disk, network, processes).
2. Build the System Monitor page with all stat panels.
3. Implement service manager (start/stop/restart allowed services).
4. Implement file browser API with path traversal protection.
5. Build the File Browser page with breadcrumb navigation and file preview.

### Phase C — Tor Hidden Service (Week 2)

1. Write `setup-tor.sh` script for Tor and Nginx installation.
2. Implement `tor-service.js` (status, start/stop, configure torrc, file management).
3. Build the Tor Website page (status, .onion address, file editor).
4. Create the sample three-page website in `website/`.

### Phase D — Tor Access Point and GPIO (Week 2–3)

1. Write `setup-ap.sh` script for hostapd/dnsmasq/iptables.
2. Implement `ap-service.js` (start/stop AP, status, client count).
3. Add captive portal iptables rules (redirect HTTP → dashboard).
4. Implement WiFi-to-WiFi travel mode (USB adapter scan, network scan, connect, start AP).
5. Build the Access Point page with one-click controls and travel mode UI.
6. Implement `gpio-service.js` (preset loading, pin layout, configure, read, write, release).
7. Create GPIO preset JSON files for Pi 4B (default), Pi 3B+, Pi 5, Pi Zero 2 W.
8. Build the GPIO page with interactive 40-pin header diagram and preset controls.

### Phase E — HTTPS and settings (Week 3)

1. Implement native HTTPS support with selfsigned library (auto-generate on first start).
2. Add `HTTPS_ENABLED`, `HTTPS_CERT_PATH`, `HTTPS_KEY_PATH` env vars.
3. Write `scripts/generate-cert.sh` for manual openssl cert generation.
4. Implement Settings API (read/write `.env`, change password).
5. Build the Settings page with env editor and password change form.
6. Write `deploy_to_pi.sh` deployment script.
7. Create systemd service file for auto-start.
8. Test full deployment on Raspberry Pi.

### Phase F — Documentation and polish (Week 3–4)

1. Write `README.md` with full setup guide.
2. Write `TSD.md` (this document).
3. Write `task.md` engineering checklist.
4. Write `docs/threat_model.md`.
5. Test all features end-to-end on Pi.

---

## 8. Deliverables

- Full working Node.js dashboard with authentication and native HTTPS.
- Tor Hidden Service management with sample .onion website.
- Real-time system monitoring with Chart.js graphs.
- One-click Tor Access Point control with captive portal.
- WiFi-to-WiFi travel mode with USB WiFi adapter support.
- Interactive GPIO pin control with hardware-specific preset files.
- Graphical file browser.
- Settings management from UI.
- Setup scripts for Tor, AP, and TLS certificate generation.
- Deploy script for Raspberry Pi (SSH alias: `rasp-pi` at `192.168.216.90`).
- `README.md`, `TSD.md`, `task.md`, `docs/threat_model.md`.
