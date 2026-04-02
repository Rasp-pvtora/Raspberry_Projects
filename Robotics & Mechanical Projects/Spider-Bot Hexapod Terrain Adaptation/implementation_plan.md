# Implementation Plan
## 🕷️ Spider-Bot Hexapod Terrain Adaptation

---

## Executive Summary

Build a 6-legged hexapod robot with 18 servos (6 legs × 3 joints: coxa, femur, tibia) on Raspberry Pi. Dual PCA9685 boards drive servos. Gait engine provides tripod/wave/ripple patterns with turning and speed control. FSR sensors on each foot enable terrain-adaptive walking. MPU6050 IMU + PID keeps the body level on uneven ground. FPV camera with pan/tilt streams to the dashboard. HC-SR04 ultrasonic sensors enable obstacle avoidance and wall following. INA219 monitors battery for low-power auto-return. Flask + SocketIO dark-themed web dashboard with Three.js 3D IK visualization, gait control, recording/replay, and per-leg diagnostics. All features `.env` toggleable.

**Budget:** ~$156–196 | **Timeline:** 9–12 days | **Difficulty:** 9/10

---

## Phase 1: Pi Setup & Dual PCA9685 Servo Control (Day 1)

### 1.1 Flash & Configure Pi

```bash
# Flash Raspberry Pi OS (64-bit) with SSH enabled
# Boot, connect, SSH
ssh rasp-pi          # alias for pi@192.168.216.90

# Full system update
sudo apt update && sudo apt upgrade -y

# Enable I2C for PCA9685, MPU6050, INA219
sudo raspi-config    # Interface Options → I2C → Enable

# Enable SPI for MCP3008 ADC (FSR reading)
sudo raspi-config    # Interface Options → SPI → Enable

# Enable camera
sudo raspi-config    # Interface Options → Camera → Enable

# Install system dependencies
sudo apt install python3-pip python3-venv libopencv-dev i2c-tools -y
```

### 1.2 Project Setup

```bash
# Clone repo
git clone <repo-url> ~/Projects/SpiderBot
cd ~/Projects/SpiderBot

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.default .env
nano .env    # Set SESSION_SECRET, ADMIN_PASSWORD, link lengths
```

### 1.3 Wire Dual PCA9685 & 18 Servos

Wire per the wiring diagram in README.md:
- Both PCA9685 boards share I2C bus: SDA → GPIO 2, SCL → GPIO 3
- Board 1 at default 0x40: legs 1–3 (channels 0–8)
- Board 2 at 0x41 (bridge A0): legs 4–6 (channels 0–8) + pan/tilt (ch 9–10)
- BEC (5V/5A) output → both PCA9685 V+ pads (servo power)
- Bridge all GND lines (Pi, BEC, PCA9685)

```bash
# Verify all I2C devices
sudo i2cdetect -y 1
# Expect: 0x40 (PCA9685 #1), 0x41 (PCA9685 #2)
```

### 1.4 Implement Dual Servo Controller

```python
# src/hardware/servo_controller.py
# - Initialize two PCA9685 boards at configured I2C addresses
# - Servo addressing: (board, channel) tuples from .env
# - set_angle(board, channel, angle) → maps angle to pulse width (500–2500 µs)
# - Per-servo min/max pulse calibration from .env
# - set_leg(leg_id, coxa_angle, femur_angle, tibia_angle) → sets all 3 servos
# - home() → move all 18 joints to configured neutral angles
# - disable() → set all channels to 0 (e-stop)
```

### 1.5 Implement Mock Hardware

```python
# src/hardware/mock_hardware.py
# - MockServoController: logs commands, tracks 18 virtual joint angles + 2 pan/tilt
# - MockIMU: returns configurable pitch/roll or gentle oscillation
# - MockFSR: returns random force values or flat terrain
# - MockUltrasonic: returns configurable distances (front/left/right)
# - MockINA219: returns configurable voltage/current
# - MockCamera: returns sample frames
# - All interfaces identical to real hardware
```

### 1.6 Test Servos

