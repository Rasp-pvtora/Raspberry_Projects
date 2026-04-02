# Implementation Plan
## 🤝 Haptic Feedback Shadow Arm

---

## Executive Summary

Build a master-slave teleoperation arm system on Raspberry Pi. A Master Arm (potentiometers via ADS1115 ADC) mirrors its position to a Slave Arm (servos via PCA9685) in real-time at ~50 Hz. INA219 current sensors on slave servos measure motor load and drive proportional haptic vibration motors (DRV2605L) on the master for force feedback. Flask + SocketIO dark-themed web dashboard with Three.js 3D visualization, force scaling, recording/playback, precision mode, gripper mirroring, and collision detection. All features `.env` toggleable.

**Budget:** ~$102–180 | **Timeline:** 7–9 days | **Difficulty:** 7/10

---

## Phase 1: Pi Setup & Basic Mirroring (Day 1)

### 1.1 Flash & Configure Pi

```bash
# Flash Raspberry Pi OS (64-bit) with SSH enabled
# Boot, connect, SSH
ssh rasp-pi          # alias for pi@192.168.216.90

# Full system update
sudo apt update && sudo apt upgrade -y

# Enable I2C for ADS1115, PCA9685, INA219, DRV2605L
sudo raspi-config    # Interface Options → I2C → Enable

# Install system dependencies
sudo apt install python3-pip python3-venv i2c-tools -y
```

### 1.2 Project Setup

```bash
# Clone repo
git clone <repo-url> ~/Projects/ShadowArm
cd ~/Projects/ShadowArm

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.default .env
nano .env    # Set SESSION_SECRET, ADMIN_PASSWORD, arm config
```

### 1.3 Wire ADS1115 ADCs & Potentiometers (Master Arm)

Wire per the wiring diagram in README.md:
- ADS1115 #1 (0x48): SDA → GPIO 2, SCL → GPIO 3, ADDR → GND, VDD → 3.3V
- ADS1115 #2 (0x49): same I2C bus, ADDR → VDD
- 6 potentiometers: VCC → 3.3V, GND → GND, wipers → ADS1115 Ax inputs

```bash
# Verify ADS1115 boards on I2C bus
sudo i2cdetect -y 1
# Expect: 0x48 and 0x49 in the grid
```

### 1.4 Wire PCA9685 & Servos (Slave Arm)

- PCA9685: SDA → GPIO 2, SCL → GPIO 3, VCC → 3.3V, GND → GND
- External 5–6V PSU → PCA9685 V+ and GND (bridge GND to Pi GND)
- Slave arm servos → PCA9685 channels 0–6

```bash
# Verify PCA9685 on I2C bus
sudo i2cdetect -y 1
# Expect: 0x40 in the grid (in addition to 0x48, 0x49)
```

### 1.5 Implement ADC Reader (Master Input)

```python
# src/master/encoder_reader.py
# - Initialize 2× ADS1115 at 0x48 and 0x49
# - read_all_joints() → [j1, j2, j3, j4, j5, j6] raw ADC values
# - apply_calibration(raw) → angle (0°–180°) via linear mapping
# - EMA filter: filtered = α × new + (1-α) × prev (α from ADC_FILTER_ALPHA)
# - Support continuous mode for fast reads (~100 SPS per channel)
# - Configurable gain for voltage range
```

### 1.6 Implement Servo Controller (Slave Output)

```python
# src/slave/servo_controller.py
# - Initialize PCA9685 at configured I2C address
# - Set PWM frequency (50 Hz for standard servos)
# - set_angle(channel, angle) → maps angle to pulse width (500–2500 µs)
# - Per-servo min/max pulse calibration from .env
# - home() → move all joints to HOME_POSITION
# - disable() → set all channels to 0 (e-stop)
```

### 1.7 Implement Mirror Engine

```python
# src/control/mirror_engine.py
# - Background thread running at MIRROR_LOOP_HZ (default 50 Hz)
# - Each tick:
#   1. Read master: encoder_reader.read_all_joints()
#   2. Apply calibration: raw ADC → angles
#   3. Apply speed limiting (if enabled)
#   4. Apply precision mode scaling (if active)
#   5. Check collision bounds (if enabled)
#   6. Write slave: servo_controller.set_angle() per joint
#   7. Read force: current_sensor.read_all() (if enabled)
#   8. Write haptic: haptic_driver.set_intensity() (if enabled)
#   9. Broadcast state via SocketIO
# - Thread-safe state: use threading.Lock for shared state dict
# - State dict: {master_angles, slave_angles, currents, force, precision, loop_ms}
```

