# Implementation Plan — Seismograph Station

## Phase 1 — Foundation & Sensor Interface

### Step 1.1 — Project Scaffolding

- [ ] Create directory structure:
  ```
  mkdir -p static/css static/js templates data/mseed deploy tests
  ```
- [ ] Create `requirements.txt`:
  ```
  flask>=3.0
  flask-socketio>=5.3
  obspy>=1.4
  adafruit-circuitpython-adxl34x>=1.12
  adafruit-circuitpython-ads1x15>=2.2
  numpy>=1.26
  scipy>=1.12
  bcrypt>=4.1
  python-dotenv>=1.0
  requests>=2.31
  eventlet>=0.35
  Jinja2>=3.1
  RPi.GPIO>=0.7
  ```
- [ ] Create `.env.example` with all variables (reference TSD §8)
- [ ] Create `.gitignore` (exclude `data/`, `.env`, `__pycache__/`, `venv/`)

### Step 1.2 — Configuration Loader

- [ ] Implement `config.py`:
  - Load `.env` via `python-dotenv`
  - Parse all feature flags as booleans
  - Parse numeric values (port, sample rate, STA/LTA windows, thresholds)
  - Parse hex values (I2C addresses)
  - Validate required paths exist (MSEED output directory)
  - Export a `Config` dataclass or dict for app-wide use

**Checkpoint:** `python -c "from config import Config; c = Config(); print(c)"` prints loaded config.

### Step 1.3 — Database Layer

- [ ] Implement `database.py`:
  - `init_db()` — create tables if not exist (seismic_events, waveform_data, station_config, settings)
  - `insert_event(type, sta_lta_ratio, peak_amplitude, magnitude, channel)` → event_id
  - `insert_waveform(event_id, channel, start_time, end_time, sample_rate, data_blob)` → waveform_id
  - `get_event(event_id)` → dict
  - `list_events(event_type, limit, offset)` → list
  - `get_station_config()` → dict
  - `update_station_config(...)` → None
  - `get_setting(key)` / `set_setting(key, value)`
  - Use parameterized queries (`?` placeholders) throughout

**Checkpoint:** `python -c "from database import init_db; init_db()"` creates `data/seismo.db` with correct schema.

### Step 1.4 — Sensor Interface

- [ ] Implement `sensor.py`:
  - `ADXL345Sensor` class:
    - Initialize via adafruit-circuitpython-adxl34x over I2C
    - `read()` → `(x, y, z)` acceleration values in m/s²
    - Configure range and data rate
  - `ADS1115Sensor` class:
    - Initialize via adafruit-circuitpython-ads1x15 over I2C
    - `read()` → voltage value from analog geophone
    - Configure gain and channel
  - `RaspberryShakeSensor` class:
    - Listen for UDP packets from RS1D/RS3D
    - Parse Raspberry Shake data format
    - `read()` → sample value(s)
  - `MockSensor` class:
    - Generate synthetic seismic waveforms (background noise + occasional P/S-wave arrivals)
    - Use numpy for realistic signal generation
  - `SensorLoop` class:
    - Runs in background thread at `SENSOR_SAMPLE_RATE` Hz
    - Fills a numpy ring buffer with raw samples
    - Exposes `get_buffer(window_sec)` → numpy array

**Checkpoint:** `python sensor.py` reads 5 seconds of data from ADXL345 and prints min/max/mean values.

### Step 1.5 — Flask Skeleton

- [ ] Implement basic `app.py`:
  - Flask app with SocketIO
  - Load config
  - Initialize database
  - Dark theme base template (`templates/base.html`)
  - Index route redirects to dashboard
- [ ] Create `static/css/style.css` — dark background, green traces, card layout (seismograph aesthetic)
- [ ] Create `static/js/app.js` — SocketIO client connection + Chart.js initialization

**Checkpoint:** `python app.py` starts on port 5000, browser shows dark-themed placeholder page.

---

## Phase 2 — Detection & Recording

### Step 2.1 — STA/LTA Earthquake Detection

