# Implementation Plan — Rogue Access Point Detector

## Phase 1 — Project Foundation & Scanning Engine

**Goal:** Scaffold the project, configure environment loading, set up the database, and build the core scanning engine with OUI lookup and mock mode.

- [ ] **Step 1.1 — Initialize Project Structure**
  - [ ] Create directory tree:
    ```
    src/, templates/, static/css/, static/js/, tests/, deploy/, scripts/, docs/, data/
    ```
  - [ ] Create `pyproject.toml` with project name, version, Python ≥3.11, and entry point `src.app`
  - [ ] Create `requirements.txt`:
    ```
    flask
    flask-socketio
    eventlet
    scapy
    manuf
    gpsd-py3
    bcrypt
    python-dotenv
    requests
    gunicorn
    pytest
    pytest-cov
    ```
  - [ ] Create `.env.example` with all variables and documented defaults (see TSD §8)
  - [ ] Create `src/__init__.py` (empty)
  - [ ] Create `tests/__init__.py` (empty) and `tests/conftest.py` with shared fixtures

- [ ] **Step 1.2 — Configuration Loader**
  - [ ] Create `src/config.py`
  - [ ] Define `@dataclass class Config` with all `.env` fields and proper types
  - [ ] Implement `load_config()` — reads `.env` via `dotenv_values()`, applies defaults
  - [ ] Convert string values to `int`, `float`, `bool` as needed
  - [ ] Add `is_enabled(feature: str) -> bool` helper for toggle checks
  - [ ] Write `tests/test_config.py` — test loading, defaults, type conversion, missing keys

- [ ] **Step 1.3 — SQLite Database Module**
  - [ ] Create `src/database.py`
  - [ ] Implement `get_connection(db_path)` with WAL mode pragma
  - [ ] Implement `init_db(conn)` — creates all 5 tables (see TSD §3)
  - [ ] Implement CRUD functions:
    - `upsert_access_point(conn, ap_data)`
    - `insert_scan_event(conn, event_data)`
    - `insert_threat(conn, threat_data)`
    - `get_baseline_aps(conn)`
    - `add_baseline_ap(conn, ap_data)`
    - `remove_baseline_ap(conn, bssid)`
    - `get_setting(conn, key)` / `set_setting(conn, key, value)`
  - [ ] Use parameterized queries for all DB operations
  - [ ] Write `tests/test_database.py` — test schema creation, all CRUD ops, WAL mode

- [ ] **Step 1.4 — Scanning Engine**
  - [ ] Create `src/scanner.py`
  - [ ] Implement `ChannelHopper` class:
    - Background thread that iterates 2.4 GHz (1–14) and/or 5 GHz (36–165) channels
    - Uses `os.system(f"iwconfig {iface} channel {ch}")` for channel switching
    - Configurable dwell time (`CHANNEL_HOP_INTERVAL`)
    - Band selection via `SCAN_BANDS`
  - [ ] Implement `Scanner` class:
    - `start()` — begins scapy sniff on monitor interface + starts channel hopper
    - `_packet_handler(pkt)` — processes Dot11Beacon and Dot11ProbeResp frames
    - Extract: SSID, BSSID, channel, signal (dBm), encryption type
    - Accumulate APs in scan cycle buffer
    - `_on_scan_cycle()` — persist APs, create scan event, emit results via callback
  - [ ] Configurable scan interval (`SCAN_INTERVAL`)
  - [ ] Write `tests/test_scanner.py` — test frame parsing, AP extraction, channel list generation

- [ ] **Step 1.5 — OUI Vendor Lookup**
  - [ ] Create `src/oui_lookup.py`
  - [ ] Initialize `manuf.MacParser()` (lazy singleton)
  - [ ] Implement `lookup_vendor(bssid: str) -> str` — returns vendor name or "Unknown"
  - [ ] Add in-memory LRU cache (`functools.lru_cache`) for repeated lookups
  - [ ] Integrate into scanner pipeline: resolve vendor for each discovered AP
  - [ ] Toggle via `ENABLE_OUI_LOOKUP` (return "N/A" when disabled)
  - [ ] Write `tests/test_oui.py` — test known MAC prefix, unknown MAC, disabled mode

- [ ] **Step 1.6 — Mock Mode**
  - [ ] Add `MockScanner` class to `src/scanner.py`
  - [ ] Generate 8–15 fake APs with realistic data (random SSIDs, valid BSSIDs, varied channels/signals)
  - [ ] Vary AP list slightly each cycle (signal fluctuation, occasional new/disappearing AP)
  - [ ] Simulate evil twin scenario every ~10 cycles
  - [ ] Simulate deauth burst every ~15 cycles
  - [ ] Activate via `MOCK_MODE=true` in config
  - [ ] Write `tests/test_mock.py` — test mock data generation, variability, simulated threats

