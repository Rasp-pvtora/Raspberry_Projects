# Task Tracker
## 🤝 Haptic Feedback Shadow Arm

---

## Phase 1: Project Setup & Basic Mirroring
- [ ] Flash Raspberry Pi OS (64-bit) to SD card with SSH enabled
- [ ] Boot Pi, connect via `ssh rasp-pi` (192.168.216.90)
- [ ] Run `sudo apt update && sudo apt upgrade -y`
- [ ] Enable I2C: `sudo raspi-config` → Interface Options → I2C → Enable
- [ ] Install system dependencies: `sudo apt install python3-pip python3-venv i2c-tools -y`
- [ ] Clone repo and create virtual environment: `python3 -m venv venv && source venv/bin/activate`
- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.default` to `.env` and configure settings
- [ ] Verify I2C bus: `sudo i2cdetect -y 1` (expect: 0x40 PCA9685, 0x48/0x49 ADS1115)
- [ ] Wire ADS1115 #1 (0x48): SDA → GPIO 2, SCL → GPIO 3, VDD → 3.3V, ADDR → GND
- [ ] Wire ADS1115 #2 (0x49): same I2C bus, ADDR → VDD
- [ ] Wire 6 potentiometers to ADS1115 inputs (J1–J4 on #1, J5–J6 on #2)
- [ ] Wire PCA9685: SDA → GPIO 2, SCL → GPIO 3, VCC → 3.3V, GND → GND
- [ ] Connect external 5–6V servo PSU to PCA9685 V+ and GND (bridge GND to Pi)
- [ ] Connect slave arm servos to PCA9685 channels 0–6 (per wiring diagram)
- [ ] Implement `src/master/encoder_reader.py` — ADS1115 init, multi-channel read, EMA filter
- [ ] Test ADC reads: `python scripts/test_adc.py` — all 6 pots should show changing values
- [ ] Implement `src/slave/servo_controller.py` — PCA9685 init, angle-to-PWM, per-channel control
- [ ] Implement per-servo pulse width calibration (min/max µs from `.env`)
- [ ] Test servos: `python scripts/test_servos.py` — each servo sweeps its range
- [ ] Implement `src/control/mirror_engine.py` — main loop: read ADC → map angle → write servo
- [ ] Implement basic calibration: linear ADC-to-angle mapping from `.env` min/max values
- [ ] Implement home position command (move all slave joints to `HOME_POSITION`)
- [ ] Implement `src/hardware/mock_hardware.py` — mock ADC, PCA9685, INA219, DRV2605L, GPIO
- [ ] Test basic mirroring: move master pot → slave servo follows in real-time

## Phase 2: Forward Kinematics & Safety
- [ ] Measure arm link lengths (calipers) and record in `config/dh_params.json`
- [ ] Implement `src/kinematics/dh_params.py` — load DH table from JSON, validate
- [ ] Implement `src/kinematics/forward_kinematics.py` — compute 4×4 homogeneous transform chain
- [ ] Support both 4-DOF and 6-DOF configurations (`ARM_DOF` env var)
- [ ] Write unit tests: `tests/test_forward_kinematics.py`
  - [ ] Test home position → expected end-effector pose
  - [ ] Test known joint angles → known Cartesian position
- [ ] Implement joint angle limits enforcement in mirror engine
- [ ] Wire e-stop button (N/O) to GPIO 4 (pull-up, active LOW)
- [ ] Wire status LEDs: green (GPIO 22), red (GPIO 23)
- [ ] Implement `src/hardware/gpio_controller.py` — e-stop interrupt, LED control
- [ ] Implement e-stop logic: GPIO interrupt → disable all PCA9685 channels → set STOPPED state
- [ ] Implement resume: explicit web button or GPIO reset → re-enable PCA9685

## Phase 3: Joint Calibration (ENABLE_JOINT_CALIBRATION=true)
- [ ] Implement `src/master/calibration.py` — auto-calibration routine
- [ ] Implement joint sweep: prompt operator to move each pot to min/max positions
- [ ] Record ADC values at each limit → save to `config/calibration.json`
- [ ] Implement plateau detection: ADC value stops changing = mechanical end of travel
- [ ] Implement `scripts/calibrate_joints.py` — interactive calibration helper
- [ ] Load calibration data on startup and apply to ADC → angle mapping
- [ ] Test: re-calibrate → verify improved angle accuracy

## Phase 4: Force Feedback — INA219 Current Sensing (ENABLE_FORCE_FEEDBACK=true)
- [ ] Wire INA219 #1 (0x40) in series with J1 slave servo V+ line
- [ ] Wire INA219 #2 (0x41) in series with J2 slave servo V+ line
- [ ] Wire INA219 #3 (0x44) in series with J3 slave servo V+ line
- [ ] Wire INA219 #4 (0x45) in series with J4 slave servo V+ line
- [ ] Verify INA219 addresses: `sudo i2cdetect -y 1` (0x40, 0x41, 0x44, 0x45)
- [ ] Implement `src/slave/current_sensor.py` — INA219 init, read current_mA per sensor
- [ ] Test current reads: `python scripts/test_current.py` — hold servo against resistance → current rises
- [ ] Measure idle current per servo (no-load) → set `FORCE_IDLE_MA` in `.env`
- [ ] Measure stall current per servo → set `FORCE_MAX_MA` in `.env`

## Phase 5: Force Feedback — DRV2605L Haptic Motors
- [ ] Wire DRV2605L: SDA → GPIO 2, SCL → GPIO 3, VIN → 3.3V, GND → GND
- [ ] Connect vibration motor leads to DRV2605L OUT+/OUT−
- [ ] Verify DRV2605L at 0x5A: `sudo i2cdetect -y 1`
- [ ] Implement `src/master/haptic_driver.py` — DRV2605L init, set vibration intensity (0–255)
- [ ] Test haptic motors: `python scripts/test_haptic.py` — motor buzzes at varying intensity
- [ ] Implement `src/control/force_feedback.py`:
  - [ ] Read INA219 current → subtract idle baseline
  - [ ] Map excess current to vibration intensity (linear scale)
  - [ ] Clamp to safe hardware max
  - [ ] Write to DRV2605L
- [ ] Integrate force feedback into mirror engine (step 7–8 of main loop)
- [ ] Test: push against slave arm → feel vibration on master proportional to resistance

## Phase 6: Force Scaling (ENABLE_FORCE_SCALING=true)
- [ ] Implement `src/control/force_scaler.py` — adjustable multiplier (0.1×–5.0×)
- [ ] Expose force scale as SocketIO-settable parameter
- [ ] Test: set scale to 3× → light touch produces strong vibration
- [ ] Test: set scale to 0.2× → heavy load produces mild vibration

## Phase 7: Speed Limiting (ENABLE_SPEED_LIMITING=true)
- [ ] Implement `src/control/speed_limiter.py`:
  - [ ] Compute angle delta per tick
  - [ ] Cap delta at MAX_VELOCITY × dt (per joint)
  - [ ] If master exceeds limit → slave tracks at capped speed, catches up when master slows
- [ ] Integrate speed limiter into mirror engine (step 3 of main loop)
- [ ] Write unit tests: `tests/test_speed_limiter.py`
  - [ ] Test: large angle jump → slave moves smoothly at max velocity
  - [ ] Test: slow movement → no capping applied
- [ ] Test on hardware: move master fast → slave follows smoothly, no jerking

## Phase 8: Precision Mode (ENABLE_PRECISION_MODE=true)
- [ ] Implement `src/control/precision_mode.py`:
  - [ ] When active: target = home + (target − home) / PRECISION_RATIO
  - [ ] Speed limits auto-tighten (multiply by `PRECISION_SPEED_FACTOR`)
- [ ] Add precision mode toggle to dashboard (button + indicator)
- [ ] Test: enable precision mode → master 10° movement → slave 1° movement

## Phase 9: Gripper Mirroring (ENABLE_GRIPPER_MIRRORING=true)
- [ ] Wire FSR with voltage divider to ADS1115 #2, channel A2
- [ ] Implement `src/master/fsr_reader.py` — read FSR analog value, map to squeeze (0.0–1.0)
- [ ] Implement gripper mapping: squeeze → gripper servo angle (open → closed)
- [ ] Implement `src/slave/gripper.py` — set gripper servo on PCA9685 channel 6
- [ ] Integrate into mirror engine: read FSR → map → set gripper servo
- [ ] Test: squeeze master handle → slave gripper closes proportionally

## Phase 10: Collision Detection (ENABLE_COLLISION_DETECTION=true)
- [ ] Create `config/workspace_bounds.json`:
  - [ ] Define rectangular workspace volume (x/y/z min/max)
  - [ ] Define cylindrical exclusion zone around arm base
- [ ] Implement `src/control/collision_detector.py`:
  - [ ] FK(target_angles) → end-effector (x, y, z)
  - [ ] Check position against workspace bounds
  - [ ] Warning threshold: alert when within `COLLISION_WARNING_MARGIN_MM`
  - [ ] Hard limit: block command if outside bounds
  - [ ] Emergency stop if `COLLISION_ESTOP_ENABLED=true` and bounds exceeded
- [ ] Integrate into mirror engine (step 5 of main loop)
- [ ] Write unit tests: `tests/test_collision_detector.py`
  - [ ] Test position inside bounds → allowed
  - [ ] Test position outside bounds → blocked
  - [ ] Test position at warning margin → warning emitted
- [ ] Test on hardware: move master toward boundary → slave stops at limit

## Phase 11: Web Dashboard — Authentication & Layout
- [ ] Implement `app.py` — Flask + SocketIO entry point
- [ ] Implement `src/services/db.py` — SQLite init with all tables from TSD
- [ ] Implement `src/routes/auth.py`:
  - [ ] Login route with bcrypt password verification
  - [ ] Rate limiting: 10 attempts / 15 min per IP
  - [ ] Session cookie: HttpOnly, SameSite, 24h expiry
  - [ ] Logout route
- [ ] Implement `templates/layout.html` — dark theme base template:
  - [ ] Sidebar navigation (Dashboard, Force Feedback, Recording, Settings)
  - [ ] E-stop button in header (always visible, red)
  - [ ] System status bar (connection, CPU temp)
- [ ] Implement `templates/login.html` — login form
- [ ] Implement `static/css/style.css`:
  - [ ] Dark theme: background `#1a1a2e`, accent `#0f3460`, card `#16213e`
  - [ ] Responsive layout (sidebar → bottom nav on mobile)
