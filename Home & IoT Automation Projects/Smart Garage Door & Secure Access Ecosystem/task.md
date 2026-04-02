# ✅ Task List — Smart Garage Door & Secure Access Ecosystem

## Phase 1: Project Setup & Authentication (Day 1)
- [ ] Initialize Python project with virtual environment
- [ ] Create `requirements.txt` with all dependencies
- [ ] Set up Flask app skeleton with Flask-SocketIO
- [ ] Create `.env.default` template with all variables
- [ ] Implement bcrypt user authentication system
- [ ] Add login rate limiting (10 attempts / 15 min)
- [ ] Implement JWT session management (24h expiry)
- [ ] Create login page (dark theme)
- [ ] Test auth flow with curl / Postman

## Phase 2: GPIO Relay Control & Reed Switches (Day 1–2)
- [ ] Wire relay module to GPIO 17 & 27
- [ ] Wire reed switches to GPIO 22 & 23
- [ ] Implement `gpio_controller.py` for relay toggling
- [ ] Add reed switch state monitoring with debounce
- [ ] Create door open/close API endpoints
- [ ] Add WebSocket `door_status` real-time push
- [ ] Create auto-close timer background thread
- [ ] Test door open/close cycle end-to-end

## Phase 3: Database & Event Logging (Day 2)
- [ ] Create SQLite schema with all tables (`init_db.py`)
- [ ] Implement `models.py` with CRUD operations
- [ ] Log every door event with trigger source
- [ ] Store plate photos in `data/photos/` directory
- [ ] Create paginated event history API
- [ ] Add event search/filter capabilities
- [ ] Test database operations and migrations

## Phase 4: Web Dashboard (Day 2–3)
- [ ] Create `layout.html` base template (dark theme, sidebar nav)
- [ ] Build dashboard page with door status cards
- [ ] Add last 10 events feed with real-time WebSocket updates
- [ ] Create quick-action buttons (open/close/lock-all)
- [ ] Add responsive CSS for mobile/tablet
- [ ] Implement Chart.js integration scaffolding
- [ ] Test dashboard on multiple screen sizes

## Phase 5: ALPR Integration (Day 3–4)
- [ ] Install OpenALPR or configure Tesseract OCR pipeline
- [ ] Implement `alpr_engine.py` with confidence threshold
- [ ] Add plate detection loop (configurable interval)
- [ ] Create whitelist management CRUD API
- [ ] Build whitelist management UI page
- [ ] Add multi-frame verification (3 consistent reads)
- [ ] Save plate photos on detection
- [ ] Auto-trigger door open for whitelisted plates
- [ ] Test with printed plates and real vehicles

## Phase 6: Camera Stream & Night Mode (Day 4)
- [ ] Set up picamera2 MJPEG streaming server
- [ ] Create authenticated camera feed route
- [ ] Build camera view page with ALPR overlay
- [ ] Implement IR LED control on GPIO 18
- [ ] Add light sensor–based auto night-mode switching
- [ ] Add motion-triggered recording (save clips)
- [ ] Test IR illumination and night capture quality

## Phase 7: Notification System (Day 5)
- [ ] Implement `notification_service.py` dispatcher
- [ ] Add Telegram bot notifications
- [ ] Add Slack webhook notifications
- [ ] Add Microsoft Teams webhook notifications
- [ ] Add email (SMTP) notifications
- [ ] Create notification preference settings UI
- [ ] Add per-event-type notification routing
- [ ] Test all notification channels

## Phase 8: Feature Toggle System (Day 5)
- [ ] Create `feature_toggles` database table
- [ ] Implement `feature_toggles.py` service
- [ ] Sync toggle state between `.env` ↔ SQLite
- [ ] Build Settings → Feature Toggles dashboard page
- [ ] Add real-time toggle via WebSocket (`toggle_feature` event)
- [ ] Guard each feature module with toggle check
- [ ] Add `PUT /api/settings/features` API endpoint
- [ ] Test toggling features on/off without restart

## Phase 9: Guest Access System (Day 6)
- [ ] Implement `guest_access.py` code generator
- [ ] Add PIN-based temporary codes
- [ ] Add QR code generation (qrcode library)
- [ ] Create code validation middleware
- [ ] Build guest code management UI page
- [ ] Add time-bound and max-use enforcement
- [ ] Add code revocation capability
- [ ] Test code lifecycle (generate → use → expire)

## Phase 10: Climate & UPS Monitoring (Day 6–7)
- [ ] Wire DHT22 sensor to GPIO 4
- [ ] Wire MQ-7 CO sensor (analog via MCP3008 or digital)
- [ ] Implement `climate_monitor.py` with polling loop
- [ ] Store readings in `climate_readings` table
- [ ] Wire INA219 on I2C bus
- [ ] Implement `ups_monitor.py` with battery % calculation
- [ ] Add low-battery alert notifications
- [ ] Build climate dashboard page with real-time graphs
- [ ] Test sensor accuracy and calibration

## Phase 11: Analytics Engine (Day 7)
- [ ] Implement `analytics.py` aggregation queries
- [ ] Add daily/weekly/monthly event summaries
- [ ] Calculate peak usage hours
- [ ] Build analytics dashboard page with Chart.js
- [ ] Add usage-by-source pie chart
- [ ] Add month-over-month trend line chart
- [ ] Create export CSV endpoint
- [ ] Test with simulated historical data

## Phase 12: Geofencing & Voice Control (Day 8–9)
- [ ] Implement `geofence.py` with GPS proximity API
- [ ] Create companion endpoint for phone GPS pings
- [ ] Add configurable radius threshold
- [ ] Implement `voice_control.py` base framework
- [ ] Add local Whisper command recognition
- [ ] Add Google Home / Alexa integration hooks
- [ ] Test geofence trigger accuracy
- [ ] Test voice command recognition rate

## Phase 13: Vacation Mode & Emergency Lock (Day 9)
- [ ] Implement `vacation_mode.py` scheduler
- [ ] Add randomized open/close intervals
- [ ] Create vacation mode settings UI
- [ ] Wire emergency button to GPIO 25
- [ ] Implement emergency lock-all function
- [ ] Add emergency lock API + dashboard panic button
- [ ] Configure tamper alarm (vibration sensor → notification + siren)
- [ ] Test vacation simulation schedule
- [ ] Test emergency lock response time

## Phase 14: Multi-Door & Deployment (Day 10)
- [ ] Add multi-door configuration support (up to 4 doors)
- [ ] Create per-door settings and status cards
- [ ] Build `deploy/deploy_to_pi.sh` script
- [ ] Create `deploy/garage-door.service` systemd unit
- [ ] Generate self-signed TLS certificate script
- [ ] Configure HTTPS-only Flask server
- [ ] Test full system with multiple doors
- [ ] Deploy to Raspberry Pi via SSH

## Phase 15: Testing & Hardening (Day 10–11)
- [ ] Write unit tests for auth, doors, ALPR, guest access
- [ ] Write integration tests for API endpoints
- [ ] Test all WebSocket events
- [ ] Perform security audit (OWASP top 10 checklist)
- [ ] Verify all .env variables load correctly
- [ ] Test feature toggles enable/disable all features
- [ ] Verify notifications fire for all event types
- [ ] Load test with simulated concurrent requests
- [ ] Final documentation review and cleanup
