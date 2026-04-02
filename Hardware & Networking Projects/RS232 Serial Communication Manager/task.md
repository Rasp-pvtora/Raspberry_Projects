# 📋 Task Breakdown — RS232 Serial Communication Manager

---

## Phase 1: Project Setup & Authentication (Day 1)

- [ ] Create project directory structure
- [ ] Initialize Python virtual environment
- [ ] Create `requirements.txt` with all dependencies
- [ ] Create `.env.example` with all configuration variables
- [ ] Create `src/init_db.py` — database initialization script with all 10 tables
- [ ] Create `src/database.py` — Database class with connection pooling and CRUD helpers
- [ ] Create `src/auth.py` — bcrypt password hashing, JWT generation/validation
- [ ] Create `src/routes/auth_routes.py` — `/api/auth/login`, `/api/auth/logout`
- [ ] Create `src/templates/login.html` — login page with dark theme
- [ ] Implement rate limiting — 10 login attempts per 15 minutes
- [ ] Create admin user on first run (from `.env` credentials)
- [ ] Write `tests/test_auth.py` — login, JWT validation, rate limit tests

---

## Phase 2: Port Manager & Auto-Detection (Day 1–2)

- [ ] Create `src/port_manager.py` — PortManager class with port scanning
- [ ] Implement auto-detection: scan `/dev/ttyUSB*`, `/dev/ttyS*`, `/dev/ttyAMA*`
- [ ] Use `serial.tools.list_ports` for device identification (VID/PID, description)
- [ ] Create `src/port_handler.py` — PortHandler class per open port
- [ ] Implement threaded read loop per port with configurable buffer size
- [ ] Implement thread-safe write queue per port
- [ ] Create `src/routes/port_routes.py` — CRUD + open/close/send/buffer APIs
- [ ] Handle port hot-plug events (detect connect/disconnect)
- [ ] Emit `port_detected` / `port_removed` WebSocket events
- [ ] Support up to `MAX_PORTS` (default 8) simultaneous ports
- [ ] Write `tests/test_port_manager.py` — mock serial port tests

---

## Phase 3: Hex / ASCII Dual View (Day 2–3)

- [ ] Create `src/templates/terminal.html` — dual-pane terminal view
- [ ] Create `static/js/terminal.js` — WebSocket serial data handling
- [ ] Create `static/js/hex_view.js` — hex dump renderer with offset column
- [ ] Implement synchronized scrolling between hex and ASCII panes
- [ ] Color-code TX (green) vs RX (blue) data
- [ ] Add timestamp column for each data chunk
- [ ] Implement send bar — hex input with auto-spacing, ASCII input with escape support
- [ ] Add clear buffer button, auto-scroll toggle, word-wrap toggle
- [ ] Support display modes: hex-only, ascii-only, dual side-by-side
- [ ] Integrate WebSocket `serial_data` event with both views

---

## Phase 4: CRC Calculator & Message Builder (Day 3)

- [ ] Create `src/crc_calculator.py` — CRC-8, CRC-16/Modbus, CRC-16/CCITT, CRC-32
- [ ] Use `crcmod` library for configurable polynomial calculations
- [ ] Create message builder UI component in terminal page
- [ ] Implement frame structure: header field + payload field + CRC selector
- [ ] Auto-calculate and append CRC when CRC type is selected
- [ ] Add byte-level editing with insert/delete/modify
- [ ] Support hex string input validation (reject non-hex chars)
- [ ] Write `tests/test_crc.py` — verify all CRC algorithms against known vectors

---

## Phase 5: Modbus RTU Engine (Day 3–4)

- [ ] Create `src/modbus_rtu.py` — ModbusRTU class
- [ ] Implement FC01 Read Coils (request builder + response parser)
- [ ] Implement FC02 Read Discrete Inputs
- [ ] Implement FC03 Read Holding Registers
- [ ] Implement FC04 Read Input Registers
- [ ] Implement FC05 Write Single Coil
- [ ] Implement FC06 Write Single Register
- [ ] Implement FC15 Write Multiple Coils
- [ ] Implement FC16 Write Multiple Registers
- [ ] Implement Modbus CRC-16 calculation and verification
- [ ] Implement timeout and retry logic (configurable via `.env`)
- [ ] Handle Modbus exception responses (error codes 01–06)
- [ ] Create `src/routes/modbus_routes.py` — all Modbus API endpoints
- [ ] Create `src/templates/modbus.html` — Modbus RTU dashboard
- [ ] Create `static/js/modbus.js` — form-based FC templates, register table view
- [ ] Add register address calculator (decimal ↔ hex conversion)
- [ ] Write `tests/test_modbus.py` — frame building, CRC, parsing tests

---

## Phase 6: Session Recording (Day 4–5)

