# 🏷️ SmartGate AI — Technical Specification Document

## 📋 Table of Contents

- [Scope](#scope)
- [MVP Features](#mvp-features)
- [Nice-to-Have Features](#nice-to-have-features)
- [Database Schema](#database-schema)
- [Architecture](#architecture)
- [Threat Model](#threat-model)
- [Tech Stack](#tech-stack)
- [Development Phases](#development-phases)
- [.env.default](#envdefault)
- [API Endpoints](#api-endpoints)
- [Performance Targets](#performance-targets)
- [Deliverables](#deliverables)

---

## Scope

### In-Scope
- ALPR-based vehicle entry/exit with GPIO gate control
- NFC/RFID badge backup access system
- MySQL-backed employee/plate/spot management
- Real-time web dashboard with SVG parking map (🔴🟢🟡⚪)
- Microsoft Teams presence integration (Graph API)
- Google Calendar/Workspace integration
- Multi-language bot notifications (Teams/Telegram/WhatsApp)
- Dynamic spot reallocation based on user response
- Shared-spot scheduling with shift logic
- EV charging station monitoring and payroll billing
- Guest plate pre-registration with time-limited access
- HR time-tracking with entry/exit timestamps
- Peak-hour analytics and heatmap visualization
- PDF/Excel monthly attendance reports
- GDPR-compliant data retention and auto-purge
- REST API for third-party HR/ERP integration
- Multi-gate support (N Pi nodes → central server)
- Emergency vehicle auto-open priority DB
- Parking violation detection (wrong spot, double park)
- QR-based visitor pass system
- Night-mode IR camera ALPR
- Sound deterrent for unauthorized access

### Out-of-Scope
- Payment gateway integration (Stripe, PayPal)
- Mobile native app (iOS/Android) — PWA only
- Integration with physical parking meters
- Video surveillance recording/playback (NVR)
- Public parking (pay-per-hour) — enterprise/private only
- Autonomous valet parking robot control

---

## MVP Features

Minimum viable product for first deployment:

1. **ALPR Entry Gate** — Camera → plate read → DB lookup → GPIO trigger
2. **NFC Backup** — RC522 override when ALPR fails
3. **Employee Database** — CRUD for employees, plates, spot assignments
4. **Real-Time Parking Map** — SVG with 🔴🟢 status per spot
5. **Access Log** — Entry/exit timestamps in MySQL
6. **Web Dashboard** — Auth, map, logs, employee management
7. **GPIO Control** — Green/Red LED + Relay gate + Buzzer

---

## Nice-to-Have Features

Post-MVP enhancements (each .env toggleable):

| Priority | Feature | Toggle |
|----------|---------|--------|
| P1 | Teams presence integration | `ENABLE_TEAMS_INTEGRATION` |
| P1 | HR time-tracking | `ENABLE_HR_TIMETRACKING` |
| P2 | Telegram/WhatsApp bot | `ENABLE_TELEGRAM_BOT` / `ENABLE_WHATSAPP_BOT` |
| P2 | Shared-spot scheduling | `ENABLE_SHARED_SPOTS` |
| P2 | Shift logic authorization | `ENABLE_SHIFT_LOGIC` |
| P2 | Guest plate management | `ENABLE_GUEST_MANAGEMENT` |
| P3 | EV charging & billing | `ENABLE_EV_BILLING` |
| P3 | Google Calendar integration | `ENABLE_GOOGLE_INTEGRATION` |
| P3 | Violation detection | `ENABLE_VIOLATION_DETECTION` |
| P3 | Heatmap analytics | `ENABLE_HEATMAP_ANALYTICS` |
| P4 | PDF/Excel reports | `ENABLE_PDF_REPORTS` |
| P4 | LDAP/Azure AD sync | `ENABLE_LDAP_SYNC` |
| P4 | Multi-gate topology | `ENABLE_MULTI_GATE` |
| P4 | QR visitor pass | `ENABLE_QR_VISITOR` |
| P5 | Emergency vehicle DB | `ENABLE_EMERGENCY_VEHICLE` |
| P5 | Night-mode IR camera | `ENABLE_NIGHT_MODE` |
| P5 | GDPR auto-purge | `ENABLE_GDPR_PURGE` |
| P5 | Sound deterrent | `ENABLE_SOUND_ALERT` |
| P5 | REST API | `ENABLE_REST_API` |
| P5 | Multi-language dashboard | `ENABLE_I18N` |

---

## Database Schema

### `employees`
```sql
CREATE TABLE employees (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     VARCHAR(50) UNIQUE NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    alias           VARCHAR(20) NOT NULL,
    email           VARCHAR(255),
    department      VARCHAR(100),
    cost_center     VARCHAR(50),
    teams_user_id   VARCHAR(255),
    google_email    VARCHAR(255),
    telegram_chat_id BIGINT,
    whatsapp_number VARCHAR(20),
    preferred_lang  ENUM('en','de','it','fr','es') DEFAULT 'en',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### `plates`
```sql
CREATE TABLE plates (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    plate_number    VARCHAR(20) NOT NULL,
    plate_country   VARCHAR(5) DEFAULT 'DE',
    is_ev           BOOLEAN DEFAULT FALSE,
    is_primary      BOOLEAN DEFAULT TRUE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE INDEX idx_plate (plate_number)
);
```

### `parking_spots`
```sql
CREATE TABLE parking_spots (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    spot_label      VARCHAR(10) NOT NULL UNIQUE,
    zone            ENUM('standard','ev','disabled','vip','guest') DEFAULT 'standard',
    is_covered      BOOLEAN DEFAULT FALSE,
    svg_x           INT NOT NULL,
    svg_y           INT NOT NULL,
    svg_width       INT DEFAULT 60,
    svg_height      INT DEFAULT 30,
    status          ENUM('free','occupied','pending','reserved','maintenance') DEFAULT 'free',
    assigned_employee_id INT,
    current_plate   VARCHAR(20),
    occupied_since  TIMESTAMP NULL,
    FOREIGN KEY (assigned_employee_id) REFERENCES employees(id) ON DELETE SET NULL
);
```

### `spot_schedules` (Shared Spots)
```sql
CREATE TABLE spot_schedules (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    spot_id         INT NOT NULL,
    employee_id     INT NOT NULL,
    day_of_week     ENUM('mon','tue','wed','thu','fri','sat','sun') NOT NULL,
    shift           ENUM('morning','evening','night','all_day') DEFAULT 'all_day',
    priority        INT DEFAULT 0,
    FOREIGN KEY (spot_id) REFERENCES parking_spots(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE INDEX idx_schedule (spot_id, day_of_week, shift)
);
```

### `access_logs`
```sql
CREATE TABLE access_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    plate_number    VARCHAR(20) NOT NULL,
    employee_id     INT,
    gate_id         VARCHAR(20) DEFAULT 'GATE_01',
    event_type      ENUM('entry','exit','denied','emergency','guest') NOT NULL,
    recognition     ENUM('alpr','nfc','manual','qr') DEFAULT 'alpr',
    confidence      FLOAT,
    spot_id         INT,
    plate_image     VARCHAR(255),
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
    FOREIGN KEY (spot_id) REFERENCES parking_spots(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_plate (plate_number),
    INDEX idx_employee (employee_id)
);
```

### `ev_sessions`
```sql
CREATE TABLE ev_sessions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    plate_number    VARCHAR(20) NOT NULL,
    employee_id     INT,
    spot_id         INT NOT NULL,
    start_time      TIMESTAMP NOT NULL,
    end_time        TIMESTAMP NULL,
    kwh_consumed    DECIMAL(8,2) DEFAULT 0,
    cost            DECIMAL(8,2) DEFAULT 0,
    billed          BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
    FOREIGN KEY (spot_id) REFERENCES parking_spots(id) ON DELETE CASCADE
);
```

### `guests`
```sql
CREATE TABLE guests (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    plate_number    VARCHAR(20) NOT NULL,
    guest_name      VARCHAR(200),
    host_employee_id INT NOT NULL,
    valid_from      TIMESTAMP NOT NULL,
    valid_until     TIMESTAMP NOT NULL,
    access_count    INT DEFAULT 0,
    max_access      INT DEFAULT 1,
    qr_token        VARCHAR(64) UNIQUE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_employee_id) REFERENCES employees(id) ON DELETE CASCADE
);
```

### `nfc_badges`
```sql
CREATE TABLE nfc_badges (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    badge_uid       VARCHAR(20) NOT NULL UNIQUE,
    is_active       BOOLEAN DEFAULT TRUE,
    issued_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);
```

### `presence_checks`
```sql
CREATE TABLE presence_checks (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    source          ENUM('teams','google') NOT NULL,
    status          VARCHAR(50),
    bot_question_sent BOOLEAN DEFAULT FALSE,
    bot_response    VARCHAR(100),
    responded_at    TIMESTAMP NULL,
    spot_action     ENUM('freed','kept','no_response') DEFAULT 'no_response',
    checked_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);
```

### `work_hours`
```sql
CREATE TABLE work_hours (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    date            DATE NOT NULL,
    first_entry     TIME,
    last_exit       TIME,
    total_minutes   INT DEFAULT 0,
    break_minutes   INT DEFAULT 0,
    net_minutes     INT DEFAULT 0,
    anomaly         ENUM('none','early_departure','late_arrival','no_exit','short_day') DEFAULT 'none',
    notes           TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE INDEX idx_emp_date (employee_id, date)
);
```

### `settings`
```sql
CREATE TABLE settings (
    key_name        VARCHAR(100) PRIMARY KEY,
    value           TEXT NOT NULL,
    description     VARCHAR(255),
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  Browser (Dashboard)  │  Telegram Bot  │  Teams Bot  │  PWA     │
└──────────┬────────────┴────────┬───────┴──────┬──────┴──────────┘
           │ HTTPS/WSS           │ Webhook       │ Graph API
┌──────────▼─────────────────────▼───────────────▼────────────────┐
│                     APPLICATION LAYER                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Flask/FAPI  │  │ APScheduler  │  │ SocketIO (real-time)   │  │
│  │ Routes      │  │ Cron Jobs    │  │ Parking map updates    │  │
│  └──────┬──────┘  └──────┬───────┘  └────────────┬───────────┘  │
│         │               │                        │               │
│  ┌──────▼──────┐  ┌─────▼────────┐  ┌───────────▼──────────┐   │
│  │ ALPR Engine │  │ Presence     │  │ Notification Engine  │   │
│  │ YOLOv8 +   │  │ Checker      │  │ Teams/TG/WA/Email    │   │
│  │ PaddleOCR  │  │ (Teams/Ggl)  │  │ Multi-lang templates │   │
│  └──────┬──────┘  └──────────────┘  └──────────────────────┘   │
│         │                                                        │
│  ┌──────▼──────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ GPIO Ctrl   │  │ NFC Reader   │  │ EV Billing Engine    │   │
│  │ LED/Relay/  │  │ RC522 SPI    │  │ Session tracking     │   │
│  │ Buzzer      │  │              │  │ Cost calculation     │   │
│  └─────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                       DATA LAYER                                 │
│  MySQL/MariaDB                                                   │
│  ┌───────────┬────────┬──────────┬─────────────┬──────────────┐ │
│  │ employees │ plates │  spots   │ access_logs │ ev_sessions  │ │
│  │ guests    │ badges │schedules │ work_hours  │ presence_chk │ │
│  └───────────┴────────┴──────────┴─────────────┴──────────────┘ │
│  + File Storage: /data/plates/ (captured plate images)           │
└──────────────────────────────────────────────────────────────────┘
```

---

## Threat Model

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Plate spoofing (printed plate) | Unauthorized access | NFC as second factor; confidence threshold; image logging for audit |
| API key leakage (Teams/Google) | Enterprise data exposure | Keys in .env only; never commit; rotate every 90 days |
| SQL injection | Full DB compromise | Parameterized queries only; ORM (SQLAlchemy) recommended |
| Tailgating (following car in) | Unauthorized entry | Ultrasonic sensor at gate; buzzer alert; log discrepancy detection |
| Dashboard password brute-force | Admin account takeover | bcrypt; rate-limit 10/15min; account lockout after 5 failures |
| GDPR violation (plate data retention) | Legal liability | `ENABLE_GDPR_PURGE`; configurable `GDPR_RETENTION_DAYS`; auto-anonymize |
| NFC badge cloning | Unauthorized badge access | UID + challenge-response; badge revocation list; audit trail |
| Network sniffing (credentials) | Credential theft | HTTPS-only; HSTS header; encrypted WebSocket |
| Man-in-the-middle (MS Graph) | Token theft | Certificate pinning; short-lived tokens; refresh token rotation |
| Physical Pi theft | Loss of gate control | Encrypted disk (LUKS); remote wipe; failsafe gate-close on disconnect |
| Relay replay attack | Gate opens without auth | Time-limited relay pulse (500ms); GPIO state monitoring |
| Camera feed hijacking | Spoofed plate images | Camera on dedicated VLAN; signed frames with timestamp |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.11+ |
| Web Framework | Flask 3.x + Flask-SocketIO |
| Database | MariaDB 11.x / MySQL 8.x |
| ORM (optional) | SQLAlchemy 2.x |
| ALPR Model | YOLOv8n (plate detection) + PaddleOCR (text) |
| NFC | mfrc522 (SPI) |
| GPIO | RPi.GPIO / gpiozero |
| Scheduler | APScheduler 3.x |
| Auth | bcrypt + flask-login |
| Enterprise APIs | msal (Teams) · google-api-python-client |
| Notifications | python-telegram-bot · requests (WhatsApp Business API) |
| Reports | reportlab (PDF) · openpyxl (Excel) |
| QR | qrcode (generate) · pyzbar (read) |
| Frontend | Jinja2 + Vanilla JS + SVG + Chart.js |
| Deployment | gunicorn · systemd · nginx (reverse proxy) |

---

## Development Phases

### Phase 1 — ALPR Core (Days 1–3)
- Camera integration with OpenCV
- YOLOv8n plate region detection
- PaddleOCR plate text extraction
- Basic accuracy benchmarking

### Phase 2 — Database & Employee CRUD (Days 3–4)
- MySQL schema initialization script
- Employee, plate, spot CRUD API
- Data validation and constraints

### Phase 3 — GPIO Gate Control (Days 4–5)
- LED (Green/Red/Yellow) control
- Relay trigger with configurable pulse duration
- Buzzer for unauthorized alerts
- NFC/RFID RC522 integration

### Phase 4 — Web Dashboard MVP (Days 5–7)
- Login with bcrypt auth + rate limiting
- Real-time SVG parking map (🔴🟢)
- Access log table with search/filter
- Employee management CRUD pages
- SocketIO real-time updates

### Phase 5 — Teams/Google Integration (Days 7–9)
- Microsoft Graph API: app registration, token flow, presence check
- Google Calendar API: event check for WFH status
- Presence polling scheduler (APScheduler)
- Status → spot color mapping (🟡⚪)

### Phase 6 — Bot Notifications (Days 9–10)
- Multi-language message templates (EN/DE/IT/FR/ES)
- Telegram bot: send question, receive reply, update DB
- WhatsApp Business API integration
- Teams adaptive card messages
- Response handler: "free spot" / "keep spot"

### Phase 7 — Shared Spots & Shifts (Days 10–11)
- Schedule table: employee↔spot↔day↔shift mapping
- Dashboard calendar view for spot assignments
- Conflict resolution logic (priority-based)
- Automatic authorization based on current shift

### Phase 8 — HR Time-Tracking (Days 11–12)
- Entry/exit → work_hours table aggregation
- Break detection (short exits)
- Anomaly detection (early departure, no exit logged)
- Daily summary email/notification to manager (optional)
- CSV export

### Phase 9 — EV Billing (Days 12–13)
- Dedicated camera for EV station monitoring
- Plate-in-bay detection logic
- Billing session start/stop with kWh tracking
- Payroll deduction record
- Unauthorized EV bay alert

### Phase 10 — Analytics & Reports (Days 13–14)
- Peak-hour occupancy charts (Chart.js)
- Heatmap visualization (hour × day matrix)
- Monthly attendance PDF report (reportlab)
- Excel export (openpyxl) for HR
- Dashboard analytics page

### Phase 11 — Advanced Features (Days 14–16)
- Guest management with time-limited access
- QR visitor pass generation and scanning
- Emergency vehicle priority DB
- Violation detection (wrong spot AI or sensor)
- LDAP/Azure AD employee sync
- REST API with key authentication
- Multi-gate node support
- Night-mode IR camera configuration
- GDPR auto-purge scheduler
- Sound deterrent logic
- Multi-language dashboard (i18n)

### Phase 12 — Hardening & Deployment (Days 16–18)
- HTTPS setup (self-signed / Let's Encrypt)
- systemd service file
- MySQL backup cron
- Log rotation
- Performance tuning (connection pooling, query optimization)
- Load testing with simulated plates
- Documentation finalization

---

## .env.default

```ini
# ╔══════════════════════════════════════════════════════════════════╗
# ║         SmartGate AI — Environment Configuration               ║
# ║         Copy to .env and fill in your values                   ║
# ╚══════════════════════════════════════════════════════════════════╝

# ── Application ──────────────────────────────────────────────────
APP_HOST=0.0.0.0
APP_PORT=5000
APP_DEBUG=false
APP_SECRET_KEY=CHANGE_ME_TO_RANDOM_64_CHARS
APP_LOG_LEVEL=INFO
APP_LANGUAGE=en
DARK_THEME=true

# ── Authentication ───────────────────────────────────────────────
ADMIN_USER=admin
ADMIN_PASS_HASH=$2b$12$REPLACE_WITH_BCRYPT_HASH
SESSION_EXPIRY_HOURS=24
MAX_LOGIN_ATTEMPTS=10
LOGIN_COOLDOWN_MINUTES=15

# ── Database (MySQL/MariaDB) ────────────────────────────────────
DB_HOST=localhost
DB_PORT=3306
DB_NAME=smartgate
DB_USER=smartgate_user
DB_PASS=CHANGE_ME
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ── Feature Toggles ─────────────────────────────────────────────
ENABLE_ALPR=true
ENABLE_NFC_BACKUP=true
ENABLE_TEAMS_INTEGRATION=false
ENABLE_GOOGLE_INTEGRATION=false
ENABLE_WHATSAPP_BOT=false
ENABLE_TELEGRAM_BOT=false
ENABLE_SHARED_SPOTS=false
ENABLE_SHIFT_LOGIC=false
ENABLE_EV_BILLING=false
ENABLE_GUEST_MANAGEMENT=false
ENABLE_HR_TIMETRACKING=true
ENABLE_VIOLATION_DETECTION=false
ENABLE_EMERGENCY_VEHICLE=false
ENABLE_NIGHT_MODE=false
ENABLE_HEATMAP_ANALYTICS=false
ENABLE_PDF_REPORTS=false
ENABLE_GDPR_PURGE=false
ENABLE_SOUND_ALERT=false
ENABLE_MULTI_GATE=false
ENABLE_LDAP_SYNC=false
ENABLE_REST_API=false
ENABLE_QR_VISITOR=false
ENABLE_I18N=false

# ── ALPR Configuration ──────────────────────────────────────────
ALPR_CAMERA_INDEX=0
ALPR_RESOLUTION_W=1920
ALPR_RESOLUTION_H=1080
ALPR_FPS=15
ALPR_CONFIDENCE_THRESHOLD=0.7
ALPR_MODEL_PATH=models/yolov8n_plate.pt
ALPR_OCR_LANG=en
ALPR_SAVE_PLATE_IMAGES=true
ALPR_IMAGE_DIR=data/plates
ALPR_MAX_IMAGE_AGE_DAYS=90

# ── GPIO Pin Assignments ────────────────────────────────────────
PIN_LED_GREEN=17
PIN_LED_RED=27
PIN_LED_YELLOW=22
PIN_RELAY_GATE=23
PIN_RELAY_LOCK=24
PIN_BUZZER=25
PIN_NFC_RST=6
RELAY_PULSE_DURATION_MS=500
GATE_OPEN_HOLD_SEC=10

# ── NFC/RFID (RC522) ────────────────────────────────────────────
NFC_SPI_BUS=0
NFC_SPI_DEVICE=0
NFC_POLL_INTERVAL_MS=500

# ── Microsoft Teams (Graph API) ─────────────────────────────────
TEAMS_TENANT_ID=
TEAMS_CLIENT_ID=
TEAMS_CLIENT_SECRET=
TEAMS_PRESENCE_POLL_MINUTES=15
TEAMS_BOT_MESSAGE_LANG=auto

# ── Google Workspace ─────────────────────────────────────────────
GOOGLE_CREDENTIALS_FILE=config/google_credentials.json
GOOGLE_CALENDAR_CHECK_EVENTS=true
GOOGLE_PRESENCE_POLL_MINUTES=15

# ── Telegram Bot ─────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=

# ── WhatsApp (Business API) ─────────────────────────────────────
WHATSAPP_API_URL=
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

# ── EV Billing ───────────────────────────────────────────────────
EV_CAMERA_INDEX=1
EV_CAMERA_POLL_INTERVAL_SEC=30
EV_KWH_RATE=0.35
EV_CURRENCY=EUR
EV_UNAUTHORIZED_ALERT_DELAY_SEC=120

# ── HR Time-Tracking ────────────────────────────────────────────
HR_WORK_DAY_START=07:00
HR_WORK_DAY_END=18:00
HR_MIN_WORK_HOURS=8.0
HR_BREAK_THRESHOLD_MIN=30
HR_EARLY_DEPARTURE_ALERT=true
HR_LATE_ARRIVAL_THRESHOLD_MIN=15
HR_NOTIFY_MANAGER=false
HR_MANAGER_TEAMS_ID=
HR_CSV_EXPORT_DIR=data/hr_exports

# ── Shared Spots & Shifts ───────────────────────────────────────
SHIFT_MORNING_START=06:00
SHIFT_MORNING_END=14:00
SHIFT_EVENING_START=14:00
SHIFT_EVENING_END=22:00
SHIFT_NIGHT_START=22:00
SHIFT_NIGHT_END=06:00
SPOT_REALLOC_TIMEOUT_MIN=30

# ── Guest Management ────────────────────────────────────────────
GUEST_MAX_VALIDITY_HOURS=24
GUEST_MAX_ACTIVE_PER_EMPLOYEE=3
GUEST_DEFAULT_ZONE=guest

# ── GDPR Compliance ─────────────────────────────────────────────
GDPR_RETENTION_DAYS=365
GDPR_PURGE_SCHEDULE_CRON=0 3 * * 0
GDPR_ANONYMIZE_PLATES=true

# ── Reports ──────────────────────────────────────────────────────
REPORT_SCHEDULE_CRON=0 6 1 * *
REPORT_OUTPUT_DIR=data/reports
REPORT_RECIPIENTS_EMAIL=

# ── Multi-Gate ───────────────────────────────────────────────────
GATE_ID=GATE_01
GATE_NAME=Main Entrance
CENTRAL_SERVER_URL=
CENTRAL_SERVER_API_KEY=

# ── LDAP/Azure AD ────────────────────────────────────────────────
LDAP_SERVER=
LDAP_BASE_DN=
LDAP_BIND_USER=
LDAP_BIND_PASS=
LDAP_SYNC_SCHEDULE_CRON=0 4 * * *

# ── REST API ─────────────────────────────────────────────────────
API_KEY=CHANGE_ME_TO_RANDOM_API_KEY
API_RATE_LIMIT=100/hour

# ── Night Mode ───────────────────────────────────────────────────
NIGHT_MODE_START=20:00
NIGHT_MODE_END=06:00
NIGHT_IR_GPIO=5

# ── Sound Alert ──────────────────────────────────────────────────
BUZZER_DURATION_MS=1000
BUZZER_PATTERN=short_short_long

# ── QR Visitor Pass ──────────────────────────────────────────────
QR_TOKEN_LENGTH=32
QR_EXPIRY_HOURS=8
```

---

## API Endpoints

### Public (Gate Nodes)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/gate/entry` | Report plate detection from gate node |
| POST | `/api/v1/gate/exit` | Report plate exit from gate node |
| GET | `/api/v1/gate/status` | Gate health check |

### Dashboard (Authenticated)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/spots` | All parking spots with current status |
| GET | `/api/v1/spots/:id` | Single spot detail |
| PUT | `/api/v1/spots/:id/override` | Manual status override |
| GET | `/api/v1/employees` | Employee list with plates |
| POST | `/api/v1/employees` | Create employee |
| PUT | `/api/v1/employees/:id` | Update employee |
| DELETE | `/api/v1/employees/:id` | Deactivate employee |
| GET | `/api/v1/logs` | Access logs (paginated, filtered) |
| GET | `/api/v1/logs/export` | Export logs as CSV |
| POST | `/api/v1/guests` | Register guest plate |
| GET | `/api/v1/guests/qr/:token` | QR code image for guest |
| GET | `/api/v1/ev/sessions` | EV charging sessions |
| GET | `/api/v1/hr/hours` | Work hours (date range, employee) |
| GET | `/api/v1/hr/report` | Monthly report (PDF/Excel) |
| GET | `/api/v1/analytics/heatmap` | Occupancy heatmap data |
| GET | `/api/v1/analytics/peak` | Peak hour statistics |
| GET | `/api/v1/settings` | Current settings |
| PUT | `/api/v1/settings` | Update settings |

### Webhooks (Bot Responses)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook/telegram` | Telegram bot callback |
| POST | `/webhook/whatsapp` | WhatsApp webhook |
| POST | `/webhook/teams` | Teams bot callback |

---

## Performance Targets

| Metric | Target |
|--------|--------|
| ALPR processing latency | < 800ms (camera frame → plate text) |
| Gate trigger latency | < 1.5s (plate detect → relay pulse) |
| Dashboard load time | < 2s (initial) |
| SocketIO map update | < 500ms (event → browser) |
| Teams presence poll | Every 15 min (configurable) |
| Bot response processing | < 3s (webhook → DB update) |
| DB query (access log) | < 100ms (indexed) |
| Report generation | < 30s (monthly PDF, 500 employees) |
| Concurrent dashboard users | 20+ |
| Plate recognition accuracy | > 92% (daylight, clean plates) |

---

## Deliverables

- [x] README.md — Project overview, hardware, quick start
- [x] TSD.md — This document
- [x] task.md — Phased task checklist
- [x] implementation_plan.md — Step-by-step implementation guide
- [ ] `app.py` — Flask application entry point
- [ ] `init_db.py` — Database schema initialization
- [ ] `alpr_engine.py` — ALPR detection + OCR pipeline
- [ ] `nfc_reader.py` — RC522 NFC badge reader
- [ ] `gpio_controller.py` — LED, relay, buzzer control
- [ ] `presence_checker.py` — Teams/Google status polling
- [ ] `notification_bot.py` — Multi-channel bot notifications
- [ ] `ev_billing.py` — EV station monitoring and billing
- [ ] `hr_tracker.py` — Work hours calculation
- [ ] `report_generator.py` — PDF/Excel report engine
- [ ] `templates/` — Dashboard HTML (Jinja2)
- [ ] `static/` — CSS, JS, SVG parking map
- [ ] `.env.default` — Environment template
- [ ] `requirements.txt` — Python dependencies
- [ ] `deploy/smartgate.service` — systemd unit file
- [ ] `deploy/nginx.conf` — Reverse proxy config