**Checkpoint:** Scanner discovers APs (real or mock), resolves vendors, persists to DB. Config and DB modules fully tested.

---

## Phase 2 — Detection Engine & Baseline

**Goal:** Implement baseline AP management and all threat detection algorithms.

- [ ] **Step 2.1 — Baseline AP Learning**
  - [ ] Create `src/baseline.py`
  - [ ] Implement `learn_baseline(conn, aps: list)`:
    - Clear existing baseline entries
    - Insert all current APs into `baseline_aps` table
    - Log count of APs learned
  - [ ] Implement `--learn-baseline` CLI argument in `src/app.py`
  - [ ] On first run with empty baseline, prompt or auto-learn
  - [ ] Toggle via `ENABLE_BASELINE_LEARNING`

- [ ] **Step 2.2 — Baseline Comparison**
  - [ ] Implement `compare_to_baseline(conn, current_aps: list) -> list[Threat]`:
    - Load baseline from DB
    - For each current AP, check if BSSID exists in baseline
    - If BSSID not found → `NEW_AP` threat (severity MEDIUM)
    - If BSSID found but encryption changed → threat (severity HIGH)
    - If BSSID found but channel changed → threat (severity LOW)
  - [ ] Implement `BASELINE_AUTO_LEARN` — silently add new APs to baseline
  - [ ] Return list of threat objects for dispatcher

- [ ] **Step 2.3 — Evil Twin Detection**
  - [ ] Create `src/detector.py` with `DetectionEngine` class
  - [ ] Implement `detect_evil_twins(current_aps, baseline_aps) -> list[Threat]`:
    - Group current APs by SSID
    - For each SSID that matches a baseline entry, check all BSSIDs
    - Flag any BSSID not in baseline with matching SSID as `EVIL_TWIN`
    - Check encryption mismatch (e.g., WPA2 baseline vs OPEN twin)
    - Severity: `HIGH`
    - Include both legitimate and suspect AP details in threat

- [ ] **Step 2.4 — Deauth Flood Detection**
  - [ ] Implement `DeauthMonitor` in `src/detector.py`:
    - Register scapy callback for Dot11Deauth (subtype 0x0c) and Dot11Disas (subtype 0x0a)
    - Maintain sliding window counter per source MAC
    - When count/sec > `DEAUTH_THRESHOLD` → `DEAUTH_FLOOD` threat
    - Record attacker MAC, target BSSID
    - Severity: `CRITICAL`
    - Resolve attacker vendor via OUI lookup

- [ ] **Step 2.5 — Rogue AP Detection**
  - [ ] Implement `detect_rogue_aps(current_aps, baseline_aps) -> list[Threat]`:
    - Any AP with BSSID not in baseline and SSID not matching any baseline → `ROGUE_AP`
    - Severity: `MEDIUM`
    - Cooldown: suppress repeated alerts for same BSSID within 5-minute window
  - [ ] Differentiate from evil twin (rogue = unknown SSID, evil twin = known SSID + different BSSID)

- [ ] **Step 2.6 — Threat Database Integration**
  - [ ] After each detection pass, persist all new threats via `insert_threat()`
  - [ ] Set `alert_sent=0` initially; update after alert dispatch
  - [ ] Include JSON `details` blob with full detection context
  - [ ] Deduplicate: skip if identical threat (type + BSSID) exists within cooldown window

- [ ] **Step 2.7 — Phase 2 Tests**
  - [ ] `tests/test_baseline.py` — learn, compare (new, changed encryption, changed channel, auto-learn)
  - [ ] `tests/test_detector.py` — evil twin (exact match, encryption mismatch, multiple twins)
  - [ ] `tests/test_detector.py` — deauth detection (below/at/above threshold)
  - [ ] `tests/test_detector.py` — rogue AP (unknown BSSID, cooldown suppression)
  - [ ] `tests/test_database.py` — threat insertion, deduplication

**Checkpoint:** Detection engine identifies evil twins, deauth floods, and rogue APs. All threats persisted. Baseline management functional.

---

## Phase 3 — Web Dashboard & Authentication

**Goal:** Build the authenticated dark-themed web dashboard with real-time updates.

- [ ] **Step 3.1 — Flask App Factory**
  - [ ] Create `src/app.py`:
    - `create_app(config)` factory pattern
    - Initialize Flask-SocketIO with eventlet mode
    - Register route handlers
    - Initialize database on startup
    - Start scanner in background thread
    - Implement `__main__` block to run the app
  - [ ] Toggle dashboard via `ENABLE_WEB_DASHBOARD`

