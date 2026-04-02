# Implementation Plan
## AI-Vision Pick-and-Place Robotic Arm

---

## Executive Summary

Build a computer-vision-guided 4/6-DOF robotic arm on Raspberry Pi. Pi Camera + ArUco markers map pixel coordinates to world space. TFLite classifies objects by color, shape, or trained class. Inverse kinematics (analytical 4-axis, numerical Jacobian 6-axis) computes joint angles. PCA9685 drives servos to pick and place objects between containers. Flask + SocketIO dark-themed web dashboard provides joint sliders, Cartesian control, teach mode, live camera, and safety limits. All features `.env` toggleable.

**Budget:** ~$90–165 | **Timeline:** 7–10 days | **Difficulty:** 8/10

---

## Phase 1: Pi Setup & PCA9685 Servo Control (Day 1)

### 1.1 Flash & Configure Pi

```bash
# Flash Raspberry Pi OS (64-bit) with SSH enabled
# Boot, connect, SSH
ssh rasp-pi          # alias for pi@192.168.216.90

# Full system update
sudo apt update && sudo apt upgrade -y

# Enable I2C for PCA9685
sudo raspi-config    # Interface Options → I2C → Enable

# Enable camera
sudo raspi-config    # Interface Options → Camera → Enable

# Install system dependencies
sudo apt install python3-pip python3-venv libopencv-dev i2c-tools -y
```

### 1.2 Project Setup

```bash
# Clone repo
git clone <repo-url> ~/Projects/PickAndPlace
cd ~/Projects/PickAndPlace

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.default .env
nano .env    # Set SESSION_SECRET, ADMIN_PASSWORD, ARM_DOF
```

### 1.3 Wire PCA9685 & Servos

Wire per the wiring diagram in README.md:
- PCA9685 SDA → GPIO 2, SCL → GPIO 3, VCC → 3.3V, GND → GND
- External 5–6V PSU → PCA9685 V+ and GND (bridge GND to Pi GND)
- Arm servos → PCA9685 channels 0–6

```bash
# Verify PCA9685 on I2C bus
sudo i2cdetect -y 1
# Expect: 0x40 in the grid
```

### 1.4 Implement Servo Controller

```python
# src/hardware/servo_controller.py
# - Initialize PCA9685 at configured I2C address
# - Set PWM frequency (50 Hz for standard servos)
# - set_angle(channel, angle) → maps angle to pulse width
# - Per-servo min/max pulse calibration from .env
# - home() → move all joints to HOME_POSITION
# - disable() → set all channels to 0 (e-stop)
```

### 1.5 Implement Mock Hardware

```python
# src/hardware/mock_hardware.py
# - MockServoController: logs commands, tracks virtual joint angles
# - MockCamera: returns sample images with colored shapes
# - MockGPIO: logs pin state changes to console
# - All interfaces identical to real hardware
```

### 1.6 Test Servos

```bash
# Test each servo individually
python scripts/test_servos.py
# Each servo sweeps 0° → 90° → 180° → 90° with 1-second pauses
# Verify: all 6 joints and gripper respond correctly

# Test home position
python -c "from src.hardware.servo_controller import ServoController; s = ServoController(); s.home()"
```

**Milestone:** PCA9685 controls all arm servos. Home position verified.

---

## Phase 2: DH Parameters & Forward Kinematics (Day 2 — Morning)

### 2.1 Measure Arm Dimensions

```bash
# Interactive measurement tool
python scripts/measure_dh.py
# Prompts for each link length (mm):
# - Base height (J1 to J2): ~70 mm
# - Upper arm (J2 to J3): ~105 mm
# - Forearm (J3 to J4): ~98 mm
# - Wrist (J4 to J5): varies
# - Wrist (J5 to J6): varies
# - Tool offset (J6 to gripper tip): ~40 mm
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
# - Extract position (x, y, z) and orientation (roll, pitch, yaw)
```

### 2.3 Verify FK

```bash
# Unit tests
pytest tests/test_forward_kinematics.py -v

# Manual check: set home angles → read end-effector position
# Compare against ruler measurement from base to gripper tip
python -c "
from src.kinematics.forward_kinematics import forward_kinematics
import numpy as np
home = [90, 90, 90, 90, 90, 90]
pose = forward_kinematics(np.radians(home))
print(f'End-effector at: x={pose[0]:.1f}, y={pose[1]:.1f}, z={pose[2]:.1f} mm')
"
```

**Milestone:** FK returns correct end-effector position for known joint angles.

