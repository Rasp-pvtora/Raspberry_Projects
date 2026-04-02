# Technical Specification Document — Rogue Access Point Detector

## 1. Scope

### In Scope

- Continuous 802.11 passive scanning on monitor-mode USB WiFi adapter
- 2.4 GHz and 5 GHz channel rotation with configurable dwell time
- Baseline AP learning, storage, and comparison
- Evil Twin detection (same SSID, different BSSID/encryption)
- Deauthentication/disassociation flood detection with configurable threshold
- MAC vendor lookup via offline OUI database
- GPS tagging for war-driving (optional USB GPS)
- Multi-channel alerts: email (SMTP), Telegram bot, generic webhook, GPIO buzzer
- SIEM integration via Syslog forwarding (UDP/TCP)
- Portable/battery mode for Pi Zero 2W
- Dark-themed Flask + SocketIO web dashboard with auth
- bcrypt authentication with rate limiting and session expiry
- Mock mode for development/testing without hardware
- All features toggled via `.env`
- SQLite for persistence
- Deployment via rsync to `rasp-pi` (192.168.216.90)

### Out of Scope

- Active wireless attacks (injection, jamming, deauth sending)
- WPA/WPA2 handshake capture or cracking
- Client device fingerprinting beyond probe requests
- Enterprise RADIUS/802.1X integration
- Cloud-hosted dashboard or multi-tenant support
- Automatic remediation (blocking rogue APs)
- Non-Linux operating systems
- Commercial licensing or paid features

---

## 2. MVP Features (P0)

| ID | Feature | Priority |
|----|---------|----------|
| P0-1 | Scanning engine (scapy, channel hopping, 2.4/5 GHz) | P0 |
| P0-2 | Evil Twin detection (SSID match, BSSID/encryption mismatch) | P0 |
| P0-3 | Deauthentication flood detection (frame rate threshold) | P0 |
| P0-4 | Baseline AP learning (first-run learn, persist, compare) | P0 |
| P0-5 | Web dashboard (dark theme, live AP table, threat feed) | P0 |
| P0-6 | Authentication (bcrypt, rate limiting 10/15min, 24h session) | P0 |
| P0-7 | Mock mode (simulated scan data for dev/testing) | P0 |
| P0-8 | Deploy script (rsync to rasp-pi, systemd service) | P0 |
| P0-9 | OUI vendor lookup (offline manuf database) | P0 |
| P0-10 | SQLite database (schema, migrations, WAL mode) | P0 |

### Nice-to-Have (P1/P2)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| P1-1 | GPS tagging | P1 | Requires USB GPS dongle + gpsd |
| P1-2 | Email alerts | P1 | Requires SMTP server credentials |
| P1-3 | Telegram alerts | P1 | Requires bot token + chat ID |
| P1-4 | Webhook alerts | P1 | Requires external receiver endpoint |
| P1-5 | GPIO buzzer alerts | P1 | Requires physical buzzer on GPIO pin |
| P1-6 | SIEM/Syslog forwarding | P1 | Requires Wazuh/Splunk receiver |
| P2-1 | Portable mode (Pi Zero 2W) | P2 | Battery optimization, headless |
| P2-2 | Chart.js signal/channel graphs | P2 | Dashboard enhancement |
| P2-3 | Settings panel (runtime toggles) | P2 | Dashboard enhancement |

---

## 3. Database Schema

SQLite with WAL mode enabled. All timestamps stored as ISO-8601 UTC.

### Table: `access_points`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique AP record ID |
| bssid | TEXT | NOT NULL, INDEX | MAC address of the AP |
| ssid | TEXT | | Network name (may be empty for hidden) |
| channel | INTEGER | | Current operating channel |
| frequency | INTEGER | | Frequency in MHz |
| signal_strength | INTEGER | | RSSI in dBm |
| encryption | TEXT | | Security type (OPEN, WEP, WPA, WPA2, WPA3) |
| vendor | TEXT | | OUI-resolved manufacturer |
| first_seen | TEXT | NOT NULL | ISO-8601 timestamp of first detection |
| last_seen | TEXT | NOT NULL | ISO-8601 timestamp of most recent detection |
| latitude | REAL | | GPS latitude (NULL if GPS disabled) |
| longitude | REAL | | GPS longitude (NULL if GPS disabled) |
| is_baseline | INTEGER | DEFAULT 0 | 1 if part of approved baseline |

