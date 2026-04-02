# ✅ Task List — Smart Pet Feeder & Health Monitor

## Phase 1: Project Setup & Authentication (Day 1)
- [ ] Initialize Python project with virtual environment
- [ ] Create `requirements.txt` with all dependencies
- [ ] Set up Flask app skeleton with Flask-SocketIO
- [ ] Create `.env.default` template with all variables
- [ ] Implement bcrypt user authentication system
- [ ] Add login rate limiting (10 attempts / 15 min)
- [ ] Implement JWT session management (24h expiry)
- [ ] Create login page (dark theme)
- [ ] Test auth flow

## Phase 2: Servo Food Dispenser & Calibration (Day 1–2)
- [ ] Wire MG996R servo to GPIO 12 (PWM)
- [ ] Implement `servo_controller.py` with rotation control
- [ ] Create portion calibration routine (grams ↔ rotation angle)
- [ ] Add software max-portion safety cap
- [ ] Create daily caloric limit per pet
- [ ] Create manual feed API endpoint
- [ ] Test dispenser with measured food portions

## Phase 3: Scheduled Feeding Engine (Day 2)
- [ ] Implement `feeding_scheduler.py` with APScheduler
- [ ] Load per-pet schedules from database
- [ ] Add cron-style feed time configuration
- [ ] Create schedule management API endpoints
- [ ] WebSocket push on feeding events
- [ ] Test scheduled triggers at configured times

## Phase 4: Database & Pet CRUD (Day 2–3)
- [ ] Create SQLite schema with all tables (`init_db.py`)
- [ ] Implement `models.py` with all CRUD operations
- [ ] Create pet profiles CRUD API
- [ ] Implement feeding log storage
- [ ] Add paginated feeding history API
- [ ] Test database operations

## Phase 5: Web Dashboard — Dark Theme (Day 3)
- [ ] Create `layout.html` base template (dark theme, sidebar nav)
- [ ] Build dashboard with pet status cards
- [ ] Add next-feed countdown timers
- [ ] Create quick-feed buttons per pet
- [ ] Implement responsive CSS for mobile/tablet
- [ ] Add WebSocket real-time update listeners
- [ ] Create pet profile management UI
- [ ] Test dashboard across screen sizes

## Phase 6: Weight Tracking — HX711 Load Cell (Day 3–4)
- [ ] Wire HX711 + load cell to GPIO 5 (DT) & 6 (SCK)
- [ ] Create `calibrate_scale.py` interactive calibration tool
- [ ] Implement `weight_tracker.py` with periodic readings
- [ ] Store weight readings in `weight_logs` table
- [ ] Build weight chart page with Chart.js trend line
- [ ] Add manual weight entry endpoint
- [ ] Test accuracy with known weights

## Phase 7: Eating Speed Analysis (Day 4)
- [ ] Implement `eating_analyzer.py` — monitor bowl weight decrease rate
- [ ] Calculate eating speed (grams/second) per feeding
- [ ] Detect fast eating and trigger slow-feed mode
- [ ] Slow-feed mode: pause servo mid-dispense in intervals
- [ ] Log eating speed and duration per feeding
- [ ] Add eating speed column to feeding log UI
- [ ] Test with simulated fast/slow eating patterns

## Phase 8: Water Level & Hopper Monitor (Day 4)
- [ ] Wire HC-SR04 ultrasonic to GPIO 23 (TRIG) & 24 (ECHO)
- [ ] Implement `water_monitor.py` with distance → level conversion
- [ ] Add configurable low-water threshold
- [ ] Wire IR proximity sensor to GPIO 25
- [ ] Implement `hopper_monitor.py` for food level detection
- [ ] Add low-hopper alert notification
- [ ] Display levels on dashboard with gauge widgets
- [ ] Test sensor accuracy and calibration

## Phase 9: Pi Camera Stream & Night Mode (Day 5)
- [ ] Set up picamera2 MJPEG streaming
- [ ] Create authenticated camera feed route
- [ ] Build live camera page in dashboard
- [ ] Wire IR LED array to GPIO 18
- [ ] Implement auto night-mode switching
- [ ] Add motion-triggered snapshot saving
- [ ] Test stream quality and latency

