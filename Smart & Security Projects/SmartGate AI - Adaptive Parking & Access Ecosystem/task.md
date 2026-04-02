# 🏷️ SmartGate AI — Task List

## Phase 1: ALPR Core Engine (Days 1–3)

- [ ] Set up Pi Camera / USB Webcam with OpenCV
- [ ] Install and configure PaddleOCR (or EasyOCR)
- [ ] Download/train YOLOv8n plate detection model
- [ ] Build `alpr_engine.py`:
  - [ ] Camera frame capture loop
  - [ ] YOLOv8 plate region detection
  - [ ] Crop plate region from frame
  - [ ] PaddleOCR text extraction
  - [ ] Confidence scoring and filtering
  - [ ] Plate image saving to `data/plates/`
- [ ] Build plate text normalization (strip spaces, uppercase)
- [ ] Benchmark accuracy: test with 50+ plate images
- [ ] Add .env toggles: `ALPR_CONFIDENCE_THRESHOLD`, `ALPR_SAVE_PLATE_IMAGES`
- [ ] Unit tests: plate detection, OCR accuracy

## Phase 2: Database & Employee Management (Days 3–4)

- [ ] Install MariaDB/MySQL on Pi
- [ ] Create `init_db.py` with full schema (10 tables)
- [ ] Build database connection pool module
- [ ] Employee CRUD:
  - [ ] Create employee with plate(s)
  - [ ] Update employee details
  - [ ] Deactivate employee (soft delete)
  - [ ] List employees with filter/search
- [ ] Plate CRUD:
  - [ ] Add/remove plates per employee
  - [ ] Mark primary plate
  - [ ] EV flag per plate
- [ ] Parking spot CRUD:
  - [ ] Define spots with SVG coordinates
  - [ ] Assign/unassign employees to spots
  - [ ] Zone management (standard/ev/disabled/vip/guest)
- [ ] Seed sample data script
- [ ] Database migration strategy document
- [ ] Unit tests: CRUD operations, constraints

## Phase 3: GPIO Gate Control (Days 4–5)

- [ ] Build `gpio_controller.py`:
  - [ ] Initialize all pins (LED Green/Red/Yellow, Relay ×2, Buzzer)
  - [ ] `grant_access()` → Green LED + Relay pulse
  - [ ] `deny_access()` → Red LED + Buzzer
  - [ ] `pending_verification()` → Yellow LED blink
  - [ ] `reset_all()` → All off
  - [ ] Configurable relay pulse duration from .env
  - [ ] Gate open hold timer (auto-close after N seconds)
- [ ] Build `nfc_reader.py`:
  - [ ] RC522 SPI initialization
  - [ ] Continuous UID polling loop
  - [ ] Badge UID → employee lookup
  - [ ] NFC as fallback when ALPR fails
- [ ] Wire up hardware on breadboard
- [ ] Test LED, relay, buzzer individually
- [ ] Integration test: plate detect → GPIO trigger
- [ ] Integration test: NFC badge → GPIO trigger

## Phase 4: Web Dashboard MVP (Days 5–7)

- [ ] Set up Flask application structure
- [ ] Authentication:
  - [ ] Login page with bcrypt password verification
  - [ ] Rate limiting (10 attempts / 15 min)
  - [ ] Session management (24h expiry)
  - [ ] CSRF protection
- [ ] Dashboard pages:
  - [ ] Main parking map (SVG) with color-coded spots
  - [ ] Real-time updates via Flask-SocketIO
  - [ ] Access log table (paginated, searchable)
  - [ ] Employee management (list, add, edit, deactivate)
  - [ ] Plate management per employee
  - [ ] Spot assignment page
  - [ ] Settings page (feature toggles, GPIO config)
- [ ] SVG parking map:
  - [ ] Render spots from DB (x, y, w, h, label)
  - [ ] Color coding: 🔴 occupied, 🟢 free, 🟡 pending, ⚪ reserved
  - [ ] Click spot → show details (employee alias, entry time)
  - [ ] Real-time updates via WebSocket
- [ ] Dark theme CSS
- [ ] Camera live-feed embed on dashboard
- [ ] Mobile-responsive layout
- [ ] Unit tests: auth, routes, SocketIO events

## Phase 5: Teams/Google Integration (Days 7–9)

- [ ] Microsoft Teams (Graph API):
  - [ ] Register Azure AD application
  - [ ] Configure required permissions (Presence.Read.All)
  - [ ] Build MSAL token acquisition flow
  - [ ] Build `presence_checker.py`:
    - [ ] Batch presence query for all Teams-linked employees
    - [ ] Map Teams status → spot status:
      - [ ] Available/InACall/InAMeeting + no car → 🟡 YELLOW
      - [ ] Away/BeRightBack + no car → ⚪ GREY (commuting)
      - [ ] Offline + no car → ⚪ GREY
    - [ ] APScheduler job: poll every N minutes