- [ ] **Step 3.2 — Authentication Module**
  - [ ] Create `src/auth.py`:
    - `verify_password(plaintext, bcrypt_hash) -> bool`
    - `login_user(session, username)` — set session data with expiry timestamp
    - `logout_user(session)` — clear session
    - `is_authenticated(session) -> bool` — check session validity and expiry
    - `login_required(f)` — decorator redirecting to `/login`
  - [ ] Route `GET /login` — render login form
  - [ ] Route `POST /login` — verify credentials, rate limit check, set session
  - [ ] Route `POST /logout` — clear session, redirect to login
  - [ ] Rate limiter: store attempt counts per IP in memory dict with 15-min window
  - [ ] Session expiry: check `SESSION_EXPIRY_HOURS` (default 24h) on each request

- [ ] **Step 3.3 — Dark Theme Templates & CSS**
  - [ ] Create `templates/base.html`:
    - HTML5 boilerplate with dark background (`#1a1a2e`)
    - Navigation bar (app title, status indicator, logout)
    - Content block, script block
    - SocketIO client script, Chart.js CDN
  - [ ] Create `static/css/style.css`:
    - Dark palette: background `#1a1a2e`, cards `#16213e`, text `#e0e0e0`, accent `#0f3460`
    - Severity badges: CRITICAL (red), HIGH (orange), MEDIUM (yellow), LOW (blue)
    - Table styling, responsive grid, form inputs

- [ ] **Step 3.4 — Login Page**
  - [ ] Create `templates/login.html` extending base
  - [ ] Centered login card with username/password fields
  - [ ] CSRF token hidden field
  - [ ] Flash message area for errors ("Invalid credentials", "Rate limited")

- [ ] **Step 3.5 — Dashboard Page**
  - [ ] Create `templates/dashboard.html` extending base
  - [ ] Summary cards row: Total APs, Baseline APs, Active Threats, Scans Today
  - [ ] AP table: SSID, BSSID, Channel, Signal, Encryption, Vendor, Status, Last Seen
  - [ ] Threat feed panel: scrollable list with severity badge, type, SSID, BSSID, timestamp
  - [ ] Chart containers for signal and channel graphs
  - [ ] Scan status bar (running/stopped, last scan timestamp)

- [ ] **Step 3.6 — SocketIO Real-time Events**
  - [ ] Server emits: `ap_update` (full AP list), `threat_alert` (new threat), `scan_status`
  - [ ] Create `static/js/dashboard.js`:
    - Connect to SocketIO namespace
    - Handle `ap_update` — rebuild AP table rows
    - Handle `threat_alert` — prepend to threat feed, flash severity color
    - Handle `scan_status` — update status bar

- [ ] **Step 3.7 — Chart.js Graphs**
  - [ ] Create `static/js/charts.js`:
    - `initSignalChart(canvasId)` — line chart, top 10 APs by signal over time
    - `initChannelChart(canvasId)` — bar chart, AP count per channel
    - `updateSignalChart(data)` / `updateChannelChart(data)` — refresh from SocketIO
    - Dark theme chart options (grid lines, font colors)

- [ ] **Step 3.8 — Settings Panel**
  - [ ] Create `templates/settings.html` extending base
  - [ ] Route `GET /settings` — render settings page
  - [ ] Baseline AP table: list all baseline APs with approve/reject buttons
  - [ ] Route `POST /settings/baseline/add` — add AP to baseline
  - [ ] Route `POST /settings/baseline/remove` — remove AP from baseline
  - [ ] Route `POST /settings/baseline/learn` — trigger baseline re-learn
  - [ ] Display current `.env` feature toggles (read-only)

- [ ] **Step 3.9 — Phase 3 Tests**
  - [ ] `tests/test_auth.py` — login, logout, invalid creds, rate limiting, session expiry
  - [ ] `tests/test_api.py` — dashboard route (auth required), settings routes, SocketIO events
  - [ ] Test CSRF protection on forms

**Checkpoint:** Fully functional dark-themed dashboard with live AP table, threat feed, charts, auth, and settings. All protected by bcrypt auth with rate limiting.

---

## Phase 4 — Alert Channels & SIEM

**Goal:** Implement all alert dispatch channels and Syslog-based SIEM integration.

