# TSD — 🤝 Haptic Feedback Shadow Arm

## 1 · Scope

Build a master-slave teleoperation arm system on Raspberry Pi. A Master Arm (potentiometers/rotary encoders via ADS1115 ADC) mirrors its position to a Slave Arm (servos via PCA9685) in real-time at ~50 Hz. INA219 current sensors on slave servos measure motor load and drive proportional haptic vibration motors (DRV2605L) on the master arm for force feedback. Includes a Flask + SocketIO dark-themed web dashboard with real-time 3D visualization (Three.js), force scaling controls, recording/playback, precision mode, gripper mirroring, collision detection, and joint auto-calibration. All features `.env` toggleable.

### In scope

| Area | Details |
|---|---|
| **Master → slave mirroring** | Potentiometers/encoders → ADS1115 → angle mapping → PCA9685 → servos at ~50 Hz |
| **Force feedback** | INA219 current sensing on slave servos → DRV2605L haptic vibration on master |
| **Force scaling** | Dashboard-adjustable multiplier/dampening (0.1×–5.0×) |
| **Network teleoperation** | LAN/WAN via SocketIO with predictive buffering for latency compensation |
| **Recording & playback** | Timestamped joint angles + gripper state → save/replay/loop |
| **Speed limiting** | Per-joint max angular velocity (degrees/sec), slave caps tracking speed |
| **Workspace visualization** | Three.js 3D arm model on dashboard, real-time joint + force rendering |
| **Precision mode** | Reduced motion ratio (configurable, default 10:1) for fine manipulation |
| **Gripper mirroring** | FSR analog on master → ADS1115 → slave gripper servo proportional |
| **Collision detection** | FK-based end-effector position → virtual workspace boundaries → e-stop |
| **Joint calibration** | Auto-calibration on startup: sweep pots → detect min/max ADC → angle map |
| **Forward kinematics** | DH parameter-based FK for end-effector position + collision checking |
| **Web dashboard** | Flask + SocketIO: 3D viz, force graph, recording UI, settings, e-stop |
| **Authentication** | bcrypt session auth, rate limiting (10/15min), 24h sessions |
| **Mock mode** | Simulated ADC + servos + current sensors + haptics for laptop development |
| **Deployment** | rsync to `rasp-pi` (192.168.216.90), systemd service |

### Out of scope

| Area | Reason |
|---|---|
| Dynamixel smart servos | Built-in torque feedback would simplify design; documented as upgrade path |
| ROS 2 integration | Adds complexity; documented as upgrade path only |
| Computer vision / object detection | This project is teleoperation-focused, not autonomous manipulation |
| Custom PCB design | Off-the-shelf breakout boards (PCA9685, ADS1115, INA219, DRV2605L) used |
| VR headset integration | Documented as future enhancement |
| Multi-arm coordination | Single master-slave pair only |
| Mobile app | Web dashboard only |

---

## 2 · MVP features

### 2.1 — ADS1115 ADC master arm input

**Priority: P0**

- Initialize 2× ADS1115 at I2C addresses 0x48 and 0x49.
- Read 6 potentiometer channels at ~100 SPS per channel (continuous mode).
- Apply per-joint calibration: raw ADC value → angle (0°–180°).
- Exponential moving average filter to reduce noise (configurable alpha).
- Support both potentiometers (absolute) and rotary encoders (incremental).
- Mock mode: generate smooth sinusoidal angle patterns.

### 2.2 — PCA9685 slave arm servo control

**Priority: P0**

- Initialize PCA9685 via I2C at configured address (default 0x40).
- Set PWM frequency (default 50 Hz for standard servos).
- Map angle (0°–180°) to pulse width (500–2500 µs) per channel.
- Support per-servo min/max pulse calibration via `.env`.
- Home position command: move all joints to configured home angles.
- Mock mode: log servo commands without hardware.

### 2.3 — Mirror engine (main control loop)

**Priority: P0**

