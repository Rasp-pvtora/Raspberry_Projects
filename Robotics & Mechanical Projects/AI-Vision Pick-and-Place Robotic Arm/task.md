# Task Tracker
## AI-Vision Pick-and-Place Robotic Arm

---

## Phase 1: Project Setup & PCA9685 Servo Control
- [ ] Flash Raspberry Pi OS (64-bit) to SD card with SSH enabled
- [ ] Boot Pi, connect via `ssh rasp-pi` (192.168.216.90)
- [ ] Run `sudo apt update && sudo apt upgrade -y`
- [ ] Enable I2C: `sudo raspi-config` → Interface Options → I2C → Enable
- [ ] Enable camera: `sudo raspi-config` → Interface Options → Camera → Enable
- [ ] Install system dependencies: `sudo apt install python3-pip python3-venv libopencv-dev -y`
- [ ] Clone repo and create virtual environment: `python3 -m venv venv && source venv/bin/activate`
- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.default` to `.env` and configure settings
- [ ] Wire PCA9685 to Pi I2C (SDA → GPIO 2, SCL → GPIO 3, VCC → 3.3V, GND → GND)
- [ ] Connect external 5–6V servo PSU to PCA9685 V+ and GND (bridge GND to Pi)
- [ ] Verify PCA9685: `sudo i2cdetect -y 1` (expect `0x40`)
- [ ] Connect arm servos to PCA9685 channels 0–6 (per wiring diagram)
- [ ] Implement `src/hardware/servo_controller.py` — PCA9685 init, angle-to-PWM, per-channel control
- [ ] Implement per-servo pulse width calibration (min/max µs from `.env`)
- [ ] Implement `src/hardware/mock_hardware.py` — simulated servos, GPIO, camera
- [ ] Test: run `python scripts/test_servos.py` — each servo should sweep its range
- [ ] Implement home position command (move all joints to `HOME_POSITION` angles)
- [ ] Verify all servos reach home position without binding

## Phase 2: DH Parameters & Forward Kinematics
- [ ] Measure arm link lengths (calipers) and record in `config/dh_params.json`
- [ ] Implement `src/kinematics/dh_params.py` — load DH table from JSON, validate
- [ ] Implement `src/kinematics/forward_kinematics.py` — compute 4×4 homogeneous transform chain
- [ ] Support both 4-DOF and 6-DOF configurations (`ARM_DOF` env var)
- [ ] Implement `scripts/measure_dh.py` — interactive tool to verify link lengths against FK output
- [ ] Write unit tests: `tests/test_forward_kinematics.py`
  - [ ] Test home position → expected end-effector pose
  - [ ] Test known joint angles → known Cartesian position
  - [ ] Test 4-DOF vs 6-DOF configuration switching

## Phase 3: Inverse Kinematics Solver
- [ ] Implement `src/kinematics/inverse_kinematics.py` — solver interface
- [ ] Implement analytical solver for 4-DOF arm (geometric decomposition):
  - [ ] J1 = atan2(y, x)
  - [ ] J2 + J3 via law of cosines
  - [ ] J4 = desired_pitch − (J2 + J3)
  - [ ] Handle elbow-up / elbow-down solutions
- [ ] Implement numerical Jacobian solver for 6-DOF arm:
  - [ ] Compute Jacobian matrix from FK
  - [ ] Iterative Jacobian pseudoinverse method
  - [ ] Convergence criteria (position error < 1 mm, orientation error < 1°)
  - [ ] Max iterations limit with fallback to scipy.optimize.minimize
- [ ] Enforce joint limits on all IK solutions
- [ ] Return "unreachable" status if no valid solution found
- [ ] Verify IK ↔ FK round-trip: IK(FK(q)) ≈ q
- [ ] Write unit tests: `tests/test_inverse_kinematics.py`
  - [ ] Test reachable points → valid joint angles
  - [ ] Test unreachable points → error returned
  - [ ] Test joint limit enforcement
  - [ ] Test FK(IK(target)) ≈ target

## Phase 4: Trajectory Interpolation
- [ ] Implement `src/kinematics/trajectory.py` — joint-space linear interpolation
- [ ] Support configurable duration and step count
- [ ] Enforce max angular velocity per joint (`MAX_JOINT_VELOCITY` from `.env`)
- [ ] Smooth start/stop with trapezoidal velocity profile
- [ ] Write unit tests: `tests/test_trajectory.py`

## Phase 5: Camera & ArUco Calibration
- [ ] Verify camera: `libcamera-hello`
- [ ] Implement `src/vision/camera.py` — Pi Camera capture, frame pipeline, resolution config
- [ ] Implement `scripts/calibrate_camera.py` — checkerboard intrinsic calibration
  - [ ] Capture ≥15 checkerboard images at various angles
  - [ ] Compute camera matrix and distortion coefficients
  - [ ] Save to `config/calibration.json`
- [ ] Print ArUco markers (DICT_4X4_50, IDs 0–3, ≥5 cm)
- [ ] Place markers at known world positions around the workspace
- [ ] Implement `src/vision/aruco_tracker.py` — ArUco detection + pose estimation
- [ ] Implement `src/vision/calibration.py` — camera-to-world transform from ArUco poses
- [ ] Implement `scripts/calibrate_aruco.py`:
  - [ ] Detect all visible ArUco markers
  - [ ] User enters world coordinates for each marker
  - [ ] Compute and save camera-to-world homography
  - [ ] Report reprojection error
- [ ] Test: point camera at known object → verify (x, y, z) output matches ruler measurement

## Phase 6: Object Detection & Classification
- [ ] Implement `src/vision/object_detector.py` — unified detection interface
- [ ] Implement color detection mode:
  - [ ] HSV thresholding with configurable ranges from `.env`
  - [ ] Contour detection → centroid → bounding box
  - [ ] Return class label (color name) + centroid (u, v)
- [ ] Implement shape detection mode:
  - [ ] Contour approximation → vertex count → classify circle/square/triangle
  - [ ] Min area filter (`SHAPE_MIN_AREA`)
- [ ] Implement TFLite detection mode:
  - [ ] Load `.tflite` model and labels
  - [ ] Preprocess frame → inference → postprocess
  - [ ] Return class label + confidence + bounding box
- [ ] Download pre-trained TFLite model: `bash scripts/download_model.sh`
- [ ] Test all three modes: place colored shapes in camera view, verify classification
- [ ] Implement pixel → world coordinate transform using calibration data

## Phase 7: Gripper Control
- [ ] Implement `src/hardware/gripper.py` — gripper abstraction with `grip()` and `release()`
- [ ] Implement parallel jaw gripper (servo channel, open/close angles from `.env`)
- [ ] Implement suction gripper (GPIO relay for vacuum pump)
- [ ] Implement soft gripper (servo channel, same interface as parallel jaw)
- [ ] Test each gripper type: open → close → open cycle
- [ ] Verify gripper settle time (`GRIPPER_SETTLE_MS`) prevents premature arm movement

## Phase 8: Pick-and-Place Pipeline
- [ ] Implement `src/control/arm_controller.py`:
  - [ ] `move_to(x, y, z, roll, pitch, yaw)` — IK → trajectory → execute
  - [ ] `pick(x, y, z)` — approach → lower → grip → raise
  - [ ] `place(x, y, z)` — move → lower → release → raise
  - [ ] `home()` — return to home position
- [ ] Implement `src/control/pick_place_pipeline.py`:
  - [ ] Capture frame → detect object → classify → get (x, y, z)
  - [ ] Lookup target container by class (`CLASS_ROUTING` from `.env`)
  - [ ] Execute pick(object_pos) → place(container_pos)
  - [ ] Log result to database (`pick_place_log` table)
  - [ ] Handle errors: IK fail, safety block, grip fail
- [ ] Implement `src/services/db.py` — SQLite init with all tables from TSD
- [ ] Test full pipeline: place a colored object → system detects, picks, places in correct bin
- [ ] Test error handling: place object outside reach → verify graceful failure

## Phase 9: Safety Manager
- [ ] Implement `src/control/safety_manager.py`:
  - [ ] Load joint limits from `.env`
  - [ ] Load no-go zones from `config/no_go_zones.json`
  - [ ] Check every IK solution against joint limits
  - [ ] Check every target position against no-go zones
  - [ ] Check workspace radius bounds (`WORKSPACE_MAX_RADIUS_MM`, `WORKSPACE_MIN_RADIUS_MM`)
- [ ] Create `config/no_go_zones.json` template:
  - [ ] Define rectangular zone (e.g., table area where the camera sits)
  - [ ] Define cylindrical zone (e.g., column near the arm base)
- [ ] Implement e-stop GPIO:
  - [ ] GPIO 4 interrupt (falling edge, pull-up)
  - [ ] On trigger: disable all PCA9685 channels immediately
  - [ ] Set system state to STOPPED
  - [ ] Require explicit resume (web button or GPIO reset)
- [ ] Implement speed limiting: cap trajectory velocity per joint
- [ ] Implement servo watchdog: if no command for 2 s → hold; if 10 s → park and disable
- [ ] Wire e-stop button (N/O) to GPIO 4
- [ ] Wire status LEDs: green (GPIO 22), red (GPIO 23)
- [ ] Write unit tests: `tests/test_safety_manager.py`
  - [ ] Test point inside no-go zone → blocked
  - [ ] Test point outside workspace → blocked
  - [ ] Test joint angle beyond limits → blocked
  - [ ] Test valid point → allowed

## Phase 10: Web Dashboard — Authentication & Layout
- [ ] Implement `app.py` — Flask + SocketIO entry point
- [ ] Implement `src/routes/auth.py`:
  - [ ] Login route with bcrypt password verification
  - [ ] Rate limiting: 10 attempts / 15 min per IP
  - [ ] Session cookie: HttpOnly, SameSite, 24h expiry
  - [ ] Logout route
- [ ] Implement `templates/layout.html` — dark theme base template:
  - [ ] Sidebar navigation (Dashboard, Joint, Cartesian, Teach, Camera, Settings)
  - [ ] E-stop button in header (always visible, red)
  - [ ] System status bar (connection, CPU temp)
- [ ] Implement `templates/login.html` — login form
- [ ] Implement `static/css/style.css`:
  - [ ] Dark theme: background `#1a1a2e`, accent `#0f3460`, card `#16213e`
  - [ ] Responsive layout (sidebar → bottom nav on mobile)
