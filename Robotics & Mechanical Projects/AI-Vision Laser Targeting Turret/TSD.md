# TSD — AI-Vision Laser Targeting Turret

## 1 · Scope

Build a computer-vision-guided laser targeting turret on Raspberry Pi. A 2/3-axis pan-tilt gimbal with SG90 servos aims a 5 mW laser module at detected targets. The Pi Camera detects targets by color (HSV), face (Haar/DNN), trained object, or motion (background subtraction). A PID control loop converts pixel error to servo corrections, keeping the laser centered on moving targets. Includes a Flask + SocketIO dark-themed web dashboard with live PID tuning, multi-target prioritization, safety zones, session recording, and day/night mode switching.

### In scope

| Area | Details |
|---|---|
| **PID controller** | Tunable P/I/D per axis from dashboard, step-response visualization |
| **Multi-target mode** | Track all visible targets, prioritize by class/size/proximity |
| **Predictive aim** | Velocity-based lead angle computation for fast-moving targets |
| **Safety zones** | No-fire pixel regions drawn on camera feed, laser cut in zone |
| **Day/night mode** | Auto-switch visible laser (day) ↔ IR laser + NoIR camera (night) |
| **Session recording** | Save video + CSV log of tracking sessions |
| **Target lock** | Lock on nearest target, ignore others until lost/unlocked |
| **Range estimation** | Known object size → distance via focal-length calculation |
| **Sound deterrent** | Piezo buzzer instead of/with laser for non-harmful deterrent |
| **Web dashboard** | Flask + SocketIO: live camera, PID tuning, safety zones, manual aim |
| **Authentication** | bcrypt session auth, rate limiting (10/15min), 24h sessions |
| **Mock mode** | Simulated servos + laser + GPIO for laptop development |
| **Deployment** | rsync to `rasp-pi` (192.168.216.90), systemd service |

### Out of scope

| Area | Reason |
|---|---|
| High-power laser (Class 3B/4) | Safety — project uses Class 3R (5 mW) only |
| Galvanometer mirror steering | Cost and complexity; documented as upgrade path |
| LIDAR / depth camera ranging | Monocular size-based estimation sufficient for MVP |
| Cloud ML inference | All detection runs locally on-device |
| Mobile app | Web dashboard only |
| Stereo vision | Single camera only; stereo documented as upgrade |
| Multi-turret coordination | Single turret only |
| Weatherproof enclosure | Indoor use only; outdoor documented as upgrade |

---

## 2 · MVP features

### 2.1 — Servo gimbal control (pigpio)

**Priority: P0**

- Initialize pigpio daemon connection.
- Set servo PWM frequency (50 Hz standard).
- Map angle (0°–180°) to pulse width (500–2500 µs) per servo.
- Support per-servo min/max angle and pulse calibration via `.env`.
- Home position command: move pan/tilt to configured center angles.
- Support 2-axis (pan + tilt) and optional 3-axis (+ yaw).
- Mock mode: log servo commands without hardware.

### 2.2 — Laser control

**Priority: P0**

- Visible laser (GPIO 17): HIGH = on, LOW = off.
- Optional IR laser (GPIO 27): separate GPIO, same interface.
- Software kill switch: global flag that overrides all laser-on commands.
- GPIO kill switch: interrupt on GPIO 4 (active LOW) → laser off immediately.
- Laser timeout: auto-off after `LASER_MAX_ON_SEC` continuous seconds.
- Laser state broadcast via SocketIO.

### 2.3 — Camera capture and detection

**Priority: P0**

- Pi Camera capture via OpenCV (640×480 default).
- Detection modes (toggleable via `.env`):
  - **Color:** HSV thresholding → contour → centroid.
  - **Face:** Haar cascade or DNN face detector → bounding box → centroid.
  - **Object:** Haar cascade or TFLite trained detector → class + centroid.
  - **Motion:** Background subtraction (MOG2) → contour → centroid.
- Return: target list of `(class, confidence, centroid_u, centroid_v, bbox)`.
- Frame center is the reference point (laser aim point when servos are at calibrated center).

### 2.4 — Pixel-to-gimbal coordinate mapping

**Priority: P0**

- Calibration: sweep servos across range, map pixel coordinates to servo angles.
- Linear mapping: `pan_angle = pan_center + (u - frame_cx) * px_per_degree_pan`.
- Linear mapping: `tilt_angle = tilt_center + (v - frame_cy) * px_per_degree_tilt`.
- Calibration stored in `.env` (`PX_PER_DEGREE_PAN`, `PX_PER_DEGREE_TILT`).
- Save/load calibration from `scripts/calibrate_gimbal.py`.