---

## Phase 3: Inverse Kinematics (Day 2 — Afternoon + Day 3)

### 3.1 Analytical IK (4-DOF)

```python
# src/kinematics/inverse_kinematics.py — analytical_ik_4dof()
#
# Given target (x, y, z, pitch):
# 1. J1 (base) = atan2(y, x)
# 2. Project into the J1 plane: r = sqrt(x² + y²), z_eff = z - d1
# 3. J2 + J3 via law of cosines:
#    cos(J3) = (r² + z_eff² - a2² - a3²) / (2 * a2 * a3)
#    J3 = atan2(±sin(J3), cos(J3))    ← elbow-up / elbow-down
#    J2 = atan2(z_eff, r) - atan2(a3*sin(J3), a2 + a3*cos(J3))
# 4. J4 (wrist) = desired_pitch - (J2 + J3)
# 5. Return both elbow-up and elbow-down solutions
# 6. Filter by joint limits
```

### 3.2 Numerical Jacobian IK (6-DOF)

```python
# src/kinematics/inverse_kinematics.py — jacobian_ik_6dof()
#
# Given target 6-DOF pose (x, y, z, roll, pitch, yaw):
# 1. Start from current joint angles (or home)
# 2. Loop (max 100 iterations):
#    a. Compute FK(current_angles) → current_pose
#    b. error = target_pose - current_pose (6×1: position + orientation)
#    c. If ||error|| < tolerance → converge, return current_angles
#    d. Compute Jacobian J (6×6) via numerical differentiation
#    e. delta_q = J_pseudoinverse @ error * step_size
#    f. current_angles += delta_q
#    g. Clamp to joint limits
# 3. If no convergence → fallback to scipy.optimize.minimize
# 4. Return joint angles or "unreachable"
```

### 3.3 Trajectory Interpolation

```python
# src/kinematics/trajectory.py
# - linear_interpolation(start_angles, end_angles, duration, step_rate)
# - Trapezoidal velocity profile (accelerate → cruise → decelerate)
# - Enforce MAX_JOINT_VELOCITY per joint
# - Return list of intermediate joint angle arrays
# - PCA9685 executes at 50 Hz update rate
```

### 3.4 Verify IK

```bash
# Unit tests: IK solutions, round-trip, joint limits, unreachable detection
pytest tests/test_inverse_kinematics.py -v
pytest tests/test_trajectory.py -v

# Manual test: move arm to known position, read FK, then IK back
python -c "
from src.kinematics.inverse_kinematics import solve_ik
result = solve_ik(x=150, y=0, z=100, solver='jacobian')
print(f'Joint angles: {result}')
"
```

**Milestone:** IK solver finds valid joint angles for reachable Cartesian targets.

---

## Phase 4: Camera & ArUco Calibration (Day 3 — Afternoon + Day 4)

### 4.1 Camera Setup

```bash
# Verify camera
libcamera-hello      # Should show camera preview

# Camera module
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f'Frame: {frame.shape}')
cap.release()
"
```

### 4.2 Camera Intrinsic Calibration

```bash
# Print a checkerboard pattern (9×6 inner corners)
# Capture calibration images
python scripts/calibrate_camera.py
# 1. Hold checkerboard at 15+ different angles/distances
# 2. Press SPACE to capture each image
# 3. Press Q when done
# 4. Computes camera matrix + distortion coefficients
# 5. Saves to config/calibration.json
# 6. Reports reprojection error (should be < 0.5 px)
```

### 4.3 ArUco Camera-to-World Calibration

```bash
# Print 4+ ArUco markers (DICT_4X4_50, IDs 0–3, ≥5 cm each)
# Place markers at known positions around the arm workspace
# (e.g., corners of the work surface at measured coordinates)

python scripts/calibrate_aruco.py
# 1. Camera detects all visible ArUco markers
# 2. For each marker, enter its world coordinates (x, y, z) in mm
# 3. Computes camera-to-world transform (homography + solvePnP)
# 4. Saves to config/calibration.json
# 5. Reports reprojection error

# Verify: point at a known position on the table
python -c "
from src.vision.calibration import pixel_to_world
# Example pixel from camera center
world = pixel_to_world(320, 240)
print(f'World: x={world[0]:.1f}, y={world[1]:.1f}, z={world[2]:.1f} mm')
"
```

### 4.4 Implement Vision Modules