- Runs at ~50 Hz in a background thread.
- Each tick:
  1. Read all master joint angles from ADS1115.
  2. Apply speed limiting (cap delta per tick).
  3. Apply precision mode scaling if active.
  4. Check collision boundaries (FK → workspace bounds).
  5. Write target angles to PCA9685 slave servos.
  6. Read INA219 current on slave servos.
  7. Map current to vibration intensity → DRV2605L.
  8. Broadcast state to dashboard via SocketIO.
- Thread-safe state sharing between mirror engine and Flask routes.

### 2.4 — Forward kinematics (DH parameters)

**Priority: P0**

- Load DH parameter table from `config/dh_params.json`.
- Compute end-effector pose (4×4 homogeneous transform) from joint angles.
- Support 4-DOF and 6-DOF configurations.
- Used for collision detection (end-effector position) and 3D visualization.

### 2.5 — Force feedback (INA219 → DRV2605L)

**Priority: P1**

- Read current (mA) from 4–6 INA219 sensors on slave servo power lines.
- Idle current baseline: `FORCE_IDLE_MA` (typically 50–150 mA for unloaded servo).
- Excess current above idle = proportional to mechanical load.
- Map `[FORCE_IDLE_MA, FORCE_MAX_MA]` → `[0, 255]` vibration intensity.
- Drive DRV2605L haptic motors with scaled intensity.
- Per-joint force → per-motor vibration (closest master joint gets feedback).

### 2.6 — Web dashboard

**Priority: P0**

**Database schema:**

**Table: `mirror_log`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | Log time |
| `master_angles` | TEXT | JSON array of master joint angles |
| `slave_angles` | TEXT | JSON array of slave angles sent |
| `currents_ma` | TEXT | JSON array of INA219 current readings (mA) |
| `force_feedback` | TEXT | JSON array of vibration intensities sent |
| `precision_mode` | INTEGER | 1 = precision mode active |
| `latency_ms` | REAL | Mirror loop latency (ms) |

**Table: `recordings`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT UNIQUE | Recording name |
| `created_at` | DATETIME | Creation time |
| `duration_ms` | INTEGER | Total recording duration |
| `frame_count` | INTEGER | Number of recorded frames |
| `file_path` | TEXT | Path to JSON recording file |
| `speed_scale` | REAL | Default replay speed (0.1–5.0) |
| `loop` | INTEGER | 1 = loop, 0 = single run |

**Table: `calibration_data`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | DATETIME | Calibration time |
| `joint` | INTEGER | Joint number (1–6) |
| `adc_min` | INTEGER | Minimum ADC value at joint limit |
| `adc_max` | INTEGER | Maximum ADC value at joint limit |
| `angle_min` | REAL | Minimum angle (degrees) |
| `angle_max` | REAL | Maximum angle (degrees) |
| `adc_address` | TEXT | ADS1115 I2C address (0x48 or 0x49) |
| `adc_channel` | INTEGER | ADS1115 channel (0–3) |

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

### 2.8 — Safety manager

**Priority: P0**

- Joint angle limits enforced before every servo command.
- Workspace bounds: FK end-effector position must stay within defined volume.
- Speed limits: max angular velocity per joint (degrees/sec).
- Emergency stop: GPIO interrupt (physical button) + web button → immediately disable all PCA9685 channels.
- Resume requires explicit unlock command (web or GPIO reset).

### 2.9 — Mock hardware

**Priority: P0**

- Simulated ADS1115 (generated smooth pot values, configurable patterns).
- Simulated PCA9685 (log commands, track virtual joint angles).
- Simulated INA219 (return configurable current values based on angle delta).
- Simulated DRV2605L (log vibration intensity to console).
- Virtual GPIO (log e-stop, LEDs to console).
- All dashboard features work identically.

### 2.10 — Deploy script

**Priority: P0**

- `deploy/deploy_to_pi.sh`: rsync + venv + pip install.
- systemd service unit documented in README.

---

## 3 · Nice-to-have features

### 3.1 — Force scaling

**Requires:** Force feedback enabled.

- Dashboard slider: force multiplier from 0.1× to 5.0×.
- Amplify mode: detect light contacts during delicate tasks.
- Dampen mode: reduce operator fatigue during heavy-load tasks.
- Toggle: `ENABLE_FORCE_SCALING=true`.

