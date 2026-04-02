# Task Tracker
## 🕷️ Spider-Bot Hexapod Terrain Adaptation

---

## Phase 1: Project Setup & Dual PCA9685 Servo Control
- [ ] Flash Raspberry Pi OS (64-bit) to SD card with SSH enabled
- [ ] Boot Pi, connect via `ssh rasp-pi` (192.168.216.90)
- [ ] Run `sudo apt update && sudo apt upgrade -y`
- [ ] Enable I2C: `sudo raspi-config` → Interface Options → I2C → Enable
- [ ] Enable SPI: `sudo raspi-config` → Interface Options → SPI → Enable
- [ ] Enable camera: `sudo raspi-config` → Interface Options → Camera → Enable
- [ ] Install system dependencies: `sudo apt install python3-pip python3-venv libopencv-dev i2c-tools -y`
- [ ] Clone repo and create virtual environment: `python3 -m venv venv && source venv/bin/activate`
- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.default` to `.env` and configure settings
- [ ] Wire PCA9685 Board 1 (0x40): SDA → GPIO 2, SCL → GPIO 3, VCC → 3.3V, GND → GND
- [ ] Wire PCA9685 Board 2 (0x41): same I2C bus, bridge A0 pad for address 0x41
- [ ] Connect BEC (5V/5A output) to both PCA9685 V+ and GND (bridge GND to Pi)
- [ ] Verify both PCA9685 boards: `sudo i2cdetect -y 1` (expect `0x40` and `0x41`)
- [ ] Connect 18 leg servos to PCA9685 channels per wiring diagram
- [ ] Connect 2 pan/tilt servos to Board 2 channels 9–10
- [ ] Implement `src/hardware/servo_controller.py` — dual PCA9685 init, (board, channel) addressing, angle-to-PWM
- [ ] Implement per-servo pulse width calibration (min/max µs from `.env`)
- [ ] Implement `src/hardware/mock_hardware.py` — simulated servos, IMU, FSR, ultrasonic, INA219, camera
- [ ] Test: run `python scripts/test_servos.py` — each of 18 servos should sweep individually
- [ ] Implement home position command (move all joints to neutral angles)
- [ ] Verify all servos reach home position without binding or collision

## Phase 2: Leg Geometry & Per-Leg Inverse Kinematics
- [ ] Measure leg link lengths with calipers: coxa, femur, tibia (mm)
- [ ] Measure leg mount positions on body: (x, y) offset from center, mount angle for each leg
- [ ] Create `config/leg_geometry.json` with measured values
- [ ] Implement `src/kinematics/leg_config.py` — load geometry from JSON, per-leg mount offsets
- [ ] Implement `src/kinematics/leg_ik.py` — 3-DOF IK solver:
  - [ ] Coxa angle: θ₁ = atan2(y, x)
  - [ ] Project into leg plane: r = sqrt(x² + y²) − L_coxa
  - [ ] Tibia angle via law of cosines
  - [ ] Femur angle via atan2 decomposition
  - [ ] Joint limit enforcement
  - [ ] Reachability check
- [ ] Implement `src/kinematics/body_ik.py` — body-level IK:
  - [ ] Apply body translation (tx, ty, tz) and rotation (roll, pitch, yaw)
  - [ ] Compute per-leg foot positions in local leg frames
  - [ ] Call per-leg IK for each leg
- [ ] Write unit tests: `tests/test_leg_ik.py`
  - [ ] Test home position → expected joint angles
  - [ ] Test reachable foot points → valid angles
  - [ ] Test unreachable points → error returned
  - [ ] Test joint limit enforcement
- [ ] Write unit tests: `tests/test_body_ik.py`
  - [ ] Test body translation → feet compensate
  - [ ] Test body rotation → all legs produce valid IK
  - [ ] Test level body at various heights
- [ ] Manual test: set foot position per leg → verify physical servo positions match expected

## Phase 3: Gait Engine
- [ ] Implement `src/gait/gait_engine.py` — gait state machine:
  - [ ] Per-leg state: SUPPORT → LIFT → SWING → DOWN → SUPPORT
  - [ ] Phase timing: configurable percentages per state
  - [ ] Gait cycle synchronized clock
- [ ] Implement `src/gait/gait_patterns.py`:
  - [ ] Tripod gait: legs {1,4,5} and {2,3,6} alternate
  - [ ] Wave gait: one leg at a time, sequence 1→2→3→4→5→6
  - [ ] Ripple gait: pairs (1,4) → (2,5) → (3,6)
  - [ ] Free gait: load custom sequences from JSON
- [ ] Implement `src/gait/speed_controller.py`:
  - [ ] Adjustable speed scale (0.1–2.0)
  - [ ] Adjustable stride length and step height
  - [ ] Turn radius control (spin in place to wide arc)
- [ ] Integrate gait engine with leg IK:
  - [ ] Each cycle step → compute foot targets → body IK → per-leg IK → servo commands
- [ ] Test tripod gait: hexapod walks forward on flat surface
- [ ] Test wave gait: hexapod walks slowly with max stability
- [ ] Test ripple gait: hexapod walks at medium speed
- [ ] Test turning: spin in place, arc turns left/right
- [ ] Test speed control: slow → fast transitions
- [ ] Write unit tests: `tests/test_gait_engine.py`
  - [ ] Test state transitions
  - [ ] Test phase timing
  - [ ] Test all three gait patterns produce valid foot sequences

## Phase 4: IMU Stabilization (ENABLE_IMU_STABILIZATION=true)
- [ ] Wire MPU6050: SDA → GPIO 2, SCL → GPIO 3, VCC → 3.3V, GND → GND
- [ ] Verify: `sudo i2cdetect -y 1` (expect `0x68`)
- [ ] Implement `src/sensors/imu.py`:
  - [ ] Initialize MPU6050 via adafruit-circuitpython-mpu6050
  - [ ] Read accelerometer (ax, ay, az) and gyroscope (gx, gy, gz)
  - [ ] Complementary filter: angle = α × (angle + gyro × dt) + (1−α) × accel_angle
  - [ ] Return stable pitch and roll at configured rate
- [ ] Implement `src/stabilization/pid_controller.py`:
  - [ ] Generic PID class: set_gains(Kp, Ki, Kd), compute(setpoint, measurement)
  - [ ] Anti-windup: clamp integral term
  - [ ] Derivative low-pass filter
- [ ] Implement `src/stabilization/body_leveler.py`:
  - [ ] Read IMU pitch/roll
  - [ ] PID pitch: correction_pitch = PID(target=0, measured=pitch)
  - [ ] PID roll: correction_roll = PID(target=0, measured=roll)
  - [ ] Feed corrections to body IK (roll=−correction_roll, pitch=−correction_pitch)
  - [ ] Clamp corrections to MAX_TILT_CORRECTION_DEG
- [ ] Create `config/pid_tuning.json` with default PID gains
- [ ] Test: tilt the hexapod body → body IK compensates → legs adjust to keep body level
- [ ] Tune PID gains: reduce oscillation, minimize steady-state error
- [ ] Write unit tests: `tests/test_pid.py`
  - [ ] Test PID step response
  - [ ] Test anti-windup
  - [ ] Test derivative filter

## Phase 5: FSR Terrain Adaptation (ENABLE_TERRAIN_ADAPTATION=true)
- [ ] Wire MCP3008: SPI0 (CLK → GPIO 11, DOUT → GPIO 9, DIN → GPIO 10, CS → GPIO 8)
- [ ] Connect FSR ×6 to MCP3008 channels 0–5 (with 10kΩ voltage dividers)
- [ ] Implement `src/sensors/fsr.py`:
  - [ ] Initialize MCP3008 via spidev
  - [ ] Read FSR values (0–1023) for each channel
  - [ ] Software low-pass filter for noise reduction
  - [ ] Return per-foot force values
- [ ] Integrate terrain adaptation into gait DOWN phase:
  - [ ] During DOWN: extend tibia incrementally
  - [ ] Stop when FSR exceeds contact threshold
  - [ ] Limit max extension to FSR_MAX_EXTENSION_MM
- [ ] Test FSR readings: `python scripts/test_fsr.py` — press each foot, verify ADC values
- [ ] Test terrain adaptation: place hexapod on uneven surface → legs auto-adjust
- [ ] Verify: feet on higher ground have shorter extension, lower ground has longer extension

## Phase 6: Battery Management (ENABLE_BATTERY_MANAGEMENT=true)
- [ ] Wire INA219: SDA → GPIO 2, SCL → GPIO 3, VIN+ → LiPo (+), VIN− → PDB (+)
- [ ] Verify: `sudo i2cdetect -y 1` (expect `0x44`)
- [ ] Implement `src/sensors/battery.py`:
  - [ ] Initialize INA219 via adafruit-circuitpython-ina219
  - [ ] Read bus voltage, shunt current, power
  - [ ] Calculate per-cell voltage (bus_voltage / 3)
  - [ ] Warning threshold: 3.5V/cell → emit warning event
  - [ ] Critical threshold: 3.3V/cell → trigger auto-return, reduce speed
- [ ] Test: `python scripts/test_battery.py` — verify voltage/current readings
- [ ] Implement low-battery actions: reduce speed, disable non-essential features, trigger return-home

## Phase 7: Ultrasonic Navigation (ENABLE_AUTONOMOUS_NAV=true)
- [ ] Wire HC-SR04 ×3: front (GPIO 17/27), left (GPIO 22/23), right (GPIO 24/25)
- [ ] Implement `src/sensors/ultrasonic.py`:
  - [ ] Trigger pulse → measure echo time → compute distance (cm)
  - [ ] Read all 3 sensors (sequential, ~20ms each)
  - [ ] Software median filter (3 readings) for noise rejection
- [ ] Implement `src/navigation/obstacle_avoidance.py`:
  - [ ] If front < OBSTACLE_STOP_CM → stop → compare left/right → turn toward open side → resume
  - [ ] If front < OBSTACLE_SLOW_CM → reduce speed
- [ ] Implement `src/navigation/wall_follower.py`:
  - [ ] PID on side sensor distance → maintain WALL_FOLLOW_DISTANCE_CM
  - [ ] Left-wall or right-wall mode
- [ ] Implement `src/navigation/return_home.py`:
  - [ ] Dead-reckoning: integrate gait steps (stride × count × heading)
  - [ ] On low battery → compute reverse heading → walk back to approximate start
- [ ] Test: `python scripts/test_ultrasonic.py` — verify distances with ruler
- [ ] Test obstacle avoidance: place obstacle in front → hexapod stops and turns
- [ ] Test wall following: hexapod maintains distance from wall

## Phase 8: FPV Camera (ENABLE_FPV_CAMERA=true)
- [ ] Verify camera: `libcamera-hello`
- [ ] Implement `src/hardware/camera.py`:
  - [ ] Open Pi Camera via OpenCV VideoCapture
  - [ ] Capture frames at configured resolution and FPS
  - [ ] JPEG encode for SocketIO streaming
- [ ] Implement `src/hardware/pan_tilt.py`:
  - [ ] Control pan servo (Board 2 ch 9) and tilt servo (Board 2 ch 10)
  - [ ] Home to center on startup
  - [ ] Smooth movement with interpolation
- [ ] Integrate camera with dashboard (SocketIO MJPEG stream)
- [ ] Test: camera feed visible on dashboard, pan/tilt responsive to controls

## Phase 9: Web Dashboard — Authentication & Layout
- [ ] Implement `app.py` — Flask + SocketIO entry point
- [ ] Implement `src/routes/auth.py`:
  - [ ] Login route with bcrypt password verification
  - [ ] Rate limiting: 10 attempts / 15 min per IP
  - [ ] Session cookie: HttpOnly, SameSite, 24h expiry
  - [ ] Logout route
- [ ] Implement `templates/layout.html` — dark theme base template:
  - [ ] Sidebar navigation (Dashboard, Gait, Camera, Navigation, Settings)
  - [ ] E-stop button in header (always visible, red)
  - [ ] System status bar (connection, battery, CPU temp)
- [ ] Implement `templates/login.html` — login form
- [ ] Implement `static/css/style.css`:
  - [ ] Dark theme: background `#1a1a2e`, accent `#0f3460`, card `#16213e`
  - [ ] Responsive layout (sidebar → bottom nav on mobile)