```python
# src/vision/camera.py
# - open(index, width, height, fps) → cv2.VideoCapture
# - capture() → frame (numpy array)
# - stream_generator() → JPEG frames for SocketIO

# src/vision/aruco_tracker.py
# - detect_markers(frame) → list of (id, corners, rvec, tvec)
# - estimate_pose(marker) → 4×4 transform

# src/vision/calibration.py
# - load_calibration(path) → camera_matrix, dist_coeffs, world_transform
# - pixel_to_world(u, v) → (x, y, z) in mm
# - world_to_pixel(x, y, z) → (u, v)
```

**Milestone:** Camera captures frames, ArUco calibration maps pixels to world mm.

---

## Phase 5: Object Detection & Classification (Day 4 — Afternoon)

### 5.1 Color Detection

```python
# src/vision/object_detector.py — detect_by_color()
# - Convert frame to HSV
# - For each configured color: apply range mask → find contours
# - Filter by min area → compute centroid
# - Return: [(class="red", confidence=1.0, centroid=(u,v), bbox)]
```

### 5.2 Shape Detection

```python
# src/vision/object_detector.py — detect_by_shape()
# - Convert to grayscale → threshold → find contours
# - For each contour: approxPolyDP → count vertices
#   3 = triangle, 4 = square/rectangle, >6 = circle
# - Return: [(class="circle", confidence, centroid, bbox)]
```

### 5.3 TFLite Detection

```bash
# Download pre-trained model
bash scripts/download_model.sh
# Downloads MobileNet-based classifier to models/object_classifier.tflite
```

```python
# src/vision/object_detector.py — detect_by_tflite()
# - Load .tflite model via tflite_runtime.Interpreter
# - Resize frame to model input size
# - Run inference → output tensor → class index + confidence
# - Map index to label using models/labels.txt
# - Return: [(class="bolt", confidence=0.87, centroid, bbox)]
```

### 5.4 Test Detections

```bash
# Place colored objects in camera view
python -c "
from src.vision.object_detector import detect
from src.vision.camera import Camera
cam = Camera()
frame = cam.capture()
results = detect(frame, mode='color')
for r in results:
    print(f'  {r.class_label} at pixel ({r.cx}, {r.cy}), conf={r.confidence:.2f}')
"
```

**Milestone:** All three detection modes return class + centroid. Pixel → world transform gives object (x, y, z).

---

## Phase 6: Gripper & Pick-and-Place Pipeline (Day 5)

### 6.1 Gripper Control

```python
# src/hardware/gripper.py
# - GripperBase: grip(), release(), is_gripping()
# - ParallelJawGripper(servo_channel, open_angle, close_angle)
# - SuctionGripper(gpio_pin)
# - SoftGripper(servo_channel, open_angle, close_angle)
# - Factory: create_gripper(type) → appropriate class from .env config
```

### 6.2 Arm Controller

```python
# src/control/arm_controller.py
# - move_to(x, y, z, roll=None, pitch=None, yaw=None)
#   → IK solve → safety check → trajectory → execute
# - pick(x, y, z)
#   → move above (z + clearance) → lower → grip → raise
# - place(x, y, z)
#   → move above → lower → release → raise
# - home() → move to HOME_POSITION
```

### 6.3 Full Pipeline

```python
# src/control/pick_place_pipeline.py
# - run_cycle():
#   1. Capture frame
#   2. Detect object → class + pixel centroid
#   3. pixel_to_world(u, v) → (x, y, z)
#   4. Lookup container: CLASS_ROUTING[class] → container position
#   5. arm.pick(object_x, object_y, object_z)
#   6. arm.place(container_x, container_y, container_z)
#   7. arm.home()
#   8. Log to database
```

### 6.4 Test Full Cycle

```bash
# Place a red object on the work surface
python -c "
from src.control.pick_place_pipeline import PickPlacePipeline
pipeline = PickPlacePipeline()
result = pipeline.run_cycle()
print(f'Result: {result}')
"
# Expected: arm detects red object → picks it → places in bin_a → returns home
```

**Milestone:** Full autonomous pick-and-place cycle working.

---

## Phase 7: Web Dashboard (Day 6–7)

### 7.1 Flask App & Authentication

```python
# app.py
# - Flask app factory
# - SocketIO initialization
# - Blueprint registration (auth, dashboard, control, teach, vision, settings)
# - SQLite database initialization
# - .env loading via python-dotenv

# src/routes/auth.py
# - POST /login — bcrypt verify, rate limit 10/15min, set session (24h)
# - GET /logout — clear session
# - @login_required decorator for all other routes
```

