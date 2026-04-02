# ✅ Task List — CAN Bus & CANopen Communication Hub

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

## Phase 2: SocketCAN Auto-Configuration (Day 1–2)
- [ ] Verify MCP2515 SPI overlay in `/boot/config.txt`
- [ ] Implement `can_interface.py` for SocketCAN management
- [ ] Auto-detect CAN interface (can0)
- [ ] Configure bitrate (125k/250k/500k/1M)
- [ ] Support CAN FD data bitrate (optional)
- [ ] Add interface up/down/restart commands
- [ ] Create status endpoint returning interface state
- [ ] Test with `candump can0` and `cansend can0 123#DEADBEEF`

## Phase 3: CAN Receive Loop & Storage (Day 2)
- [ ] Implement `can_receiver.py` using python-can
- [ ] Create non-blocking receive loop in background thread
- [ ] Parse CAN frames (ID, DLC, data, timestamp, flags)
- [ ] Store recent messages in SQLite with circular buffer
- [ ] Implement software message filtering
- [ ] Create paginated message query API
- [ ] Test with simulated CAN traffic (cangen)

## Phase 4: Live Message Viewer (Day 2–3)
- [ ] Emit CAN frames via WebSocket `can_message` event
- [ ] Build live viewer page with scrolling message table
- [ ] Add column display: timestamp, ID (hex), DLC, data (hex), direction
- [ ] Implement pause/resume button
- [ ] Add ID filter input (single ID, range, or mask)
- [ ] Add message rate counter display
- [ ] Color-code by message ID for visual grouping
- [ ] Test with 1000+ msg/sec throughput

## Phase 5: Web Dashboard (Day 3)
- [ ] Create `layout.html` base template (dark theme, sidebar nav)
- [ ] Build dashboard with CAN bus status card
- [ ] Add bus load gauge (percentage)
- [ ] Display message rate (msg/sec)
- [ ] Show error frame counter
- [ ] Add quick-send widget for common frames
- [ ] Create responsive CSS for mobile/tablet
- [ ] Test dashboard on multiple screen sizes

## Phase 6: Message Sender (Day 3–4)
- [ ] Implement `can_sender.py` using python-can
- [ ] Build hex data builder UI (8-byte editor)
- [ ] Support standard (11-bit) and extended (29-bit) IDs
- [ ] Add single-send and repeat mode (interval + count)
- [ ] Add message templates (save/load common frames)
- [ ] Log all sent frames in database
- [ ] Test send with oscilloscope/analyzer verification

## Phase 7: DBC Signal Decoder (Day 4)
- [ ] Implement `dbc_decoder.py` using cantools library
- [ ] Add DBC file upload endpoint with validation
- [ ] Parse DBC messages and signals on upload
- [ ] Auto-decode incoming CAN frames against loaded DBC
- [ ] Display decoded signal names, values, and units
- [ ] Add decoded signals to WebSocket payload
- [ ] Build DBC manager page (upload, list, delete)
- [ ] Test with sample automotive DBC files

## Phase 8: Recorder & Replay (Day 4–5)
- [ ] Implement `recorder.py` with ASC file format writer
- [ ] Add BLF (Binary Logging Format) writer
- [ ] Add CSV writer as alternative
- [ ] Create start/stop recording API
- [ ] Add auto-rotation on max file size
- [ ] Build recorder UI page with file list and download
- [ ] Implement `replay_engine.py` for playback
- [ ] Support speed factor (0.1x to 10x)
- [ ] Add progress tracking via WebSocket
- [ ] Test record → replay cycle end-to-end

## Phase 9: Message Filtering (Day 5)
- [ ] Implement hardware filter (SocketCAN kernel filter)
- [ ] Implement software filter (ID range, mask, DBC signal)
- [ ] Create filter CRUD API endpoints
- [ ] Build filter manager UI page
- [ ] Support multiple active filters simultaneously
- [ ] Apply filters to live viewer + recorder
- [ ] Test with mixed CAN traffic (accept/reject scenarios)

## Phase 10: Bus Diagnostics (Day 5–6)
- [ ] Implement `bus_diagnostics.py` reading CAN controller status
- [ ] Monitor TX/RX error counters via `/sys/class/net/can0/statistics`
- [ ] Calculate bus load percentage from message rate + bitrate
- [ ] Detect bus-off condition and auto-recovery
- [ ] Track error frame count and types
- [ ] Build diagnostics dashboard page with gauges/charts
- [ ] Add bus-off and high-error alerting
- [ ] Emit `bus_diag` WebSocket events periodically
- [ ] Test with intentional bus error injection