### 3.2 — Network teleoperation

**Requires:** SocketIO network stack.

- Master Pi sends joint angles over SocketIO to remote slave Pi.
- Predictive buffering: client-side extrapolation during latency spikes.
- Round-trip latency displayed on dashboard.
- Toggle: `ENABLE_NETWORK_TELEOPERATION=true`.

### 3.3 — Recording & playback

**Requires:** Web dashboard.

- Record timestamped frames: `{t_ms, joints: [...], gripper: float}`.
- Save/load named recordings as JSON.
- Replay at configurable speed (0.1×–5.0×).
- Loop mode for training demos.
- Toggle: `ENABLE_RECORDING_PLAYBACK=true`.

### 3.4 — Speed limiting

**Requires:** Mirror engine.

- Per-joint max angular velocity (degrees/sec).
- Slave tracks at capped speed, catches up smoothly when master stabilizes.
- Toggle: `ENABLE_SPEED_LIMITING=true`.

### 3.5 — Workspace visualization (Three.js)

**Requires:** Web dashboard + FK solver.

- Real-time 3D rendering of master and slave arms.
- Joint segments colored by force feedback intensity.
- Workspace boundary volumes shown as translucent boxes/cylinders.
- End-effector trace path (optional).
- Toggle: `ENABLE_WORKSPACE_VISUALIZATION=true`.

### 3.6 — Precision mode

**Requires:** Mirror engine.

- Motion ratio reduction: master 10° → slave 1° (configurable `PRECISION_RATIO`).
- Toggled from dashboard or physical button.
- Speed limits auto-tighten in precision mode.
- Toggle: `ENABLE_PRECISION_MODE=true`.

### 3.7 — Gripper mirroring

**Requires:** FSR on master + gripper servo on slave.

- FSR analog → ADS1115 → squeeze force (0–1023 range).
- Map squeeze to gripper servo angle (fully open → fully closed).
- Proportional control: partial squeeze = partial close.
- Toggle: `ENABLE_GRIPPER_MIRRORING=true`.

### 3.8 — Collision detection

**Requires:** FK solver + workspace bounds config.

- FK computes end-effector (x, y, z) for each command.
- Workspace bounds loaded from `config/workspace_bounds.json`.
- Warning threshold: dashboard alert when approaching boundary.
- Hard limit: emergency stop if boundary exceeded.
- Toggle: `ENABLE_COLLISION_DETECTION=true`.

### 3.9 — Joint calibration

**Requires:** ADS1115 + master arm potentiometers.

- Auto-calibration routine: prompt operator to sweep each joint through full range.
- Record ADC min/max at mechanical limits.
- Detect plateau in ADC values = end of physical travel.
- Save to `config/calibration.json` and database.
- Recalibrate from dashboard Settings page.
- Toggle: `ENABLE_JOINT_CALIBRATION=true`.

---

## 4 · Environment configuration (.env.default)

