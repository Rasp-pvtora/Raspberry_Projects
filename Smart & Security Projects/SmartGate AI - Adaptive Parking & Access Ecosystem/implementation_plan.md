# 🏷️ SmartGate AI — Implementation Plan

## Overview

| Item | Detail |
|------|--------|
| Estimated Duration | 16–18 days |
| Hardware Cost | $133–308 |
| Controller | Raspberry Pi 4 (4GB+) |
| Language | Python 3.11+ |
| Database | MariaDB / MySQL |
| Web Framework | Flask + SocketIO |
| AI Stack | YOLOv8n + PaddleOCR |

---

## Phase 1: ALPR Core Engine (Days 1–3)

### Checkpoint: Camera captures frame → detects plate → reads text with >85% accuracy

- [ ] **1.1** Connect Pi Camera or USB Webcam

```bash
# Test camera
libcamera-still -o test.jpg   # Pi Camera
# or
python3 -c "import cv2; cap=cv2.VideoCapture(0); ret,f=cap.read(); cv2.imwrite('test.jpg',f)"
```

- [ ] **1.2** Install ALPR dependencies

```bash
pip install opencv-python-headless ultralytics paddlepaddle paddleocr numpy
```

- [ ] **1.3** Download YOLOv8n plate detection model

```bash
mkdir -p models
# Option A: Use pretrained plate model
wget -O models/yolov8n_plate.pt <plate-model-url>
# Option B: Fine-tune on plate dataset
yolo detect train data=plates.yaml model=yolov8n.pt epochs=50 imgsz=640
```

- [ ] **1.4** Build ALPR pipeline (`alpr_engine.py`)

```python
class ALPREngine:
    def __init__(self):
        self.yolo = YOLO(os.getenv('ALPR_MODEL_PATH'))
        self.ocr = PaddleOCR(lang=os.getenv('ALPR_OCR_LANG', 'en'))
    
    def detect_plate(self, frame) -> list[PlateResult]:
        """frame → [PlateResult(text, confidence, bbox, image)]"""
        results = self.yolo(frame, conf=float(os.getenv('ALPR_CONFIDENCE_THRESHOLD', 0.7)))
        plates = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = frame[y1:y2, x1:x2]
            ocr_result = self.ocr.ocr(crop, cls=True)
            text = self._normalize_plate(ocr_result)
            plates.append(PlateResult(text=text, confidence=box.conf[0], ...))
        return plates
```

- [ ] **1.5** Build plate normalization (strip spaces, uppercase, handle country formats)
- [ ] **1.6** Benchmark: test with 50+ plate images, log accuracy
- [ ] **1.7** Plate image saving with timestamp naming

---

## Phase 2: Database & Employee CRUD (Days 3–4)

### Checkpoint: MySQL running, all 10 tables created, CRUD tested via CLI

- [ ] **2.1** Install and secure MariaDB

```bash
sudo apt install mariadb-server python3-dev libmariadb-dev -y
sudo mysql_secure_installation
sudo mysql -e "CREATE DATABASE smartgate;"
sudo mysql -e "CREATE USER 'smartgate_user'@'localhost' IDENTIFIED BY 'CHANGE_ME';"
sudo mysql -e "GRANT ALL ON smartgate.* TO 'smartgate_user'@'localhost';"
```

- [ ] **2.2** Create `init_db.py` with all tables from TSD schema
- [ ] **2.3** Build `db.py` connection pool module

```python
import mysql.connector.pooling
pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="smartgate",
    pool_size=int(os.getenv('DB_POOL_SIZE', 10)),
    host=os.getenv('DB_HOST'), ...
)
```

- [ ] **2.4** Build employee service (create, read, update, deactivate)
- [ ] **2.5** Build plate service (add, remove, set primary, toggle EV)
- [ ] **2.6** Build spot service (define spots with SVG coords, assign employees)
- [ ] **2.7** Create seed script with 10 sample employees + plates + spots
- [ ] **2.8** Test all CRUD operations

---

