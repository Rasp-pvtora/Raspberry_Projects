# Solar Panel Follower

An intelligent dual-axis solar tracking system for Raspberry Pi that uses servo motors and light sensors to maximize energy absorption, with machine learning to predict optimal angles. Includes real-time power monitoring (INA219), astronomical tracking fallback, energy logging and analytics, weather-aware tracking, and a web dashboard for monitoring power output, angle control, and energy statistics.

🪙 **Donations are Welcome!**
If you find this project helpful, you can support my work with a small donation.
₿ Bitcoin donation: `bc1q...`

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Budget](#budget)
4. [Libraries and dependencies](#libraries-and-dependencies)
5. [Quickstart — Laptop (development)](#quickstart--laptop-development)
6. [Environment configuration (.env)](#environment-configuration-env)
7. [System overview](#system-overview)
8. [Feature 1 — Dual-axis solar tracking (LDR + servos)](#feature-1--dual-axis-solar-tracking-ldr--servos)
9. [Feature 2 — Power monitoring (INA219)](#feature-2--power-monitoring-ina219)
10. [Feature 3 — Astronomical tracking fallback](#feature-3--astronomical-tracking-fallback)
11. [Feature 4 — ML-based angle prediction](#feature-4--ml-based-angle-prediction)
12. [Feature 5 — Energy logging and analytics](#feature-5--energy-logging-and-analytics)
13. [Feature 6 — Weather-aware tracking](#feature-6--weather-aware-tracking)
14. [Feature 7 — Servo sleep mode](#feature-7--servo-sleep-mode)
15. [Feature 8 — Web dashboard](#feature-8--web-dashboard)
16. [Wiring diagram](#wiring-diagram)
17. [Frame and mount](#frame-and-mount)
18. [Authentication](#authentication)
19. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
20. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
21. [Real-world applications](#real-world-applications)
22. [Security notes](#security-notes)
23. [Troubleshooting](#troubleshooting)
24. [Where to next](#where-to-next)

---

## Project structure

```
.
├── app.py                     ← Python entry point (Flask + tracking loop)
├── requirements.txt           ← Python dependencies
├── .env.default               ← Environment variable template (copy to .env)
├── .gitignore                 ← Git ignore rules
├── src/
│   ├── tracking/
│   │   ├── ldr_tracker.py     ← LDR-based light tracking (quadrant sensor)
│   │   ├── astro_tracker.py   ← Astronomical solar position calculation
│   │   ├── ml_predictor.py    ← ML-based optimal angle prediction
│   │   └── tracker_manager.py ← Tracking mode coordinator
│   ├── hardware/
│   │   ├── servo_controller.py ← Servo motor control (pan + tilt)
│   │   ├── adc_reader.py      ← ADS1115 ADC for LDR readings
│   │   ├── power_monitor.py   ← INA219 voltage/current/power monitoring
│   │   └── mock_hardware.py   ← Mock hardware for development
│   ├── routes/
│   │   ├── auth.py            ← Login / logout routes
│   │   ├── dashboard.py       ← Dashboard API
│   │   ├── tracking.py        ← Tracking control API
│   │   ├── energy.py          ← Energy data and analytics API
│   │   └── settings.py        ← Settings API
│   └── services/
│       ├── energy_logger.py   ← Energy data logging to SQLite
│       ├── weather_service.py ← Weather API integration
│       ├── analytics_service.py ← Energy statistics and reports
│       ├── system_service.py  ← System info (temp, memory, disk)
│       └── db.py              ← SQLite database initialization
├── models/
│   └── angle_predictor.pkl    ← Trained ML model (generated after training)
├── data/
│   └── energy_log.db          ← SQLite database for energy data
├── templates/                 ← Jinja2 HTML templates
│   ├── layout.html            ← Base layout with sidebar navigation
│   ├── login.html             ← Login page
│   ├── dashboard.html         ← Live power, angle, and sensor dashboard
│   ├── energy.html            ← Energy analytics and charts
│   ├── tracking.html          ← Tracking mode control and manual override
│   └── settings.html          ← System and tracking settings
├── static/                    ← Static frontend assets
│   ├── css/style.css          ← Dark theme dashboard stylesheet
│   └── js/
│       ├── main.js            ← WebSocket client for real-time data
│       ├── dashboard.js       ← Dashboard gauges + Chart.js logic
│       ├── energy.js          ← Energy analytics charts
│       └── tracking.js        ← Tracking control and manual override
├── scripts/
│   ├── setup-i2c.sh           ← Enable I2C interface on the Pi
│   ├── setup-servo.sh         ← Servo and PWM configuration
│   ├── calibrate-ldr.sh       ← LDR sensor calibration routine
│   └── train-model.sh         ← Train ML angle predictor from logged data
├── deploy/
│   └── deploy_to_pi.sh        ← rsync-based deploy script
├── docs/
│   └── threat_model.md        ← Threat model and mitigations
├── tests/                     ← Test directory
├── README.md                  ← This file
├── TSD.md                     ← Technical Specification Description
└── task.md                    ← Engineering checklist
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 3B+ / 4 / 5 | Yes | Any model with I2C and GPIO; Pi 4 recommended |
| microSD card (16 GB+) | Yes | For OS, project files, and energy data |
| SG90 micro servo (×2) | Yes | Pan (azimuth) and tilt (elevation); 180° range |
| LDR photoresistors (×4) | Yes | Light Dependent Resistors in quadrant arrangement |
| ADS1115 ADC module (I2C) | Yes | 16-bit ADC for analog LDR readings (Pi has no analog inputs) |
| INA219 power monitor (I2C) | Yes | Measures solar panel voltage, current, and power |
| Solar panel 5V 200mA | Yes | Test panel: 110mm × 60mm (4.33" × 2.36") |
| 10kΩ resistors (×4) | Yes | Voltage dividers for LDRs |
| Pan-tilt servo bracket | Yes | Mechanical mount for the two servos + panel |
| Jumper wires | Yes | For connections |
| Power supply (official) | Yes | 5V 3A for Pi 4/5 |
| Breadboard | Optional | For prototyping connections |

---

## Budget

| Item | Estimated Price (USD) | Notes |
|---|---|---|
| SG90 micro servo (×2) | $4 – $6 | ~$2–3 each; 180° rotation, 1.8 kg·cm torque |
| LDR photoresistor (×4) | $2 – $3 | Often sold in 10-packs for $3 |
| ADS1115 ADC module | $3 – $5 | 16-bit, 4-channel, I2C |
| INA219 power monitor | $3 – $5 | I2C voltage/current sensor |
| Solar panel 5V 200mA (110×60mm) | $3 – $5 | Test panel for prototype |
| 10kΩ resistors (×4) | $1 | Standard through-hole |
| Pan-tilt servo bracket | $5 – $10 | Plastic or 3D-printed; holds 2 servos |
| Jumper wires (40-pack M/F) | $2 – $3 | Male-to-female for connections |
| Breadboard | $3 – $5 | For prototyping |
| **Optional:** MG996R servo (×2) | $8 – $12 | Stronger servos for larger panels (~$4–6 each) |
| **Optional:** NEMA 17 stepper + DRV8825 (×2) | $20 – $30 | Production-grade motors for heavier panels |
| **Optional:** Larger solar panel (12V 10W) | $15 – $25 | For real-world energy production |
| **Total (minimum)** | **~$26 – $42** | LDRs + ADC + INA219 + servos + panel + bracket |

> **Note:** The Raspberry Pi itself, microSD card, and power supply are not included in the budget above.

---

## Libraries and dependencies

### Python dependencies

| Library | Version | Purpose |
|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | ^3.1.0 | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | ^5.4.0 | WebSocket for real-time sensor data |
| [Jinja2](https://jinja.palletsprojects.com/) | ^3.1.4 | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ^1.0.1 | Load environment variables from `.env` |
| [adafruit-circuitpython-ads1x15](https://pypi.org/project/adafruit-circuitpython-ads1x15/) | ^2.4.0 | ADS1115 ADC driver (I2C) |
| [adafruit-circuitpython-ina219](https://pypi.org/project/adafruit-circuitpython-ina219/) | ^3.5.0 | INA219 power monitor driver (I2C) |
| [adafruit-blinka](https://pypi.org/project/Adafruit-Blinka/) | ^8.48.0 | CircuitPython hardware abstraction layer |
| [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) | ^0.7.1 | GPIO PWM for servo control |
| [pigpio](https://pypi.org/project/pigpio/) | ^1.78 | Hardware PWM for jitter-free servo control |
| [pvlib](https://pvlib-python.readthedocs.io/) | ^0.11.0 | Solar position calculation (astronomical tracking) |
| [scikit-learn](https://scikit-learn.org/) | ^1.5.0 | ML model for angle prediction |
| [numpy](https://numpy.org/) | ^1.26.0 | Numerical operations |
| [pandas](https://pandas.pydata.org/) | ^2.2.0 | Data analysis for energy logs |
| [bcrypt](https://pypi.org/project/bcrypt/) | ^4.2.0 | Password hashing |
| [requests](https://requests.readthedocs.io/) | ^2.32.0 | Weather API calls |
| [chart.js](https://www.chartjs.org/) | ^4.4.7 | Dashboard charts (loaded via CDN) |

### Dev dependencies

| Library | Version | Purpose |
|---|---|---|
| [pytest](https://docs.pytest.org/) | ^8.3.0 | Testing framework |

### System packages (installed on the Pi)

| Package | Purpose |
|---|---|
| `pigpio` | Hardware PWM daemon for servo control |
| `i2c-tools` | I2C debugging and detection |
| `python3-smbus` | I2C communication library |
| `Python 3.11+` | Python runtime |

---

## Quickstart — Laptop (development)

**1. Clone the repository**

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/Solar Panel Follower"
```

**2. Create the `.env` file from the template**

```bash
# Linux / macOS
cp .env.default .env

# Windows
copy .env.default .env
```

Edit `.env` and set your values (at minimum, change `SESSION_SECRET` and `ADMIN_PASSWORD`).

**3. Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

**4. Start the development server**

```bash
python app.py
```

**5. Open the dashboard**

Navigate to `http://localhost:5000` in your browser.

- **Username:** `admin` (or whatever you set in `.env`)
- **Password:** `changeme` (or whatever you set in `.env`)

> **Note:** On a laptop without I2C/GPIO hardware, the system runs in mock mode — sensor values are simulated, servos are virtual. The dashboard, energy analytics, and tracking controls work fully with simulated data.

---

## Environment configuration (.env)

Copy `.env.default` to `.env` and edit it. **Never commit `.env` to git.**

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Dashboard web server port |
| `HOST` | `0.0.0.0` | Listen address |
| `SESSION_SECRET` | `CHANGE_ME...` | Random string for session encryption |
| `ADMIN_USERNAME` | `admin` | Dashboard login username |
| `ADMIN_PASSWORD` | `changeme` | Dashboard login password |
| `SERVO_PAN_PIN` | `18` | GPIO pin for pan servo (azimuth) |
| `SERVO_TILT_PIN` | `19` | GPIO pin for tilt servo (elevation) |
| `SERVO_PAN_MIN_ANGLE` | `0` | Minimum pan angle (degrees) |
| `SERVO_PAN_MAX_ANGLE` | `180` | Maximum pan angle (degrees) |
| `SERVO_TILT_MIN_ANGLE` | `0` | Minimum tilt angle (degrees) |
| `SERVO_TILT_MAX_ANGLE` | `90` | Maximum tilt angle (degrees) |
| `ADC_I2C_ADDRESS` | `0x48` | ADS1115 I2C address |
| `INA219_I2C_ADDRESS` | `0x40` | INA219 I2C address |
| `LDR_THRESHOLD` | `50` | Minimum LDR difference to trigger servo movement |
| `TRACKING_INTERVAL_SEC` | `5` | Seconds between tracking adjustments |
| `TRACKING_MODE` | `ldr` | Tracking mode: `ldr`, `astronomical`, `ml`, `manual` |
| `LATITUDE` | `45.4642` | Location latitude (for astronomical tracking) |
| `LONGITUDE` | `9.1900` | Location longitude (for astronomical tracking) |
| `TIMEZONE` | `Europe/Rome` | Timezone for solar calculations |
| `WEATHER_API_KEY` | `` | OpenWeatherMap API key (free tier) |
| `WEATHER_ENABLED` | `false` | Enable weather-aware tracking |
| `SLEEP_ENABLED` | `true` | Park panel at sunrise angle overnight |
| `ENERGY_LOG_INTERVAL_SEC` | `60` | Seconds between energy data log entries |

---

## System overview

| Stage | Component | Tool | What it does |
|---|---|---|---|
| **1. Sense** | LDR quadrant (×4) | ADS1115 ADC (I2C) | Reads light intensity from 4 directions |
| **2. Calculate** | Tracker Manager | Python | Determines optimal pan/tilt angle |
| **3. Move** | Servo Controller | pigpio PWM | Adjusts panel azimuth and elevation |
| **4. Monitor** | Power Monitor | INA219 (I2C) | Measures voltage, current, and power from the panel |
| **5. Log** | Energy Logger | SQLite | Stores power, angle, light, and weather data |
| **6. Predict** | ML Predictor | scikit-learn | Predicts optimal angle from historical data |
| **7. Dashboard** | Web Server | Flask + WebSocket | Real-time gauges, charts, and controls |

**How the tracking loop works:**

```
Every 5 seconds:
    → Read 4 LDR values from ADS1115
    → Calculate brightness difference (top-bottom, left-right)
    → If difference > threshold:
        → Adjust pan/tilt servos toward brightest quadrant
    → Read INA219: voltage, current, power
    → Log data to SQLite
    → Push update to dashboard via WebSocket
```

---

## Feature 1 — Dual-axis solar tracking (LDR + servos)

The panel moves on two axes to follow the sun throughout the day.

### LDR Quadrant Arrangement

Four LDR photoresistors are mounted in a cross pattern with a divider wall between them:

```
        ┌─────┐
        │ TL  │  TR
        ├──┼──┤
        │ BL  │  BR
        └─────┘
```

- **TL** (Top-Left) + **TR** (Top-Right) → average = top brightness.
- **BL** (Bottom-Left) + **BR** (Bottom-Right) → average = bottom brightness.
- **TL** + **BL** → average = left brightness.
- **TR** + **BR** → average = right brightness.

**Tracking logic:**
- If top > bottom: tilt up.
- If bottom > top: tilt down.
- If left > right: pan left.
- If right > left: pan right.
- If all four are within threshold: panel is aligned — no movement.

### Servos

- **Pan servo (azimuth):** Rotates left/right (0°–180°). Tracks the sun's east-to-west movement.
- **Tilt servo (elevation):** Tilts up/down (0°–90°). Tracks the sun's altitude.
- **PWM control via pigpio:** Hardware PWM for smooth, jitter-free movement. Software PWM (RPi.GPIO) as fallback.

---

## Feature 2 — Power monitoring (INA219)

The INA219 sensor measures the solar panel's electrical output in real time.

- **Voltage:** Panel output voltage (0–26V range).
- **Current:** Panel output current (mA precision).
- **Power:** Calculated power (mW) = voltage × current.
- **I2C interface:** Shares the I2C bus with the ADS1115 (different addresses).

**Dashboard gauges:**
- Live voltage gauge (V).
- Live current gauge (mA).
- Live power gauge (mW).
- Power history chart (last hour, 24 hours, 7 days).

---

## Feature 3 — Astronomical tracking fallback

When clouds make LDR readings unreliable, fall back to calculated solar position.

- **pvlib library:** Calculates the sun's azimuth and elevation for any location and time.
- **GPS coordinates:** Set `LATITUDE`, `LONGITUDE`, and `TIMEZONE` in `.env`.
- **Automatic fallback:** If all 4 LDR readings are below a threshold (heavy overcast), the system switches to astronomical mode automatically.
- **Manual selection:** Set `TRACKING_MODE=astronomical` in `.env` to always use astronomical tracking.

**How it works:**
1. Calculate the sun's azimuth and elevation for the current time and location.
2. Map azimuth → pan servo angle (0°–180°).
3. Map elevation → tilt servo angle (0°–90°).
4. Move servos to calculated position.

---

## Feature 4 — ML-based angle prediction

After collecting energy data for several days, train a model to predict the optimal angle.

- **Training data:** Historical database of (date, time, weather, LDR values, angles, power output).
- **Model:** scikit-learn regression (LinearRegression, RandomForest, or GradientBoosting).
- **Prediction:** Given the current time and weather conditions, predict the angle that maximizes power.
- **Advantage over LDR:** Works during cloudy periods where LDR is noisy. Learns seasonal patterns.
- **Training:** Run `bash scripts/train-model.sh` after accumulating ≥7 days of data.
- **Manual selection:** Set `TRACKING_MODE=ml` in `.env`.

---

## Feature 5 — Energy logging and analytics

Log and visualize energy production over time.

**Logged data (every 60 seconds by default):**
- Timestamp
- Panel voltage, current, power
- Pan and tilt angles
- LDR readings (4 channels)
- Tracking mode (LDR / astronomical / ML / manual)
- Weather conditions (if enabled)

**Analytics (dashboard Energy page):**

| Chart/Report | Description |
|---|---|
| **Daily energy curve** | Power output over one day (sunrise to sunset) |
| **Daily energy total** | Total Wh harvested per day |
| **Weekly/monthly trend** | Energy production trend over time |
| **Tracking vs. fixed comparison** | Estimated gain of tracking vs. a fixed-angle panel |
| **Angle heatmap** | Best angles by time of day |
| **Weather impact** | Power output correlation with weather conditions |
| **CSV export** | Download raw data for external analysis |

---

## Feature 6 — Weather-aware tracking

Use weather forecasts to optimize tracking behavior.

- **OpenWeatherMap API:** Free tier provides current weather and 3-hour forecasts (1,000 calls/day).
- **Cloud cover awareness:** If forecast predicts heavy clouds, switch to astronomical mode (saves servo power).
- **Clear sky optimization:** On clear days, use LDR tracking for maximum precision.
- **Configurable:** Set `WEATHER_ENABLED=true` and `WEATHER_API_KEY` in `.env`.

---

## Feature 7 — Servo sleep mode

Save power overnight by parking the panel and disabling tracking.

- **Sunset detection:** When the power output drops below a threshold (or astronomical calculation shows sunset), the system parks the panel.
- **Park position:** Panel moves to the optimal sunrise angle for the next morning (calculated astronomically).
- **Servo disable:** PWM signal is stopped after parking — servos draw no power while sleeping.
- **Sunrise wake:** Tracking resumes when the sun rises (detected by LDR or astronomical time).
- **Configurable:** Set `SLEEP_ENABLED=true` in `.env`.

---

## Feature 8 — Web dashboard

A real-time web interface for monitoring and controlling the solar tracker.

| Section | Description |
|---|---|
| **Dashboard** | Live power gauge, angle display, LDR readings, sun position, tracking status |
| **Energy** | Energy analytics: daily/weekly/monthly charts, total Wh, comparisons |
| **Tracking** | Tracking mode selection (LDR/astronomical/ML/manual), manual servo control |
| **Settings** | Location, weather API, servo limits, tracking interval, password |

**Real-time features:**
- **Power gauge** — live voltage, current, power readings via WebSocket.
- **Angle display** — current pan/tilt angles with animated servo position.
- **LDR heatmap** — 4-quadrant light intensity display.
- **Sun position** — compass showing calculated sun azimuth and elevation.
- **Tracking status** — current mode (LDR/astro/ML) and last adjustment time.

**Manual control (Tracking page):**
- Sliders to manually set pan and tilt angles.
- Buttons: Track Now (single adjustment), Park, Wake.
- Mode selector: LDR, Astronomical, ML, Manual.
- Calibrate LDR sensors.

---

## Wiring diagram

### ADS1115 ADC (I2C)

| ADS1115 Pin | Pi GPIO Pin | Notes |
|---|---|---|
| VDD | 3.3V (Pin 1) | Power |
| GND | GND (Pin 6) | Ground |
| SCL | GPIO 3 (Pin 5) | I2C clock |
| SDA | GPIO 2 (Pin 3) | I2C data |
| A0 | LDR Top-Left | Via 10kΩ voltage divider |
| A1 | LDR Top-Right | Via 10kΩ voltage divider |
| A2 | LDR Bottom-Left | Via 10kΩ voltage divider |
| A3 | LDR Bottom-Right | Via 10kΩ voltage divider |

### INA219 Power Monitor (I2C)

| INA219 Pin | Connection | Notes |
|---|---|---|
| VCC | 3.3V (Pin 1) | Power |
| GND | GND (Pin 9) | Ground |
| SCL | GPIO 3 (Pin 5) | Shared I2C clock (same bus as ADS1115) |
| SDA | GPIO 2 (Pin 3) | Shared I2C data (same bus as ADS1115) |
| VIN+ | Solar panel + | High-side current sense |
| VIN− | Load + (or measurement resistor) | Current flows through |

### LDR Voltage Divider (×4)

```
3.3V ── LDR ──┬── 10kΩ ── GND
              │
              └── ADS1115 Ax input
```

### Servos

| Servo | Pi GPIO Pin | Notes |
|---|---|---|
| Pan servo (signal) | GPIO 18 (Pin 12) | Hardware PWM channel 0 |
| Tilt servo (signal) | GPIO 19 (Pin 35) | Hardware PWM channel 1 |
| Both servos VCC | 5V (Pin 2 or 4) | **Power from 5V rail** |
| Both servos GND | GND (Pin 14) | Common ground |

> **Note:** For MG996R or heavier servos, use an external 5V power supply (not the Pi's 5V rail) to avoid brownouts.

### Solar panel

| Connection | Where | Notes |
|---|---|---|
| Solar panel + | INA219 VIN+ | Positive terminal |
| Solar panel − | INA219 GND / load | Negative terminal |

---

## Frame and mount

### Prototype (SG90 servos + small panel)

- **Pan-tilt bracket:** Two SG90 servos mounted in an L-bracket. Available pre-made (~$5) or 3D-printed.
- **Panel mount:** Glue or tape the 110×60mm solar panel to the top platform of the tilt servo.
- **LDR mount:** Glue 4 LDRs in a cross pattern on a small board, with a 1cm divider wall (cardboard or 3D-printed) between them. Mount this board on the panel.
- **Base:** Secure the pan servo to a stable base (weight, clamp, or screws).

### Production upgrade (stepper motors)

For larger panels (12V 10W+), replace SG90 servos with:
- **NEMA 17 stepper motors** (×2) + **DRV8825 stepper drivers** (×2).
- More torque, more precise, no jitter.
- Requires a more robust mechanical frame (aluminum extrusion or welded steel).

---

## Authentication

The web dashboard is protected by session-based authentication.

- Credentials are stored in `.env` (`ADMIN_USERNAME` and `ADMIN_PASSWORD`).
- Login attempts are rate-limited (10 attempts per 15 minutes) to prevent brute-force.
- Sessions expire after 24 hours.
- Passwords can be changed from **Settings → Change Password** in the dashboard.

---

## How to deploy to Raspberry Pi

Your SSH config is already set up at `~/.ssh/config`:

```
Host rasp-pi
    HostName 192.168.216.90
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

**Method A — Use the deploy script (recommended)**

From the project directory on your laptop:

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/SolarTracker
```

This will:
1. Create the remote directory.
2. Rsync all project files (excludes `venv`, `.env`, `.git`, `data/`).
3. Create a virtual environment and install dependencies on the Pi.
4. Create `.env` from `.env.default` if it does not exist.

**Method B — Manual rsync**

```bash
rsync -avz --delete \
  --exclude='venv/' \
  --exclude='.env' \
  --exclude='.git/' \
  --exclude='data/' \
  ./ \
  rasp-pi:/home/pi/Projects/SolarTracker/

ssh rasp-pi "cd /home/pi/Projects/SolarTracker && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
```

---

## How to run on the Raspberry Pi

**1. SSH into the Pi**

```bash
ssh rasp-pi
```

**2. Go to the project directory**

```bash
cd /home/pi/Projects/SolarTracker
```

**3. Enable I2C and set up hardware**

```bash
sudo bash scripts/setup-i2c.sh
sudo bash scripts/setup-servo.sh
```

**4. Verify I2C devices**

```bash
i2cdetect -y 1
```

You should see the ADS1115 at `0x48` and INA219 at `0x40`.

**5. Edit the .env file**

```bash
nano .env
```

Set `SESSION_SECRET`, `ADMIN_PASSWORD`, `LATITUDE`, `LONGITUDE`, and `TIMEZONE`.

**6. Calibrate the LDR sensors**

```bash
bash scripts/calibrate-ldr.sh
```

Follow the prompts to set baseline values for your LDR sensors.

**7. Start the solar tracker**

```bash
source venv/bin/activate
python app.py
```

Access the dashboard at `http://192.168.216.90:5000`.

**8. (Optional) Train the ML model**

After ≥7 days of energy data:

```bash
bash scripts/train-model.sh
```

Then set `TRACKING_MODE=ml` in `.env` to use the trained model.

**9. (Optional) Run as a systemd service**

```bash
sudo nano /etc/systemd/system/solar-tracker.service
```

```ini
[Unit]
Description=Solar Panel Follower
After=network-online.target pigpiod.service
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/SolarTracker
ExecStart=/home/pi/Projects/SolarTracker/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable solar-tracker
sudo systemctl start solar-tracker
```

---

## Real-world applications

| Application | Who uses it | Why |
|---|---|---|
| **Solar energy education** | Teachers, students | Hands-on project combining electronics, programming, physics, and ML |
| **Off-grid power optimization** | Off-grid homes, cabins | Maximize solar energy harvest from small panels |
| **IoT sensor power** | Remote sensor deployments | Keep a solar-powered Pi running 24/7 in the field |
| **Solar research** | Researchers, hobbyists | Measure and log solar energy production, compare tracking vs. fixed |
| **Garden/greenhouse** | Gardeners, farmers | Power garden sensors and irrigation from a tracked solar panel |
| **STEM competitions** | Students, makers | Science fair or robotics competition project |
| **Portable solar charger** | Campers, travelers | Maximize charge rate for USB devices while camping |
| **Weather station power** | Weather enthusiasts | Solar-powered weather station with energy analytics |
| **Maker community** | Hardware hobbyists | Learn servo control, ADC, I2C, ML, and web development |

---

## Security notes

- **Change the default password immediately** after first login. Use the Settings page or edit `.env`.
- **Generate a strong `SESSION_SECRET`** — run: `python -c "import secrets; print(secrets.token_hex(32))"`
- **The `.env` file contains sensitive data** (password, weather API key). It is in `.gitignore` and should never be committed. Protect it: `chmod 600 .env`
- **Weather API key:** The free tier OpenWeatherMap key allows 1,000 calls/day. Do not expose it publicly.
- **Rate limiting** is enabled on the login endpoint.
- **GPIO access requires appropriate permissions.** Add `pi` to the `gpio` and `i2c` groups: `sudo usermod -aG gpio,i2c pi`.
- **Servo power:** Heavy servos can draw enough current to brown out the Pi. Use an external 5V supply for MG996R or larger servos.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| I2C devices not detected | Enable I2C: `sudo raspi-config` → Interface Options → I2C. Run `i2cdetect -y 1`. Check wiring. |
| ADS1115 not at 0x48 | Check ADDR pin (GND = 0x48, VDD = 0x49). Verify SDA/SCL connections. |
| INA219 not at 0x40 | Check A0/A1 jumpers. Verify I2C wiring. |
| Servo jittering | Use `pigpio` hardware PWM instead of RPi.GPIO software PWM. Run `sudo pigpiod`. |
| Servo not moving | Check PWM pin number. Verify 5V power. Test with `pigs s 18 1500` (center position). |
| LDR readings all zero | Check voltage divider wiring. Verify ADS1115 address. Run `calibrate-ldr.sh`. |
| LDR readings saturated | LDRs may be getting direct sunlight without diffusion. Add a thin diffuser or adjust divider resistor values. |
| Power reads zero | Check INA219 wiring. Ensure solar panel is connected to VIN+/VIN−. Verify load is in circuit. |
| Astronomical tracking inaccurate | Verify `LATITUDE`, `LONGITUDE`, and `TIMEZONE` in `.env`. Check system time: `date`. |
| ML model poor predictions | Need ≥7 days of data. Retrain: `bash scripts/train-model.sh`. Check data quality in energy log. |
| Mock mode on Pi | Ensure I2C libraries installed: `pip install adafruit-circuitpython-ads1x15 adafruit-circuitpython-ina219`. |
| Dashboard not loading | Check if the server is running. Verify IP and port. Check `python app.py` output. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- See [task.md](task.md) for the engineering checklist with step-by-step implementation tasks.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model and mitigations.
