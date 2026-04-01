# TSD — Solar Panel Follower

## 1 · Scope

Build an intelligent dual-axis solar tracking system for Raspberry Pi that uses light-dependent resistor (LDR) sensors, servo motors, and an I2C ADC to follow the sun and maximize energy harvest from a small solar panel. The system includes real-time power monitoring (INA219), astronomical tracking fallback, ML-based angle prediction, energy logging and analytics, weather-aware tracking, and a web dashboard for monitoring and control.

### In scope

| Area | Details |
|---|---|
| **Dual-axis tracking** | Pan (azimuth, 0°–180°) and tilt (elevation, 0°–90°) using two SG90 or MG996R servo motors |
| **LDR sensor array** | 4 LDR photoresistors in quadrant arrangement with ADS1115 16-bit ADC (I2C) |
| **Power monitoring** | INA219 I2C sensor measuring solar panel voltage, current, and power output in real time |
| **Astronomical tracking** | pvlib-based solar position calculation as fallback when LDR readings are unreliable (clouds, night) |
| **ML angle prediction** | scikit-learn regression model trained on historical data to predict optimal angles |
| **Energy logging** | SQLite database recording power, angles, LDR readings, weather, and tracking mode every 60 seconds |
| **Energy analytics** | Daily/weekly/monthly charts, total Wh, tracking-vs-fixed comparison, angle heatmap, CSV export |
| **Weather integration** | OpenWeatherMap API (free tier) for cloud-aware tracking decisions |
| **Servo sleep mode** | Park panel at sunrise angle overnight, disable PWM to save power |
| **Web dashboard** | Flask + WebSocket real-time interface with power gauges, angle display, charts, and manual control |
| **Authentication** | Session-based login with bcrypt password hashing and rate limiting |
| **Mock hardware** | Full development mode on laptop with simulated sensors and servos |
| **Deployment** | rsync-based deploy script to Raspberry Pi; systemd service |

### Out of scope

| Area | Reason |
|---|---|
| Battery charge controller | Requires specialized hardware (MPPT/PWM charge controller) outside software scope |
| Grid-tie inverter | Industrial electrical engineering; safety and regulatory concerns |
| Panel manufacturing | Hardware engineering; pre-made panels are used |
| Production-grade mechanical frame | Aluminum extrusion or welded steel design; documented as upgrade path only |
| Multiple panel arrays | Single-panel system; multi-panel coordination is a future project |
| Mobile app | Web dashboard is accessible from mobile browsers; native app not needed |

---

## 2 · MVP features

### 2.1 — Dual-axis LDR tracking

**Priority: P0 — Must have**

The core tracking system that reads 4 LDR sensors and adjusts two servos to point the solar panel toward the brightest light source.

- Read 4 LDR values from ADS1115 ADC via I2C.
- Calculate brightness differences: top-bottom (tilt), left-right (pan).
- If difference exceeds configurable threshold → move the corresponding servo.
- Smooth servo movement (step-by-step, not instant jumps) to reduce mechanical stress.
- Configurable tracking interval (default: 5 seconds).
- Dead-zone: no movement when all 4 readings are within threshold (panel aligned).
- Servo angle limits configurable in `.env`.
- Hardware PWM via `pigpio` for jitter-free movement; software PWM fallback.

### 2.2 — Power monitoring (INA219)

**Priority: P0 — Must have**

Real-time measurement of the solar panel's electrical output.

- Read voltage (V), current (mA), and power (mW) from INA219 via I2C.
- Shared I2C bus with ADS1115 (different addresses: 0x40 vs 0x48).
- Sample every tracking cycle (5 seconds).
- Push readings to dashboard via WebSocket.
- Display live gauges: voltage, current, power.
- Power history chart (last hour).

### 2.3 — Energy logging (SQLite)

**Priority: P0 — Must have**

Persistent storage of all sensor data for analytics and ML training.

**Database schema:**

**Table: `energy_log`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment ID |
| `timestamp` | DATETIME | UTC timestamp |
| `voltage_v` | REAL | Panel voltage (V) |
| `current_ma` | REAL | Panel current (mA) |
| `power_mw` | REAL | Panel power (mW) |
| `pan_angle` | REAL | Pan servo angle (degrees) |
| `tilt_angle` | REAL | Tilt servo angle (degrees) |
| `ldr_tl` | INTEGER | LDR top-left raw ADC value |
| `ldr_tr` | INTEGER | LDR top-right raw ADC value |
| `ldr_bl` | INTEGER | LDR bottom-left raw ADC value |
| `ldr_br` | INTEGER | LDR bottom-right raw ADC value |
| `tracking_mode` | TEXT | Current mode: ldr, astronomical, ml, manual |
| `weather_condition` | TEXT | Weather (if enabled), e.g., "clear", "cloudy" |
| `temperature_c` | REAL | Ambient temperature (if weather enabled) |
| `cloud_cover_pct` | INTEGER | Cloud cover percentage (if weather enabled) |

