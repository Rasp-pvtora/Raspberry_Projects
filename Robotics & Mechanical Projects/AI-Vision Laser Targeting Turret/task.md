# Task Tracker
## AI-Vision Laser Targeting Turret

---

## Phase 1: Project Setup & Servo Gimbal Control
- [ ] Flash Raspberry Pi OS (64-bit) to SD card with SSH enabled
- [ ] Boot Pi, connect via `ssh rasp-pi` (192.168.216.90)
- [ ] Run `sudo apt update && sudo apt upgrade -y`
- [ ] Enable camera: `sudo raspi-config` → Interface Options → Camera → Enable
- [ ] Install system dependencies: `sudo apt install python3-pip python3-venv libopencv-dev pigpio -y`
- [ ] Enable and start pigpio daemon: `sudo systemctl enable pigpiod && sudo systemctl start pigpiod`
- [ ] Clone repo and create virtual environment: `python3 -m venv venv && source venv/bin/activate`
- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.default` to `.env` and configure settings
- [ ] Assemble pan-tilt bracket with 2× SG90 servos
- [ ] Mount laser module on tilt bracket (aligned with camera FOV center)
- [ ] Mount Pi Camera on tilt bracket (co-axial with laser)
- [ ] Wire pan servo signal → GPIO 12, tilt servo signal → GPIO 13
- [ ] Wire servo VCC → Pi 5V (pin 2), servo GND → Pi GND (pin 6)
- [ ] (Optional) Wire 3rd servo (yaw) signal → GPIO 18
- [ ] Implement `src/hardware/servo_controller.py` — pigpio init, angle-to-PWM, per-servo control
- [ ] Implement per-servo pulse width calibration (min/max µs from `.env`)
- [ ] Implement home position command (move pan/tilt to center angles)
- [ ] Implement `src/hardware/mock_hardware.py` — simulated servos, laser, GPIO, camera
- [ ] Test: run `python scripts/test_servos.py` — each servo should sweep its range
- [ ] Verify home position centers the gimbal

## Phase 2: Laser Control & Kill Switch
- [ ] Wire visible laser signal → GPIO 17, VCC → 3.3V/5V, GND → GND
- [ ] Wire switching transistor (2N2222/MOSFET) if laser draws >16 mA
- [ ] (Optional) Wire IR laser signal → GPIO 27
- [ ] (Optional) Wire kill switch (N/O) → GPIO 4 (internal pull-up)
- [ ] (Optional) Wire green LED → GPIO 23, red LED → GPIO 24
- [ ] (Optional) Wire buzzer signal → GPIO 22, GND → GND
- [ ] Implement `src/hardware/laser_controller.py`:
  - [ ] `laser_on()` / `laser_off()` for visible laser (GPIO 17)
  - [ ] `ir_laser_on()` / `ir_laser_off()` for IR laser (GPIO 27)
  - [ ] Software kill switch flag (overrides all laser-on)
  - [ ] Laser timeout: auto-off after `LASER_MAX_ON_SEC` continuous seconds
  - [ ] SocketIO broadcast of laser state changes
- [ ] Implement `src/hardware/gpio_controller.py`:
  - [ ] Kill switch GPIO 4 interrupt (falling edge, pull-up)
  - [ ] On trigger: laser off immediately, set kill flag
  - [ ] Status LEDs: green = tracking, red = laser active
  - [ ] Resume: explicit re-enable from dashboard
- [ ] Implement `src/hardware/buzzer_controller.py`:
  - [ ] Active buzzer: on/off via GPIO
  - [ ] Passive buzzer: PWM frequency via pigpio
  - [ ] Pulse pattern: on_ms/off_ms cycle
- [ ] Test: run `python scripts/test_laser.py` — laser on/off, kill switch, timeout
- [ ] Verify kill switch cuts laser immediately when pressed

## Phase 3: Camera Capture & Detection Pipeline
- [ ] Verify camera: `libcamera-hello`
- [ ] Implement `src/vision/camera.py` — Pi Camera capture, frame pipeline, resolution config
- [ ] Implement `src/vision/color_detector.py`:
  - [ ] HSV thresholding with configurable color ranges from `.env`
  - [ ] Contour detection → centroid → bounding box
  - [ ] Return: class label (color name), confidence, centroid (u, v), bbox
- [ ] Implement `src/vision/face_detector.py`:
  - [ ] Haar cascade face detection (cv2.CascadeClassifier)
  - [ ] Optional DNN face detector (OpenCV DNN module)
  - [ ] Return: class "face", confidence, centroid (u, v), bbox
- [ ] Implement `src/vision/motion_detector.py`:
  - [ ] Background subtraction (cv2.createBackgroundSubtractorMOG2)
  - [ ] Contour filtering by min area
  - [ ] Return: class "motion", confidence, centroid (u, v), bbox
- [ ] Implement `src/vision/object_detector.py`:
  - [ ] Haar cascade or TFLite trained model detection
  - [ ] Return: class label, confidence, centroid (u, v), bbox
- [ ] Test all detection modes: place colored objects, show face, move in frame
- [ ] Verify each mode returns `(class, confidence, centroid_u, centroid_v, bbox)`

## Phase 4: Pixel-to-Gimbal Coordinate Mapping
- [ ] Implement `src/targeting/coordinate_mapper.py`:
  - [ ] Linear mapping: pan_angle = pan_home + (u − frame_cx) / PX_PER_DEGREE_PAN
  - [ ] Linear mapping: tilt_angle = tilt_home + (v − frame_cy) / PX_PER_DEGREE_TILT
  - [ ] Load calibration from `.env` (PX_PER_DEGREE_PAN, PX_PER_DEGREE_TILT)
- [ ] Implement `scripts/calibrate_gimbal.py`:
  - [ ] Sweep pan servo across range, record pixel position of laser dot at each angle
  - [ ] Compute pixels-per-degree from linear regression
  - [ ] Repeat for tilt axis
  - [ ] Output calibration values for `.env`
- [ ] Run calibration: `python scripts/calibrate_gimbal.py`
- [ ] Verify: command a pixel coordinate → laser points at that pixel in camera feed
- [ ] Write unit tests: `tests/test_coordinate_mapper.py`

## Phase 5: PID Controller
- [ ] Implement `src/targeting/pid_controller.py`:
  - [ ] PID class with configurable Kp, Ki, Kd
  - [ ] `compute(error, dt)` → output
  - [ ] Anti-windup: clamp integral to `PID_I_MAX`
  - [ ] Output clamping: limit to `PID_OUTPUT_MAX`
  - [ ] Derivative filter: low-pass on D term
  - [ ] `reset()` — clear integral and previous error
  - [ ] `set_gains(kp, ki, kd)` — live gain update
- [ ] Create separate PID instances for pan and tilt axes
- [ ] Write unit tests: `tests/test_pid_controller.py`
  - [ ] Test step response (error → output converges to zero)
  - [ ] Test anti-windup (integral doesn't grow unbounded)
  - [ ] Test gain update (new gains take effect immediately)
  - [ ] Test reset (integral and previous error cleared)

## Phase 6: Tracking Loop Integration
- [ ] Implement `src/control/turret_controller.py`:
  - [ ] Main tracking loop running at `TRACKING_FPS`:
    1. Capture frame
    2. Detect targets (selected mode)
    3. Select primary target (nearest to center, or locked target)
    4. Compute pixel error: `error_u = target_u − frame_cx`, `error_v = target_v − frame_cy`
    5. PID compute: `pan_correction = pid_pan.compute(error_u, dt)`
    6. PID compute: `tilt_correction = pid_tilt.compute(error_v, dt)`
    7. Update servo angles: `pan += pan_correction / PX_PER_DEGREE_PAN`
    8. Safety zone check: if target in safe zone → laser on; else → laser off
    9. Set servo positions via pigpio
    10. Broadcast state via SocketIO
  - [ ] `start()` / `stop()` — begin/end tracking
  - [ ] `manual_aim(u, v)` — point turret at specific pixel
  - [ ] `lock_target()` / `unlock_target()` — target lock toggle
- [ ] Implement `src/control/safety_manager.py`:
  - [ ] Load safety zones from `config/safety_zones.json`
  - [ ] `is_safe(u, v)` → True if point is NOT in any enabled safety zone
  - [ ] `add_zone(name, x_min, y_min, x_max, y_max)` — add zone at runtime
  - [ ] `remove_zone(name)` — remove zone
  - [ ] `toggle_zone(name, enabled)` — enable/disable zone
- [ ] Test: place target → turret tracks and laser stays on target
- [ ] Test: move target into safety zone → laser turns off, servos keep tracking
- [ ] Test: kill switch → laser off immediately
- [ ] Write unit tests: `tests/test_safety_manager.py`

## Phase 7: Web Dashboard — Authentication & Layout
- [ ] Implement `app.py` — Flask + SocketIO entry point
- [ ] Implement `src/services/db.py` — SQLite init with all tables from TSD
- [ ] Implement `src/routes/auth.py`:
  - [ ] Login route with bcrypt password verification
  - [ ] Rate limiting: 10 attempts / 15 min per IP
  - [ ] Session cookie: HttpOnly, SameSite, 24h expiry
  - [ ] Logout route
- [ ] Implement `templates/layout.html` — dark theme base template:
  - [ ] Sidebar navigation (Dashboard, PID Tuning, Camera, Settings)
  - [ ] Kill switch button in header (always visible, red)
  - [ ] System status bar (connection, CPU temp)
- [ ] Implement `templates/login.html` — login form
- [ ] Implement `static/css/style.css`:
  - [ ] Dark theme: background `#1a1a2e`, accent `#0f3460`, card `#16213e`
  - [ ] Responsive layout (sidebar → bottom nav on mobile)