```bash
# Test each servo individually (all 18 + 2 pan/tilt)
python scripts/test_servos.py
# Each servo sweeps 0° → 90° → 180° → 90° with 0.5-second pauses
# Verify: all 18 leg joints respond, no binding

# Test home position
python scripts/calibrate_servos.py
# Interactive: select servo → sweep → adjust center/min/max → save to .env
```

**Milestone:** Dual PCA9685 controls all 18 leg servos + 2 pan/tilt. Home position verified.

---

## Phase 2: Leg Geometry & Per-Leg Inverse Kinematics (Day 2)

### 2.1 Measure Leg Dimensions

```bash
# Measure with calipers (mm):
# - Coxa length: pivot to femur joint (~30 mm)
# - Femur length: femur joint to tibia joint (~80 mm)
# - Tibia length: tibia joint to foot tip (~120 mm)
# - Leg mount positions: (x, y) offset from body center for each leg
# - Mount angles: rotation of each leg relative to body forward axis

# Save to config/leg_geometry.json
```

### 2.2 Leg Geometry Config

```json
// config/leg_geometry.json
{
  "body": {
    "length_mm": 160,
    "width_mm": 80
  },
  "link_lengths_mm": {
    "coxa": 30,
    "femur": 80,
    "tibia": 120
  },
  "legs": [
    {"id": 1, "name": "front_right",  "mount_x":  60, "mount_y": -40, "mount_angle_deg":  45, "board": 1, "channels": [0,1,2]},
    {"id": 2, "name": "mid_right",    "mount_x":   0, "mount_y": -50, "mount_angle_deg":  90, "board": 1, "channels": [3,4,5]},
    {"id": 3, "name": "rear_right",   "mount_x": -60, "mount_y": -40, "mount_angle_deg": 135, "board": 1, "channels": [6,7,8]},
    {"id": 4, "name": "front_left",   "mount_x":  60, "mount_y":  40, "mount_angle_deg": -45, "board": 2, "channels": [0,1,2]},
    {"id": 5, "name": "mid_left",     "mount_x":   0, "mount_y":  50, "mount_angle_deg": -90, "board": 2, "channels": [3,4,5]},
    {"id": 6, "name": "rear_left",    "mount_x": -60, "mount_y":  40, "mount_angle_deg":-135, "board": 2, "channels": [6,7,8]}
  ]
}
```

### 2.3 Implement Per-Leg IK

```python
# src/kinematics/leg_ik.py
#
# Given target foot position (x, y, z) relative to coxa mount:
# 1. θ₁ (coxa) = atan2(y, x)
# 2. r = sqrt(x² + y²) - L_coxa  (projected distance in leg plane)
# 3. d = sqrt(r² + z²)  (distance from femur joint to foot)
# 4. Check reachability: |L_femur - L_tibia| < d < L_femur + L_tibia
# 5. cos(θ₃) = (L_femur² + L_tibia² - d²) / (2 * L_femur * L_tibia)
#    θ₃ = acos(cos(θ₃))
# 6. α = atan2(z, r), β = atan2(L_tibia*sin(θ₃), L_femur + L_tibia*cos(θ₃))
#    θ₂ = α + β
# 7. Clamp all angles to joint limits
```

### 2.4 Implement Body-Level IK

```python
# src/kinematics/body_ik.py
#
# Given body transform (tx, ty, tz, roll, pitch, yaw):
# 1. Build 4×4 body transform matrix T_body
# 2. For each leg:
#    a. Get foot position in world frame (from current foot placement)
#    b. Apply inverse body transform: P_local = T_body⁻¹ × P_world
#    c. Subtract leg mount offset, rotate by mount angle
#    d. Solve per-leg IK for P_local → (θ₁, θ₂, θ₃)
# 3. Return all 18 joint angles
```

### 2.5 Verify IK

