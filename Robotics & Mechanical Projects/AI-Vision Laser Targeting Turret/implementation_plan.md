# Implementation Plan
## AI-Vision Laser Targeting Turret

---

## Executive Summary

Build a computer-vision-guided 2/3-axis laser targeting turret on Raspberry Pi. Pi Camera detects targets by color, face, trained object, or motion. A PID control loop converts pixel error to servo correction angles, keeping a 5 mW laser pointer centered on moving targets via a pan-tilt SG90 gimbal. pigpio provides hardware-timed PWM for jitter-free servo control. Flask + SocketIO dark-themed web dashboard provides live PID tuning, safety zones, session recording, and manual aim. All features `.env` toggleable.

**Budget:** ~$34–71 | **Timeline:** 5–7 days | **Difficulty:** 6/10

---

## Phase 1: Pi Setup & Servo Gimbal Control (Day 1)

### 1.1 Flash & Configure Pi

```bash
# Flash Raspberry Pi OS (64-bit) with SSH enabled
# Boot, connect, SSH
ssh rasp-pi          # alias for pi@192.168.216.90

# Full system update
sudo apt update && sudo apt upgrade -y

# Enable camera
sudo raspi-config    # Interface Options → Camera → Enable

# Install system dependencies
sudo apt install python3-pip python3-venv libopencv-dev pigpio -y

# Enable and start pigpio daemon (required for hardware-timed PWM)
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### 1.2 Project Setup

```bash
# Clone repo
git clone <repo-url> ~/Projects/LaserTurret
cd ~/Projects/LaserTurret

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.default .env
nano .env    # Set SESSION_SECRET, ADMIN_PASSWORD, PID gains
```

### 1.3 Assemble Gimbal & Wire Servos

Assemble per wiring diagram in README.md:
- Mount 2× SG90 servos on pan-tilt bracket
- Mount laser module on tilt platform (aligned with camera axis)
- Mount Pi Camera on tilt platform (co-axial with laser)
- Pan servo signal → GPIO 12 (hardware PWM0)
- Tilt servo signal → GPIO 13 (hardware PWM1)
- Servo VCC → Pi 5V (pin 2), servo GND → Pi GND (pin 6)
- (Optional) 3rd servo → GPIO 18

### 1.4 Implement Servo Controller

```python
# src/hardware/servo_controller.py
# - Connect to pigpio daemon
# - set_angle(axis, angle) → maps angle to pulse width via pigpio.set_servo_pulsewidth()
# - Per-servo min/max pulse calibration from .env
# - home() → move all axes to configured center angles
# - get_angles() → current pan, tilt (, yaw) angles
# - disable() → set all pulsewidths to 0 (stop servo signal)
```

### 1.5 Implement Mock Hardware

```python
# src/hardware/mock_hardware.py
# - MockServoController: logs commands, tracks virtual angles
# - MockLaserController: logs on/off, tracks state
# - MockCamera: returns sample images with colored circles
# - MockGPIO: logs kill switch, LEDs, buzzer to console
# - All interfaces identical to real hardware
```

### 1.6 Test Servos

```bash
# Test each servo individually
python scripts/test_servos.py
# Pan sweeps 0° → 90° → 180° → 90° with 1-second pauses
# Tilt sweeps 0° → 90° → 180° → 90°
# Verify: smooth movement, no jitter, no binding

