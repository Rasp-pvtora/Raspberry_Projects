# TSD — AI-Vision Pick-and-Place Robotic Arm

## 1 · Scope

Build a computer-vision-guided robotic arm system on Raspberry Pi. The Pi Camera detects and classifies objects (color, shape, or TFLite-trained class), computes the object's world-space (x, y, z) via ArUco marker calibration, solves inverse kinematics for joint angles, and drives a 4/6-DOF servo arm via PCA9685 to pick and place objects between containers. Includes a Flask + SocketIO dark-themed web dashboard with joint/Cartesian control, teach mode, live camera, and safety limits.

### In scope

| Area | Details |
|---|---|
| **Inverse kinematics** | Analytical closed-form (4-DOF), numerical Jacobian (6-DOF) via scipy |
| **Forward kinematics** | DH parameter-based FK for solution verification and visualization |
| **Camera-to-world calibration** | ArUco markers for extrinsic estimation, checkerboard for intrinsics |
| **Object classification** | TFLite inference — color (HSV), shape (contour), trained class (custom model) |
| **Conveyor belt** | DC motor control, speed sensing, lead-time compensation for moving objects |
| **Gripper options** | Suction (pump relay), parallel jaw (servo), soft gripper (servo) |
| **3D pose estimation** | Object orientation from monocular ArUco-referenced plane |
| **Teach mode** | Manual waypoint recording, sequence save/load/replay/loop |
| **Web dashboard** | Flask + SocketIO: joint sliders, Cartesian x/y/z, teach UI, live camera, e-stop |
| **Safety limits** | No-go zones (JSON config), joint angle limits, workspace bounds, e-stop GPIO |
| **Authentication** | bcrypt session auth, rate limiting (10/15min), 24h sessions |
| **Mock mode** | Simulated servos + camera + GPIO for laptop development |
| **Deployment** | rsync to `rasp-pi` (192.168.216.90), systemd service |

### Out of scope

| Area | Reason |
|---|---|
| ROS 2 / MoveIt integration | Adds complexity; documented as upgrade path only |
| Depth camera (RealSense, OAK-D) | ArUco calibration provides sufficient depth for pick-and-place |
| Force/torque sensing | Hobby servos lack feedback; document as Dynamixel upgrade |
| Custom PCB or motor controller design | Off-the-shelf PCA9685 used |
| Multi-arm coordination | Single arm only |
| Cloud ML inference | All inference runs locally on TFLite |
| Mobile app | Web dashboard only |

---

## 2 · MVP features

### 2.1 — PCA9685 servo control

**Priority: P0**

- Initialize PCA9685 via I2C at configured address.
- Set PWM frequency (default 50 Hz for standard servos).
- Map angle (0°–180°) to pulse width (500–2500 µs) per channel.
- Support per-servo min/max pulse calibration via `.env`.
- Home position command: move all joints to configured home angles.
- Mock mode: log servo commands without hardware.

### 2.2 — Forward kinematics (DH parameters)

**Priority: P0**

- Load DH parameter table from `config/dh_params.json`.
- Compute end-effector pose (4×4 homogeneous transform) from joint angles.
- Support 4-DOF and 6-DOF configurations.
- Used to verify IK solutions before sending to servos.

### 2.3 — Inverse kinematics solver

**Priority: P0**

- **Analytical (4-DOF):** Geometric closed-form for base-shoulder-elbow-wrist.
- **Numerical Jacobian (6-DOF):** Iterative solver using `scipy.optimize.minimize` with Jacobian transpose.
- Return multiple solutions when available (elbow-up / elbow-down).
- Reject solutions that violate joint limits.
- Report "unreachable" if no valid solution found.
- Toggle: `IK_SOLVER=analytical` or `IK_SOLVER=jacobian`.

### 2.4 — Camera-to-world calibration

**Priority: P0**

- Camera intrinsic calibration using checkerboard pattern.
- ArUco marker detection (`cv2.aruco.DICT_4X4_50`).
- Compute camera-to-world homography from ≥4 ArUco markers at known positions.
- Transform pixel (u, v) → world (x, y, z) using calibration matrix.
- Save/load calibration to `config/calibration.json`.
- Recalibrate command from dashboard.

### 2.5 — Object detection and classification

**Priority: P0**

