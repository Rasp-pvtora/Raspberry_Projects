# Task List — Seismograph Station

## Phase 1 — Foundation & Sensor Interface

- [ ] Create project directory structure
- [ ] Create `requirements.txt` with all dependencies
- [ ] Create `.env.example` with all variables and defaults
- [ ] Implement `config.py` — load `.env`, parse feature flags, validate paths
- [ ] Implement `database.py` — SQLite schema init (seismic_events, waveform_data, station_config, settings)
- [ ] Add database migration/versioning support
- [ ] Implement `sensor.py` — ADXL345 I2C driver (adafruit-circuitpython-adxl34x)
- [ ] Implement ADS1115 ADC driver in `sensor.py` (adafruit-circuitpython-ads1x15)
- [ ] Implement Raspberry Shake UDP listener in `sensor.py`
- [ ] Implement sensor sampling loop (configurable Hz, threaded)
- [ ] Implement data buffering with ring buffer (numpy array)
- [ ] Add mock sensor mode (synthetic seismic waveforms + noise)
- [ ] Create basic Flask app skeleton (`app.py`)
- [ ] Set up Jinja2 base template with dark theme
- [ ] Create `static/css/style.css` (dark theme, green-on-black seismogram aesthetic)
- [ ] Create `static/js/app.js` (SocketIO client + Chart.js stub)
- [ ] Verify I2C sensor detection on Pi (`i2cdetect -y 1`)

## Phase 2 — Detection & Recording

- [ ] Implement `detector.py` — STA/LTA algorithm via ObsPy `classic_sta_lta`
- [ ] Implement configurable trigger/detrigger thresholds
- [ ] Implement P-wave arrival detection (first break picking)
- [ ] Implement event recording — store detected events in `seismic_events` table
- [ ] Estimate event magnitude from peak amplitude
- [ ] Capture waveform snapshot around event (pre-trigger + post-trigger window)
- [ ] Store waveform snapshots in `waveform_data` table
- [ ] Implement `recorder.py` — MiniSEED continuous recording via ObsPy
- [ ] Implement file rotation by `MSEED_FILE_DURATION_SEC`
- [ ] Write proper SEED header metadata (station, network, channel, location codes)
- [ ] Add mock detection mode (simulated STA/LTA triggers)
- [ ] Test detection with synthetic earthquake waveforms

## Phase 3 — Dashboard & Authentication

- [ ] Implement `auth.py` — bcrypt password verification
- [ ] Implement login route and `templates/login.html`
- [ ] Implement session management (server-side, 24h expiry)
- [ ] Add `@login_required` decorator for protected routes
- [ ] Implement rate limiting middleware (10 req / 15 min / IP)
- [ ] Add CSRF protection to all forms
- [ ] Create `templates/dashboard.html` — live seismogram (Chart.js waveform)
- [ ] Set up Flask-SocketIO server for real-time waveform streaming
- [ ] Implement WebSocket event: broadcast new waveform samples
- [ ] Implement Chart.js scrolling waveform display (green trace on dark background)
- [ ] Add seismogram time window selector (`SEISMOGRAM_WINDOW_SEC`)
- [ ] Create `templates/events.html` — detected events list with detail view
- [ ] Create event detail page (waveform replay, metadata, STA/LTA ratio)
- [ ] Create `templates/settings.html` — station config, feature flags, sensor status
- [ ] Add station location input (latitude, longitude, elevation)
- [ ] Toggle auth on/off via `AUTH_ENABLED`

## Phase 4 — Analysis & Replay

- [ ] Implement `spectrogram.py` — FFT analysis via scipy
- [ ] Generate spectrogram image data (time-frequency heatmap)
- [ ] Create `templates/spectrogram.html` — spectrogram viewer
- [ ] Implement real-time spectrogram update via SocketIO
- [ ] Add configurable FFT parameters (`SPECTROGRAM_NFFT`, window size)
- [ ] Implement `replay.py` — download USGS earthquake event data via API
- [ ] Parse USGS FDSN event response (QuakeML)
- [ ] Download historical waveform data from IRIS FDSN web services
- [ ] Create `templates/replay.html` — event search and waveform replay
- [ ] Implement event search by date range, magnitude, region
- [ ] Display replayed waveform on Chart.js with event metadata overlay
- [ ] Implement multi-axis support — 3-channel display (Z, N, E)
- [ ] Add 3-axis waveform overlay on dashboard
- [ ] Add comparison view (station data vs. USGS reference)

## Phase 5 — Alerts & Network

- [ ] Implement `alerts.py` — alert dispatcher (email, Telegram, GPIO)
- [ ] Implement email alert via smtplib (event details, magnitude, time)
- [ ] Implement Telegram bot alert via requests (message with event info)
- [ ] Implement GPIO buzzer alert (RPi.GPIO, configurable pin and duration)
- [ ] Add alert cooldown to prevent rapid-fire alerts
- [ ] Add alert history to database
- [ ] Implement `network.py` — FDSN data upload client
- [ ] Implement Raspberry Shake data forwarding
- [ ] Implement IRIS data contribution upload
- [ ] Add upload status tracking and retry logic
- [ ] Add network contribution status display on settings page
- [ ] Test upload with Raspberry Shake test server

## Phase 6 — Hardening & Deployment

- [ ] Create `deploy/deploy_to_pi.sh` — SCP + service restart
- [ ] Create systemd service file template
- [ ] Add Content-Security-Policy headers
- [ ] Audit all routes for input validation
- [ ] Audit all database queries for parameterized statements
- [ ] Add structured logging (file + console)
- [ ] Add error handling for sensor disconnection
- [ ] Add error handling for I2C bus errors
- [ ] Add error handling for disk full / MiniSEED write failure
- [ ] Add error handling for network upload failures
- [ ] Performance benchmark: sampling rate stability at 100 Hz
- [ ] Performance benchmark: STA/LTA detection latency
- [ ] Performance benchmark: SocketIO waveform streaming throughput
- [ ] Memory profiling under continuous 24h recording
- [ ] Write unit tests for `sensor.py` (mock I2C)
- [ ] Write unit tests for `detector.py` (synthetic waveforms)
- [ ] Write unit tests for `recorder.py` (MiniSEED I/O)
- [ ] Write unit tests for `auth.py` (bcrypt, rate limiter)
- [ ] Write unit tests for `alerts.py` (mock SMTP, mock Telegram)
- [ ] Write unit tests for `network.py` (mock FDSN upload)
- [ ] Write integration test: full event lifecycle (detect → record → alert → upload)
- [ ] Update `README.md` with final instructions
- [ ] Final `.env.example` review — all variables documented