## Phase 3: GPIO Gate Control (Days 4–5)

### Checkpoint: Plate detected → correct LED + relay fires; NFC badge → same result

- [ ] **3.1** Wire hardware: LEDs (GPIO 17/27/22), Relay (23/24), Buzzer (25), RC522 (SPI)
- [ ] **3.2** Build `gpio_controller.py`

```python
class GateController:
    def grant_access(self):
        GPIO.output(PIN_LED_GREEN, HIGH)
        GPIO.output(PIN_RELAY_GATE, HIGH)
        time.sleep(RELAY_PULSE_DURATION_MS / 1000)
        GPIO.output(PIN_RELAY_GATE, LOW)
        threading.Timer(GATE_OPEN_HOLD_SEC, self.reset).start()
    
    def deny_access(self):
        GPIO.output(PIN_LED_RED, HIGH)
        if os.getenv('ENABLE_SOUND_ALERT') == 'true':
            GPIO.output(PIN_BUZZER, HIGH)
            time.sleep(BUZZER_DURATION_MS / 1000)
            GPIO.output(PIN_BUZZER, LOW)
```

- [ ] **3.3** Build `nfc_reader.py` — SPI RC522 polling, badge UID → employee lookup
- [ ] **3.4** Integration: ALPR → DB lookup → GPIO trigger
- [ ] **3.5** Integration: NFC → DB lookup → GPIO trigger
- [ ] **3.6** Test: authorized plate → green + relay; unknown plate → red + buzzer

---

## Phase 4: Web Dashboard MVP (Days 5–7)

### Checkpoint: Login works, parking map shows live status, employees manageable, logs visible

- [ ] **4.1** Flask project structure

```
app.py
├── routes/
│   ├── auth.py          # Login, logout, session
│   ├── dashboard.py     # Main map page
│   ├── employees.py     # Employee CRUD pages
│   ├── spots.py         # Spot management
│   ├── logs.py          # Access log viewer
│   └── settings.py      # Feature toggles, config
├── services/
│   ├── alpr_engine.py
│   ├── gpio_controller.py
│   ├── nfc_reader.py
│   └── db.py
├── templates/
│   ├── layout.html      # Base with dark theme
│   ├── login.html
│   ├── dashboard.html   # SVG parking map
│   ├── employees.html
│   ├── logs.html
│   └── settings.html
├── static/
│   ├── css/style.css    # Dark theme
│   ├── js/
│   │   ├── map.js       # SVG map + SocketIO
│   │   ├── logs.js      # Log table with filter
│   │   └── employees.js
│   └── img/
└── .env.default
```

- [ ] **4.2** Authentication: bcrypt login + rate limiting + CSRF
- [ ] **4.3** SVG parking map:
  - [ ] Generate SVG from spot DB (x, y, w, h coordinates)
  - [ ] Color fill based on status (red/green/yellow/grey)
  - [ ] Employee alias text inside occupied spots
  - [ ] Click handler → spot detail popup
- [ ] **4.4** SocketIO real-time:
  - [ ] Server emits `spot_update` on entry/exit
  - [ ] Client JS updates SVG fill color + label
- [ ] **4.5** Camera live feed: MJPEG stream endpoint
- [ ] **4.6** Employee management pages (list, add, edit)
- [ ] **4.7** Access log page (paginated, search by plate/name/date)
- [ ] **4.8** Settings page (toggle features, view GPIO config)
- [ ] **4.9** Dark theme CSS throughout
- [ ] **4.10** Mobile responsive breakpoints

---

## Phase 5: Teams/Google Integration (Days 7–9)

### Checkpoint: Reserved spots with no car show 🟡/⚪ based on Teams/Google status

- [ ] **5.1** Azure AD app registration:

```
Azure Portal → App registrations → New
  API Permissions: Presence.Read.All (Application)
  Certificates & Secrets → New Client Secret
  Copy: tenant_id, client_id, client_secret → .env
```

- [ ] **5.2** Build Teams presence checker:

