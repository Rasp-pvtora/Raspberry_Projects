# Task List — Rogue Access Point Detector

## Phase 1 — Project Foundation & Scanning Engine

- [ ] **1.1 Initialize project structure**
  - [ ] Create directory tree (`src/`, `templates/`, `static/`, `tests/`, `deploy/`, `scripts/`, `docs/`, `data/`)
  - [ ] Create `pyproject.toml` with project metadata
  - [ ] Create `requirements.txt` with all dependencies
  - [ ] Create `.env.example` with all variables and defaults
  - [ ] Create `src/__init__.py`
  - [ ] Create `tests/__init__.py` and `tests/conftest.py`

- [ ] **1.2 Implement configuration loader**
  - [ ] Create `src/config.py` with dataclass for all `.env` variables
  - [ ] Load and validate `.env` using `python-dotenv`
  - [ ] Type conversion for int, float, bool values
  - [ ] Defaults for all optional settings
  - [ ] Feature-toggle helper method (`is_enabled("feature_name")`)

- [ ] **1.3 Implement SQLite database module**
  - [ ] Create `src/database.py` with connection manager
  - [ ] Enable WAL mode on connection
  - [ ] Create `access_points` table schema
  - [ ] Create `scan_events` table schema
  - [ ] Create `threats` table schema
  - [ ] Create `baseline_aps` table schema
  - [ ] Create `settings` table schema
  - [ ] Implement `init_db()` to create all tables
  - [ ] Implement CRUD helpers for each table
  - [ ] Implement parameterized queries for all DB operations

- [ ] **1.4 Implement scanning engine**
  - [ ] Create `src/scanner.py`
  - [ ] Implement channel hopping thread (2.4 GHz channels 1–14)
  - [ ] Implement channel hopping for 5 GHz channels (36–165)
  - [ ] Implement configurable band selection (`SCAN_BANDS`)
  - [ ] Implement scapy beacon/probe-response frame handler
  - [ ] Extract AP metadata: SSID, BSSID, channel, signal, encryption
  - [ ] Persist discovered APs to `access_points` table
  - [ ] Create `scan_events` record per scan cycle
  - [ ] Implement configurable scan interval (`SCAN_INTERVAL`)
  - [ ] Run scanner as background daemon thread

- [ ] **1.5 Implement OUI vendor lookup**
  - [ ] Create `src/oui_lookup.py`
  - [ ] Initialize `manuf.MacParser` with offline database
  - [ ] Implement `lookup_vendor(bssid) -> str` function
  - [ ] Cache lookups in memory to reduce disk reads
  - [ ] Integrate vendor lookup into AP discovery pipeline
  - [ ] Toggle via `ENABLE_OUI_LOOKUP`

- [ ] **1.6 Implement mock mode**
  - [ ] Add mock AP data generator to scanner module
  - [ ] Generate realistic fake APs (varied SSIDs, BSSIDs, channels, signals)
  - [ ] Simulate channel hopping delay
  - [ ] Conditional activation via `MOCK_MODE=true`
  - [ ] Simulate occasional evil twin and deauth events for testing

- [ ] **1.7 Write Phase 1 tests**
  - [ ] Test config loader (valid `.env`, missing values, type conversion)
  - [ ] Test database schema creation and CRUD operations
  - [ ] Test scanner AP extraction from mock frames
  - [ ] Test OUI lookup (known MAC, unknown MAC)
  - [ ] Test mock mode data generation

---

## Phase 2 — Detection Engine & Baseline

- [ ] **2.1 Implement baseline AP learning**
  - [ ] Create `src/baseline.py`
  - [ ] Implement `learn_baseline()` — snapshot current APs
  - [ ] Store baseline entries in `baseline_aps` table
  - [ ] Implement `--learn-baseline` CLI flag
  - [ ] Toggle via `ENABLE_BASELINE_LEARNING`

- [ ] **2.2 Implement baseline comparison**
  - [ ] Compare scan results against `baseline_aps`
  - [ ] Detect new APs not in baseline → `NEW_AP` threat
  - [ ] Detect changed encryption for known BSSID
  - [ ] Detect channel migration for known BSSID
  - [ ] Auto-learn mode (`BASELINE_AUTO_LEARN=true`)