## Phase 10: Pet Facial Recognition (Day 5–6)
- [ ] Collect training photos per pet (GUI upload or CLI)
- [ ] Create `train_pet_model.py` with MobileNetV2 transfer learning
- [ ] Export trained model to TFLite format
- [ ] Implement `pet_recognition.py` inference engine
- [ ] Add confidence threshold filtering
- [ ] Route recognized pet to correct feeding profile
- [ ] Log recognition events with confidence
- [ ] Test with multiple pets and varying conditions

## Phase 11: RFID Collar Tag System (Day 6)
- [ ] Wire MFRC522 to SPI bus + GPIO 22 (RST)
- [ ] Implement `rfid_reader.py` with UID reading loop
- [ ] Register collar tag UIDs to pet profiles
- [ ] Add RFID-authorized feeding: only dispense for registered pet
- [ ] Log unknown tag attempts
- [ ] Build RFID management UI (assign/unassign tags)
- [ ] Test with multiple RFID tags

## Phase 12: Health Alerts & Notifications (Day 7)
- [ ] Implement `health_alerts.py` alert engine
- [ ] Detect missed meals (no feeding within threshold hours)
- [ ] Detect overeating (portion > multiplier × normal)
- [ ] Detect weight change anomalies (> threshold % change)
- [ ] Detect low water and low hopper states
- [ ] Implement `notification_service.py` (Telegram, email)
- [ ] Build health alerts page with acknowledge buttons
- [ ] Test all alert scenarios

## Phase 13: Feature Toggle System (Day 7)
- [ ] Create `feature_toggles` database table
- [ ] Implement `feature_toggles.py` service
- [ ] Sync toggle state between `.env` ↔ SQLite
- [ ] Build Settings → Feature Toggles dashboard page
- [ ] Add real-time toggle via WebSocket
- [ ] Guard each feature module with toggle check
- [ ] Add `PUT /api/settings/features` API endpoint
- [ ] Test toggling features on/off without restart

## Phase 14: Treat Launcher & Medication (Day 8)
- [ ] Wire SG90 treat servo to GPIO 13
- [ ] Implement `treat_launcher.py` with single-shot dispense
- [ ] Build treat game page with camera view + launch button
- [ ] Wire SG90 medication servo to GPIO 19
- [ ] Implement `medication_dispenser.py` with schedule
- [ ] Create medication schedule CRUD API
- [ ] Add medication reminder notifications
- [ ] Test precise single-treat dispensing

## Phase 15: Two-Way Audio (Day 8–9)
- [ ] Set up PyAudio for USB microphone capture
- [ ] Set up pygame for speaker playback
- [ ] Implement `audio_manager.py` with WebSocket audio stream
- [ ] Build audio controls on live camera page
- [ ] Add push-to-talk interface in dashboard
- [ ] Test audio quality and latency

## Phase 16: Analytics & Vet Export (Day 9)
- [ ] Implement `analytics.py` aggregation queries
- [ ] Calculate average portion, feeding frequency, weight trends
- [ ] Build analytics page with Chart.js (bar, line, pie charts)
- [ ] Implement CSV export endpoint
- [ ] Implement PDF vet report generation (reportlab or weasyprint)
- [ ] Add date range selector for exports
- [ ] Test with historical data

## Phase 17: Motion Detection & Activity Log (Day 9)
- [ ] Wire PIR sensor to GPIO 17
- [ ] Implement `motion_detector.py` with callback
- [ ] Log motion events with optional pet identification
- [ ] Add activity timeline to dashboard
- [ ] Trigger camera snapshot on motion
- [ ] Test detection range and false positive rate

## Phase 18: Deployment & Hardening (Day 10)
- [ ] Build `deploy/deploy_to_pi.sh` deployment script
- [ ] Create `deploy/pet-feeder.service` systemd unit
- [ ] Generate self-signed TLS certificate
- [ ] Configure HTTPS-only Flask server
- [ ] Write unit tests for feeding, weight, health, toggles
- [ ] Write integration tests for API endpoints
- [ ] Perform security audit (OWASP checklist)
- [ ] Final documentation review
- [ ] Deploy to Raspberry Pi via SSH