- [ ] Implement `static/js/main.js` — SocketIO connection, kill switch handler
- [ ] Test: login → see dashboard → kill switch button works

## Phase 8: Web Dashboard — Targeting & PID Tuning
- [ ] Implement `src/routes/dashboard.py`:
  - [ ] Dashboard page with live camera feed
  - [ ] SocketIO: stream turret state (pan/tilt angles, laser state, PID errors)
- [ ] Implement `src/routes/control_api.py`:
  - [ ] POST `/api/aim` — manual aim (u, v pixel coordinates)
  - [ ] POST `/api/laser/on` — turn laser on (if safe)
  - [ ] POST `/api/laser/off` — turn laser off
  - [ ] POST `/api/kill` — kill switch (laser off, require re-enable)
  - [ ] POST `/api/resume` — re-enable laser after kill
  - [ ] POST `/api/lock` — lock on nearest target
  - [ ] POST `/api/unlock` — release target lock
  - [ ] POST `/api/home` — return gimbal to home position
  - [ ] GET `/api/state` — current turret state
- [ ] Implement `src/routes/pid_api.py`:
  - [ ] POST `/api/pid/gains` — set PID gains (pan and tilt)
  - [ ] GET `/api/pid/gains` — get current PID gains
  - [ ] POST `/api/pid/preset/save` — save current gains as preset
  - [ ] GET `/api/pid/presets` — list saved presets
  - [ ] POST `/api/pid/preset/load` — load a preset