- **Color mode:** HSV thresholding → contour → centroid.
- **Shape mode:** Contour approximation → classify circle/square/triangle.
- **TFLite mode:** Run `.tflite` model, return class label + bounding box.
- Return: class label, confidence, pixel centroid (u, v).
- Convert pixel → world (x, y, z) using calibration.

### 2.6 — Pick-and-place pipeline

**Priority: P0**

- **Detect:** Capture frame → classify → get (x, y, z).
- **Plan:** IK solver → joint angles → safety check.
- **Approach:** Trajectory to position above object (z + clearance).
- **Pick:** Lower to object → activate gripper → raise.
- **Move:** Trajectory to place container position.
- **Place:** Lower → release gripper → raise → return to home.

### 2.7 — Web dashboard

**Priority: P0**

**Database schema:**

**Table: `pick_place_log`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | Operation time |
| `object_class` | TEXT | Detected class (color/shape/TFLite label) |
| `confidence` | REAL | Detection confidence |
| `world_x` | REAL | Object world X coordinate (mm) |
| `world_y` | REAL | Object world Y coordinate (mm) |
| `world_z` | REAL | Object world Z coordinate (mm) |
| `place_container` | TEXT | Target container name |
| `joint_angles` | TEXT | JSON array of joint angles used |
| `duration_ms` | INTEGER | Total pick-place duration (ms) |
| `result` | TEXT | `success`, `ik_failed`, `safety_blocked`, `grip_failed` |
| `image_path` | TEXT | Path to detection snapshot |

**Table: `teach_sequences`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT UNIQUE | Sequence name |
| `created_at` | DATETIME | Creation time |
| `updated_at` | DATETIME | Last modification |
| `waypoints` | TEXT | JSON array of waypoints [{joints: [...], gripper: bool, delay_ms: int}] |
| `loop` | INTEGER | 1 = loop, 0 = single run |
| `speed_scale` | REAL | Replay speed multiplier (0.1–2.0) |

**Table: `calibration_data`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | Calibration time |
| `camera_matrix` | TEXT | JSON 3×3 intrinsic matrix |
| `dist_coeffs` | TEXT | JSON distortion coefficients |
| `world_transform` | TEXT | JSON 4×4 camera-to-world transform |
| `aruco_positions` | TEXT | JSON array of marker world positions |
| `reprojection_error` | REAL | Calibration reprojection error (px) |

**Table: `settings`**

| Column | Type | Description |
|---|---|---|
| `key` | TEXT PK | Setting name |
| `value` | TEXT | Setting value (JSON) |
| `updated_at` | DATETIME | Last update |

### 2.8 — Authentication

**Priority: P0**

- bcrypt password hashing.
- Rate limiting: 10 attempts / 15 min per IP.
- Session cookies (HttpOnly, SameSite).
- Session expiry: 24 hours.

### 2.9 — Safety manager

**Priority: P0**

- Joint angle limits enforced before every servo command.
- No-go zones: rectangular/cylindrical volumes in world coordinates.
- Workspace bounds: maximum reach radius.
- Emergency stop: GPIO interrupt (physical button) + web button → immediately disable all PCA9685 channels.
- Speed limits: max angular velocity per joint (degrees/sec).
- Resume requires explicit unlock command (web or GPIO reset).

### 2.10 — Mock hardware

**Priority: P0**

- Simulated PCA9685 (log commands, track virtual joint angles).
- Simulated camera (sample images with colored shapes).
- Virtual GPIO (log e-stop, LEDs to console).
- All dashboard features work identically.

### 2.11 — Deploy script

**Priority: P0**

- `deploy/deploy_to_pi.sh`: rsync + venv + pip install.
- systemd service unit documented in README.

---

## 3 · Nice-to-have features

### 3.1 — Conveyor belt integration

**Requires:** DC motor + motor driver + speed sensor.

- Belt speed sensing via encoder/photointerrupter on GPIO interrupt.
- Lead time calculation: distance from camera FOV center to pick zone / belt speed.
- Arm pre-positions and times the pick.
- Toggle: `ENABLE_CONVEYOR=true`.

### 3.2 — 3D pose estimation

**Requires:** ArUco calibration + 6-DOF IK solver.

- Estimate object orientation from contour + ArUco height reference.
- 6-DOF IK targets position + orientation.
- Toggle: `ENABLE_3D_POSE=true`.

### 3.3 — Teach mode

**Requires:** Web dashboard.