- [ ] **Step 4.1 — Alert Dispatcher Core**
  - [ ] Create `src/alerts.py` with `AlertDispatcher` class
  - [ ] Constructor: accept config, initialize enabled channels
  - [ ] `dispatch(threat)` method:
    - Check `ENABLE_ALERTS` master toggle
    - Check per-threat rate limit (same type+BSSID within 5-minute cooldown)
    - Format alert message (type, severity, SSID, BSSID, vendor, time, GPS)
    - Iterate enabled channels, send in try/except per channel
    - Update `alert_sent=1` in DB on success

- [ ] **Step 4.2 — Email Alert Channel**
  - [ ] Implement `_send_email(subject, body)`:
    - Connect to `SMTP_HOST:SMTP_PORT` with TLS (STARTTLS)
    - Authenticate with `SMTP_USER` / `SMTP_PASS`
    - Send to `ALERT_EMAIL_TO`
    - HTML body with threat summary table
  - [ ] Timeout: 10 seconds; log error on failure
  - [ ] Toggle via `ENABLE_EMAIL_ALERTS`

- [ ] **Step 4.3 — Telegram Alert Channel**
  - [ ] Implement `_send_telegram(message)`:
    - POST to `https://api.telegram.org/bot{token}/sendMessage`
    - Payload: `chat_id`, `text` (Markdown formatted), `parse_mode=Markdown`
  - [ ] Timeout: 10 seconds; log error on failure
  - [ ] Toggle via `ENABLE_TELEGRAM_ALERTS`

- [ ] **Step 4.4 — Webhook Alert Channel**
  - [ ] Implement `_send_webhook(threat_data)`:
    - POST JSON to `WEBHOOK_URL`
    - Include full threat metadata as JSON body
    - Set `Content-Type: application/json`
  - [ ] Timeout: 10 seconds; log error on failure
  - [ ] Toggle via `ENABLE_WEBHOOK_ALERTS`

- [ ] **Step 4.5 — GPIO Buzzer Alert Channel**
  - [ ] Implement `_trigger_buzzer(severity)`:
    - Import `RPi.GPIO` (skip gracefully on non-Pi)
    - Set `GPIO_BUZZER_PIN` as output
    - Pulse pattern: CRITICAL = 3 long, HIGH = 2 short, MEDIUM = 1 short
    - Clean up GPIO after pulse
  - [ ] Toggle via `ENABLE_GPIO_BUZZER`

- [ ] **Step 4.6 — SIEM Syslog Forwarder**
  - [ ] Create `src/siem.py` with `SyslogForwarder` class
  - [ ] Implement `forward(threat)`:
    - Format as CEF: `CEF:0|RogueAPDetector|Scanner|1.0|{type}|{severity}|...`
    - Send via UDP or TCP socket to `SIEM_HOST:SIEM_PORT`
  - [ ] Implement socket connection management (reconnect on TCP failure)
  - [ ] Toggle via `ENABLE_SIEM`

- [ ] **Step 4.7 — Phase 4 Tests**
  - [ ] `tests/test_alerts.py`:
    - Test dispatcher routing (all channels enabled, some disabled, master off)
    - Test alert rate limiting (cooldown suppression)
    - Test email sending (mock `smtplib.SMTP`)
    - Test Telegram API call (mock `requests.post`)
    - Test webhook POST (mock `requests.post`)
    - Test GPIO buzzer (mock `RPi.GPIO`)
    - Test Syslog forwarding (mock `socket.socket`)

**Checkpoint:** All alert channels functional with rate limiting. SIEM integration sends CEF-formatted Syslog messages. All channels tested with mocks.

---

## Phase 5 — GPS, Portable Mode & Polish

**Goal:** Add GPS tagging, implement portable/battery mode, and polish the system.

- [ ] **Step 5.1 — GPS Handler**
  - [ ] Create `src/gps_handler.py`
  - [ ] Implement `GPSHandler` class:
    - `connect()` — connect to gpsd at `GPS_HOST:GPS_PORT`
    - `get_position() -> dict` — return `{lat, lon, alt, speed, time}` or `None`
    - `is_connected() -> bool` — check gpsd connection status
    - `has_fix() -> bool` — check satellite fix status
  - [ ] Graceful handling: return `None` when no fix, disconnected, or GPS disabled
  - [ ] Toggle via `ENABLE_GPS`

- [ ] **Step 5.2 — GPS Integration**
  - [ ] In scanner: call `gps_handler.get_position()` at start of each scan cycle
  - [ ] Store GPS in `scan_events` record
  - [ ] Store GPS in `threats` record when threat detected
  - [ ] Store GPS in `access_points` `first_seen` location
  - [ ] Include GPS in alert messages when available