- [ ] Implement `templates/dashboard.html`:
  - [ ] Live camera feed with crosshair overlay (SocketIO image stream)
  - [ ] Target bounding box + class label overlay
  - [ ] Click-to-aim: click on feed → turret aims there
  - [ ] Laser toggle button
  - [ ] Target lock button
  - [ ] Gimbal position display (pan°, tilt°)
  - [ ] Range estimate display (if enabled)
- [ ] Implement `templates/pid.html`:
  - [ ] Pan P/I/D sliders with real-time update
  - [ ] Tilt P/I/D sliders with real-time update
  - [ ] Step-response graph (Canvas/Chart.js): PID error over time
  - [ ] Preset save/load/delete buttons
  - [ ] Reset PID button (clear integral)
- [ ] Implement `static/js/targeting.js`:
  - [ ] Click-to-aim handler
  - [ ] Laser toggle, lock/unlock buttons
  - [ ] SocketIO state updates (angles, laser, error)
- [ ] Implement `static/js/pid_tuner.js`:
  - [ ] PID slider change → SocketIO emit → live gain update
  - [ ] Step-response chart rendering (error history graph)
  - [ ] Preset management

## Phase 9: Web Dashboard — Camera & Safety Zones
- [ ] Implement `src/routes/vision_api.py`:
  - [ ] SocketIO event: stream camera frames as JPEG (configurable quality)
  - [ ] SocketIO event: stream detection results (class, confidence, bbox)
  - [ ] POST `/api/detect/mode` — change detection mode
  - [ ] GET `/api/detect/modes` — list available modes