- Record waypoints from current joint positions.
- Save/load named sequences.
- Replay at configurable speed.
- Loop mode for production.
- Toggle: `ENABLE_TEACH_MODE=true`.

### 3.4 — Multiple place containers

- Define multiple target containers with world coordinates.
- Route detected objects to containers by class (e.g., red → bin A, blue → bin B).
- Configure via `PLACE_CONTAINERS` in `.env` (JSON array).

---

## 4 · Environment configuration (.env.default)

```ini
###############################################################################
# AI-VISION PICK-AND-PLACE ROBOTIC ARM — ENVIRONMENT CONFIGURATION
# Copy to .env and customize before deployment
# All features are toggleable via ENABLE_* flags
###############################################################################

# ─── General ────────────────────────────────────────────────────
PORT=5000
HOST=0.0.0.0
SESSION_SECRET=CHANGE_ME_TO_A_RANDOM_STRING
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
LOG_LEVEL=INFO

# ─── Arm Configuration ─────────────────────────────────────────
# Degrees of freedom: 4 or 6
ARM_DOF=6

# IK solver: analytical (4-DOF only) or jacobian (4/6-DOF)
IK_SOLVER=jacobian

# DH parameters file
DH_PARAMS_PATH=./config/dh_params.json

# Home position (degrees, comma-separated per joint)
HOME_POSITION=90,90,90,90,90,90

# ─── PCA9685 Servo Driver ──────────────────────────────────────
PCA9685_I2C_ADDRESS=0x40
PCA9685_FREQUENCY=50

# Per-servo pulse range (µs) — calibrate for your servos
# Format: min_pulse,max_pulse
SERVO_J1_PULSE=500,2500
SERVO_J2_PULSE=500,2500
SERVO_J3_PULSE=500,2500
SERVO_J4_PULSE=500,2500
SERVO_J5_PULSE=500,2500
SERVO_J6_PULSE=500,2500
SERVO_GRIPPER_PULSE=500,2500

# Servo PCA9685 channel assignments
SERVO_J1_CHANNEL=0
SERVO_J2_CHANNEL=1
SERVO_J3_CHANNEL=2
SERVO_J4_CHANNEL=3
SERVO_J5_CHANNEL=4
SERVO_J6_CHANNEL=5
SERVO_GRIPPER_CHANNEL=6

# ─── Joint Limits (degrees) ────────────────────────────────────
# Format: min_angle,max_angle
JOINT_1_LIMITS=0,180
JOINT_2_LIMITS=15,165
JOINT_3_LIMITS=0,180
JOINT_4_LIMITS=0,180
JOINT_5_LIMITS=0,180
JOINT_6_LIMITS=0,180

# Max angular velocity per joint (degrees/sec)
MAX_JOINT_VELOCITY=60

# ─── Gripper ───────────────────────────────────────────────────
# Type: parallel_jaw, suction, soft_gripper
GRIPPER_TYPE=parallel_jaw

# Parallel jaw: open angle, close angle
GRIPPER_OPEN_ANGLE=90
GRIPPER_CLOSE_ANGLE=30

# Suction: pump relay GPIO pin
SUCTION_PUMP_GPIO=24

# Gripper settle time (ms) — wait after grip/release before moving
GRIPPER_SETTLE_MS=300

# ─── Camera ─────────────────────────────────────────────────────
ENABLE_CAMERA=true
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=15

# ─── ArUco Calibration ─────────────────────────────────────────
ENABLE_ARUCO_CALIBRATION=true
ARUCO_DICTIONARY=DICT_4X4_50
ARUCO_MARKER_SIZE_MM=50
CALIBRATION_FILE=./config/calibration.json

# ─── Object Detection ──────────────────────────────────────────
ENABLE_TFLITE=true

# Detection mode: color, shape, tflite
DETECTION_MODE=color

# Color detection: HSV ranges (H_min,S_min,V_min,H_max,S_max,V_max)
COLOR_RED=0,120,70,10,255,255
COLOR_GREEN=36,50,70,86,255,255
COLOR_BLUE=94,80,50,126,255,255
COLOR_YELLOW=20,100,100,35,255,255

# Shape detection: min contour area (pixels)
SHAPE_MIN_AREA=500

# TFLite model
TFLITE_MODEL_PATH=./models/object_classifier.tflite
TFLITE_LABELS_PATH=./models/labels.txt
TFLITE_CONFIDENCE=0.5

# ─── Pick-and-Place ────────────────────────────────────────────
# Approach height above object (mm)
PICK_APPROACH_HEIGHT_MM=50

# Place containers (JSON array: [{"name":"bin_a","x":150,"y":-100,"z":0}, ...])
PLACE_CONTAINERS=[{"name":"bin_a","x":150,"y":-100,"z":0},{"name":"bin_b","x":150,"y":100,"z":0}]

# Object-to-container routing (JSON: {"red":"bin_a","blue":"bin_b"})
CLASS_ROUTING={"red":"bin_a","blue":"bin_b","green":"bin_a","yellow":"bin_b"}

# ─── Conveyor Belt ──────────────────────────────────────────────
ENABLE_CONVEYOR=false
CONVEYOR_MOTOR_DIR_GPIO=17
CONVEYOR_MOTOR_PWM_GPIO=18
CONVEYOR_SPEED_SENSOR_GPIO=27
CONVEYOR_SPEED_DEFAULT=50
CONVEYOR_LEAD_TIME_OFFSET_MS=0

# Pick zone X range on conveyor (mm from arm base)
CONVEYOR_PICK_ZONE_MIN_X=80
CONVEYOR_PICK_ZONE_MAX_X=120

# ─── Teach Mode ─────────────────────────────────────────────────
ENABLE_TEACH_MODE=true
TEACH_SEQUENCE_DIR=./config/sequences

# ─── 3D Pose Estimation ────────────────────────────────────────
ENABLE_3D_POSE=false

# ─── Safety Limits ──────────────────────────────────────────────
ENABLE_SAFETY_LIMITS=true

# No-go zones config
NO_GO_ZONES_PATH=./config/no_go_zones.json

# Emergency stop GPIO (active LOW with pull-up)
ESTOP_GPIO=4

# Status LEDs
LED_RUNNING_GPIO=22
LED_ERROR_GPIO=23

# Workspace radius limit (mm from base)
WORKSPACE_MAX_RADIUS_MM=350
WORKSPACE_MIN_RADIUS_MM=60

# ─── Web Dashboard ──────────────────────────────────────────────
ENABLE_WEB_DASHBOARD=true

# SocketIO update rate for joint state (Hz)
SOCKETIO_JOINT_RATE=10

# Camera stream JPEG quality (0-100)
STREAM_JPEG_QUALITY=50

# ─── Mock Hardware ──────────────────────────────────────────────
ENABLE_MOCK_HARDWARE=false

# ─── Deployment ─────────────────────────────────────────────────
DEPLOY_HOST=rasp-pi
DEPLOY_PATH=/home/pi/Projects/PickAndPlace
```

