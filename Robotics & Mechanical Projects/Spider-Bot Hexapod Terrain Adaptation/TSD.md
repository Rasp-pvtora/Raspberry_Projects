# TSD — 🕷️ Spider-Bot Hexapod Terrain Adaptation

## 1 · Scope

Build a 6-legged hexapod robot with 18 servos (6 legs × 3 joints: coxa, femur, tibia) on Raspberry Pi. Implements switchable gait patterns (tripod/wave/ripple/free), terrain adaptation via FSR sensors on each foot, IMU-based body stabilization (MPU6050 + PID), FPV camera head with pan/tilt streaming, autonomous navigation with ultrasonic obstacle avoidance, battery management via INA219, and real-time 3D IK visualization (Three.js). Includes a Flask + SocketIO dark-themed web dashboard with gait control, speed tuning, gait recording/replay, and per-leg diagnostics.

### In scope

| Area | Details |
|---|---|
| **Per-leg inverse kinematics** | 3-DOF IK (coxa/femur/tibia) for each leg using geometric solution |
| **Body-level IK** | Translate/rotate body relative to foot positions for body posing |
| **Gait engine** | State machine: tripod, wave, ripple, free (custom) patterns |
| **Terrain adaptation** | FSR on each foot → auto-adjust leg extension during ground contact |
| **IMU stabilization** | MPU6050 pitch/roll → PID → body IK tilt correction |
| **FPV camera** | Pi Camera + pan/tilt servos, MJPEG stream to dashboard |
| **Autonomous navigation** | HC-SR04 ×3 → obstacle avoidance, wall following, return-home |
| **Battery management** | INA219 voltage/current monitoring, low-battery auto-return |
| **IK visualization** | Three.js real-time 3D hexapod visualization on dashboard |
| **Gait recording** | Record joint states during walking, save/replay custom gaits |
| **Speed control** | Adjustable walking speed and turn radius from dashboard |
| **Modular leg config** | Configure leg count (4/6/8) and joint count from `.env` |
| **Web dashboard** | Flask + SocketIO: 3D view, gait control, FPV, nav, battery, settings |
| **Authentication** | bcrypt session auth, rate limiting (10/15min), 24h sessions |
| **Mock mode** | Simulated servos + sensors for laptop development |
| **Deployment** | rsync to `rasp-pi` (192.168.216.90), systemd service |

### Out of scope

| Area | Reason |
|---|---|
| ROS 2 / MoveIt integration | Adds complexity; documented as upgrade path only |
| LIDAR / SLAM mapping | HC-SR04 provides basic obstacle avoidance; LIDAR documented as upgrade |
| Computer vision navigation | Camera used for FPV only; CV nav documented as upgrade |
| Dynamixel smart servos | Code targets SG90/MG90S via PCA9685; Dynamixel documented as upgrade |
| Custom PCB design | Off-the-shelf PCA9685, MCP3008, INA219 used |
| Swarm coordination | Single hexapod only |
| Mobile app | Web dashboard only |
| GPS-based return-home | Dead reckoning only; GPS documented as optional add-on |

---

## 2 · MVP features

### 2.1 — Dual PCA9685 servo control (18 servos)

**Priority: P0**

- Initialize two PCA9685 boards via I2C at addresses `0x40` and `0x41`.
- Set PWM frequency to 50 Hz for standard servos.
- Map angle (0°–180°) to pulse width (500–2500 µs) per channel.
- Support per-servo min/max pulse calibration via `.env`.
- Servo addressing: `(board, channel)` tuple for each of the 18 leg servos + 2 pan/tilt.
- Home position command: move all joints to configured neutral angles.
- Mock mode: log servo commands without hardware.

### 2.2 — Leg geometry and configuration

**Priority: P0**

- Load leg mount positions from `config/leg_geometry.json`:
  - Per-leg: mount (x, y) offset from body center, mount angle (degrees), coxa/femur/tibia link lengths (mm).
- Support 6-leg (hexapod) default, configurable to 4-leg (quadruped) or 8-leg (octopod) via `MODULAR_LEG_CONFIG`.
- Per-joint limits (min/max angle) configurable in `.env`.

