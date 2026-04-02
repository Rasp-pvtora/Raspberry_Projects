# Seismograph Station

Connect a geophone sensor (or ADXL345 accelerometer + ADS1115 ADC for DIY budget version) to the Raspberry Pi. Continuously record seismic data, detect earthquake events via STA/LTA algorithm, visualize seismograms on a web dashboard, and contribute data to citizen seismology networks (Raspberry Shake, IRIS, USGS). Uses ObsPy for seismological data processing and MiniSEED format for industry-standard data storage.

> **Citizen science:** Your station becomes part of the global seismic network. Earthquake data is uploaded in real time to Raspberry Shake / IRIS / USGS for professional seismologists to use.

---

### Support This Project

If you find this project useful, consider supporting development:

**Bitcoin:** `bc1q...`

---

## Table of Contents

- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Libraries](#libraries)
- [Quickstart](#quickstart)
- [Environment Variables](#environment-variables)
- [System Overview](#system-overview)
- [Features](#features)
  - [Real-Time Seismogram Display](#real-time-seismogram-display)
  - [STA/LTA Earthquake Detection](#stalta-earthquake-detection)
  - [Earthquake Early Warning](#earthquake-early-warning)
  - [MiniSEED Data Recording](#miniseed-data-recording)
  - [Network Contribution](#network-contribution)
  - [Historical Event Replay](#historical-event-replay)
  - [Spectrogram](#spectrogram)
  - [Multi-Axis Support](#multi-axis-support)
  - [Web Dashboard](#web-dashboard)
  - [Alert System](#alert-system)
- [Authentication & Security](#authentication--security)
- [Deployment](#deployment)
- [Running with systemd](#running-with-systemd)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
Seismograph Station/
├── README.md                   # This file
├── TSD.md                      # Technical specification document
├── task.md                     # Task checklist by phase
├── implementation_plan.md      # Step-by-step implementation guide
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── app.py                      # Flask application entry point
├── config.py                   # Configuration loader (.env)
├── auth.py                     # Authentication (bcrypt, sessions)
├── sensor.py                   # ADXL345/ADS1115 sensor interface
├── detector.py                 # STA/LTA earthquake detection engine
├── recorder.py                 # MiniSEED data recorder (ObsPy)
├── network.py                  # FDSN upload (Raspberry Shake, IRIS)
├── alerts.py                   # Alert system (email, Telegram, GPIO buzzer)
├── replay.py                   # Historical event replay (USGS download)
├── spectrogram.py              # Frequency analysis and spectrogram generation
├── database.py                 # SQLite database models & queries
├── deploy/
│   └── deploy_to_pi.sh         # SCP deploy script
├── static/
│   ├── css/
│   │   └── style.css           # Dark theme dashboard styles
│   └── js/
│       └── app.js              # SocketIO client, Chart.js waveforms
├── templates/
│   ├── base.html               # Base template (dark theme)
│   ├── login.html              # Login page
│   ├── dashboard.html          # Main dashboard (live seismogram)
│   ├── events.html             # Detected seismic events list
│   ├── replay.html             # Historical event replay view
│   ├── spectrogram.html        # Spectrogram / frequency analysis
│   └── settings.html           # Settings page
├── data/
│   ├── seismo.db               # SQLite database (auto-created)
│   └── mseed/                  # MiniSEED data files
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_sensor.py
    ├── test_detector.py
    ├── test_recorder.py
    ├── test_network.py
    ├── test_alerts.py
    └── test_auth.py
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 / Pi 5 | **Yes** | 2 GB+ RAM sufficient |
| ADXL345 Accelerometer (DIY) | **Option A** | I2C, 3-axis, budget option |
| ADS1115 ADC (DIY) | **Option A** | 16-bit ADC for geophone input |
| Raspberry Shake RS1D (Pro) | **Option B** | Professional single-axis geophone |
| Raspberry Shake RS3D (Pro) | **Option B** | Professional 3-axis geophone |
| MicroSD Card (32 GB+) | **Yes** | Class 10 / A2 for continuous recording |
| Power Supply (5V 3A+) | **Yes** | Official Pi PSU recommended |
| Piezo Buzzer (optional) | Optional | GPIO-connected for local earthquake alert |
| Ethernet Cable | Recommended | Wired connection for stable data upload |

---

## Budget

| Item | Cost |
|---|---|
| **DIY Option** | |
| ADXL345 Accelerometer | ~$5 |
| ADS1115 16-bit ADC | ~$4 |
| **DIY Total** | **~$9** |
| **Professional Option** | |
| Raspberry Shake RS1D | ~$300 |
| Raspberry Shake RS3D | ~$450 |
| **Professional Total** | **~$300–450** |

*(Pi, SD card, and power supply assumed owned)*

---

## Libraries

| Library | Purpose |
|---|---|
| `Flask` | Web dashboard framework |
| `Flask-SocketIO` | WebSocket for real-time seismogram streaming |
| `obspy` | Seismological data processing, MiniSEED I/O, STA/LTA |
| `adafruit-circuitpython-adxl34x` | ADXL345 accelerometer driver |
| `adafruit-circuitpython-ads1x15` | ADS1115 ADC driver |
| `numpy` | Numerical processing for waveform data |
| `scipy` | Signal processing, filtering, spectral analysis |
| `bcrypt` | Password hashing for authentication |
| `python-dotenv` | Load environment variables from `.env` |
| `Jinja2` | HTML templating (bundled with Flask) |
| `requests` | FDSN/USGS API communication |

---

## Quickstart

### 1. Clone & Deploy

```bash
# From your development machine
scp -r . rasp-pi:~/seismograph-station/
ssh rasp-pi
cd ~/seismograph-station
```

### 2. System Dependencies

```bash
sudo apt update && sudo apt install -y \
  python3-pip python3-venv i2c-tools \
  libatlas-base-dev libopenblas-dev \
  python3-smbus
```

### 3. Enable I2C

```bash
sudo raspi-config nonint do_i2c 0
sudo reboot
```

### 4. Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure

```bash
cp .env.example .env
nano .env    # Edit as needed — all features are toggleable
```

### 6. Verify Sensor

```bash
# Check I2C devices are detected
i2cdetect -y 1
# ADXL345 should appear at 0x53, ADS1115 at 0x48
```

### 7. Initialize & Run

```bash
python app.py
# Dashboard: http://192.168.216.90:5000
```

---

## Environment Variables

All features are toggleable via `.env`. Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `change-me-in-production` | Flask session secret key |
| `FLASK_HOST` | `0.0.0.0` | Bind address |
| `FLASK_PORT` | `5000` | Bind port |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |
| `AUTH_ENABLED` | `true` | Enable bcrypt authentication |
| `AUTH_USERNAME` | `admin` | Dashboard login username |
| `AUTH_PASSWORD_HASH` | *(bcrypt hash)* | Bcrypt-hashed password |
| `SESSION_EXPIRY_HOURS` | `24` | Session expiry in hours |
| `RATE_LIMIT_MAX` | `10` | Max login attempts per window |
| `RATE_LIMIT_WINDOW_MIN` | `15` | Rate-limit window in minutes |
| `SENSOR_BACKEND` | `adxl345` | Sensor: `adxl345`, `ads1115`, `raspberry_shake`, `mock` |
| `SENSOR_SAMPLE_RATE` | `100` | Samples per second (Hz) |
| `SENSOR_I2C_BUS` | `1` | I2C bus number |
| `ADXL345_ADDRESS` | `0x53` | ADXL345 I2C address |
| `ADS1115_ADDRESS` | `0x48` | ADS1115 I2C address |
| `ADS1115_GAIN` | `1` | ADS1115 PGA gain (1, 2, 4, 8, 16) |
| `ADS1115_CHANNEL` | `0` | ADS1115 analog input channel (0-3) |
| `SEISMOGRAM_ENABLED` | `true` | Enable real-time seismogram display |
| `SEISMOGRAM_WINDOW_SEC` | `60` | Visible waveform window duration |
| `DETECTION_ENABLED` | `true` | Enable STA/LTA earthquake detection |
| `STA_WINDOW_SEC` | `1.0` | Short-term average window (seconds) |
| `LTA_WINDOW_SEC` | `30.0` | Long-term average window (seconds) |
| `STA_LTA_TRIGGER` | `3.5` | STA/LTA ratio trigger threshold |
| `STA_LTA_DETRIGGER` | `1.5` | STA/LTA ratio detrigger threshold |
| `EARLY_WARNING_ENABLED` | `false` | Enable P-wave early warning alert |
| `P_WAVE_THRESHOLD` | `2.0` | P-wave detection amplitude threshold |
| `RECORDING_ENABLED` | `true` | Enable MiniSEED data recording |
| `MSEED_PATH` | `data/mseed` | MiniSEED file output directory |
| `MSEED_FILE_DURATION_SEC` | `3600` | MiniSEED file rotation interval (seconds) |
| `STATION_CODE` | `MYSTA` | Station code for MiniSEED headers |
| `NETWORK_CODE` | `AM` | Network code (AM = amateur) |
| `LOCATION_CODE` | `00` | Location code |
| `CHANNEL_CODE` | `EHZ` | Channel code (EHZ = short-period vertical) |
| `NETWORK_UPLOAD_ENABLED` | `false` | Enable FDSN data upload |
| `FDSN_SERVER_URL` | `` | FDSN server URL for data submission |
| `RASPBERRY_SHAKE_KEY` | `` | Raspberry Shake station key |
| `IRIS_UPLOAD_ENABLED` | `false` | Enable IRIS data contribution |
| `IRIS_STATION_ID` | `` | IRIS station identifier |
| `REPLAY_ENABLED` | `true` | Enable historical event replay |
| `USGS_API_URL` | `https://earthquake.usgs.gov/fdsnws/event/1/query` | USGS event API |
| `SPECTROGRAM_ENABLED` | `true` | Enable spectrogram frequency analysis |
| `SPECTROGRAM_WINDOW_SEC` | `300` | Spectrogram time window (seconds) |
| `SPECTROGRAM_NFFT` | `256` | FFT window size for spectrogram |
| `MULTI_AXIS_ENABLED` | `false` | Enable 3-axis recording (RS3D) |
| `ALERT_EMAIL_ENABLED` | `false` | Enable email alerts on detection |
| `ALERT_EMAIL_SMTP` | `` | SMTP server for email alerts |
| `ALERT_EMAIL_PORT` | `587` | SMTP port |
| `ALERT_EMAIL_USER` | `` | SMTP username |
| `ALERT_EMAIL_PASS` | `` | SMTP password |
| `ALERT_EMAIL_TO` | `` | Alert email recipient |
| `ALERT_TELEGRAM_ENABLED` | `false` | Enable Telegram alerts |
| `ALERT_TELEGRAM_BOT_TOKEN` | `` | Telegram bot token |
| `ALERT_TELEGRAM_CHAT_ID` | `` | Telegram chat ID |
| `ALERT_GPIO_ENABLED` | `false` | Enable GPIO buzzer alert |
| `ALERT_GPIO_PIN` | `17` | GPIO pin number for buzzer |
| `ALERT_BUZZER_DURATION_SEC` | `5` | Buzzer alert duration (seconds) |
| `DB_PATH` | `data/seismo.db` | SQLite database path |
| `MOCK_MODE` | `false` | Use mock sensor data for development |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Seismograph Station                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌───────────────┐    ┌────────────────────┐     │
│  │ ADXL345 /   │───▶│ sensor.py     │───▶│ detector.py        │     │
│  │ ADS1115 /   │    │ I2C / ADC     │    │ STA/LTA (ObsPy)    │     │
│  │ Rasp Shake  │    │ Sampling      │    │ P-wave detection   │     │
│  └─────────────┘    └───────────────┘    └────────┬───────────┘     │
│                                                    │                 │
│                               ┌────────────────────┼──────────┐     │
│                               │                    │          │     │
│                               ▼                    ▼          ▼     │
│                    ┌──────────────┐    ┌──────────────┐  ┌───────┐ │
│                    │ recorder.py  │    │ Flask-SocketIO│  │SQLite │ │
│                    │ MiniSEED     │    │ Live Waveform │  │Events │ │
│                    │ (ObsPy)      │    │ (Chart.js)    │  │Archive│ │
│                    └──────────────┘    └──────────────┘  └───────┘ │
│                                                                      │
│                    ┌──────────────────────────────────────┐         │
│                    │ Analysis & Network                   │         │
│                    │  ├─ spectrogram.py (FFT analysis)   │         │
│                    │  ├─ network.py (FDSN/IRIS upload)   │         │
│                    │  ├─ replay.py (USGS historical)     │         │
│                    │  └─ alerts.py (email/TG/buzzer)     │         │
│                    └──────────────────────────────────────┘         │
│                                                                      │
│                    ┌──────────────────────────────────────┐         │
│                    │ Flask Dashboard (Dark Theme)         │         │
│                    │  ├─ Live Seismogram (Chart.js)       │         │
│                    │  ├─ Detected Events Table            │         │
│                    │  ├─ Spectrogram View                 │         │
│                    │  ├─ Historical Replay                │         │
│                    │  └─ Station Settings & Status        │         │
│                    └──────────────────────────────────────┘         │
│                                                                      │
│                    ┌──────────────────────────────────────┐         │
│                    │ Auth: bcrypt | Rate Limit: 10/15min  │         │
│                    │ Session: 24h expiry | HTTPS ready    │         │
│                    └──────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Features

### Real-Time Seismogram Display

Streams live seismic waveform data to the browser via Flask-SocketIO. Displays a continuous scrolling waveform graph using Chart.js — like a hospital heart monitor but for the Earth. Configurable time window and update rate.

- Toggle: `SEISMOGRAM_ENABLED=true`
- Window: `SEISMOGRAM_WINDOW_SEC=60`

### STA/LTA Earthquake Detection

Uses the classic Short-Term Average / Long-Term Average (STA/LTA) algorithm via ObsPy to detect seismic events in real time. When the STA/LTA ratio exceeds the trigger threshold, an event is recorded with magnitude estimate, P-wave arrival time, and duration.

- Toggle: `DETECTION_ENABLED=true`
- Sensitivity: `STA_LTA_TRIGGER=3.5`, `STA_LTA_DETRIGGER=1.5`
- Windows: `STA_WINDOW_SEC=1.0`, `LTA_WINDOW_SEC=30.0`

### Earthquake Early Warning

Detects P-wave arrivals (the first, faster seismic wave) to provide early warning before the destructive S-wave arrives. Triggers alert system with estimated seconds until S-wave impact based on distance calculation.

- Toggle: `EARLY_WARNING_ENABLED=true`
- Threshold: `P_WAVE_THRESHOLD=2.0`

### MiniSEED Data Recording

Records continuous seismic data in MiniSEED format — the standard format used by seismological networks worldwide. Files are rotated at configurable intervals and include proper station/network/channel metadata per SEED conventions.

- Toggle: `RECORDING_ENABLED=true`
- Path: `MSEED_PATH=data/mseed`
- Rotation: `MSEED_FILE_DURATION_SEC=3600`

### Network Contribution

Upload seismic data to citizen seismology networks via FDSN protocol. Contribute to Raspberry Shake's global network, IRIS, or USGS. Your data helps seismologists locate earthquakes more accurately and advances earthquake science.

- Toggle: `NETWORK_UPLOAD_ENABLED=true`
- Config: `FDSN_SERVER_URL`, `RASPBERRY_SHAKE_KEY`, `IRIS_STATION_ID`

### Historical Event Replay

Download historical earthquake waveform data from USGS/IRIS FDSN web services and replay them on the dashboard. Compare your station's recordings with professional network data. Great for calibration and educational purposes.

- Toggle: `REPLAY_ENABLED=true`
- API: `USGS_API_URL`

### Spectrogram

Real-time frequency analysis of seismic data displayed as a spectrogram (time vs. frequency heatmap). Helps identify earthquake signals vs. noise sources (traffic, construction, weather). Uses FFT via scipy.

- Toggle: `SPECTROGRAM_ENABLED=true`
- Window: `SPECTROGRAM_WINDOW_SEC=300`
- Resolution: `SPECTROGRAM_NFFT=256`

### Multi-Axis Support

Record and display all three axes (Z, N, E) when using a Raspberry Shake RS3D or similar 3-axis sensor. Enables full vector analysis, particle motion plots, and more accurate magnitude estimation.

- Toggle: `MULTI_AXIS_ENABLED=true`

### Web Dashboard

Flask web dashboard with dark theme and Chart.js waveform visualization. Real-time seismogram, event table, spectrogram viewer, historical replay, and station configuration — all accessible from any browser on the LAN.

- Features: Live waveform, event list, spectrogram, replay, settings
- Theme: Dark mode (seismogram green-on-black aesthetic)

### Alert System

Multi-channel earthquake alert system triggered by STA/LTA detection:

- **Email** — SMTP notification with event details (magnitude, distance, time)
- **Telegram** — Bot message with event info and waveform snapshot
- **GPIO Buzzer** — Physical piezo buzzer alarm for immediate local alert

Toggles: `ALERT_EMAIL_ENABLED`, `ALERT_TELEGRAM_ENABLED`, `ALERT_GPIO_ENABLED`

---

## Authentication & Security

- **bcrypt password hashing** — passwords are never stored in plaintext
- **Rate limiting** — 10 requests per 15-minute window per IP (configurable)
- **Session management** — server-side sessions with 24-hour expiry
- **CSRF protection** — enabled on all form submissions
- **Auth toggle** — disable for trusted LAN environments (`AUTH_ENABLED=false`)

Generate a password hash:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```

Set the hash in `.env`:

```
AUTH_PASSWORD_HASH=$2b$12$...your-hash...
```

---

## Deployment

### Deploy via SCP

```bash
# From development machine
scp -r . rasp-pi:~/seismograph-station/
```

### Deploy Script

```bash
chmod +x deploy/deploy_to_pi.sh
./deploy/deploy_to_pi.sh
```

The deploy script:
1. Syncs project files to `rasp-pi` (192.168.216.90)
2. Installs/updates Python dependencies
3. Restarts the systemd service

---

## Running with systemd

Create the service file:

```bash
sudo nano /etc/systemd/system/seismograph-station.service
```

```ini
[Unit]
Description=Seismograph Station
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/seismograph-station
Environment=PATH=/home/pi/seismograph-station/venv/bin:/usr/bin
ExecStart=/home/pi/seismograph-station/venv/bin/python app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable seismograph-station
sudo systemctl start seismograph-station
sudo systemctl status seismograph-station
```

Access the dashboard: `http://192.168.216.90:5000`

---

## Security Notes

- **All processing is local.** Seismic data is processed and stored on the Raspberry Pi.
- **Network upload is opt-in.** Data is only sent to FDSN/IRIS when explicitly enabled.
- **No internet required** for core functionality (recording, detection, dashboard).
- **SQLite database** is stored locally; encrypt the SD card for additional protection (`LUKS`).
- **Bind to LAN only** — do not expose port 5000 to the internet without a reverse proxy and TLS.
- **I2C bus** is a local hardware interface — no wireless attack surface.
- **Update regularly** — `pip install --upgrade` and `sudo apt upgrade` for security patches.
- **Physical security** — mount the sensor on a stable, vibration-isolated surface (concrete slab ideal).

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `No I2C device at 0x53` | Check ADXL345 wiring (SDA→GPIO2, SCL→GPIO3). Run `i2cdetect -y 1`. |
| `No I2C device at 0x48` | Check ADS1115 wiring and address jumper. Verify I2C enabled. |
| `I2C permission denied` | Add user to `i2c` group: `sudo usermod -aG i2c pi` |
| `Noisy seismogram` | Isolate sensor from vibrations. Use a longer LTA window. Check power supply. |
| `STA/LTA false triggers` | Increase `STA_LTA_TRIGGER` threshold. Increase `LTA_WINDOW_SEC`. |
| `MiniSEED write errors` | Check disk space. Verify `MSEED_PATH` directory exists and is writable. |
| `FDSN upload failing` | Verify `FDSN_SERVER_URL` and credentials. Check network connectivity. |
| `WebSocket not connecting` | Check firewall allows port 5000. Verify `FLASK_HOST=0.0.0.0`. |
| `ObsPy import error` | Install system deps: `sudo apt install libxml2-dev libxslt1-dev`. |
| `bcrypt import error` | Install system dependency: `sudo apt install libffi-dev && pip install bcrypt` |
| `Spectrogram blank` | Verify sensor is producing data. Check `SPECTROGRAM_NFFT` ≤ sample buffer size. |
| `Raspberry Shake not detected` | RS devices use UDP; check `SENSOR_BACKEND=raspberry_shake` and network config. |

---

## Where to Next

- **ShakeNet integration** — join the Raspberry Shake global network for real-time earthquake detection
- **Machine learning detection** — train a CNN/LSTM model on your local seismic data for better accuracy
- **Multi-station array** — deploy multiple Pis with geophones for triangulation and source location
- **Infrasound monitoring** — add a barometric pressure sensor for atmospheric event detection
- **MQTT bridge** — publish events to Home Assistant or Node-RED for smart home integration
- **Telegram bot commands** — query station status and recent events via Telegram
- **GPS timing** — add a GPS module for precise NTP-independent time synchronization
- **HVSR analysis** — horizontal-to-vertical spectral ratio for site characterization
- **Web-based filter designer** — interactive bandpass/notch filter tuning in the dashboard
- **3D particle motion** — visualize ground motion in 3D using three-component data