- [ ] Implement `templates/camera.html`:
  - [ ] Full camera feed canvas with detection overlay
  - [ ] Detection mode dropdown (color/face/object/motion)
  - [ ] Detection results list
  - [ ] Safety zone overlay (semi-transparent red rectangles)
  - [ ] Draw new safety zone (click-drag on canvas)
  - [ ] Zone list with enable/disable/delete
- [ ] Implement `static/js/camera_feed.js`:
  - [ ] SocketIO image stream → canvas render
  - [ ] Draw bounding boxes and labels overlay
  - [ ] Draw crosshair at frame center
- [ ] Implement `static/js/safety_zones.js`:
  - [ ] Click-drag to draw new zones on canvas
  - [ ] Zone overlay rendering (semi-transparent red)
  - [ ] Zone CRUD (add, toggle, delete) via API

## Phase 10: Multi-Target Mode (ENABLE_MULTI_TARGET=true)
- [ ] Implement `src/targeting/target_tracker.py`:
  - [ ] Track all detected targets across frames (simple centroid tracker)
  - [ ] Assign priority score: class × weight + size × weight + proximity × weight
  - [ ] Select highest-priority target for tracking
  - [ ] Switch to next target when current lost or after dwell timer
  - [ ] Target ID persistence across frames
- [ ] Add multi-target overlay to dashboard (numbered targets with priority)
- [ ] Add target priority config to Settings page
- [ ] Test: multiple colored objects → turret tracks highest priority → switches correctly

## Phase 11: Predictive Aim (ENABLE_PREDICTIVE_AIM=true)
- [ ] Implement `src/targeting/predictive_aim.py`:
  - [ ] Maintain rolling buffer of target positions (last N frames)
  - [ ] Compute velocity (pixels/frame) via linear regression
  - [ ] Compute lead offset: `lead_u = velocity_u × PREDICTION_FRAMES`
  - [ ] Return adjusted target point: (u + lead_u, v + lead_v)
- [ ] Integrate with tracking loop: apply lead before PID input
- [ ] Write unit tests: `tests/test_predictive_aim.py`
  - [ ] Test stationary target → zero lead
  - [ ] Test constant velocity → correct lead
  - [ ] Test direction change → lead adapts

## Phase 12: Session Recording (ENABLE_RECORDING=true)
- [ ] Implement `src/control/session_recorder.py`:
  - [ ] `start_session()` → open VideoWriter + CSV file
  - [ ] `record_frame(frame, state)` → annotate frame, write video + CSV row
  - [ ] `stop_session()` → close files, create DB entry
  - [ ] Annotations: crosshair, target bbox, laser state indicator, PID error text
- [ ] Implement `src/services/session_store.py`:
  - [ ] List sessions from DB
  - [ ] Get session details
  - [ ] Delete session (file + DB)
- [ ] Add recording toggle to dashboard
- [ ] Add session library to Settings page (list, replay, delete)
- [ ] Test: start recording → track target → stop → verify video and CSV files

## Phase 13: Day/Night Mode (ENABLE_DAY_NIGHT=true)
- [ ] Implement `src/vision/day_night.py`:
  - [ ] Compute frame brightness (mean of grayscale)
  - [ ] If brightness < `DAY_NIGHT_THRESHOLD` → night mode
  - [ ] Night: activate IR laser, deactivate visible laser
  - [ ] Night: switch to IR-optimized detection thresholds
  - [ ] Day: visible laser, standard detection
  - [ ] Manual override from dashboard