### 1.8 Implement Mock Hardware

```python
# src/hardware/mock_hardware.py
# - MockADS1115: returns smooth sinusoidal ADC values per channel
# - MockPCA9685: logs servo commands, tracks virtual joint angles
# - MockINA219: returns configurable current based on angle change rate
# - MockDRV2605L: logs vibration intensity to console
# - MockGPIO: logs e-stop, LED state changes
# - All interfaces identical to real hardware
```

### 1.9 Test Basic Mirroring

```bash
# Test ADC reads
python scripts/test_adc.py
# Move each potentiometer → see ADC values change for correct channel

# Test servos
python scripts/test_servos.py
# Each servo sweeps 0° → 90° → 180° → 90° with 1-second pauses

# Test basic mirror (no force feedback yet)
python -c "
from src.control.mirror_engine import MirrorEngine
engine = MirrorEngine()
engine.start()
# Move master pots → slave servos should follow
import time; time.sleep(10)
engine.stop()
"
```

**Milestone:** Master potentiometers drive slave servos in real-time. Mirror loop runs at ~50 Hz.

---

## Phase 2: Forward Kinematics & Safety (Day 2 — Morning)

### 2.1 Measure Arm Dimensions

```bash
# Interactive measurement tool
python scripts/measure_dh.py
# Prompts for each link length (mm):
# - Base height (J1 to J2): ~70 mm
# - Upper arm (J2 to J3): ~105 mm
# - Forearm (J3 to J4): ~98 mm
# - Wrist sections: varies by kit
# - Tool offset (last joint to gripper tip): ~40 mm
# Saves to config/dh_params.json
```

### 2.2 Implement FK Solver

```python
# src/kinematics/dh_params.py
# - Load DH table from config/dh_params.json
# - Validate: correct number of rows for ARM_DOF
# - Return structured DH parameter list

# src/kinematics/forward_kinematics.py
# - dh_transform(alpha, a, d, theta) → 4×4 homogeneous matrix
# - forward_kinematics(joint_angles) → chain multiply → end-effector pose
# - Support 4-DOF and 6-DOF
# - Extract position (x, y, z) for collision detection
```

### 2.3 Safety Manager

```python
# Integrated into mirror engine:
# - Joint angle limits: clamp angles to JOINT_N_LIMITS before sending to PCA9685
# - E-stop GPIO 4: falling edge interrupt → disable all PCA9685 → set STOPPED
# - Web e-stop: POST /api/estop → same disable logic
# - Resume: explicit POST /api/resume → re-enable PCA9685
# - Status LEDs: green (GPIO 22) = running, red (GPIO 23) = error/e-stop
```

### 2.4 Verify FK & Safety

```bash
# Unit tests
pytest tests/test_forward_kinematics.py -v

# Manual check: set known angles → verify end-effector position
python -c "
from src.kinematics.forward_kinematics import forward_kinematics
import numpy as np
home = [90, 90, 90, 90, 90, 90]
pos = forward_kinematics(np.radians(home))
print(f'End-effector: x={pos[0]:.1f}, y={pos[1]:.1f}, z={pos[2]:.1f} mm')
"
```

**Milestone:** FK computes end-effector position. Joint limits enforced. E-stop works.

---

## Phase 3: Joint Calibration (Day 2 — Afternoon)

### 3.1 Auto-Calibration Routine

```python
# src/master/calibration.py
# - calibrate_joint(joint_num):
#   1. Prompt user: "Move joint N to MIN position, press Enter"
#   2. Read ADC value → store as adc_min
#   3. Prompt user: "Move joint N to MAX position, press Enter"
#   4. Read ADC value → store as adc_max
#   5. Compute mapping: angle = (raw - min) / (max - min) × range + offset
#   6. Save to config/calibration.json
#
# - calibrate_all():
#   Loop through joints 1–6, calibrate each sequentially
#
# - Plateau detection (auto mode):
#   Slowly read ADC while user moves joint
#   Detect when ADC stops changing (derivative ≈ 0 for N samples)
#   That's a mechanical limit
```

### 3.2 Test Calibration