### 2.3 — Per-leg inverse kinematics (3-DOF)

**Priority: P0**

Given a target foot position `(x, y, z)` relative to the coxa mount point:

1. **Coxa angle** `θ₁ = atan2(y, x)`
2. **Projected distance** in the leg plane: `r = sqrt(x² + y²) − L_coxa`
3. **Distance to foot** in leg plane: `d = sqrt(r² + z²)`
4. **Tibia angle** via law of cosines:
   - `cos(θ₃) = (L_femur² + L_tibia² − d²) / (2 × L_femur × L_tibia)`
   - `θ₃ = acos(cos(θ₃))` (knee bend angle)
5. **Femur angle**:
   - `α = atan2(z, r)`
   - `β = atan2(L_tibia × sin(θ₃), L_femur + L_tibia × cos(θ₃))`
   - `θ₂ = α + β` (or `α − β` for knee-up vs knee-down)
6. Filter by joint limits. Report unreachable if `d > L_femur + L_tibia` or `d < |L_femur − L_tibia|`.

### 2.4 — Body-level inverse kinematics

**Priority: P0**

- Given body translation `(tx, ty, tz)` and rotation `(roll, pitch, yaw)`:
  - Compute the new position of each foot relative to the body center.
  - For each foot: subtract body transform → get foot position in local leg frame → per-leg IK.
- Used for: body posing (tilt, shift, rotate) while feet stay planted.
- Used by IMU stabilization to apply pitch/roll correction.

### 2.5 — Gait engine (state machine)

**Priority: P0**

Gait state machine for each leg: `SUPPORT → LIFT → SWING → DOWN → SUPPORT`

**Tripod gait:** Legs {1, 4, 5} and {2, 3, 6} alternate. 3 legs swing while 3 support.

**Wave gait:** Legs move one at a time in sequence: 1 → 2 → 3 → 4 → 5 → 6. Maximum stability.

**Ripple gait:** Legs move in pairs with overlap: (1,4) → (2,5) → (3,6). Balance of speed/stability.

**Free gait:** User-defined sequence from gait recorder.

Parameters per gait:
- `STEP_HEIGHT_MM` — how high each foot lifts during swing.
- `STRIDE_LENGTH_MM` — forward distance per step cycle.
- `CYCLE_TIME_MS` — duration of one full gait cycle.
- `BODY_HEIGHT_MM` — default standing height of body above ground.

### 2.6 — Web dashboard

**Priority: P0**

**Database schema:**

**Table: `gait_log`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | Log time |
| `gait_pattern` | TEXT | Active gait (tripod/wave/ripple/free) |
| `speed` | REAL | Walking speed (mm/s) |
| `duration_s` | REAL | Duration of walk session |
| `distance_mm` | REAL | Estimated distance traveled |
| `avg_current_ma` | REAL | Average current draw |
| `terrain_events` | INTEGER | Number of terrain adaptation events |

**Table: `battery_log`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | Reading time |
| `voltage_v` | REAL | Battery bus voltage |
| `current_ma` | REAL | Load current (mA) |
| `power_mw` | REAL | Power consumption (mW) |
| `cell_voltage_v` | REAL | Per-cell voltage (voltage / 3) |

**Table: `recorded_gaits`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT UNIQUE | Gait name |
| `created_at` | DATETIME | Creation time |
| `updated_at` | DATETIME | Last modification |
| `frames` | TEXT | JSON array of gait frames [{joints: {leg1: [c,f,t], ...}, timing_ms: int}] |
| `cycle_count` | INTEGER | Number of recorded cycles |
| `metadata` | TEXT | JSON: stride, height, speed at time of recording |

**Table: `settings`**

| Column | Type | Description |
|---|---|---|
| `key` | TEXT PK | Setting name |
| `value` | TEXT | Setting value (JSON) |
| `updated_at` | DATETIME | Last update |

### 2.7 — Authentication

**Priority: P0**

- bcrypt password hashing.
- Rate limiting: 10 attempts / 15 min per IP.
- Session cookies (HttpOnly, SameSite).
- Session expiry: 24 hours.

### 2.8 — Mock hardware

**Priority: P0**