```bash
# Unit tests
pytest tests/test_leg_ik.py -v
pytest tests/test_body_ik.py -v

# Manual: move each leg to a known position, verify angles
python -c "
from src.kinematics.leg_ik import solve_leg_ik
angles = solve_leg_ik(x=100, y=0, z=-80, coxa_len=30, femur_len=80, tibia_len=120)
print(f'Coxa={angles[0]:.1f}°, Femur={angles[1]:.1f}°, Tibia={angles[2]:.1f}°')
"
```

**Milestone:** Per-leg IK produces correct joint angles. Body IK translates/rotates body while feet stay planted.

---

## Phase 3: Gait Engine (Day 3–4)

### 3.1 Gait State Machine

```python
# src/gait/gait_engine.py
#
# Each leg has a state: SUPPORT, LIFT, SWING, DOWN
# Gait engine:
# 1. Advance gait phase clock by dt
# 2. For each leg: determine target state from gait pattern + phase offset
# 3. SUPPORT: foot on ground, push body forward (stance)
# 4. LIFT: raise foot to STEP_HEIGHT_MM
# 5. SWING: move foot forward by STRIDE_LENGTH_MM
# 6. DOWN: lower foot to ground (or FSR contact if terrain adaptation enabled)
# 7. Compute foot targets → body IK → leg IK → servo commands
# 8. Loop at 50 Hz (PCA9685 update rate)
```

### 3.2 Gait Patterns

```python
# src/gait/gait_patterns.py
#
# Tripod:
#   Group A: legs {1, 4, 5} — phase offset 0%
#   Group B: legs {2, 3, 6} — phase offset 50%
#   Swing/support alternate between groups
#
# Wave:
#   Each leg has phase offset: leg_i → offset = (i-1) / 6 * 100%
#   Only one leg swings at a time, 5 always grounded
#
# Ripple:
#   Pairs: (1,4) offset 0%, (2,5) offset 33%, (3,6) offset 66%
#   Two legs swing at a time, 4 always grounded
#
# Free: load from JSON (recorded gait sequence)
```

### 3.3 Turning

```python
# Turning by varying stride length per side:
# - Spin in place (TURN_RADIUS_MM = 0):
#     Left legs: +stride (forward)
#     Right legs: -stride (backward)
# - Arc turn:
#     Inner stride = stride × (R - body_width/2) / R
#     Outer stride = stride × (R + body_width/2) / R
#   where R = TURN_RADIUS_MM
```

### 3.4 Test Gaits

```bash
# Test tripod gait (fastest)
python -c "
from src.gait.gait_engine import GaitEngine
engine = GaitEngine(pattern='tripod')
engine.start()
import time; time.sleep(5)
engine.stop()
"
# Hexapod should walk forward 5 seconds in tripod pattern

# Test each gait pattern: tripod, wave, ripple
# Test turning: spin in place, arc left, arc right
# Test speed: 0.5× and 2.0× speed scale
```

**Milestone:** Hexapod walks with all three gait patterns. Turning and speed control work.

---

## Phase 4: IMU Stabilization & FSR Terrain Adaptation (Day 4–5)

### 4.1 MPU6050 IMU Setup

```bash
# Verify MPU6050
sudo i2cdetect -y 1    # Expect 0x68

python scripts/test_imu.py
# Should print pitch/roll at 100 Hz
# Tilt the board → values change
```

### 4.2 Implement IMU + PID + Body Leveling

```python
# src/sensors/imu.py
# - Initialize MPU6050 at configured address
# - Read accel (ax, ay, az) and gyro (gx, gy, gz)
# - Complementary filter: angle = 0.98*(angle + gyro*dt) + 0.02*accel_angle
# - Return stable pitch and roll estimates

# src/stabilization/pid_controller.py
# - PID class: __init__(Kp, Ki, Kd), compute(setpoint, measurement, dt)
# - Anti-windup: clamp integral to ±max
# - Derivative low-pass: d_filtered = α * d_raw + (1-α) * d_prev

# src/stabilization/body_leveler.py
# - Loop at IMU_RATE_HZ:
#   1. Read IMU pitch/roll
#   2. pitch_correction = pid_pitch.compute(0, imu_pitch, dt)
#   3. roll_correction = pid_roll.compute(0, imu_roll, dt)
#   4. Clamp corrections to MAX_TILT_CORRECTION_DEG
#   5. body_ik.update(roll=-roll_correction, pitch=-pitch_correction)
```