- [ ] Implement `static/js/main.js` — SocketIO connection, e-stop handler
- [ ] Test: login → see dashboard → e-stop button works

## Phase 11: Web Dashboard — Joint & Cartesian Control
- [ ] Implement `src/routes/control_api.py`:
  - [ ] POST `/api/joint` — set individual joint angles
  - [ ] POST `/api/cartesian` — set target (x, y, z) → IK → move
  - [ ] POST `/api/home` — return to home position
  - [ ] POST `/api/estop` — emergency stop
  - [ ] POST `/api/resume` — resume from e-stop
  - [ ] GET `/api/state` — current joint angles, end-effector position, status
- [ ] Implement `templates/dashboard.html`:
  - [ ] Live camera feed (SocketIO image stream)
  - [ ] Current joint angles display
  - [ ] End-effector position display
  - [ ] Pick-and-place stats from database
- [ ] Implement `static/js/joint_control.js`:
  - [ ] 6 range sliders (J1–J6) with real-time values
  - [ ] Slider change → SocketIO emit → arm moves immediately
  - [ ] Home button
- [ ] Implement `static/js/cartesian_control.js`:
  - [ ] x/y/z sliders or number inputs
  - [ ] Optional roll/pitch/yaw for 6-DOF
  - [ ] "Move To" button → IK solve → move arm
  - [ ] Display IK status (valid/unreachable)