---

## 5 · DH Parameters Configuration

The Denavit-Hartenberg parameter table defines the arm's kinematic chain. Each row describes a joint-to-joint transformation.

### DH Convention (Modified DH)

Each row: `[alpha_i-1, a_i-1, d_i, theta_offset_i]`

- `alpha` — twist angle about X (radians)
- `a` — link length along X (mm)
- `d` — link offset along Z (mm)
- `theta_offset` — joint angle offset (radians, added to commanded angle)

### `config/dh_params.json`

```json
{
  "description": "6-DOF hobby servo arm DH parameters (Modified DH convention)",
  "units": {
    "length": "mm",
    "angle": "radians"
  },
  "dof": 6,
  "links": [
    {
      "joint": 1,
      "name": "base",
      "alpha": 0,
      "a": 0,
      "d": 70,
      "theta_offset": 0,
      "type": "revolute"
    },
    {
      "joint": 2,
      "name": "shoulder",
      "alpha": -1.5708,
      "a": 0,
      "d": 0,
      "theta_offset": -1.5708,
      "type": "revolute"
    },
    {
      "joint": 3,
      "name": "elbow",
      "alpha": 0,
      "a": 105,
      "d": 0,
      "theta_offset": 0,
      "type": "revolute"
    },
    {
      "joint": 4,
      "name": "wrist_pitch",
      "alpha": -1.5708,
      "a": 0,
      "d": 98,
      "theta_offset": -1.5708,
      "type": "revolute"
    },
    {
      "joint": 5,
      "name": "wrist_roll",
      "alpha": 1.5708,
      "a": 0,
      "d": 0,
      "theta_offset": 0,
      "type": "revolute"
    },
    {
      "joint": 6,
      "name": "wrist_yaw",
      "alpha": -1.5708,
      "a": 0,
      "d": 65,
      "theta_offset": 0,
      "type": "revolute"
    }
  ],
  "tool_offset": {
    "x": 0,
    "y": 0,
    "z": 40,
    "description": "Distance from J6 to gripper tip (mm)"
  }
}
```