- [ ] **2.3 Implement Evil Twin detection**
  - [ ] Create `src/detector.py`
  - [ ] Match SSIDs between scan results and baseline
  - [ ] Flag SSID match with different BSSID as `EVIL_TWIN`
  - [ ] Flag SSID match with weaker/different encryption as `EVIL_TWIN`
  - [ ] Assign severity `HIGH`
  - [ ] Include legitimate AP details in threat record for comparison

- [ ] **2.4 Implement deauthentication flood detection**
  - [ ] Register scapy handler for deauth (subtype 0x0c) and disassoc (subtype 0x0a) frames
  - [ ] Count frames per source MAC per second
  - [ ] Trigger `DEAUTH_FLOOD` alert when count exceeds `DEAUTH_THRESHOLD`
  - [ ] Identify attacker MAC and target BSSID
  - [ ] Assign severity `CRITICAL`
  - [ ] OUI lookup on attacker MAC

- [ ] **2.5 Implement rogue AP detection**
  - [ ] Flag any new AP not in baseline as `ROGUE_AP` with severity `MEDIUM`
  - [ ] Differentiate from `EVIL_TWIN` (no SSID match required)
  - [ ] Suppress repeated alerts for same BSSID within cooldown window

- [ ] **2.6 Integrate detector with threat database**
  - [ ] Write all detected threats to `threats` table
  - [ ] Include full metadata (type, severity, SSID, BSSID, vendor, GPS, details JSON)
  - [ ] Mark `alert_sent` after successful dispatch

- [ ] **2.7 Write Phase 2 tests**
  - [ ] Test baseline learning (snapshot, persist, retrieve)
  - [ ] Test baseline comparison (new AP, changed encryption, channel migration)
  - [ ] Test Evil Twin detection (various SSID/BSSID/encryption combos)
  - [ ] Test deauth flood detection (below threshold, at threshold, above threshold)
  - [ ] Test rogue AP detection (new unknown AP)
  - [ ] Test threat DB integration (record creation, deduplication)

---

## Phase 3 — Web Dashboard & Authentication

- [ ] **3.1 Implement Flask app factory**
  - [ ] Create `src/app.py` with `create_app()` factory
  - [ ] Initialize Flask-SocketIO with eventlet
  - [ ] Register blueprints/routes
  - [ ] Integrate config and database initialization
  - [ ] Implement `__main__` entry point

- [ ] **3.2 Implement authentication**
  - [ ] Create `src/auth.py`
  - [ ] Implement bcrypt password verification
  - [ ] Implement login route (`POST /login`)
  - [ ] Implement logout route (`POST /logout`)
  - [ ] Implement rate limiting (10 attempts per 15 minutes per IP)
  - [ ] Implement session with 24-hour expiry
  - [ ] Implement `@login_required` decorator for all protected routes
  - [ ] Read `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` from config

- [ ] **3.3 Create dark theme templates and CSS**
  - [ ] Create `templates/base.html` with dark theme layout
  - [ ] Create `static/css/style.css` with dark color scheme
  - [ ] Responsive layout for desktop and tablet
  - [ ] Navigation bar with app title and logout button

- [ ] **3.4 Build login page**
  - [ ] Create `templates/login.html`
  - [ ] Username and password form with CSRF token
  - [ ] Error message display for failed login
  - [ ] Rate limit warning display

- [ ] **3.5 Build dashboard page**
  - [ ] Create `templates/dashboard.html`
  - [ ] Live AP table (SSID, BSSID, channel, signal, vendor, status, last seen)
  - [ ] Sortable columns
  - [ ] Threat feed panel (chronological, severity badges)
  - [ ] Scan status indicator (running/stopped, last scan time)
  - [ ] Summary cards (total APs, baseline APs, active threats, scan count)