- [ ] Implement `static/js/safety_panel.js`:
  - [ ] E-stop button (red, large)
  - [ ] Safety status indicators (joint limits, no-go zones)
  - [ ] Resume button (after e-stop)

## Phase 12: Web Dashboard — Camera Feed & Detections
- [ ] Implement `src/routes/vision_api.py`:
  - [ ] SocketIO event: stream camera frames as JPEG (configurable quality)
  - [ ] SocketIO event: stream detection results (class, confidence, bbox)
  - [ ] POST `/api/detect` — trigger single detection + return result
  - [ ] POST `/api/pick-place` — trigger full pick-and-place cycle
- [ ] Implement `templates/camera.html`:
  - [ ] Live camera canvas with detection overlay
  - [ ] Detection mode toggle (color/shape/tflite)
  - [ ] Detection results list
  - [ ] "Pick & Place" button (trigger full pipeline)
- [ ] Implement `static/js/camera_feed.js`:
  - [ ] SocketIO image stream → canvas render
  - [ ] Draw bounding boxes and labels overlay
  - [ ] Display detection confidence

## Phase 13: Teach Mode
- [ ] Implement `src/control/teach_mode.py`:
  - [ ] `start_recording()` — begin capturing waypoints
  - [ ] `record_waypoint()` — save current joint angles + gripper state
  - [ ] `stop_recording()` — finalize sequence
  - [ ] `save_sequence(name)` — persist to `config/sequences/` + DB
  - [ ] `load_sequence(name)` — load from file
  - [ ] `replay_sequence(name, speed_scale)` — execute waypoints
  - [ ] `loop_sequence(name, speed_scale)` — repeat until stopped