### 2.5 — PID control loop

**Priority: P0**

- Separate PID controller for pan and tilt axes.
- Inputs: pixel error (target centroid − frame center).
- Output: servo angle correction (degrees).
- PID formula: `output = Kp*error + Ki*∫error·dt + Kd*(d_error/dt)`.
- Anti-windup: clamp integral term to `PID_I_MAX`.
- Derivative filter: low-pass filter on D term to reduce noise.
- Tunable live from dashboard (sliders update PID gains in real time).
- Loop runs at `TRACKING_FPS` (default 30 Hz).

### 2.6 — Safety manager

**Priority: P0**

- Safety zones: list of rectangular pixel regions where laser must not fire.
- Load zones from `config/safety_zones.json`.
- Before every laser-on: check if target centroid is inside any safety zone.
- If in zone: laser OFF, tracking continues (servos still follow target).
- Kill switch: GPIO interrupt + software flag → immediate laser off.
- Laser timeout: after `LASER_MAX_ON_SEC` continuous on → auto off, require manual re-enable.

### 2.7 — Web dashboard

**Priority: P0**

**Database schema:**

**Table: `tracking_sessions`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `started_at` | DATETIME | Session start time |
| `ended_at` | DATETIME | Session end time |
| `duration_sec` | REAL | Total session duration |
| `detection_mode` | TEXT | Detection mode used |
| `targets_detected` | INTEGER | Total targets detected |
| `laser_on_sec` | REAL | Total laser-on time |
| `video_path` | TEXT | Path to session recording |
| `csv_path` | TEXT | Path to CSV log |

**Table: `tracking_log`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `session_id` | INTEGER FK | References tracking_sessions.id |
| `timestamp` | DATETIME | Frame timestamp |
| `target_u` | INTEGER | Target pixel X |
| `target_v` | INTEGER | Target pixel Y |
| `error_pan` | REAL | Pan pixel error |
| `error_tilt` | REAL | Tilt pixel error |
| `pid_pan_out` | REAL | PID pan output (degrees) |
| `pid_tilt_out` | REAL | PID tilt output (degrees) |
| `servo_pan` | REAL | Servo pan angle (degrees) |
| `servo_tilt` | REAL | Servo tilt angle (degrees) |
| `laser_state` | INTEGER | 1 = on, 0 = off |
| `target_class` | TEXT | Detected class label |
| `confidence` | REAL | Detection confidence |
| `range_mm` | REAL | Estimated range (if enabled) |

**Table: `pid_presets`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT UNIQUE | Preset name |
| `pan_kp` | REAL | Pan proportional gain |
| `pan_ki` | REAL | Pan integral gain |
| `pan_kd` | REAL | Pan derivative gain |
| `tilt_kp` | REAL | Tilt proportional gain |
| `tilt_ki` | REAL | Tilt integral gain |
| `tilt_kd` | REAL | Tilt derivative gain |
| `created_at` | DATETIME | Creation time |

**Table: `safety_zones`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT | Zone name |
| `x_min` | INTEGER | Left pixel boundary |
| `y_min` | INTEGER | Top pixel boundary |
| `x_max` | INTEGER | Right pixel boundary |
| `y_max` | INTEGER | Bottom pixel boundary |
| `enabled` | INTEGER | 1 = active, 0 = disabled |

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

### 2.9 — Mock hardware

**Priority: P0**

- Simulated servos (log commands, track virtual pan/tilt angles).
- Simulated laser (log on/off events to console).
- Simulated camera (sample images with colored circles as targets).
- Virtual GPIO (log kill switch, LEDs, buzzer to console).
- All dashboard features work identically.

### 2.10 — Deploy script

**Priority: P0**

- `deploy/deploy_to_pi.sh`: rsync + venv + pip install.
- systemd service unit documented in README.

---

## 3 · Nice-to-have features

### 3.1 — Multi-target mode

**Requires:** Base detection pipeline.

- Detect all targets in each frame.
- Assign priority score: `weight_class × class_score + weight_size × size_score + weight_proximity × proximity_score`.
- Track highest-priority target; switch when current target lost or on timer.
- Toggle: `ENABLE_MULTI_TARGET=true`.

### 3.2 — Predictive aim

**Requires:** PID controller + multi-frame target history.