- [ ] Implement `detector.py`:
  - `STALTADetector` class:
    - Initialize with STA/LTA window sizes and trigger/detrigger thresholds
    - `process(data_buffer)` → list of `{ triggered, sta_lta_ratio, trigger_index }`
    - Uses ObsPy `classic_sta_lta()` function
    - Tracks trigger/detrigger state machine
  - `PWaveDetector` class:
    - Detect P-wave first arrival via amplitude/frequency change
    - Estimate S-wave arrival time from P-S time difference
    - `detect(data_buffer)` → `{ p_time, estimated_s_time, estimated_distance_km }`
  - `MockDetector` — generates periodic synthetic triggers

**Checkpoint:** Feed synthetic earthquake waveform to `STALTADetector`, verify trigger fires at correct time.

### Step 2.2 — MiniSEED Recording

- [ ] Implement `recorder.py`:
  - `MiniSEEDRecorder` class:
    - Initialize with station/network/channel/location codes
    - `write_samples(data_buffer, start_time)` — append to current MiniSEED file via ObsPy `Stream.write()`
    - Rotate file every `MSEED_FILE_DURATION_SEC`
    - File naming: `{NETWORK}.{STATION}.{LOCATION}.{CHANNEL}.{YYYY}.{JJJ}.mseed`
    - Properly set ObsPy `Stats` headers (sampling_rate, npts, starttime)
  - `EventRecorder`:
    - Capture waveform window around detected event (configurable pre/post trigger seconds)
    - Store snapshot in `waveform_data` table as compressed blob

**Checkpoint:** Record 60 seconds of data → valid MiniSEED file readable by ObsPy `read()`.

### Step 2.3 — Detection Pipeline

- [ ] Wire sensor loop → detector → recorder → database in `app.py`:
  - Background thread reads from sensor ring buffer
  - Passes buffer to STA/LTA detector at regular intervals
  - On trigger: log event to database, capture waveform snapshot, emit SocketIO alert
  - Continuous recording to MiniSEED regardless of detection

**Checkpoint:** Run with mock sensor → synthetic events detected, logged to DB, MiniSEED files written.

---

## Phase 3 — Dashboard & Authentication

### Step 3.1 — Authentication System

- [ ] Implement `auth.py`:
  - `hash_password(plaintext)` → bcrypt hash
  - `verify_password(plaintext, hash)` → bool
  - `login_required` decorator — checks session, redirects to login
  - Rate limiter — track attempts per IP, block after `RATE_LIMIT_MAX` in `RATE_LIMIT_WINDOW_MIN`
  - Session config: `SESSION_EXPIRY_HOURS` enforced via before_request

**Checkpoint:** Login with correct password succeeds; 11th rapid attempt returns 429.

### Step 3.2 — Login Page

- [ ] Create `templates/login.html`:
  - Username + password form
  - CSRF token
  - Error message display
  - Dark theme consistent with base
- [ ] Implement `/login` POST route (verify bcrypt, set session)
- [ ] Implement `/logout` route (clear session)

**Checkpoint:** Browse to dashboard → redirected to login → enter creds → see dashboard.

### Step 3.3 — Live Seismogram Dashboard

- [ ] Create `templates/dashboard.html`:
  - Chart.js line chart for real-time waveform (scrolling, green trace on dark background)
  - SocketIO client receives waveform data packets at ~10-20 Hz update rate
  - Time window selector (30s, 60s, 5min, 15min)
  - Current STA/LTA ratio display (gauge or bar)
  - Last detected event summary card
  - Station status indicators (sensor connected, recording active, network upload status)
- [ ] Implement SocketIO waveform broadcast:
  - Downsample sensor buffer for display (100 Hz → ~20 points/sec for smooth chart)
  - Emit `waveform_data` event with timestamp + samples array
  - Emit `event_detected` event when STA/LTA triggers

**Checkpoint:** Open dashboard → live scrolling seismogram visible, tapping table triggers visible spike.

