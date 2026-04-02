# 🕷️ Spider-Bot Hexapod Terrain Adaptation

<div align="center">

![Hexapod](https://img.shields.io/badge/Hexapod-6_Legs_×_3_Joints-FF5722?style=for-the-badge)
![PCA9685](https://img.shields.io/badge/PCA9685-×2_Servo_Driver-4CAF50?style=for-the-badge)
![IMU](https://img.shields.io/badge/MPU6050-IMU_Stabilization-2196F3?style=for-the-badge)
![FSR](https://img.shields.io/badge/FSR-Terrain_Adaptation-9C27B0?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-SocketIO_Dashboard-000000?style=for-the-badge&logo=flask&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-4%2F5-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A 6-legged hexapod robot with 18 servos (6 legs × 3 joints: coxa, femur, tibia) controlled by a Raspberry Pi. Implements multiple gait patterns (tripod/wave/ripple), terrain adaptation via force-sensitive resistors on each foot, IMU-based body stabilization with PID control, camera head with FPV streaming, autonomous navigation with obstacle avoidance, and battery management. Includes a Flask + SocketIO dark-themed web dashboard with 3D IK visualization (Three.js), gait control, speed tuning, and gait recording/replay. Difficulty: 9/10.**

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
  - [Gait Engine](#gait-engine)
  - [Inverse Kinematics (Per-Leg)](#inverse-kinematics-per-leg)
  - [Terrain Adaptation (FSR)](#terrain-adaptation-fsr)
  - [IMU Stabilization (MPU6050)](#imu-stabilization-mpu6050)
  - [FPV Camera (Pan/Tilt)](#fpv-camera-pantilt)
  - [Autonomous Navigation](#autonomous-navigation)
  - [Battery Management (INA219)](#battery-management-ina219)
  - [IK Visualization (Three.js)](#ik-visualization-threejs)
  - [Gait Recording & Replay](#gait-recording--replay)
  - [Web-Based Control Dashboard](#web-based-control-dashboard)
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
Spider-Bot Hexapod Terrain Adaptation/
├── README.md                        # This file
├── TSD.md                          # Technical Specification Document
├── task.md                         # Development task checklist
├── implementation_plan.md          # Phased implementation guide
├── app.py                          # Python entry point (Flask + SocketIO + main loop)
├── requirements.txt                # Python dependencies
├── .env.default                    # Environment variable template (copy to .env)
├── .gitignore                      # Git ignore rules
├── src/
│   ├── kinematics/
│   │   ├── leg_ik.py               # Per-leg 3-DOF inverse kinematics (coxa/femur/tibia)
│   │   ├── body_ik.py              # Body-level IK (translate/rotate body relative to feet)
│   │   └── leg_config.py           # Leg mount positions, offsets, joint limits per leg
│   ├── gait/
│   │   ├── gait_engine.py          # Gait state machine (tripod/wave/ripple/free)
│   │   ├── gait_patterns.py        # Step sequence definitions for each gait type
│   │   ├── gait_recorder.py        # Record and replay custom gait patterns
│   │   └── speed_controller.py     # Walking speed and turn radius control
│   ├── sensors/
│   │   ├── imu.py                  # MPU6050 IMU reader (accel + gyro + complementary filter)
│   │   ├── fsr.py                  # Force-sensitive resistor reader (6 channels via ADS1115/MCP3008)
│   │   ├── ultrasonic.py           # HC-SR04 ultrasonic distance sensors ×3
│   │   └── battery.py              # INA219 voltage/current/power monitoring
│   ├── stabilization/
│   │   ├── pid_controller.py       # Generic PID controller class
│   │   └── body_leveler.py         # IMU → PID → body IK → keep body level
│   ├── navigation/
│   │   ├── obstacle_avoidance.py   # Ultrasonic-based obstacle detection and avoidance
│   │   ├── wall_follower.py        # Wall-following algorithm
│   │   └── return_home.py          # Low-battery auto-return via dead reckoning
│   ├── hardware/
│   │   ├── servo_controller.py     # Dual PCA9685 driver (18 servos across 2 boards)
│   │   ├── camera.py               # Pi Camera capture + MJPEG stream
│   │   ├── pan_tilt.py             # Camera pan/tilt servo control
│   │   ├── gpio_controller.py      # Status LEDs, misc GPIO
│   │   └── mock_hardware.py        # Mock servos + sensors for dev without hardware
│   ├── routes/
│   │   ├── auth.py                 # Login / logout routes
│   │   ├── dashboard.py            # Dashboard page and API
│   │   ├── gait_api.py             # Gait control API (start/stop/switch pattern)
│   │   ├── control_api.py          # Body translation/rotation, manual leg control
│   │   ├── camera_api.py           # FPV stream and pan/tilt control
│   │   ├── nav_api.py              # Autonomous navigation API
│   │   ├── record_api.py           # Gait recording/replay API
│   │   └── settings.py             # Settings and calibration API
│   └── services/
│       ├── db.py                   # SQLite database initialization
│       ├── gait_store.py           # Recorded gait persistence
│       └── system_service.py       # System info (temp, memory, CPU, battery)
├── config/
│   ├── leg_geometry.json           # Per-leg mount positions, link lengths, offsets
│   ├── gait_sequences/             # Saved gait recordings
│   │   └── .gitkeep
│   └── pid_tuning.json             # PID gains for pitch/roll stabilization
├── data/
│   └── hexapod.db                  # SQLite database
├── templates/                      # Jinja2 HTML templates
│   ├── layout.html                 # Base layout with sidebar navigation
│   ├── login.html                  # Login page
│   ├── dashboard.html              # Main control dashboard with 3D view
│   ├── gait.html                   # Gait pattern control + recording
│   ├── camera.html                 # FPV camera feed + pan/tilt
│   ├── nav.html                    # Autonomous navigation controls
│   └── settings.html               # Configuration and calibration
├── static/
│   ├── css/style.css               # Dark theme stylesheet
│   └── js/
│       ├── main.js                 # SocketIO client + shared utilities
│       ├── three_viz.js            # Three.js 3D hexapod IK visualization
│       ├── gait_control.js         # Gait pattern selector + speed slider
│       ├── body_control.js         # Body translation/rotation joystick
│       ├── camera_feed.js          # FPV camera stream + pan/tilt controls
│       ├── nav_panel.js            # Navigation mode controls
│       └── battery_panel.js        # Battery status and per-leg current
├── scripts/
│   ├── test_servos.py              # Test each servo individually
│   ├── calibrate_servos.py         # Per-servo center/min/max calibration
│   ├── test_imu.py                 # Verify MPU6050 readings
│   ├── test_fsr.py                 # Verify FSR readings per foot
│   ├── test_ultrasonic.py          # Verify HC-SR04 distances
│   └── test_battery.py             # Verify INA219 readings
├── deploy/
│   └── deploy_to_pi.sh             # rsync-based deploy script
├── docs/
│   ├── wiring_diagram.md           # Complete wiring reference
│   ├── ik_math.md                  # Hexapod IK derivation
│   ├── gait_patterns.md            # Gait pattern explanation with timing diagrams
│   └── threat_model.md             # Threat model and mitigations
└── tests/
    ├── test_leg_ik.py              # Per-leg IK unit tests
    ├── test_body_ik.py             # Body-level IK tests
    ├── test_gait_engine.py         # Gait state machine tests
    ├── test_pid.py                 # PID controller tests
    └── test_obstacle_avoidance.py  # Navigation tests
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB+) / Pi 5 | Yes | Pi 5 recommended for 18-servo control + vision + nav |
| PCA9685 16-Ch Servo Driver ×2 | Yes | Board 1 (0x40): legs 1–5 channels, Board 2 (0x41): legs 5–6 + camera |
| SG90 Micro Servos ×18 | Yes | 6 legs × 3 joints (coxa, femur, tibia) |
| Hexapod Frame Kit | Yes | 6-leg chassis with mounting brackets for servos |
| FSR (Force-Sensitive Resistors) ×6 | Yes | One per foot — terrain contact force sensing |
| MCP3008 ADC (or ADS1115) | Yes | 8-ch ADC for FSR analog → digital conversion |
| MPU6050 IMU | Yes | Accelerometer + gyroscope for body leveling |
| HC-SR04 Ultrasonic Sensors ×3 | Yes | Front + left + right obstacle detection |
| Pi Camera Module v2/v3 | Yes | FPV streaming and navigation vision |
| Pan-Tilt Bracket + 2× SG90 | Yes | Camera head movement (pan + tilt servos) |
| LiPo Battery 3S 2200 mAh | Yes | 11.1V power source |
| BEC (5V/5A) | Yes | Step-down from LiPo to 5V for servos and Pi |
| INA219 Current Sensor | Yes | Battery voltage/current monitoring |
| Power Distribution Board | Yes | Split power to PCA9685 boards + Pi + sensors |
| MicroSD Card (32 GB+) | Yes | For OS, code, and data |

### Optional Hardware

| Component | Required | Notes |
|---|---|---|
| ADS1115 (16-bit ADC) | No | Higher-resolution FSR reading (replaces MCP3008) |
| Additional INA219 per leg pair | No | Per-leg current monitoring |
| GPS Module (NEO-6M) | No | Outdoor return-home with coordinates |
| LED Strip (Neopixel) | No | Status/mood lighting on body |

---

## Budget

| Item | Estimated Cost |
|---|---|
| SG90 Micro Servos ×18 | ~$36 |
| PCA9685 Servo Driver ×2 | ~$8 |
| Hexapod Frame Kit | $40–80 |
| FSR ×6 | ~$12 |
| MCP3008 ADC | ~$4 |
| MPU6050 IMU | ~$4 |
| HC-SR04 Ultrasonic ×3 | ~$6 |
| Pi Camera Module v2 | ~$25 |
| Pan-Tilt Bracket + 2× SG90 | ~$6 |
| LiPo 3S 2200 mAh + BEC (5V/5A) | ~$25 |
| INA219 Current Sensor | ~$4 |
| Power Distribution Board | ~$5 |
| **Total (core build)** | **~$156–196** |

*(Assumes you already own a Raspberry Pi 4/5 with power supply and MicroSD.)*

---

## Wiring Diagram

### Dual PCA9685 → Pi I2C

| PCA9685 Board | I2C Address | Connection | Notes |
|---|---|---|---|
| Board 1 | 0x40 (default) | SDA → GPIO 2, SCL → GPIO 3 | Legs 1–3 (channels 0–8) |
| Board 2 | 0x41 (A0 bridged) | SDA → GPIO 2, SCL → GPIO 3 | Legs 4–6 (ch 0–8) + pan/tilt (ch 9–10) |
| Both boards | — | VCC → 3.3V, GND → GND | Logic power from Pi |
| Both boards | — | V+ → BEC 5V output, GND → BEC GND | Servo power from BEC |

### Servo Channel Mapping

| Leg | Joint | Board | Channel | Servo |
|---|---|---|---|---|
| Leg 1 (Front-Right) | Coxa | Board 1 | Ch 0 | SG90 |
| Leg 1 | Femur | Board 1 | Ch 1 | SG90 |
| Leg 1 | Tibia | Board 1 | Ch 2 | SG90 |
| Leg 2 (Mid-Right) | Coxa | Board 1 | Ch 3 | SG90 |
| Leg 2 | Femur | Board 1 | Ch 4 | SG90 |
| Leg 2 | Tibia | Board 1 | Ch 5 | SG90 |
| Leg 3 (Rear-Right) | Coxa | Board 1 | Ch 6 | SG90 |
| Leg 3 | Femur | Board 1 | Ch 7 | SG90 |
| Leg 3 | Tibia | Board 1 | Ch 8 | SG90 |
| Leg 4 (Front-Left) | Coxa | Board 2 | Ch 0 | SG90 |
| Leg 4 | Femur | Board 2 | Ch 1 | SG90 |
| Leg 4 | Tibia | Board 2 | Ch 2 | SG90 |
| Leg 5 (Mid-Left) | Coxa | Board 2 | Ch 3 | SG90 |
| Leg 5 | Femur | Board 2 | Ch 4 | SG90 |
| Leg 5 | Tibia | Board 2 | Ch 5 | SG90 |
| Leg 6 (Rear-Left) | Coxa | Board 2 | Ch 6 | SG90 |
| Leg 6 | Femur | Board 2 | Ch 7 | SG90 |
| Leg 6 | Tibia | Board 2 | Ch 8 | SG90 |
| Camera Pan | — | Board 2 | Ch 9 | SG90 |
| Camera Tilt | — | Board 2 | Ch 10 | SG90 |

### MPU6050 IMU → Pi I2C

| MPU6050 Pin | Connection | Notes |
|---|---|---|
| SDA | GPIO 2 (pin 3) — I2C SDA | Shared bus with PCA9685 (address 0x68) |
| SCL | GPIO 3 (pin 5) — I2C SCL | Shared bus |
| VCC | 3.3V (pin 1) | Logic power |
| GND | GND (pin 6) | Common ground |

### INA219 Battery Monitor → Pi I2C

| INA219 Pin | Connection | Notes |
|---|---|---|
| SDA | GPIO 2 (pin 3) — I2C SDA | Shared bus (address 0x44) |
| SCL | GPIO 3 (pin 5) — I2C SCL | Shared bus |
| VIN+ | LiPo battery (+) | High-side current sensing |
| VIN− | Power distribution board (+) | After shunt |
| VCC | 3.3V | Logic power |
| GND | GND | Common ground |

### MCP3008 ADC (FSR Reading) → Pi SPI

| MCP3008 Pin | Connection | Notes |
|---|---|---|
| VDD | 3.3V | Logic power |
| VREF | 3.3V | Reference voltage |
| AGND | GND | Analog ground |
| DGND | GND | Digital ground |
| CLK | GPIO 11 (SPI0 SCLK) | SPI clock |
| DOUT | GPIO 9 (SPI0 MISO) | SPI data out |
| DIN | GPIO 10 (SPI0 MOSI) | SPI data in |
| CS | GPIO 8 (SPI0 CE0) | Chip select |
| CH0–CH5 | FSR 1–6 (with voltage divider) | FSR per foot |

### HC-SR04 Ultrasonic Sensors → Pi GPIO

| Sensor | Trigger GPIO | Echo GPIO | Position |
|---|---|---|---|
| Front | GPIO 17 (pin 11) | GPIO 27 (pin 13) | Front center |
| Left | GPIO 22 (pin 15) | GPIO 23 (pin 16) | Left side |
| Right | GPIO 24 (pin 18) | GPIO 25 (pin 22) | Right side |

### Pi Camera → Pi CSI

| Connection | Detail |
|---|---|
| Ribbon cable | Pi CSI port → Camera module |
| Verify | `libcamera-hello` |

### Power Distribution

```
LiPo 3S (11.1V) ──┬── INA219 (high-side sense) ──┬── BEC (5V/5A) ──┬── PCA9685 Board 1 V+
                   │                                │                  ├── PCA9685 Board 2 V+
                   │                                │                  └── Pi 5V (via GPIO header or USB-C)
                   │                                └── GND (common)
                   └── Balance connector → LiPo charger
```

> **Warning:** Always use a BEC (Battery Eliminator Circuit) to step down LiPo voltage to 5V. Never feed 11.1V directly to servos or Pi. Bridge all grounds (LiPo, BEC, PCA9685, Pi).

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| [Flask](https://flask.palletsprojects.com/) | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | WebSocket for real-time gait state + camera feed |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Load environment variables from `.env` |
| [adafruit-circuitpython-pca9685](https://pypi.org/project/adafruit-circuitpython-pca9685/) | PCA9685 servo driver over I2C |
| [adafruit-circuitpython-servokit](https://pypi.org/project/adafruit-circuitpython-servokit/) | High-level servo angle control |
| [adafruit-circuitpython-mpu6050](https://pypi.org/project/adafruit-circuitpython-mpu6050/) | MPU6050 IMU accelerometer + gyroscope |
| [adafruit-circuitpython-ina219](https://pypi.org/project/adafruit-circuitpython-ina219/) | INA219 battery voltage/current monitor |
| [numpy](https://numpy.org/) | Matrix operations, IK math, PID |
| [opencv-python-headless](https://pypi.org/project/opencv-python-headless/) | Camera capture, FPV streaming |
| [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) | GPIO for ultrasonic sensors, status LEDs |
| [smbus2](https://pypi.org/project/smbus2/) | I2C communication (fallback/raw access) |
| [bcrypt](https://pypi.org/project/bcrypt/) | Password hashing for dashboard auth |
| [spidev](https://pypi.org/project/spidev/) | SPI for MCP3008 ADC (FSR reading) |

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
git clone <repo-url> ~/Projects/SpiderBot && cd ~/Projects/SpiderBot

# 3. Create .env from template
cp .env.default .env
nano .env              # Set SESSION_SECRET, ADMIN_PASSWORD, leg geometry

# 4. Virtual environment and dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Enable I2C (for PCA9685, MPU6050, INA219)
sudo raspi-config     # Interface Options → I2C → Enable

# 6. Enable SPI (for MCP3008 ADC)
sudo raspi-config     # Interface Options → SPI → Enable

# 7. Enable camera
sudo raspi-config     # Interface Options → Camera → Enable
libcamera-hello       # Verify camera feed

# 8. Verify I2C devices
sudo i2cdetect -y 1   # Expect: 0x40 (PCA9685 #1), 0x41 (PCA9685 #2), 0x68 (MPU6050), 0x44 (INA219)

# 9. Calibrate servos
python scripts/calibrate_servos.py

# 10. Start the server
python app.py

# 11. Open dashboard → http://192.168.216.90:5000
```

---

## Environment Configuration

Copy `.env.default` to `.env`. **Never commit `.env` to git.**

See [TSD.md — §4 Environment Configuration](TSD.md#4--environment-configuration-envdefault) for the full `.env.default` block.

Key toggles:

| Variable | Default | Description |
|---|---|---|
| `ENABLE_GAIT_ENGINE` | `true` | Gait pattern engine (tripod/wave/ripple/free) |
| `ENABLE_TERRAIN_ADAPTATION` | `true` | FSR-based terrain-adaptive leg height/force |
| `ENABLE_IMU_STABILIZATION` | `true` | MPU6050 PID body leveling |
| `ENABLE_FPV_CAMERA` | `true` | Camera head with pan/tilt + live stream |
| `ENABLE_AUTONOMOUS_NAV` | `false` | Ultrasonic obstacle avoidance + wall following |
| `ENABLE_BATTERY_MANAGEMENT` | `true` | INA219 monitoring + low-battery return home |
| `ENABLE_IK_VISUALIZATION` | `true` | Three.js real-time 3D leg position on dashboard |
| `ENABLE_MODULAR_LEG_CONFIG` | `false` | Configure 4/6/8 legs from `.env` |
| `ENABLE_GAIT_RECORDING` | `true` | Record and replay custom gaits |
| `ENABLE_SPEED_CONTROL` | `true` | Adjustable walking speed and turn radius |
| `ENABLE_MOCK_HARDWARE` | `false` | Simulated servos + sensors for dev |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Web Browser (Dark Theme Dashboard)                  │
│  ┌────────────┐ ┌──────────────┐ ┌───────────┐ ┌────────────────┐   │
│  │ 3D IK      │ │ Gait Pattern │ │ FPV       │ │ Battery        │   │
│  │ Three.js   │ │ Selector     │ │ Camera    │ │ Monitor        │   │
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
│  │    (dashboard, auth, gait API, camera feed, nav, recording)      │ │
│  └──────────────────────────┬───────────────────────────────────────┘ │
│                              │                                        │
│  ┌──────────────┐  ┌────────▼──────────┐  ┌────────────────────────┐ │
│  │ Gait Engine  │  │  Body IK + Leg IK │  │ Stabilization (PID)    │ │
│  │ Tripod/Wave/ ├──►  Per-leg 3-DOF    ◄──┤ MPU6050 → pitch/roll  │ │
│  │ Ripple/Free  │  │  coxa/femur/tibia │  │ → body tilt correction │ │
│  └──────────────┘  └────────┬──────────┘  └────────────────────────┘ │
│                              │                                        │
│  ┌──────────────┐  ┌────────▼──────────┐  ┌────────────────────────┐ │
│  │ Terrain      │  │  Servo Controller │  │ Navigation             │ │
│  │ Adaptation   ├──►  PCA9685 ×2       │  │ HC-SR04 ×3 → obstacle │ │
│  │ FSR ×6 →    │  │  18 servos + 2 PT │  │ avoidance / wall follow│ │
│  │ height adjust│  └──────────────────┘  └────────────────────────┘ │
│  └──────────────┘                                                     │
│                                                                       │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────────┐ │
│  │ FPV Camera   │  │ Battery Manager  │  │ Gait Recorder          │ │
│  │ Pan/Tilt +   │  │ INA219 → V/I/P   │  │ Record/replay custom   │ │
│  │ MJPEG stream │  │ low-bat → return │  │ gait patterns          │ │
│  └──────────────┘  └──────────────────┘  └────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

Gait Cycle:
  Gait engine selects active legs → per-leg IK computes joint angles
  → IMU PID corrects body tilt → FSR adjusts foot height per terrain
  → PCA9685 ×2 drives 18 servos → hexapod walks
  → Ultrasonic sensors detect obstacles → gait adjusts heading
  → INA219 monitors battery → low-bat triggers return-home
```

---

## Features

### Gait Engine

Four gait patterns, switchable from dashboard or `.env`:

| Gait | Pattern | Speed | Stability | Description |
|---|---|---|---|---|
| **Tripod** | 3+3 alternating | Fast | Moderate | Two groups of 3 legs alternate (insect-like) |
| **Wave** | 1 at a time | Slow | Very high | One leg lifts at a time (5 always grounded) |
| **Ripple** | 2 at a time | Medium | High | Overlapping waves — compromise of speed/stability |
| **Free** | User-defined | Variable | Variable | Custom leg sequences from gait recorder |

The gait state machine cycles through: **Lift → Swing → Down → Push** for each active leg group. Step height, stride length, and cycle time are configurable via `.env`.

Toggle: `ENABLE_GAIT_ENGINE=true`, `GAIT_PATTERN=tripod` in `.env`.

### Inverse Kinematics (Per-Leg)

Each leg is a 3-DOF serial chain: **coxa (yaw) → femur (pitch) → tibia (pitch)**.

Given a target foot position `(x, y, z)` relative to the coxa mount:
1. **Coxa angle** = `atan2(y, x)` — rotates the leg plane to face the target.
2. **Projected distance** in the leg plane: `r = sqrt(x² + y²) - coxa_length`.
3. **Femur + Tibia** via law of cosines (2-link planar IK):
   - `cos(tibia) = (r² + z² - femur² - tibia²) / (2 × femur × tibia)`
   - `femur_angle = atan2(z, r) - atan2(tibia×sin(tibia_angle), femur + tibia×cos(tibia_angle))`

Body-level IK translates/rotates the body relative to all foot positions, then per-leg IK resolves each leg independently.

### Terrain Adaptation (FSR)

When `ENABLE_TERRAIN_ADAPTATION=true`:

- Each foot has a force-sensitive resistor (FSR) read via MCP3008 ADC.
- During the **Down** phase, the leg extends until the FSR exceeds a threshold (foot has made contact).
- On uneven terrain, legs automatically adjust height — short legs extend further, tall ground contact triggers early stop.
- Force feedback prevents over-pressing on hard surfaces and compensates for soft terrain.
- FSR readings are streamed to the dashboard for real-time visualization.

### IMU Stabilization (MPU6050)

When `ENABLE_IMU_STABILIZATION=true`:

- MPU6050 reads accelerometer + gyroscope at 100 Hz.
- Complementary filter fuses accel/gyro into stable pitch and roll estimates.
- Two PID controllers (one for pitch, one for roll) compute body tilt correction.
- Body IK applies the correction — tilting the body via symmetric leg length adjustments.
- Result: body stays level even on slopes and uneven terrain.
- PID gains configurable in `config/pid_tuning.json` and via Settings dashboard page.

### FPV Camera (Pan/Tilt)

When `ENABLE_FPV_CAMERA=true`:

- Pi Camera streams MJPEG frames via SocketIO to the dashboard.
- Pan/tilt servos on PCA9685 Board 2 (channels 9–10) aim the camera head.
- Dashboard provides pan/tilt sliders and a joystick-style control.
- Camera auto-centers on startup and can track heading during autonomous navigation.
- Configurable resolution, FPS, and JPEG quality in `.env`.

### Autonomous Navigation

When `ENABLE_AUTONOMOUS_NAV=true`:

- Three HC-SR04 ultrasonic sensors (front, left, right) measure distances.
- **Obstacle avoidance:** If front sensor < threshold → stop → turn toward the more-open side → resume.
- **Wall following:** Maintain constant distance from left or right wall using PID on side sensor.
- **Return home:** Dead-reckoning path integration — on low battery, retrace steps to approximate starting position.
- Navigation mode selectable from dashboard (manual / avoid / wall-follow / return).

### Battery Management (INA219)

When `ENABLE_BATTERY_MANAGEMENT=true`:

- INA219 reads bus voltage, shunt current, and power at 10 Hz.
- Dashboard displays: voltage (V), current draw (A), power (W), estimated remaining capacity (%).
- LiPo cell voltage thresholds: warning at 3.5V/cell (10.5V), critical at 3.3V/cell (9.9V).
- On critical: auto-activate return-home, reduce gait speed, disable non-essential features.
- Per-leg current monitoring (optional with additional INA219 boards) identifies stuck or overloaded servos.

### IK Visualization (Three.js)

When `ENABLE_IK_VISUALIZATION=true`:

- Dashboard includes a real-time 3D visualization of the hexapod rendered with Three.js.
- Shows: body frame, all 6 legs with coxa/femur/tibia segments, foot contact points.
- Updates at SocketIO rate — reflects actual servo positions from leg IK.
- Mouse orbit/zoom controls for inspection.
- Color-coded: green = grounded, blue = swing phase, red = FSR overload.

### Gait Recording & Replay

When `ENABLE_GAIT_RECORDING=true`:

- **Record:** While walking, capture the full joint state at each gait cycle step.
- **Save:** Store recorded gait as a named JSON sequence in `config/gait_sequences/`.
- **Replay:** Load a recorded gait and replay as a custom "free" gait pattern.
- **Edit:** Adjust stride length, step height, and timing of recorded gaits from dashboard.
- Useful for tuning gaits on specific terrain, teaching new movement patterns.

### Web-Based Control Dashboard

The dark-themed Flask + SocketIO dashboard at `http://192.168.216.90:5000` provides:

| Tab | Controls |
|---|---|
| **Dashboard** | 3D IK visualization, body translation/rotation joystick, gait selector, battery status, IMU tilt |
| **Gait** | Pattern selector (tripod/wave/ripple/free), speed slider, stride/height tuning, record/replay |
| **Camera** | FPV live stream, pan/tilt slider/joystick, snapshot button |
| **Navigation** | Mode selector (manual/avoid/wall-follow/return), sensor distance readout, heading indicator |
| **Settings** | Leg geometry, PID tuning, servo calibration, feature toggles, system info |

Real-time features via SocketIO:
- Joint angles streamed to Three.js at 20 Hz.
- IMU pitch/roll and FSR values at 10 Hz.
- Camera frames at configured FPS.
- Battery voltage/current at 1 Hz.
- Ultrasonic distances at 5 Hz.

---

## Web Dashboard

The dark-themed web dashboard runs at `http://192.168.216.90:5000` and connects via SocketIO:

- **Dark theme:** Background `#1a1a2e`, accent `#0f3460`, card `#16213e`.
- **Responsive layout:** Sidebar navigation on desktop, bottom nav on mobile.
- **Pages:** Dashboard, Gait, Camera, Navigation, Settings.
- **E-stop:** Red emergency stop button visible on every page — sends immediate halt command (all servos to neutral).

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
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/SpiderBot
```

**Manual:**

```bash
rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' --exclude='data/' \
  ./ rasp-pi:/home/pi/Projects/SpiderBot/
```

---

## How to Run on the Raspberry Pi

```bash
ssh rasp-pi
cd /home/pi/Projects/SpiderBot
nano .env   # Set SESSION_SECRET, ADMIN_PASSWORD, leg geometry
source venv/bin/activate
python app.py
```

Access: `http://192.168.216.90:5000`

**systemd service:**

```ini
[Unit]
Description=Spider-Bot Hexapod Terrain Adaptation
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/SpiderBot
ExecStart=/home/pi/Projects/SpiderBot/venv/bin/python app.py
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
- PCA9685 I2C has no authentication — physical access to I2C bus controls the servos.
- LiPo batteries are fire hazards — never discharge below 3.0V/cell. Use the INA219 auto-shutdown.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| PCA9685 not detected | `sudo i2cdetect -y 1` — expect `0x40` and `0x41`. Verify A0 solder bridge on board 2. Enable I2C via `raspi-config`. |
| Servos jittering | Use BEC (not Pi 5V) for servo power. Add 1000µF cap across V+ on each PCA9685 board. |
| Only 16 servos work | Verify second PCA9685 at address `0x41`. Bridge the A0 pad on board 2. |
| MPU6050 not responding | `sudo i2cdetect -y 1` — expect `0x68`. Check SDA/SCL wiring. Try `AD0` pin to GND. |
| IMU drift / oscillation | Tune PID gains in `config/pid_tuning.json`. Reduce P gain if oscillating. Increase I gain if drifting. |
| FSR readings noisy | Add 10kΩ pull-down resistor in voltage divider. Use software low-pass filter. Verify MCP3008 SPI wiring. |
| Hexapod tips over | Reduce walking speed. Switch to wave gait (most stable). Check IMU stabilization is enabled. |
| Camera not detected | `libcamera-hello`. Enable camera in `raspi-config`. Check ribbon cable orientation. |
| Battery drains fast | Reduce gait speed. Servos draw most power — use wave gait for lower current. Check for stalled/binding servos. |
| INA219 reads 0 | Verify high-side wiring (VIN+ before load, VIN− after). Check I2C address (`0x44`). |
| Ultrasonic always reads max | Verify trigger/echo GPIO pins match `.env`. Check 5V power to HC-SR04. |
| Three.js visualization blank | Check browser console for WebGL errors. Ensure SocketIO is connected. |
| Mock mode not working | Set `ENABLE_MOCK_HARDWARE=true` in `.env`. No PCA9685, IMU, or FSR required. |

---

## Where to Next

- Add a LIDAR sensor (RPLidar A1) for 360° SLAM mapping and true autonomous navigation.
- Upgrade to MG90S metal-gear servos for better durability and torque.
- Add Dynamixel smart servos for position feedback and torque sensing.
- Implement computer vision obstacle detection using Pi Camera + TFLite.
- Add a robotic arm/gripper on top of the hexapod for mobile manipulation.
- Implement a ROS 2 node for integration with the ROS ecosystem.
- Add terrain classification via camera (grass, gravel, stairs) for automatic gait selection.
- Build a swarm of hexapods with mesh communication (LoRa or ESP-NOW).
- Add a voice command interface for hands-free control.
- 3D print custom leg segments with integrated FSR mounts and cable routing.