```python
from msal import ConfidentialClientApplication
app = ConfidentialClientApplication(
    TEAMS_CLIENT_ID, authority=f"https://login.microsoftonline.com/{TEAMS_TENANT_ID}",
    client_credential=TEAMS_CLIENT_SECRET
)
token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
# Batch presence: POST /communications/getPresencesByUserId
```

- [ ] **5.3** Build Google Calendar checker:
  - [ ] OAuth2 service account credentials
  - [ ] Check today's events for "WFH" / "Home Office" keywords
- [ ] **5.4** Status → spot mapping logic
- [ ] **5.5** APScheduler: `presence_check_job` every `TEAMS_PRESENCE_POLL_MINUTES`
- [ ] **5.6** Dashboard: presence icon overlay on spots (Teams/Google logo)

---

## Phase 6: Bot Notifications (Days 9–10)

### Checkpoint: 🟡 spot triggers multilang bot message → user replies → spot updates to 🟢 or ⚪

- [ ] **6.1** Create language template files (`i18n/en.json`, `de.json`, etc.)
- [ ] **6.2** Telegram bot:

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
keyboard = [[
    InlineKeyboardButton("✅ Yes, free it", callback_data=f"free_{spot_id}"),
    InlineKeyboardButton("❌ No, I'm coming", callback_data=f"keep_{spot_id}")
]]
bot.send_message(chat_id=emp.telegram_chat_id, text=msg, reply_markup=InlineKeyboardMarkup(keyboard))
```

- [ ] **6.3** Telegram webhook handler: parse callback → update spot status
- [ ] **6.4** WhatsApp Business API: send template message + webhook for reply
- [ ] **6.5** Teams Adaptive Card: actionable card with Yes/No buttons
- [ ] **6.6** Response timeout: 30 min no reply → spot stays 🟡
- [ ] **6.7** Dashboard: notification history log (sent/responded/timed out)

---

## Phase 7: Shared Spots & Shift Logic (Days 10–11)

### Checkpoint: Shared spot correctly authorizes User A on Mon, User B on Tue; shift boundaries enforced

- [ ] **7.1** Build schedule CRUD service
- [ ] **7.2** Dashboard calendar view: week grid with spot assignments
- [ ] **7.3** Authorization check: on plate detect → `get_authorized_employee(spot_id, day, shift)`
- [ ] **7.4** Conflict resolution: if two employees claim same slot → highest priority wins
- [ ] **7.5** Shift boundary transitions: auto-update spot assignment at shift change
- [ ] **7.6** Test scenarios: Mon/Fri split, morning/evening split, vacation override

---

## Phase 8: HR Time-Tracking (Days 11–12)

### Checkpoint: Entry/exit logs produce accurate work hours; anomalies flagged and notified

- [ ] **8.1** Build `hr_tracker.py`:
  - [ ] `on_entry(employee_id)` → create/update work_hours row
  - [ ] `on_exit(employee_id)` → update last_exit, calculate minutes
  - [ ] Break logic: exit + re-entry within `HR_BREAK_THRESHOLD_MIN`
- [ ] **8.2** Anomaly detection engine:
  - [ ] Early departure: exit before `HR_WORK_DAY_END` by >30 min
  - [ ] Late arrival: entry after `HR_WORK_DAY_START` + threshold
  - [ ] No exit: end-of-day job flags missing exits
  - [ ] Short day: net_minutes < `HR_MIN_WORK_HOURS × 60`
- [ ] **8.3** Notification: anomaly → message to employee (+ manager if enabled)
- [ ] **8.4** Dashboard HR page: daily table, weekly chart, department filter
- [ ] **8.5** CSV export: `/api/v1/hr/hours?format=csv&from=...&to=...`

---

## Phase 9: EV Billing Module (Days 12–13)

### Checkpoint: Plate enters EV bay → timer starts; plate leaves → cost calculated; unauthorized alerted

- [ ] **9.1** Configure second camera for EV station (or zone in main camera)
- [ ] **9.2** Build `ev_billing.py`:
  - [ ] Define EV bay coordinates in parking map
  - [ ] Plate-in-bay detection: plate position overlaps bay region
  - [ ] Session lifecycle: start → active → end
  - [ ] Cost calculation: `duration_hours × EV_KWH_RATE`
- [ ] **9.3** Visual guidance: on entry, if `plate.is_ev` → highlight recommended EV spot
- [ ] **9.4** Unauthorized detection: non-DB plate in EV bay → supervisor alert
- [ ] **9.5** Dashboard EV page: active sessions, history, monthly billing
- [ ] **9.6** Payroll integration: billing record per employee per month

---

## Phase 10: Analytics & Reports (Days 13–14)

### Checkpoint: Heatmap displays on dashboard; monthly PDF auto-generated

- [ ] **10.1** Build analytics queries:
  - [ ] Hourly occupancy rate (GROUP BY HOUR(timestamp))
  - [ ] Day-of-week utilization pattern
  - [ ] Zone breakdown (standard vs EV vs guest)
  - [ ] Top 10 most/least used spots
- [ ] **10.2** Dashboard analytics page: Chart.js visualizations
- [ ] **10.3** Heatmap: hour × day_of_week colored grid
- [ ] **10.4** Build `report_generator.py`:
  - [ ] PDF template with company header, tables, charts
  - [ ] Excel workbook with multiple sheets (attendance, EV, access)
- [ ] **10.5** APScheduler: monthly report generation + email/save
- [ ] **10.6** Manual report trigger from dashboard (date range picker)

---

## Phase 11: Advanced Features (Days 14–16)

### Checkpoint: Guest QR works; LDAP syncs; GDPR purges; multi-gate reports centrally

- [ ] **11.1** Guest management: register, validate, expire, dashboard page
- [ ] **11.2** QR visitor pass: generate (qrcode lib), scan (pyzbar), validate token
- [ ] **11.3** Emergency vehicle DB: priority table, zero-delay gate open
- [ ] **11.4** Violation detection: wrong-spot plate mismatch → notification
- [ ] **11.5** LDAP sync: query, map fields, create/update employees, scheduled job
- [ ] **11.6** REST API: key auth, rate limit, all endpoints from TSD, OpenAPI docs
- [ ] **11.7** Multi-gate: node registration, central DB, per-gate view
- [ ] **11.8** Night mode: auto-switch camera, IR LED GPIO, adjust thresholds
- [ ] **11.9** GDPR purge: scheduled deletion + anonymization + image cleanup
- [ ] **11.10** Sound patterns: configurable buzzer sequences
- [ ] **11.11** Dashboard i18n: extract strings, translation files, language selector

---

## Phase 12: Hardening & Deployment (Days 16–18)

### Checkpoint: Production-ready with HTTPS, systemd, backups, passing load test

- [ ] **12.1** HTTPS setup:

```bash
# Self-signed
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
# Or Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d smartgate.local
```

- [ ] **12.2** nginx reverse proxy:

```nginx
server {
    listen 443 ssl;
    ssl_certificate     /etc/ssl/smartgate/cert.pem;
    ssl_certificate_key /etc/ssl/smartgate/key.pem;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

- [ ] **12.3** systemd service:

```ini
[Unit]
Description=SmartGate AI Parking System
After=network.target mariadb.service

[Service]
User=pi
WorkingDirectory=/opt/smartgate
ExecStart=/opt/smartgate/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- [ ] **12.4** Database backup cron: daily mysqldump, 30-day rotation
- [ ] **12.5** Log rotation: logrotate config for app + access logs
- [ ] **12.6** Security audit: parameterized queries, CSRF, .env perms, no secrets in git
- [ ] **12.7** Performance tuning: MySQL indices, connection pool, frame pipeline profiling
- [ ] **12.8** Load test: 50 concurrent plate reads, 20 dashboard users
- [ ] **12.9** Full integration test: entry → DB → GPIO → map → bot → response → update
- [ ] **12.10** Documentation: admin guide, user guide, API docs
- [ ] **12.11** Final commit and tag: `v1.0.0`