- [ ] Create `src/session_recorder.py` — SessionRecorder class
- [ ] Record TX/RX data with timestamps to binary file
- [ ] Generate parallel text log with hex + ASCII + timestamps
- [ ] Track recording metadata in `recordings` table
- [ ] Implement max file size limit (configurable via `.env`)
- [ ] Create `src/routes/recording_routes.py` — start/stop/list/download/delete
- [ ] Create `src/templates/recordings.html` — recording management page
- [ ] Add recording indicator in terminal view (red dot when active)
- [ ] Implement retention policy — auto-delete recordings older than N days
- [ ] Write binary replay capability (play back recorded session at original timing)

---

## Phase 7: Auto-Response Rules (Day 5)

- [ ] Create `src/auto_response.py` — AutoResponseEngine class
- [ ] Support match types: `contains`, `starts_with`, `ends_with`, `exact`, `regex`
- [ ] Support hex and ASCII matching patterns
- [ ] Implement configurable response delay
- [ ] Priority-based rule ordering (lower number = higher priority)
- [ ] Per-port filtering (apply rule to specific ports or all)
- [ ] Create `src/routes/response_routes.py` — CRUD for auto-response rules
- [ ] Add rule enable/disable toggle without deletion
- [ ] Emit `auto_response_fired` WebSocket event when rule triggers
- [ ] Write `tests/test_auto_response.py` — pattern matching, priority tests

---

## Phase 8: TCP Bridge (Day 5–6)

- [ ] Create `src/tcp_bridge.py` — TCPBridge class
- [ ] Implement raw mode — direct byte forwarding
- [ ] Implement RFC 2217 basics (baud rate, data size, parity negotiation)
- [ ] Support multiple simultaneous TCP clients per bridge
- [ ] Implement IP whitelist filtering (optional)
- [ ] Add client connection/disconnection tracking
- [ ] Implement inactivity timeout (disconnect idle clients)
- [ ] Create `src/routes/bridge_routes.py` — create/delete/list bridges
- [ ] Create `src/templates/bridge.html` — bridge management page
- [ ] Emit `bridge_client` WebSocket events for client connect/disconnect
- [ ] Write `tests/test_tcp_bridge.py` — connection handling, data forwarding tests

---

## Phase 9: Real-Time Data Plotting (Day 7)

- [ ] Create `src/templates/plotting.html` — Chart.js plotting page
- [ ] Create `static/js/plotting.js` — live chart management
- [ ] Extract numeric values from serial data using configurable regex
- [ ] Support multiple simultaneous plot lines (one per data stream)
- [ ] Implement rolling window (max N points, configurable)
- [ ] Add plot controls: pause, resume, reset, time range selector
- [ ] Support multiple chart types: line, scatter, bar
- [ ] Emit `plot_data` WebSocket events with extracted numeric values
- [ ] Auto-detect numeric patterns in incoming data
- [ ] Add CSV export of plotted data points

---

## Phase 10: Message Macros (Day 7–8)

- [ ] Create `src/routes/macro_routes.py` — CRUD + execute macro APIs
- [ ] Create `src/templates/macros.html` — macro management page
- [ ] Create `static/js/macros.js` — macro editor and quick-send panel
- [ ] Support hex and ASCII macro data
- [ ] Implement repeat count with configurable delay between repeats
- [ ] Add macro categories for organization
- [ ] Quick-send panel in terminal view (sidebar with macro buttons)
- [ ] Optional keyboard hotkey binding per macro
- [ ] Macro sequence support — execute multiple macros in order with delays
- [ ] Import/export macros as JSON file

---

## Phase 11: Port Profiles (Day 8)

- [ ] Create `src/routes/profile_routes.py` — save/load/apply/delete profiles
- [ ] Save complete port configuration as named profile
- [ ] Apply profile to any port with one click
- [ ] Include default profiles: `9600-8N1`, `115200-8N1`, `Modbus-RTU-Default`
- [ ] Profile import/export as JSON
- [ ] Quick-select dropdown in port configuration panel
- [ ] Add profile description field for documentation

---

## Phase 12: Protocol Analyzer (Day 8–9)

- [ ] Create `src/protocol_analyzer.py` — ProtocolAnalyzer class
- [ ] Implement Modbus RTU frame decoder (auto-detect by CRC match)
- [ ] Implement NMEA 0183 sentence parser ($GPGGA, $GPRMC, etc.)
- [ ] Create custom parser configuration format (JSON-based)
- [ ] Create `config/parsers/modbus_rtu.json` — Modbus frame definition
- [ ] Create `config/parsers/nmea_0183.json` — NMEA sentence definitions
- [ ] Create `src/routes/protocol_routes.py` — decode/encode APIs
- [ ] Create `src/templates/protocol.html` — protocol analysis page
- [ ] Display decoded frames inline in terminal view
- [ ] Support loading custom parsers from `config/parsers/` directory
- [ ] Write `tests/test_protocol.py` — decoding accuracy tests