- [ ] Google Calendar API:
  - [ ] Create Google Cloud project + credentials
  - [ ] Build calendar event checker (WFH events)
  - [ ] Build presence status derivation
- [ ] Dashboard: show presence source icon per spot
- [ ] .env toggles: `ENABLE_TEAMS_INTEGRATION`, `ENABLE_GOOGLE_INTEGRATION`
- [ ] Unit tests: mock Graph API, mock Calendar API

## Phase 6: Bot Notifications (Days 9–10)

- [ ] Multi-language message templates:
  - [ ] English: "Are you in Home Office today? Can we free your spot?"
  - [ ] German: "Bist du heute im Home Office? Können wir deinen Parkplatz freigeben?"
  - [ ] Italian: "Sei in Home Office oggi? Possiamo liberare il tuo parcheggio?"
  - [ ] French: "Êtes-vous en télétravail aujourd'hui ? Pouvons-nous libérer votre place ?"
  - [ ] Spanish: "¿Estás en Home Office hoy? ¿Podemos liberar tu plaza?"
- [ ] Telegram bot:
  - [ ] Create bot via BotFather
  - [ ] Send question with inline keyboard (Yes/No)
  - [ ] Webhook handler for responses
  - [ ] Update spot status based on reply
- [ ] WhatsApp Business API:
  - [ ] Message template registration
  - [ ] Send/receive via API
  - [ ] Webhook handler
- [ ] Teams bot (Adaptive Card):
  - [ ] Send actionable card with buttons
  - [ ] Process card action callback
- [ ] Response timeout logic:
  - [ ] No response after 30 min → keep spot as 🟡
  - [ ] Dashboard shows "No Response" indicator
- [ ] .env toggles per channel
- [ ] Unit tests: template rendering, response handling

## Phase 7: Shared Spots & Shift Logic (Days 10–11)

- [ ] Build schedule management:
  - [ ] CRUD for spot_schedules table
  - [ ] Dashboard calendar view (week view with spots)
  - [ ] Visual drag-and-drop assignment (nice-to-have)
- [ ] Shift authorization logic:
  - [ ] Check day_of_week + shift when plate detected
  - [ ] If plate matches schedule → authorize
  - [ ] If conflict (two plates for same slot) → priority field
- [ ] Spot sharing rules:
  - [ ] User A: Mon/Fri, User B: Tue/Wed/Thu
  - [ ] Auto-resolve current shift owner on entry
- [ ] Dashboard: schedule overview per spot
- [ ] Unit tests: shift authorization, conflict resolution

## Phase 8: HR Time-Tracking (Days 11–12)

- [ ] Build `hr_tracker.py`:
  - [ ] On entry: record first_entry in work_hours
  - [ ] On exit: update last_exit
  - [ ] Calculate total_minutes, break_minutes, net_minutes
  - [ ] Break detection: exit < 30 min → break (configurable)
  - [ ] Anomaly detection:
    - [ ] Early departure (before HR_WORK_DAY_END)
    - [ ] Late arrival (after HR_WORK_DAY_START + threshold)
    - [ ] No exit logged (end of day → flag)
    - [ ] Short day (< HR_MIN_WORK_HOURS)
- [ ] Alert notifications:
  - [ ] Early departure → notify employee + optional manager
  - [ ] No exit → end-of-day reminder
- [ ] Dashboard HR page:
  - [ ] Daily attendance table
  - [ ] Weekly summary chart
  - [ ] Filter by employee/department/cost center
- [ ] CSV export endpoint
- [ ] .env toggles: alert thresholds, notify manager
- [ ] Unit tests: hour calculations, anomaly detection

## Phase 9: EV Billing Module (Days 12–13)

- [ ] Build `ev_billing.py`:
  - [ ] Dedicated camera monitoring EV charging bays
  - [ ] Plate-in-bay detection (check plate position vs bay coordinates)
  - [ ] Session start: plate enters EV bay → create ev_session
  - [ ] Session end: plate leaves bay → end session, calculate cost
  - [ ] Cost = duration × EV_KWH_RATE
- [ ] Visual guidance:
  - [ ] On entry: if plate.is_ev → highlight recommended EV spot on map
  - [ ] Dashboard: EV spot status with charging duration
- [ ] Unauthorized EV bay detection:
  - [ ] Non-DB plate in EV bay → alert supervisor
  - [ ] Non-EV plate in EV bay → gentle notification
- [ ] Dashboard EV page:
  - [ ] Active charging sessions
  - [ ] Session history with costs
  - [ ] Monthly billing summary per employee
- [ ] Unit tests: session logic, cost calculation

## Phase 10: Analytics & Reports (Days 13–14)

- [ ] Build analytics module:
  - [ ] Peak-hour occupancy calculation
  - [ ] Heatmap data: hour × day_of_week matrix
  - [ ] Average occupancy rate per zone
  - [ ] Most/least used spots ranking
