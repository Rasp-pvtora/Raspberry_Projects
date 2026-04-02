# Task List — PLC Replacement with OpenPLC

## Phase 1 — Project Foundation & OpenPLC Setup

- [ ] **1.1 Initialize project structure**
  - [ ] Create directory tree (`src/`, `templates/`, `static/css/`, `static/js/`, `tests/`, `deploy/`, `scripts/`, `docs/`, `data/`, `programs/`)
  - [ ] Create `pyproject.toml` with project metadata
  - [ ] Create `requirements.txt` with all dependencies
  - [ ] Create `.env.example` with all variables and defaults
  - [ ] Create `src/__init__.py`
  - [ ] Create `tests/__init__.py` and `tests/conftest.py`

- [ ] **1.2 Implement configuration loader**
  - [ ] Create `src/config.py` with dataclass for all `.env` variables
  - [ ] Load and validate `.env` using `python-dotenv`
  - [ ] Type conversion for int, float, bool values
  - [ ] Parse `MCP23017_ADDRESSES` comma-separated hex list
  - [ ] Parse `RATE_LIMIT` into count/window tuple
  - [ ] Defaults for all optional settings
  - [ ] Feature-toggle helper method (`is_enabled("feature_name")`)

- [ ] **1.3 Implement SQLite database module**
  - [ ] Create `src/database.py` with connection manager
  - [ ] Enable WAL mode on connection
  - [ ] Create `io_states` table schema
  - [ ] Create `data_logs` table schema
  - [ ] Create `programs` table schema
  - [ ] Create `alarms` table schema
  - [ ] Create `settings` table schema
  - [ ] Implement `init_db()` to create all tables
  - [ ] Implement CRUD helpers for each table
  - [ ] Implement parameterized queries for all DB operations

- [ ] **1.4 Create OpenPLC Runtime install script**
  - [ ] Create `scripts/install_openplc.sh`
  - [ ] Clone OpenPLC Runtime repository
  - [ ] Compile runtime for Raspberry Pi (Linux ARM)
  - [ ] Configure runtime to use Pi GPIO pins
  - [ ] Create systemd service for OpenPLC Runtime
  - [ ] Verify installation with test program upload

- [ ] **1.5 Implement PLC runtime bridge**
  - [ ] Create `src/plc_runtime.py`
  - [ ] Implement GPIO pin mapping (define input/output pin assignments)
  - [ ] Implement scan cycle status monitoring
  - [ ] Implement program upload to OpenPLC Runtime via API
  - [ ] Implement runtime start/stop/restart commands
  - [ ] Implement I/O state reading from runtime

- [ ] **1.6 Implement mock mode**
  - [ ] Add mock GPIO class (simulates pin read/write)
  - [ ] Add mock I2C bus (simulates MCP23017 responses)
  - [ ] Add mock Modbus server (returns test registers)
  - [ ] Activate via `MOCK_MODE=true` in config
  - [ ] Allow full dashboard testing without hardware

- [ ] **1.7 Write Phase 1 tests**
  - [ ] Test config loader (valid `.env`, missing values, type conversion, MCP address parsing)
  - [ ] Test database schema creation and CRUD operations for all 5 tables
  - [ ] Test PLC runtime bridge (GPIO mapping, status read, mock mode)

---

## Phase 2 — I/O Layer & Watchdog

- [ ] **2.1 Implement digital output control**
  - [ ] Create GPIO output pin initialization
  - [ ] Implement `set_output(pin, value)` with validation
  - [ ] Implement `get_output_state(pin)` readback
  - [ ] Support relay module active-high and active-low configurations
  - [ ] Update `io_states` table on every state change

- [ ] **2.2 Implement digital input reading**
  - [ ] Create GPIO input pin initialization with pull-up/pull-down config
  - [ ] Implement `read_input(pin)` with debounce filtering
  - [ ] Implement input change detection (edge-triggered callbacks)
  - [ ] Update `io_states` table on every input change

- [ ] **2.3 Implement MCP23017 I2C expansion driver**
  - [ ] Create `src/io_expansion.py`
  - [ ] Implement MCP23017 initialization (direction, pull-up config per pin)
  - [ ] Implement `read_port(chip_addr, port)` — read 8-bit port value
  - [ ] Implement `write_port(chip_addr, port, value)` — write 8-bit port value
  - [ ] Implement `read_pin(chip_addr, pin)` / `write_pin(chip_addr, pin, value)`
  - [ ] Support multiple chips at different I2C addresses
  - [ ] Implement interrupt-based change detection (INTA/INTB pins)
  - [ ] Toggle via `ENABLE_IO_EXPANSION`

- [ ] **2.4 Implement watchdog timer manager**
  - [ ] Create `src/watchdog.py`
  - [ ] Implement software watchdog timer (configurable timeout)
  - [ ] Implement hardware watchdog integration (`/dev/watchdog`)
  - [ ] Implement `kick()` method — called each PLC scan cycle
  - [ ] Implement `on_trip()` — drive all outputs to safe state
  - [ ] Log watchdog trips as `watchdog` alarms
  - [ ] Toggle via `ENABLE_WATCHDOG`