- Maintain rolling buffer of target positions (last N frames).
- Compute velocity vector (pixels/frame) via linear regression or Kalman filter.
- Lead angle: `lead_px = velocity × PREDICTION_FRAMES`.
- Add lead offset to PID target point.
- Toggle: `ENABLE_PREDICTIVE_AIM=true`.

### 3.3 — Day/night mode

**Requires:** NoIR camera + IR laser module.

- Compute frame brightness (mean of grayscale frame).
- If brightness < `DAY_NIGHT_THRESHOLD` → switch to night mode:
  - Activate IR laser (GPIO 27), deactivate visible laser (GPIO 17).
  - Switch camera processing to IR-optimized thresholds.
- Manual override from dashboard.
- Toggle: `ENABLE_DAY_NIGHT=true`.

### 3.4 — Session recording

**Requires:** Camera + tracking pipeline.

- On session start: open VideoWriter (MJPEG) + CSV file.
- Each frame: annotate frame (crosshair, bbox, PID info), write to video.
- Each frame: write CSV row (timestamp, target, errors, servo angles, laser state).
- On session stop: close files, create DB entry.
- Toggle: `ENABLE_RECORDING=true`.

### 3.5 — Range estimation

**Requires:** Known target sizes + camera focal length.

- `distance_mm = (known_size_mm × focal_length_px) / apparent_size_px`.
- `focal_length_px` from camera calibration or approximated from camera spec.
- `known_size_mm` per target class from `config/target_classes.json`.
- `apparent_size_px` from bounding box width or height.
- Toggle: `ENABLE_RANGE_ESTIMATION=true`.

### 3.6 — Sound deterrent

**Requires:** Piezo buzzer on GPIO.

- Active buzzer: GPIO HIGH = sound, LOW = off.
- Passive buzzer: pigpio PWM at configurable frequency.
- Modes: buzzer-only, buzzer+laser, pulsed.
- Pulse pattern: on_ms/off_ms configurable.
- Toggle: `ENABLE_SOUND_DETERRENT=true`.

---

## 4 · Environment configuration (.env.default)