### 4.3 FSR Terrain Adaptation

```bash
# Test FSR readings
python scripts/test_fsr.py
# Press each foot pad → verify ADC values (0–1023) change
```

```python
# src/sensors/fsr.py
# - Initialize MCP3008 via spidev
# - read_all() → [fsr1, fsr2, ..., fsr6] (0–1023)
# - Software low-pass filter per channel

# Integration with gait DOWN phase:
# In gait_engine.py, during DOWN state for each leg:
# 1. Start lowering foot from swing position
# 2. Each iteration: extend tibia by 1mm increment
# 3. Read FSR for that foot
# 4. If FSR > FSR_CONTACT_THRESHOLD → stop (foot touched ground)
# 5. If extension > FSR_MAX_EXTENSION_MM → stop (max reached)
# 6. Result: each foot finds its own ground level
```

### 4.4 Test Stabilization + Terrain

```bash
# Test IMU stabilization:
# Place hexapod on flat surface → start walking → tilt surface 10°
# Body should stay level (legs adjust asymmetrically)

# Test terrain adaptation:
# Place hexapod on surface with books/ramps under some feet
# Legs should auto-adjust to different heights
# All feet should make solid contact
```

**Milestone:** Body stays level on slopes. Legs adapt to uneven terrain via FSR.

---

## Phase 5: Battery Management & Ultrasonic Navigation (Day 5–6)

### 5.1 INA219 Battery Monitoring

```bash
# Verify INA219
sudo i2cdetect -y 1    # Expect 0x44

python scripts/test_battery.py
# Should print: voltage (V), current (mA), power (mW)
# Verify against multimeter reading
```

```python
# src/sensors/battery.py
# - Initialize INA219 at configured address
# - read() → {voltage_v, current_ma, power_mw, cell_voltage_v}
# - Warning: cell_voltage < 3.5V → emit event
# - Critical: cell_voltage < 3.3V → trigger auto-return, reduce speed
```

### 5.2 Ultrasonic Sensors

```bash
# Test each sensor
python scripts/test_ultrasonic.py
# Place hand at known distances → verify readings (cm)
```

```python
# src/sensors/ultrasonic.py
# - trigger_and_read(trig_pin, echo_pin) → distance_cm
# - read_all() → {front: cm, left: cm, right: cm}
# - Median filter: 3 readings per measurement

# src/navigation/obstacle_avoidance.py
# - Loop: read front/left/right sensors
# - If front < OBSTACLE_STOP_CM: stop → compare left vs right → turn toward open side
# - If front < OBSTACLE_SLOW_CM: reduce speed to 50%
# - Resume normal speed when clear

# src/navigation/wall_follower.py
# - PID on side sensor: maintain WALL_FOLLOW_DISTANCE_CM
# - Error = target_distance - measured_distance
# - Output = turn radius adjustment → gait engine
```

### 5.3 Return Home

```python
# src/navigation/return_home.py
# - Track position via dead reckoning:
#   x += stride * cos(heading) per step
#   y += stride * sin(heading) per step
# - On low battery trigger:
#   1. Compute reverse heading: atan2(-y, -x)
#   2. Estimate distance: sqrt(x² + y²)
#   3. Walk toward origin with obstacle avoidance active
#   4. Stop when estimated near start or battery critical
```

**Milestone:** Battery monitoring triggers warnings. Obstacle avoidance and wall following work.

---

## Phase 6: FPV Camera & Pan/Tilt (Day 6)

### 6.1 Camera Setup

```bash
# Verify camera
libcamera-hello

python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f'Frame: {frame.shape}')
cap.release()
"
```

### 6.2 Implement Camera & Pan/Tilt