```bash
# Interactive calibration
python scripts/calibrate_joints.py
# Follow prompts for each joint

# Verify calibration accuracy
python -c "
from src.master.encoder_reader import EncoderReader
reader = EncoderReader()
while True:
    angles = reader.read_all_calibrated()
    print(f'Angles: {[f\"{a:.1f}°\" for a in angles]}', end='\r')
"
# Move master arm → angles should read 0°–180° accurately at limits
```

**Milestone:** Calibrated ADC-to-angle mapping for all 6 joints. Calibration persists in JSON.

---

## Phase 4: Force Feedback — INA219 + DRV2605L (Day 3)

### 4.1 Wire INA219 Current Sensors

Wire INA219 in series with slave servo V+ lines (see wiring diagram in README):
- INA219 #1 (0x40): J1 servo
- INA219 #2 (0x41): J2 servo
- INA219 #3 (0x44): J3 servo
- INA219 #4 (0x45): J4 servo

```bash
# Verify INA219 addresses
sudo i2cdetect -y 1
# Expect: 0x40, 0x41, 0x44, 0x45 (note: 0x40 may conflict with PCA9685)
# If conflict: change PCA9685 address via A0 solder bridge → 0x41, and shift INA219s
```

> **Important:** PCA9685 default address is also 0x40. If using INA219 at 0x40, change PCA9685 to 0x41 by bridging its A0 pad, then update `PCA9685_I2C_ADDRESS=0x41` in `.env`. Alternatively, shift INA219 addresses.

### 4.2 Implement Current Sensor

```python
# src/slave/current_sensor.py
# - Initialize 4–6 INA219 sensors at configured addresses
# - read_current(sensor_id) → current_mA
# - read_all() → [j1_mA, j2_mA, j3_mA, j4_mA]
# - Automatic shunt resistor calibration on init
# - Handle I2C bus errors gracefully (retry once)
```

### 4.3 Wire DRV2605L Haptic Driver

- DRV2605L: SDA → GPIO 2, SCL → GPIO 3, VIN → 3.3V
- Vibration motor → DRV2605L OUT+/OUT−
- For multiple motors: TCA9548A multiplexer at 0x70, each DRV2605L on a separate mux channel

### 4.4 Implement Haptic Driver

```python
# src/master/haptic_driver.py
# - Initialize DRV2605L via smbus2 at 0x5A
# - set_mode(ERM or LRA) from .env
# - set_intensity(motor_id, value_0_255) → real-time vibration control
# - For single DRV2605L: multiplex via TCA9548A or time-division
# - For simplified setup: single motor, max of all force channels
# - stop_all() → set all motors to 0
```

### 4.5 Implement Force Feedback Pipeline

```python
# src/control/force_feedback.py
# - process(currents_ma, force_scale):
#   1. For each joint:
#      excess = current_mA - FORCE_IDLE_MA
#      excess = max(0, excess)  # ignore below-idle noise
#      normalized = excess / (FORCE_MAX_MA - FORCE_IDLE_MA)
#      intensity = clamp(normalized * 255 * force_scale, 0, 255)
#   2. Return [intensity_j1, intensity_j2, intensity_j3, intensity_j4]
#
# - Map to haptic motors:
#   Motor 0 (base area)  ← max(intensity_j1, intensity_j2)
#   Motor 1 (forearm)    ← intensity_j3
#   Motor 2 (wrist)      ← intensity_j4
#   Motor 3 (gripper)    ← gripper force (future)
```

### 4.6 Test Force Feedback

```bash
# Test INA219 reads
python scripts/test_current.py
# Move slave servo under load → current should increase

# Test DRV2605L haptic motor
python scripts/test_haptic.py
# Motor vibrates at low, medium, high intensity

# Test full force feedback loop
python -c "
from src.control.mirror_engine import MirrorEngine
engine = MirrorEngine(force_feedback=True)
engine.start()
# Push against slave arm → feel vibration on master
import time; time.sleep(30)
engine.stop()
"
```

**Milestone:** INA219 reads servo current. DRV2605L drives vibration motors. Operator feels resistance.

---

## Phase 5: Speed Limiting & Precision Mode (Day 4 — Morning)

### 5.1 Speed Limiter