```ini
###############################################################################
# HAPTIC FEEDBACK SHADOW ARM — ENVIRONMENT CONFIGURATION
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

# DH parameters file
DH_PARAMS_PATH=./config/dh_params.json

# Home position (degrees, comma-separated per joint)
HOME_POSITION=90,90,90,90,90,90

# ─── ADS1115 ADC (Master Arm Potentiometers) ───────────────────
ADS1115_1_ADDRESS=0x48
ADS1115_2_ADDRESS=0x49
ADC_SAMPLE_RATE=128
ADC_GAIN=1
ADC_FILTER_ALPHA=0.3

# Per-joint ADC channel mapping: adc_board,channel
# Board 1 = 0x48, Board 2 = 0x49
ADC_J1_CHANNEL=1,0
ADC_J2_CHANNEL=1,1
ADC_J3_CHANNEL=1,2
ADC_J4_CHANNEL=1,3
ADC_J5_CHANNEL=2,0
ADC_J6_CHANNEL=2,1
ADC_GRIPPER_CHANNEL=2,2

# ─── PCA9685 Servo Driver (Slave Arm) ──────────────────────────
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

# ─── INA219 Current Sensors (Slave Servo Force Sensing) ────────
INA219_J1_ADDRESS=0x40
INA219_J2_ADDRESS=0x41
INA219_J3_ADDRESS=0x44
INA219_J4_ADDRESS=0x45

# Current thresholds (mA) for force feedback mapping
# Idle = no-load current (no vibration), Max = full vibration
FORCE_IDLE_MA=100
FORCE_MAX_MA=800

# ─── DRV2605L Haptic Driver (Master Vibration Motors) ──────────
DRV2605L_ADDRESS=0x5A
HAPTIC_MODE=ERM

# For multiple DRV2605L boards, use TCA9548A multiplexer:
# TCA9548A_ADDRESS=0x70
# HAPTIC_MUX_CHANNELS=0,1,2,3

# ─── Feature Toggles ───────────────────────────────────────────
ENABLE_FORCE_FEEDBACK=true
ENABLE_FORCE_SCALING=true
ENABLE_NETWORK_TELEOPERATION=false
ENABLE_RECORDING_PLAYBACK=true
ENABLE_SPEED_LIMITING=true
ENABLE_WORKSPACE_VISUALIZATION=true
ENABLE_PRECISION_MODE=true
ENABLE_GRIPPER_MIRRORING=true
ENABLE_COLLISION_DETECTION=true
ENABLE_JOINT_CALIBRATION=true

# ─── Force Scaling ──────────────────────────────────────────────
FORCE_SCALE_DEFAULT=1.0
FORCE_SCALE_MIN=0.1
FORCE_SCALE_MAX=5.0

# ─── Network Teleoperation ─────────────────────────────────────
TELEOP_SERVER_HOST=0.0.0.0
TELEOP_SERVER_PORT=5001
TELEOP_BUFFER_SIZE=5
TELEOP_PREDICTION_ENABLED=true

# ─── Recording & Playback ──────────────────────────────────────
RECORDING_DIR=./config/recordings
RECORDING_FPS=50
PLAYBACK_SPEED_DEFAULT=1.0

# ─── Speed Limiting ────────────────────────────────────────────
# Max angular velocity per joint (degrees/sec)
MAX_JOINT_VELOCITY_J1=120
MAX_JOINT_VELOCITY_J2=90
MAX_JOINT_VELOCITY_J3=90
MAX_JOINT_VELOCITY_J4=180
MAX_JOINT_VELOCITY_J5=180
MAX_JOINT_VELOCITY_J6=180

# ─── Precision Mode ────────────────────────────────────────────
PRECISION_RATIO=10
PRECISION_SPEED_FACTOR=0.5

# ─── Gripper ───────────────────────────────────────────────────
GRIPPER_OPEN_ANGLE=90
GRIPPER_CLOSE_ANGLE=10
FSR_MIN_ADC=200
FSR_MAX_ADC=30000

# ─── Collision Detection ───────────────────────────────────────
WORKSPACE_BOUNDS_PATH=./config/workspace_bounds.json
COLLISION_WARNING_MARGIN_MM=20
COLLISION_ESTOP_ENABLED=true

# ─── Joint Calibration ─────────────────────────────────────────
CALIBRATION_FILE=./config/calibration.json
CALIBRATION_ON_STARTUP=false
CALIBRATION_SWEEP_SPEED=30

# ─── Safety ─────────────────────────────────────────────────────
ESTOP_GPIO=4
LED_RUNNING_GPIO=22
LED_ERROR_GPIO=23

# ─── Mirror Engine ──────────────────────────────────────────────
MIRROR_LOOP_HZ=50

# ─── Web Dashboard ──────────────────────────────────────────────
ENABLE_WEB_DASHBOARD=true
SOCKETIO_UPDATE_RATE=10
STREAM_JPEG_QUALITY=50

# ─── Mock Hardware ──────────────────────────────────────────────
ENABLE_MOCK_HARDWARE=false

# ─── Deployment ─────────────────────────────────────────────────
DEPLOY_HOST=rasp-pi
DEPLOY_PATH=/home/pi/Projects/ShadowArm
```

---

## 5 · Forward Kinematics (DH Parameters)