```python
# src/hardware/camera.py
# - Open Pi Camera via cv2.VideoCapture
# - capture() → frame (numpy array)
# - encode_jpeg(frame, quality) → JPEG bytes
# - stream_generator() → yields JPEG frames for SocketIO

# src/hardware/pan_tilt.py
# - set_pan(angle) → Board 2 channel 9
# - set_tilt(angle) → Board 2 channel 10
# - home() → pan=90°, tilt=90°
# - smooth_move(target_pan, target_tilt, duration) → interpolated movement
```

**Milestone:** Camera streams MJPEG to dashboard. Pan/tilt responsive.

---

## Phase 7: Web Dashboard (Day 7–9)

### 7.1 Flask App & Authentication

```python
# app.py
# - Flask app factory + SocketIO init
# - Blueprint registration (auth, dashboard, gait, control, camera, nav, record, settings)
# - SQLite database initialization
# - .env loading via python-dotenv
# - Background threads: gait engine, IMU loop, sensor polling, camera stream

# src/routes/auth.py
# - POST /login — bcrypt verify, rate limit 10/15min, set session (24h)
# - GET /logout — clear session
# - @login_required decorator for all other routes
```

### 7.2 Dashboard Layout

```html
<!-- templates/layout.html -->
<!-- Dark theme: background #1a1a2e, accent #0f3460, cards #16213e -->
<!-- Sidebar: Dashboard | Gait | Camera | Navigation | Settings -->
<!-- Header: project name + E-STOP button (red, always visible) -->
<!-- Footer: connection status, battery voltage, CPU temp -->
```

### 7.3 Three.js 3D Visualization

```javascript
// static/js/three_viz.js
// - Three.js scene: hexapod body as rectangular box
// - 6 legs: coxa (cylinder), femur (cylinder), tibia (cylinder) per leg
// - Update from SocketIO: receive 18 joint angles → update leg transforms
// - Color-coded: green (support), blue (swing phase), red (FSR overload)
// - OrbitControls for mouse orbit/zoom
// - Ground plane grid for reference
// - FSR force indicators at foot tips (circle size = force)
// - IMU visualization: body tilt matches real robot
```

### 7.4 Gait Control Page

```javascript
// static/js/gait_control.js
// - Gait pattern buttons: Tripod / Wave / Ripple / Free
// - Start/Stop walking buttons
// - Speed slider: 0.1× – 2.0×
// - Stride length slider
// - Step height slider
// - Turn radius: joystick or slider (left ← → right)
// - If ENABLE_GAIT_RECORDING: Record / Stop / Save buttons
// - Recorded gait library: Load / Delete / Replay
```

### 7.5 Camera Page

```javascript
// static/js/camera_feed.js
// - SocketIO image stream → <canvas> render
// - Pan slider (0°–180°) and tilt slider (30°–150°)
// - Virtual joystick for pan/tilt control
// - "Center" button → reset to 90°/90°
// - "Snapshot" button → download current frame as JPEG
```

### 7.6 Navigation Page

```javascript
// static/js/nav_panel.js
// - Mode buttons: Manual / Obstacle Avoid / Wall Follow / Return Home
// - Ultrasonic distance bars (front/left/right) — color-coded by proximity
// - Top-down heading indicator (compass-like arrow)
// - Estimated position display (x, y from dead reckoning)
// - Start/Stop autonomous mode
```

### 7.7 Settings Page

- Leg geometry display (link lengths, mount positions)
- PID tuning live sliders (Kp, Ki, Kd for pitch and roll) — changes apply in real-time
- Servo calibration: select servo → test sweep → set min/max/center
- Feature toggle switches (ENABLE_* flags)
- Battery info: voltage, current, estimated remaining
- System info: CPU temp, memory, disk, uptime

**Milestone:** Full web dashboard with 3D visualization, gait control, FPV, navigation, and settings.

---

## Phase 8: Gait Recording (Day 9)

### 8.1 Recording Flow

1. User starts walking in any gait pattern.
2. User clicks "Record" on dashboard.
3. System captures: all 18 joint angles + phase state + timing at each gait step.
4. User clicks "Stop" → recording finalized.
5. User enters name → saves to `config/gait_sequences/{name}.json` and DB.

### 8.2 Replay Flow