- [ ] **Step 5.3 — Portable Mode**
  - [ ] When `ENABLE_PORTABLE_MODE=true`:
    - Triple `SCAN_INTERVAL` to conserve battery
    - Disable web dashboard (set `ENABLE_WEB_DASHBOARD=false` internally)
    - Enable file logging to `data/portable_scan.log`
    - Reduce log verbosity to WARNING
  - [ ] Implement LED status via GPIO (if available):
    - Slow blink: scanning
    - Fast blink: threat detected
    - Solid: idle/error
  - [ ] Log summary statistics periodically (APs found, threats detected)

- [ ] **Step 5.4 — Dashboard GPS Display**
  - [ ] Add GPS coordinates column to AP detail view (expandable row)
  - [ ] Add GPS coordinates to threat detail view
  - [ ] Add GPS status indicator in dashboard header (fix/no-fix/disabled)
  - [ ] Display "No GPS data" gracefully when GPS disabled or no fix

- [ ] **Step 5.5 — Phase 5 Tests**
  - [ ] `tests/test_gps.py`:
    - Test GPS connection (mock gpsd)
    - Test position reading (valid fix, no fix)
    - Test disconnection handling
    - Test disabled mode (returns None)
  - [ ] Test GPS data in scan events and threats
  - [ ] Test portable mode configuration changes
  - [ ] Test LED patterns (mock GPIO)

**Checkpoint:** GPS tagging functional. Portable mode optimized for battery. Dashboard displays location data.

---

## Phase 6 — Deployment & Documentation

**Goal:** Finalize deployment pipeline, systemd integration, and all project documentation.

- [ ] **Step 6.1 — Deploy Script**
  - [ ] Create `deploy/deploy_to_pi.sh`:
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    PI_HOST="rasp-pi"
    REMOTE_DIR="/home/pi/rogue-ap-detector"
    rsync -avz --exclude '.venv' --exclude '__pycache__' \
        --exclude '*.pyc' --exclude '.git' --exclude 'data/' \
        ./ "${PI_HOST}:${REMOTE_DIR}/"
    ssh "${PI_HOST}" "cd ${REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt"
    echo "[✓] Deploy complete. Restart: sudo systemctl restart rogue-ap-detector"
    ```
  - [ ] Make executable (`chmod +x`)

- [ ] **Step 6.2 — Monitor Mode Script**
  - [ ] Create `scripts/setup_monitor_mode.sh`:
    - Accept interface name as `$1` (default `wlan1`)
    - Run `airmon-ng check kill` to stop interfering processes
    - Run `airmon-ng start $1` to enable monitor mode
    - Verify with `iwconfig` that `${1}mon` exists
    - Print success/failure message

- [ ] **Step 6.3 — OS Dependency Installer**
  - [ ] Create `scripts/install_deps.sh`:
    - `sudo apt update`
    - `sudo apt install -y aircrack-ng gpsd gpsd-clients python3-venv python3-dev`
    - Verify installations
    - Print summary

- [ ] **Step 6.4 — systemd Service**
  - [ ] Create service unit (documented in README):
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
  - [ ] Commands: `daemon-reload`, `enable`, `start`, `journalctl -f`

- [ ] **Step 6.5 — Threat Model Document**
  - [ ] Create `docs/threat_model.md`:
    - Trust boundaries (LAN, Pi, USB adapter, external services)
    - Data flow diagram (scan → detect → alert → dashboard)
    - Threat vectors table (brute force, CSRF, injection, physical theft, etc.)
    - Mitigation strategies for each threat
    - Security recommendations for deployment

- [ ] **Step 6.6 — Integration Testing on Hardware**
  - [ ] Test full scan cycle on Raspberry Pi with real USB adapter
  - [ ] Test Evil Twin detection with a controlled rogue AP (phone hotspot with same SSID)
  - [ ] Test deauth detection with `aireplay-ng` in controlled lab
  - [ ] Test email, Telegram, webhook alerts end-to-end
  - [ ] Test GPIO buzzer with physical hardware
  - [ ] Test GPS with real USB dongle
  - [ ] Test systemd service (start, stop, restart, crash recovery)
  - [ ] Test dashboard under 3+ concurrent browser sessions

- [ ] **Step 6.7 — Documentation Finalization**
  - [ ] Review and update `README.md` with any implementation changes
  - [ ] Verify all `.env` variables match actual code usage
  - [ ] Update `TSD.md` with final architecture and any schema changes
  - [ ] Mark completed tasks in `task.md`
  - [ ] Ensure troubleshooting table covers all known issues

**Checkpoint:** Project fully deployed on Pi, running as systemd service, all documentation complete and accurate. All tests passing.
