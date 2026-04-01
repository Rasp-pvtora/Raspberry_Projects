# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for **RFID RC522 + MySQL Integration**.

---

## 1. Scope

This project builds a secure, keyless entry system using an MFRC522 RFID reader, Raspberry Pi GPIO, and a MariaDB database. It combines hardware (RFID reader, relay, electric lock) with a server-side application (Flask, MariaDB) to create a complete access control solution. A web dashboard provides tag management, access logs, time-based rules, and real-time event monitoring.

**Key goals:**
- RFID-based keyless entry with GPIO-controlled relay and electric lock.
- Full access logging to MariaDB with audit trail.
- Time-based access rules (e.g., office hours only).
- Temporary guest access with auto-expiry.
- Anti-passback protection (entry + exit readers).
- Multi-door support from a single Pi.
- Web dashboard for management and monitoring.
- Telegram/email notifications for security events.

---

## 2. Minimum Viable Features (MVP)

### 2.1 RFID Reading and Authentication

- MFRC522 module reads 13.56 MHz RFID tag UIDs via SPI.
- Auth engine checks tag against MariaDB: registered? active? time-allowed? anti-passback OK?
- Mock reader mode for development on laptops without SPI.

### 2.2 Lock Control

- GPIO-controlled relay activates electric strike/solenoid lock.
- Configurable open duration (`LOCK_OPEN_DURATION_SEC`).
- Configurable relay polarity (`RELAY_ACTIVE_HIGH`).
- Optional piezo buzzer and LED feedback (green=granted, red=denied).

### 2.3 Access Logging and Audit Trail

- Every scan logged to MariaDB: timestamp, tag UID, owner, door, result, denial reason, rule applied.
- Filterable access log (date range, owner, door, result).
- CSV export for external reporting.
- Real-time event feed via WebSocket.

### 2.4 Time-Based Access Rules

- Per-tag weekly schedules (e.g., Mon–Fri 8:00–18:00).
- Multiple rules per tag (different rules per door).
- Holiday/override dates to block access.
- Default: 24/7 access if no rule is set.
- Visual schedule editor on dashboard.

### 2.5 Temporary Access Codes

- Register tags with start/end validity dates.
- Auto-expire after the validity window.
- Revocable from the dashboard.
- Optional notification on temporary tag usage.

### 2.6 Anti-Passback Protection

- Requires two MFRC522 readers (entry + exit).
- Soft mode: log violation but allow entry.
- Hard mode: deny entry on violation.
- Dashboard reset for passback state.

### 2.7 Multi-Door Support

- Multiple MFRC522 readers via different SPI chip-selects (CE0, CE1).
- Per-door relay pin, authorized tags, and time rules.
- Shared MariaDB database.

### 2.8 Web Dashboard (Flask + SocketIO + Jinja2)

- **Authentication:** Session-based login with rate limiting.
- **Dashboard page:** Live access events, door status, system stats.
- **Tags page:** Register, assign owners, activate/deactivate.
- **Access Log page:** Filterable audit trail with CSV export.
- **Rules page:** Time-based rules with visual schedule editor.
- **Doors page:** Multi-door configuration.
- **Settings page:** Notifications, lock settings, anti-passback, password change.

### 2.9 Notifications

- Telegram: unauthorized attempts, temporary tag usage, anti-passback violations.
- Email: daily summary reports, unauthorized attempt alerts.
- Configurable triggers per event type.

### 2.10 Database Schema

```sql
CREATE TABLE tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(20) NOT NULL UNIQUE,
    owner_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_temporary BOOLEAN DEFAULT FALSE,
    valid_from DATETIME,
    valid_until DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE doors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    reader_id VARCHAR(50) NOT NULL,
    relay_pin INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE access_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tag_id INT,
    door_id INT,
    day_of_week TINYINT,        -- 0=Mon, 6=Sun
    start_time TIME,
    end_time TIME,
    FOREIGN KEY (tag_id) REFERENCES tags(id),
    FOREIGN KEY (door_id) REFERENCES doors(id)
);

CREATE TABLE access_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tag_uid VARCHAR(20),
    owner_name VARCHAR(100),
    door_id INT,
    result ENUM('granted', 'denied') NOT NULL,
    denial_reason VARCHAR(100),
    rule_applied VARCHAR(100),
    scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (door_id) REFERENCES doors(id)
);

CREATE TABLE passback_state (
    tag_id INT PRIMARY KEY,
    last_direction ENUM('in', 'out'),
    last_scan_at DATETIME,
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);
```