- [ ] Implement `static/js/main.js` — SocketIO connection, e-stop handler
- [ ] Test: login → see dashboard → e-stop button works

## Phase 12: Web Dashboard — 3D Visualization (ENABLE_WORKSPACE_VISUALIZATION=true)
- [ ] Implement `templates/dashboard.html`:
  - [ ] Three.js 3D canvas for arm visualization
  - [ ] Master/slave joint angle readouts (side-by-side)
  - [ ] Force feedback current graphs
  - [ ] System status panel
- [ ] Implement `src/routes/dashboard.py`:
  - [ ] Dashboard page route
  - [ ] SocketIO events: arm_state (master + slave angles, currents, force intensities)
- [ ] Implement `static/js/three_visualizer.js`:
  - [ ] Load Three.js from CDN
  - [ ] Build arm model from DH parameters (cylinders for links, spheres for joints)
  - [ ] Render both master (blue) and slave (green) arms
  - [ ] Update joint rotations from SocketIO state at update rate
  - [ ] Color joint segments by force feedback intensity (green → yellow → red)
  - [ ] Show workspace boundaries as translucent volumes
  - [ ] OrbitControls for camera rotation/zoom
- [ ] Implement `static/js/force_panel.js`:
  - [ ] Per-joint current bar chart (real-time)
  - [ ] Force scaling slider (0.1×–5.0×)
  - [ ] Force idle/max threshold adjustment