```ini
###############################################################################
# AI-VISION LASER TARGETING TURRET — ENVIRONMENT CONFIGURATION
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

# ─── Servo Configuration ───────────────────────────────────────
# Number of axes: 2 (pan+tilt) or 3 (pan+tilt+yaw)
GIMBAL_AXES=2

# Servo GPIO pins (pigpio hardware-timed PWM)
SERVO_PAN_GPIO=12
SERVO_TILT_GPIO=13
SERVO_YAW_GPIO=18

# Servo pulse ranges (µs) — calibrate for your SG90s
SERVO_PAN_PULSE_MIN=500
SERVO_PAN_PULSE_MAX=2500
SERVO_TILT_PULSE_MIN=500
SERVO_TILT_PULSE_MAX=2500
SERVO_YAW_PULSE_MIN=500
SERVO_YAW_PULSE_MAX=2500

# Servo angle limits (degrees)
SERVO_PAN_MIN=0
SERVO_PAN_MAX=180
SERVO_TILT_MIN=0
SERVO_TILT_MAX=180
SERVO_YAW_MIN=0
SERVO_YAW_MAX=180

# Home (center) position (degrees)
SERVO_PAN_HOME=90
SERVO_TILT_HOME=90
SERVO_YAW_HOME=90

# ─── Laser Configuration ───────────────────────────────────────
LASER_VISIBLE_GPIO=17
LASER_IR_GPIO=27

# Laser safety timeout (seconds) — auto-off after continuous on
LASER_MAX_ON_SEC=30

# ─── Camera ─────────────────────────────────────────────────────
ENABLE_CAMERA=true
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=30

# Camera type: standard (has IR filter) or noir (no IR filter)
CAMERA_TYPE=standard

# ─── Detection ──────────────────────────────────────────────────
# Detection mode: color, face, object, motion
DETECTION_MODE=color

# Color detection: HSV ranges (H_min,S_min,V_min,H_max,S_max,V_max)
COLOR_TARGET_1=0,120,70,10,255,255
COLOR_TARGET_2=36,50,70,86,255,255
COLOR_TARGET_3=94,80,50,126,255,255

# Face detection
FACE_CASCADE_PATH=haarcascade_frontalface_default.xml
FACE_MIN_SIZE=30

# Object detection confidence threshold
DETECTION_CONFIDENCE=0.5

# Motion detection: background subtraction sensitivity
MOTION_THRESHOLD=25
MOTION_MIN_AREA=500

# ─── PID Controller ────────────────────────────────────────────
ENABLE_PID_CONTROLLER=true

# PID gains — Pan axis
PID_PAN_KP=0.05
PID_PAN_KI=0.001
PID_PAN_KD=0.02

# PID gains — Tilt axis
PID_TILT_KP=0.05
PID_TILT_KI=0.001
PID_TILT_KD=0.02

# PID limits
PID_I_MAX=50.0
PID_OUTPUT_MAX=10.0

# Tracking loop rate (frames per second)
TRACKING_FPS=30

# ─── Coordinate Mapping ────────────────────────────────────────
# Pixels per degree — calibrate with scripts/calibrate_gimbal.py
PX_PER_DEGREE_PAN=3.5
PX_PER_DEGREE_TILT=3.5

# ─── Multi-Target Mode ─────────────────────────────────────────
ENABLE_MULTI_TARGET=false

# Priority weights (0.0–1.0, should sum to 1.0)
MULTI_TARGET_WEIGHT_CLASS=0.5
MULTI_TARGET_WEIGHT_SIZE=0.3
MULTI_TARGET_WEIGHT_PROXIMITY=0.2

# Time to dwell on each target before switching (seconds)
MULTI_TARGET_DWELL_SEC=3.0

# ─── Predictive Aim ────────────────────────────────────────────
ENABLE_PREDICTIVE_AIM=false

# Number of frames to look ahead for lead calculation
PREDICTION_FRAMES=3

# Velocity buffer size (frames of history)
PREDICTION_BUFFER_SIZE=10

# ─── Safety Zones ──────────────────────────────────────────────
ENABLE_SAFETY_ZONES=true
SAFETY_ZONES_PATH=./config/safety_zones.json

# ─── Kill Switch ───────────────────────────────────────────────
ENABLE_LASER_KILL_SWITCH=true
KILL_SWITCH_GPIO=4

# Status LEDs
LED_TRACKING_GPIO=23
LED_LASER_GPIO=24

# ─── Day/Night Mode ────────────────────────────────────────────
ENABLE_DAY_NIGHT=false

# Frame brightness threshold (0–255) for day/night switch
DAY_NIGHT_THRESHOLD=50

# ─── Session Recording ─────────────────────────────────────────
ENABLE_RECORDING=false
RECORDING_DIR=./config/sessions
RECORDING_CODEC=MJPG
RECORDING_FPS=15

# ─── Target Lock ───────────────────────────────────────────────
ENABLE_TARGET_LOCK=true

# Seconds to maintain lock after target lost before releasing
LOCK_TIMEOUT_SEC=3.0

# ─── Range Estimation ──────────────────────────────────────────
ENABLE_RANGE_ESTIMATION=false

# Camera focal length in pixels (calibrate or approximate)
FOCAL_LENGTH_PX=600

# Target classes config
TARGET_CLASSES_PATH=./config/target_classes.json

# ─── Sound Deterrent ───────────────────────────────────────────
ENABLE_SOUND_DETERRENT=false
BUZZER_GPIO=22

# Buzzer type: active (on/off) or passive (PWM frequency)
BUZZER_TYPE=active

# Passive buzzer frequency (Hz)
BUZZER_FREQUENCY=2000

# Deterrent mode: buzzer_only, buzzer_and_laser, pulsed
DETERRENT_MODE=buzzer_only

# Pulse pattern (ms)
BUZZER_PULSE_ON_MS=500
BUZZER_PULSE_OFF_MS=500

# ─── Web Dashboard ──────────────────────────────────────────────
ENABLE_WEB_DASHBOARD=true

# SocketIO update rates
SOCKETIO_STATE_RATE=20
STREAM_JPEG_QUALITY=50

# ─── Mock Hardware ──────────────────────────────────────────────
ENABLE_MOCK_HARDWARE=false

# ─── Deployment ─────────────────────────────────────────────────
DEPLOY_HOST=rasp-pi
DEPLOY_PATH=/home/pi/Projects/LaserTurret
```

---

## 5 · PID controller configuration

### PID Tuning Reference

The PID controller runs independently for pan and tilt axes. Each axis computes:

```
error = target_pixel - frame_center_pixel
output = Kp * error + Ki * ∫error·dt + Kd * d(error)/dt
servo_angle += output * px_per_degree
```

### Tuning Procedure