### 2.11 Environment Configuration

- All configuration via `.env` file (created from `.env.default` template).
- `.env` is in `.gitignore` and never committed.
- Settings page provides a web-based editor.

### 2.12 Deployment

- `deploy/deploy_to_pi.sh` script: rsync files to the Pi, create venv, install dependencies.
- `scripts/setup-spi.sh` for SPI interface enablement.
- `scripts/setup-mariadb.sh` for MariaDB installation and user creation.
- `scripts/setup-gpio.sh` for GPIO group permissions.
- Systemd service file for auto-start.

---

## 3. Nice-to-Have Features

These features require paid third-party services or substantially more complexity.

### 3.1 Remote Database Replication

- Replicate the MariaDB access log to a remote/cloud database for off-site backup.
- Requires a remote MySQL server (self-hosted or cloud: AWS RDS, PlanetScale, etc.).
- Adds cost depending on the provider.

### 3.2 NFC Challenge-Response Authentication

- Upgrade from basic UID reading to NFC DESFire challenge-response.
- Cryptographic authentication prevents UID cloning.
- Requires DESFire tags (~$3–5 each) and more complex firmware.

### 3.3 Mobile App Integration

- Companion mobile app (Flutter/React Native) for remote tag management and push notifications.
- Requires mobile development and push notification service (Firebase).

### 3.4 Biometric Combo

- Add fingerprint reader (e.g., R503/R307) for two-factor authentication: RFID + fingerprint.
- Requires additional hardware and fingerprint matching library.

### 3.5 Integration with Building Management Systems

- MQTT/REST API to integrate with enterprise BMS or Home Assistant.
- Publish access events to MQTT topics.

---

## 4. High-Level Architecture

```
                      ┌────────────────────────────────────────────────────┐
                      │            Raspberry Pi                            │
                      │                                                    │
  Browser ─HTTP────► │  Flask (port 5000)                                  │
  Browser ──WS─────► │  ├── Session auth + rate limiting                   │
                      │  ├── Jinja2 templates (dashboard, tags, etc.)      │
                      │  ├── REST API (/api/tags, /api/log, /api/rules)    │
                      │  ├── SocketIO (live access events)                 │
                      │  └── Static files (/static)                        │
                      │                                                    │
                      │  RFID Pipeline:                                     │
                      │  ┌──────────────────────────────────────────┐      │
                      │  │ MFRC522 (SPI) → Read tag UID            │      │
                      │  │  → Auth Engine (MariaDB lookup)          │      │
                      │  │  → Time rule check                      │      │
                      │  │  → Anti-passback check                   │      │
                      │  │  → Relay → Lock (GPIO)                   │      │
                      │  │  → Buzzer + LEDs (GPIO)                  │      │
                      │  │  → Log to MariaDB                        │      │
                      │  │  → Notification (Telegram / Email)       │      │
                      │  │  → WebSocket (dashboard update)          │      │
                      │  └──────────────────────────────────────────┘      │
                      │                                                    │
                      │  Database:                                          │
                      │  └── MariaDB (rfid_access)                         │
                      │      ├── tags (registered tags + owners)           │
                      │      ├── doors (reader + relay config)             │
                      │      ├── access_rules (time schedules)             │
                      │      ├── access_log (audit trail)                  │
                      │      └── passback_state (anti-passback)            │
                      └────────────────────────────────────────────────────┘
```

---

## 5. Security and Threat Model

**Primary assets:**
- Dashboard credentials and session tokens.
- Database credentials.
- Access log data (who entered where, when).
- RFID tag database (authorized UIDs).
- Physical lock control (GPIO relay).
- `.env` file (all secrets).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Brute-force login | Rate limiting (10 attempts per 15 min); strong password |
| Session hijacking | `httpOnly`, `sameSite` cookies; strong session secret |
| RFID UID cloning | Document limitation; recommend DESFire upgrade for high-security |
| SQL injection | Parameterized queries only; no string concatenation in SQL |
| Unauthorized database access | Dedicated DB user with minimal privileges; not root |
| Physical relay tampering | Lock has manual override; tamper switch on enclosure (advanced) |
| Power failure (lock state) | Use fail-secure lock (locked on power loss) for security; fail-safe (unlocked) for fire safety |
| `.env` exposure | In `.gitignore`; `chmod 600` recommended |
| Access log tampering | Database user has INSERT + SELECT only (no DELETE/UPDATE on logs) |
| XSS via tag owner names | HTML-escape all user input in templates |