- [ ] Implement `src/routes/control_api.py`:
  - [ ] POST `/api/estop` — emergency stop
  - [ ] POST `/api/resume` — resume from e-stop
  - [ ] POST `/api/precision` — toggle precision mode
  - [ ] POST `/api/force-scale` — set force scaling multiplier
  - [ ] GET `/api/state` — current mirror engine state
- [ ] Implement `static/js/safety_panel.js`:
  - [ ] E-stop button (red, large)
  - [ ] Precision mode toggle + indicator
  - [ ] Collision warning indicators
  - [ ] Resume button (after e-stop)

## Phase 13: Web Dashboard — Recording & Playback (ENABLE_RECORDING_PLAYBACK=true)
- [ ] Implement `src/control/recorder.py`:
  - [ ] `start_recording()` — begin capturing timestamped frames
  - [ ] Each frame: {t_ms, master_angles[], gripper, force_intensities[]}
  - [ ] `stop_recording()` — finalize recording
  - [ ] `save_recording(name)` — persist to `config/recordings/` + DB
  - [ ] `load_recording(name)` — load from file
- [ ] Implement `src/control/player.py`:
  - [ ] `replay_recording(name, speed_scale)` — play back at configurable speed
  - [ ] `loop_recording(name, speed_scale)` — repeat until stopped
  - [ ] `stop_playback()` — halt replay
  - [ ] During playback: mirror engine sources angles from recording instead of ADC