- [ ] Implement `static/js/main.js` — SocketIO connection, e-stop handler
- [ ] Test: login → see dashboard → e-stop button works

## Phase 10: Web Dashboard — 3D Visualization & Gait Control
- [ ] Implement `static/js/three_viz.js`:
  - [ ] Three.js scene: hexapod body + 6 legs as segments
  - [ ] Update leg positions from SocketIO joint state at 20 Hz
  - [ ] Color-coded: green (support), blue (swing), red (overload)
  - [ ] Mouse orbit/zoom controls (OrbitControls)
- [ ] Implement `src/routes/gait_api.py`:
  - [ ] POST `/api/gait/start` — start walking with selected pattern
  - [ ] POST `/api/gait/stop` — stop walking (park in standing pose)
  - [ ] POST `/api/gait/pattern` — switch gait pattern (tripod/wave/ripple/free)
  - [ ] POST `/api/gait/speed` — set speed scale
  - [ ] POST `/api/gait/turn` — set turn radius
  - [ ] GET `/api/gait/state` — current gait pattern, speed, leg states
- [ ] Implement `src/routes/control_api.py`:
  - [ ] POST `/api/body/translate` — body translation (x, y, z)
  - [ ] POST `/api/body/rotate` — body rotation (roll, pitch, yaw)
  - [ ] POST `/api/leg/{id}/position` — manual single-leg foot position
  - [ ] POST `/api/estop` — emergency stop (all servos to neutral)
  - [ ] POST `/api/resume` — resume from e-stop
  - [ ] GET `/api/state` — all joint angles, IMU, FSR, battery, ultrasonic