- [ ] Add day/night indicator to dashboard
- [ ] Add day/night threshold slider to Settings
- [ ] Test: dim lights → mode auto-switches → IR laser activates (verify with NoIR camera)

## Phase 14: Range Estimation (ENABLE_RANGE_ESTIMATION=true)
- [ ] Implement `src/targeting/range_estimator.py`:
  - [ ] `estimate_range(bbox, target_class)` → distance_mm
  - [ ] Formula: `distance = known_size_mm × focal_length_px / apparent_size_px`
  - [ ] Load `known_size_mm` from `config/target_classes.json`
  - [ ] `FOCAL_LENGTH_PX` from `.env`
- [ ] Add range display to dashboard
- [ ] Log range in session CSV
- [ ] Test: place known-size object at measured distances → verify estimation accuracy

## Phase 15: Sound Deterrent (ENABLE_SOUND_DETERRENT=true)
- [ ] Integrate buzzer with tracking loop:
  - [ ] `buzzer_only` mode: buzzer on when target tracked, no laser
  - [ ] `buzzer_and_laser` mode: both buzzer and laser on
  - [ ] `pulsed` mode: buzzer pulses at on_ms/off_ms
- [ ] Add deterrent mode selector to Settings page
- [ ] Test: track target → buzzer activates → verify sound patterns

## Phase 16: Settings & System Info
- [ ] Implement `src/routes/settings.py`:
  - [ ] GET/POST `/api/settings` — read/write settings
  - [ ] GET `/api/system` — CPU temp, memory, disk, uptime
- [ ] Implement `templates/settings.html`:
  - [ ] Detection configuration (mode, thresholds, HSV ranges)
  - [ ] Servo calibration values
  - [ ] Day/night threshold
  - [ ] Recording configuration
  - [ ] Sound deterrent configuration
  - [ ] Safety zone management
  - [ ] System info panel

## Phase 17: Deployment & Production
- [ ] Create `deploy/deploy_to_pi.sh`: rsync + venv setup + pip install
- [ ] Create systemd service file (documented in README)
- [ ] Create pigpiod dependency in systemd unit
- [ ] Enable and test: `sudo systemctl enable --now laserturret`
- [ ] Test auto-start on boot (pigpiod starts before app)
- [ ] Test full power cycle: Pi boots → pigpiod → service starts → dashboard accessible

## Phase 18: Testing & Final Validation
- [ ] Run all unit tests: `pytest tests/`
- [ ] Test PID tracking: stationary target → laser converges to center
- [ ] Test PID tracking: moving target → laser follows with minimal lag
- [ ] Test all four detection modes (color, face, object, motion)
- [ ] Test safety zones: target in zone → laser off, target out → laser on
- [ ] Test kill switch: press button → laser immediately off
- [ ] Test laser timeout: leave laser on → auto-off after `LASER_MAX_ON_SEC`
- [ ] Test multi-target mode: multiple targets → correct prioritization
- [ ] Test predictive aim: fast-moving target → reduced tracking lag
- [ ] Test target lock: lock on target → ignore others
- [ ] Test session recording: video and CSV files generated with correct data
- [ ] Test day/night mode (if IR hardware available): auto-switch works
- [ ] Test range estimation: known object at known distance → correct estimate
- [ ] Test sound deterrent: buzzer-only, buzzer+laser, pulsed modes
- [ ] Test mock mode: full dashboard without hardware
- [ ] Test web dashboard on mobile browser (responsive layout)
- [ ] Test rate limiting: 11 failed logins → blocked
- [ ] Verify all `.env` toggles work (enable/disable each feature)
- [ ] Write `docs/threat_model.md`
- [ ] Write `docs/laser_safety.md`
- [ ] Write `docs/pid_tuning_guide.md`
- [ ] Review and finalize README.md