- [ ] **3.6 Implement SocketIO real-time updates**
  - [ ] Emit `ap_update` events on each scan cycle
  - [ ] Emit `threat_alert` events on new threat detection
  - [ ] Emit `scan_status` events (started, completed, error)
  - [ ] Client-side SocketIO handler in `static/js/dashboard.js`
  - [ ] DOM update functions for AP table and threat feed

- [ ] **3.7 Implement Chart.js graphs**
  - [ ] Create `static/js/charts.js`
  - [ ] Signal strength over time line chart (top N APs)
  - [ ] Channel utilization bar chart (AP count per channel)
  - [ ] Threat timeline chart (threats over time by type)
  - [ ] Auto-refresh charts via SocketIO data push

- [ ] **3.8 Build settings panel**
  - [ ] Create `templates/settings.html`
  - [ ] Baseline AP management (list, approve, reject, reset)
  - [ ] Runtime feature toggles (scanning, detection, alerts)
  - [ ] Current configuration display (read-only sensitive values)
  - [ ] Manual baseline learn trigger button

- [ ] **3.9 Write Phase 3 tests**
  - [ ] Test login (valid credentials, invalid credentials, rate limiting)
  - [ ] Test session expiry (24-hour window)
  - [ ] Test protected route access (authenticated vs unauthenticated)
  - [ ] Test dashboard data API endpoints
  - [ ] Test SocketIO event emission
  - [ ] Test settings panel baseline management

---

## Phase 4 — Alert Channels & SIEM

- [ ] **4.1 Implement alert dispatcher**
  - [ ] Create `src/alerts.py` with `AlertDispatcher` class
  - [ ] Implement alert rate limiting (prevent spam during sustained attacks)
  - [ ] Implement master toggle (`ENABLE_ALERTS`)
  - [ ] Format threat data into alert message (type, severity, SSID, BSSID, vendor, GPS, time)
  - [ ] Dispatch to all enabled channels in parallel

- [ ] **4.2 Implement email alerts**
  - [ ] SMTP email sending with TLS
  - [ ] Configurable recipient (`ALERT_EMAIL_TO`)
  - [ ] HTML-formatted email body with threat details
  - [ ] Toggle via `ENABLE_EMAIL_ALERTS`
  - [ ] Timeout and error handling for SMTP failures

- [ ] **4.3 Implement Telegram alerts**
  - [ ] Send formatted message via Telegram Bot API
  - [ ] Use `requests.post` to `api.telegram.org`
  - [ ] Include threat type, SSID, BSSID, vendor, severity
  - [ ] Toggle via `ENABLE_TELEGRAM_ALERTS`
  - [ ] Error handling for API failures

- [ ] **4.4 Implement webhook alerts**
  - [ ] POST JSON payload to `WEBHOOK_URL`
  - [ ] Include full threat metadata in payload
  - [ ] Toggle via `ENABLE_WEBHOOK_ALERTS`
  - [ ] Configurable timeout and retry

- [ ] **4.5 Implement GPIO buzzer alerts**
  - [ ] Pulse GPIO pin (`GPIO_BUZZER_PIN`) on threat detection
  - [ ] Configurable pulse duration based on severity
  - [ ] Toggle via `ENABLE_GPIO_BUZZER`
  - [ ] Graceful skip when GPIO unavailable (dev machine)

- [ ] **4.6 Implement SIEM Syslog forwarding**
  - [ ] Create `src/siem.py`
  - [ ] Format threat data as CEF (Common Event Format) messages
  - [ ] Send via UDP or TCP (`SIEM_PROTOCOL`)
  - [ ] Configurable host and port (`SIEM_HOST`, `SIEM_PORT`)
  - [ ] Toggle via `ENABLE_SIEM`
  - [ ] Error handling for network failures

- [ ] **4.7 Write Phase 4 tests**
  - [ ] Test alert dispatcher routing (enabled/disabled channels)
  - [ ] Test alert rate limiting
  - [ ] Test email sending (mocked SMTP)
  - [ ] Test Telegram API call (mocked requests)
  - [ ] Test webhook POST (mocked requests)
  - [ ] Test GPIO buzzer (mocked RPi.GPIO)
  - [ ] Test Syslog forwarding (mocked socket)

---

## Phase 5 — GPS, Portable Mode & Polish

