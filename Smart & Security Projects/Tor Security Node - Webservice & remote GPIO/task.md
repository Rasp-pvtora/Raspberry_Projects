# Task Checklist — Tor Security Node

Step-by-step engineering checklist for implementing the Tor Security Node project.

---

## Phase A — Project Scaffold & Dashboard

- [x] Initialize `package.json` with all dependencies
- [x] Create `.env.default` with all configuration variables documented
- [x] Create `.gitignore` (node_modules, .env, tor-data, sessions, coverage)
- [x] Create `server.js` — Express server with EJS, sessions, helmet, rate limiting
- [x] Create `src/middleware/auth.js` — session-based authentication middleware
- [x] Create `src/routes/auth.js` — login/logout routes
- [x] Create `views/layout.ejs` — base layout with sidebar navigation
- [x] Create `views/login.ejs` — login page with form and error handling
- [x] Create `public/css/style.css` — dark-themed dashboard stylesheet
- [x] Create `public/js/main.js` — WebSocket client for real-time top-bar stats
- [x] Implement WebSocket server in `server.js` (authenticated upgrade)
- [x] Create `views/dashboard.ejs` — overview page with stat cards
- [x] Create `public/js/dashboard.js` — Chart.js temperature/memory history

## Phase B — System Monitor & File Browser

- [x] Create `src/services/system-service.js`
  - [x] `getCpuTemperature()` — read from sysfs, fallback to systeminformation
  - [x] `getMemoryInfo()` — total/used/free/percent from os module
  - [x] `getCpuLoad()` — 1/5/15 minute load averages
  - [x] `getDiskUsage()` — parse `df` output
  - [x] `getNetworkInfo()` — interfaces, IPs, MACs from os.networkInterfaces
  - [x] `getUptime()` — formatted uptime string
  - [x] `getHostInfo()` — hostname, platform, arch, kernel, CPU model
  - [x] `getProcesses()` — top 20 by CPU from `ps aux`
  - [x] `getQuickStats()` — lightweight stats for WebSocket
  - [x] `getFullReport()` — all stats combined
  - [x] `isServiceActive()` — check systemd service status
  - [x] `manageService()` — start/stop/restart (whitelisted services only)
- [x] Create `src/routes/system.js` — REST API for system stats and service management
- [x] Create `views/system.ejs` — system monitor page
- [x] Create `public/js/system.js` — system page logic with real-time updates
- [x] Create `src/routes/files.js` — file browser API with path traversal protection
  - [x] `GET /api/files/list?path=` — list directory contents
  - [x] `GET /api/files/read?path=` — read file content (max 1MB)
  - [x] Path validation: resolved path must start with FILE_BROWSER_ROOT
- [x] Create `views/file-browser.ejs` — file browser page
- [x] Create `public/js/files.js` — file browser with breadcrumb navigation

## Phase C — Tor Hidden Service

- [x] Create `src/services/tor-service.js`
  - [x] `getOnionAddress()` — read from hidden service hostname file
  - [x] `isTorRunning()` — check systemctl is-active tor
  - [x] `getTorStatus()` — combined status object
  - [x] `startTor()` / `stopTor()` / `restartTor()` — service management
  - [x] `configureHiddenService()` — write HiddenServiceDir/Port to torrc
  - [x] `getWebsiteFiles()` — list files in TOR_WEBSITE_DIR
  - [x] `readWebsiteFile()` — read with path traversal protection
  - [x] `writeWebsiteFile()` — write with path traversal protection
- [x] Create `src/routes/tor.js` — Tor management REST API
- [x] Create `views/tor-website.ejs` — Tor website management page
- [x] Create `public/js/tor.js` — Tor page logic (status, file editor)
- [x] Create sample website in `website/`
  - [x] `website/index.html` — Home page
  - [x] `website/contact.html` — Contact page
  - [x] `website/price.html` — Pricing page
  - [x] `website/css/style.css` — Sample website dark theme
- [x] Create `scripts/setup-tor.sh` — automated Tor + Nginx setup on Pi

## Phase D — Tor Access Point & GPIO Control

- [x] Create `src/services/ap-service.js`
  - [x] `getAPStatus()` — check hostapd/dnsmasq/tor status, client count
  - [x] `startAP()` — write configs, set iptables, start services
  - [x] `stopAP()` — stop services, flush iptables
- [x] Create `src/routes/access-point.js` — AP management REST API
- [x] Create `views/access-point.ejs` — AP control page
- [x] Create `public/js/ap.js` — AP page logic
- [x] Create `scripts/setup-ap.sh` — automated AP setup on Pi
- [x] Create `src/services/gpio-service.js`
  - [x] Full 40-pin header layout definition
  - [x] `isAvailable()` — check if GPIO hardware is present
  - [x] `getPinLayout()` — layout with current states
  - [x] `configurePin()` — set pin direction (in/out)
  - [x] `readPin()` / `writePin()` — read/write pin values
  - [x] `releasePin()` / `releaseAll()` — clean up
  - [x] Mock mode for non-Pi development
  - [x] Process exit cleanup (SIGINT/SIGTERM)
- [x] Create `src/routes/gpio.js` — GPIO REST API
- [x] Create `views/gpio.ejs` — GPIO control page with pin map
- [x] Create `public/js/gpio.js` — interactive pin diagram and controls

## Phase E — Settings & Deployment

- [x] Create `src/routes/settings.js`
  - [x] `GET /api/settings` — read .env (passwords masked)
  - [x] `PUT /api/settings` — update .env variables
  - [x] `PUT /api/settings/password` — change admin password
- [x] Create `views/settings.ejs` — settings page with env editor and password form
- [x] Create `deploy/deploy_to_pi.sh` — rsync deploy script for rasp-pi (192.168.216.90)
- [ ] Create systemd service file on Pi (`tor-security-node.service`)
- [ ] Test deploy script end-to-end

## Phase F — Documentation

- [x] Create `README.md` — full setup guide, features, deployment, troubleshooting
- [x] Create `TSD.md` — technical specification
- [x] Create `task.md` — this checklist
- [x] Create `docs/threat_model.md` — threat model and mitigations
- [x] Create `.env.default` — documented environment template
- [ ] Test all features on Raspberry Pi
- [ ] Run `npm test` and verify all tests pass

## Phase G — Testing (future)

- [ ] Unit tests for `system-service.js` (mock sysfs/os data)
- [ ] Unit tests for `tor-service.js` (mock file reads/exec)
- [ ] Unit tests for `gpio-service.js` (mock onoff)
- [ ] Integration tests for auth routes (login/logout flow)
- [ ] Integration tests for API routes (authenticated requests)
- [ ] End-to-end test: deploy to Pi, verify dashboard loads
- [ ] End-to-end test: Tor hidden service accessible via Tor Browser
- [ ] End-to-end test: AP starts and routes traffic through Tor

## Phase H — Nice-to-Have (future)

- [ ] VPN integration for Access Point (requires paid VPN subscription)
- [ ] Dynamic DNS for remote dashboard access
- [ ] Tor Bridge / obfs4 support for censored networks
- [ ] Multi-user support with role-based access
- [ ] GPIO presets (save/load pin configurations)
- [ ] Travel router mode (WiFi-to-WiFi with USB adapter)
- [ ] HTTPS for the dashboard (self-signed or Let's Encrypt)