- Simulated dual PCA9685 (log commands, track 18 virtual joint angles).
- Simulated MPU6050 (returns configurable pitch/roll or gentle oscillation).
- Simulated FSR ×6 (returns random force values or flat terrain).
- Simulated HC-SR04 ×3 (returns configurable distances).
- Simulated INA219 (returns configurable voltage/current).
- Simulated camera (returns sample frames).
- All dashboard features work identically.

### 2.9 — Deploy script

**Priority: P0**

- `deploy/deploy_to_pi.sh`: rsync + venv + pip install.
- systemd service unit documented in README.

---

## 3 · Nice-to-have features

### 3.1 — Terrain adaptation (FSR)

**Requires:** FSR ×6 + MCP3008 ADC.

- Each foot has a force-sensitive resistor, read via SPI (MCP3008 channels 0–5).
- During leg **DOWN** phase: extend tibia until FSR exceeds contact threshold.
- On uneven terrain, each leg finds its own ground level independently.
- Force feedback prevents over-pressing on hard surfaces.
- Toggle: `ENABLE_TERRAIN_ADAPTATION=true`.

### 3.2 — IMU stabilization

**Requires:** MPU6050 on I2C.

- Read accelerometer + gyroscope at 100 Hz.
- Complementary filter: `angle = 0.98 × (angle + gyro × dt) + 0.02 × accel_angle`.
- Dual PID controllers for pitch and roll.
- Output: body tilt correction fed to body IK.
- Toggle: `ENABLE_IMU_STABILIZATION=true`.

### 3.3 — FPV camera

**Requires:** Pi Camera + pan/tilt bracket + 2 SG90 servos.

- MJPEG stream via SocketIO at configured FPS.
- Pan servo (0°–180°) and tilt servo (0°–180°) on PCA9685 Board 2 ch 9–10.
- Dashboard joystick or sliders for aiming.
- Toggle: `ENABLE_FPV_CAMERA=true`.

### 3.4 — Autonomous navigation

**Requires:** HC-SR04 ultrasonic ×3.

- Obstacle avoidance: front sensor < threshold → stop + turn toward open side.
- Wall following: side sensor PID maintains constant distance.
- Return home: dead-reckoning integration of gait steps.
- Toggle: `ENABLE_AUTONOMOUS_NAV=true`.

### 3.5 — Battery management

**Requires:** INA219 on I2C.

- Read voltage/current/power at 10 Hz.
- LiPo 3S thresholds: warning 10.5V, critical 9.9V.
- On critical: auto-return, reduce speed, disable non-essential features.
- Toggle: `ENABLE_BATTERY_MANAGEMENT=true`.

### 3.6 — IK visualization (Three.js)

**Requires:** Dashboard only — no extra hardware.

- Three.js scene with hexapod body + 6 legs rendered as segments.
- Updated at 20 Hz from SocketIO joint state.
- Color-coded phase: green (support), blue (swing), red (overload).
- Mouse orbit/zoom for inspection.
- Toggle: `ENABLE_IK_VISUALIZATION=true`.

### 3.7 — Gait recording

**Requires:** Working gait engine.

- Capture joint angles + timing at each gait step.
- Save as JSON to `config/gait_sequences/`.
- Replay as a "free" gait pattern.
- Toggle: `ENABLE_GAIT_RECORDING=true`.

### 3.8 — Modular leg configuration

- `LEG_COUNT=4|6|8` — dynamically configure number of legs.
- `JOINTS_PER_LEG=2|3` — support 2-DOF (coxa+femur) or 3-DOF (coxa+femur+tibia).
- Leg mount positions auto-calculated from `LEG_COUNT` if not individually specified.
- Toggle: `ENABLE_MODULAR_LEG_CONFIG=true`.

---

## 4 · Environment configuration (.env.default)