The DH parameter table defines the kinematic chain for both master and slave arms (assumed mechanically identical kits).

### DH Convention (Modified DH)

Each row: `[alpha_i-1, a_i-1, d_i, theta_offset_i]`

- `alpha` — twist angle about X (radians)
- `a` — link length along X (mm)
- `d` — link offset along Z (mm)
- `theta_offset` — joint angle offset (radians, added to commanded angle)

### `config/dh_params.json`

```json
{
  "description": "4-6 DOF hobby servo arm DH parameters (Modified DH convention)",
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

> **Note:** Measure your specific arm's link lengths with calipers. Values above are typical for a generic hobby servo arm. Both arms must be mechanically identical for accurate mirroring.

### FK Computation

The homogeneous transformation for each joint:

$$T_i = \begin{bmatrix} \cos\theta_i & -\sin\theta_i\cos\alpha_i & \sin\theta_i\sin\alpha_i & a_i\cos\theta_i \\ \sin\theta_i & \cos\theta_i\cos\alpha_i & -\cos\theta_i\sin\alpha_i & a_i\sin\theta_i \\ 0 & \sin\alpha_i & \cos\alpha_i & d_i \\ 0 & 0 & 0 & 1 \end{bmatrix}$$

End-effector pose:

$$T_{0 \to n} = T_1 \cdot T_2 \cdot T_3 \cdots T_n$$

For collision detection, extract the translation vector (x, y, z) from the final 4×4 matrix to get end-effector world position.

### 4-DOF Simplification

For 4-DOF arms, use joints 1–4 and set `ARM_DOF=4`. The analytical IK solver uses geometric decomposition:
1. $J_1 = \text{atan2}(y, x)$
2. $r = \sqrt{x^2 + y^2}, \quad z_{\text{eff}} = z - d_1$
3. $\cos(J_3) = \frac{r^2 + z_{\text{eff}}^2 - a_2^2 - a_3^2}{2 \cdot a_2 \cdot a_3}$
4. $J_3 = \text{atan2}(\pm\sin(J_3), \cos(J_3))$ — elbow-up / elbow-down
5. $J_2 = \text{atan2}(z_{\text{eff}}, r) - \text{atan2}(a_3\sin(J_3), a_2 + a_3\cos(J_3))$
6. $J_4 = \text{pitch}_{\text{desired}} - (J_2 + J_3)$

---

## 6 · Master-Slave Communication Protocol

### Local Mode (Single Pi)

All I2C on one Raspberry Pi. The mirror engine runs as a Python thread:

```
Mirror Engine Thread (~50 Hz loop):
┌─────────────────────────────────────────────────────────────┐
│ 1. READ MASTER                                               │
│    ADS1115 #1 (0x48): read A0–A3 → J1–J4 raw ADC           │
│    ADS1115 #2 (0x49): read A0–A1 → J5–J6 raw ADC           │
│    ADS1115 #2 (0x49): read A2    → FSR gripper              │
│                                                              │
│ 2. CALIBRATION MAP                                           │
│    raw_adc → angle = (raw - adc_min) / (adc_max - adc_min)  │
│                       × (angle_max - angle_min) + angle_min  │
│    Apply EMA filter: filtered = α × new + (1-α) × prev      │
│                                                              │
│ 3. SPEED LIMITING (if ENABLE_SPEED_LIMITING)                 │
│    delta = target - current                                  │
│    max_delta = MAX_VELOCITY × dt                             │
│    if |delta| > max_delta: target = current + sign(delta)    │
│                            × max_delta                       │
│                                                              │
│ 4. PRECISION MODE (if ENABLE_PRECISION_MODE and active)      │
│    target = home + (target - home) / PRECISION_RATIO         │
│                                                              │
│ 5. COLLISION CHECK (if ENABLE_COLLISION_DETECTION)            │
│    FK(target_angles) → (x, y, z)                             │
│    Check against workspace_bounds.json                       │
│    If outside bounds → block command, trigger e-stop if hard │
│                                                              │
│ 6. WRITE SLAVE                                               │
│    PCA9685 (0x40): set channels 0–5 → J1–J6 pulse widths    │
│    PCA9685 (0x40): set channel 6   → gripper (from FSR map) │
│                                                              │
│ 7. READ FORCE (if ENABLE_FORCE_FEEDBACK)                     │
│    INA219 ×4: read current_mA per servo                      │
│    excess = current_mA - FORCE_IDLE_MA                       │
│    intensity = clamp(excess / (FORCE_MAX_MA - FORCE_IDLE_MA) │
│                × 255 × force_scale, 0, 255)                  │
│                                                              │
│ 8. WRITE HAPTIC (if ENABLE_FORCE_FEEDBACK)                   │
│    DRV2605L (0x5A): set vibration intensity per motor        │
│                                                              │
│ 9. BROADCAST STATE                                           │
│    SocketIO emit: {master_angles, slave_angles, currents,    │
│                    force_intensities, precision_active,       │
│                    collision_warning, latency_ms}             │
└─────────────────────────────────────────────────────────────┘
```

### Network Mode (ENABLE_NETWORK_TELEOPERATION=true)

Master Pi and Slave Pi communicate over SocketIO:

```
MASTER PI                              SLAVE PI
┌──────────────┐    SocketIO     ┌──────────────────────┐
│ ADS1115      │                 │ PCA9685 → servos     │
│ → read pots  │──joint_state──►│ → drive slave arm     │
│              │   {angles[],   │                        │
│              │    gripper,    │ INA219 → currents      │
│              │    t_ms}       │                        │
│ DRV2605L     │◄──force_data──│ → read servo load     │
│ → vibrate    │   {currents[], │                        │
│              │    t_ms}       │                        │
└──────────────┘                 └──────────────────────┘