### Table: `scan_events`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique scan event ID |
| timestamp | TEXT | NOT NULL | ISO-8601 scan start time |
| duration_ms | INTEGER | | Scan cycle duration |
| aps_found | INTEGER | | Number of APs discovered |
| channels_scanned | TEXT | | JSON array of channels scanned |
| latitude | REAL | | GPS latitude at scan time |
| longitude | REAL | | GPS longitude at scan time |
| band | TEXT | | Scanned band (2.4, 5, both) |

### Table: `threats`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique threat ID |
| timestamp | TEXT | NOT NULL | ISO-8601 detection time |
| threat_type | TEXT | NOT NULL | EVIL_TWIN, DEAUTH_FLOOD, ROGUE_AP, NEW_AP |
| severity | TEXT | NOT NULL | LOW, MEDIUM, HIGH, CRITICAL |
| ssid | TEXT | | Involved SSID |
| bssid | TEXT | | Involved BSSID |
| details | TEXT | | JSON blob with extended info |
| vendor | TEXT | | OUI vendor of involved MAC |
| latitude | REAL | | GPS latitude |
| longitude | REAL | | GPS longitude |
| acknowledged | INTEGER | DEFAULT 0 | 1 if operator has acknowledged |
| alert_sent | INTEGER | DEFAULT 0 | 1 if alert dispatched |

### Table: `baseline_aps`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique baseline entry ID |
| bssid | TEXT | NOT NULL, UNIQUE | Approved AP MAC address |
| ssid | TEXT | | Approved SSID |
| channel | INTEGER | | Approved channel |
| encryption | TEXT | | Approved encryption type |
| vendor | TEXT | | OUI vendor |
| added_at | TEXT | NOT NULL | ISO-8601 when added to baseline |
| added_by | TEXT | DEFAULT 'auto' | 'auto' or 'manual' |

### Table: `settings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | TEXT | PK | Setting name |
| value | TEXT | | Setting value (JSON-encoded) |
| updated_at | TEXT | NOT NULL | ISO-8601 last update time |

---