# Test home position
python -c "
from src.hardware.servo_controller import ServoController
s = ServoController()
s.home()
print(f'Pan: {s.get_angles()[0]}°, Tilt: {s.get_angles()[1]}°')
"
```

**Milestone:** pigpio drives pan/tilt servos. Home position centers the gimbal.

---

## Phase 2: Laser Control & Kill Switch (Day 1 — Afternoon)

### 2.1 Wire Laser & Kill Switch

Wire per wiring diagram in README.md:
- Laser signal → GPIO 17 (via 2N2222 transistor if >16 mA)
- (Optional) IR laser → GPIO 27
- (Optional) Kill switch (N/O) → GPIO 4 (internal pull-up)
- (Optional) Green LED → GPIO 23, Red LED → GPIO 24
- (Optional) Buzzer → GPIO 22

### 2.2 Implement Laser Controller

```python
# src/hardware/laser_controller.py
# - laser_on() → GPIO 17 HIGH (if not killed)
# - laser_off() → GPIO 17 LOW
# - ir_laser_on() → GPIO 27 HIGH (if not killed)
# - ir_laser_off() → GPIO 27 LOW
# - kill() → immediate off, set kill flag, ignore future on() calls
# - resume() → clear kill flag, allow on() calls
# - _timeout_watchdog() → thread that auto-offs after LASER_MAX_ON_SEC
# - is_on() → current laser state
```

### 2.3 Implement Kill Switch GPIO

```python
# src/hardware/gpio_controller.py
# - GPIO 4: falling edge interrupt → laser_controller.kill()
# - Green LED (GPIO 23): on when tracking, off when idle
# - Red LED (GPIO 24): on when laser active, off when off
# - Interrupt callback runs in separate thread for immediate response
```

### 2.4 Test Laser & Kill Switch

```bash
python scripts/test_laser.py
# 1. Laser ON for 2 seconds → OFF
# 2. Press kill switch during ON → verify immediate OFF
# 3. Laser timeout test: ON for LASER_MAX_ON_SEC → auto OFF
# 4. Resume → laser can be turned ON again

# SAFETY: Wear goggles. Never look into the beam.
```

**Milestone:** Laser toggles via GPIO. Kill switch immediately cuts power. Timeout works.

---

## Phase 3: Camera & Detection Pipeline (Day 2)

### 3.1 Camera Setup

```bash
# Verify camera
libcamera-hello      # Should show camera preview

# OpenCV capture test
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f'Frame: {frame.shape}')
cap.release()
"
```

### 3.2 Implement Detection Modes

```python
# src/vision/color_detector.py — detect_by_color(frame)
# - Convert frame to HSV
# - For each configured color: apply range mask → find contours
# - Filter by min area → compute centroid
# - Return: [(class="red", confidence=1.0, centroid=(u,v), bbox)]

# src/vision/face_detector.py — detect_faces(frame)
# - Load Haar cascade (haarcascade_frontalface_default.xml)
# - Convert to grayscale → detectMultiScale
# - Return: [(class="face", confidence, centroid=(u,v), bbox)]

# src/vision/motion_detector.py — detect_motion(frame)
# - Apply background subtractor (MOG2)
# - Threshold → find contours → filter by min area
# - Return: [(class="motion", confidence, centroid=(u,v), bbox)]

# src/vision/object_detector.py — detect_objects(frame)
# - Haar cascade or TFLite model inference
# - Return: [(class=label, confidence, centroid=(u,v), bbox)]
```

### 3.3 Test Detections

```bash
# Place colored objects in camera view
python -c "
from src.vision.camera import Camera
from src.vision.color_detector import detect_by_color
cam = Camera()
frame = cam.capture()
targets = detect_by_color(frame)
for t in targets:
    print(f'  {t.class_label} at ({t.cx}, {t.cy}), conf={t.confidence:.2f}')
"