```ini
###############################################################################
# SPIDER-BOT HEXAPOD TERRAIN ADAPTATION — ENVIRONMENT CONFIGURATION
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

# ─── Feature Toggles ───────────────────────────────────────────
ENABLE_GAIT_ENGINE=true
ENABLE_TERRAIN_ADAPTATION=true
ENABLE_IMU_STABILIZATION=true
ENABLE_FPV_CAMERA=true
ENABLE_AUTONOMOUS_NAV=false
ENABLE_BATTERY_MANAGEMENT=true
ENABLE_IK_VISUALIZATION=true
ENABLE_MODULAR_LEG_CONFIG=false
ENABLE_GAIT_RECORDING=true
ENABLE_SPEED_CONTROL=true
ENABLE_MOCK_HARDWARE=false

# ─── Leg Configuration ─────────────────────────────────────────
# Number of legs (4, 6, or 8 — requires ENABLE_MODULAR_LEG_CONFIG for non-6)
LEG_COUNT=6

# Joints per leg (2 or 3 — requires ENABLE_MODULAR_LEG_CONFIG for non-3)
JOINTS_PER_LEG=3

# Link lengths (mm) — measure your frame
COXA_LENGTH_MM=30
FEMUR_LENGTH_MM=80
TIBIA_LENGTH_MM=120

# Body dimensions for leg mount calculation (mm)
BODY_LENGTH_MM=160
BODY_WIDTH_MM=80

# Leg geometry config file (overrides BODY_LENGTH/WIDTH if present)
LEG_GEOMETRY_PATH=./config/leg_geometry.json

# Default standing height (mm — body center to ground)
BODY_HEIGHT_MM=80

# ─── PCA9685 Servo Drivers ─────────────────────────────────────
PCA9685_BOARD1_ADDRESS=0x40
PCA9685_BOARD2_ADDRESS=0x41
PCA9685_FREQUENCY=50

# Per-servo pulse range (µs) — calibrate for your SG90s
# Format: min_pulse,max_pulse
SERVO_DEFAULT_PULSE=500,2500

# Per-servo overrides (board:channel=min,max) — uncomment and adjust as needed
# SERVO_1_0_PULSE=500,2500
# SERVO_1_1_PULSE=500,2500
# ... (18 leg servos + 2 pan/tilt)

# Servo channel mapping (board:channel for each leg joint)
# Leg 1 (Front-Right): coxa, femur, tibia
LEG1_CHANNELS=1:0,1:1,1:2
LEG2_CHANNELS=1:3,1:4,1:5
LEG3_CHANNELS=1:6,1:7,1:8
LEG4_CHANNELS=2:0,2:1,2:2
LEG5_CHANNELS=2:3,2:4,2:5
LEG6_CHANNELS=2:6,2:7,2:8

# Camera pan/tilt channels
PAN_TILT_CHANNELS=2:9,2:10

# ─── Joint Limits (degrees) ────────────────────────────────────
# Format: min_angle,max_angle
COXA_LIMITS=0,180
FEMUR_LIMITS=0,180
TIBIA_LIMITS=0,180
PAN_LIMITS=0,180
TILT_LIMITS=30,150

# ─── Gait Parameters ───────────────────────────────────────────
# Default gait: tripod, wave, ripple, free
GAIT_PATTERN=tripod

# Step height (mm) — how high each foot lifts during swing
STEP_HEIGHT_MM=30

# Stride length (mm) — forward distance per step cycle
STRIDE_LENGTH_MM=50

# Gait cycle time (ms) — duration of one full cycle
CYCLE_TIME_MS=1000

# Turn radius (mm) — 0 = spin in place, large = wide turn
TURN_RADIUS_MM=0

# Walk speed scale (0.1–2.0)
SPEED_SCALE=1.0

# ─── IMU / Stabilization ───────────────────────────────────────
MPU6050_I2C_ADDRESS=0x68

# Complementary filter alpha (0–1, higher = trust gyro more)
IMU_FILTER_ALPHA=0.98

# IMU read rate (Hz)
IMU_RATE_HZ=100

# PID tuning file
PID_TUNING_PATH=./config/pid_tuning.json

# PID defaults (used if pid_tuning.json not found)
PID_PITCH_KP=1.0
PID_PITCH_KI=0.05
PID_PITCH_KD=0.2
PID_ROLL_KP=1.0
PID_ROLL_KI=0.05
PID_ROLL_KD=0.2

# Max stabilization tilt correction (degrees)
MAX_TILT_CORRECTION_DEG=15

# ─── FSR / Terrain Adaptation ──────────────────────────────────
# MCP3008 SPI settings
MCP3008_SPI_BUS=0
MCP3008_SPI_DEVICE=0

# FSR channels on MCP3008 (one per foot)
FSR_CHANNELS=0,1,2,3,4,5

# Contact threshold (0–1023 ADC value)
FSR_CONTACT_THRESHOLD=200

# Max extra extension during terrain probing (mm)
FSR_MAX_EXTENSION_MM=20

# ─── Ultrasonic Navigation ─────────────────────────────────────
# HC-SR04 GPIO pins (trigger, echo)
ULTRASONIC_FRONT_TRIG=17
ULTRASONIC_FRONT_ECHO=27
ULTRASONIC_LEFT_TRIG=22
ULTRASONIC_LEFT_ECHO=23
ULTRASONIC_RIGHT_TRIG=24
ULTRASONIC_RIGHT_ECHO=25

# Obstacle distance thresholds (cm)
OBSTACLE_STOP_CM=15
OBSTACLE_SLOW_CM=30

# Wall-follow target distance (cm)
WALL_FOLLOW_DISTANCE_CM=20

# ─── Battery Management ────────────────────────────────────────
INA219_I2C_ADDRESS=0x44

# LiPo 3S cell count
BATTERY_CELL_COUNT=3

# Voltage thresholds (per cell)
BATTERY_WARNING_V=3.5
BATTERY_CRITICAL_V=3.3

# Max current draw warning (mA)
BATTERY_MAX_CURRENT_MA=3000

# ─── Camera / FPV ──────────────────────────────────────────────
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=15
STREAM_JPEG_QUALITY=50

# Pan/tilt home position (degrees)
PAN_HOME=90
TILT_HOME=90

# ─── Gait Recording ────────────────────────────────────────────
GAIT_SEQUENCE_DIR=./config/gait_sequences

# ─── Web Dashboard ──────────────────────────────────────────────
ENABLE_WEB_DASHBOARD=true

# SocketIO update rates (Hz)
SOCKETIO_JOINT_RATE=20
SOCKETIO_SENSOR_RATE=10
SOCKETIO_BATTERY_RATE=1

# ─── Deployment ─────────────────────────────────────────────────
DEPLOY_HOST=rasp-pi
DEPLOY_PATH=/home/pi/Projects/SpiderBot
```