1. **Set Ki=0, Kd=0.** Start with P-only.
2. **Increase Kp** until the laser oscillates around the target. Note this value as `Ku` (ultimate gain).
3. **Set Kp = 0.6 × Ku.** This is a good starting P gain.
4. **Add Kd** to damp oscillations. Start at `Kd = Kp × 0.1` and increase until oscillation stops.
5. **Add Ki** to eliminate steady-state offset. Start at `Ki = Kp × 0.01`. Increase slowly.
6. **Test with moving target.** Adjust D to prevent overshoot on direction changes.

### PID Presets (saved in DB)

| Preset | Kp | Ki | Kd | Use Case |
|---|---|---|---|---|
| `gentle` | 0.03 | 0.0005 | 0.015 | Slow-moving targets, minimal overshoot |
| `responsive` | 0.08 | 0.002 | 0.03 | Fast-moving targets, tolerates some overshoot |
| `snappy` | 0.12 | 0.005 | 0.04 | Very fast tracking, may oscillate on small targets |

### `config/target_classes.json`

```json
{
  "classes": [
    {
      "name": "face",
      "priority": 10,
      "known_size_mm": 180,
      "description": "Human face (average width)"
    },
    {
      "name": "red_ball",
      "priority": 5,
      "known_size_mm": 65,
      "description": "Standard table tennis ball (painted red)"
    },
    {
      "name": "bird",
      "priority": 8,
      "known_size_mm": 150,
      "description": "Common garden bird body width"
    }
  ]
}
```

### `config/safety_zones.json`

```json
{
  "zones": [
    {
      "name": "doorway",
      "x_min": 0,
      "y_min": 0,
      "x_max": 100,
      "y_max": 480,
      "enabled": true
    },
    {
      "name": "window",
      "x_min": 400,
      "y_min": 0,
      "x_max": 640,
      "y_max": 200,
      "enabled": true
    }
  ]
}
```

---

## 6 · High-level architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           AI-VISION LASER TARGETING TURRET                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  VISION PIPELINE                         │  │
│  │  Camera → Color/Face/Object/Motion detect                │  │
│  │  → target centroid (u,v) → target list                   │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                 TARGETING ENGINE                          │  │
│  │  pixel error → PID controller → angle correction         │  │
│  │  → predictive aim lead → coordinate mapper               │  │
│  │  → safety zone check → servo command                     │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │                 HARDWARE CONTROL                         │  │
│  │  SG90 servos (pigpio) │ Laser GPIO │ Buzzer │ Kill switch│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 WEB DASHBOARD                            │  │
│  │  Flask + SocketIO │ PID tuning │ Safety zones │ Manual   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 SAFETY MANAGER                           │  │
│  │  Safety zones │ Kill switch │ Laser timeout │ Day/night  │  │
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
| T6 | Unauthorized laser control | All endpoints require auth; kill switch always active |
| T7 | Laser fired into unsafe area | Safety zones enforced before every laser-on; kill switch GPIO |
| T8 | Laser left on unattended | `LASER_MAX_ON_SEC` auto-timeout; session recording for review |
| T9 | GPIO spoofing | Physical security only — document in threat model |
| T10 | Camera feed interception | Local network only, HTTPS via nginx reverse proxy |
| T11 | Laser aimed at eyes | Safety zone config; physical kill switch wired N/O (fail-safe) |
| T12 | IR laser invisible hazard | Dashboard warns when IR mode active; LED indicator on turret |

---

## 8 · Suggested tech stack

### Backend

| Component | Technology | Justification |
|---|---|---|
| Language | Python 3.11+ | Best CV/control ecosystem |
| Web framework | Flask 3.1 + SocketIO | Lightweight, real-time capable |
| Computer vision | OpenCV 4.10 | Face detection, color tracking, motion detection |
| Servo control | pigpio | Hardware-timed PWM, jitter-free SG90 |
| GPIO | RPi.GPIO | Laser, kill switch, buzzer, LEDs |
| Math | numpy | PID, coordinate mapping, prediction |
| Database | SQLite | Zero-config file-based |
| Auth | bcrypt + Flask sessions | Password hashing + rate limiting |

### Frontend

| Component | Technology |
|---|---|
| Templates | Jinja2 |
| Real-time | Socket.IO client (CDN) |
| PID graphs | HTML5 Canvas or Chart.js (CDN) |
| Styling | Custom CSS (dark theme) |

---

## 9 · Development phases

### Phase 1 — Servo gimbal + laser control