- [ ] Implement `templates/dashboard.html`:
  - [ ] Three.js 3D hexapod visualization canvas
  - [ ] Gait pattern selector (dropdown/buttons)
  - [ ] Speed slider
  - [ ] Body translate/rotate joystick
  - [ ] IMU pitch/roll indicators
  - [ ] Battery voltage/current display
- [ ] Implement `static/js/gait_control.js`:
  - [ ] Gait pattern buttons (tripod/wave/ripple)
  - [ ] Start/stop walking buttons
  - [ ] Speed slider (0.1× – 2.0×)
  - [ ] Stride length and step height sliders
- [ ] Implement `static/js/body_control.js`:
  - [ ] Virtual joystick for body translation (x/y)
  - [ ] Height slider (body z)
  - [ ] Roll/pitch/yaw sliders for body rotation

## Phase 11: Web Dashboard — Camera & Navigation
- [ ] Implement `src/routes/camera_api.py`:
  - [ ] SocketIO event: stream camera frames as JPEG
  - [ ] POST `/api/camera/pan` — set pan angle
  - [ ] POST `/api/camera/tilt` — set tilt angle
  - [ ] POST `/api/camera/home` — center camera
- [ ] Implement `templates/camera.html`:
  - [ ] Live FPV camera canvas
  - [ ] Pan/tilt sliders or joystick
  - [ ] Snapshot button (download current frame)