---

## 5 · Inverse kinematics math

### 5.1 — Per-leg 3-DOF IK

Each leg is a 3-DOF serial chain mounted on the body at a known position and angle. Given a target foot position `P_foot = (x, y, z)` in the leg's local coordinate frame (origin at coxa joint):

**Step 1 — Coxa angle (yaw rotation around Z):**

$$\theta_1 = \text{atan2}(y,\, x)$$

**Step 2 — Project into the leg plane:**

$$r = \sqrt{x^2 + y^2} - L_{coxa}$$

where $L_{coxa}$ is the coxa link length.

**Step 3 — Distance from femur joint to foot:**

$$d = \sqrt{r^2 + z^2}$$

Check reachability: $|L_{femur} - L_{tibia}| < d < L_{femur} + L_{tibia}$

**Step 4 — Tibia angle (law of cosines):**

$$\cos(\theta_3) = \frac{L_{femur}^2 + L_{tibia}^2 - d^2}{2 \cdot L_{femur} \cdot L_{tibia}}$$

$$\theta_3 = \arccos\!\left(\cos(\theta_3)\right)$$

**Step 5 — Femur angle:**

$$\alpha = \text{atan2}(z,\, r)$$

$$\beta = \text{atan2}\!\left(L_{tibia} \sin(\theta_3),\; L_{femur} + L_{tibia} \cos(\theta_3)\right)$$

$$\theta_2 = \alpha + \beta$$

**Step 6 — Apply joint limits.** Reject if any angle outside `[min, max]`.

### 5.2 — Body-level IK

To translate the body by `(tx, ty, tz)` and rotate by `(roll, pitch, yaw)`:

1. Construct the 4×4 body transform matrix `T_body` from the translation and Euler angles.
2. For each leg $i$: compute the foot position in body frame from the current foot world position.
3. Apply the inverse body transform: `P_foot_local[i] = T_body⁻¹ × P_foot_world[i]`.
4. Convert to leg-local coordinate frame (subtract leg mount offset, rotate by mount angle).
5. Solve per-leg IK for each `P_foot_local[i]`.

This allows the body to translate/rotate while all feet remain planted in their current world positions.

### 5.3 — IK with IMU stabilization

The IMU stabilization loop runs at `IMU_RATE_HZ`:

1. Read MPU6050 accelerometer + gyroscope.
2. Apply complementary filter: `angle = α × (angle + gyro_rate × dt) + (1−α) × accel_angle`.
3. PID for pitch: `correction_pitch = PID(target=0, measured=imu_pitch)`.
4. PID for roll: `correction_roll = PID(target=0, measured=imu_roll)`.
5. Feed corrections to body IK as `(roll=−correction_roll, pitch=−correction_pitch)`.
6. Body IK adjusts leg commands → body stays level on uneven ground.

---

## 6 · Gait state machine

### 6.1 — Leg states

Each leg cycles through four states:

```
SUPPORT ──► LIFT ──► SWING ──► DOWN ──► SUPPORT
   │                                        │
   └────────────────────────────────────────┘
```

| State | Action | Duration |
|---|---|---|
| **SUPPORT** | Foot planted, push body forward (stance phase) | ~60% of cycle |
| **LIFT** | Raise foot to step height | ~10% of cycle |
| **SWING** | Move foot forward to next position | ~20% of cycle |
| **DOWN** | Lower foot to ground (FSR contact if enabled) | ~10% of cycle |

### 6.2 — Gait phase diagrams

**Tripod gait** (fastest, 3+3 alternating):

```
Leg  │ Phase 0 (50%) │ Phase 1 (50%) │
─────┼───────────────┼───────────────┤
  1  │   SWING ███   │  SUPPORT ───  │
  2  │  SUPPORT ───  │   SWING ███   │
  3  │   SWING ███   │  SUPPORT ───  │
  4  │  SUPPORT ───  │   SWING ███   │
  5  │   SWING ███   │  SUPPORT ───  │
  6  │  SUPPORT ───  │   SWING ███   │
```

**Wave gait** (slowest, max stability):

```
Leg  │ Φ0  │ Φ1  │ Φ2  │ Φ3  │ Φ4  │ Φ5  │
─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  1  │ SWG │ SUP │ SUP │ SUP │ SUP │ SUP │
  2  │ SUP │ SWG │ SUP │ SUP │ SUP │ SUP │
  3  │ SUP │ SUP │ SWG │ SUP │ SUP │ SUP │
  4  │ SUP │ SUP │ SUP │ SWG │ SUP │ SUP │
  5  │ SUP │ SUP │ SUP │ SUP │ SWG │ SUP │
  6  │ SUP │ SUP │ SUP │ SUP │ SUP │ SWG │
```

**Ripple gait** (medium, pairs):

```
Leg  │ Phase 0 (33%) │ Phase 1 (33%) │ Phase 2 (33%) │
─────┼───────────────┼───────────────┼───────────────┤
 1,4 │   SWING ███   │  SUPPORT ───  │  SUPPORT ───  │
 2,5 │  SUPPORT ───  │   SWING ███   │  SUPPORT ───  │
 3,6 │  SUPPORT ───  │  SUPPORT ───  │   SWING ███   │
```

### 6.3 — Turning

Turning is achieved by varying stride length per side:

- **Spin in place** (`TURN_RADIUS_MM=0`): left legs stride forward, right legs stride backward (or vice versa).
- **Arc turn**: inner legs use shorter stride, outer legs use longer stride. Ratio = `(R ± body_width/2) / R` where `R = TURN_RADIUS_MM`.
- **Heading change**: autonomous navigation adjusts `TURN_RADIUS_MM` based on obstacle sensor readings.

---

