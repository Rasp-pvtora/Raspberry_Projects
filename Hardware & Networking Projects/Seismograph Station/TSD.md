# Technical Specification Document — Seismograph Station

## 1. Project Scope

A Raspberry Pi–based seismograph station that continuously records seismic data from a geophone or ADXL345 accelerometer (via ADS1115 ADC), detects earthquake events using the STA/LTA algorithm, and visualizes real-time seismograms on a Flask web dashboard. Supports MiniSEED data format, citizen seismology network contribution (Raspberry Shake, IRIS, USGS), historical event replay, spectrogram analysis, and multi-channel alerts. All features are toggleable via `.env`. Uses ObsPy for seismological data processing.

**Target hardware:** Raspberry Pi 4 / Pi 5 with ADXL345 + ADS1115 (DIY) or Raspberry Shake RS1D/RS3D (professional).

**Citizen science goal:** Contribute seismic data to global networks to improve earthquake detection and research.

---

## 2. Feature Tiers

### P0 — MVP (Must Have)

| Feature | Description |
|---|---|
| Real-time seismogram | Chart.js waveform display via Flask-SocketIO WebSocket |
| STA/LTA detection | ObsPy classic STA/LTA with configurable trigger/detrigger thresholds |
| MiniSEED recording | Continuous data recording in standard seismological format (ObsPy) |
| Web dashboard | Flask dark theme, live waveform, event list, settings |
| Authentication | bcrypt hashing, rate limiting (10/15 min), 24h session |
| Sensor interface | ADXL345 (I2C) and ADS1115 (I2C/ADC) driver support |
| Mock mode | Simulated seismic data (synthetic waveforms) for development |
| Configuration | All features toggleable via `.env` |

### P1 — Nice to Have

| Feature | Description |
|---|---|
| Earthquake early warning | P-wave detection with S-wave arrival time estimation |
| Network contribution | FDSN upload to Raspberry Shake, IRIS |
| Historical event replay | Download and replay USGS earthquake waveform data |
| Spectrogram | Real-time frequency analysis (FFT via scipy) |
| Multi-axis support | 3-axis recording for RS3D or 3x ADXL345 channels |
| Alert system | Email, Telegram bot, GPIO buzzer on earthquake detection |
| Raspberry Shake backend | Native support for RS1D/RS3D UDP data stream |

---

## 3. Database Schema