# Test face detection
python -c "
from src.vision.camera import Camera
from src.vision.face_detector import detect_faces
cam = Camera()
frame = cam.capture()
faces = detect_faces(frame)
print(f'Detected {len(faces)} faces')
"
```

**Milestone:** All detection modes return target list with class, confidence, centroid.

---

## Phase 4: Pixel-to-Gimbal Mapping & Calibration (Day 2 — Afternoon)

### 4.1 Implement Coordinate Mapper

```python
# src/targeting/coordinate_mapper.py
# - pixel_to_angle(u, v):
#     pan_error_deg = (u - frame_cx) / PX_PER_DEGREE_PAN
#     tilt_error_deg = (v - frame_cy) / PX_PER_DEGREE_TILT
#     return (pan_error_deg, tilt_error_deg)
# - angle_to_pixel(pan_offset, tilt_offset):
#     u = frame_cx + pan_offset * PX_PER_DEGREE_PAN
#     v = frame_cy + tilt_offset * PX_PER_DEGREE_TILT
#     return (u, v)
# - PX_PER_DEGREE_PAN, PX_PER_DEGREE_TILT from .env
```

### 4.2 Calibration Script

```bash
python scripts/calibrate_gimbal.py
# 1. Set pan to home, tilt to home
# 2. Sweep pan in 5° increments (e.g., 60° to 120°)
# 3. At each angle, capture frame and detect laser dot position
# 4. Linear regression: pixel displacement vs angle change → PX_PER_DEGREE_PAN
# 5. Repeat for tilt axis
# 6. Output: "PX_PER_DEGREE_PAN=3.5" and "PX_PER_DEGREE_TILT=3.5"
# 7. User copies values to .env
```

### 4.3 Verify Mapping

```bash
# Manual aim test: command turret to aim at center of frame
python -c "
from src.targeting.coordinate_mapper import CoordinateMapper
from src.hardware.servo_controller import ServoController
mapper = CoordinateMapper()
servo = ServoController()
# Aim at pixel (320, 240) — frame center
pan_angle, tilt_angle = mapper.pixel_to_servo_angle(320, 240)
servo.set_angle('pan', pan_angle)
servo.set_angle('tilt', tilt_angle)
print(f'Aimed at center: pan={pan_angle:.1f}°, tilt={tilt_angle:.1f}°')
"
```

**Milestone:** Calibrated pixel-to-angle mapping. Commanding a pixel = laser hits that pixel.

---

## Phase 5: PID Controller & Tracking Loop (Day 3)

### 5.1 Implement PID Controller

```python
# src/targeting/pid_controller.py
class PIDController:
    def __init__(self, kp, ki, kd, i_max, output_max):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.i_max = i_max
        self.output_max = output_max
        self._integral = 0.0
        self._prev_error = 0.0

    def compute(self, error, dt):
        # Proportional
        p = self.kp * error
        # Integral (with anti-windup)
        self._integral += error * dt
        self._integral = max(-self.i_max, min(self.i_max, self._integral))
        i = self.ki * self._integral
        # Derivative (with low-pass filter)
        d = self.kd * (error - self._prev_error) / dt if dt > 0 else 0
        self._prev_error = error
        # Output (clamped)
        output = p + i + d
        return max(-self.output_max, min(self.output_max, output))

    def set_gains(self, kp, ki, kd):
        self.kp, self.ki, self.kd = kp, ki, kd

    def reset(self):
        self._integral = 0.0
        self._prev_error = 0.0
```

### 5.2 Implement Tracking Loop

```python
# src/control/turret_controller.py — main loop (simplified)
def tracking_loop():
    while running:
        t0 = time.time()
        frame = camera.capture()
        targets = detect(frame, mode=DETECTION_MODE)

        if targets:
            target = select_target(targets)  # nearest or locked
            error_u = target.cx - frame_cx
            error_v = target.cy - frame_cy

            dt = time.time() - last_t
            pan_correction = pid_pan.compute(error_u, dt)
            tilt_correction = pid_tilt.compute(error_v, dt)

            current_pan += pan_correction / PX_PER_DEGREE_PAN
            current_tilt += tilt_correction / PX_PER_DEGREE_TILT

            servo.set_angle('pan', clamp(current_pan, PAN_MIN, PAN_MAX))
            servo.set_angle('tilt', clamp(current_tilt, TILT_MIN, TILT_MAX))

            if safety_manager.is_safe(target.cx, target.cy):
                laser.laser_on()
            else:
                laser.laser_off()
        else:
            pid_pan.reset()
            pid_tilt.reset()
            laser.laser_off()

        socketio.emit('state', get_state())
        dt_loop = time.time() - t0
        sleep(max(0, 1.0/TRACKING_FPS - dt_loop))