## 4. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Raspberry Pi                                 │
│                                                                     │
│  ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐  │
│  │ USB WiFi    │────>│  Scanner Engine   │────>│  Detection      │  │
│  │ Adapter     │     │  (scapy)         │     │  Engine         │  │
│  │ (wlan1mon)  │     │  - Channel hop   │     │  - Evil Twin    │  │
│  └─────────────┘     │  - Frame capture │     │  - Deauth Flood │  │
│                      │  - AP extraction │     │  - Rogue AP     │  │
│  ┌─────────────┐     └────────┬─────────┘     └────────┬────────┘  │
│  │ USB GPS     │──┐           │                        │           │
│  │ (optional)  │  │     ┌─────▼──────┐          ┌──────▼────────┐  │
│  └─────────────┘  │     │ Baseline   │          │ Alert         │  │
│                   └────>│ Manager    │          │ Dispatcher    │  │
│                         │            │          │ ┌───────────┐ │  │
│                         └─────┬──────┘          │ │ Email     │ │  │
│                               │                 │ │ Telegram  │ │  │
│  ┌────────────────────────────▼──────────────┐  │ │ Webhook   │ │  │
│  │            SQLite Database                │  │ │ GPIO      │ │  │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ │  │ └───────────┘ │  │
│  │  │access_   │ │scan_      │ │threats   │ │  └───────────────┘  │
│  │  │points    │ │events     │ │          │ │          │           │
│  │  └──────────┘ └───────────┘ └──────────┘ │          │           │
│  │  ┌──────────┐ ┌───────────┐              │  ┌───────▼────────┐  │
│  │  │baseline_ │ │settings   │              │  │ SIEM / Syslog  │  │
│  │  │aps       │ │           │              │  │ Forwarder      │  │
│  │  └──────────┘ └───────────┘              │  └───────┬────────┘  │
│  └───────────────────────────────────────────┘         │           │
│                         │                              │           │
│  ┌──────────────────────▼────────────────────┐         │           │
│  │  Flask + SocketIO Web Dashboard           │         ▼           │
│  │  - bcrypt auth (rate limit 10/15min)      │   Wazuh / Splunk   │
│  │  - 24h session expiry                     │                     │
│  │  - Dark theme, Chart.js graphs            │                     │
│  │  - Real-time AP table & threat feed       │                     │
│  └───────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Threat Model

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| Brute-force login to dashboard | Unauthorized access to controls | Medium | bcrypt hashing, rate limiting (10/15min), session expiry (24h) |
| Session hijacking (cookie theft) | Impersonate admin | Low | Secure cookie flags, `SECRET_KEY` rotation, session expiry |
| CSRF on dashboard actions | Unauthorized baseline changes | Medium | CSRF tokens on all forms, SameSite cookie attribute |
| SQLite injection via dashboard input | Data corruption/exfiltration | Low | Parameterized queries, input validation |
| Denial of service on dashboard | Dashboard unavailable | Low | Rate limiting, bind to LAN only |
| Malicious .env modification | Feature disabling, credential theft | Medium | File permissions (600), deploy via rsync only |
| Monitor-mode interface hijack | Attacker controls scanner NIC | Low | Root-only access, systemd hardening |
| Syslog injection | SIEM pollution | Low | Structured CEF format, input sanitization |
| GPS spoofing | Incorrect location data | Low | Cross-reference with known AP positions |
| Physical device theft | Data exposure, credential leak | Medium | Disk encryption, strong admin password |
| OUI database tampering | Incorrect vendor resolution | Low | Read-only OUI file, integrity checks |

---

## 6. Tech Stack

| Layer | Technology | Version / Notes |
|-------|-----------|-----------------|
| Language | Python 3.11+ | Type hints throughout |
| Web framework | Flask | 3.x with app factory pattern |
| Real-time | Flask-SocketIO | eventlet async mode |
| Packet capture | scapy | 802.11 frame parsing |
| OUI lookup | manuf | Offline MAC vendor DB |
| GPS | gpsd-py3 | Client for gpsd daemon |
| Auth | bcrypt | Password hashing |
| Config | python-dotenv | `.env` loader |
| HTTP client | requests | Telegram, webhook alerts |
| Database | SQLite3 | WAL mode, stdlib `sqlite3` |
| Charts | Chart.js 4.x | CDN or vendored |
| CSS | Custom dark theme | No framework |
| OS tooling | aircrack-ng | Monitor mode management |
| Deployment | rsync + systemd | SSH alias `rasp-pi` |
| Testing | pytest + pytest-cov | Mocking with unittest.mock |

---

## 7. Development Phases

### Phase 1 — Project Foundation & Scanning Engine

**Goal:** Scaffold the project, set up configuration loading, database, and the core scanning engine.

| # | Task | Deliverable |
|---|------|-------------|
| 1.1 | Initialize project structure (dirs, `pyproject.toml`, `requirements.txt`) | Repo skeleton |
| 1.2 | Implement `.env` config loader with dataclass validation | `src/config.py` |
| 1.3 | Implement SQLite database module with schema creation (WAL mode) | `src/database.py` |
| 1.4 | Implement scanning engine (scapy, channel hopping, AP extraction) | `src/scanner.py` |
| 1.5 | Implement OUI vendor lookup integration | `src/oui_lookup.py` |
| 1.6 | Implement mock mode scanner (simulated AP data) | Mock path in `src/scanner.py` |
| 1.7 | Write unit tests for scanner, config, database, OUI lookup | `tests/` |

