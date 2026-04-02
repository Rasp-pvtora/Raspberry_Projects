# ✅ Task List — IoT-Based Smart Aquaponics Optimizer

## Phase 1: Project Setup & Authentication (Day 1)
- [ ] Initialize Python project with virtual environment
- [ ] Create `requirements.txt` with all dependencies
- [ ] Set up Flask app skeleton with Flask-SocketIO
- [ ] Create `.env.default` template with all ~90 variables
- [ ] Implement bcrypt user authentication system
- [ ] Add login rate limiting (10 attempts / 15 min)
- [ ] Implement JWT session management (24h expiry)
- [ ] Create login page (dark theme)
- [ ] Test auth flow

## Phase 2: Atlas Scientific Sensor Integration (Day 1–2)
- [ ] Install `atlas-i2c` library
- [ ] Implement `sensors/atlas_ph.py` — pH probe reading on I2C 0x63
- [ ] Implement `sensors/atlas_ec.py` — EC probe reading on I2C 0x64
- [ ] Implement `sensors/atlas_do.py` — DO probe reading on I2C 0x61
- [ ] Create calibration scripts (`calibrate_ph.py`, `calibrate_ec.py`, `calibrate_do.py`)
- [ ] Add sensor reading loop with configurable intervals
- [ ] Test all three Atlas sensors end-to-end

## Phase 3: Temperature Probes & Thermal Control (Day 2)
- [ ] Wire DS18B20 probes on 1-Wire bus (GPIO 4)
- [ ] Implement `sensors/ds18b20.py` — multi-probe temperature reading
- [ ] Implement `controllers/temp_controller.py` — heater/chiller relay logic
- [ ] Add hysteresis band to prevent relay cycling
- [ ] Configure target temperature + tolerance from .env
- [ ] Test heater ON/OFF at threshold boundaries

## Phase 4: Database & Data Logging Pipeline (Day 2–3)
- [ ] Create SQLite schema with all tables (`init_db.py`)
- [ ] Implement `models.py` with all CRUD operations
- [ ] Install and configure InfluxDB 2.x (optional)
- [ ] Implement `influxdb_client.py` — write sensor data to InfluxDB
- [ ] Create dual-write pipeline: SQLite (relational) + InfluxDB (time-series)
- [ ] Test data persistence and retrieval

## Phase 5: Web Dashboard — Dark Theme (Day 3–4)
- [ ] Create `layout.html` base template (dark theme, sidebar nav)
- [ ] Build dashboard page with health score gauge (0–100)
- [ ] Add sensor reading cards (pH, EC, DO, temp) with color coding
- [ ] Create quick-action buttons (feed fish, dose pH, trigger top-off)
- [ ] Implement Chart.js real-time line charts for sensor history
- [ ] Add WebSocket listeners for live sensor updates
- [ ] Create responsive CSS for mobile/tablet
- [ ] Test dashboard across screen sizes

## Phase 6: pH Auto-Dosing System (Day 4)
- [ ] Wire peristaltic pump 1 (pH-up) to relay/GPIO 25
- [ ] Wire peristaltic pump 2 (pH-down) to relay/GPIO 5
- [ ] Implement `controllers/dosing_controller.py` with PID-like logic
- [ ] Add dose amount cap (max ml per cycle)
- [ ] Add cooldown timer between doses (min 5 minutes)
- [ ] Add daily total dose limit safety
- [ ] Log all dosing events with before/after values
- [ ] Create manual dose API endpoints
- [ ] Test auto-dosing response to pH drift

## Phase 7: Grow Light PWM Control (Day 4–5)
- [ ] Wire LED grow light to GPIO 12 via MOSFET
- [ ] Implement `controllers/light_controller.py` with PWM dimming
- [ ] Add photoperiod scheduler (on/off times)
- [ ] Create light schedule management API
- [ ] Add manual intensity override from dashboard
- [ ] Build grow light status UI widget
- [ ] Test intensity levels 0–100%

## Phase 8: Water Flow Sensor (Day 5)
- [ ] Wire YF-S201 flow sensor to GPIO 16
- [ ] Implement `sensors/flow_sensor.py` with pulse counting
- [ ] Convert pulses to liters-per-minute
- [ ] Add low-flow alert threshold
- [ ] Log flow rate to InfluxDB
- [ ] Display flow rate on dashboard with alert indicator
- [ ] Test with running circulation pump