```

### 5.3 PID Tuning

```bash
# CLI PID tuning helper
python scripts/tune_pid.py
# 1. Places a stationary target in view
# 2. Starts tracking with current PID gains
# 3. Prints real-time error values
# 4. Allows live gain adjustment via keyboard
# 5. Shows step-response timing (rise time, overshoot, settling time)

# Tuning procedure:
# 1. Set Ki=0, Kd=0
# 2. Increase Kp until oscillation → note Ku (ultimate gain)
# 3. Set Kp = 0.6 × Ku
# 4. Add Kd = Kp × 0.1, increase until oscillation stops
# 5. Add Ki = Kp × 0.01, increase slowly to eliminate offset
```

### 5.4 Unit Tests

```bash
pytest tests/test_pid_controller.py -v
pytest tests/test_coordinate_mapper.py -v

# Integration test: place colored ball → turret tracks → laser stays on target
```

**Milestone:** PID tracking loop keeps laser on moving target. Tunable from CLI.

---

## Phase 6: Safety Manager (Day 3 — Afternoon)

### 6.1 Safety Zone Implementation

```python
# src/control/safety_manager.py
# - Load zones from config/safety_zones.json
# - is_safe(u, v) → True if (u,v) is NOT inside any enabled zone
# - add_zone / remove_zone / toggle_zone
# - Check runs before every laser_on() in tracking loop
```

### 6.2 Safety Zone Config

```json
// config/safety_zones.json
{
  "zones": [
    {
      "name": "doorway",
      "x_min": 0, "y_min": 0,
      "x_max": 100, "y_max": 480,
      "enabled": true
    },
    {
      "name": "window",
      "x_min": 400, "y_min": 0,
      "x_max": 640, "y_max": 200,
      "enabled": true
    }
  ]
}
```

### 6.3 Test Safety

```bash
# Unit tests
pytest tests/test_safety_manager.py -v

# Integration: move target into safety zone → laser turns off
# Move target out → laser turns back on
# Kill switch → laser off, cannot re-enable without resume
```

**Milestone:** Safety zones prevent laser firing in restricted areas. Kill switch is immediate.

---

## Phase 7: Web Dashboard (Day 4–5)

### 7.1 Flask App & Authentication

```python
# app.py
# - Flask app factory
# - SocketIO initialization
# - Blueprint registration (auth, dashboard, control, pid, vision, settings)
# - SQLite database initialization
# - .env loading via python-dotenv
# - Start tracking loop in background thread

# src/routes/auth.py
# - POST /login — bcrypt verify, rate limit 10/15min, set session (24h)
# - GET /logout — clear session
# - @login_required decorator for all other routes
```

### 7.2 Dashboard Layout

```html
<!-- templates/layout.html -->
<!-- Dark theme: background #1a1a2e, accent #0f3460, cards #16213e -->
<!-- Sidebar: Dashboard | PID Tuning | Camera | Settings -->
<!-- Header: project name + KILL SWITCH button (red, always visible) -->
<!-- Footer: connection status, system temp, laser state indicator -->
```

### 7.3 Dashboard Page

```javascript
// static/js/targeting.js
// - Live camera feed via SocketIO (JPEG frames)
// - Crosshair overlay at frame center
// - Target bounding box + class label
// - Click-to-aim: click on feed → emit('aim', {u, v})
// - Laser ON/OFF toggle button
// - Target Lock / Unlock button
// - Gimbal angle display (pan°, tilt°)
// - Range estimate (if enabled)
// - PID error bars (visual error magnitude)
```

### 7.4 PID Tuning Page

```javascript
// static/js/pid_tuner.js
// - Pan: P/I/D sliders (range 0–1 for P/D, 0–0.1 for I)
// - Tilt: P/I/D sliders (same ranges)
// - On slider change → socket.emit('pid_gains', {axis, kp, ki, kd})
// - Server updates PID gains in real-time (no restart)
// - Step-response graph: Canvas chart of PID error vs time
//   - X axis: time (last 5 seconds)
//   - Y axis: pixel error
//   - Two lines: pan error (blue), tilt error (orange)
// - Preset buttons: Save / Load / Delete
// - Reset button: clear PID integral accumulator
```

### 7.5 Camera & Safety Zones Page

```javascript
// static/js/camera_feed.js
// - SocketIO image stream → <canvas> render
// - Draw detection bounding boxes + labels
// - Draw crosshair at frame center