### Phase 2 — Detection Engine & Baseline

**Goal:** Implement all detection algorithms and baseline AP management.

| # | Task | Deliverable |
|---|------|-------------|
| 2.1 | Implement baseline AP learning (first-run snapshot) | `src/baseline.py` |
| 2.2 | Implement baseline comparison (new AP, changed encryption/channel) | `src/baseline.py` |
| 2.3 | Implement Evil Twin detection logic | `src/detector.py` |
| 2.4 | Implement deauthentication flood detection | `src/detector.py` |
| 2.5 | Implement rogue AP detection (new AP not in baseline) | `src/detector.py` |
| 2.6 | Integrate detector output with threat DB table | `src/database.py` |
| 2.7 | Write unit tests for all detection paths | `tests/` |

### Phase 3 — Web Dashboard & Authentication

**Goal:** Build the dark-themed web dashboard with real-time updates and secure auth.

| # | Task | Deliverable |
|---|------|-------------|
| 3.1 | Implement Flask app factory with SocketIO | `src/app.py` |
| 3.2 | Implement bcrypt auth with rate limiting (10/15min) and session (24h) | `src/auth.py` |
| 3.3 | Create dark-theme base template and CSS | `templates/`, `static/` |
| 3.4 | Build login page | `templates/login.html` |
| 3.5 | Build dashboard page (live AP table, threat feed) | `templates/dashboard.html` |
| 3.6 | Implement SocketIO event emitters for real-time updates | `src/app.py` |
| 3.7 | Implement Chart.js signal strength and channel graphs | `static/js/` |
| 3.8 | Build settings panel (baseline management, feature toggles) | `templates/settings.html` |
| 3.9 | Write API endpoint and auth tests | `tests/` |

### Phase 4 — Alert Channels & SIEM

**Goal:** Implement all alert dispatch channels and SIEM Syslog forwarding.

| # | Task | Deliverable |
|---|------|-------------|
| 4.1 | Implement alert dispatcher base with rate limiting | `src/alerts.py` |
| 4.2 | Implement email alert channel (SMTP) | `src/alerts.py` |
| 4.3 | Implement Telegram bot alert channel | `src/alerts.py` |
| 4.4 | Implement webhook alert channel | `src/alerts.py` |
| 4.5 | Implement GPIO buzzer alert channel | `src/alerts.py` |
| 4.6 | Implement SIEM Syslog forwarder (UDP/TCP, CEF format) | `src/siem.py` |
| 4.7 | Write unit tests with mocked external services | `tests/` |

### Phase 5 — GPS, Portable Mode & Polish

**Goal:** Add GPS tagging, portable mode, and overall polish.

| # | Task | Deliverable |
|---|------|-------------|
| 5.1 | Implement GPS handler (gpsd-py3 client) | `src/gps_handler.py` |
| 5.2 | Integrate GPS data into scan events and threats | `src/scanner.py`, `src/detector.py` |
| 5.3 | Implement portable mode (reduced frequency, headless, LED status) | `src/config.py`, `src/scanner.py` |
| 5.4 | Add GPS coordinate display to dashboard | `templates/dashboard.html` |
| 5.5 | Write GPS and portable mode tests | `tests/` |

### Phase 6 — Deployment & Documentation

**Goal:** Finalize deploy pipeline, systemd service, and all documentation.

| # | Task | Deliverable |
|---|------|-------------|
| 6.1 | Create deploy script (rsync to rasp-pi) | `deploy/deploy_to_pi.sh` |
| 6.2 | Create monitor-mode setup script | `scripts/setup_monitor_mode.sh` |
| 6.3 | Create OS dependency installer script | `scripts/install_deps.sh` |
| 6.4 | Write systemd service unit file | `docs/` or README |
| 6.5 | Write threat model document | `docs/threat_model.md` |
| 6.6 | Final integration testing on Raspberry Pi hardware | Test report |
| 6.7 | Update README with final instructions | `README.md` |

