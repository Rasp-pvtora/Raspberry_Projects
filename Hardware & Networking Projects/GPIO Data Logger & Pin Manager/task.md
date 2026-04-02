# ✅ Task List — GPIO Data Logger & Pin Manager

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

## Phase 2: Pin Configuration File (Day 1–2)
- [ ] Design `pins.default.json` schema with all pin types
- [ ] Implement `pin_config.py` JSON parser and validator
- [ ] Add startup validation (duplicate pin detection, range checks)
- [ ] Sync pins.json → SQLite `pin_configs` table on startup
- [ ] Add bidirectional sync (dashboard changes → pins.json)
- [ ] Implement `POST /api/pins/reload` for runtime config reload
- [ ] Test with various pin configurations (digital, analog, output)

## Phase 3: GPIO Digital Input Reading (Day 2)
- [ ] Implement `gpio_reader.py` using RPi.GPIO library
- [ ] Add `polling_scheduler.py` with per-pin configurable intervals
- [ ] Support pull-up/pull-down resistor configuration
- [ ] Implement debounce logic for button/switch inputs
- [ ] Add pin state caching to reduce redundant reads
- [ ] Implement digital output control (HIGH/LOW toggle)
- [ ] Test with push buttons (GPIO 17, 27) and PIR sensor (GPIO 22)

## Phase 4: Database & Reading Storage (Day 2–3)
- [ ] Create SQLite schema with all tables (`init_db.py`)
- [ ] Implement `models.py` with CRUD operations
- [ ] Implement `sqlite_logger.py` for reading insertion
- [ ] Add batch insert for high-frequency readings
- [ ] Create paginated readings query API
- [ ] Add per-pin reading count and last-read tracking
- [ ] Create indexes for efficient date-range queries
- [ ] Test database operations with simulated data

## Phase 5: Web Dashboard — Dark Theme (Day 3)
- [ ] Create `layout.html` base template (dark theme, sidebar nav)
- [ ] Build dashboard page with per-group pin overview cards
- [ ] Display live values with color-coded status indicators
- [ ] Add WebSocket real-time value updates
- [ ] Create responsive CSS for mobile/tablet
- [ ] Add pin enable/disable quick-toggle on dashboard
- [ ] Test dashboard on multiple screen sizes

## Phase 6: Pin Manager UI (Day 3–4)
- [ ] Build visual GPIO pin header layout (40-pin diagram)
- [ ] Add click-to-assign pin names and types
- [ ] Implement drag-and-drop pin-to-group assignment
- [ ] Add polling interval picker per pin
- [ ] Add threshold configuration sliders
- [ ] Show real-time pin state on the header diagram
- [ ] Sync all changes to pins.json and SQLite
- [ ] Test pin manager with multiple browser sessions

## Phase 7: CSV & JSON Logging (Day 4)
- [ ] Implement `csv_logger.py` with file rotation
- [ ] Add CSV headers: timestamp, pin, value, unit
- [ ] Configure rotation by hours and max file count
- [ ] Implement `json_logger.py` with newline-delimited format
- [ ] Add log directory creation and permission checks
- [ ] Test log rotation and file size management

## Phase 8: MCP3008 ADC Analog Support (Day 4–5)
- [ ] Implement `adc_reader.py` using spidev library
- [ ] Configure SPI bus and chip select
- [ ] Read all 8 MCP3008 channels
- [ ] Apply conversion formulas from pin config
- [ ] Add VREF calibration support
- [ ] Display analog values with units on dashboard
- [ ] Test with soil moisture, LDR, and TMP36 sensors

## Phase 9: Edge-Triggered Logging (Day 5)
- [ ] Implement `edge_detector.py` using GPIO interrupt callbacks
- [ ] Support rising, falling, and both edge detection
- [ ] Log only state changes instead of continuous polling
- [ ] Add bounce time configuration per pin
- [ ] Emit WebSocket `pin_edge` events on state change
- [ ] Test with push buttons and motion sensor