### Step 3.4 — Events & Settings Pages

- [ ] Create `templates/events.html`:
  - Paginated event table (time, type, magnitude, STA/LTA ratio, duration)
  - Click event → detail view with waveform replay
  - Filter by event type and date range
- [ ] Create event detail view:
  - Waveform replay (Chart.js from stored waveform_data blob)
  - Event metadata (magnitude, P-wave time, duration, channel)
  - Alert status (sent/not sent)
- [ ] Create `templates/settings.html`:
  - Station config (codes, location, sensor type)
  - Feature flag states display
  - Sensor status (connected, sample rate, last reading)
  - MiniSEED recording status (current file, disk usage)

**Checkpoint:** Dashboard shows event list; clicking event shows waveform replay.

---

## Phase 4 — Analysis & Replay

### Step 4.1 — Spectrogram

- [ ] Implement `spectrogram.py`:
  - `generate_spectrogram(data_buffer, sample_rate, nfft)` → 2D array (time × frequency)
  - Uses `scipy.signal.spectrogram()` for STFT computation
  - Return as JSON-serializable data for Chart.js heatmap or canvas rendering
  - Configurable frequency range, color scale, window function
- [ ] Create `templates/spectrogram.html`:
  - Canvas-based spectrogram display (time on X, frequency on Y, amplitude as color)
  - Real-time update via SocketIO
  - Frequency band markers (microseismic, teleseismic, local earthquake ranges)
  - Time window selector

**Checkpoint:** Spectrogram page shows real-time frequency content; earthquake signal visible as bright band.

### Step 4.2 — Historical Event Replay

- [ ] Implement `replay.py`:
  - `search_usgs_events(start_date, end_date, min_magnitude, max_radius_km, lat, lon)` → event list
  - `download_waveform(network, station, channel, start_time, end_time)` → ObsPy Stream
  - Uses ObsPy `Client('IRIS')` for FDSN waveform download
  - Cache downloaded waveforms in `data/` to avoid repeated downloads
- [ ] Create `templates/replay.html`:
  - Event search form (date range, magnitude, region)
  - Results table (time, magnitude, location, depth)
  - Click event → load and display waveform from IRIS
  - Side-by-side comparison with local station recording (if available)

**Checkpoint:** Search for M5.0+ in last 30 days → select event → waveform displays from IRIS.

### Step 4.3 — Multi-Axis Support

- [ ] Extend sensor interface for 3-axis data (Z, N, E channels)
- [ ] Extend recorder for multi-channel MiniSEED (3 separate streams)
- [ ] Add 3-axis waveform display on dashboard (stacked or overlay Chart.js charts)
- [ ] Update STA/LTA detector to process all 3 channels

**Checkpoint:** With 3-axis sensor, dashboard shows Z/N/E waveforms; detection uses all channels.

---

## Phase 5 — Alerts & Network

### Step 5.1 — Alert System

- [ ] Implement `alerts.py`:
  - `AlertDispatcher` class:
    - `send_alert(event)` — dispatches to all enabled alert channels
    - Cooldown timer to prevent alert flooding (configurable minimum interval)
  - `EmailAlert`:
    - Send via smtplib with TLS
    - Subject: "Seismic Event Detected — M{magnitude} at {time}"
    - Body: event details, STA/LTA ratio, station info
  - `TelegramAlert`:
    - POST to Telegram Bot API via requests
    - Message with event details and waveform snapshot (if possible)
  - `GPIOBuzzerAlert`:
    - Activate GPIO pin for `ALERT_BUZZER_DURATION_SEC`
    - Use RPi.GPIO for pin control
  - `MockAlertDispatcher` — logs alerts without sending

**Checkpoint:** Trigger synthetic event → email received, Telegram message sent, buzzer sounds for 5 seconds.

### Step 5.2 — Network Contribution