---

## 8. `.env.default` Reference

```ini
# ─── Flask & Security ──────────────────────────────────────
SECRET_KEY=change-me-to-a-random-string
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...  # bcrypt hash of your password

# ─── Database ──────────────────────────────────────────────
DB_PATH=data/rogue_ap.db

# ─── Scanner ───────────────────────────────────────────────
MONITOR_INTERFACE=wlan1mon
SCAN_INTERVAL=10
CHANNEL_HOP_INTERVAL=0.5
SCAN_BANDS=both

# ─── Detection ─────────────────────────────────────────────
ENABLE_EVIL_TWIN_DETECTION=true
ENABLE_DEAUTH_DETECTION=true
DEAUTH_THRESHOLD=10
ENABLE_BASELINE_LEARNING=true
BASELINE_AUTO_LEARN=false

# ─── OUI Lookup ────────────────────────────────────────────
ENABLE_OUI_LOOKUP=true

# ─── GPS ───────────────────────────────────────────────────
ENABLE_GPS=false
GPS_HOST=127.0.0.1
GPS_PORT=2947

# ─── Alerts (master) ──────────────────────────────────────
ENABLE_ALERTS=true

# ─── Email Alerts ──────────────────────────────────────────
ENABLE_EMAIL_ALERTS=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
ALERT_EMAIL_TO=

# ─── Telegram Alerts ──────────────────────────────────────
ENABLE_TELEGRAM_ALERTS=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# ─── Webhook Alerts ───────────────────────────────────────
ENABLE_WEBHOOK_ALERTS=false
WEBHOOK_URL=

# ─── GPIO Buzzer ──────────────────────────────────────────
ENABLE_GPIO_BUZZER=false
GPIO_BUZZER_PIN=18

# ─── SIEM / Syslog ────────────────────────────────────────
ENABLE_SIEM=false
SIEM_HOST=127.0.0.1
SIEM_PORT=514
SIEM_PROTOCOL=udp

# ─── Portable Mode ────────────────────────────────────────
ENABLE_PORTABLE_MODE=false

# ─── Web Dashboard ────────────────────────────────────────
ENABLE_WEB_DASHBOARD=true
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
SESSION_EXPIRY_HOURS=24
RATE_LIMIT=10/15min

# ─── Development ──────────────────────────────────────────
MOCK_MODE=false
LOG_LEVEL=INFO
```

---

## 9. Deliverables

| # | Deliverable | Format | Notes |
|---|-------------|--------|-------|
| 1 | Scanning engine with channel hopping | Python module | `src/scanner.py` |
| 2 | Evil Twin & deauth detection engine | Python module | `src/detector.py` |
| 3 | Baseline AP manager | Python module | `src/baseline.py` |
| 4 | OUI vendor lookup | Python module | `src/oui_lookup.py` |
| 5 | GPS handler | Python module | `src/gps_handler.py` |
| 6 | Alert dispatcher (email, Telegram, webhook, GPIO) | Python module | `src/alerts.py` |
| 7 | SIEM Syslog forwarder | Python module | `src/siem.py` |
| 8 | SQLite database layer | Python module | `src/database.py` |
| 9 | Flask + SocketIO web dashboard | Python + HTML/JS/CSS | `src/app.py`, `templates/`, `static/` |
| 10 | bcrypt auth with rate limiting | Python module | `src/auth.py` |
| 11 | Configuration loader | Python module | `src/config.py` |
| 12 | Monitor mode setup script | Bash | `scripts/setup_monitor_mode.sh` |
| 13 | OS dependency installer | Bash | `scripts/install_deps.sh` |
| 14 | Deploy script | Bash | `deploy/deploy_to_pi.sh` |
| 15 | systemd service unit | INI | Documented in README |
| 16 | Test suite (≥80% coverage) | pytest | `tests/` |
| 17 | Threat model | Markdown | `docs/threat_model.md` |
| 18 | README & TSD | Markdown | Root-level docs |