### 7.2 Dashboard Layout

```html
<!-- templates/layout.html -->
<!-- Dark theme: background #1a1a2e, accent #0f3460, cards #16213e -->
<!-- Sidebar: Dashboard | Joint Control | Cartesian | Teach | Camera | Settings -->
<!-- Header: project name + E-STOP button (red, always visible) -->
<!-- Footer: connection status, system temp -->
```

### 7.3 Joint Control Page

```javascript
// static/js/joint_control.js
// - 6 range sliders (J1–J6): 0°–180° with current value display
// - On slider change → socket.emit('set_joint', {joint: 1, angle: 90})
// - Server receives → servo_controller.set_angle(channel, angle)
// - Gripper open/close toggle button
// - Home button → all joints to HOME_POSITION
// - Read current angles at SOCKETIO_JOINT_RATE Hz
```

### 7.4 Cartesian Control Page

```javascript
// static/js/cartesian_control.js
// - x/y/z number inputs with ±1mm and ±10mm step buttons
// - (Optional) roll/pitch/yaw for 6-DOF
// - "Move To" button → POST /api/cartesian → IK solve → move
// - IK status indicator (green=valid, red=unreachable)
// - Current end-effector position display (from FK)
```

### 7.5 Camera Feed Page

```javascript
// static/js/camera_feed.js
// - SocketIO image stream → render on <canvas>
// - Detection overlay: bounding boxes + class labels
// - Detection mode dropdown (color / shape / tflite)
// - "Detect" button → single detection → show results
// - "Pick & Place" button → full pipeline cycle
// - Detection history list (last 10)
```

### 7.6 Teach Mode Page

```javascript
// static/js/teach_mode.js
// - Record / Stop / Save buttons
// - Current teaching: waypoint list (joint angles + gripper state)
// - "Add Waypoint" → capture current position
// - Delete / reorder waypoints
// - Saved sequences list → Load / Delete / Replay
// - Speed slider (0.1× – 2.0×)
// - Loop toggle checkbox
```

### 7.7 Settings Page

- Arm configuration display (DOF, IK solver, gripper type)
- Calibration status: last calibrated date, reprojection error
- "Recalibrate Camera" and "Recalibrate ArUco" buttons
- Safety zone visualization: 2D top-down view of workspace with no-go zones
- System info: CPU temp, memory, disk, uptime

**Milestone:** Full web dashboard with all control modes, camera feed, and teach mode.

---

## Phase 8: Safety Manager & E-Stop (Day 7 — Afternoon)

### 8.1 Safety Implementation

```python
# src/control/safety_manager.py
# - check_joint_limits(angles) → True/False
# - check_no_go_zones(x, y, z) → True/False (loads config/no_go_zones.json)
# - check_workspace_bounds(x, y, z) → True/False (radius check)
# - validate_move(target_angles, target_xyz) → (allowed, reason)
# - All IK solutions pass through validation before execution
```

### 8.2 E-Stop GPIO

```bash
# Wire N/O button between GPIO 4 and GND (use internal pull-up)
# Wire green LED to GPIO 22 (running indicator)
# Wire red LED to GPIO 23 (error/e-stop indicator)
```

```python
# GPIO 4: falling edge interrupt → emergency_stop()
# emergency_stop():
#   1. Disable all PCA9685 channels (set PWM to 0)
#   2. Set state = STOPPED
#   3. Red LED on, green LED off
#   4. SocketIO broadcast: {status: 'EMERGENCY_STOP'}
# resume():
#   1. Require explicit call (web button or GPIO reset)
#   2. Re-enable PCA9685
#   3. Green LED on, red LED off
```

### 8.3 No-Go Zone Config

```json
// config/no_go_zones.json
{
  "zones": [
    {
      "name": "camera_mount",
      "type": "rectangular",
      "x_min": -50, "x_max": 50,
      "y_min": 150, "y_max": 250,
      "z_min": 0, "z_max": 200
    },
    {
      "name": "base_exclusion",
      "type": "cylindrical",
      "center_x": 0, "center_y": 0,
      "radius": 60,
      "z_min": 0, "z_max": 300
    }
  ]
}
```

**Milestone:** Safety manager prevents dangerous moves. E-stop halts arm immediately.

---

## Phase 9: Conveyor Belt Integration (Day 8 — Optional)

### 9.1 Wiring