---

## Phase 13: Scripting Engine (Day 9–10)

- [ ] Create `src/scripting_engine.py` — sandboxed Python execution
- [ ] Implement restricted `exec()` with limited builtins
- [ ] Whitelist imports: `time`, `struct`, `binascii`, `re`, `json`
- [ ] Provide scripting API: `serial.send()`, `serial.read()`, `serial.wait()`
- [ ] Implement execution timeout (configurable via `.env`)
- [ ] Create `src/routes/script_routes.py` — save/run/delete scripts
- [ ] Create `src/templates/scripts.html` — code editor with syntax highlighting
- [ ] Create `static/js/scripts.js` — editor with run button and output console
- [ ] Store script output/errors in database for review
- [ ] Add example scripts: Modbus scanner, ping-pong test, stress test
- [ ] Write `tests/test_scripting.py` — sandbox escape prevention tests

---

## Phase 14: Connection Statistics (Day 10)

- [ ] Implement per-port byte counters (TX/RX)
- [ ] Calculate rolling throughput (bytes/sec)
- [ ] Track error counts (parity, framing, overrun)
- [ ] Periodic stats snapshot to `connection_stats` table
- [ ] Create analytics dashboard section with Chart.js bar/line charts
- [ ] Create `src/routes/analytics_routes.py` — stats queries with time ranges
- [ ] Emit `stats_update` WebSocket events (per port, every 2 seconds)
- [ ] Display stats summary in port list and terminal header

---

## Phase 15: Notifications (Day 10–11)

- [ ] Create `src/notification_service.py` — multi-channel notification sender
- [ ] Implement Telegram bot notifications via `python-telegram-bot`
- [ ] Implement Slack webhook notifications
- [ ] Implement email notifications via SMTP
- [ ] Notification triggers: port disconnect, error threshold, pattern match, bridge client
- [ ] Configurable notification cooldown (avoid spam)
- [ ] Notification log in database
- [ ] Test notification button in settings page

---

## Phase 16: Feature Toggles & Settings (Day 11)

- [ ] Create `src/feature_toggles.py` — bidirectional `.env` ↔ SQLite sync
- [ ] Create `src/routes/settings_routes.py` — `GET/PUT /api/settings/features`
- [ ] Create `src/templates/settings.html` — settings page with toggle switches
- [ ] Implement `toggle_feature` / `feature_toggled` WebSocket events
- [ ] Sync toggle changes to `.env` file on disk
- [ ] Load feature states on app startup (DB takes precedence)
- [ ] Conditionally register routes/start services based on feature state
- [ ] Create `static/js/settings.js` — toggle switch UI with confirmation

---

## Phase 17: Dashboard & Dark Theme (Day 11–12)

- [ ] Create `src/templates/layout.html` — base template with navigation
- [ ] Create `src/templates/dashboard.html` — system overview page
- [ ] Create `static/css/style.css` — dark theme (matches existing projects)
- [ ] Create `static/js/main.js` — navigation, WebSocket connection, notifications
- [ ] Add sidebar navigation: Dashboard, Terminal, Modbus, Macros, Plot, Bridge, etc.
- [ ] Dashboard widgets: open ports list, active bridges, recording status, system health
- [ ] Responsive layout for tablet/desktop
- [ ] Port status indicators (green=open, red=error, grey=closed)

---

## Phase 18: Deployment (Day 12)

- [ ] Create `deploy/deploy_to_pi.sh` — automated deployment script
- [ ] Create systemd service file (`serial-manager.service`)
- [ ] Configure firewall rules (port 5000 + TCP bridge ports)
- [ ] Add user to `dialout` group for serial port access
- [ ] Enable UART in Raspberry Pi config
- [ ] Test service start/stop/restart/status
- [ ] Create log rotation configuration
- [ ] Document backup/restore procedure

---

## Phase 19: Testing & Documentation (Day 13–14)

- [ ] Write `tests/test_auth.py` — authentication and authorization tests
- [ ] Write `tests/test_port_manager.py` — port scanning, open/close, send/receive
- [ ] Write `tests/test_crc.py` — all CRC algorithm verification
- [ ] Write `tests/test_modbus.py` — frame building, parsing, exception handling
- [ ] Write `tests/test_tcp_bridge.py` — bridge creation, data forwarding
- [ ] Write `tests/test_auto_response.py` — pattern matching, priority ordering
- [ ] Write `tests/test_protocol.py` — Modbus/NMEA decoding accuracy
- [ ] Write `tests/test_api.py` — full REST API endpoint testing
- [ ] Write `tests/test_scripting.py` — sandbox security tests
- [ ] Test all 16 feature toggles (enable/disable cycle)
- [ ] Test WebSocket events with multiple concurrent clients
- [ ] Cross-check all API responses against TSD specifications
- [ ] Final review: security audit, input validation, error handling