```sql
-- Detected seismic events
CREATE TABLE seismic_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type      TEXT NOT NULL DEFAULT 'earthquake'
                    CHECK (event_type IN ('earthquake', 'tremor', 'blast', 'noise', 'unknown')),
    sta_lta_ratio   REAL NOT NULL,
    peak_amplitude  REAL,
    magnitude_est   REAL,
    p_wave_time     DATETIME,
    s_wave_time     DATETIME,
    duration_sec    REAL,
    channel         TEXT NOT NULL DEFAULT 'EHZ',
    latitude        REAL,
    longitude       REAL,
    depth_km        REAL,
    distance_km     REAL,
    alert_sent      INTEGER NOT NULL DEFAULT 0,
    notes           TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Raw waveform data (downsampled snapshots for dashboard replay)
CREATE TABLE waveform_data (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER REFERENCES seismic_events(id) ON DELETE CASCADE,
    channel         TEXT NOT NULL DEFAULT 'EHZ',
    start_time      DATETIME NOT NULL,
    end_time        DATETIME NOT NULL,
    sample_rate     REAL NOT NULL,
    num_samples     INTEGER NOT NULL,
    data_blob       BLOB NOT NULL,
    format          TEXT NOT NULL DEFAULT 'float32'
                    CHECK (format IN ('float32', 'int16', 'int32')),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Station configuration and metadata
CREATE TABLE station_config (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    station_code    TEXT NOT NULL DEFAULT 'MYSTA',
    network_code    TEXT NOT NULL DEFAULT 'AM',
    location_code   TEXT NOT NULL DEFAULT '00',
    channel_code    TEXT NOT NULL DEFAULT 'EHZ',
    latitude        REAL,
    longitude       REAL,
    elevation_m     REAL,
    sensor_type     TEXT NOT NULL DEFAULT 'adxl345'
                    CHECK (sensor_type IN ('adxl345', 'ads1115', 'raspberry_shake', 'mock')),
    sample_rate     REAL NOT NULL DEFAULT 100.0,
    description     TEXT,
    installed_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Application settings (key-value)
CREATE TABLE settings (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_events_detected ON seismic_events(detected_at);
CREATE INDEX idx_events_type ON seismic_events(event_type);
CREATE INDEX idx_events_magnitude ON seismic_events(magnitude_est);
CREATE INDEX idx_waveform_event ON waveform_data(event_id);
CREATE INDEX idx_waveform_time ON waveform_data(start_time);
```

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Raspberry Pi (Local)                              │
│                                                                             │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────────┐   ┌──────────────┐ │
│  │ ADXL345/ │──▶│ sensor.py    │──▶│ detector.py     │──▶│ database.py  │ │
│  │ ADS1115/ │   │ I2C / ADC    │   │ STA/LTA (ObsPy) │   │ SQLite       │ │
│  │ RaspShk  │   │ 100 Hz       │   │ P-wave detect   │   └──────┬───────┘ │
│  └──────────┘   └──────────────┘   └────────┬────────┘          │         │
│                                              │                   │         │
│              ┌───────────────────────────────┼───────────────────┤         │
│              │                               │                   │         │
│              ▼                               ▼                   ▼         │
│  ┌──────────────────┐            ┌────────────────┐   ┌────────────────┐  │
│  │ recorder.py      │            │ Flask-SocketIO  │   │ alerts.py      │  │
│  │ MiniSEED writer  │            │ Chart.js wfm    │   │ Email/TG/GPIO  │  │
│  │ (ObsPy)          │            │ Spectrogram     │   │                │  │
│  └──────────────────┘            └────────────────┘   └────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  Flask Web Dashboard (Dark Theme)                    │   │
│  │  ┌───────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────────────┐ │   │
│  │  │ Login     │ │ Seismogram  │ │ Events   │ │ Spectrogram       │ │   │
│  │  │ (bcrypt)  │ │ Live Chart  │ │ List     │ │ FFT Heatmap       │ │   │
│  │  └───────────┘ └─────────────┘ └──────────┘ └───────────────────┘ │   │
│  │  ┌────────────────┐ ┌────────────────┐ ┌──────────────────────┐   │   │
│  │  │ Replay (USGS)  │ │ Network Upload │ │ Settings / Station   │   │   │
│  │  │ Historical     │ │ FDSN / IRIS    │ │ Config & Status      │   │   │
│  │  └────────────────┘ └────────────────┘ └──────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Security Layer                                                      │   │
│  │  • bcrypt auth   • Rate limit: 10 req / 15 min   • 24h sessions   │   │
│  │  • CSRF tokens   • Input validation              • Parameterized Q │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Threat Model