- [ ] **2.5 Write Phase 2 tests**
  - [ ] Test digital output set/get with mock GPIO
  - [ ] Test digital input read with debounce
  - [ ] Test MCP23017 read/write with mock I2C
  - [ ] Test watchdog trip and safe-state activation

---

## Phase 3 — Modbus Communication

- [ ] **3.1 Implement Modbus TCP slave**
  - [ ] Create `src/modbus_handler.py`
  - [ ] Initialize pymodbus TCP server on configured host/port
  - [ ] Map I/O states to Modbus holding registers and coils
  - [ ] Implement register read handler (function codes 01, 02, 03, 04)
  - [ ] Implement register write handler (function codes 05, 06, 15, 16)
  - [ ] Update `io_states` table on remote write

- [ ] **3.2 Implement Modbus TCP master**
  - [ ] Implement TCP client connection to remote slave devices
  - [ ] Implement `poll_device(ip, port, slave_id, registers)` — scheduled polling
  - [ ] Parse polled values into `io_states` table
  - [ ] Implement configurable poll interval per device
  - [ ] Generate `comm_loss` alarm on connection failure

- [ ] **3.3 Implement Modbus RTU slave**
  - [ ] Initialize pymodbus RTU server on serial port
  - [ ] Map same I/O registers as TCP slave
  - [ ] Handle serial framing (baud rate, parity, stop bits)
  - [ ] Toggle via `ENABLE_MODBUS_RTU`

- [ ] **3.4 Implement Modbus RTU master**
  - [ ] Implement RTU client for serial polling of remote devices
  - [ ] Handle RS-485 direction control if applicable
  - [ ] Configurable serial parameters per device
  - [ ] Toggle via `ENABLE_MODBUS_RTU`

- [ ] **3.5 Write Phase 3 tests**
  - [ ] Test TCP slave register read/write with mock client
  - [ ] Test TCP master polling with mock slave
  - [ ] Test RTU slave/master with mock serial
  - [ ] Test Modbus ↔ io_states synchronization

---

## Phase 4 — Web Dashboard & Authentication

- [ ] **4.1 Implement Flask app factory**
  - [ ] Create `src/app.py` with app factory pattern
  - [ ] Initialize SocketIO with eventlet
  - [ ] Register blueprints for auth, dashboard, API
  - [ ] Initialize database on startup
  - [ ] Start background I/O polling thread

- [ ] **4.2 Implement bcrypt authentication**
  - [ ] Create `src/auth.py`
  - [ ] Implement `hash_password(password)` and `verify_password(password, hash)`
  - [ ] Implement login endpoint with bcrypt verification
  - [ ] Implement rate limiting (10 attempts per 15-minute window)
  - [ ] Implement session management with 24-hour expiry
  - [ ] Implement `@login_required` decorator
  - [ ] Add CSRF protection to all forms

- [ ] **4.3 Create dark-theme templates**
  - [ ] Create `templates/base.html` with dark theme layout, navigation
  - [ ] Create `static/css/style.css` with dark color scheme
  - [ ] Create `templates/login.html`

- [ ] **4.4 Build I/O monitoring dashboard**
  - [ ] Create `templates/dashboard.html` — overview with I/O summary, alarms, system status
  - [ ] Create `templates/io_monitor.html` — real-time I/O state table with color indicators
  - [ ] Implement SocketIO push for live I/O state updates
  - [ ] Implement manual force/override for outputs (with auth)
  - [ ] Create `static/js/dashboard.js`

- [ ] **4.5 Build program management page**
  - [ ] Create `templates/programs.html`
  - [ ] Implement program upload endpoint (accepts `.st` files)
  - [ ] Implement program activate/deactivate
  - [ ] Display program library with descriptions
  - [ ] Show currently active program and runtime status

- [ ] **4.6 Build Modbus configuration page**
  - [ ] Create `templates/modbus.html`
  - [ ] Display current Modbus register map
  - [ ] Configure remote TCP/RTU devices for master polling
  - [ ] Show connection status per remote device
  - [ ] Create `static/js/modbus.js`

- [ ] **4.7 Build alarm viewer page**
  - [ ] Create `templates/alarms.html`
  - [ ] Display active alarms with severity indicators
  - [ ] Display alarm history with filtering/search
  - [ ] Implement alarm acknowledge endpoint

- [ ] **4.8 Build settings panel**
  - [ ] Create `templates/settings.html`
  - [ ] Display current feature toggle states
  - [ ] Allow runtime setting changes (persist to `settings` table)
  - [ ] Display system info (uptime, scan cycle time, I/O count)

- [ ] **4.9 Write Phase 4 tests**
  - [ ] Test auth login/logout, rate limiting, session expiry
  - [ ] Test I/O monitoring API endpoints
  - [ ] Test program upload and activation
  - [ ] Test alarm acknowledge endpoint
  - [ ] Test CSRF protection