## Phase 9: Water Level & Auto Top-Off (Day 5)
- [ ] Wire HC-SR04 to GPIO 20 (TRIG) & 21 (ECHO)
- [ ] Implement `sensors/water_level.py` with distance → level conversion
- [ ] Wire solenoid valve to relay/GPIO 24
- [ ] Implement `controllers/topoff_controller.py` with max-duration safety
- [ ] Add manual top-off API endpoint
- [ ] Display water level gauge on dashboard
- [ ] Test solenoid open/close and safety timeout

## Phase 10: Air Pump Control (Day 5–6)
- [ ] Wire air pump to relay/GPIO 22
- [ ] Implement `controllers/air_pump.py` with on/off scheduling
- [ ] Add day/night schedule configuration
- [ ] Create air pump status UI widget
- [ ] Test relay switching and schedule

## Phase 11: Fish Feeder Servo (Day 6)
- [ ] Wire SG90 servo to GPIO 13 (PWM)
- [ ] Implement `controllers/fish_feeder.py` with portion control
- [ ] Add APScheduler feeding schedule (configurable times)
- [ ] Create manual feed API endpoint
- [ ] Log all feedings to database
- [ ] Build feeding log page in dashboard
- [ ] Test portion dispensing accuracy

## Phase 12: Feature Toggle System (Day 6)
- [ ] Create `feature_toggles` database table
- [ ] Implement `feature_toggles.py` service with 20 features
- [ ] Sync toggle state between `.env` ↔ SQLite
- [ ] Build Settings → Feature Toggles dashboard page
- [ ] Add real-time toggle via WebSocket
- [ ] Guard each feature module with toggle check
- [ ] Add `PUT /api/settings/features` API endpoint
- [ ] Test toggling features on/off without restart

## Phase 13: Notification System (Day 7)
- [ ] Implement `notification_service.py` dispatcher
- [ ] Add Telegram bot notifications
- [ ] Add email (SMTP) notifications
- [ ] Create per-alert-type notification routing
- [ ] Add notification preferences in settings page
- [ ] Test all notification channels

## Phase 14: System Health Score Engine (Day 7)
- [ ] Implement `health_score.py` with weighted composite algorithm
- [ ] Configure weights from .env (pH 20%, temp 20%, DO 20%, EC 15%, flow 15%, level 10%)
- [ ] Create scoring rules per component (see TSD algorithm)
- [ ] Log health score to InfluxDB every minute
- [ ] Build health score gauge widget on dashboard
- [ ] Add color coding: green (80–100), yellow (50–79), red (0–49)
- [ ] Trigger alerts when score drops below thresholds
- [ ] Test with various sensor scenarios

## Phase 15: Camera Stream (Day 7–8)
- [ ] Set up picamera2 MJPEG streaming
- [ ] Create authenticated camera feed route
- [ ] Build camera view page (fish tank + grow beds)
- [ ] Add snapshot-on-demand functionality
- [ ] Test stream quality and latency

## Phase 16: Fish Counter — OpenCV (Day 8)
- [ ] Implement `ai/fish_counter.py` with OpenCV blob detection
- [ ] Add background subtraction for moving fish
- [ ] Tune detection parameters for underwater camera
- [ ] Log fish count with confidence score
- [ ] Display count on fish tank dashboard page
- [ ] Test with different fish densities and lighting

## Phase 17: Plant Health CNN (Day 8–9)
- [ ] Collect/source leaf photos (healthy, disease, deficiency categories)
- [ ] Create `train_plant_model.py` with MobileNetV2 transfer learning
- [ ] Export to TFLite format
- [ ] Implement `ai/plant_health.py` inference engine
- [ ] Schedule periodic plant health checks (camera snapshot → inference)
- [ ] Log results with issue classification
- [ ] Build plant health status cards on grow beds page
- [ ] Test with various leaf conditions

