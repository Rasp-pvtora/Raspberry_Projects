# ✅ Task List — OPC-UA Industrial Gateway

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

## Phase 2: OPC-UA Server Bootstrap (Day 1–2)
- [ ] Install opcua-asyncio library
- [ ] Implement `opcua_server.py` with asyncio event loop
- [ ] Configure endpoint URI and server name from `.env`
- [ ] Create custom namespace (urn:raspberry:opcua:gateway)
- [ ] Add base folder structure (GPIO/, CAN/, Serial/, Modbus/, Custom/)
- [ ] Implement server start/stop lifecycle management
- [ ] Create status API endpoint
- [ ] Test connection with UaExpert or Prosys OPC-UA Browser

## Phase 3: GPIO Data Source Plugin (Day 2–3)
- [ ] Implement base plugin interface (`plugins/base_plugin.py`)
- [ ] Implement `plugins/gpio_plugin.py` using RPi.GPIO
- [ ] Load GPIO source config from `config/gpio_sources.json`
- [ ] Create OPC-UA Variable nodes for each configured pin
- [ ] Poll GPIO values at configurable interval
- [ ] Update OPC-UA variable values in address space
- [ ] Support digital input, digital output, and DHT22 sensor
- [ ] Test with SCADA client subscribing to GPIO variables

## Phase 4: Database & Node Storage (Day 3)
- [ ] Create SQLite schema with all tables (`init_db.py`)
- [ ] Implement `models.py` with CRUD operations
- [ ] Persist OPC-UA node definitions to database
- [ ] Load node structure from database on startup
- [ ] Create source mapping table for plugin → node bindings
- [ ] Test node persistence across server restarts

## Phase 5: Web Dashboard (Day 3–4)
- [ ] Create `layout.html` base template (dark theme, sidebar nav)
- [ ] Build dashboard with OPC-UA server status card
- [ ] Display active session count and subscription stats
- [ ] Show data source health cards (GPIO/CAN/Serial/Modbus)
- [ ] Add alarm summary widget
- [ ] Create responsive CSS for mobile/tablet
- [ ] Test dashboard on multiple screen sizes

## Phase 6: Address Space Browser (Day 4)
- [ ] Implement `address_space.py` for tree traversal
- [ ] Build tree-view UI with expandable nodes and folders
- [ ] Display node attributes (NodeId, BrowseName, DataType, Value)
- [ ] Add real-time value updates via WebSocket
- [ ] Support node search by browse name or NodeId
- [ ] Add right-click context menu (read, write, history)
- [ ] Test with 100+ nodes in address space

## Phase 7: Dynamic Node Creation (Day 4–5)
- [ ] Implement `node_manager.py` for runtime node CRUD
- [ ] Create node creation API (browse name, data type, parent)
- [ ] Create node deletion API with child cleanup
- [ ] Build node manager UI page with form
- [ ] Support Variable, Object, and Folder node classes
- [ ] Sync created nodes to database
- [ ] Test creating and reading nodes from OPC-UA client

## Phase 8: Data Source Mapping Editor (Day 5)
- [ ] Build drag-and-drop mapping UI
- [ ] List available data source signals (left panel)
- [ ] List OPC-UA nodes (right panel)
- [ ] Create drag-drop connection with optional transform
- [ ] Save mappings to `source_mappings` table
- [ ] Apply mappings at runtime (update OPC-UA values from sources)
- [ ] Support adding/removing mappings without restart
- [ ] Test with GPIO → OPC-UA mapping flow

## Phase 9: Historical Data Access (Day 5–6)
- [ ] Implement `historical_access.py` HDA storage
- [ ] Mark historizing nodes in address space
- [ ] Store time-series values in `historical_data` table
- [ ] Implement OPC-UA HistoryRead service handler
- [ ] Add date-range query API for dashboard
- [ ] Build historical data chart page with Chart.js
- [ ] Configure retention policy (default 90 days)
- [ ] Add data export (CSV, JSON)
- [ ] Test with UaExpert Historian trend view

## Phase 10: CAN Bus Data Source Plugin (Day 6–7)
- [ ] Implement `plugins/can_plugin.py` using python-can
- [ ] Auto-setup SocketCAN interface (if ENABLE_CAN_SOURCE)
- [ ] Load DBC file for signal decoding
- [ ] Create OPC-UA nodes per DBC signal
- [ ] Update node values on CAN frame reception
- [ ] Support CAN → OPC-UA mapping editor integration
- [ ] Test with CAN simulator or automotive ECU

## Phase 11: RS232 Serial Data Source Plugin (Day 7)
- [ ] Implement `plugins/serial_plugin.py` using pyserial
- [ ] Open serial port with configurable baud/parity/databits
- [ ] Parse incoming serial data (CSV, fixed-width, JSON)
- [ ] Create OPC-UA nodes for parsed fields
- [ ] Support send/write via OPC-UA write command
- [ ] Test with serial device or loopback