// static/js/safety_zones.js
// - Draw existing zones as semi-transparent red rectangles
// - Click-drag on canvas to create new zone
// - Zone list panel: name, coordinates, enable/disable toggle, delete button
// - POST /api/safety/zones to save changes
```

### 7.6 Settings Page

- Detection configuration (mode, thresholds, HSV ranges)
- Servo calibration values (PX_PER_DEGREE)
- Day/night threshold and override
- Recording toggle and session library
- Sound deterrent mode selector
- System info: CPU temp, memory, disk, uptime

**Milestone:** Full web dashboard with live targeting, PID tuning, safety zones, settings.

---

## Phase 8: Advanced Features (Day 5–6)

### 8.1 Multi-Target Mode

```python
# src/targeting/target_tracker.py
# - Maintain target list across frames (centroid-based ID matching)
# - Priority score = w_class × class_priority + w_size × bbox_area + w_proximity × (1/dist_to_laser)
# - Track highest priority; switch when:
#   a) Current target lost for >1 second
#   b) Dwell timer (MULTI_TARGET_DWELL_SEC) expires
#   c) Higher-priority target appears
# - Dashboard shows all targets numbered by priority
```

### 8.2 Predictive Aim

```python
# src/targeting/predictive_aim.py
# - Rolling buffer of (timestamp, u, v) for tracked target
# - Velocity estimation: linear regression over last PREDICTION_BUFFER_SIZE frames
# - Lead computation: lead_u = vx × PREDICTION_FRAMES / FPS
# - Return adjusted target: (u + lead_u, v + lead_v)
# - Integrate before PID input in tracking loop
```

### 8.3 Target Lock

```python
# src/control/turret_controller.py — lock mode
# - lock_target() → set _locked_target to nearest detection
# - While locked: only track that target (match by position proximity / class)
# - If target lost: wait LOCK_TIMEOUT_SEC → unlock
# - unlock_target() → clear lock, resume priority-based selection
```

### 8.4 Session Recording

```python
# src/control/session_recorder.py
# - start(): open VideoWriter(MJPG) + CSV writer
# - record_frame(frame, state):
#     Annotate frame: crosshair, bbox, laser indicator, PID error text
#     Write frame to video
#     Write CSV row: timestamp, target_u, target_v, error_pan, error_tilt,
#                    pid_pan_out, pid_tilt_out, servo_pan, servo_tilt,
#                    laser_state, target_class, confidence, range_mm
# - stop(): close files, insert into tracking_sessions table
```

### 8.5 Range Estimation

```python
# src/targeting/range_estimator.py
# - estimate(bbox, target_class):
#     known_size = target_classes[class].known_size_mm
#     apparent_size = max(bbox.width, bbox.height)
#     distance = known_size * FOCAL_LENGTH_PX / apparent_size
#     return distance  # mm
```

### 8.6 Day/Night Mode

```python
# src/vision/day_night.py
# - check_ambient(frame):
#     brightness = np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
#     return 'night' if brightness < DAY_NIGHT_THRESHOLD else 'day'
# - switch_mode(mode):
#     if mode == 'night':
#         laser_controller.ir_laser_on()
#         laser_controller.laser_off()
#     else:
#         laser_controller.laser_on()
#         laser_controller.ir_laser_off()
```

### 8.7 Sound Deterrent

```python
# src/hardware/buzzer_controller.py
# - Integration with tracking loop:
#   buzzer_only → buzzer on when tracking, no laser
#   buzzer_and_laser → both active
#   pulsed → buzzer toggles on_ms/off_ms while tracking
```

**Milestone:** All advanced features operational and toggleable.

---

## Phase 9: Deployment & Production (Day 6)

### 9.1 Deploy Script

```bash
# deploy/deploy_to_pi.sh
#!/bin/bash
HOST=${1:-rasp-pi}
DEST=${2:-/home/pi/Projects/LaserTurret}

rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' \
  --exclude='data/' --exclude='config/sessions/' \
  --exclude='__pycache__/' --exclude='*.pyc' \
  ./ ${HOST}:${DEST}/

ssh ${HOST} "cd ${DEST} && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

echo "Deployed to ${HOST}:${DEST}"
```

### 9.2 systemd Service

```bash
sudo tee /etc/systemd/system/laserturret.service << 'EOF'
[Unit]
Description=AI-Vision Laser Targeting Turret
After=network-online.target pigpiod.service
Wants=network-online.target pigpiod.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/LaserTurret
ExecStart=/home/pi/Projects/LaserTurret/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now laserturret
sudo systemctl status laserturret
```

### 9.3 Verify Production

```bash
# Ensure pigpiod starts on boot
sudo systemctl enable pigpiod

# Full power cycle test
sudo reboot
# After boot, verify:
systemctl status pigpiod       # active (running)
systemctl status laserturret   # active (running)
curl http://localhost:5000     # dashboard loads
# Open http://192.168.216.90:5000 from browser
```

**Milestone:** Deployed, auto-starts on boot, full dashboard accessible.

---

## Phase 10: Final Testing & Documentation (Day 6–7)

### 10.1 Unit Tests

```bash
pytest tests/ -v
# test_pid_controller.py — PID response, anti-windup, gain update
# test_coordinate_mapper.py — pixel↔angle mapping accuracy
# test_safety_manager.py — zone checks, kill switch
# test_predictive_aim.py — lead calculation, stationary vs moving
```

### 10.2 Integration Tests

| Test | Expected Outcome |
|---|---|
| Stationary colored target → track | Laser converges to target center within 1–2 sec |
| Moving colored target → track | Laser follows with PID, minimal overshoot |
| Fast-moving target + predictive aim | Reduced tracking lag compared to PID-only |
| Target enters safety zone | Laser OFF, servos continue tracking |
| Target exits safety zone | Laser ON, tracking resumes |
| Kill switch pressed | Laser immediately OFF, cannot re-enable |
| Resume after kill | Laser can be turned ON again |
| Laser timeout (30 sec) | Auto-off triggered, dashboard shows timeout |
| Multi-target: 2 targets visible | Tracks highest priority, switches on dwell timeout |
| Target lock on nearest | Ignores other targets, follows locked target |
| Lock lost (target disappears) | Waits LOCK_TIMEOUT_SEC, then unlocks |
| Session recording | Video + CSV files saved with correct data |
| Day/night switch (dim lights) | IR laser activates, visible laser deactivates |
| Range estimation (known object) | Distance estimate within ±20% of measured distance |
| Sound deterrent (buzzer-only) | Buzzer sounds when tracking, no laser |
| PID gain change via dashboard | Tracking behavior changes immediately |
| 11 failed logins | 12th attempt blocked (rate limit) |
| `ENABLE_MOCK_HARDWARE=true` | Dashboard works without servos, laser, or GPIO |
| Mobile browser | Responsive layout, controls work |

### 10.3 Documentation

- [ ] Finalize README.md (with laser safety section)
- [ ] Write `docs/laser_safety.md` — detailed safety reference
- [ ] Write `docs/pid_tuning_guide.md` — step-by-step PID tuning
- [ ] Write `docs/wiring_diagram.md` — full pin-by-pin reference
- [ ] Write `docs/threat_model.md` — security analysis

**Milestone:** All tests pass, documentation complete, project ready for use.