| # | Task | Priority |
|---|---|---|
| 1.1 | Project scaffolding (Flask app, .env, DB) | P0 |
| 1.2 | pigpio servo controller (pan/tilt/yaw) | P0 |
| 1.3 | Laser GPIO controller (visible + IR) | P0 |
| 1.4 | Kill switch GPIO + laser timeout | P0 |
| 1.5 | Mock hardware mode | P0 |
| 1.6 | Unit tests (servo, laser) | P1 |

### Phase 2 — Camera + detection pipeline

| # | Task | Priority |
|---|---|---|
| 2.1 | Camera capture module | P0 |
| 2.2 | Color detection (HSV thresholding) | P0 |
| 2.3 | Face detection (Haar cascade / DNN) | P0 |
| 2.4 | Motion detection (MOG2 background subtraction) | P0 |
| 2.5 | Object detection (trained Haar / TFLite) | P1 |
| 2.6 | Pixel-to-gimbal coordinate mapping | P0 |
| 2.7 | Gimbal calibration script | P0 |

### Phase 3 — PID controller + tracking loop

| # | Task | Priority |
|---|---|---|
| 3.1 | PID controller class (per-axis) | P0 |
| 3.2 | Tracking loop (detect → PID → servo) | P0 |
| 3.3 | Safety zone enforcement | P0 |
| 3.4 | PID tuning API (live gain adjustment) | P0 |
| 3.5 | PID presets (save/load) | P1 |
| 3.6 | Unit tests (PID, coordinate mapper) | P1 |

### Phase 4 — Web dashboard

| # | Task | Priority |
|---|---|---|
| 4.1 | Flask app + auth + layout (dark theme) | P0 |
| 4.2 | Dashboard: live camera + targeting overlay | P0 |
| 4.3 | PID tuning page: sliders + step-response graph | P0 |
| 4.4 | Manual aim (click-to-point on feed) | P0 |
| 4.5 | Safety zone drawing on camera feed | P0 |
| 4.6 | Kill switch button on every page | P0 |
| 4.7 | Settings page (detection, servo, safety) | P1 |
| 4.8 | System status (CPU temp, uptime) | P1 |

### Phase 5 — Advanced features

| # | Task | Priority |
|---|---|---|
| 5.1 | Multi-target mode + prioritization | P1 |
| 5.2 | Predictive aim (velocity lead) | P1 |
| 5.3 | Target lock mode | P1 |
| 5.4 | Session recording (video + CSV) | P1 |
| 5.5 | Range estimation | P2 |
| 5.6 | Day/night mode switching | P2 |
| 5.7 | Sound deterrent (buzzer) | P2 |

### Phase 6 — Deployment and polish

| # | Task | Priority |
|---|---|---|
| 6.1 | Deploy script (rsync) | P0 |
| 6.2 | systemd service | P1 |
| 6.3 | Threat model document | P1 |
| 6.4 | Laser safety documentation | P0 |
| 6.5 | End-to-end testing | P1 |
| 6.6 | README finalization | P0 |

---

## 10 · Performance expectations

| Metric | Pi 4 (2 GB) | Pi 5 (4 GB) |
|---|---|---|
| Color detection | ~8 ms/frame | ~4 ms/frame |
| Face detection (Haar) | ~25 ms/frame | ~12 ms/frame |
| Face detection (DNN) | ~60 ms/frame | ~30 ms/frame |
| Motion detection (MOG2) | ~10 ms/frame | ~5 ms/frame |
| PID compute | <1 ms | <1 ms |
| Coordinate mapping | <1 ms | <1 ms |
| Servo update rate | 50 Hz (pigpio) | 50 Hz (pigpio) |
| Camera capture (640×480) | ~30 FPS | ~30 FPS |
| End-to-end tracking latency | ~40–80 ms | ~20–40 ms |
| SocketIO latency | ~20 ms | ~10 ms |
| Dashboard stream FPS | ~15 FPS | ~25 FPS |

---

## 11 · Deliverables

| # | Deliverable | Phase |
|---|---|---|
| D1 | Servo gimbal control + laser + kill switch + mock mode | Phase 1 |
| D2 | Camera capture + detection pipeline (color, face, motion, object) | Phase 2 |
| D3 | PID controller + tracking loop + safety zones + calibration | Phase 3 |
| D4 | Web dashboard with PID tuning, camera, safety zones, manual aim | Phase 4 |
| D5 | Multi-target, predictive aim, target lock, recording, day/night, buzzer | Phase 5 |
| D6 | Deployment, systemd, documentation, testing | Phase 6 |