```bash
# DC motor driver:
# - Direction: GPIO 17
# - PWM speed: GPIO 18 (hardware PWM)
# - Speed sensor (encoder): GPIO 27 (interrupt)
```

### 9.2 Implementation

```python
# src/hardware/conveyor.py
# - start(speed_percent) → set PWM duty
# - stop() → PWM to 0
# - get_speed() → belt velocity in mm/s (from encoder pulses)
# - Lead time: t = pick_zone_distance / belt_speed
# - Arm pre-positions at pick zone X, waits for object to arrive
```

### 9.3 Test

```bash
# Place object on belt
# System detects approaching object
# Arm moves to pick zone, waits, picks at calculated time
python -c "
from src.control.pick_place_pipeline import PickPlacePipeline
pipeline = PickPlacePipeline()
pipeline.run_conveyor_mode()
"
```

**Milestone:** Arm picks moving objects from conveyor with lead-time compensation.

---

## Phase 10: Teach Mode Deep Dive (Day 8)

### 10.1 Recording Flow

1. User clicks "Record" on dashboard.
2. User moves arm via joint sliders or Cartesian controls.
3. At each desired position, user clicks "Add Waypoint".
4. System captures: `{joints: [j1..j6], gripper: true/false, delay_ms: 500}`.
5. User clicks "Stop" → sequence ready for save.
6. User enters name → saves to `config/sequences/{name}.json` and DB.

### 10.2 Replay Flow

1. User selects a saved sequence from the library.
2. Sets speed scale (0.1× to 2.0×) and loop toggle.
3. Clicks "Replay" → arm executes each waypoint in order.
4. Between waypoints: trajectory interpolation at configured speed.
5. If loop enabled → repeat from first waypoint indefinitely.
6. "Stop Replay" button or E-stop halts immediately.

**Milestone:** Teach mode works end-to-end — record, save, replay, loop.

---

## Phase 11: Deployment & Production (Day 9)

### 11.1 Deploy Script

```bash
# deploy/deploy_to_pi.sh
#!/bin/bash
HOST=${1:-rasp-pi}
DEST=${2:-/home/pi/Projects/PickAndPlace}

rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' \
  --exclude='data/' --exclude='models/training_data/' \
  --exclude='__pycache__/' --exclude='*.pyc' \
  ./ ${HOST}:${DEST}/

ssh ${HOST} "cd ${DEST} && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

echo "Deployed to ${HOST}:${DEST}"
```

### 11.2 systemd Service

```bash
sudo tee /etc/systemd/system/pickplace.service << 'EOF'
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
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now pickplace
sudo systemctl status pickplace
```

### 11.3 Verify Production

```bash
# Full power cycle test
sudo reboot
# After boot, verify:
systemctl status pickplace    # active (running)
curl http://localhost:5000    # dashboard loads
# Open http://192.168.216.90:5000 from browser
```

**Milestone:** Deployed, auto-starts on boot, full dashboard accessible.

---

## Phase 12: Final Testing & Documentation (Day 9–10)

### 12.1 Unit Tests

```bash
pytest tests/ -v
# test_forward_kinematics.py — FK accuracy
# test_inverse_kinematics.py — IK solutions, round-trip, limits, unreachable
# test_safety_manager.py — no-go zones, workspace bounds, joint limits
# test_trajectory.py — interpolation, velocity limits
```

### 12.2 Integration Tests

| Test | Expected Outcome |
|---|---|
| Place red object → auto pick-place | Object moved to bin_a |
| Place blue object → auto pick-place | Object moved to bin_b |
| Command point in no-go zone | Move rejected, error displayed |
| Command beyond workspace radius | Move rejected, error displayed |
| Press e-stop during move | Arm halts immediately |
| Resume after e-stop | Arm re-enabled, moves to home |
| Record 4 waypoints → save → replay | Arm follows exact path |
| Replay with loop | Arm repeats until stop pressed |
| 11 failed logins | 12th attempt blocked (rate limit) |
| `ENABLE_MOCK_HARDWARE=true` | Dashboard works without PCA9685 |
| Mobile browser | Responsive layout, sliders work |

### 12.3 Documentation

- [ ] Finalize README.md
- [ ] Write `docs/dh_parameters.md` — how to measure and set DH params
- [ ] Write `docs/calibration_guide.md` — camera + ArUco step-by-step
- [ ] Write `docs/wiring_diagram.md` — full pin-by-pin reference
- [ ] Write `docs/threat_model.md` — security analysis

**Milestone:** All tests pass, documentation complete, project ready for use.