- [ ] Implement `src/routes/teach_api.py`:
  - [ ] POST `/api/teach/start` — start recording
  - [ ] POST `/api/teach/waypoint` — record current position
  - [ ] POST `/api/teach/stop` — stop recording
  - [ ] POST `/api/teach/save` — save with name
  - [ ] GET `/api/teach/sequences` — list saved sequences
  - [ ] POST `/api/teach/replay` — replay a sequence
  - [ ] POST `/api/teach/stop-replay` — stop replay
- [ ] Implement `templates/teach.html`:
  - [ ] Record/Stop/Save buttons
  - [ ] Waypoint list (editable: delete, reorder)
  - [ ] Sequence library (load/delete saved sequences)
  - [ ] Speed slider (0.1×–2.0×)
  - [ ] Loop toggle
- [ ] Implement `static/js/teach_mode.js`:
  - [ ] Record/stop/save/load/replay interactivity
  - [ ] Waypoint list management
- [ ] Test: record 4 waypoints → save → replay → verify arm follows path

## Phase 14: Conveyor Belt Integration (ENABLE_CONVEYOR=true)
- [ ] Wire DC motor: direction → GPIO 17, PWM → GPIO 18, GND
- [ ] Wire speed sensor: GPIO 27 (interrupt)
- [ ] Implement `src/hardware/conveyor.py`:
  - [ ] Motor control: start, stop, set speed (PWM duty)
  - [ ] Speed sensing: pulse count → belt velocity (mm/s)
  - [ ] Direction control
- [ ] Implement lead-time compensation:
  - [ ] Compute: time = distance_to_pick_zone / belt_speed
  - [ ] Pre-position arm at pick zone
  - [ ] Time the grip to intercept the moving object
- [ ] Configure pick zone: `CONVEYOR_PICK_ZONE_MIN_X`, `CONVEYOR_PICK_ZONE_MAX_X`
- [ ] Test: place object on belt → system picks it while belt is moving

## Phase 15: 3D Pose Estimation (ENABLE_3D_POSE=true)
- [ ] Implement `src/vision/pose_estimator.py`:
  - [ ] Estimate object orientation from contour + ArUco reference plane
  - [ ] Return 6-DOF pose (x, y, z, roll, pitch, yaw)
- [ ] Pass full 6-DOF pose to Jacobian IK solver
- [ ] Test: rotated object on table → arm approaches with correct orientation

## Phase 16: Settings & Calibration Dashboard
- [ ] Implement `src/routes/settings.py`:
  - [ ] GET/POST `/api/settings` — read/write settings
  - [ ] POST `/api/calibrate/camera` — trigger camera calibration
  - [ ] POST `/api/calibrate/aruco` — trigger ArUco calibration
  - [ ] GET `/api/system` — CPU temp, memory, disk, uptime
- [ ] Implement `templates/settings.html`:
  - [ ] Arm configuration (DOF, IK solver, gripper type)
  - [ ] Calibration status and recalibrate buttons
  - [ ] Safety zone visualization (2D top-down workspace view)
  - [ ] System info panel

## Phase 17: Deployment & Production
- [ ] Create `deploy/deploy_to_pi.sh`: rsync + venv setup + pip install
- [ ] Create systemd service file (documented in README)
- [ ] Enable and test: `sudo systemctl enable --now pickplace`
- [ ] Test auto-start on boot
- [ ] Test full power cycle: Pi boots → service starts → dashboard accessible

## Phase 18: Testing & Final Validation
- [ ] Run all unit tests: `pytest tests/`
- [ ] Test FK/IK round-trip accuracy across workspace
- [ ] Test all three detection modes (color, shape, TFLite)
- [ ] Test full pick-and-place cycle: detect → pick → place → log
- [ ] Test safety: command point in no-go zone → blocked, e-stop → all stop
- [ ] Test teach mode: record → save → load → replay → loop
- [ ] Test conveyor mode (if hardware available): moving object pick
- [ ] Test mock mode: full dashboard without hardware
- [ ] Test web dashboard on mobile browser (responsive layout)
- [ ] Test rate limiting: 11 failed logins → blocked
- [ ] Verify all `.env` toggles work (enable/disable each feature)
- [ ] Write `docs/threat_model.md`
- [ ] Review and finalize README.md