- [ ] Implement `static/js/camera_feed.js`:
  - [ ] SocketIO image stream → canvas render
  - [ ] Pan/tilt control → API calls
- [ ] Implement `src/routes/nav_api.py`:
  - [ ] POST `/api/nav/mode` — set navigation mode (manual/avoid/wall-follow/return)
  - [ ] GET `/api/nav/sensors` — current ultrasonic distances
  - [ ] GET `/api/nav/status` — navigation state, heading, estimated position
- [ ] Implement `templates/nav.html`:
  - [ ] Navigation mode selector
  - [ ] Sensor distance readout (front/left/right bars)
  - [ ] Top-down heading indicator
  - [ ] Start/stop autonomous mode buttons
- [ ] Implement `static/js/nav_panel.js`:
  - [ ] Mode toggle buttons
  - [ ] Real-time sensor distance bars
  - [ ] Heading compass widget

## Phase 12: Gait Recording & Replay (ENABLE_GAIT_RECORDING=true)
- [ ] Implement `src/gait/gait_recorder.py`:
  - [ ] `start_recording()` — begin capturing gait frames
  - [ ] Capture: all 18 joint angles + timing per gait step
  - [ ] `stop_recording()` — finalize sequence
  - [ ] `save_recording(name)` — persist to `config/gait_sequences/{name}.json` + DB
  - [ ] `load_recording(name)` — load from file
  - [ ] `replay_recording(name, speed_scale)` — play as "free" gait
