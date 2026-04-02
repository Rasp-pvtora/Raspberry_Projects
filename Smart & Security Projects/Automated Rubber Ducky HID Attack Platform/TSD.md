# Technical Specification Document — Automated Rubber Ducky HID Attack Platform

## 1. Scope

### In Scope

- USB HID keyboard emulation via Linux ConfigFS USB Gadget (`libcomposite`)
- DuckyScript interpreter (Hak5 DuckyScript syntax compatible)
- Categorized payload library (recon, exfiltration, configuration)
- Dual-mode USB composite gadget (HID keyboard + mass storage)
- Web-based payload editor with syntax highlighting
- Execution logging with per-keystroke timestamps
- Multiple trigger modes: immediate, button (GPIO), timed delay, manual (web UI)
- Target OS detection from USB enumeration metadata
- Anti-detection documentation for defensive awareness
- WiFi Access Point mode for wireless payload management (hostapd + dnsmasq)
- Dark-themed Flask + SocketIO web dashboard with auth
- bcrypt authentication with rate limiting and session expiry
- Mock mode for development/testing without hardware
- All features toggled via `.env`
- SQLite for persistence
- Deployment via rsync to `rasp-pi` (192.168.216.90)

### Out of Scope

- Active network attacks (MitM, ARP poisoning, packet injection)
- Wireless attacks (deauth, evil twin, WiFi cracking)
- Firmware-level USB exploits (BadUSB firmware modification)
- Physical keylogger functionality (capturing target's keystrokes)
- Multi-Pi coordination or C2 infrastructure
- Cloud-hosted dashboard or remote management over the internet
- Non-Linux host OS for the Pi (Windows IoT, etc.)
- Commercial licensing or paid features
- Automated exploitation without user-initiated triggers

---

## 2. MVP Features (P0)

| ID | Feature | Priority |
|----|---------|----------|
| P0-1 | ConfigFS USB HID gadget setup & teardown | P0 |
| P0-2 | DuckyScript parser (STRING, DELAY, GUI, ALT, CTRL, SHIFT, ENTER, arrows, F-keys) | P0 |
| P0-3 | Keystroke execution engine (HID report writer to /dev/hidg0) | P0 |
| P0-4 | Payload manager (CRUD, file-based storage, SQLite index) | P0 |
| P0-5 | Web dashboard (dark theme, payload list, trigger controls) | P0 |
| P0-6 | Web-based payload editor (CodeMirror, syntax validation) | P0 |
| P0-7 | Manual trigger mode (execute from web UI) | P0 |
| P0-8 | Execution logging (per-payload, timestamped) | P0 |
| P0-9 | Authentication (bcrypt, rate limiting 10/15min, 24h session) | P0 |
| P0-10 | SQLite database (schema, payloads, logs, settings) | P0 |
| P0-11 | Mock mode (simulated HID output for dev/testing) | P0 |
| P0-12 | Deploy script (rsync to rasp-pi, systemd service) | P0 |

### Nice-to-Have (P1/P2)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| P1-1 | Target OS detection from USB enumeration | P1 | Conditional DuckyScript branching |
| P1-2 | GPIO button trigger | P1 | Requires physical button on GPIO pin |
| P1-3 | Timed trigger (configurable delay) | P1 | Auto-execute after N seconds |
| P1-4 | Immediate trigger (execute on plug-in) | P1 | Dangerous — requires explicit enable |
| P1-5 | Status LED (GPIO) | P1 | Visual feedback for headless operation |
| P1-6 | Dual-mode USB (HID + mass storage) | P1 | Composite gadget for exfiltration payloads |
| P1-7 | WiFi Access Point mode | P1 | Requires hostapd + dnsmasq setup |
| P1-8 | Per-keystroke execution logging | P1 | Detailed audit trail for pentest reports |
| P2-1 | Payload import/export (file upload/download) | P2 | Dashboard enhancement |
| P2-2 | DuckyScript variable substitution ($TARGET_OS, etc.) | P2 | Advanced scripting |
| P2-3 | Conditional execution (IFOS ... ENDIF) | P2 | OS-specific payload branching |
| P2-4 | Execution replay from logs | P2 | Re-run logged keystroke sequence |

---

## 3. Database Schema

SQLite with WAL mode enabled. All timestamps stored as ISO-8601 UTC.

### Table: `payloads`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique payload ID |
| name | TEXT | NOT NULL, UNIQUE | Payload display name |
| description | TEXT | | Human-readable description |
| category | TEXT | NOT NULL | `recon`, `exfiltration`, `configuration`, `custom` |
| target_os | TEXT | DEFAULT 'any' | Target OS: `any`, `windows`, `macos`, `linux` |
| filename | TEXT | NOT NULL | Relative path in `payloads/` directory |
| content | TEXT | | DuckyScript source (cached from file) |
| author | TEXT | DEFAULT 'local' | Payload author |
| risk_level | TEXT | DEFAULT 'medium' | `low`, `medium`, `high`, `critical` |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |
| updated_at | TEXT | NOT NULL | ISO-8601 last modification timestamp |
| execution_count | INTEGER | DEFAULT 0 | Number of times executed |
| last_executed_at | TEXT | | ISO-8601 timestamp of last execution |

### Table: `execution_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique log entry ID |
| payload_id | INTEGER | FK → payloads.id | Executed payload reference |
| payload_name | TEXT | NOT NULL | Payload name (denormalized for log integrity) |
| started_at | TEXT | NOT NULL | ISO-8601 execution start time |
| completed_at | TEXT | | ISO-8601 execution end time (NULL if aborted) |
| status | TEXT | NOT NULL | `running`, `completed`, `aborted`, `error` |
| trigger_mode | TEXT | NOT NULL | `immediate`, `button`, `timed`, `manual` |
| target_os | TEXT | | Detected target OS (`windows`, `macos`, `linux`, `unknown`) |
| keystrokes_sent | INTEGER | DEFAULT 0 | Total keystrokes sent |
| duration_ms | INTEGER | | Execution duration in milliseconds |
| error_message | TEXT | | Error details if status is `error` |

### Table: `keystroke_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique keystroke log ID |
| execution_id | INTEGER | FK → execution_logs.id, INDEX | Parent execution reference |
| timestamp | TEXT | NOT NULL | ISO-8601 with microsecond precision |
| command | TEXT | NOT NULL | DuckyScript command (`STRING`, `ENTER`, `DELAY`, etc.) |
| argument | TEXT | | Command argument (the string typed, delay value, etc.) |
| hid_report | TEXT | | Raw HID report bytes (hex-encoded) |
| sequence_num | INTEGER | NOT NULL | Order within execution |
| success | INTEGER | DEFAULT 1 | 1 if sent successfully, 0 on error |

### Table: `settings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | TEXT | PK | Setting name |
| value | TEXT | | Setting value (JSON-encoded) |
| updated_at | TEXT | NOT NULL | ISO-8601 last update time |

---

## 4. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Raspberry Pi 4                                │
│                                                                      │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐  │
│  │  ConfigFS     │    │  DuckyScript     │    │  Execution        │  │
│  │  USB Gadget   │<──>│  Interpreter     │───>│  Engine           │  │
│  │  /dev/hidg0   │    │  (parser +       │    │  (HID report      │  │
│  │  /dev/hidg1   │    │   variables)     │    │   writer)         │  │
│  │  (mass stor.) │    └──────────────────┘    └────────┬──────────┘  │
│  └──────┬───────┘                                     │              │
│         │            ┌──────────────────┐    ┌────────▼──────────┐  │
│         │            │  Trigger Manager │    │  Execution        │  │
│         │            │                  │    │  Logger           │  │
│         │            │  ┌────────────┐  │    │  (per-keystroke   │  │
│         │            │  │ Immediate  │  │    │   timestamps)     │  │
│         │            │  │ GPIO Btn   │  │    └────────┬──────────┘  │
│         │            │  │ Timed      │  │             │              │
│         │            │  │ Manual/Web │  │             │              │
│         │            │  └────────────┘  │             │              │
│         │            └──────────────────┘             │              │
│         │                                             │              │
│         │            ┌──────────────────┐             │              │
│         │            │  OS Detector     │             │              │
│         │            │  (USB enum       │             │              │
│         │            │   analysis)      │             │              │
│         │            └──────────────────┘             │              │
│         │                                             │              │
│  ┌──────▼─────────────────────────────────────────────▼──────────┐  │
│  │                    SQLite Database                              │  │
│  │  ┌──────────┐ ┌───────────────┐ ┌──────────────┐ ┌─────────┐ │  │
│  │  │payloads  │ │execution_logs │ │keystroke_logs│ │settings │ │  │
│  │  └──────────┘ └───────────────┘ └──────────────┘ └─────────┘ │  │
│  └───────────────────────────┬────────────────────────────────────┘  │
│                              │                                       │
│  ┌──────────────┐   ┌───────▼────────────────────────────────────┐  │
│  │  WiFi AP      │   │  Flask + SocketIO Web Dashboard            │  │
│  │  (hostapd +   │──>│  - bcrypt auth (rate limit 10/15min)       │  │
│  │   dnsmasq)    │   │  - 24h session expiry                      │  │
│  │  10.0.0.1     │   │  - Dark theme, payload editor (CodeMirror) │  │
│  └──────────────┘   │  - Live execution status & log viewer       │  │
│                      │  - Trigger mode selection                    │  │
│  ┌──────────────┐   └────────────────────────────────────────────┘  │
│  │  GPIO         │                                                   │
│  │  - Btn (17)   │                                                   │
│  │  - LED (27)   │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                            │
│         ▼                                                            │
│   USB-C ──────────> Target Computer (HID keyboard / mass storage)    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Threat Model

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| Unauthorized use against non-consented systems | Criminal liability, organizational damage | High (misuse risk) | Legal disclaimer, audit logging, require written authorization |
| Brute-force login to dashboard | Unauthorized payload execution | Medium | bcrypt hashing, rate limiting (10/15min), session expiry (24h) |
| Session hijacking (cookie theft) | Impersonate admin, trigger payloads | Low | Secure cookie flags, `SECRET_KEY` rotation, session expiry |
| CSRF on payload execution | Unauthorized payload trigger | High | CSRF tokens on all forms, SameSite cookie attribute |
| SQLite injection via dashboard input | Data corruption, payload tampering | Low | Parameterized queries, input validation |
| Malicious payload injection via editor | Execute unintended commands on target | Medium | Payload review before execution, risk level classification |
| WiFi AP credential brute-force | Unauthorized dashboard access via AP | Medium | WPA2 with strong password, client isolation, MAC filtering |
| Execution log data exposure | Passwords/tokens in keystroke logs | High | Encrypt logs at rest, limit retention, access control |
| Physical device theft | Payload and log exposure | Medium | SD card encryption, strong admin password, remote wipe capability |
| Malicious .env modification | Feature disabling, credential theft | Medium | File permissions (600), deploy via rsync only |
| HID report injection from compromised Pi | Uncontrolled keystroke execution | Low | Root-only access to /dev/hidg0, systemd hardening |
| USB VID/PID detection by EDR | HID device blocked by endpoint security | Medium | Configurable VID/PID, documented anti-detection strategies |
| DuckyScript parsing exploit | Arbitrary code execution on Pi | Low | Sandboxed parser, no `eval()`/`exec()`, input sanitization |

---

## 6. Tech Stack

| Layer | Technology | Version / Notes |
|-------|-----------|-----------------|
| Language | Python 3.11+ | Type hints throughout |
| Web framework | Flask | 3.x with app factory pattern |
| Real-time | Flask-SocketIO | eventlet async mode |
| USB gadget | ConfigFS + libcomposite | Kernel module, no external lib |
| HID protocol | Custom HID report writer | Raw bytes to /dev/hidg0 |
| DuckyScript | Custom interpreter | Hak5 syntax compatible |
| WiFi AP | hostapd + dnsmasq | System services |
| Auth | bcrypt | Password hashing |
| Config | python-dotenv | `.env` loader |
| Database | SQLite3 | WAL mode, stdlib `sqlite3` |
| Editor UI | CodeMirror 6 | CDN or vendored |
| CSS | Custom dark theme | No framework |
| GPIO | RPi.GPIO | Button trigger + status LED |
| Deployment | rsync + systemd | SSH alias `rasp-pi` |
| Testing | pytest + pytest-cov | Mocking with unittest.mock |

---

## 7. Development Phases

### Phase 1 — Project Foundation & USB HID Gadget

**Goal:** Scaffold the project, set up configuration loading, database, and the core USB HID gadget with basic keystroke execution.

| # | Task | Deliverable |
|---|------|-------------|
| 1.1 | Initialize project structure (dirs, `pyproject.toml`, `requirements.txt`) | Repo skeleton |
| 1.2 | Implement `.env` config loader with dataclass validation | `src/config.py` |
| 1.3 | Implement SQLite database module with schema creation (WAL mode) | `src/database.py` |
| 1.4 | Implement ConfigFS USB HID gadget setup/teardown | `src/hid_gadget.py` |
| 1.5 | Implement HID report writer (raw keystroke sender) | `src/executor.py` |
| 1.6 | Implement mock mode (simulated HID output for dev/testing) | Mock path in `src/executor.py` |
| 1.7 | Create USB gadget setup script | `scripts/setup_usb_gadget.sh` |
| 1.8 | Write unit tests for config, database, HID gadget, executor | `tests/` |

### Phase 2 — DuckyScript Interpreter & Payload Library

**Goal:** Build the DuckyScript parser and payload management system.

| # | Task | Deliverable |
|---|------|-------------|
| 2.1 | Implement DuckyScript parser (tokenizer, command mapping) | `src/duckyscript.py` |
| 2.2 | Implement all standard DuckyScript commands | `src/duckyscript.py` |
| 2.3 | Implement variable substitution ($TARGET_OS, $TIMESTAMP, etc.) | `src/duckyscript.py` |
| 2.4 | Implement conditional execution (IFOS ... ENDIF) | `src/duckyscript.py` |
| 2.5 | Implement payload manager (CRUD, file + DB sync) | `src/payload_manager.py` |
| 2.6 | Create sample payloads (recon, exfiltration, configuration) | `payloads/` |
| 2.7 | Write unit tests for parser, commands, payload manager | `tests/` |

### Phase 3 — Web Dashboard & Authentication

**Goal:** Build the dark-themed web dashboard with payload editor and authentication.

| # | Task | Deliverable |
|---|------|-------------|
| 3.1 | Implement Flask app factory with SocketIO | `src/app.py` |
| 3.2 | Implement bcrypt auth with rate limiting (10/15min) and session (24h) | `src/auth.py` |
| 3.3 | Create dark-theme base template and CSS | `templates/`, `static/` |
| 3.4 | Build login page | `templates/login.html` |
| 3.5 | Build dashboard page (payload list, status, trigger controls) | `templates/dashboard.html` |
| 3.6 | Build payload editor page (CodeMirror, syntax validation) | `templates/editor.html` |
| 3.7 | Build payload library browser (search, filter, categories) | `templates/library.html` |
| 3.8 | Implement SocketIO real-time execution status | `src/app.py`, `static/js/` |
| 3.9 | Build settings panel (runtime toggles, trigger mode) | `templates/settings.html` |
| 3.10 | Write API endpoint and auth tests | `tests/` |

### Phase 4 — Trigger Modes & Execution Logging

**Goal:** Implement all trigger modes and detailed execution logging.

| # | Task | Deliverable |
|---|------|-------------|
| 4.1 | Implement trigger mode manager | `src/trigger.py` |
| 4.2 | Implement immediate trigger (execute on USB connection detect) | `src/trigger.py` |
| 4.3 | Implement GPIO button trigger with debounce | `src/trigger.py` |
| 4.4 | Implement timed trigger (configurable delay) | `src/trigger.py` |
| 4.5 | Implement manual trigger (web UI button) | `src/app.py` |
| 4.6 | Implement execution logging (per-payload, per-keystroke) | `src/logger.py` |
| 4.7 | Implement log viewer page with real-time streaming | `templates/logs.html` |
| 4.8 | Implement log export (CSV, JSON) | `src/app.py` |
| 4.9 | Write trigger mode and logging tests | `tests/` |

### Phase 5 — OS Detection, Dual-Mode USB & WiFi AP

**Goal:** Add target OS detection, dual-mode USB, and WiFi access point.

| # | Task | Deliverable |
|---|------|-------------|
| 5.1 | Implement target OS detection from USB enumeration | `src/os_detect.py` |
| 5.2 | Integrate OS detection into DuckyScript variables | `src/duckyscript.py` |
| 5.3 | Implement composite USB gadget (HID + mass storage) | `src/mass_storage.py` |
| 5.4 | Implement WiFi AP manager (hostapd + dnsmasq control) | `src/wifi_ap.py` |
| 5.5 | Create WiFi AP setup script | `scripts/setup_wifi_ap.sh` |
| 5.6 | Implement status LED GPIO patterns | `src/trigger.py` |
| 5.7 | Write OS detection, mass storage, and WiFi AP tests | `tests/` |

### Phase 6 — Deployment & Documentation

**Goal:** Finalize deploy pipeline, systemd service, and all documentation.

| # | Task | Deliverable |
|---|------|-------------|
| 6.1 | Create deploy script (rsync to rasp-pi) | `deploy/deploy_to_pi.sh` |
| 6.2 | Create USB gadget setup script | `scripts/setup_usb_gadget.sh` |
| 6.3 | Create OS dependency installer script | `scripts/install_deps.sh` |
| 6.4 | Write systemd service unit file | docs / README |
| 6.5 | Write threat model document | `docs/threat_model.md` |
| 6.6 | Write DuckyScript reference guide | `docs/duckyscript_reference.md` |
| 6.7 | Write anti-detection documentation | `docs/anti_detection.md` |
| 6.8 | Final integration testing on Raspberry Pi hardware | Test report |
| 6.9 | Update README with final instructions | `README.md` |

---

## 8. `.env.default` Reference

```ini
# ─── Flask & Security ──────────────────────────────────────
SECRET_KEY=change-me-to-a-random-string
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...  # bcrypt hash of your password

# ─── Database ──────────────────────────────────────────────
DB_PATH=data/rubber_ducky.db

# ─── USB HID Gadget ───────────────────────────────────────
ENABLE_HID_GADGET=true
HID_DEVICE_PATH=/dev/hidg0
ENABLE_MASS_STORAGE=false
MASS_STORAGE_IMAGE=data/storage.img
MASS_STORAGE_SIZE_MB=64

# ─── DuckyScript ──────────────────────────────────────────
ENABLE_DUCKYSCRIPT=true
DEFAULT_DELAY_MS=50

# ─── Payload Library ─────────────────────────────────────
ENABLE_PAYLOAD_LIBRARY=true
PAYLOAD_DIR=payloads/

# ─── Execution Logging ───────────────────────────────────
ENABLE_EXECUTION_LOGGING=true
LOG_KEYSTROKES=true

# ─── Trigger Modes ───────────────────────────────────────
TRIGGER_MODE=manual
TRIGGER_DELAY_SECONDS=5
ENABLE_GPIO_TRIGGER=false
GPIO_TRIGGER_PIN=17

# ─── Status LED ──────────────────────────────────────────
ENABLE_STATUS_LED=false
GPIO_LED_PIN=27

# ─── OS Detection ────────────────────────────────────────
ENABLE_OS_DETECTION=true

# ─── WiFi Access Point ───────────────────────────────────
ENABLE_WIFI_AP=false
WIFI_AP_SSID=DuckyConfig
WIFI_AP_PASSWORD=ducky12345
WIFI_AP_CHANNEL=6
WIFI_AP_IP=10.0.0.1

# ─── Web Dashboard ───────────────────────────────────────
ENABLE_WEB_DASHBOARD=true
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
SESSION_EXPIRY_HOURS=24
RATE_LIMIT=10/15min

# ─── Development ─────────────────────────────────────────
MOCK_MODE=false
LOG_LEVEL=INFO
```

---

## 9. Deliverables

| # | Deliverable | Format | Notes |
|---|-------------|--------|-------|
| 1 | ConfigFS USB HID gadget manager | Python module | `src/hid_gadget.py` |
| 2 | DuckyScript interpreter | Python module | `src/duckyscript.py` |
| 3 | Keystroke execution engine | Python module | `src/executor.py` |
| 4 | Payload manager (CRUD, categories) | Python module | `src/payload_manager.py` |
| 5 | Trigger mode manager | Python module | `src/trigger.py` |
| 6 | Target OS detector | Python module | `src/os_detect.py` |
| 7 | Dual-mode USB mass storage | Python module | `src/mass_storage.py` |
| 8 | WiFi AP manager | Python module | `src/wifi_ap.py` |
| 9 | Execution logger | Python module | `src/logger.py` |
| 10 | SQLite database layer | Python module | `src/database.py` |
| 11 | Flask + SocketIO web dashboard | Python + HTML/JS/CSS | `src/app.py`, `templates/`, `static/` |
| 12 | Web-based payload editor | HTML/JS | `templates/editor.html`, `static/js/editor.js` |
| 13 | bcrypt auth with rate limiting | Python module | `src/auth.py` |
| 14 | Configuration loader | Python module | `src/config.py` |
| 15 | USB gadget setup script | Bash | `scripts/setup_usb_gadget.sh` |
| 16 | WiFi AP setup script | Bash | `scripts/setup_wifi_ap.sh` |
| 17 | OS dependency installer | Bash | `scripts/install_deps.sh` |
| 18 | Deploy script | Bash | `deploy/deploy_to_pi.sh` |
| 19 | systemd service unit | INI | Documented in README |
| 20 | Sample payloads (recon, exfil, config) | DuckyScript `.txt` | `payloads/` |
| 21 | Test suite (≥80% coverage) | pytest | `tests/` |
| 22 | Threat model | Markdown | `docs/threat_model.md` |
| 23 | DuckyScript reference | Markdown | `docs/duckyscript_reference.md` |
| 24 | Anti-detection documentation | Markdown | `docs/anti_detection.md` |
| 25 | README & TSD | Markdown | Root-level docs |