```python
# src/control/speed_limiter.py
# - limit(current_angles, target_angles, dt):
#   For each joint:
#     delta = target - current
#     max_delta = MAX_JOINT_VELOCITY_Jn * dt
#     if abs(delta) > max_delta:
#       target = current + sign(delta) * max_delta
#   return clamped_target_angles
#
# - Prevents sudden jerks that could damage servos or workspace
# - Slave catches up smoothly when master stabilizes
```

### 5.2 Precision Mode

```python
# src/control/precision_mode.py
# - When active:
#   target = home_angle + (target - home_angle) / PRECISION_RATIO
#   MAX_JOINT_VELOCITY_Jn *= PRECISION_SPEED_FACTOR
#
# - Toggle via dashboard button or API
# - Home angle = reference center for scaled movement
# - PRECISION_RATIO=10 → master 10° movement = slave 1° movement
```

### 5.3 Test

```bash
# Test speed limiting
pytest tests/test_speed_limiter.py -v
# Fast input → output capped at max velocity

# Test precision mode
# Enable from dashboard → move master arm widely → slave arm moves subtly
```

**Milestone:** Speed limiting prevents dangerous jerks. Precision mode enables fine manipulation.

---

## Phase 6: Gripper Mirroring & Collision Detection (Day 4 — Afternoon)

### 6.1 Gripper Mirroring

```python
# src/master/fsr_reader.py
# - Read FSR from ADS1115 #2, channel A2
# - Map ADC value (FSR_MIN_ADC–FSR_MAX_ADC) → squeeze (0.0–1.0)
# - 0.0 = no squeeze (gripper fully open)
# - 1.0 = max squeeze (gripper fully closed)

# src/slave/gripper.py
# - map_squeeze_to_angle(squeeze) → servo angle
#   angle = GRIPPER_OPEN_ANGLE + squeeze * (GRIPPER_CLOSE_ANGLE - GRIPPER_OPEN_ANGLE)
# - set_angle(angle) → PCA9685 channel 6
```

### 6.2 Collision Detection

```python
# src/control/collision_detector.py
# - Load workspace bounds from config/workspace_bounds.json
# - check(joint_angles):
#   1. FK(joint_angles) → end_effector (x, y, z)
#   2. For each bound in workspace:
#      - Rectangular: x_min ≤ x ≤ x_max, y_min ≤ y ≤ y_max, z_min ≤ z ≤ z_max
#      - Cylindrical: sqrt(x² + y²) ≤ radius, z_min ≤ z ≤ z_max
#   3. If outside bounds: return BLOCKED
#   4. If within warning_margin: return WARNING
#   5. Else: return OK
# - If COLLISION_ESTOP_ENABLED and BLOCKED → trigger e-stop
```

### 6.3 Workspace Bounds Config

```json
// config/workspace_bounds.json
{
  "workspace": {
    "type": "cylindrical",
    "description": "Maximum arm reach envelope",
    "center_x": 0,
    "center_y": 0,
    "radius_mm": 350,
    "z_min_mm": -50,
    "z_max_mm": 400
  },
  "exclusion_zones": [
    {
      "name": "base_exclusion",
      "type": "cylindrical",
      "center_x": 0,
      "center_y": 0,
      "radius_mm": 60,
      "z_min_mm": 0,
      "z_max_mm": 300
    }
  ]
}
```

### 6.4 Test

```bash
# Collision detection
pytest tests/test_collision_detector.py -v

# Gripper mirroring: squeeze FSR → slave gripper closes
python -c "
from src.master.fsr_reader import FSRReader
from src.slave.gripper import Gripper
fsr = FSRReader()
grip = Gripper()
while True:
    squeeze = fsr.read_squeeze()
    grip.set_from_squeeze(squeeze)
    print(f'Squeeze: {squeeze:.2f}', end='\r')
"
```

**Milestone:** Gripper mirroring works. Collision detection blocks unsafe poses.

---

## Phase 7: Web Dashboard (Day 5–6)

### 7.1 Flask App & Authentication

```python
# app.py
# - Flask app factory
# - SocketIO initialization
# - Blueprint registration (auth, dashboard, control, recording, visualization, settings)
# - SQLite database initialization
# - .env loading via python-dotenv
# - Start mirror engine in background thread

# src/routes/auth.py
# - POST /login — bcrypt verify, rate limit 10/15min, set session (24h)
# - GET /logout — clear session
# - @login_required decorator for all other routes
```

