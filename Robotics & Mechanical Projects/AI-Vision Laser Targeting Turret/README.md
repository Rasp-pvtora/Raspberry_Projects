# AI-Vision Laser Targeting Turret

<div align="center">

![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![PID](https://img.shields.io/badge/PID-Control_Loop-00BCD4?style=for-the-badge)
![Servo](https://img.shields.io/badge/SG90-Pan_Tilt_Gimbal-4CAF50?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-SocketIO_Dashboard-000000?style=for-the-badge&logo=flask&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-4%2F5-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A 2/3-axis laser targeting turret controlled by a Raspberry Pi with computer vision. Pi Camera detects targets (color, face, trained object), calculates target pixel position, converts to gimbal pan/tilt coordinates, and uses PID control to keep the laser centered on moving targets. Includes a Flask + SocketIO dark-themed web dashboard with PID tuning, multi-target mode, safety zones, recording, and day/night switching. Applications: pest control, optical alignment, educational tracking. Difficulty: 6/10.**

[Laser Safety](#%EF%B8%8F-laser-safety-warning) • [Features](#features) • [Hardware](#hardware-requirements) • [Budget](#budget) • [Quick Start](#quick-start) • [Configuration](#environment-configuration) • [Web Dashboard](#web-dashboard) • [Troubleshooting](#troubleshooting)

</div>

---

**If you find this project useful, consider supporting development:**

**BTC:** `bc1q...`

---

## ⚠️ LASER SAFETY WARNING

> **THIS PROJECT USES A CLASS 3R LASER (5 mW). FAILURE TO FOLLOW SAFETY PRECAUTIONS CAN CAUSE PERMANENT EYE DAMAGE.**

| Rule | Details |
|---|---|
| **Never point at eyes** | A 5 mW laser causes retinal damage in <0.25 seconds. Never aim at people, animals (except designated pest deterrent), or reflective surfaces. |
| **Wear laser safety goggles** | OD 2+ goggles rated for your laser wavelength (532 nm green / 650 nm red / 808 nm IR). |
| **IR laser is invisible** | The optional IR laser (808 nm) is invisible to the naked eye but still dangerous. Always use IR-rated goggles when testing. |
| **Define safety zones** | Use the `ENABLE_SAFETY_ZONES` feature to define no-fire pixel regions in the camera frame (e.g., doorways, windows, seating areas). |
| **Use the kill switch** | The software kill switch (`ENABLE_LASER_KILL_SWITCH`) and physical GPIO kill switch immediately cut laser power. Test before every session. |
| **Supervise operation** | Never leave the turret running unattended. Use `SESSION_RECORDING` to review autonomous sessions. |
| **Check local laws** | Laser pointer regulations vary by country/state. Many jurisdictions restrict lasers >1 mW. Verify legality before use. |
| **Enclose the workspace** | When possible, operate in an enclosed area with non-reflective walls to contain stray beams. |
| **Label the device** | Affix a "DANGER — LASER RADIATION" warning label per IEC 60825-1 / 21 CFR 1040. |

**By building and operating this project, you accept full responsibility for laser safety compliance.**

---

## Table of Contents

- [Laser Safety Warning](#%EF%B8%8F-laser-safety-warning)
- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Wiring Diagram](#wiring-diagram)
- [Libraries & Dependencies](#libraries--dependencies)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [System Overview](#system-overview)
- [Features](#features)
  - [PID Controller](#pid-controller)
  - [Multi-Target Mode](#multi-target-mode)
  - [Predictive Aim](#predictive-aim)
  - [Safety Zones](#safety-zones)
  - [Day/Night Mode](#daynight-mode)
  - [Session Recording](#session-recording)
  - [Target Lock](#target-lock)
  - [Range Estimation](#range-estimation)
  - [Sound Deterrent Mode](#sound-deterrent-mode)
- [Web Dashboard](#web-dashboard)
- [Authentication](#authentication)
- [How to Deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
- [How to Run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
AI-Vision Laser Targeting Turret/
├── README.md                        # This file
├── TSD.md                          # Technical Specification Document
├── task.md                         # Development task checklist
├── implementation_plan.md          # Phased implementation guide
├── app.py                          # Python entry point (Flask + SocketIO + main loop)
├── requirements.txt                # Python dependencies
├── .env.default                    # Environment variable template (copy to .env)
├── .gitignore                      # Git ignore rules
├── src/
│   ├── targeting/
│   │   ├── pid_controller.py       # PID control loop (P/I/D tunable from dashboard)
│   │   ├── target_tracker.py       # Multi-target tracking, prioritization, lock-on
│   │   ├── predictive_aim.py       # Velocity-based motion prediction / lead aim
│   │   ├── range_estimator.py      # Known object size → distance estimation
│   │   └── coordinate_mapper.py    # Pixel (u,v) → gimbal (pan°, tilt°) mapping
│   ├── vision/
│   │   ├── camera.py               # Pi Camera / NoIR capture and frame pipeline
│   │   ├── color_detector.py       # HSV color-based target detection
│   │   ├── face_detector.py        # Haar cascade / DNN face detection
│   │   ├── object_detector.py      # Trained object detection (Haar / TFLite)
│   │   ├── motion_detector.py      # Background subtraction motion detection
│   │   └── day_night.py            # Ambient light sensing + camera/laser switching
│   ├── hardware/
│   │   ├── servo_controller.py     # SG90 servo driver (pigpio PWM for pan/tilt/yaw)
│   │   ├── laser_controller.py     # Laser module GPIO control (visible + IR)
│   │   ├── buzzer_controller.py    # Piezo buzzer for sound deterrent mode
│   │   ├── gpio_controller.py      # Kill switch, status LEDs
│   │   └── mock_hardware.py        # Mock servos + laser + GPIO for dev without hardware
│   ├── control/
│   │   ├── turret_controller.py    # High-level: scan, acquire, track, fire
│   │   ├── safety_manager.py       # Safety zones (no-fire pixel regions), kill switch
│   │   └── session_recorder.py     # Record tracking sessions (video + CSV log)
│   ├── routes/
│   │   ├── auth.py                 # Login / logout routes
│   │   ├── dashboard.py            # Dashboard page and API
│   │   ├── control_api.py          # Manual aim, laser toggle, target lock API
│   │   ├── pid_api.py              # PID tuning API (live P/I/D adjustment)
│   │   ├── vision_api.py           # Camera feed and detection API
│   │   └── settings.py             # Settings API
│   └── services/
│       ├── db.py                   # SQLite database initialization
│       ├── session_store.py        # Tracking session persistence
│       └── system_service.py       # System info (temp, memory, CPU)
├── config/
│   ├── safety_zones.json           # No-fire pixel region definitions
│   ├── target_classes.json         # Target class priorities and sizes
│   └── sessions/                   # Saved tracking session recordings
│       └── .gitkeep
├── data/
│   └── turret.db                   # SQLite database
├── templates/                      # Jinja2 HTML templates
│   ├── layout.html                 # Base layout with sidebar navigation
│   ├── login.html                  # Login page
│   ├── dashboard.html              # Main targeting dashboard
│   ├── pid.html                    # PID tuning interface
│   ├── camera.html                 # Camera feed and detection view
│   └── settings.html               # Configuration and safety zones
├── static/
│   ├── css/style.css               # Dark theme stylesheet
│   └── js/
│       ├── main.js                 # SocketIO client + shared utilities
│       ├── targeting.js            # Targeting controls (aim, lock, fire)
│       ├── pid_tuner.js            # PID slider controls + response graph
│       ├── camera_feed.js          # Live camera feed + detection overlay
│       └── safety_zones.js         # Safety zone drawing on camera frame
├── scripts/
│   ├── calibrate_gimbal.py         # Servo range → pixel mapping calibration
│   ├── test_servos.py              # Test pan/tilt/yaw sweep
│   ├── test_laser.py               # Test laser on/off + kill switch
│   └── tune_pid.py                 # CLI PID tuning helper (step response)
├── deploy/
│   └── deploy_to_pi.sh             # rsync-based deploy script
├── docs/
│   ├── wiring_diagram.md           # Complete wiring reference
│   ├── pid_tuning_guide.md         # PID tuning walkthrough
│   ├── laser_safety.md             # Detailed laser safety reference
│   └── threat_model.md             # Threat model and mitigations
└── tests/
    ├── test_pid_controller.py      # PID unit tests
    ├── test_coordinate_mapper.py   # Pixel → gimbal mapping tests
    ├── test_safety_manager.py      # Safety zone tests
    └── test_predictive_aim.py      # Prediction accuracy tests
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (2 GB+) / Pi 5 | Yes | Pi 5 recommended for vision + PID at higher FPS |
| Pan-Tilt Bracket | Yes | Two-axis gimbal bracket (~$3–5) |
| SG90 Micro Servos ×2 | Yes | Pan servo + tilt servo (9g, 180°) |
| Laser Module (5 mW, 650 nm red) | Yes | 3.3V or 5V laser diode module |
| Pi Camera Module v2/v3 | Yes | Target detection |
| MicroSD Card (32 GB+) | Yes | For OS, recordings, and data |

### Optional Hardware

| Component | Required | Notes |
|---|---|---|
| 3rd SG90 Servo (yaw axis) | No | Adds a third axis for finer aim adjustment |
| IR Laser Module (808 nm) | No | Invisible laser for night/covert mode |
| NoIR Camera Module | No | Required for IR laser — sees IR illumination |
| Piezo Buzzer | No | Sound deterrent mode (with or instead of laser) |
| Physical Kill Switch (N/O) | No | GPIO-wired emergency laser cutoff |
| LED Indicators | No | Status LEDs (tracking, laser active, error) |

---

## Budget

| Item | Estimated Cost |
|---|---|
| Pan-Tilt Bracket + 2× SG90 Servos | $6–10 |
| Laser Module (5 mW, 650 nm red) | ~$3 |
| Pi Camera Module v2 | ~$25 |
| **Total (core build)** | **~$34–38** |

Optional add-ons:

| Item | Estimated Cost |
|---|---|
| 3rd SG90 Servo (yaw axis) | ~$3 |
| IR Laser Module (808 nm) | ~$10 |
| NoIR Camera Module (replaces standard) | ~$25 |
| Piezo Buzzer | ~$1 |
| Kill Switch Button | ~$2 |

**Total with all options:** ~$71

*(Assumes you already own a Raspberry Pi 4/5 with power supply and MicroSD.)*

---

## Wiring Diagram

### SG90 Servos → Pi GPIO (via pigpio)

| Servo | GPIO | Pin | Notes |
|---|---|---|---|
| Pan (horizontal) | GPIO 12 (PWM0) | Pin 32 | Hardware PWM for smooth movement |
| Tilt (vertical) | GPIO 13 (PWM1) | Pin 33 | Hardware PWM for smooth movement |
| Yaw (optional 3rd) | GPIO 18 | Pin 12 | Software PWM via pigpio |

> **Note:** pigpio provides hardware-timed PWM on all GPIO pins, eliminating SG90 jitter common with RPi.GPIO software PWM.

### Servo Power

| Connection | Detail |
|---|---|
| Servo VCC (red) | 5V (pin 2 or 4) — OK for 2–3 SG90s at 9g each |
| Servo GND (brown) | GND (pin 6) |

> **Note:** SG90 servos draw ~250 mA each under load. Two SG90s can safely run from the Pi 5V rail. For 3 servos or if you see jitter, use an external 5V 1A supply.

### Laser Module → Pi GPIO

| Pin | GPIO | Notes |
|---|---|---|
| Laser Signal (visible) | GPIO 17 (pin 11) | HIGH = laser on, LOW = laser off |
| Laser Signal (IR, optional) | GPIO 27 (pin 13) | HIGH = IR laser on |
| Laser VCC | 3.3V (pin 1) or 5V (pin 2) | Match laser module voltage |
| Laser GND | GND (pin 9) | Common ground |

> **Warning:** Use a transistor (2N2222 or MOSFET) to switch laser modules that draw >16 mA. Pi GPIO can source only 16 mA per pin. Most 5 mW modules draw 20–30 mA and need a switching transistor.

### Pi Camera → Pi CSI

| Connection | Detail |
|---|---|
| Ribbon cable | Pi CSI port → Camera module (or NoIR module) |
| Verify | `libcamera-hello` |

### Buzzer (Optional) → Pi GPIO

| Pin | GPIO | Notes |
|---|---|---|
| Buzzer Signal | GPIO 22 (pin 15) | Active buzzer: HIGH = on. Passive: PWM for tone. |
| Buzzer GND | GND (pin 14) | Common ground |

### Kill Switch (Optional) → Pi GPIO

| Pin | GPIO | Notes |
|---|---|---|
| Kill Switch (N/O) | GPIO 4 (pin 7) | Internal pull-up, active LOW on press |
| Status LED (Green) | GPIO 23 (pin 16) | Tracking active indicator |
| Status LED (Red) | GPIO 24 (pin 18) | Laser active indicator |

> **Warning:** Wire the kill switch as normally-open so a disconnected wire defaults to laser OFF (safe state).

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| [Flask](https://flask.palletsprojects.com/) | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | WebSocket for real-time camera feed + turret state |
| [Jinja2](https://jinja.palletsprojects.com/) | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Load environment variables from `.env` |
| [opencv-python-headless](https://pypi.org/project/opencv-python-headless/) | Camera capture, face detection, color tracking, motion detection |
| [numpy](https://numpy.org/) | Coordinate math, PID calculations, prediction vectors |
| [pigpio](http://abyz.me.uk/rpi/pigpio/python.html) | Hardware-timed servo PWM (jitter-free SG90 control) |
| [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) | Laser GPIO, kill switch, LEDs, buzzer |
| [bcrypt](https://pypi.org/project/bcrypt/) | Password hashing for dashboard auth |

### Dev Dependencies

| Library | Purpose |
|---|---|
| [pytest](https://docs.pytest.org/) | Testing framework |

---

## Quick Start

```bash
# 1. SSH into the Pi
ssh rasp-pi          # alias for pi@192.168.216.90

# 2. Clone the repo
git clone <repo-url> ~/Projects/LaserTurret && cd ~/Projects/LaserTurret

# 3. Create .env from template
cp .env.default .env
nano .env              # Set SESSION_SECRET, ADMIN_PASSWORD, PID gains

# 4. Virtual environment and dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Start pigpio daemon (required for servo PWM)
sudo pigpiod

# 6. Enable camera
sudo raspi-config     # Interface Options → Camera → Enable
libcamera-hello       # Verify camera feed

# 7. Calibrate gimbal (map servo range to camera pixel range)
python scripts/calibrate_gimbal.py

# 8. Test servos and laser
python scripts/test_servos.py
python scripts/test_laser.py

# 9. Start the server
python app.py

# 10. Open dashboard → http://192.168.216.90:5000
```

---

## Environment Configuration

Copy `.env.default` to `.env`. **Never commit `.env` to git.**

See [TSD.md — §4 Environment Configuration](TSD.md#4--environment-configuration-envdefault) for the full `.env.default` block.

Key toggles:

| Variable | Default | Description |
|---|---|---|
| `ENABLE_PID_CONTROLLER` | `true` | PID tracking loop (tunable P/I/D from dashboard) |
| `ENABLE_MULTI_TARGET` | `false` | Track multiple targets, prioritize by class/size/proximity |
| `ENABLE_PREDICTIVE_AIM` | `false` | Lead target based on velocity vector |
| `ENABLE_SAFETY_ZONES` | `true` | No-fire pixel regions on camera frame |
| `ENABLE_DAY_NIGHT` | `false` | Auto-switch visible/IR laser + camera |
| `ENABLE_RECORDING` | `false` | Save tracking sessions (video + CSV) |
| `ENABLE_TARGET_LOCK` | `true` | Button to lock on nearest target |
| `ENABLE_RANGE_ESTIMATION` | `false` | Known object size → distance estimation |
| `ENABLE_SOUND_DETERRENT` | `false` | Buzzer instead of/with laser |
| `ENABLE_LASER_KILL_SWITCH` | `true` | Software + GPIO kill switch for laser |
| `ENABLE_MOCK_HARDWARE` | `false` | Simulated servos + laser for dev |
| `DETECTION_MODE` | `color` | Detection: `color`, `face`, `object`, `motion` |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Web Browser (Dark Theme Dashboard)                  │
│  ┌────────────┐ ┌──────────────┐ ┌───────────┐ ┌────────────────┐   │
│  │ Targeting  │ │ PID Tuning   │ │ Live      │ │ Safety Zones   │   │
│  │ Controls   │ │ P/I/D Sliders│ │ Camera    │ │ Draw/Edit      │   │
│  └──────┬─────┘ └──────┬───────┘ └─────┬─────┘ └───────┬────────┘   │
│         └──────────────┼───────────────┼────────────────┘            │
│                        │ SocketIO (WebSocket)                         │
└────────────────────────┼─────────────────────────────────────────────┘
                         │ http://192.168.216.90:5000
┌────────────────────────▼─────────────────────────────────────────────┐
│                    Raspberry Pi (Flask + SocketIO)                     │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                  Flask + SocketIO Server                          │ │
│  │       (dashboard, auth, control API, camera feed, PID API)       │ │
│  └──────────────────────────┬───────────────────────────────────────┘ │
│                              │                                        │
│  ┌──────────┐  ┌────────────▼───────┐  ┌───────────────────────────┐ │
│  │ Pi Camera│  │   Vision Pipeline   │  │    Turret Controller      │ │
│  │ v2/v3   ├──► Color / Face /      │  │  ┌──────────┐ ┌────────┐ │ │
│  │ (NoIR)   │  │ Object / Motion    ├──►  │   PID    │ │Safety  │ │ │
│  └──────────┘  │ → target (u,v)     │  │  │Controller│ │Manager │ │ │
│                 └────────────────────┘  │  └─────┬────┘ └───┬────┘ │ │
│                                         │        │          │       │ │
│  ┌──────────┐  ┌────────────────────┐  │  ┌─────▼──────────▼────┐ │ │
│  │ SG90     │  │  Coordinate        │  │  │  Pan/Tilt Angles    │ │ │
│  │ Servos   ◄──┤  Mapper            ◄──┘  │  → Servo PWM        │ │ │
│  │ (pigpio) │  │  pixel→gimbal°     │     │  → Laser On/Off     │ │ │
│  └──────────┘  └────────────────────┘     └─────────────────────┘ │ │
│                                                                       │
│  ┌──────────┐  ┌────────────────────┐  ┌───────────────────────────┐ │
│  │ Laser    │  │  Session Recorder   │  │   Predictive Aim          │ │
│  │ Module   │  │  Video + CSV log   │  │   Velocity → lead angle   │ │
│  │ (Vis/IR) │  └────────────────────┘  └───────────────────────────┘ │
│  └──────────┘                                                         │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    Safety Manager                                 │ │
│  │  Safety zones │ Kill switch │ Laser timeout │ Day/night switch   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

Targeting Pipeline:
  Camera frame → Detect target (color/face/object/motion)
  → Target centroid (u,v) → Error = centroid − frame center
  → PID controller → pan/tilt correction angles
  → Coordinate mapper → servo PWM update
  → Safety zone check → Laser ON if target in safe region
  → Repeat at TRACKING_FPS Hz
```

---

## Features

### PID Controller

A tunable proportional-integral-derivative control loop keeps the laser centered on the target:

- **P (Proportional):** Correction proportional to pixel error. Higher P = faster response, but overshoot.
- **I (Integral):** Accumulates error over time. Eliminates steady-state offset (e.g., gravity droop on tilt servo).
- **D (Derivative):** Damps oscillations based on error rate of change. Prevents overshooting.

Tune P/I/D live from the dashboard via sliders. The step-response graph shows real-time convergence. Separate PID banks for pan and tilt axes.

Toggle: `ENABLE_PID_CONTROLLER=true` in `.env`.

### Multi-Target Mode

When `ENABLE_MULTI_TARGET=true`:

- Detects and tracks all visible targets simultaneously.
- Prioritization strategies (configurable):
  - **By class:** Prefer faces over colors, or specific trained objects.
  - **By size:** Largest target first (closest/most prominent).
  - **By proximity:** Target nearest to current laser position (minimize servo travel).
- Cycles between targets at configurable interval or on target-lost.
- Dashboard shows all detected targets with priority overlay.

### Predictive Aim

When `ENABLE_PREDICTIVE_AIM=true`:

- Estimates target velocity from consecutive frame positions (Kalman filter or simple averaging).
- Computes a lead angle: where the target will be by the time servos complete their move.
- Particularly effective for fast-moving targets where PID alone introduces lag.
- Lead amount configurable via `PREDICTION_FRAMES` (number of frames to look ahead).

### Safety Zones

When `ENABLE_SAFETY_ZONES=true`:

- Define rectangular regions on the camera frame where the laser must not fire.
- Draw zones interactively on the dashboard camera feed (click-drag rectangles).
- Zones saved to `config/safety_zones.json`.
- If the target enters a safety zone, laser turns OFF but tracking continues.
- Laser resumes when target exits the safety zone.
- Use cases: exclude doorways, windows, pet sleeping areas, reflective surfaces.

### Day/Night Mode

When `ENABLE_DAY_NIGHT=true`:

- **Day mode:** Standard Pi Camera + visible red laser (650 nm).
- **Night mode:** NoIR Camera + IR laser (808 nm) — invisible to humans, visible to camera.
- Auto-switch based on ambient light level (computed from frame brightness).
- Manual override from dashboard.
- Requires optional NoIR camera and IR laser module.

### Session Recording

When `ENABLE_RECORDING=true`:

- Records tracking sessions as video (annotated frames with crosshair + target box).
- Simultaneously logs CSV data: timestamp, target (u,v), gimbal angles, laser state, PID output.
- Sessions saved to `config/sessions/` with timestamped filenames.
- Replay sessions from dashboard (video player + data overlay).
- Useful for PID tuning analysis and reviewing autonomous operation.

### Target Lock

When `ENABLE_TARGET_LOCK=true`:

- Dashboard button or keyboard shortcut to lock onto the nearest detected target.
- Once locked, the turret ignores other targets and tracks only the locked target.
- Lock persists until: target is lost for `LOCK_TIMEOUT_SEC`, user unlocks, or kill switch.
- Visual indicator on camera feed (lock icon + reticle around locked target).

### Range Estimation

When `ENABLE_RANGE_ESTIMATION=true`:

- Estimates distance to target using known object size and apparent pixel size.
- Formula: `distance = (known_size × focal_length) / pixel_size`.
- Requires target class to have a `known_size_mm` entry in `config/target_classes.json`.
- Distance displayed on dashboard and logged in session CSV.
- Useful for adjusting PID gains at different ranges (far targets need less correction).

### Sound Deterrent Mode

When `ENABLE_SOUND_DETERRENT=true`:

- Activates a piezo buzzer when a target is tracked.
- Configurable modes:
  - **Buzzer only:** Sound without laser (non-harmful pest deterrent).
  - **Buzzer + laser:** Combined audio-visual deterrent.
  - **Pulsed:** Buzzer pulses at configurable frequency for attention-getting.
- Frequency and pattern configurable via `.env`.
- Useful for bird/animal deterrent applications where laser alone is insufficient.

---

## Web Dashboard

The dark-themed web dashboard runs at `http://192.168.216.90:5000` and connects via SocketIO:

- **Dark theme:** Background `#1a1a2e`, accent `#0f3460`, card `#16213e`.
- **Responsive layout:** Sidebar navigation on desktop, bottom nav on mobile.
- **Pages:** Dashboard (live targeting), PID Tuning, Camera, Settings.
- **Kill switch:** Red laser kill button visible on every page — immediately cuts laser power.

| Tab | Controls |
|---|---|
| **Dashboard** | Live camera with crosshair + target overlay, manual aim (click to point), laser toggle, target lock button, gimbal position, range readout |
| **PID Tuning** | Pan P/I/D sliders, tilt P/I/D sliders, step-response graph, save/load PID presets |
| **Camera** | Full camera feed, detection mode toggle, safety zone drawing, multi-target list |
| **Settings** | Detection config, servo calibration, day/night, recording, buzzer, system info |

Real-time features via SocketIO:
- Camera frames with detection overlay at `TRACKING_FPS`.
- Gimbal angles and PID error streamed at 20 Hz.
- Click-to-aim: click anywhere on camera feed → turret points there.
- Kill switch on every page.

---

## Authentication

- Session-based login with bcrypt password hashing.
- Rate limiting: 10 attempts per 15 minutes per IP.
- Session expiry: 24 hours.
- Default credentials set in `.env` (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).
- Password changeable from Settings page.

---

## How to Deploy to Raspberry Pi

SSH config at `~/.ssh/config`:

```
Host rasp-pi
    HostName 192.168.216.90
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

**Deploy script:**

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/LaserTurret
```

**Manual:**

```bash
rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' --exclude='data/' --exclude='config/sessions/' \
  ./ rasp-pi:/home/pi/Projects/LaserTurret/
```

---

## How to Run on the Raspberry Pi

```bash
ssh rasp-pi
cd /home/pi/Projects/LaserTurret
nano .env   # Set SESSION_SECRET, ADMIN_PASSWORD, PID gains
source venv/bin/activate
sudo pigpiod          # Start pigpio daemon for servo PWM
python app.py
```

Access: `http://192.168.216.90:5000`

**systemd service:**

```ini
[Unit]
Description=AI-Vision Laser Targeting Turret
After=network-online.target pigpiod.service
Wants=network-online.target pigpiod.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/LaserTurret
ExecStartPre=/usr/bin/pigpiod
ExecStart=/home/pi/Projects/LaserTurret/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

---

## Security Notes

- Change the default password immediately.
- Generate a strong `SESSION_SECRET`: `python -c "import secrets; print(secrets.token_hex(32))"`
- `.env` contains sensitive data — never commit. Protect: `chmod 600 .env`
- Dashboard is HTTP only — use an nginx reverse proxy with TLS for remote access.
- Laser GPIO has no software interlock beyond the kill switch — physical access to GPIO pins controls the laser.
- Wire the kill switch normally-open so a disconnected wire defaults to laser OFF.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Servos jittering | Ensure `pigpiod` is running: `sudo pigpiod`. Use hardware PWM pins (GPIO 12, 13). Add 100µF cap across servo power. |
| Laser not turning on | Check GPIO 17 wiring. Verify transistor circuit if laser draws >16 mA. Test: `python scripts/test_laser.py`. |
| Camera not detected | `libcamera-hello`. Enable camera in `raspi-config`. Check ribbon cable orientation. |
| PID oscillating | Reduce P gain. Increase D gain. Use the step-response graph on the PID Tuning page. |
| PID slow to converge | Increase P gain. Small I gain helps with steady-state error. See [docs/pid_tuning_guide.md](docs/pid_tuning_guide.md). |
| Target detection unreliable | Adjust HSV ranges for color mode. Improve lighting. Increase `DETECTION_CONFIDENCE` threshold. |
| IR laser not visible on camera | Use NoIR camera module (standard camera has IR filter). Set `CAMERA_TYPE=noir` in `.env`. |
| Safety zones not working | Check `config/safety_zones.json` syntax. Zones are in pixel coordinates matching camera resolution. |
| Kill switch not responding | Check GPIO 4 wiring (N/O to GND). Verify internal pull-up enabled. Test: `python scripts/test_laser.py`. |
| Mock mode not working | Set `ENABLE_MOCK_HARDWARE=true` in `.env`. No servos, laser, or GPIO required. |
| Range estimation inaccurate | Recalibrate focal length (`scripts/calibrate_gimbal.py`). Verify `known_size_mm` in target config. |

---

## Where to Next

- Add a depth camera (Intel RealSense) for true 3D target localization and range.
- Train a custom TFLite model for specific pest detection (birds, squirrels, insects).
- Implement galvanometer-based steering for sub-millisecond laser aim (no servo latency).
- Add a second camera for stereo vision and true triangulated range estimation.
- Integrate with Home Assistant or MQTT for smart home automation triggers.
- Upgrade to a stronger laser (Class 3B) for material etching — requires full enclosure and interlocks.
- Add a LIDAR sensor (VL53L0X) for precise distance measurement.
- Implement object tracking via DeepSORT for more robust multi-target identity persistence.
- Build a waterproof enclosure for outdoor pest deterrent deployment.
