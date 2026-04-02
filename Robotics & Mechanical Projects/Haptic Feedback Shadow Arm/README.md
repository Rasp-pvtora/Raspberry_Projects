# 🤝 Haptic Feedback Shadow Arm

<div align="center">

![Teleoperation](https://img.shields.io/badge/Teleoperation-Master%2FSlave-FF6F00?style=for-the-badge)
![Force Feedback](https://img.shields.io/badge/Force_Feedback-INA219%2BHaptic-00BCD4?style=for-the-badge)
![PCA9685](https://img.shields.io/badge/PCA9685-Servo_Driver-4CAF50?style=for-the-badge)
![ADS1115](https://img.shields.io/badge/ADS1115-ADC_Encoder-9C27B0?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-SocketIO_Dashboard-000000?style=for-the-badge&logo=flask&logoColor=white)
![Three.js](https://img.shields.io/badge/Three.js-3D_Visualization-black?style=for-the-badge&logo=threedotjs&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-4%2F5-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A teleoperation system where a Master Arm (potentiometers/rotary encoders) mirrors its position to a Slave Arm (servos) in real-time. Force feedback reads motor current via INA219 sensors on the slave and drives proportional haptic vibration motors on the master. Includes a Flask + SocketIO dark-themed dashboard with real-time 3D workspace visualization (Three.js), force scaling, recording/playback, precision mode, gripper mirroring, collision detection, and joint auto-calibration. Applications: remote manipulation, surgical training, bomb disposal training, education. Difficulty: 7/10.**

[Features](#features) • [Hardware](#hardware-requirements) • [Budget](#budget) • [Quick Start](#quick-start) • [Configuration](#environment-configuration) • [Web Dashboard](#web-dashboard) • [Troubleshooting](#troubleshooting)

</div>

---

**If you find this project useful, consider supporting development:**

**BTC:** `bc1q...`

---

## Table of Contents

- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Wiring Diagram](#wiring-diagram)
- [Libraries & Dependencies](#libraries--dependencies)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [System Overview](#system-overview)
- [Features](#features)
  - [Master → Slave Mirroring](#master--slave-mirroring)
  - [Force Feedback (INA219 → Haptic)](#force-feedback-ina219--haptic)
  - [Force Scaling](#force-scaling)
  - [Network Teleoperation](#network-teleoperation)
  - [Recording & Playback](#recording--playback)
  - [Speed Limiting](#speed-limiting)
  - [Workspace Visualization (Three.js)](#workspace-visualization-threejs)
  - [Precision Mode](#precision-mode)
  - [Gripper Mirroring](#gripper-mirroring)
  - [Collision Detection](#collision-detection)
  - [Joint Calibration](#joint-calibration)
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
Haptic Feedback Shadow Arm/
├── README.md                        # This file
├── TSD.md                          # Technical Specification Document
├── task.md                         # Development task checklist
├── implementation_plan.md          # Phased implementation guide
├── app.py                          # Python entry point (Flask + SocketIO + main loop)
├── requirements.txt                # Python dependencies
├── .env.default                    # Environment variable template (copy to .env)
├── .gitignore                      # Git ignore rules
├── src/
│   ├── master/
│   │   ├── encoder_reader.py       # ADS1115 ADC reads potentiometers/encoders
│   │   ├── haptic_driver.py        # DRV2605L vibration motor control (force feedback)
│   │   ├── fsr_reader.py           # FSR (force-sensitive resistor) for gripper input
│   │   └── calibration.py          # Joint auto-calibration (sweep + limit detection)
│   ├── slave/
│   │   ├── servo_controller.py     # PCA9685 servo driver (angle → PWM)
│   │   ├── current_sensor.py       # INA219 current sensing per servo
│   │   └── gripper.py              # Slave gripper servo control
│   ├── control/
│   │   ├── mirror_engine.py        # Master → Slave position mirroring loop
│   │   ├── force_feedback.py       # INA219 current → vibration motor intensity
│   │   ├── force_scaler.py         # Adjustable force multiplier/dampening
│   │   ├── speed_limiter.py        # Max angular velocity enforcement per joint
│   │   ├── precision_mode.py       # Reduced motion ratio (10:1) control
│   │   ├── collision_detector.py   # Virtual workspace boundaries + e-stop
│   │   ├── recorder.py             # Record arm movements to file
│   │   ├── player.py               # Replay recorded movements
│   │   └── network_teleop.py       # LAN/WAN teleoperation with latency compensation
│   ├── kinematics/
│   │   ├── forward_kinematics.py   # FK solver using DH parameters
│   │   ├── inverse_kinematics.py   # IK solver (analytical 4-DOF / Jacobian 6-DOF)
│   │   └── dh_params.py            # DH parameter table loader
│   ├── hardware/
│   │   ├── gpio_controller.py      # Emergency stop, LEDs, status
│   │   └── mock_hardware.py        # Mock ADC + servos + sensors for dev without hardware
│   ├── routes/
│   │   ├── auth.py                 # Login / logout routes
│   │   ├── dashboard.py            # Dashboard page and API
│   │   ├── control_api.py          # Mirror control, force scaling, precision mode API
│   │   ├── recording_api.py        # Record/playback API
│   │   ├── visualization_api.py    # Three.js arm state streaming
│   │   └── settings.py             # Settings API
│   └── services/
│       ├── db.py                   # SQLite database initialization
│       ├── recording_store.py      # Recording persistence
│       └── system_service.py       # System info (temp, memory, CPU)
├── config/
│   ├── dh_params.json              # DH parameter table for both arms
│   ├── workspace_bounds.json       # Virtual workspace boundary definitions
│   ├── calibration.json            # Joint calibration data (min/max ADC → angles)
│   └── recordings/                 # Saved movement recordings
│       └── .gitkeep
├── data/
│   └── shadow_arm.db               # SQLite database
├── templates/                      # Jinja2 HTML templates
│   ├── layout.html                 # Base layout with sidebar navigation
│   ├── login.html                  # Login page
│   ├── dashboard.html              # Main control dashboard
│   ├── recording.html              # Recording/playback interface
│   └── settings.html               # Configuration and calibration
├── static/
│   ├── css/style.css               # Dark theme stylesheet
│   └── js/
│       ├── main.js                 # SocketIO client + shared utilities
│       ├── three_visualizer.js     # Three.js 3D arm visualization
│       ├── force_panel.js          # Force feedback graph + scaling controls
│       ├── recording_ui.js         # Record/playback UI
│       └── safety_panel.js         # Collision bounds + e-stop button
├── scripts/
│   ├── test_servos.py              # Test PCA9685 servo sweep
│   ├── test_adc.py                 # Test ADS1115 ADC readings
│   ├── test_current.py             # Test INA219 current sensing
│   ├── test_haptic.py              # Test DRV2605L vibration motors
│   ├── calibrate_joints.py         # Interactive joint calibration helper
│   └── measure_dh.py               # Interactive DH parameter measurement
├── deploy/
│   └── deploy_to_pi.sh             # rsync-based deploy script
├── docs/
│   ├── wiring_diagram.md           # Complete wiring reference
│   ├── dh_parameters.md            # DH parameter measurement guide
│   ├── protocol.md                 # Master-slave communication protocol
│   └── threat_model.md             # Threat model and mitigations
└── tests/
    ├── test_mirror_engine.py       # Mirroring accuracy tests
    ├── test_force_feedback.py      # Force scaling + current-to-vibration tests
    ├── test_collision_detector.py  # Virtual boundary tests
    ├── test_forward_kinematics.py  # FK unit tests
    └── test_speed_limiter.py       # Velocity limit tests
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB+) / Pi 5 | Yes | Runs both master read + slave control loops |
| Robot Arm Kit ×2 (4–6 DOF) | Yes | One master (manual), one slave (servo-driven) |
| Potentiometers or Rotary Encoders ×6 | Yes | Mounted on master arm joints for position sensing |
| ADS1115 16-bit ADC ×2 | Yes | I2C ADC for reading potentiometers (4 ch each) |
| PCA9685 16-Channel Servo Driver ×1 | Yes | PWM driver for slave arm servos |
| MG996R Servos ×6 (or included in kit) | Yes | Slave arm joint actuators |
| INA219 Current Sensors ×4–6 | Yes | Inline on slave servo power for force sensing |
| Vibration Motors ×4 | Yes | Mounted on master arm for haptic force feedback |
| DRV2605L Haptic Driver ×1 | Yes | I2C haptic motor controller with waveform library |
| FSR (Force-Sensitive Resistor) ×1 | No | Master gripper squeeze input |
| 5V Servo Power Supply (5–6V, 5A+) | Yes | Separate supply for slave servos — NOT from Pi |
| MicroSD Card (32 GB+) | Yes | For OS and data |

---

## Budget

| Item | Estimated Cost |
|---|---|
| Robot Arm Kit ×2 (4–6 DOF, with servos) | $60–120 |
| Potentiometers / Rotary Encoders ×6 | $4–12 |
| ADS1115 16-bit ADC ×2 | ~$8 |
| INA219 Current Sensors ×4–6 | $20–30 |
| Vibration Motors ×4 | ~$6 |
| DRV2605L Haptic Driver ×1 | ~$4 |
| PCA9685 Servo Driver ×1 | ~$4 |
| **Total** | **~$102–180** |

*(Assumes you already own a Raspberry Pi 4/5 with power supply and MicroSD. MG996R servos often included with arm kits.)*

---

## Wiring Diagram

### ADS1115 ADC (Master Arm Potentiometers) → Pi I2C

Two ADS1115 boards read 6 potentiometers (4 channels each, 6 used total):

| ADS1115 #1 (0x48) | Connection | Notes |
|---|---|---|
| SDA | GPIO 2 (pin 3) — I2C SDA | Shared I2C bus |
| SCL | GPIO 3 (pin 5) — I2C SCL | Shared I2C bus |
| VDD | 3.3V (pin 1) | Logic power |
| GND | GND (pin 6) | Common ground |
| A0 | Pot J1 wiper | Base joint |
| A1 | Pot J2 wiper | Shoulder joint |
| A2 | Pot J3 wiper | Elbow joint |
| A3 | Pot J4 wiper | Wrist pitch |
| ADDR | GND | Address 0x48 |

| ADS1115 #2 (0x49) | Connection | Notes |
|---|---|---|
| SDA | GPIO 2 (pin 3) — I2C SDA | Shared I2C bus |
| SCL | GPIO 3 (pin 5) — I2C SCL | Shared I2C bus |
| VDD | 3.3V (pin 1) | Logic power |
| GND | GND (pin 6) | Common ground |
| A0 | Pot J5 wiper | Wrist roll |
| A1 | Pot J6 wiper | Wrist yaw |
| A2 | FSR output (voltage divider) | Gripper squeeze |
| ADDR | VDD | Address 0x49 |

> Potentiometer wiring: VCC → pot pin 1, GND → pot pin 3, wiper (pin 2) → ADS1115 Ax input.

### PCA9685 Servo Driver (Slave Arm) → Pi I2C

| PCA9685 Pin | Connection | Notes |
|---|---|---|
| SDA | GPIO 2 (pin 3) — I2C SDA | Shared I2C bus |
| SCL | GPIO 3 (pin 5) — I2C SCL | Shared I2C bus |
| VCC | 3.3V (pin 1) | Logic power from Pi |
| GND | GND (pin 6) | Common ground with Pi |
| V+ | External 5–6V PSU (+) | Servo power — NOT from Pi |
| GND (V+) | External 5–6V PSU (−) | Bridge GND to Pi GND |

### Slave Arm Servos → PCA9685 Channels

| Joint | PCA9685 Channel | Servo | Range |
|---|---|---|---|
| Base (J1 — yaw) | Channel 0 | MG996R | 0°–180° |
| Shoulder (J2 — pitch) | Channel 1 | MG996R | 0°–180° |
| Elbow (J3 — pitch) | Channel 2 | MG996R | 0°–180° |
| Wrist Pitch (J4) | Channel 3 | MG90S / SG90 | 0°–180° |
| Wrist Roll (J5) | Channel 4 | MG90S / SG90 | 0°–180° |
| Wrist Yaw (J6) | Channel 5 | MG90S / SG90 | 0°–180° |
| Gripper | Channel 6 | SG90 | Open/Close |

### INA219 Current Sensors → Slave Servo Power Lines

Wire INA219 modules inline on the servo power (V+) lines. Each INA219 has a selectable I2C address via A0/A1 jumpers:

| INA219 | I2C Address | Monitors | Connection |
|---|---|---|---|
| INA219 #1 | 0x40 | J1 servo current | V+ in series with J1 servo power |
| INA219 #2 | 0x41 | J2 servo current | V+ in series with J2 servo power |
| INA219 #3 | 0x44 | J3 servo current | V+ in series with J3 servo power |
| INA219 #4 | 0x45 | J4 servo current | V+ in series with J4 servo power |

> All INA219 SDA/SCL connect to same I2C bus (GPIO 2/3). VCC to 3.3V, GND to common.

### DRV2605L Haptic Driver + Vibration Motors → Pi I2C

| DRV2605L Pin | Connection | Notes |
|---|---|---|
| SDA | GPIO 2 (pin 3) | Shared I2C bus |
| SCL | GPIO 3 (pin 5) | Shared I2C bus |
| VIN | 3.3V (pin 1) | Logic + motor power |
| GND | GND (pin 6) | Common ground |
| OUT+ / OUT− | Vibration motor leads | ERM or LRA motor |

> For multiple vibration motors: use a TCA9548A I2C multiplexer to address multiple DRV2605L boards (all ship at address 0x5A), or use GPIO-controlled transistor switching for simpler setups.

### Emergency Stop → Pi GPIO

| Pin | GPIO | Notes |
|---|---|---|
| E-Stop Button (N/O) | GPIO 4 (pin 7) | Pull-up, active LOW on press |
| Status LED (Green) | GPIO 22 (pin 15) | Running indicator |
| Status LED (Red) | GPIO 23 (pin 16) | Error/E-stop indicator |

> **Warning:** Always use a separate 5–6V power supply for the slave servos. Drawing servo current from the Pi will cause brownouts and SD card corruption. Bridge the ground between the servo PSU and Pi.

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| [Flask](https://flask.palletsprojects.com/) | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | WebSocket for real-time arm state + 3D visualization |
| [Jinja2](https://jinja.palletsprojects.com/) | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Load environment variables from `.env` |
| [adafruit-circuitpython-pca9685](https://pypi.org/project/adafruit-circuitpython-pca9685/) | PCA9685 servo driver over I2C |
| [adafruit-circuitpython-servokit](https://pypi.org/project/adafruit-circuitpython-servokit/) | High-level servo angle control |
| [adafruit-circuitpython-ads1x15](https://pypi.org/project/adafruit-circuitpython-ads1x15/) | ADS1115 ADC for potentiometer/encoder reads |
| [adafruit-circuitpython-ina219](https://pypi.org/project/adafruit-circuitpython-ina219/) | INA219 current/power sensor for force sensing |
| [numpy](https://numpy.org/) | Matrix operations, DH transforms, kinematics math |
| [bcrypt](https://pypi.org/project/bcrypt/) | Password hashing for dashboard auth |
| [smbus2](https://pypi.org/project/smbus2/) | Low-level I2C access (DRV2605L haptic driver) |
| [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) | GPIO for e-stop, LEDs, status |

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
git clone <repo-url> ~/Projects/ShadowArm && cd ~/Projects/ShadowArm

# 3. Create .env from template
cp .env.default .env
nano .env              # Set SESSION_SECRET, ADMIN_PASSWORD, arm config

# 4. Virtual environment and dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Enable I2C (for PCA9685, ADS1115, INA219, DRV2605L)
sudo raspi-config     # Interface Options → I2C → Enable
sudo i2cdetect -y 1   # Verify: 0x40 (PCA9685/INA219), 0x48/0x49 (ADS1115), 0x5A (DRV2605L)

# 6. Run joint calibration (sweeps each master joint to detect min/max ADC values)
python scripts/calibrate_joints.py

# 7. Start the server
python app.py

# 8. Open dashboard → http://192.168.216.90:5000
```

---

## Environment Configuration

Copy `.env.default` to `.env`. **Never commit `.env` to git.**

See [TSD.md — §4 Environment Configuration](TSD.md#4--environment-configuration-envdefault) for the full `.env.default` block.

Key toggles:

| Variable | Default | Description |
|---|---|---|
| `ENABLE_FORCE_FEEDBACK` | `true` | INA219 current → vibration motors |
| `ENABLE_FORCE_SCALING` | `true` | Adjustable force multiplier from dashboard |
| `ENABLE_NETWORK_TELEOPERATION` | `false` | LAN/WAN teleoperation with latency compensation |
| `ENABLE_RECORDING_PLAYBACK` | `true` | Record arm movements + replay |
| `ENABLE_SPEED_LIMITING` | `true` | Max angular velocity per joint |
| `ENABLE_WORKSPACE_VISUALIZATION` | `true` | Three.js 3D arm model on dashboard |
| `ENABLE_PRECISION_MODE` | `true` | Reduced motion ratio (10:1) |
| `ENABLE_GRIPPER_MIRRORING` | `true` | FSR → slave gripper servo |
| `ENABLE_COLLISION_DETECTION` | `true` | Virtual workspace boundaries + e-stop |
| `ENABLE_JOINT_CALIBRATION` | `true` | Auto-calibration on startup |
| `ENABLE_MOCK_HARDWARE` | `false` | Simulated ADC + servos + sensors for dev |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Web Browser (Dark Theme Dashboard)                  │
│  ┌────────────┐ ┌──────────────┐ ┌───────────┐ ┌────────────────┐   │
│  │ 3D Arm     │ │ Force        │ │ Recording │ │ Safety &       │   │
│  │ Three.js   │ │ Feedback     │ │ Playback  │ │ E-Stop         │   │
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
│  │        (dashboard, auth, control API, 3D viz stream)             │ │
│  └──────────────────────────┬───────────────────────────────────────┘ │
│                              │                                        │
│  ┌──────────────────────────▼───────────────────────────────────────┐ │
│  │                     MIRROR ENGINE (main loop ~50 Hz)              │ │
│  │                                                                   │ │
│  │  MASTER ARM (Input)              SLAVE ARM (Output)               │ │
│  │  ┌──────────────────┐           ┌──────────────────────┐         │ │
│  │  │ Potentiometers   │           │ MG996R Servos        │         │ │
│  │  │ ×6 joints        │           │ ×6 joints            │         │ │
│  │  │ → ADS1115 ADC ×2 │──angle──►│ → PCA9685 PWM        │         │ │
│  │  │ (I2C 0x48, 0x49) │           │ (I2C 0x40)           │         │ │
│  │  └──────────────────┘           └──────────┬───────────┘         │ │
│  │                                             │                     │ │
│  │  ┌──────────────────┐           ┌──────────▼───────────┐         │ │
│  │  │ Vibration Motors │           │ INA219 Current       │         │ │
│  │  │ ×4 on master     │◄──force──│ Sensors ×4–6         │         │ │
│  │  │ → DRV2605L       │           │ (I2C 0x40–0x45)      │         │ │
│  │  │ (I2C 0x5A)       │           │ mA → force estimate  │         │ │
│  │  └──────────────────┘           └──────────────────────┘         │ │
│  │                                                                   │ │
│  │  ┌──────────────────┐           ┌──────────────────────┐         │ │
│  │  │ FSR (gripper)    │──squeeze─►│ Slave Gripper Servo  │         │ │
│  │  │ → ADS1115 A2     │           │ → PCA9685 Ch 6       │         │ │
│  │  └──────────────────┘           └──────────────────────┘         │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌──────────┐  ┌────────────────────┐  ┌───────────────────────────┐ │
│  │ Speed    │  │  Collision         │  │   Precision Mode          │ │
│  │ Limiter  │  │  Detection         │  │   10:1 ratio for fine     │ │
│  │ per joint│  │  Virtual bounds    │  │   manipulation            │ │
│  └──────────┘  └────────────────────┘  └───────────────────────────┘ │
│                                                                       │
│  ┌──────────┐  ┌────────────────────┐  ┌───────────────────────────┐ │
│  │ Recording│  │  Network Teleop    │  │   Joint Calibration       │ │
│  │ Playback │  │  LAN/WAN + latency │  │   Auto-sweep on startup   │ │
│  │          │  │  compensation      │  │                           │ │
│  └──────────┘  └────────────────────┘  └───────────────────────────┘ │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                       SAFETY MANAGER                              │ │
│  │  Joint limits │ Workspace bounds │ E-stop GPIO │ Speed limits    │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

Teleoperation Loop (~50 Hz):
  Master pots → ADS1115 ADC → raw values → calibration map → angles
  → speed limit → precision scale → collision check
  → PCA9685 → slave servos move
  → INA219 reads servo current (mA) → force scale
  → DRV2605L → vibration motors on master (proportional haptic)
```

---

## Features

### Master → Slave Mirroring

The core teleoperation loop runs at ~50 Hz:

1. **Read master:** ADS1115 ADCs sample 6 potentiometers (16-bit, ±4.096V range).
2. **Calibration map:** Raw ADC values → joint angles via per-joint min/max calibration.
3. **Safety check:** Speed limit, workspace bounds, collision detection.
4. **Drive slave:** PCA9685 sets servo angles on the slave arm channels.

The mapping is direct: master joint N angle → slave joint N angle. The slave mirrors the master's pose in real-time with minimal latency (~20 ms I2C round-trip).

### Force Feedback (INA219 → Haptic)

When `ENABLE_FORCE_FEEDBACK=true`:

- INA219 current sensors measure the electrical current drawn by each slave servo.
- Higher current = more mechanical load = the slave is pushing against something.
- Current (mA) is mapped to vibration intensity on the master's haptic motors via DRV2605L.
- The operator *feels* resistance when the slave arm contacts objects.
- Configurable current thresholds: `FORCE_IDLE_MA` (no vibration) and `FORCE_MAX_MA` (max vibration).

### Force Scaling

When `ENABLE_FORCE_SCALING=true`:

- Dashboard slider adjusts force feedback multiplier (0.1× – 5.0×).
- **Amplify:** Increase sensitivity to detect light contacts (delicate manipulation).
- **Dampen:** Reduce feedback for high-load tasks (prevent operator fatigue).
- Real-time adjustment without restarting the system.

### Network Teleoperation

When `ENABLE_NETWORK_TELEOPERATION=true`:

- Master and slave can operate on separate machines (LAN or WAN).
- Master Pi reads encoders and sends joint angles over SocketIO to the slave Pi.
- **Predictive buffering:** Client-side prediction smooths input during network latency spikes.
- **Latency display:** Dashboard shows round-trip time.
- Configurable: `TELEOP_SERVER_HOST`, `TELEOP_SERVER_PORT`.

### Recording & Playback

When `ENABLE_RECORDING_PLAYBACK=true`:

- **Record:** Capture timestamped joint angles + gripper state during manual teleoperation.
- **Save:** Store recordings as JSON files in `config/recordings/`.
- **Replay:** Play back recorded movements on the slave arm at configurable speed.
- **Loop:** Repeat a recording indefinitely for demos or training.
- Useful for demonstrations, teaching sequences, or replaying delicate procedures.

### Speed Limiting

When `ENABLE_SPEED_LIMITING=true`:

- Maximum angular velocity enforced per joint (degrees/sec).
- Prevents sudden jerky movements that could damage servos or the workspace.
- If the master moves faster than the limit, the slave tracks at the capped speed and catches up smoothly.
- Configurable per joint via `MAX_JOINT_VELOCITY_J1` through `MAX_JOINT_VELOCITY_J6`.

### Workspace Visualization (Three.js)

When `ENABLE_WORKSPACE_VISUALIZATION=true`:

- Real-time 3D rendering of both master and slave arms in the browser.
- Built with Three.js, loaded from CDN.
- Shows joint angles, end-effector position, workspace boundaries.
- Force feedback intensity visualized as color gradients on joint segments.
- Collision boundaries displayed as translucent volumes.
- Updates via SocketIO at dashboard refresh rate.

### Precision Mode

When `ENABLE_PRECISION_MODE=true`:

- Reduces the motion ratio from 1:1 to 10:1 (configurable via `PRECISION_RATIO`).
- Moving the master 10° moves the slave 1° — ideal for fine manipulation tasks.
- Toggle on/off from the dashboard or a physical button.
- Speed limits automatically tighten in precision mode.

### Gripper Mirroring

When `ENABLE_GRIPPER_MIRRORING=true`:

- An FSR (force-sensitive resistor) mounted on the master's gripper handle measures squeeze force.
- FSR analog value → ADS1115 → mapped to slave gripper servo angle.
- Light squeeze = partially open, hard squeeze = fully closed.
- Proportional control: the slave gripper opening matches the master grip pressure.

### Collision Detection

When `ENABLE_COLLISION_DETECTION=true`:

- Virtual workspace boundaries defined in `config/workspace_bounds.json`.
- Forward kinematics computes the slave end-effector position for every command.
- If the target position exits the allowed workspace volume → command is blocked.
- If a boundary is approached within a warning threshold → dashboard alert.
- If a boundary is exceeded → emergency stop (all PCA9685 channels disabled).
- Boundaries visualized in the Three.js 3D view.

### Joint Calibration

When `ENABLE_JOINT_CALIBRATION=true`:

- On startup, the system runs an auto-calibration routine.
- Each master joint potentiometer is prompted through its full range (or swept automatically if servos are on the master too).
- Records min/max ADC values → maps to joint angle range.
- Saves calibration to `config/calibration.json`.
- Recalibrate from the dashboard Settings page at any time.
- Detects mechanical limits (sudden ADC value plateau = end of travel).

---

## Web Dashboard

The dark-themed web dashboard runs at `http://192.168.216.90:5000` and connects via SocketIO:

- **Dark theme:** Background `#1a1a2e`, accent `#0f3460`, card `#16213e`.
- **Responsive layout:** Sidebar navigation on desktop, bottom nav on mobile.
- **Pages:** Dashboard (3D viz), Force Feedback, Recording, Settings.
- **E-stop:** Red emergency stop button visible on every page — sends immediate halt command.

| Tab | Controls |
|---|---|
| **Dashboard** | 3D arm visualization (Three.js), master/slave angle readouts, force feedback graph, system status |
| **Force Feedback** | Force scaling slider, per-joint current graph, idle/max threshold adjustment |
| **Recording** | Record/Stop/Save/Load/Replay buttons, recording list, speed slider, loop toggle |
| **Settings** | Arm config, precision mode toggle, calibration trigger, collision bounds editor |

Real-time features via SocketIO:
- Joint angles (master + slave) streamed at 10 Hz.
- Force feedback current values at 10 Hz.
- Three.js model updates in sync with arm movement.
- E-stop button on every page.

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
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/ShadowArm
```

**Manual:**

```bash
rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' --exclude='data/' \
  ./ rasp-pi:/home/pi/Projects/ShadowArm/
```

---

## How to Run on the Raspberry Pi

```bash
ssh rasp-pi
cd /home/pi/Projects/ShadowArm
nano .env   # Set SESSION_SECRET, ADMIN_PASSWORD
source venv/bin/activate
python app.py
```

Access: `http://192.168.216.90:5000`

**systemd service:**

```ini
[Unit]
Description=Haptic Feedback Shadow Arm
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/ShadowArm
ExecStart=/home/pi/Projects/ShadowArm/venv/bin/python app.py
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
- Network teleoperation exposes the SocketIO port — use VPN or SSH tunnel for WAN access.
- INA219/PCA9685/ADS1115 communicate over I2C — physical access to the bus is a risk; document in threat model.
- All dashboard endpoints require authentication.
- Rate limiting prevents brute-force login attempts.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `i2cdetect` shows no devices | Check wiring: SDA → GPIO 2, SCL → GPIO 3. Enable I2C in `raspi-config`. |
| ADS1115 not at 0x48/0x49 | Verify ADDR pin: GND = 0x48, VDD = 0x49. Check for shorts. |
| PCA9685 not at 0x40 | Confirm solder bridges on A0–A5 address pins are open (default 0x40). |
| Servos jitter or don't move | Check external 5–6V PSU. Bridge GND between PSU and Pi. Verify PWM frequency = 50 Hz. |
| INA219 reads 0 mA always | INA219 must be wired in series with servo V+ line. Check shunt resistor soldering. |
| Vibration motors don't buzz | Check DRV2605L at 0x5A. Verify motor leads on OUT+/OUT−. Test with `scripts/test_haptic.py`. |
| ADC values don't change | Verify pot wiper connected to ADS1115 Ax. Check pot VCC/GND connections. |
| High latency (>50 ms) | Reduce I2C bus load: lower ADC sample rate, reduce update frequency. Use I2C bus speed 400 kHz. |
| Slave doesn't mirror master | Run `scripts/test_adc.py` to verify encoder reads. Run `scripts/test_servos.py` to verify servo response. |
| Dashboard won't load | Check Flask is running on `0.0.0.0:5000`. Check firewall: `sudo ufw allow 5000`. |
| SocketIO connection drops | Check network stability. Increase `SOCKETIO_PING_TIMEOUT` in `.env`. |
| Calibration fails | Ensure full joint range during calibration sweep. Check for stuck potentiometers. |

---

## Where to Next

- **Dynamixel upgrade:** Replace hobby servos with Dynamixel smart servos for built-in torque feedback (eliminates INA219 sensors).
- **Dual Pi setup:** Dedicated Pi for master, dedicated Pi for slave — network teleoperation natively.
- **ROS 2 integration:** Use ROS 2 for master-slave communication with standardized message types.
- **IMU-based master:** Replace potentiometers with IMUs on operator's arm for wearable teleoperation.
- **Machine learning:** Train a model to predict optimal force feedback scaling from task context.
- **VR integration:** Stream slave camera feed to VR headset + use VR controller as master input.