See [docs/threat_model.md](docs/threat_model.md) for the complete analysis.

---

## 6. Suggested Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| Backend | Python 3.11+ / Flask | Simple, well-supported, good GPIO ecosystem |
| Real-time | Flask-SocketIO | WebSocket for live access events |
| Templating | Jinja2 | Server-side rendering, no build step |
| Database | MariaDB | MySQL-compatible, full SQL, multi-user capable |
| RFID | mfrc522 + spidev | Standard Pi RFID library |
| GPIO | RPi.GPIO | Standard Pi GPIO control |
| Auth | Session-based + bcrypt | Simple, single-user device auth |
| Notifications | Telegram Bot API, SMTP | Free, reliable |
| CSS | Custom dark theme | Lightweight, no framework dependency |

---

## 7. Development Phases & Concrete Steps

### Phase A — Project scaffold and RFID hardware (Week 1)

1. Initialize Python project with `requirements.txt` and virtual environment.
2. Create `.env.default` template and `.gitignore`.
3. Implement Flask server with Jinja2 layout and sidebar navigation.
4. Implement session-based authentication.
5. Create dark-themed CSS and login page.
6. Implement MFRC522 reader interface (SPI) and mock reader.
7. Test tag UID reading and display on console.

### Phase B — Database and access control (Week 1–2)

1. Write `sql/schema.sql` (tags, doors, rules, log, passback_state).
2. Create `scripts/setup-mariadb.sh` for database setup.
3. Implement `db.py` — MariaDB connection and query helpers.
4. Implement auth engine (tag lookup, time rule check, passback check).
5. Implement lock controller (GPIO relay, buzzer, LEDs).
6. Wire full pipeline: scan → auth → lock → log.
7. Build Dashboard page with live events via WebSocket.

### Phase C — Tag management and logging (Week 2)

1. Implement tag management API (register, deactivate, assign owner).
2. Build Tags page (register from scan, manage, search).
3. Implement access log API with filters and CSV export.
4. Build Access Log page with filterable table.
5. Implement time-based rules API.
6. Build Rules page with visual schedule editor.

### Phase D — Advanced features (Week 2–3)

1. Implement temporary access codes (validity window, auto-expire).
2. Implement anti-passback logic (entry/exit tracking, soft/hard mode).
3. Implement multi-door support (multiple readers, per-door config).
4. Build Doors page (configure readers, relays, per-door settings).
5. Implement Telegram and email notifications.
6. Build Settings page (notifications, lock, anti-passback, password).

### Phase E — Deployment and polish (Week 3)

1. Create `scripts/setup-spi.sh` and `scripts/setup-gpio.sh`.
2. Write deployment script `deploy/deploy_to_pi.sh`.
3. Create systemd service file.
4. Test full deployment on Raspberry Pi with hardware.
5. Test all features end-to-end (tag registration, access, rules, notifications).

### Phase F — Documentation (Week 3–4)

1. Write `README.md` with full setup guide and wiring diagrams.
2. Write `TSD.md` (this document).
3. Write `task.md` engineering checklist.
4. Write `docs/threat_model.md`.

---

## 8. Deliverables

- Full working RFID access control system with MFRC522, relay, and electric lock.
- MariaDB-backed access logging with full audit trail.
- Time-based access rules with visual schedule editor.
- Temporary guest access with auto-expiry.
- Anti-passback protection (soft/hard mode).
- Multi-door support from a single Pi.
- Web dashboard for tag management, access logs, rules, and settings.
- Telegram and email notifications.
- Database schema and setup scripts.
- Deploy script for Raspberry Pi (SSH alias: `rasp-pi` at `192.168.216.90`).
- `README.md`, `TSD.md`, `task.md`, `docs/threat_model.md`.