- [ ] Implement `src/routes/record_api.py`:
  - [ ] POST `/api/record/start` — start recording
  - [ ] POST `/api/record/stop` — stop recording
  - [ ] POST `/api/record/save` — save with name
  - [ ] GET `/api/record/list` — list saved recordings
  - [ ] POST `/api/record/replay` — replay a recording
  - [ ] POST `/api/record/stop-replay` — stop replay
  - [ ] DELETE `/api/record/{name}` — delete a recording
- [ ] Add gait recording controls to `templates/gait.html`:
  - [ ] Record/Stop/Save buttons
  - [ ] Recording list with Load/Delete/Replay
  - [ ] Speed slider for replay
- [ ] Test: walk in tripod gait → record → save → switch to free gait → replay → hexapod repeats recorded pattern

## Phase 13: Settings & Calibration Dashboard
- [ ] Implement `src/routes/settings.py`:
  - [ ] GET/POST `/api/settings` — read/write settings
  - [ ] POST `/api/calibrate/servos` — trigger servo calibration wizard
  - [ ] POST `/api/calibrate/imu` — IMU zero/calibrate
  - [ ] GET `/api/system` — CPU temp, memory, disk, uptime, battery
- [ ] Implement `templates/settings.html`:
  - [ ] Leg geometry display and editor
  - [ ] PID tuning sliders (Kp, Ki, Kd for pitch and roll)
  - [ ] Servo calibration tool (select servo → test sweep → set min/max)
  - [ ] Feature toggle switches (mirror `.env` ENABLE_* flags)
  - [ ] System info panel
- [ ] Implement `static/js/battery_panel.js`:
  - [ ] Battery voltage bar graph (color-coded: green/yellow/red)
  - [ ] Current draw graph (sparkline)
  - [ ] Per-leg current display (if additional INA219 present)

## Phase 14: Deployment & Production
- [ ] Create `deploy/deploy_to_pi.sh`: rsync + venv setup + pip install
- [ ] Create systemd service file (documented in README)
- [ ] Enable and test: `sudo systemctl enable --now spiderbot`
- [ ] Test auto-start on boot
- [ ] Test full power cycle: Pi boots → service starts → dashboard accessible

## Phase 15: Testing & Final Validation
- [ ] Run all unit tests: `pytest tests/`
- [ ] Test per-leg IK accuracy: command foot positions → measure with ruler
- [ ] Test all three gait patterns on flat ground
- [ ] Test terrain adaptation on uneven surface (books, ramps)
- [ ] Test IMU stabilization: tilt surface → body stays level
- [ ] Test battery monitoring: verify voltage/current readings match multimeter
- [ ] Test autonomous obstacle avoidance: place obstacles → hexapod avoids
- [ ] Test wall following: hexapod maintains parallel to wall
- [ ] Test FPV camera: stream visible, pan/tilt responsive
- [ ] Test gait recording: record → save → replay cycle
- [ ] Test Three.js visualization: 3D model matches physical hexapod pose
- [ ] Test e-stop: press e-stop → all servos go to neutral immediately
- [ ] Test mock mode: full dashboard without hardware (`ENABLE_MOCK_HARDWARE=true`)
- [ ] Test web dashboard on mobile browser (responsive layout)
- [ ] Test rate limiting: 11 failed logins → blocked
- [ ] Verify all `.env` toggles work (enable/disable each feature)
- [ ] Write `docs/threat_model.md`
- [ ] Review and finalize README.md