1. User selects saved recording from library.
2. Sets speed scale (0.1× – 2.0×).
3. Clicks "Replay" → gait engine switches to "free" pattern using recorded frames.
4. Robot replays the exact recorded leg movements.
5. "Stop Replay" button or e-stop halts immediately.

```python
# src/gait/gait_recorder.py
# - start_recording() → begin capture
# - Per gait step: append {joints: {leg1: [c,f,t], ...}, timing_ms, phase}
# - stop_recording() → finalize
# - save(name) → JSON file + DB entry
# - load(name) → return frame list
# - replay(name, speed_scale) → feed frames to gait engine as "free" pattern
```

**Milestone:** Record, save, and replay custom gait patterns.

---

## Phase 9: Deployment & Production (Day 10)

### 9.1 Deploy Script

```bash
# deploy/deploy_to_pi.sh
#!/bin/bash
HOST=${1:-rasp-pi}
DEST=${2:-/home/pi/Projects/SpiderBot}

rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' \
  --exclude='data/' --exclude='__pycache__/' --exclude='*.pyc' \
  ./ ${HOST}:${DEST}/

ssh ${HOST} "cd ${DEST} && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

echo "Deployed to ${HOST}:${DEST}"
```

### 9.2 systemd Service

```bash
sudo tee /etc/systemd/system/spiderbot.service << 'EOF'
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
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now spiderbot
sudo systemctl status spiderbot
```

### 9.3 Verify Production

```bash
# Full power cycle test
sudo reboot
# After boot, verify:
systemctl status spiderbot    # active (running)
curl http://localhost:5000    # dashboard loads
# Open http://192.168.216.90:5000 from browser
```

**Milestone:** Deployed, auto-starts on boot, full dashboard accessible.

---

## Phase 10: Final Testing & Documentation (Day 10–12)

### 10.1 Unit Tests

```bash
pytest tests/ -v
# test_leg_ik.py — per-leg IK accuracy, reachability, joint limits
# test_body_ik.py — body translation/rotation, foot compensation
# test_gait_engine.py — state transitions, phase timing, all patterns
# test_pid.py — PID step response, anti-windup, derivative filter
# test_obstacle_avoidance.py — sensor thresholds, turn decisions
```

### 10.2 Integration Tests

| Test | Expected Outcome |
|---|---|
| Tripod gait on flat ground | Hexapod walks forward smoothly |
| Wave gait on flat ground | Hexapod walks slowly, very stable |
| Ripple gait on flat ground | Hexapod walks at medium speed |
| Spin in place (turn_radius=0) | Hexapod rotates without translating |
| Arc turn left/right | Hexapod follows curved path |
| Terrain adaptation (books under some feet) | Legs auto-adjust heights, all feet make contact |
| IMU stabilization (tilt surface 10°) | Body stays level, legs compensate |
| Obstacle avoidance (place obstacle in front) | Hexapod stops, turns, resumes |
| Wall following | Hexapod maintains constant distance from wall |
| Battery warning at 10.5V | Dashboard shows warning, speed reduced |
| Battery critical at 9.9V | Return-home triggered, non-essential disabled |
| FPV camera stream | Live feed on dashboard, pan/tilt responsive |
| Gait record → save → replay | Hexapod replays exact recorded pattern |
| Three.js visualization | 3D model matches physical robot pose in real-time |
| E-stop button | All servos go to neutral immediately |
| 11 failed logins | 12th attempt blocked (rate limit) |
| `ENABLE_MOCK_HARDWARE=true` | Dashboard works without hardware |
| Mobile browser | Responsive layout, sliders and joystick work |

### 10.3 Documentation

- [ ] Finalize README.md
- [ ] Write `docs/ik_math.md` — hexapod IK derivation with diagrams
- [ ] Write `docs/gait_patterns.md` — gait timing diagrams and tuning guide
- [ ] Write `docs/wiring_diagram.md` — full pin-by-pin reference
- [ ] Write `docs/threat_model.md` — security analysis

**Milestone:** All tests pass, documentation complete, project ready for use.