## 7 · High-level architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           SPIDER-BOT HEXAPOD TERRAIN ADAPTATION                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  GAIT ENGINE                             │  │
│  │  State machine: tripod/wave/ripple/free                  │  │
│  │  → per-leg foot targets each cycle step                  │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                 KINEMATICS                               │  │
│  │  Body IK (translate/rotate body) + Per-leg IK (3-DOF)    │  │
│  │  → 18 joint angles for coxa/femur/tibia per leg          │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                 HARDWARE CONTROL                         │  │
│  │  PCA9685 ×2 (18 servos + 2 pan/tilt) │ Camera │ GPIO    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 SENSOR FUSION                            │  │
│  │  MPU6050 (IMU) │ FSR ×6 (terrain) │ HC-SR04 ×3 (nav)   │  │
│  │  INA219 (battery) │ Pi Camera (FPV)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 STABILIZATION                            │  │
│  │  IMU → complementary filter → PID (pitch/roll)          │  │
│  │  → body IK correction → level body on uneven terrain    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 WEB DASHBOARD                            │  │
│  │  Flask + SocketIO │ Three.js 3D │ Gait │ FPV │ Battery  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8 · Security / Threat model

| # | Threat | Mitigation |
|---|---|---|
| T1 | Credential exposure | `.env` in `.gitignore`, `chmod 600` |
| T2 | Brute-force login | Rate limiting: 10/15 min |
| T3 | Session hijacking | Strong `SESSION_SECRET`, HttpOnly, SameSite cookies |
| T4 | XSS | Jinja2 auto-escaping |
| T5 | SQL injection | Parameterized queries (sqlite3 placeholders) |
| T6 | Unauthorized robot control | All endpoints require auth |
| T7 | Physical harm from legs | Joint limits, speed limits, e-stop on dashboard |
| T8 | I2C bus spoofing | Physical security only — document in threat model |
| T9 | Camera feed interception | Local network only, HTTPS via nginx reverse proxy |
| T10 | LiPo battery fire | INA219 auto-cutoff at critical voltage, BEC fuse |
| T11 | Servo runaway / stall | Current monitoring, auto-disable stalled servos |
| T12 | Unauthorized firmware update | Deploy via SSH key auth only |

---

## 9 · Suggested tech stack

### Backend

| Component | Technology | Justification |
|---|---|---|
| Language | Python 3.11+ | Best robotics/sensor ecosystem |
| Web framework | Flask 3.1 + SocketIO | Lightweight, real-time capable |
| Servo control | adafruit-circuitpython-pca9685 + servokit | I2C servo driver |
| IMU | adafruit-circuitpython-mpu6050 | Accelerometer + gyroscope |
| Battery monitor | adafruit-circuitpython-ina219 | Voltage/current sensing |
| ADC (FSR) | spidev + MCP3008 | SPI analog-to-digital |
| Computer vision | OpenCV 4.10 (headless) | Camera capture, MJPEG stream |
| Math | numpy | Matrix operations, IK, PID |
| Database | SQLite | Zero-config file-based |
| GPIO | RPi.GPIO | Ultrasonic sensors, LEDs |
| Auth | bcrypt + Flask sessions | Password hashing + rate limiting |
| I2C fallback | smbus2 | Raw I2C communication |

### Frontend

| Component | Technology |
|---|---|
| Templates | Jinja2 |
| Real-time | Socket.IO client (CDN) |
| 3D visualization | Three.js (CDN) |
| Controls | HTML5 range inputs + virtual joystick JS |
| Styling | Custom CSS (dark theme) |

---

## 10 · Development phases

### Phase 1 — Servo control and leg IK

| # | Task | Priority |
|---|---|---|
| 1.1 | Project scaffolding (Flask app, .env, DB) | P0 |
| 1.2 | Dual PCA9685 servo driver module | P0 |
| 1.3 | Leg geometry loader and per-leg 3-DOF IK | P0 |
| 1.4 | Body-level IK (translate/rotate body) | P0 |
| 1.5 | Home position and manual joint control | P0 |
| 1.6 | Mock hardware mode | P0 |
| 1.7 | Unit tests (leg IK, body IK) | P1 |

### Phase 2 — Gait engine

| # | Task | Priority |
|---|---|---|
| 2.1 | Gait state machine framework | P0 |
| 2.2 | Tripod gait implementation | P0 |
| 2.3 | Wave gait implementation | P0 |
| 2.4 | Ripple gait implementation | P0 |
| 2.5 | Turning (spin + arc) | P0 |
| 2.6 | Speed control | P0 |
| 2.7 | Unit tests (gait state machine) | P1 |