## Phase 12: Modbus TCP/RTU Data Source Plugin (Day 7–8)
- [ ] Implement `plugins/modbus_plugin.py` using pymodbus
- [ ] Support Modbus TCP and Modbus RTU (via serial)
- [ ] Map holding registers, input registers, coils, discrete inputs
- [ ] Create OPC-UA nodes per configured register
- [ ] Poll at configurable interval
- [ ] Support bi-directional write (OPC-UA → Modbus)
- [ ] Test with Modbus simulator (ModRSsim2 or mbtget)

## Phase 13: Alarms & Conditions (Day 8–9)
- [ ] Implement `alarm_manager.py` with configurable alarm limits
- [ ] Support alarm types: high, hihi, low, lolo, rate-of-change
- [ ] Create OPC-UA Alarm & Condition objects
- [ ] Trigger alarms when node values cross thresholds
- [ ] Implement alarm acknowledgment (OPC-UA + dashboard)
- [ ] Build alarms page with active/historical views
- [ ] Add severity-based filtering and sorting
- [ ] Test alarm trigger/clear/ack cycle

## Phase 14: Certificate Security (Day 9)
- [ ] Implement `cert_manager.py` for X.509 operations
- [ ] Create `scripts/generate_certs.py` for self-signed cert
- [ ] Configure OPC-UA server security policies (Basic256Sha256)
- [ ] Implement certificate trust/reject workflow
- [ ] Build certificates management UI page
- [ ] Auto-reject untrusted client connections
- [ ] Test with secure OPC-UA client connection

## Phase 15: REST API Proxy (Day 9–10)
- [ ] Implement `rest_proxy.py` mapping browse paths to endpoints
- [ ] Support GET → OPC-UA Read
- [ ] Support PUT → OPC-UA Write
- [ ] Auto-generate REST paths from address space structure
- [ ] Return JSON with value, data type, timestamp, quality
- [ ] Add rate limiting to REST proxy
- [ ] Test with curl and non-OPC-UA applications

## Phase 16: Node-RED Integration (Day 10)
- [ ] Install Node-RED and node-red-contrib-opcua
- [ ] Configure Node-RED to connect to local OPC-UA server
- [ ] Embed Node-RED editor via iframe in dashboard
- [ ] Create sample flow (GPIO → OPC-UA → email)
- [ ] Add flow backup/restore functionality
- [ ] Test visual flow programming end-to-end

## Phase 17: CODESYS Runtime Info (Day 10–11)
- [ ] Implement `codesys_info.py` for runtime status display
- [ ] Show CODESYS connection instructions
- [ ] Display OPC-UA Variable → IEC 61131-3 type mapping hints
- [ ] Add CODESYS runtime status polling (if reachable)
- [ ] Build CODESYS info page in dashboard
- [ ] Test with CODESYS GatewayPLC

## Phase 18: Diagnostics & Analytics (Day 11)
- [ ] Implement `diagnostics.py` for server metrics collection
- [ ] Track: active sessions, subscriptions, publish interval, memory
- [ ] Build diagnostics dashboard page with real-time charts
- [ ] Implement `analytics.py` with trend aggregation
- [ ] Build analytics page with alarm frequency, source uptime
- [ ] Add data export for analytics

## Phase 19: Notification System (Day 11–12)
- [ ] Implement `notification_service.py` dispatcher
- [ ] Add Telegram bot notifications
- [ ] Add Slack webhook notifications
- [ ] Add email (SMTP) notifications
- [ ] Trigger on: alarms, node failures, server errors, source disconnect
- [ ] Build notification preference settings UI
- [ ] Test all notification channels

## Phase 20: Feature Toggle System (Day 12)
- [ ] Create `feature_toggles` database table
- [ ] Implement `feature_toggles.py` service
- [ ] Sync toggle state between `.env` ↔ SQLite
- [ ] Build Settings → Feature Toggles dashboard page
- [ ] Add real-time toggle via WebSocket (`toggle_feature` event)
- [ ] Guard each feature module with toggle check
- [ ] Add `PUT /api/settings/features` API endpoint
- [ ] Test toggling features on/off without restart

## Phase 21: Deployment & Hardening (Day 12–13)
- [ ] Build `deploy/deploy_to_pi.sh` deployment script
- [ ] Create `deploy/opcua-gateway.service` systemd unit
- [ ] Generate production TLS certificates
- [ ] Generate production OPC-UA certificates
- [ ] Set file permissions (600 for .env, cert keys)
- [ ] Configure firewall rules (ports 4840, 5000, 1880)
- [ ] Test full deployment on Raspberry Pi

## Phase 22: Testing & Documentation (Day 13–14)
- [ ] Write unit tests for OPC-UA server and node manager
- [ ] Write unit tests for each data source plugin
- [ ] Write unit tests for alarm manager and HDA
- [ ] Write integration tests for API endpoints
- [ ] Test all WebSocket events
- [ ] Test OPC-UA security with signed/encrypted sessions
- [ ] Perform security audit (OWASP top 10 checklist)
- [ ] Verify all .env variables load correctly
- [ ] Test feature toggles enable/disable all features
- [ ] Test with UaExpert, Prosys, and Node-RED OPC-UA client
- [ ] Final documentation review and cleanup