## Phase 18: Ammonia Prediction ML Model (Day 9–10)
- [ ] Collect sensor history for training data
- [ ] Implement `ai/ammonia_predictor.py` with scikit-learn RandomForest
- [ ] Features: pH trend, temp, DO, EC, feeding frequency, time-of-day
- [ ] Train model to predict NH3 levels 6–12 hours ahead
- [ ] Export model to pickle (`.pkl`)
- [ ] Schedule prediction runs every hour
- [ ] Trigger alert if predicted NH3 exceeds safe threshold
- [ ] Build prediction chart on predictions page
- [ ] Test with historical data patterns

## Phase 19: Auto Nutrient Dosing (Day 10)
- [ ] Wire nutrient pump 1 to relay/GPIO 5
- [ ] Wire nutrient pump 2 to relay/GPIO 6
- [ ] Implement nutrient dosing in `controllers/dosing_controller.py`
- [ ] Add EC-based auto-dosing (if EC < target, dose nutrients)
- [ ] Add configurable dosing intervals and amounts
- [ ] Log nutrient dosing events
- [ ] Create nutrient dosing settings UI
- [ ] Test EC response after dosing

## Phase 20: Solar Monitor (Day 10–11)
- [ ] Wire INA219 to I2C bus (0x40)
- [ ] Implement `sensors/solar_monitor.py` with voltage/current/power reading
- [ ] Log solar data to InfluxDB
- [ ] Build solar & energy dashboard page
- [ ] Add daily/weekly energy production charts
- [ ] Calculate energy self-sufficiency percentage
- [ ] Test with solar panel connected

## Phase 21: Grafana Integration (Day 11)
- [ ] Create Grafana datasource for InfluxDB
- [ ] Design `aquaponics-overview.json` dashboard
- [ ] Design `water-chemistry.json` dashboard
- [ ] Embed Grafana iframes in web dashboard
- [ ] Export dashboard JSON files for distribution
- [ ] Test responsive Grafana embeds

## Phase 22: Predictive Maintenance Engine (Day 11–12)
- [ ] Implement `predictive_maintenance.py`
- [ ] Detect pump degradation (declining flow rate trend)
- [ ] Detect sensor drift (readings diverging from cross-sensor correlation)
- [ ] Detect filter clogging (flow rate vs pump power correlation)
- [ ] Schedule water change reminders based on water chemistry trends
- [ ] Build maintenance task list page
- [ ] Test with simulated degradation patterns

## Phase 23: Multi-Bed / Multi-Tank Support (Day 12)
- [ ] Add `systems` table with configurable beds/tanks
- [ ] Route sensor readings to correct system
- [ ] Create per-system dashboard views
- [ ] Add system selector dropdown in UI
- [ ] Configure GPIO mapping per system
- [ ] Test with 2 simulated systems

## Phase 24: Weather API Integration (Day 12)
- [ ] Implement `weather_service.py` with OpenWeatherMap API
- [ ] Fetch outdoor temperature, humidity, UV index
- [ ] Influence grow light schedule based on daylight hours
- [ ] Adjust temperature target based on outdoor conditions
- [ ] Display weather widget on dashboard
- [ ] Test with configurable city/coordinates

## Phase 25: Harvest Tracking & Yield Prediction (Day 13)
- [ ] Implement `harvest_tracker.py` with harvest logging
- [ ] Add plant growth timeline tracking
- [ ] Implement `ai/yield_predictor.py` using growth curve models
- [ ] Build harvest log page with yield trends
- [ ] Add crop planning suggestions based on historical data
- [ ] Test with simulated harvest data

## Phase 26: Deployment & Hardening (Day 13–14)
- [ ] Build `deploy/deploy_to_pi.sh` deployment script
- [ ] Create `deploy/aquaponics.service` systemd unit
- [ ] Generate self-signed TLS certificate
- [ ] Configure HTTPS-only Flask server
- [ ] Write unit tests (auth, sensors, dosing, health score, toggles)
- [ ] Write integration tests for API endpoints
- [ ] Test all WebSocket events
- [ ] Perform security audit (OWASP checklist)
- [ ] Verify dose safety caps and rate limits
- [ ] Verify solenoid max-duration safety
- [ ] Final documentation review
- [ ] Deploy to Raspberry Pi via SSH