- [ ] Implement `src/services/recording_store.py` — recording metadata persistence
- [ ] Implement `src/routes/recording_api.py`:
  - [ ] POST `/api/recording/start` — start recording
  - [ ] POST `/api/recording/stop` — stop recording
  - [ ] POST `/api/recording/save` — save with name
  - [ ] GET `/api/recording/list` — list saved recordings
  - [ ] POST `/api/recording/replay` — replay a recording
  - [ ] POST `/api/recording/stop-replay` — stop replay
  - [ ] DELETE `/api/recording/<id>` — delete recording
- [ ] Implement `templates/recording.html`:
  - [ ] Record/Stop/Save buttons
  - [ ] Recording list (Name, Duration, Frame count, Date)
  - [ ] Load/Delete/Replay per recording
  - [ ] Speed slider (0.1×–5.0×)
  - [ ] Loop toggle
- [ ] Implement `static/js/recording_ui.js`:
  - [ ] Record/stop/save interactivity
  - [ ] Recording list management
  - [ ] Replay controls + progress bar
- [ ] Test: record 5 seconds → save → replay → verify slave follows recorded path

## Phase 14: Web Dashboard — Settings & Calibration
- [ ] Implement `src/routes/settings.py`:
  - [ ] GET/POST `/api/settings` — read/write settings
  - [ ] POST `/api/calibrate` — trigger joint calibration routine
  - [ ] GET `/api/system` — CPU temp, memory, disk, uptime
- [ ] Implement `templates/settings.html`:
  - [ ] Arm configuration display (DOF, feature toggles)
  - [ ] Calibration status and recalibrate button
  - [ ] Precision mode config (ratio, speed factor)
  - [ ] Collision bounds editor (workspace volume min/max)
  - [ ] Force feedback thresholds (idle/max mA)
  - [ ] System info panel

## Phase 15: Network Teleoperation (ENABLE_NETWORK_TELEOPERATION=true)
- [ ] Implement `src/control/network_teleop.py`:
  - [ ] SocketIO server mode (slave side): listen for joint_state events
  - [ ] SocketIO client mode (master side): emit joint_state + receive force_data
  - [ ] Timestamped packets with sequence numbers
  - [ ] Predictive buffering: buffer last N packets, extrapolate on stall
  - [ ] Smooth blend back to live data when packets resume
  - [ ] Latency measurement: round-trip time display
- [ ] Configure `.env`: `TELEOP_SERVER_HOST`, `TELEOP_SERVER_PORT`, `TELEOP_BUFFER_SIZE`
- [ ] Test on LAN: master Pi → slave Pi, verify smooth mirroring with <50 ms latency
- [ ] Test stall recovery: disconnect network briefly → slave extrapolates → reconnect smoothly

## Phase 16: Deployment & Production
- [ ] Create `deploy/deploy_to_pi.sh`: rsync + venv setup + pip install
- [ ] Create systemd service file (documented in README)
- [ ] Enable and test: `sudo systemctl enable --now shadowarm`
- [ ] Test auto-start on boot
- [ ] Test full power cycle: Pi boots → service starts → dashboard accessible

## Phase 17: Testing & Final Validation
- [ ] Run all unit tests: `pytest tests/`
- [ ] Test basic mirroring: 6 joints mirror accurately with <30 ms latency
- [ ] Test force feedback: push slave arm → feel proportional vibration on master
- [ ] Test force scaling: 0.2× dampens, 3× amplifies vibration
- [ ] Test speed limiting: fast master movement → slave tracks smoothly at capped speed
- [ ] Test precision mode: 10:1 ratio → fine slave movements
- [ ] Test gripper mirroring: FSR squeeze → slave gripper closes proportionally
- [ ] Test collision detection: move toward boundary → slave stops
- [ ] Test recording/playback: record → save → load → replay → loop
- [ ] Test e-stop: GPIO button → all servos disable instantly; web button → same
- [ ] Test joint calibration: run routine → verify min/max angle accuracy
- [ ] Test network teleoperation (if second Pi available): LAN mirroring + force feedback
- [ ] Test mock mode: full dashboard without hardware
- [ ] Test web dashboard on mobile browser (responsive layout)
- [ ] Test rate limiting: 11 failed logins → blocked
- [ ] Verify all `.env` toggles work (enable/disable each feature)
- [ ] Write `docs/threat_model.md`
- [ ] Review and finalize README.md