**Table: `daily_summary`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment ID |
| `date` | DATE | Summary date |
| `total_wh` | REAL | Total watt-hours harvested |
| `peak_power_mw` | REAL | Maximum power reading |
| `avg_power_mw` | REAL | Average power during daylight |
| `sunrise_time` | TIME | First tracking activity |
| `sunset_time` | TIME | Last tracking activity |
| `dominant_mode` | TEXT | Most-used tracking mode |

**Table: `settings`**

| Column | Type | Description |
|---|---|---|
| `key` | TEXT PK | Setting name |
| `value` | TEXT | Setting value (JSON-encoded) |
| `updated_at` | DATETIME | Last update time |

- Log interval configurable (default: 60 seconds).
- Data retention: no automatic deletion (SQLite file grows; user can export and purge).
- Database stored in `data/energy_log.db` (excluded from git and rsync).

### 2.4 — Web dashboard

**Priority: P0 — Must have**

Real-time web interface for monitoring and control.

**Pages:**

| Page | Components |
|---|---|
| **Dashboard** | Live power gauge (V, mA, mW), pan/tilt angle display, LDR quadrant heatmap, sun position compass, tracking status, system info (CPU temp, uptime) |
| **Energy** | Daily energy curve (Chart.js), daily total Wh, weekly/monthly trend, best-angle heatmap |
| **Tracking** | Mode selector (LDR/Astronomical/ML/Manual), manual servo sliders, Track Now / Park / Wake buttons, LDR calibration |
| **Settings** | Location (lat/lon/tz), servo limits, tracking interval, weather API config, change password |
| **Login** | Username + password form |

- **WebSocket:** Real-time push of sensor data (every 5 seconds).
- **Responsive:** Works on desktop and mobile browsers.
- **Chart.js:** Embedded via CDN for all charts and gauges.
- **Dark theme** consistent with other projects in this repository.

### 2.5 — Authentication

**Priority: P0 — Must have**

- Username/password from `.env` (default: admin/changeme).
- Password hashed with bcrypt on first startup.
- Session-based (Flask session, cookie-encrypted with `SESSION_SECRET`).
- Rate limiting: 10 login attempts per 15 minutes (by IP).
- Session expiry: 24 hours.
- Settings page allows password change.
- All API endpoints require authentication (except `/login`).

### 2.6 — Mock hardware mode

**Priority: P0 — Must have**

Development mode that simulates all hardware for laptop development.

- Auto-detected: if I2C devices are not available, switch to mock hardware.
- Simulated LDR readings: follow a sine-wave pattern simulating sun movement.
- Simulated INA219 readings: correlated with LDR (brighter = more power).
- Virtual servos: log angle changes to console, display on dashboard.
- All dashboard features work identically in mock mode.

### 2.7 — Deployment and systemd service

**Priority: P0 — Must have**

- `deploy/deploy_to_pi.sh`: rsync project files to Pi, create venv, install deps.
- `scripts/setup-i2c.sh`: enable I2C, install tools.
- `scripts/setup-servo.sh`: install and configure pigpio daemon.
- `scripts/calibrate-ldr.sh`: interactive LDR calibration routine.
- systemd service unit for auto-start on boot (documented in README).

---

## 3 · Nice-to-have features

Features that require paid services or third-party hardware. Implemented only if the user opts in.

### 3.1 — Weather-aware tracking (OpenWeatherMap)