- [ ] **5.1 Implement GPS handler**
  - [ ] Create `src/gps_handler.py`
  - [ ] Connect to gpsd daemon via `gpsd-py3`
  - [ ] Implement `get_position() -> (lat, lon, alt)` function
  - [ ] Handle no-fix and disconnection gracefully
  - [ ] Toggle via `ENABLE_GPS`
  - [ ] Configurable `GPS_HOST` and `GPS_PORT`

- [ ] **5.2 Integrate GPS into scan pipeline**
  - [ ] Tag `scan_events` with GPS coordinates
  - [ ] Tag `threats` with GPS coordinates
  - [ ] Tag `access_points` with first-seen GPS coordinates
  - [ ] Include GPS data in alert messages

- [ ] **5.3 Implement portable mode**
  - [ ] Reduce scan frequency for battery conservation
  - [ ] Disable web dashboard in portable mode
  - [ ] File-based logging for headless operation
  - [ ] Status LED blink patterns (scanning, threat detected, idle)
  - [ ] Toggle via `ENABLE_PORTABLE_MODE`

- [ ] **5.4 Add GPS display to dashboard**
  - [ ] Show GPS coordinates in AP detail view
  - [ ] Show GPS coordinates in threat detail view
  - [ ] GPS status indicator in dashboard header
  - [ ] Placeholder for future map integration

- [ ] **5.5 Write Phase 5 tests**
  - [ ] Test GPS handler (connection, read position, no fix, disconnect)
  - [ ] Test GPS integration in scan events and threats
  - [ ] Test portable mode configuration (reduced frequency, dashboard disabled)
  - [ ] Test LED status patterns (mocked GPIO)

---

## Phase 6 — Deployment & Documentation

- [ ] **6.1 Create deploy script**
  - [ ] Create `deploy/deploy_to_pi.sh`
  - [ ] rsync project to `rasp-pi` (pi@192.168.216.90)
  - [ ] Exclude `.venv`, `__pycache__`, `.git`, `data/`
  - [ ] Remote `pip install -r requirements.txt`
  - [ ] Print restart instructions

- [ ] **6.2 Create monitor-mode setup script**
  - [ ] Create `scripts/setup_monitor_mode.sh`
  - [ ] Accept interface name as argument
  - [ ] Kill interfering processes (`airmon-ng check kill`)
  - [ ] Enable monitor mode (`airmon-ng start <iface>`)
  - [ ] Verify monitor mode is active

- [ ] **6.3 Create OS dependency installer**
  - [ ] Create `scripts/install_deps.sh`
  - [ ] Install `aircrack-ng`, `gpsd`, `gpsd-clients`, `python3-venv`, `python3-dev`
  - [ ] Handle apt update and error cases
  - [ ] Print success/failure summary

- [ ] **6.4 Write systemd service unit**
  - [ ] Create service file for `rogue-ap-detector`
  - [ ] Configure `After=network-online.target gpsd.service`
  - [ ] Configure `ExecStartPre` for monitor mode
  - [ ] Configure restart on failure with 10s delay
  - [ ] Document enable/start commands in README

- [ ] **6.5 Write threat model document**
  - [ ] Create `docs/threat_model.md`
  - [ ] Document all threat vectors and mitigations
  - [ ] Include data flow diagram
  - [ ] Include trust boundary analysis
  - [ ] Security recommendations for deployment

- [ ] **6.6 Final integration testing**
  - [ ] Test full scan cycle on real Pi hardware
  - [ ] Test Evil Twin detection with controlled rogue AP
  - [ ] Test deauth detection with `aireplay-ng` (controlled environment)
  - [ ] Test all alert channels end-to-end
  - [ ] Test dashboard under load (multiple concurrent clients)
  - [ ] Test systemd service lifecycle (start, stop, restart, crash recovery)

- [ ] **6.7 Finalize documentation**
  - [ ] Update README with final usage instructions
  - [ ] Verify all `.env` variables documented
  - [ ] Update TSD with any changes from implementation
  - [ ] Update task.md with completion status
  - [ ] Review and update troubleshooting table