- [ ] Implement `network.py`:
  - `FDSNUploader` class:
    - Upload MiniSEED data to configured FDSN server
    - Support Raspberry Shake forwarding protocol
    - Retry with exponential backoff on failure
    - Track upload status per file
  - `IRISUploader` class:
    - Upload to IRIS data management center
    - Authenticate with station credentials
  - Upload queue — background thread processes pending uploads
  - Status tracking — last upload time, success/fail count

**Checkpoint:** Record 5 minutes → MiniSEED file uploaded to test FDSN server successfully.

### Step 5.3 — Alert Management

- [ ] Add alert history to events page (which alerts sent, when, status)
- [ ] Add alert test button on settings page (send test alert to all enabled channels)
- [ ] Add network upload status display (last upload time, queue depth, error log)

**Checkpoint:** Settings page shows alert and network upload status; test button triggers test alert.

---

## Phase 6 — Hardening & Deployment

### Step 6.1 — Security Hardening

- [ ] Add `Content-Security-Policy` header to all responses
- [ ] Add `X-Content-Type-Options: nosniff` header
- [ ] Add `X-Frame-Options: DENY` header
- [ ] Audit all user inputs for sanitization (search queries, station config, settings)
- [ ] Verify all SQL uses parameterized queries
- [ ] Verify Jinja2 auto-escaping is enabled on all templates
- [ ] Test rate limiter under load

**Checkpoint:** Security headers present on all responses; injection attempts blocked.

### Step 6.2 — Error Handling & Logging

- [ ] Add structured logging to all modules (Python `logging` module)
- [ ] Log to file (`data/app.log`) and console
- [ ] Handle I2C bus errors gracefully (sensor reconnect with backoff)
- [ ] Handle sensor disconnection (pause sampling, notify dashboard)
- [ ] Handle disk full (stop MiniSEED recording, alert user)
- [ ] Handle network upload failure (queue and retry)
- [ ] Add health check endpoint (`/api/health`)

**Checkpoint:** Disconnect I2C sensor → dashboard shows warning, auto-reconnects when restored.

### Step 6.3 — Deployment

- [ ] Create `deploy/deploy_to_pi.sh`:
  ```bash
  #!/bin/bash
  REMOTE="rasp-pi"
  REMOTE_DIR="~/seismograph-station"
  rsync -avz --exclude='venv' --exclude='data' --exclude='.env' \
    . ${REMOTE}:${REMOTE_DIR}/
  ssh ${REMOTE} "cd ${REMOTE_DIR} && source venv/bin/activate && pip install -r requirements.txt"
  ssh ${REMOTE} "sudo systemctl restart seismograph-station"
  ```
- [ ] Create systemd service file
- [ ] Test deploy script end-to-end
- [ ] Verify service starts on boot

**Checkpoint:** Run deploy script → service restarts on Pi → dashboard accessible at `http://192.168.216.90:5000`.

### Step 6.4 — Testing & Documentation

- [ ] Write unit tests for `sensor.py` (mock I2C bus, verify sampling)
- [ ] Write unit tests for `detector.py` (synthetic waveforms, verify STA/LTA triggers)
- [ ] Write unit tests for `recorder.py` (MiniSEED write/read round-trip)
- [ ] Write unit tests for `auth.py` (bcrypt, rate limiter, session expiry)
- [ ] Write unit tests for `alerts.py` (mock SMTP, mock Telegram API, mock GPIO)
- [ ] Write unit tests for `network.py` (mock FDSN upload)
- [ ] Write integration test: full event lifecycle (detect → record → alert → upload)
- [ ] Run all tests on Pi hardware
- [ ] Performance benchmark: 100 Hz sampling stability over 24 hours
- [ ] Performance benchmark: STA/LTA detection latency (target: <500ms)
- [ ] Performance benchmark: SocketIO waveform throughput (target: <100ms latency)
- [ ] Memory profile: 24-hour continuous recording stays under 512 MB RSS
- [ ] Final review of `README.md`, `TSD.md`, all docstrings
- [ ] Verify `.env.example` has all variables with comments

**Checkpoint:** All tests pass on Pi. README accurately reflects final implementation.