Latency compensation (predictive buffering):
  - Master sends timestamped joint state packets at MIRROR_LOOP_HZ
  - Slave buffers last TELEOP_BUFFER_SIZE packets
  - On network stall (no packet for >2 ticks):
    Slave extrapolates from velocity of last N packets
    (linear prediction: angle += velocity × dt)
  - When packets resume, slave smoothly blends back to live data
  - Dashboard displays round-trip latency
```

### Recording Format

```json
{
  "name": "demo_pick_sequence",
  "created_at": "2025-01-15T14:30:00Z",
  "fps": 50,
  "frames": [
    {
      "t_ms": 0,
      "master_angles": [90.0, 45.0, 120.0, 90.0, 90.0, 90.0],
      "gripper": 0.0,
      "force_intensities": [0, 0, 12, 0]
    },
    {
      "t_ms": 20,
      "master_angles": [90.5, 44.8, 120.2, 90.1, 90.0, 90.0],
      "gripper": 0.0,
      "force_intensities": [0, 0, 15, 0]
    }
  ]
}
```

---

## 7 · High-level architecture

```
┌─────────────────────────────────────────────────────────────────┐
│             HAPTIC FEEDBACK SHADOW ARM                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  MASTER ARM INPUT                        │  │
│  │  Potentiometers → ADS1115 ADC → calibration → angles    │  │
│  │  FSR (gripper) → ADS1115 → squeeze force                │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                 MIRROR ENGINE (~50 Hz)                    │  │
│  │  Speed limit → Precision scale → Collision check         │  │
│  │  → PCA9685 servo write → INA219 force read               │  │
│  │  → DRV2605L haptic write → SocketIO broadcast            │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                 SLAVE ARM OUTPUT                          │  │
│  │  PCA9685 servo driver │ INA219 current sensors           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 WEB DASHBOARD                            │  │
│  │  Flask + SocketIO │ Three.js 3D │ Force graph │ Record  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 SAFETY MANAGER                           │  │
│  │  Joint limits │ Workspace bounds │ E-stop │ Speed limits │  │
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
| T6 | Unauthorized arm control | All endpoints require auth |
| T7 | Physical harm from arm | Speed limits, workspace bounds, e-stop GPIO, collision detection |
| T8 | I2C bus spoofing | Physical security only — document in threat model |
| T9 | Network teleop interception | SocketIO over VPN/SSH tunnel for WAN; HTTPS via nginx for LAN |
| T10 | Servo runaway | Watchdog: if no master update for 500 ms → hold position; if 2 s → park and disable |
| T11 | Force feedback amplification attack | Clamp vibration intensity to hardware-safe max regardless of software scaling |
| T12 | Replay attack on teleop channel | Timestamped packets + sequence numbers, reject stale data |