**Requires:** Free API key from [openweathermap.org](https://openweathermap.org/) (1,000 calls/day).

- Poll weather every 30 minutes.
- If cloud cover > 80%: switch to astronomical mode (LDR is unreliable in heavy overcast).
- If clear sky: use LDR tracking for maximum precision.
- Log weather conditions alongside energy data for ML training.
- Dashboard shows current weather and forecast.

### 3.2 — ML-based angle prediction

**Requires:** ≥7 days of logged energy data; computational time for training.

- Train a scikit-learn regression model (RandomForest or GradientBoosting) on historical data.
- Features: hour-of-day, day-of-year, temperature, cloud cover.
- Target: pan and tilt angles that produced maximum power.
- Predict optimal angle for current conditions.
- Retrain periodically (weekly cron job).
- `scripts/train-model.sh` triggers training.
- Set `TRACKING_MODE=ml` to enable.

### 3.3 — Stepper motor upgrade

**Requires:** NEMA 17 stepper motors ($10–15 each) + DRV8825 drivers ($3–5 each).

- Replace SG90 servos with stepper motors for:
  - Higher torque (heavier panels).
  - 360° rotation (full azimuth range).
  - Precise microstepping.
- Software abstraction: `servo_controller.py` has a common interface; swap implementation.
- Documented as upgrade path in README.

---

## 4 · High-level architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SOLAR PANEL FOLLOWER                             │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    TRACKING LOOP (every 5s)                      │   │
│  │                                                                  │   │
│  │  ┌────────────┐   ┌──────────────────┐   ┌──────────────────┐   │   │
│  │  │ LDR Array  │──→│ Tracker Manager  │──→│ Servo Controller │   │   │
│  │  │ (ADS1115)  │   │                  │   │ (pigpio PWM)     │   │   │
│  │  └────────────┘   │  Mode selector:  │   └──────────────────┘   │   │
│  │                    │  - LDR tracking  │                          │   │
│  │  ┌────────────┐   │  - Astronomical  │                          │   │
│  │  │ pvlib      │──→│  - ML prediction │                          │   │
│  │  │ (solar pos)│   │  - Manual        │                          │   │
│  │  └────────────┘   └────────┬─────────┘                          │   │
│  │                             │                                    │   │
│  │  ┌────────────┐            │                                    │   │
│  │  │ ML Model   │──→─────────┘                                    │   │
│  │  │ (sklearn)  │                                                 │   │
│  │  └────────────┘                                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      MONITORING LAYER                            │   │
│  │                                                                  │   │
│  │  ┌────────────┐   ┌──────────────────┐   ┌──────────────────┐   │   │
│  │  │ INA219     │──→│ Energy Logger    │──→│ SQLite DB        │   │   │
│  │  │ (V, A, W)  │   │ (60s interval)   │   │ (energy_log.db)  │   │   │
│  │  └────────────┘   └──────────────────┘   └──────────────────┘   │   │
│  │                                                                  │   │
│  │  ┌────────────┐   ┌──────────────────┐                          │   │
│  │  │ Weather    │──→│ Analytics Service│                          │   │
│  │  │ (OWM API)  │   │ (daily/weekly)   │                          │   │
│  │  └────────────┘   └──────────────────┘                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                       WEB DASHBOARD                              │   │
│  │                                                                  │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │   │
│  │  │ Flask App   │←──→│ SocketIO    │←──→│ Browser (JS/CSS)    │  │   │
│  │  │ (Routes)    │    │ (WebSocket) │    │ Chart.js gauges     │  │   │
│  │  └─────────────┘    └─────────────┘    └─────────────────────┘  │   │
│  │                                                                  │   │
│  │  Pages: Dashboard | Energy | Tracking | Settings | Login         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                       I2C BUS                                    │   │
│  │                                                                  │   │
│  │  GPIO 2 (SDA) ──── ADS1115 (0x48) ──── INA219 (0x40)           │   │
│  │  GPIO 3 (SCL) ──── ADS1115 (0x48) ──── INA219 (0x40)           │   │
│  │                                                                  │   │
│  │  GPIO 18 ─── Pan Servo (PWM ch0)                                │   │
│  │  GPIO 19 ─── Tilt Servo (PWM ch1)                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data flow

```
LDR (×4) → ADS1115 → I2C → Tracker Manager → Servo Controller → Servos
                                   ↑
                          pvlib (astronomical)
                          ML model (scikit-learn)
                          Manual override (dashboard)

Solar Panel → INA219 → I2C → Energy Logger → SQLite → Analytics Service
                                                         ↓
                                               Dashboard (WebSocket)

Weather API → Weather Service → Tracker Manager (mode decision)
                              → Energy Logger (weather data)
```

---

## 5 · Security / Threat model

| # | Threat | Mitigation |
|---|---|---|
| T1 | Credential theft via `.env` file exposure | `.env` excluded from git (`.gitignore`). File permissions `600` on Pi. |
| T2 | Brute-force login attempts | Rate limiting: 10 attempts per 15 minutes per IP. |
| T3 | Session hijacking | `SESSION_SECRET` must be a strong random string. Cookies marked `HttpOnly` and `SameSite`. |
| T4 | Unauthorized servo control | All API endpoints require authentication. |
| T5 | SQL injection on energy data queries | SQLite parameterized queries only. No raw string interpolation. |
| T6 | Weather API key exposure | Key stored in `.env` (not committed). Never returned to the frontend. |
| T7 | I2C bus tampering | Physical access required. Not a practical remote threat. Document physical security. |
| T8 | Servo overdrive / hardware damage | Software angle limits enforced. Configurable min/max in `.env`. |
| T9 | Power brownout from heavy servos | Document: use external 5V supply for MG996R or larger servos. |
| T10 | Unencrypted HTTP | Dashboard runs on local network. Document: use nginx reverse proxy with Let's Encrypt for remote access. |
| T11 | XSS in dashboard | Jinja2 auto-escaping enabled. No raw HTML rendering of user input. |
| T12 | Data exfiltration of energy logs | Energy data is local only. No cloud sync. Export requires authentication. |

See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## 6 · Suggested tech stack

### Backend

| Component | Technology | Justification |
|---|---|---|
| Language | Python 3.11+ | Excellent hardware library ecosystem; consistent with other projects |
| Web framework | Flask 3.1 | Lightweight; Jinja2 templating; sufficient for dashboard |
| WebSocket | Flask-SocketIO | Real-time sensor data push to browser |
| Database | SQLite | Zero-config; file-based; sufficient for single-device logging |
| ADC driver | adafruit-circuitpython-ads1x15 | Official Adafruit library for ADS1115 |
| Power monitor | adafruit-circuitpython-ina219 | Official Adafruit library for INA219 |
| Servo control | pigpio | Hardware PWM for jitter-free servo control |
| Solar position | pvlib | Industry-standard solar position library |
| ML model | scikit-learn | Simple regression models; trains fast on Pi |
| Weather | requests + OpenWeatherMap API | Free tier; simple REST API |
| Authentication | bcrypt + Flask sessions | Password hashing + session cookies |
| Config | python-dotenv | `.env` file for configuration |

### Frontend

| Component | Technology | Justification |
|---|---|---|
| Template engine | Jinja2 (server-side) | No SPA complexity; server-rendered pages |
| Charts | Chart.js 4 (CDN) | Rich, responsive charts; no build step |
| WebSocket client | Socket.IO client (CDN) | Real-time data updates |
| Styling | Custom CSS (dark theme) | Consistent with other projects in this repo |
| Icons | Lucide or similar (CDN) | Lightweight icon set |

### Infrastructure

| Component | Technology | Justification |
|---|---|---|
| Deployment | rsync + SSH | Simple, reliable, matches other projects |
| Process manager | systemd | Built into Raspberry Pi OS; auto-restart on failure |
| PWM daemon | pigpiod | System service for hardware PWM |
| I2C | `/dev/i2c-1` | Standard Raspberry Pi I2C bus |

---

## 7 · Development phases

### Phase 1 — Hardware interface and basic tracking

**Goal:** Read LDR sensors, control servos, achieve basic sun tracking.

| # | Task | Priority |
|---|---|---|
| 1.1 | Set up project structure (folders, `requirements.txt`, `.env.default`) | P0 |
| 1.2 | Implement `adc_reader.py` — read 4 LDR values from ADS1115 via I2C | P0 |
| 1.3 | Implement `servo_controller.py` — control pan/tilt servos via pigpio PWM | P0 |
| 1.4 | Implement `ldr_tracker.py` — calculate brightness differences and servo adjustments | P0 |
| 1.5 | Implement `mock_hardware.py` — simulated ADC and servo for laptop development | P0 |
| 1.6 | Implement main tracking loop (read → calculate → move, every 5s) | P0 |
| 1.7 | Write `scripts/setup-i2c.sh` and `scripts/setup-servo.sh` | P0 |
| 1.8 | Write `scripts/calibrate-ldr.sh` | P1 |
| 1.9 | Unit tests for ADC reader, servo controller, and tracker logic | P1 |

### Phase 2 — Power monitoring and energy logging

**Goal:** Measure power output and log all data to SQLite.

| # | Task | Priority |
|---|---|---|
| 2.1 | Implement `power_monitor.py` — read INA219 voltage, current, power via I2C | P0 |
| 2.2 | Implement `db.py` — SQLite database initialization (create tables) | P0 |
| 2.3 | Implement `energy_logger.py` — log sensor data every 60 seconds | P0 |
| 2.4 | Add daily summary generation (nightly aggregate from `energy_log` to `daily_summary`) | P1 |
| 2.5 | Mock INA219 in `mock_hardware.py` (power correlated with LDR brightness) | P0 |
| 2.6 | Unit tests for power monitor and energy logger | P1 |

### Phase 3 — Web dashboard

**Goal:** Real-time web interface with gauges, charts, and controls.

| # | Task | Priority |
|---|---|---|
| 3.1 | Set up Flask app with Jinja2 templates and SocketIO | P0 |
| 3.2 | Implement authentication (login, session, rate limiting) | P0 |
| 3.3 | Build `dashboard.html` — live power gauges, angle display, LDR heatmap | P0 |
| 3.4 | Build `energy.html` — daily energy curve (Chart.js), daily total Wh | P0 |
| 3.5 | Build `tracking.html` — mode selector, manual servo sliders, Park/Wake buttons | P0 |
| 3.6 | Build `settings.html` — location, servo limits, tracking interval, password | P0 |
| 3.7 | Build `layout.html` — sidebar navigation, dark theme | P0 |
| 3.8 | Implement WebSocket push for real-time sensor data | P0 |
| 3.9 | Responsive layout for mobile browsers | P1 |
| 3.10 | Integration tests for dashboard routes and WebSocket | P1 |

### Phase 4 — Astronomical tracking and sleep mode

**Goal:** Fallback tracking when LDR is unreliable; overnight power saving.

| # | Task | Priority |
|---|---|---|
| 4.1 | Implement `astro_tracker.py` — solar position calculation using pvlib | P0 |
| 4.2 | Implement `tracker_manager.py` — mode coordinator (LDR, astronomical, ML, manual) | P0 |
| 4.3 | Auto-fallback: switch to astronomical when LDR readings are all below threshold | P0 |
| 4.4 | Implement servo sleep mode — park at sunrise angle, disable PWM overnight | P1 |
| 4.5 | Sunrise wake — resume tracking when LDR detects light or astronomical sunrise time | P1 |
| 4.6 | Add tracking mode display and controls to dashboard | P0 |
| 4.7 | Unit tests for astronomical tracker and mode manager | P1 |

### Phase 5 — Weather integration and ML prediction

**Goal:** Weather-aware tracking and ML-based angle optimization.

| # | Task | Priority |
|---|---|---|
| 5.1 | Implement `weather_service.py` — OpenWeatherMap API integration | P1 |
| 5.2 | Weather-aware mode switching (heavy clouds → astronomical, clear → LDR) | P1 |
| 5.3 | Log weather conditions in energy_log table | P1 |
| 5.4 | Display weather on dashboard | P1 |
| 5.5 | Implement `ml_predictor.py` — train regression model from energy data | P2 |
| 5.6 | Write `scripts/train-model.sh` | P2 |
| 5.7 | Add ML mode to tracker manager | P2 |
| 5.8 | Unit tests for weather service and ML predictor | P2 |

### Phase 6 — Analytics, deployment, and polish

**Goal:** Energy analytics dashboard, deployment automation, documentation.

| # | Task | Priority |
|---|---|---|
| 6.1 | Implement `analytics_service.py` — weekly/monthly trends, tracking-vs-fixed comparison | P1 |
| 6.2 | Add angle heatmap to Energy page | P1 |
| 6.3 | CSV export endpoint | P1 |
| 6.4 | Write `deploy/deploy_to_pi.sh` | P0 |
| 6.5 | Write systemd service unit (documented in README) | P1 |
| 6.6 | Write `docs/threat_model.md` | P1 |
| 6.7 | Write `task.md` — engineering checklist | P1 |
| 6.8 | End-to-end testing: full tracking loop with mock hardware | P1 |
| 6.9 | Documentation review: README, TSD, task.md | P2 |

---

## 8 · Deliverables

| # | Deliverable | Phase |
|---|---|---|
| D1 | Working dual-axis LDR tracking with servo control | Phase 1 |
| D2 | INA219 power monitoring and SQLite energy logging | Phase 2 |
| D3 | Web dashboard with real-time gauges, charts, and controls | Phase 3 |
| D4 | Astronomical tracking fallback and servo sleep mode | Phase 4 |
| D5 | Weather-aware tracking and ML angle prediction | Phase 5 |
| D6 | Energy analytics, deployment script, systemd service, documentation | Phase 6 |