### 7.2 Dashboard Layout

```html
<!-- templates/layout.html -->
<!-- Dark theme: background #1a1a2e, accent #0f3460, cards #16213e -->
<!-- Sidebar: Dashboard (3D) | Force Feedback | Recording | Settings -->
<!-- Header: project name + E-STOP button (red, always visible) -->
<!-- Footer: connection status, system temp, mirror loop rate -->
```

### 7.3 Three.js 3D Visualization

```javascript
// static/js/three_visualizer.js
// - Load Three.js + OrbitControls from CDN
// - Build arm model from DH parameters:
//   - Cylinders for link segments (colored by role)
//   - Spheres for joints (rotation animated)
//   - Master arm in blue tones, slave arm in green tones
// - Update on SocketIO 'arm_state' event:
//   - Set joint rotations from angle arrays
//   - Color segments by force intensity (green → yellow → red gradient)
// - Show workspace bounds as translucent wireframe cylinder
// - Show collision exclusion zones as translucent red volumes
// - OrbitControls for rotate/zoom/pan
// - Grid helper on XY plane for spatial reference
```

### 7.4 Force Feedback Panel

```javascript
// static/js/force_panel.js
// - Per-joint horizontal bar chart showing current (mA)
//   - Bar color: green (below idle) → yellow → red (near max)
// - Force scaling slider: 0.1× – 5.0× with current value display
//   - On change → socket.emit('set_force_scale', {scale: 2.5})
// - Idle/max threshold display (from .env)
// - Real-time update at SOCKETIO_UPDATE_RATE Hz
```

### 7.5 Recording Interface

```javascript
// static/js/recording_ui.js
// - Record button (red pulsing while active) + Stop button
// - Save dialog: enter recording name
// - Recording list: name, duration, date, frame count
// - Per recording: Load, Replay, Loop, Delete buttons
// - Speed slider: 0.1× – 5.0× with preset buttons (0.5×, 1×, 2×)
// - Progress bar during replay (current frame / total)
// - Loop checkbox
```

### 7.6 Settings Page

- Arm configuration display (DOF, home position)
- Feature toggle status (read-only display of .env flags)
- Calibration: "Recalibrate Joints" button → triggers calibration routine
- Precision mode: ratio display, speed factor
- Collision bounds: current workspace volume, exclusion zones (read-only)
- Force thresholds: idle and max mA display
- System info: CPU temp, memory, disk, uptime, mirror loop Hz

**Milestone:** Full web dashboard with 3D visualization, force graph, recording UI, and settings.

---

## Phase 8: Recording & Playback (Day 6 — Afternoon)

### 8.1 Recording Implementation

```python
# src/control/recorder.py
# - start_recording(fps=50):
#   Set recording flag, create empty frame list
#   Mirror engine appends frame each tick: {t_ms, master_angles, gripper, force}
#
# - stop_recording() → return frame list
#
# - save_recording(name, frames):
#   Save as JSON to config/recordings/{name}.json
#   Insert metadata into recordings DB table
#
# - load_recording(name) → frame list
```

### 8.2 Playback Implementation

```python
# src/control/player.py
# - replay_recording(frames, speed_scale=1.0):
#   Set playback flag on mirror engine
#   Mirror engine reads angles from frame list instead of ADS1115
#   Timing: sleep(frame_interval / speed_scale) between frames
#
# - loop_recording(frames, speed_scale):
#   Same as replay but wraps back to first frame
#
# - stop_playback():
#   Clear playback flag, mirror engine resumes reading from ADS1115
```

### 8.3 Test

```bash
# Record a short sequence
# Dashboard → Recording → Record → move master arm for 5 seconds → Stop → Save as "test_seq"

# Replay
# Dashboard → Recording → select "test_seq" → Replay
# Slave arm should reproduce the recorded movements

# Loop mode
# Check "Loop" → Replay → slave arm repeats sequence until stopped
```

**Milestone:** Record, save, load, replay, and loop arm movements.

---

## Phase 9: Network Teleoperation (Day 7 — Optional)

### 9.1 SocketIO Network Protocol