## Phase 10: Threshold Alert System (Day 5–6)
- [ ] Implement `threshold_monitor.py` checking readings against limits
- [ ] Add per-pin high/low threshold configuration
- [ ] Store alerts in `alerts` table with acknowledgment tracking
- [ ] Implement cooldown period to avoid alert flooding
- [ ] Dispatch notifications via Telegram/Slack/Teams/Email
- [ ] Build alerts page with history and acknowledge buttons
- [ ] Add WebSocket `threshold_alert` real-time push
- [ ] Test thresholds with simulated sensor readings

## Phase 11: Real-Time Chart.js Visualization (Day 6)
- [ ] Integrate Chart.js library into dashboard
- [ ] Create live line charts per pin with WebSocket data feed
- [ ] Add bar chart for recent reading distribution
- [ ] Add gauge chart for current analog values
- [ ] Support chart zoom and pan interactions
- [ ] Add time-range selector (1h, 6h, 24h, 7d)
- [ ] Create multi-pin overlay chart
- [ ] Test chart performance with high-frequency data

## Phase 12: Data Retention & Rotation (Day 6–7)
- [ ] Implement `data_retention.py` background scheduler
- [ ] Add configurable retention period (default 90 days)
- [ ] Archive old data before deletion (optional)
- [ ] Purge CSV/JSON files according to policy
- [ ] Compact SQLite database after purge
- [ ] Add retention settings to dashboard
- [ ] Test archive creation and automatic purging

## Phase 13: Data Export Engine (Day 7)
- [ ] Implement `data_export.py` with format selection
- [ ] Add CSV export with date-range and pin filters
- [ ] Add JSON export with the same filters
- [ ] Add SQLite export (full backup or filtered subset)
- [ ] Create export page with date picker and format selector
- [ ] Add background job queue for large exports
- [ ] Emit `export_complete` WebSocket event when done
- [ ] Test exports with large datasets (100k+ readings)

## Phase 14: Analytics Engine (Day 7–8)
- [ ] Implement `analytics.py` with SQL aggregation queries
- [ ] Calculate min/max/avg/stddev per pin per period
- [ ] Generate heatmap data (hour × day-of-week matrix)
- [ ] Create trend line analysis (moving average)
- [ ] Build analytics dashboard page with Chart.js
- [ ] Add pin comparison overlay chart
- [ ] Add CSV export of analytics summaries
- [ ] Test with simulated 90-day historical data

## Phase 15: Pin Grouping (Day 8)
- [ ] Create pin group CRUD API endpoints
- [ ] Add pin-to-group assignment and reassignment
- [ ] Build group management UI page
- [ ] Add per-group dashboard view with collapsed/expanded cards
- [ ] Color-code group indicators on charts
- [ ] Sync group changes to pins.json
- [ ] Test with multiple groups and pin reassignment

## Phase 16: Feature Toggle System (Day 8–9)
- [ ] Create `feature_toggles` database table
- [ ] Implement `feature_toggles.py` service
- [ ] Sync toggle state between `.env` ↔ SQLite
- [ ] Build Settings → Feature Toggles dashboard page
- [ ] Add real-time toggle via WebSocket (`toggle_feature` event)
- [ ] Guard each feature module with toggle check
- [ ] Add `PUT /api/settings/features` API endpoint
- [ ] Test toggling features on/off without restart

## Phase 17: Deployment & Hardening (Day 9)
- [ ] Build `deploy/deploy_to_pi.sh` deployment script
- [ ] Create `deploy/gpio-logger.service` systemd unit
- [ ] Generate self-signed TLS certificate script
- [ ] Configure HTTPS-only Flask server
- [ ] Set file permissions (600 for .env, pins.json)
- [ ] Add log rotation for application logs
- [ ] Test full deployment on Raspberry Pi

## Phase 18: Testing & Documentation (Day 9–10)
- [ ] Write unit tests for pin config parser
- [ ] Write unit tests for GPIO reader and ADC reader
- [ ] Write unit tests for CSV/JSON loggers
- [ ] Write integration tests for API endpoints
- [ ] Test all WebSocket events
- [ ] Perform security audit (OWASP top 10 checklist)
- [ ] Verify all .env variables load correctly
- [ ] Test feature toggles enable/disable all features
- [ ] Load test with simulated concurrent requests
- [ ] Final documentation review and cleanup