## Phase 11: CANopen NMT Manager (Day 6–7)
- [ ] Implement `canopen_nmt.py` using canopen Python library
- [ ] Send NMT commands: Start, Stop, Enter Pre-Operational, Reset
- [ ] Discover nodes using NMT boot-up message (0x700+NodeID)
- [ ] Track node NMT state transitions
- [ ] Build NMT control panel UI (dropdown per node)
- [ ] Add node map visualization
- [ ] Test with CANopen test slave (or canopen-stack simulator)

## Phase 12: CANopen SDO Client (Day 7)
- [ ] Implement `canopen_sdo.py` for expedited & segmented transfers
- [ ] Add SDO upload (read) from node OD entry
- [ ] Add SDO download (write) to node OD entry
- [ ] Support all data types (UNSIGNED8/16/32, INTEGER, VISIBLE_STRING)
- [ ] Handle SDO abort codes and error reporting
- [ ] Build SDO read/write form UI
- [ ] Test with standard OD entries (Device Type 0x1000, etc.)

## Phase 13: CANopen PDO & Heartbeat (Day 7–8)
- [ ] Implement `canopen_pdo.py` for TPDO/RPDO monitoring
- [ ] Parse PDO mapping parameters (0x1A00-0x1A03, 0x1600-0x1603)
- [ ] Display decoded PDO data on dashboard
- [ ] Implement `heartbeat_monitor.py` tracking 0x700+NodeID
- [ ] Configure expected heartbeat interval per node
- [ ] Alert on heartbeat timeout
- [ ] Build PDO mapping viewer UI
- [ ] Test with CANopen motor controller or simulator

## Phase 14: Object Dictionary Browser (Day 8)
- [ ] Implement `od_browser.py` EDS/DCF file parser
- [ ] Build tree-view UI for OD entries (index/subindex/name/type/access)
- [ ] Add EDS file upload and association with node
- [ ] Allow inline SDO read/write from OD browser
- [ ] Display current values next to OD entries
- [ ] Test with standard CANopen EDS files

## Phase 15: CAN↔TCP Bridge (Day 8–9)
- [ ] Implement `tcp_bridge.py` with asyncio TCP server
- [ ] Define wire protocol (length-prefixed JSON or binary CAN frame)
- [ ] Forward received CAN frames to TCP clients
- [ ] Forward TCP client commands to CAN bus
- [ ] Add authentication token for TCP clients
- [ ] Limit max concurrent TCP connections
- [ ] Build bridge status page in dashboard
- [ ] Test with Python TCP client from remote machine

## Phase 16: Analytics Engine (Day 9)
- [ ] Implement `analytics.py` with SQL aggregation queries
- [ ] Calculate message rate trends (per-second/minute/hour)
- [ ] Generate per-ID frequency analysis
- [ ] Track bus load history over time
- [ ] Build analytics dashboard page with Chart.js
- [ ] Add error rate trending
- [ ] Create export CSV endpoint for analytics data
- [ ] Test with 24h simulated traffic data

## Phase 17: Notification System (Day 9–10)
- [ ] Implement `notification_service.py` dispatcher
- [ ] Add Telegram bot notifications
- [ ] Add Slack webhook notifications
- [ ] Add email (SMTP) notifications
- [ ] Trigger on: bus-off, heartbeat timeout, error threshold, bus load %
- [ ] Build notification preference settings UI
- [ ] Test all notification channels

## Phase 18: Feature Toggle System (Day 10)
- [ ] Create `feature_toggles` database table
- [ ] Implement `feature_toggles.py` service
- [ ] Sync toggle state between `.env` ↔ SQLite
- [ ] Build Settings → Feature Toggles dashboard page
- [ ] Add real-time toggle via WebSocket (`toggle_feature` event)
- [ ] Guard each feature module with toggle check
- [ ] Add `PUT /api/settings/features` API endpoint
- [ ] Test toggling features on/off without restart

## Phase 19: Deployment & Hardening (Day 10–11)
- [ ] Build `deploy/deploy_to_pi.sh` deployment script
- [ ] Create `deploy/can-hub.service` systemd unit
- [ ] Auto-load MCP2515 overlay on boot
- [ ] Auto-bring-up can0 interface on boot
- [ ] Generate self-signed TLS certificate script
- [ ] Set file permissions (600 for .env, config files)
- [ ] Test full deployment on Raspberry Pi with CAN HAT

## Phase 20: Testing & Documentation (Day 11–12)
- [ ] Write unit tests for CAN interface and sender/receiver
- [ ] Write unit tests for DBC decoder and recorder
- [ ] Write unit tests for CANopen NMT/SDO/PDO
- [ ] Write integration tests for API endpoints
- [ ] Test all WebSocket events
- [ ] Test with real CAN bus traffic (automotive or industrial)
- [ ] Perform security audit (OWASP top 10 checklist)
- [ ] Verify all .env variables load correctly
- [ ] Test feature toggles enable/disable all features
- [ ] Final documentation review and cleanup
