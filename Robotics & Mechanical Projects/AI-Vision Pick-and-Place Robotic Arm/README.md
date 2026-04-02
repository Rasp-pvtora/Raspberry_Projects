# AI-Vision Pick-and-Place Robotic Arm

<div align="center">

![TFLite](https://img.shields.io/badge/TFLite-Object_Classification-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![Inverse Kinematics](https://img.shields.io/badge/IK-Inverse_Kinematics-00BCD4?style=for-the-badge)
![PCA9685](https://img.shields.io/badge/PCA9685-Servo_Driver-4CAF50?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-SocketIO_Dashboard-000000?style=for-the-badge&logo=flask&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-4%2F5-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A 4/6-axis robotic arm controlled by a Raspberry Pi with computer vision for autonomous pick-and-place. Pi Camera identifies objects by color, shape, or trained class (TFLite). The system calculates object (x, y, z) from camera-to-world calibration (ArUco markers), applies inverse kinematics (analytical 4-axis / numerical Jacobian 6-axis) for joint angles, and moves the arm to pick and place objects between containers. Includes a Flask + SocketIO dark-themed web dashboard with joint sliders, Cartesian control, teach mode, live camera feed, and safety limits. Difficulty: 8/10.**

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
  - [Inverse Kinematics Solver](#inverse-kinematics-solver)
  - [Camera-to-World Calibration (ArUco)](#camera-to-world-calibration-aruco)
  - [Object Classification (TFLite)](#object-classification-tflite)
  - [Conveyor Belt Integration](#conveyor-belt-integration)
  - [Gripper Options](#gripper-options)
  - [3D Pose Estimation](#3d-pose-estimation)
  - [Teach Mode](#teach-mode)
  - [Web-Based Control Dashboard](#web-based-control-dashboard)
  - [Safety Limits](#safety-limits)
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
AI-Vision Pick-and-Place Robotic Arm/
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
│   │   ├── forward_kinematics.py   # FK solver using DH parameters
│   │   ├── inverse_kinematics.py   # IK solver (analytical 4-axis, Jacobian 6-axis)
│   │   ├── dh_params.py            # DH parameter table loader from .env/config
│   │   └── trajectory.py           # Joint-space trajectory interpolation
│   ├── vision/
│   │   ├── camera.py               # Pi Camera capture and frame pipeline
│   │   ├── calibration.py          # Camera intrinsics + ArUco camera-to-world
│   │   ├── object_detector.py      # TFLite inference (color, shape, trained class)
│   │   ├── aruco_tracker.py        # ArUco marker detection and pose estimation
│   │   └── pose_estimator.py       # 3D object pose from 2D detections + depth
│   ├── hardware/
│   │   ├── servo_controller.py     # PCA9685 servo driver (angle → PWM)
│   │   ├── gripper.py              # Gripper abstraction (suction, parallel jaw, soft)
│   │   ├── conveyor.py             # Conveyor belt motor control + speed sensing
│   │   ├── gpio_controller.py      # Emergency stop, LEDs, limit switches
│   │   └── mock_hardware.py        # Mock servos + GPIO for dev without hardware
│   ├── control/
│   │   ├── arm_controller.py       # High-level arm: move_to(x,y,z), pick(), place()
│   │   ├── safety_manager.py       # No-go zones, joint limits, collision avoidance
│   │   ├── teach_mode.py           # Manual position recording + sequence replay
│   │   └── pick_place_pipeline.py  # Full pipeline: detect → plan → pick → place
│   ├── routes/
│   │   ├── auth.py                 # Login / logout routes
│   │   ├── dashboard.py            # Dashboard page and API
│   │   ├── control_api.py          # Joint/Cartesian control API
│   │   ├── teach_api.py            # Teach mode recording/replay API
│   │   ├── vision_api.py           # Camera feed and detection API
│   │   └── settings.py             # Settings API
│   └── services/
│       ├── db.py                   # SQLite database initialization
│       ├── sequence_store.py       # Teach mode sequence persistence
│       └── system_service.py       # System info (temp, memory, CPU)
├── models/
│   ├── object_classifier.tflite    # TFLite object classification model
│   ├── labels.txt                  # Class labels for TFLite model
│   └── training_data/              # Captured training images
├── config/
│   ├── dh_params.json              # DH parameter table for robot arm
│   ├── calibration.json            # Camera intrinsic + extrinsic calibration data
│   ├── no_go_zones.json            # Workspace no-go zone definitions
│   └── sequences/                  # Saved teach mode sequences
│       └── .gitkeep
├── data/
│   └── arm.db                      # SQLite database
├── templates/                      # Jinja2 HTML templates
│   ├── layout.html                 # Base layout with sidebar navigation
│   ├── login.html                  # Login page
│   ├── dashboard.html              # Main control dashboard
│   ├── teach.html                  # Teach mode interface
│   ├── camera.html                 # Camera feed and detection view
│   └── settings.html               # Configuration and calibration
├── static/
│   ├── css/style.css               # Dark theme stylesheet
│   └── js/
│       ├── main.js                 # SocketIO client + shared utilities
│       ├── joint_control.js        # Joint slider controls
│       ├── cartesian_control.js    # Cartesian (x/y/z) controls
│       ├── teach_mode.js           # Teach mode record/replay UI
│       ├── camera_feed.js          # Live camera feed + detection overlay
│       └── safety_panel.js         # Safety status and e-stop button
├── scripts/
│   ├── calibrate_camera.py         # Camera intrinsic calibration helper
│   ├── calibrate_aruco.py          # ArUco camera-to-world calibration
│   ├── test_servos.py              # Test each servo individually
│   ├── download_model.sh           # Download pre-trained TFLite model
│   └── measure_dh.py               # Interactive DH parameter measurement
├── deploy/
│   └── deploy_to_pi.sh             # rsync-based deploy script
├── docs/
│   ├── wiring_diagram.md           # Complete wiring reference
│   ├── dh_parameters.md            # DH parameter explanation and measurement guide
│   ├── calibration_guide.md        # Camera and ArUco calibration walkthrough
│   └── threat_model.md             # Threat model and mitigations
└── tests/
    ├── test_forward_kinematics.py  # FK unit tests
    ├── test_inverse_kinematics.py  # IK unit tests
    ├── test_safety_manager.py      # Safety zone tests
    └── test_trajectory.py          # Trajectory interpolation tests
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB+) / Pi 5 | Yes | Pi 5 recommended for TFLite + vision + control loop |
| 6-DOF Robotic Arm Kit | Yes | Hobby servo arm (e.g., LeArm, xArm, SainSmart 6-DOF) |
| PCA9685 16-Channel Servo Driver | Yes | I2C PWM driver — powers all arm servos |
| Pi Camera Module v2/v3 | Yes | Object detection and ArUco calibration |
| 5V Servo Power Supply (5–6V, 5A+) | Yes | Separate supply for servos — do NOT power from Pi |
| ArUco Markers (printed) | Yes | Camera-to-world coordinate calibration |
| MicroSD Card (32 GB+) | Yes | For OS, models, and data |

### Optional Hardware

| Component | Required | Notes |
|---|---|---|
| Conveyor Belt Kit (DC motor) | No | Automated object feed with lead-time compensation |
| Suction Gripper (vacuum pump) | No | Pick smooth/flat objects |
| Parallel Jaw Gripper (servo) | No | Default gripper on most arm kits |
| Soft Gripper (silicone fingers) | No | Delicate objects — 3D printed |
| Emergency Stop Button (N/O) | No | Physical GPIO e-stop for safety |
| LED Indicators | No | Status LEDs (running, error, e-stop) |

---

## Budget

| Item | Estimated Cost |
|---|---|
| 6-DOF Robotic Arm Kit (with servos) | $60–120 |
| PCA9685 16-Channel Servo Driver | ~$4 |
| Pi Camera Module v2 | ~$25 |
| 5V 5A Servo Power Supply | ~$8 |
| ArUco Markers (print yourself) | ~$0 |
| **Total (core build)** | **~$90–165** |

Optional add-ons:

| Item | Estimated Cost |
|---|---|
| Conveyor Belt + DC Motor Kit | $20–40 |
| Suction Gripper (vacuum pump + cup) | ~$15 |
| Emergency Stop Button | ~$3 |
| LED Indicators ×3 | ~$2 |

*(Assumes you already own a Raspberry Pi 4/5 with power supply and MicroSD.)*

---

## Wiring Diagram

### PCA9685 Servo Driver → Pi I2C

| PCA9685 Pin | Connection | Notes |
|---|---|---|
| SDA | GPIO 2 (pin 3) — I2C SDA | Data line |
| SCL | GPIO 3 (pin 5) — I2C SCL | Clock line |
| VCC | 3.3V (pin 1) | Logic power from Pi |
| GND | GND (pin 6) | Common ground with Pi |
| V+ | External 5–6V PSU (+) | Servo power — NOT from Pi |
| GND (V+) | External 5–6V PSU (−) | Servo power ground — bridge to Pi GND |

### Arm Servos → PCA9685 Channels

| Joint | PCA9685 Channel | Servo | Range |
|---|---|---|---|
| Base (J1 — yaw) | Channel 0 | MG996R / MG90S | 0°–180° |
| Shoulder (J2 — pitch) | Channel 1 | MG996R | 0°–180° |
| Elbow (J3 — pitch) | Channel 2 | MG996R | 0°–180° |
| Wrist Pitch (J4) | Channel 3 | MG90S / SG90 | 0°–180° |
| Wrist Roll (J5) | Channel 4 | MG90S / SG90 | 0°–180° |
| Wrist Yaw (J6) | Channel 5 | MG90S / SG90 | 0°–180° |
| Gripper | Channel 6 | SG90 / Pump relay | Open/Close or On/Off |

### Pi Camera → Pi CSI

| Connection | Detail |
|---|---|
| Ribbon cable | Pi CSI port → Camera module |
| Verify | `libcamera-hello` |

### Conveyor Belt (Optional) → Pi GPIO

| Pin | GPIO | Notes |
|---|---|---|
| Motor Direction | GPIO 17 (pin 11) | Motor driver IN1 |
| Motor PWM | GPIO 18 (pin 12) | Motor speed (hardware PWM) |
| Motor GND | GND (pin 14) | Common ground |
| Speed Sensor | GPIO 27 (pin 13) | Interrupt-driven pulse counter |

### Emergency Stop (Optional) → Pi GPIO

| Pin | GPIO | Notes |
|---|---|---|
| E-Stop Button (N/O) | GPIO 4 (pin 7) | Pull-up, active LOW on press |
| Status LED (Green) | GPIO 22 (pin 15) | Running indicator |
| Status LED (Red) | GPIO 23 (pin 16) | Error/E-stop indicator |

> **Warning:** Always use a separate 5–6V power supply for the servos. Drawing servo current from the Pi will cause brownouts and SD card corruption. Bridge the ground between the servo PSU and Pi.

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| [Flask](https://flask.palletsprojects.com/) | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | WebSocket for real-time camera feed + joint state |
| [Jinja2](https://jinja.palletsprojects.com/) | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Load environment variables from `.env` |
| [opencv-python-headless](https://pypi.org/project/opencv-python-headless/) | Camera capture, ArUco detection, image processing |
| [tflite-runtime](https://www.tensorflow.org/lite/guide/python) | TFLite model inference for object classification |
| [numpy](https://numpy.org/) | Matrix operations, DH transforms, kinematics math |
| [scipy](https://scipy.org/) | Numerical IK solver (Jacobian, optimization) |
| [adafruit-circuitpython-pca9685](https://pypi.org/project/adafruit-circuitpython-pca9685/) | PCA9685 servo driver over I2C |
| [adafruit-circuitpython-servokit](https://pypi.org/project/adafruit-circuitpython-servokit/) | High-level servo angle control |
| [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) | GPIO for e-stop, LEDs, conveyor, limit switches |
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
git clone <repo-url> ~/Projects/PickAndPlace && cd ~/Projects/PickAndPlace

# 3. Create .env from template
cp .env.default .env
nano .env              # Set SESSION_SECRET, ADMIN_PASSWORD, arm joint limits

# 4. Virtual environment and dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Enable I2C (for PCA9685)
sudo raspi-config     # Interface Options → I2C → Enable
sudo i2cdetect -y 1   # Verify PCA9685 at 0x40

# 6. Enable camera
sudo raspi-config     # Interface Options → Camera → Enable
libcamera-hello       # Verify camera feed

# 7. Download TFLite model
bash scripts/download_model.sh

# 8. Calibrate camera-to-world (ArUco markers)
python scripts/calibrate_aruco.py

# 9. Start the server
python app.py

# 10. Open dashboard → http://192.168.216.90:5000
```

---

## Environment Configuration

Copy `.env.default` to `.env`. **Never commit `.env` to git.**

See [TSD.md — §4 Environment Configuration](TSD.md#4-environment-configuration-envdefault) for the full `.env.default` block.

Key toggles:

| Variable | Default | Description |
|---|---|---|
| `ARM_DOF` | `6` | Arm degrees of freedom: `4` or `6` |
| `IK_SOLVER` | `analytical` | IK method: `analytical` (4-DOF) or `jacobian` (6-DOF) |
| `ENABLE_CAMERA` | `true` | Pi Camera for vision pipeline |
| `ENABLE_TFLITE` | `true` | TFLite object classification |
| `ENABLE_ARUCO_CALIBRATION` | `true` | ArUco camera-to-world calibration |
| `ENABLE_CONVEYOR` | `false` | Conveyor belt integration |
| `ENABLE_TEACH_MODE` | `true` | Manual position recording + replay |
| `ENABLE_SAFETY_LIMITS` | `true` | Joint limits + no-go zones + e-stop GPIO |
| `ENABLE_3D_POSE` | `false` | 3D pose estimation from monocular depth |
| `GRIPPER_TYPE` | `parallel_jaw` | Gripper: `suction`, `parallel_jaw`, `soft_gripper` |
| `ENABLE_WEB_DASHBOARD` | `true` | Flask + SocketIO web dashboard |
| `ENABLE_MOCK_HARDWARE` | `false` | Simulated servos + GPIO for dev |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Web Browser (Dark Theme Dashboard)                  │
│  ┌────────────┐ ┌──────────────┐ ┌───────────┐ ┌────────────────┐   │
│  │ Joint       │ │ Cartesian    │ │ Live      │ │ Teach Mode     │   │
│  │ Sliders    │ │ x/y/z Ctrl   │ │ Camera    │ │ Record/Play    │   │
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
│  │         (dashboard, auth, control API, camera feed)              │ │
│  └──────────────────────────┬───────────────────────────────────────┘ │
│                              │                                        │
│  ┌──────────┐  ┌────────────▼───────┐  ┌───────────────────────────┐ │
│  │ Pi Camera│  │   Vision Pipeline   │  │     Arm Controller        │ │
│  │ v2/v3   ├──► Camera → ArUco     │  │  ┌──────────┐ ┌────────┐ │ │
│  │          │  │ → TFLite classify  ├──►  │ IK Solver│ │Safety  │ │ │
│  └──────────┘  │ → (x,y,z) object  │  │  │ (4/6 DOF)│ │Manager │ │ │
│                 └────────────────────┘  │  └─────┬────┘ └───┬────┘ │ │
│                                         │        │          │       │ │
│  ┌──────────┐  ┌────────────────────┐  │  ┌─────▼──────────▼────┐ │ │
│  │ PCA9685  │  │  Trajectory        │  │  │   Joint Angles      │ │ │
│  │ Servo    ◄──┤  Interpolation     ◄──┘  │   → Trajectory      │ │ │
│  │ Driver   │  └────────────────────┘     │   → PCA9685 PWM     │ │ │
│  └──────────┘                              └─────────────────────┘ │ │
│                                                                       │
│  ┌──────────┐  ┌────────────────────┐  ┌───────────────────────────┐ │
│  │ Gripper  │  │  Teach Mode        │  │   Conveyor Belt           │ │
│  │ Suction/ │  │  Record positions  │  │   Speed sense + lead time │ │
│  │ Jaw/Soft │  │  Replay sequences  │  │   compensation            │ │
│  └──────────┘  └────────────────────┘  └───────────────────────────┘ │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    Safety Manager                                 │ │
│  │  Joint limits │ No-go zones │ E-stop GPIO │ Workspace bounds     │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

Pick-and-Place Pipeline:
  Camera frame → ArUco calibration → TFLite classify object
  → Compute (x,y,z) in world frame → IK solver → joint angles
  → Safety check → Trajectory interpolation → PCA9685 → Arm moves
  → Gripper pick → Move to place container → Gripper release
```

---

## Features

### Inverse Kinematics Solver

Two IK modes depending on the arm's degrees of freedom:

- **Analytical (4-DOF):** Closed-form geometric solution for base-shoulder-elbow-wrist. Fast, deterministic, no iteration. Best for simple 4-axis arms.
- **Numerical Jacobian (6-DOF):** Iterative Jacobian-transpose/pseudoinverse solver using `scipy`. Handles full 6-DOF pose (position + orientation). Converges to target within tolerance or reports unreachable.

Both solvers use the DH parameter table from `config/dh_params.json` (link lengths, offsets, joint limits). Forward kinematics verifies solutions before sending to servos.

Toggle: `IK_SOLVER=analytical` or `IK_SOLVER=jacobian` in `.env`.

### Camera-to-World Calibration (ArUco)

Transforms 2D pixel coordinates to 3D world coordinates using ArUco markers:

1. **Camera intrinsics** — calibrate once with a checkerboard (`scripts/calibrate_camera.py`).
2. **ArUco markers** — place printed markers at known world positions around the workspace.
3. **Extrinsic estimation** — `cv2.aruco.estimatePoseSingleMarkers()` computes camera-to-marker transform.
4. **World mapping** — compose transforms to get pixel → world (x, y, z) mapping.

The calibration result is saved to `config/calibration.json` and loaded at startup. Recalibrate when the camera or workspace moves.

Toggle: `ENABLE_ARUCO_CALIBRATION=true` in `.env`.

### Object Classification (TFLite)

Three classification modes, all running on TFLite:

- **Color:** HSV thresholding to sort objects by color (red, green, blue, yellow).
- **Shape:** Contour analysis to classify circle, square, triangle.
- **Trained class:** Custom TFLite model trained on specific objects (bolts, caps, fruit, etc.).

The classifier returns the object class and bounding box. Combined with ArUco calibration, the system computes the object's (x, y, z) world coordinates for the IK solver.

Toggle: `ENABLE_TFLITE=true`, `DETECTION_MODE=color|shape|tflite` in `.env`.

### Conveyor Belt Integration

When `ENABLE_CONVEYOR=true`:

- DC motor drives a conveyor belt past the camera field of view.
- A speed sensor (encoder or photointerrupter) measures belt velocity.
- The system computes lead time: the delay between detection and the arm's pick position.
- The arm pre-positions and times the grab to intercept the moving object.
- Configurable pick zone (x range) and belt direction.

### Gripper Options

Three gripper types, selectable via `GRIPPER_TYPE`:

| Type | Mechanism | Best For |
|---|---|---|
| `parallel_jaw` | Servo-driven fingers | General objects, default |
| `suction` | Vacuum pump + suction cup | Flat/smooth objects (PCB, cards) |
| `soft_gripper` | Silicone fingers (3D printed) | Delicate/irregular objects (fruit) |

The gripper abstraction exposes `grip()` and `release()` — the servo channel or pump relay is configured via `.env`.

### 3D Pose Estimation

When `ENABLE_3D_POSE=true`:

- Estimates object orientation (roll, pitch, yaw) in addition to position.
- Uses ArUco marker plane as height reference + object contour analysis.
- 6-DOF IK solver targets the full pose (position + orientation) for the end effector.
- Required for precisely grasping oriented objects (e.g., pick a bolt by the head).

### Teach Mode

When `ENABLE_TEACH_MODE=true`:

- **Record:** Manually move the arm (via joint sliders or Cartesian controls) to waypoints and save each position.
- **Save:** Store the recorded sequence as a named file in `config/sequences/`.
- **Replay:** Load and replay a saved sequence at configurable speed.
- **Loop:** Repeat a sequence indefinitely for production-like operation.
- **Edit:** Modify individual waypoints in a saved sequence via the dashboard.

Useful for repetitive tasks without programming: record the pick-and-place path once, then replay.

### Web-Based Control Dashboard

The dark-themed Flask + SocketIO dashboard at `http://192.168.216.90:5000` provides:

| Tab | Controls |
|---|---|
| **Dashboard** | Live camera feed with detection overlays, arm 3D visualization, system status |
| **Joint Control** | Individual joint sliders (J1–J6) with real-time arm movement |
| **Cartesian Control** | x/y/z position + orientation sliders → IK solver → arm movement |
| **Teach Mode** | Record/stop/save/load/replay buttons, waypoint list, speed slider |
| **Camera** | Live camera feed, detection mode toggle, classification results |
| **Settings** | Arm config, gripper type, safety zones, calibration trigger |

Real-time features via SocketIO:
- Joint angles streamed to browser at 10 Hz.
- Camera frames with detection overlays at configured FPS.
- Immediate arm response to slider changes.
- E-stop button on every page.

### Safety Limits

When `ENABLE_SAFETY_LIMITS=true`:

- **Joint limits:** Each joint has min/max angle (from DH config). IK solutions outside limits are rejected.
- **No-go zones:** Rectangular or cylindrical zones in world coordinates where the end effector must not enter (defined in `config/no_go_zones.json`).
- **Workspace bounds:** Maximum reach envelope prevents commands beyond the arm's physical range.
- **Emergency stop (GPIO):** Physical button and web button immediately halt all servos (PCA9685 channels disabled). Requires explicit resume.
- **Speed limits:** Maximum angular velocity per joint to prevent jerky/dangerous motion.

---

## Web Dashboard

The dark-themed web dashboard runs at `http://192.168.216.90:5000` and connects via SocketIO:

- **Dark theme:** Background `#1a1a2e`, accent `#0f3460`, card `#16213e`.
- **Responsive layout:** Sidebar navigation on desktop, bottom nav on mobile.
- **Pages:** Dashboard, Joint Control, Cartesian Control, Teach Mode, Camera, Settings.
- **E-stop:** Red emergency stop button visible on every page — sends immediate halt command.

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
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/PickAndPlace
```

**Manual:**

```bash
rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' --exclude='data/' --exclude='models/training_data/' \
  ./ rasp-pi:/home/pi/Projects/PickAndPlace/
```

---

## How to Run on the Raspberry Pi

```bash
ssh rasp-pi
cd /home/pi/Projects/PickAndPlace
nano .env   # Set SESSION_SECRET, ADMIN_PASSWORD, ARM_DOF, GRIPPER_TYPE
source venv/bin/activate
python app.py
```

Access: `http://192.168.216.90:5000`

**systemd service:**

```ini
[Unit]
Description=AI-Vision Pick-and-Place Robotic Arm
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/PickAndPlace
ExecStart=/home/pi/Projects/PickAndPlace/venv/bin/python app.py
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
- PCA9685 I2C has no authentication — physical access to I2C bus controls the arm.
- Emergency stop GPIO should be wired normally-open so a disconnected wire triggers safe state.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| PCA9685 not detected | `sudo i2cdetect -y 1` — expect `0x40`. Enable I2C via `raspi-config`. Check SDA/SCL wiring. |
| Servos jittering | Use separate 5–6V PSU for servos, not Pi 5V. Add capacitor (1000µF) across servo power. |
| Camera not detected | `libcamera-hello`. Enable camera in `raspi-config`. Check ribbon cable orientation. |
| IK solver fails (unreachable) | Point is outside workspace. Check DH parameters match physical arm. Verify calibration. |
| ArUco markers not detected | Ensure good lighting. Print markers at ≥5 cm size. Use `DICT_4X4_50` dictionary. |
| TFLite model not loading | Run `bash scripts/download_model.sh`. Verify path in `.env`. |
| Arm moves to wrong position | Recalibrate ArUco (`python scripts/calibrate_aruco.py`). Verify DH parameters. |
| Conveyor timing off | Recalibrate belt speed sensor. Adjust `CONVEYOR_LEAD_TIME_OFFSET_MS` in `.env`. |
| Emergency stop stuck | Check GPIO 4 wiring. Press and release physical button. Click Resume on dashboard. |
| Mock mode not working | Set `ENABLE_MOCK_HARDWARE=true` in `.env`. No PCA9685 or GPIO required. |

---

## Where to Next

- Add a depth camera (Intel RealSense / OAK-D Lite) for true 3D object localization.
- Integrate ROS 2 MoveIt for advanced motion planning with collision avoidance.
- Train a custom TFLite model on your specific objects using Google Teachable Machine or Edge Impulse.
- Add a second arm for bimanual pick-and-place coordination.
- Implement visual servoing — use real-time camera feedback to correct arm position during approach.
- Add force/torque sensing at the end effector for compliant grasping.
- Build a bin-picking system with randomized object orientations.
- Upgrade to Dynamixel smart servos for position feedback and torque control.