- [ ] Dashboard analytics page:
  - [ ] Occupancy chart (Chart.js line/bar)
  - [ ] Heatmap visualization (color grid)
  - [ ] Zone utilization pie chart
  - [ ] Trends comparison (week-over-week)
- [ ] Build `report_generator.py`:
  - [ ] Monthly attendance PDF (reportlab):
    - [ ] Per employee: days present, total hours, anomalies
    - [ ] Per department summary
    - [ ] Parking utilization stats
  - [ ] Excel export (openpyxl):
    - [ ] Raw work hours data
    - [ ] EV billing records
    - [ ] Access log extract
  - [ ] APScheduler: auto-generate on 1st of month
- [ ] .env: `REPORT_SCHEDULE_CRON`, `REPORT_OUTPUT_DIR`
- [ ] Unit tests: data aggregation, report generation

## Phase 11: Advanced Features (Days 14–16)

- [ ] Guest management:
  - [ ] Employee registers guest plate + validity period
  - [ ] Dashboard guest page with active/expired guests
  - [ ] Guest access limit enforcement
- [ ] QR visitor pass:
  - [ ] Generate QR code with unique token
  - [ ] Scan QR at gate (pyzbar) → validate token → authorize
  - [ ] Token expiry enforcement
- [ ] Emergency vehicle DB:
  - [ ] Priority plates table (ambulance, fire, police)
  - [ ] Auto-open with zero delay
  - [ ] Alert dashboard: "Emergency vehicle entered"
- [ ] Violation detection:
  - [ ] Wrong-spot: plate in spot assigned to someone else
  - [ ] Double-parking: CV detection of obstruction (nice-to-have)
  - [ ] Disabled-zone: non-authorized plate in disabled spot
  - [ ] Notification to violator + supervisor
- [ ] LDAP/Azure AD sync:
  - [ ] Query LDAP for employee list
  - [ ] Auto-create/update employee records
  - [ ] Map LDAP fields to DB columns
  - [ ] Scheduled sync job
- [ ] REST API:
  - [ ] API key authentication middleware
  - [ ] Rate limiting
  - [ ] OpenAPI documentation
  - [ ] All endpoints from TSD
- [ ] Multi-gate:
  - [ ] Gate node registration
  - [ ] Central server aggregation
  - [ ] Per-gate dashboard view
- [ ] Night mode:
  - [ ] Auto-switch to IR camera between NIGHT_MODE_START/END
  - [ ] IR LED GPIO control
  - [ ] Adjusted ALPR thresholds for IR images
- [ ] GDPR purge:
  - [ ] Scheduled job: delete logs older than GDPR_RETENTION_DAYS
  - [ ] Anonymize plate numbers in old records
  - [ ] Purge plate images
- [ ] Sound deterrent:
  - [ ] Buzzer patterns (short-short-long for unauthorized)
  - [ ] Configurable duration and pattern
- [ ] Multi-language dashboard (i18n):
  - [ ] Extract all strings to translation files
  - [ ] Language selector in settings
  - [ ] Support EN/DE/IT/FR/ES

## Phase 12: Hardening & Deployment (Days 16–18)

- [ ] HTTPS:
  - [ ] Generate self-signed certificate (or Let's Encrypt)
  - [ ] Configure flask/gunicorn with TLS
- [ ] Reverse proxy:
  - [ ] nginx configuration with SSL termination
  - [ ] WebSocket proxy for SocketIO
- [ ] systemd service:
  - [ ] Create `smartgate.service` unit file
  - [ ] Enable on boot
  - [ ] Restart policy on failure
- [ ] Database backup:
  - [ ] mysqldump cron job (daily)
  - [ ] Backup rotation (keep last 30)
- [ ] Log management:
  - [ ] Application log rotation (logrotate)
  - [ ] Access log archiving
- [ ] Performance:
  - [ ] MySQL query optimization (EXPLAIN)
  - [ ] Connection pooling verification
  - [ ] Camera frame pipeline profiling
  - [ ] SocketIO event batching
- [ ] Security audit:
  - [ ] Check all SQL uses parameterized queries
  - [ ] Verify CSRF on all POST forms
  - [ ] Audit .env permissions (600)
  - [ ] Verify no secrets in git history
- [ ] Load testing:
  - [ ] Simulate 50 concurrent plate reads
  - [ ] Simulate 20 concurrent dashboard users
  - [ ] Stress test SocketIO broadcast
- [ ] Documentation:
  - [ ] API documentation (OpenAPI/Swagger)
  - [ ] Admin guide (setup, backup, troubleshooting)
  - [ ] User guide (dashboard usage)
- [ ] Final integration test:
  - [ ] Full workflow: plate → DB → GPIO → dashboard → bot → response → spot update
  - [ ] Edge cases: unknown plate, expired guest, shift conflict, EV unauthorized
  - [ ] Failover: NFC when camera fails, manual override