---

## 9 · Suggested tech stack

### Backend

| Component | Technology | Justification |
|---|---|---|
| Language | Python 3.11+ | Best I2C/sensor/robotics ecosystem |
| Web framework | Flask 3.1 + SocketIO | Lightweight, real-time capable |
| ADC input | adafruit-circuitpython-ads1x15 | ADS1115 16-bit ADC driver |
| Servo output | adafruit-circuitpython-pca9685 + servokit | I2C PWM servo driver |
| Current sensing | adafruit-circuitpython-ina219 | Motor current measurement |
| Haptic output | smbus2 (DRV2605L) | Low-level I2C haptic driver |
| Math | numpy | Matrix operations, DH transforms, filtering |
| Database | SQLite | Zero-config file-based |
| GPIO | RPi.GPIO | E-stop, LEDs, status |
| Auth | bcrypt + Flask sessions | Password hashing + rate limiting |

### Frontend

| Component | Technology |
|---|---|
| Templates | Jinja2 |
| Real-time | Socket.IO client (CDN) |
| 3D visualization | Three.js (CDN) |
| Force graph | Chart.js or canvas-based |
| Styling | Custom CSS (dark theme) |

---

## 10 · Development phases

### Phase 1 — ADS1115 input + PCA9685 output + basic mirroring

| # | Task | Priority |
|---|---|---|
| 1.1 | Project scaffolding (Flask app, .env, DB) | P0 |
| 1.2 | ADS1115 ADC reader module (2 boards, 6 channels) | P0 |
| 1.3 | PCA9685 servo driver module | P0 |
| 1.4 | Mirror engine: read master → write slave (50 Hz loop) | P0 |
| 1.5 | Joint home position and basic calibration | P0 |
| 1.6 | Mock hardware for dev without physical boards | P0 |

### Phase 2 — FK + safety + calibration

| # | Task | Priority |
|---|---|---|
| 2.1 | DH parameter loader and FK solver | P0 |
| 2.2 | Joint limits enforcement | P0 |
| 2.3 | E-stop GPIO + web e-stop | P0 |
| 2.4 | Auto-calibration routine (sweep + limit detection) | P1 |

### Phase 3 — Force feedback

| # | Task | Priority |
|---|---|---|
| 3.1 | INA219 current sensor reading (4–6 sensors) | P1 |
| 3.2 | DRV2605L haptic driver + vibration motor control | P1 |
| 3.3 | Current → vibration intensity mapping | P1 |
| 3.4 | Force scaling (dashboard slider) | P1 |

### Phase 4 — Web dashboard + Three.js

| # | Task | Priority |
|---|---|---|
| 4.1 | Auth (bcrypt, rate limit, 24h sessions) | P0 |
| 4.2 | Dashboard layout (dark theme) + e-stop | P0 |
| 4.3 | Three.js 3D arm visualization | P1 |
| 4.4 | Force feedback graph panel | P1 |
| 4.5 | Settings page (calibration, precision, collision) | P1 |

### Phase 5 — Advanced features

| # | Task | Priority |
|---|---|---|
| 5.1 | Speed limiting (per-joint max velocity) | P1 |
| 5.2 | Precision mode (10:1 ratio) | P1 |
| 5.3 | Gripper mirroring (FSR → servo) | P1 |
| 5.4 | Collision detection (FK → workspace bounds) | P1 |
| 5.5 | Recording & playback | P2 |
| 5.6 | Network teleoperation (SocketIO LAN/WAN) | P2 |

### Phase 6 — Deployment + testing

| # | Task | Priority |
|---|---|---|
| 6.1 | Deploy script (rsync) | P0 |
| 6.2 | systemd service | P0 |
| 6.3 | Full integration testing | P0 |
| 6.4 | Threat model documentation | P1 |