```python
# src/control/network_teleop.py
#
# SLAVE MODE (server):
# - Listen on TELEOP_SERVER_PORT for joint_state events
# - Validate packet: timestamp, sequence number, angles array
# - Feed into slave servo controller (bypasses local ADC)
# - Emit force_data events back to master: {currents_ma, t_ms}
#
# MASTER MODE (client):
# - Connect to slave's TELEOP_SERVER_HOST:TELEOP_SERVER_PORT
# - Read local ADS1115 → emit joint_state events
# - Receive force_data → feed to local DRV2605L
#
# PREDICTIVE BUFFERING:
# - Slave maintains ring buffer of last TELEOP_BUFFER_SIZE angle packets
# - Compute per-joint velocity: (angle[n] - angle[n-1]) / dt
# - On network stall (no packet for >2 tick intervals):
#   predicted = last_angle + velocity × elapsed_time
#   Clamp to joint limits
# - On packet resume:
#   Blend: target = α × live + (1-α) × predicted (α ramps 0→1 over 5 ticks)
```

### 9.2 Latency Measurement

```python
# Round-trip time:
# Master sends ping with timestamp → Slave echoes → Master computes RTT
# Display on dashboard: "Latency: 23 ms" (rolling average of last 10)
```

### 9.3 Test

```bash
# On Slave Pi:
TELEOP_MODE=slave python app.py
# Listens on port 5001

# On Master Pi:
TELEOP_MODE=master TELEOP_SERVER_HOST=192.168.216.91 python app.py
# Connects to slave, sends joint data

# Test: move master on Pi A → slave on Pi B follows
# Test: push slave on Pi B → vibration on master Pi A

# Test latency resilience:
# Introduce delay: tc qdisc add dev eth0 root netem delay 100ms
# Master → slave should still track (with prediction smoothing stalls)
```

**Milestone:** LAN teleoperation with force feedback across two Pis, latency compensation active.

---

## Phase 10: Deployment & Production (Day 8)

### 10.1 Deploy Script

```bash
# deploy/deploy_to_pi.sh
#!/bin/bash
set -e
HOST=${1:-rasp-pi}
DEST=${2:-/home/pi/Projects/ShadowArm}

echo "Deploying to $HOST:$DEST ..."
rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' \
  --exclude='data/' --exclude='config/recordings/' \
  ./ "$HOST:$DEST/"

ssh "$HOST" "cd $DEST && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
echo "Deploy complete. SSH to $HOST and start: cd $DEST && source venv/bin/activate && python app.py"
```

### 10.2 systemd Service

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

```bash
# Install service
sudo cp deploy/shadowarm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now shadowarm

# Verify
sudo systemctl status shadowarm
journalctl -u shadowarm -f
```

### 10.3 Final Validation

```bash
# Full test checklist:
# 1. Basic mirroring: move master → slave follows (all 6 joints)
# 2. Force feedback: push slave → feel vibration on master
# 3. Force scaling: adjust 0.5× and 3× → feel difference
# 4. Speed limiting: fast master movement → slave smooth
# 5. Precision mode: toggle → fine control verified
# 6. Gripper: squeeze FSR → slave gripper closes
# 7. Collision detection: move toward boundary → slave stops
# 8. Recording: record → save → replay → loop
# 9. Dashboard: 3D viz updates, force graph real-time
# 10. E-stop: GPIO button + web button → all servos disable
# 11. Calibration: run calibrate_joints.py → improved accuracy
# 12. Auth: login required, rate limit works, 24h session
# 13. Boot test: power cycle → service auto-starts → dashboard accessible
```

**Milestone:** Production-ready teleoperation system, systemd managed, dashboard accessible on boot.

---

## Phase 11: Testing & Documentation (Day 8–9)

### 11.1 Unit Tests

```bash
pytest tests/ -v

# Test coverage:
# - test_forward_kinematics.py: FK chain accuracy, 4/6 DOF
# - test_mirror_engine.py: ADC → angle → servo mapping accuracy
# - test_force_feedback.py: current → vibration scaling, clamping
# - test_speed_limiter.py: velocity capping, smooth tracking
# - test_collision_detector.py: workspace bounds, exclusion zones
```

### 11.2 Documentation

```bash
# Write docs/threat_model.md (from TSD §8)
# Write docs/wiring_diagram.md (detailed pin-by-pin reference)
# Write docs/dh_parameters.md (measurement guide)
# Write docs/protocol.md (master-slave communication protocol)
# Review and finalize README.md
```

**Milestone:** All tests pass. Documentation complete. Project ready for use.