| Threat | Impact | Mitigation |
|---|---|---|
| Unauthorized dashboard access | Data exposure | bcrypt auth, rate limiting, session expiry |
| Session hijacking | Impersonation | Secure cookies, 24h expiry, server-side sessions |
| Brute-force login | Account compromise | Rate limit: 10 attempts / 15 min per IP |
| CSRF attacks | Unauthorized actions | CSRF tokens on all forms |
| SQL injection | Data breach | Parameterized queries only (SQLite `?` placeholders) |
| XSS in dashboard | Script injection | Jinja2 auto-escaping, Content-Security-Policy headers |
| Physical SD card theft | Data exposure | LUKS disk encryption recommended |
| FDSN credential theft | Network abuse | Credentials in `.env` only, not in code or version control |
| Malicious USGS API response | Data poisoning | Validate downloaded waveform data before processing |
| Denial of service | Service outage | Rate limiting, resource limits in systemd |
| I2C bus tampering | Sensor spoofing | Physical security of hardware installation |
| Unencrypted network traffic | Data interception | Nginx reverse proxy with TLS (Let's Encrypt) |

---

## 6. Tech Stack

| Layer | Technology |
|---|---|
| Hardware | Raspberry Pi 4/5, ADXL345 + ADS1115 (DIY) or Raspberry Shake RS1D/RS3D |
| OS | Raspberry Pi OS (64-bit, Bookworm) |
| Runtime | Python 3.11+ |
| Web Framework | Flask 3.x + Flask-SocketIO |
| WebSocket | python-socketio (eventlet or gevent) |
| Templates | Jinja2 (dark theme) |
| Seismology | ObsPy (STA/LTA, MiniSEED, FDSN client) |
| Sensor Drivers | adafruit-circuitpython-adxl34x, adafruit-circuitpython-ads1x15 |
| Signal Processing | numpy, scipy (FFT, filtering) |
| Visualization | Chart.js (client-side waveform / spectrogram) |
| Database | SQLite 3 |
| Auth | bcrypt + Flask sessions |
| Alerts | smtplib (email), requests (Telegram), RPi.GPIO (buzzer) |
| Config | python-dotenv (`.env` file) |
| Process Manager | systemd |
| Deployment | SCP / rsync to `rasp-pi` (192.168.216.90) |

---

## 7. Implementation Phases

### Phase 1 — Foundation & Sensor Interface

- Project scaffolding (directory structure, `.env`, config loader)
- SQLite database initialization with schema
- ADXL345 I2C driver (adafruit-circuitpython-adxl34x)
- ADS1115 ADC driver (adafruit-circuitpython-ads1x15)
- Sensor sampling loop (configurable Hz)
- Mock sensor mode for development
- Basic Flask app skeleton with dark theme

### Phase 2 — Detection & Recording

- STA/LTA earthquake detection via ObsPy
- P-wave arrival detection
- Event recording in SQLite (seismic_events table)
- MiniSEED continuous recording via ObsPy
- File rotation by configurable interval
- Waveform snapshot capture around detected events

### Phase 3 — Dashboard & Authentication

- bcrypt authentication (login page, session management)
- Rate limiting middleware (10 req / 15 min / IP)
- Session expiry (24 hours)
- Live seismogram display (Chart.js via SocketIO)
- Detected events list page with detail view
- Station settings and status page

### Phase 4 — Analysis & Replay

- Spectrogram generation (scipy FFT)
- Spectrogram visualization page (time-frequency heatmap)
- Historical event download from USGS API
- Event replay on dashboard waveform view
- Multi-axis support (3-channel display and recording)
- Comparison view (station data vs. USGS reference)

### Phase 5 — Alerts & Network

- Email alert on earthquake detection (smtplib)
- Telegram bot alert with event details
- GPIO buzzer alert (RPi.GPIO)
- FDSN data upload to Raspberry Shake network
- IRIS data contribution support
- Alert history and management page

### Phase 6 — Hardening & Deployment

- systemd service configuration
- Deploy script (`deploy_to_pi.sh`)
- CSRF protection on all forms
- Content-Security-Policy headers
- Input validation and sanitization audit
- Error handling and logging
- Performance profiling (continuous sampling benchmarks)
- Documentation finalization

---

## 8. Default Environment Configuration

```ini
# .env.default — Seismograph Station

# --- Flask ---
SECRET_KEY=change-me-in-production
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false

# --- Authentication ---
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=
SESSION_EXPIRY_HOURS=24
RATE_LIMIT_MAX=10
RATE_LIMIT_WINDOW_MIN=15

# --- Sensor ---
SENSOR_BACKEND=adxl345
SENSOR_SAMPLE_RATE=100
SENSOR_I2C_BUS=1
ADXL345_ADDRESS=0x53
ADS1115_ADDRESS=0x48
ADS1115_GAIN=1
ADS1115_CHANNEL=0

# --- Seismogram Display ---
SEISMOGRAM_ENABLED=true
SEISMOGRAM_WINDOW_SEC=60

# --- STA/LTA Detection ---
DETECTION_ENABLED=true
STA_WINDOW_SEC=1.0
LTA_WINDOW_SEC=30.0
STA_LTA_TRIGGER=3.5
STA_LTA_DETRIGGER=1.5

# --- Earthquake Early Warning ---
EARLY_WARNING_ENABLED=false
P_WAVE_THRESHOLD=2.0

# --- MiniSEED Recording ---
RECORDING_ENABLED=true
MSEED_PATH=data/mseed
MSEED_FILE_DURATION_SEC=3600
STATION_CODE=MYSTA
NETWORK_CODE=AM
LOCATION_CODE=00
CHANNEL_CODE=EHZ

# --- Network Contribution ---
NETWORK_UPLOAD_ENABLED=false
FDSN_SERVER_URL=
RASPBERRY_SHAKE_KEY=
IRIS_UPLOAD_ENABLED=false
IRIS_STATION_ID=

# --- Historical Replay ---
REPLAY_ENABLED=true
USGS_API_URL=https://earthquake.usgs.gov/fdsnws/event/1/query

# --- Spectrogram ---
SPECTROGRAM_ENABLED=true
SPECTROGRAM_WINDOW_SEC=300
SPECTROGRAM_NFFT=256

# --- Multi-Axis ---
MULTI_AXIS_ENABLED=false

# --- Alerts: Email ---
ALERT_EMAIL_ENABLED=false
ALERT_EMAIL_SMTP=
ALERT_EMAIL_PORT=587
ALERT_EMAIL_USER=
ALERT_EMAIL_PASS=
ALERT_EMAIL_TO=

# --- Alerts: Telegram ---
ALERT_TELEGRAM_ENABLED=false
ALERT_TELEGRAM_BOT_TOKEN=
ALERT_TELEGRAM_CHAT_ID=

# --- Alerts: GPIO Buzzer ---
ALERT_GPIO_ENABLED=false
ALERT_GPIO_PIN=17
ALERT_BUZZER_DURATION_SEC=5

# --- Database ---
DB_PATH=data/seismo.db

# --- Development ---
MOCK_MODE=false
```

---

## 9. Deliverables

| Deliverable | Format | Description |
|---|---|---|
| `app.py` | Python | Flask application entry point with SocketIO |
| `config.py` | Python | `.env` loader, feature flags, validation |
| `auth.py` | Python | bcrypt auth, rate limiting, session management |
| `sensor.py` | Python | ADXL345 / ADS1115 / Raspberry Shake sensor interface |
| `detector.py` | Python | STA/LTA earthquake detection engine (ObsPy) |
| `recorder.py` | Python | MiniSEED continuous recorder (ObsPy) |
| `network.py` | Python | FDSN upload to Raspberry Shake, IRIS |
| `alerts.py` | Python | Email, Telegram, GPIO buzzer alert system |
| `replay.py` | Python | USGS historical event download & replay |
| `spectrogram.py` | Python | FFT spectral analysis and spectrogram generation |
| `database.py` | Python | SQLite schema, CRUD, event queries |
| `templates/` | HTML/Jinja2 | Dark theme dashboard pages |
| `static/` | CSS/JS | Styles + Chart.js waveform client |
| `deploy/deploy_to_pi.sh` | Bash | SCP deploy + service restart |
| `tests/` | Python | Unit + integration tests |
| `requirements.txt` | Text | Pinned Python dependencies |
| `.env.example` | Text | Environment variable template |
| `README.md` | Markdown | Full project documentation |