### Phase 3 — Sensors and stabilization

| # | Task | Priority |
|---|---|---|
| 3.1 | MPU6050 IMU driver + complementary filter | P0 |
| 3.2 | PID controller | P0 |
| 3.3 | Body leveling (IMU → PID → body IK) | P0 |
| 3.4 | FSR reading via MCP3008 SPI | P0 |
| 3.5 | Terrain-adaptive leg extension | P0 |
| 3.6 | INA219 battery monitoring | P0 |
| 3.7 | HC-SR04 ultrasonic distance | P0 |
| 3.8 | Unit tests (PID, sensor mocks) | P1 |

### Phase 4 — Navigation and camera

| # | Task | Priority |
|---|---|---|
| 4.1 | Camera capture + MJPEG stream | P0 |
| 4.2 | Pan/tilt servo control | P0 |
| 4.3 | Obstacle avoidance algorithm | P1 |
| 4.4 | Wall-following algorithm | P1 |
| 4.5 | Return-home (dead reckoning) | P2 |
| 4.6 | Low-battery auto-return trigger | P1 |

### Phase 5 — Web dashboard

| # | Task | Priority |
|---|---|---|
| 5.1 | Flask app + auth + layout (dark theme) | P0 |
| 5.2 | Three.js 3D hexapod visualization | P0 |
| 5.3 | Gait pattern selector + speed control | P0 |
| 5.4 | Body translation/rotation controls | P0 |
| 5.5 | FPV camera feed + pan/tilt controls | P0 |
| 5.6 | Battery and sensor status panels | P0 |
| 5.7 | Gait recording/replay UI | P1 |
| 5.8 | Navigation mode controls | P1 |
| 5.9 | Settings page (PID tuning, servo cal) | P1 |
| 5.10 | System status (CPU temp, uptime) | P1 |

### Phase 6 — Advanced features and deployment

| # | Task | Priority |
|---|---|---|
| 6.1 | Gait recording engine | P1 |
| 6.2 | Modular leg configuration (4/6/8) | P2 |
| 6.3 | Per-leg current monitoring | P2 |
| 6.4 | Deploy script (rsync) | P0 |
| 6.5 | systemd service | P1 |
| 6.6 | Threat model document | P1 |
| 6.7 | End-to-end testing | P1 |
| 6.8 | README finalization | P0 |

---

## 11 · Performance expectations

| Metric | Pi 4 (4 GB) | Pi 5 (8 GB) |
|---|---|---|
| Gait cycle (6-leg IK solve) | ~2 ms | ~1 ms |
| Per-leg IK (3-DOF analytical) | <0.1 ms | <0.1 ms |
| Body IK + all legs | ~1 ms | ~0.5 ms |
| IMU read + filter | ~0.5 ms | ~0.3 ms |
| PID compute | <0.1 ms | <0.1 ms |
| FSR read (6 channels SPI) | ~1 ms | ~0.5 ms |
| Ultrasonic read (3 sensors) | ~60 ms (serial) | ~60 ms (serial) |
| Camera capture (640×480) | ~30 FPS | ~30 FPS |
| Servo update rate | 50 Hz (PCA9685) | 50 Hz (PCA9685) |
| Three.js render (browser) | 60 FPS | 60 FPS |
| SocketIO latency | ~20 ms | ~10 ms |
| Full control loop | ~50 Hz | ~100 Hz |

---

## 12 · Deliverables

| # | Deliverable | Phase |
|---|---|---|
| D1 | Dual PCA9685 servo control + per-leg IK + body IK + mock mode | Phase 1 |
| D2 | Gait engine (tripod/wave/ripple) + turning + speed control | Phase 2 |
| D3 | IMU stabilization + FSR terrain adaptation + battery monitoring | Phase 3 |
| D4 | FPV camera + autonomous navigation + obstacle avoidance | Phase 4 |
| D5 | Web dashboard with Three.js 3D + gait control + FPV + battery | Phase 5 |
| D6 | Gait recording, modular config, deployment, documentation | Phase 6 |