> **Note:** Measure your specific arm's link lengths with calipers. The values above are typical for a generic 6-DOF hobby servo arm (LeArm / SainSmart style). Use `scripts/measure_dh.py` to interactively measure and record DH parameters.

### 4-DOF Simplification

For 4-DOF arms, use only joints 1–4 and set `ARM_DOF=4` / `IK_SOLVER=analytical`. The analytical solver uses geometric decomposition:
1. J1 (base) = `atan2(y, x)`.
2. J2 + J3 (shoulder + elbow) solved via triangle law of cosines.
3. J4 (wrist) = desired pitch − (J2 + J3).

---

## 6 · High-level architecture

```
┌─────────────────────────────────────────────────────────────────┐
│            AI-VISION PICK-AND-PLACE ROBOTIC ARM                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  VISION PIPELINE                         │  │
│  │  Camera → ArUco calibrate → TFLite/Color/Shape detect   │  │
│  │  → pixel (u,v) → world (x,y,z) → object class          │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                 MOTION PLANNING                          │  │
│  │  target (x,y,z,r,p,y) → IK solver → joint angles        │  │
│  │  → safety check → trajectory interpolation               │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                 HARDWARE CONTROL                         │  │
│  │  PCA9685 servo driver │ Gripper │ Conveyor │ GPIO        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 WEB DASHBOARD                            │  │
│  │  Flask + SocketIO │ Joint/Cartesian │ Teach │ Camera     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 SAFETY MANAGER                           │  │
│  │  Joint limits │ No-go zones │ E-stop GPIO │ Speed limits │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7 · Security / Threat model

| # | Threat | Mitigation |
|---|---|---|
| T1 | Credential exposure | `.env` in `.gitignore`, `chmod 600` |
| T2 | Brute-force login | Rate limiting: 10/15 min |
| T3 | Session hijacking | Strong `SESSION_SECRET`, HttpOnly, SameSite cookies |
| T4 | XSS | Jinja2 auto-escaping |
| T5 | SQL injection | Parameterized queries (sqlite3 placeholders) |
| T6 | Unauthorized arm control | All endpoints require auth |
| T7 | Physical harm from arm | Safety limits, no-go zones, e-stop GPIO, speed limits |
| T8 | I2C bus spoofing | Physical security only — document in threat model |
| T9 | Camera feed interception | Local network only, HTTPS via nginx reverse proxy |
| T10 | Servo runaway | Watchdog: if no command for 2 s → hold position; if no heartbeat 10 s → park and disable |

---

## 8 · Suggested tech stack

### Backend

| Component | Technology | Justification |
|---|---|---|
| Language | Python 3.11+ | Best ML/CV/robotics ecosystem |
| Web framework | Flask 3.1 + SocketIO | Lightweight, real-time capable |
| ML inference | tflite-runtime | Optimized for Raspberry Pi |
| Computer vision | OpenCV 4.10 | ArUco, calibration, contour analysis |
| IK solver | numpy + scipy | Matrix math, numerical optimization |
| Servo control | adafruit-circuitpython-pca9685 | I2C servo driver |
| Database | SQLite | Zero-config file-based |
| GPIO | RPi.GPIO | E-stop, LEDs, conveyor |
| Auth | bcrypt + Flask sessions | Password hashing + rate limiting |

### Frontend

| Component | Technology |
|---|---|
| Templates | Jinja2 |
| Real-time | Socket.IO client (CDN) |
| Sliders | HTML5 range inputs + custom JS |
| Styling | Custom CSS (dark theme) |

---

## 9 · Development phases

### Phase 1 — PCA9685 servo control and FK

| # | Task | Priority |
|---|---|---|
| 1.1 | Project scaffolding (Flask app, .env, DB) | P0 |
| 1.2 | PCA9685 servo driver module | P0 |
| 1.3 | DH parameter loader and FK solver | P0 |
| 1.4 | Joint home position and manual angle control | P0 |
| 1.5 | Mock hardware mode | P0 |
| 1.6 | Unit tests (FK) | P1 |

### Phase 2 — Inverse kinematics

| # | Task | Priority |
|---|---|---|
| 2.1 | Analytical IK solver (4-DOF) | P0 |
| 2.2 | Numerical Jacobian IK solver (6-DOF) | P0 |
| 2.3 | Joint limit enforcement | P0 |
| 2.4 | Trajectory interpolation (joint-space linear) | P0 |
| 2.5 | Unit tests (IK) | P1 |

### Phase 3 — Vision pipeline

| # | Task | Priority |
|---|---|---|
| 3.1 | Camera capture module | P0 |
| 3.2 | Camera intrinsic calibration (checkerboard) | P0 |
| 3.3 | ArUco marker detection and camera-to-world calibration | P0 |
| 3.4 | Color-based object detection (HSV) | P0 |
| 3.5 | Shape-based object detection (contours) | P0 |
| 3.6 | TFLite model inference | P0 |
| 3.7 | Pixel → world coordinate transform | P0 |
| 3.8 | Unit tests (calibration transforms) | P1 |

### Phase 4 — Pick-and-place pipeline

| # | Task | Priority |
|---|---|---|
| 4.1 | Arm controller (move_to, pick, place) | P0 |
| 4.2 | Gripper abstraction (jaw, suction, soft) | P0 |
| 4.3 | Full pick-and-place pipeline | P0 |
| 4.4 | Object-to-container routing by class | P0 |
| 4.5 | Pick-place logging to database | P0 |

### Phase 5 — Web dashboard

| # | Task | Priority |
|---|---|---|
| 5.1 | Flask app + auth + layout (dark theme) | P0 |
| 5.2 | Joint slider control page | P0 |
| 5.3 | Cartesian x/y/z control page | P0 |
| 5.4 | Live camera feed with detection overlay (SocketIO) | P0 |
| 5.5 | E-stop button on every page | P0 |
| 5.6 | Teach mode page (record/replay) | P1 |
| 5.7 | Settings page (calibration, gripper, safety) | P1 |
| 5.8 | System status (CPU temp, uptime) | P1 |

### Phase 6 — Safety and advanced features

| # | Task | Priority |
|---|---|---|
| 6.1 | Safety manager (no-go zones, workspace bounds) | P0 |
| 6.2 | E-stop GPIO integration | P0 |
| 6.3 | Speed limiting per joint | P0 |
| 6.4 | Conveyor belt integration | P1 |
| 6.5 | 3D pose estimation | P2 |
| 6.6 | Teach mode looping and editing | P1 |

### Phase 7 — Deployment and polish

| # | Task | Priority |
|---|---|---|
| 7.1 | Deploy script (rsync) | P0 |
| 7.2 | systemd service | P1 |
| 7.3 | Threat model document | P1 |
| 7.4 | End-to-end testing | P1 |
| 7.5 | README finalization | P0 |

---

## 10 · Performance expectations

| Metric | Pi 4 (4 GB) | Pi 5 (8 GB) |
|---|---|---|
| TFLite inference (MobileNet) | ~80 ms/frame | ~40 ms/frame |
| Color/shape detection | ~15 ms/frame | ~8 ms/frame |
| IK solve (analytical, 4-DOF) | <1 ms | <1 ms |
| IK solve (Jacobian, 6-DOF) | ~5–20 ms | ~2–10 ms |
| FK compute | <1 ms | <1 ms |
| Camera capture (640×480) | ~30 FPS | ~30 FPS |
| Servo update rate | 50 Hz (PCA9685) | 50 Hz (PCA9685) |
| Full pick-and-place cycle | ~3–5 s | ~2–4 s |
| SocketIO latency | ~20 ms | ~10 ms |
| Dashboard stream FPS | ~10 FPS | ~15 FPS |

---

## 11 · Deliverables

| # | Deliverable | Phase |
|---|---|---|
| D1 | PCA9685 servo control + FK solver + mock mode | Phase 1 |
| D2 | IK solver (analytical + Jacobian) + trajectory | Phase 2 |
| D3 | Vision pipeline (camera, ArUco, TFLite, color, shape) | Phase 3 |
| D4 | Full pick-and-place pipeline with gripper + routing | Phase 4 |
| D5 | Web dashboard with joint/Cartesian/teach/camera/e-stop | Phase 5 |
| D6 | Safety manager, conveyor, 3D pose, deployment | Phase 6–7 |