---

## Phase 5 — Data Logging, Alarms & OPC-UA

- [ ] **5.1 Implement data logger**
  - [ ] Create `src/data_logger.py`
  - [ ] Implement scheduled I/O state sampling at `LOG_INTERVAL_SEC`
  - [ ] Write samples to `data_logs` table
  - [ ] Implement automatic log rotation (delete entries older than `LOG_RETENTION_DAYS`)
  - [ ] Implement CSV export of historical data
  - [ ] Toggle via `ENABLE_DATA_LOGGING`

- [ ] **5.2 Implement alarm engine**
  - [ ] Implement high/low threshold alarms (configurable per I/O pin)
  - [ ] Implement state-change alarms (digital input transitions)
  - [ ] Implement watchdog trip alarms
  - [ ] Implement communication loss alarms (Modbus master failures)
  - [ ] Write alarm records to `alarms` table
  - [ ] Emit SocketIO alarm events for dashboard
  - [ ] Toggle via `ENABLE_ALARMS`

- [ ] **5.3 Build data log viewer**
  - [ ] Create `templates/data_logs.html` with time-range selector
  - [ ] Create `static/js/charts.js` for rendering I/O trend charts
  - [ ] Implement API endpoint for querying log data (JSON)
  - [ ] Implement CSV download endpoint

- [ ] **5.4 Implement OPC-UA server**
  - [ ] Create `src/opcua_server.py`
  - [ ] Initialize OPC-UA server on configured endpoint
  - [ ] Create OPC-UA address space nodes for all I/O states
  - [ ] Implement tag browsing (clients can discover all I/O)
  - [ ] Implement read handler (real-time I/O values)
  - [ ] Implement write handler (remote setpoint changes, if `OPCUA_READ_ONLY=false`)
  - [ ] Toggle via `ENABLE_OPCUA`

- [ ] **5.5 Create pre-built program library**
  - [ ] Create `programs/traffic_light.st` — Red/Yellow/Green sequencer with pedestrian crossing
  - [ ] Create `programs/motor_start_stop.st` — 3-phase motor with interlock and e-stop
  - [ ] Create `programs/tank_level.st` — PID level control with high/low alarms
  - [ ] Create `programs/conveyor_belt.st` — Multi-zone conveyor with jam detection

- [ ] **5.6 Implement program library manager**
  - [ ] Create `src/program_library.py`
  - [ ] Scan `programs/` directory for available programs
  - [ ] Register library programs in `programs` table with `is_library=1`
  - [ ] Implement quick-load from library to OpenPLC Runtime
  - [ ] Toggle via `ENABLE_PROGRAM_LIBRARY`

- [ ] **5.7 Write Phase 5 tests**
  - [ ] Test data logger sampling and log rotation
  - [ ] Test alarm threshold and state-change triggers
  - [ ] Test OPC-UA tag browsing and read/write
  - [ ] Test program library scanning and registration

---

## Phase 6 — ScadaBR, Deployment & Documentation

- [ ] **6.1 Create ScadaBR install script**
  - [ ] Create `scripts/install_scadabr.sh`
  - [ ] Install Java runtime (OpenJDK)
  - [ ] Download and install ScadaBR
  - [ ] Configure ScadaBR to poll Pi's Modbus TCP slave
  - [ ] Create systemd service for ScadaBR

- [ ] **6.2 Implement ScadaBR bridge**
  - [ ] Create `src/scada_bridge.py`
  - [ ] Auto-configure ScadaBR data source (Modbus TCP pointing to localhost)
  - [ ] Auto-create ScadaBR data points matching `io_states` pins
  - [ ] Verify ScadaBR connectivity and polling

- [ ] **6.3 Create deployment scripts**
  - [ ] Create `deploy/deploy_to_pi.sh` (rsync to `rasp-pi:~/openplc-pi/`)
  - [ ] Create `scripts/install_deps.sh` (OS-level dependencies)
  - [ ] Create `scripts/generate_password_hash.sh` (bcrypt hash helper)

- [ ] **6.4 Write systemd service unit**
  - [ ] Create service file for the Flask dashboard
  - [ ] Configure `After=openplc.service` dependency
  - [ ] Configure auto-restart on failure

- [ ] **6.5 Write documentation**
  - [ ] Create `docs/wiring_guide.md` — GPIO pinout, relay wiring, input module wiring
  - [ ] Create `docs/modbus_reference.md` — register map, function codes, addressing
  - [ ] Create `docs/program_guide.md` — quick-start for writing ST/LD/FBD programs

- [ ] **6.6 Final integration testing**
  - [ ] Test full scan cycle: read inputs → execute program → write outputs
  - [ ] Test Modbus TCP/RTU communication with real or simulated devices
  - [ ] Test ScadaBR polling and HMI display
  - [ ] Test OPC-UA client connection and tag browsing
  - [ ] Test watchdog trip and recovery
  - [ ] Test alarm generation and dashboard notification
  - [ ] Test data logging and chart rendering
  - [ ] Update README with final instructions
