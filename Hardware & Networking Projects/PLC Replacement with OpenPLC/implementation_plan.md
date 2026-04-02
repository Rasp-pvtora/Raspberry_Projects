# Implementation Plan — PLC Replacement with OpenPLC

## Phase 1 — Project Foundation & OpenPLC Setup

**Goal:** Scaffold the project, configure environment loading, set up the database, install OpenPLC Runtime, and map Pi GPIOs.

- [ ] **Step 1.1 — Initialize Project Structure**
  - [ ] Create directory tree:
    ```
    src/, templates/, static/css/, static/js/, tests/, deploy/, scripts/, docs/, data/, programs/
    ```
  - [ ] Create `pyproject.toml` with project name, version, Python ≥3.11, and entry point `src.app`
  - [ ] Create `requirements.txt`:
    ```
    flask
    flask-socketio
    eventlet
    bcrypt
    python-dotenv
    pymodbus
    python-opcua
    smbus2
    RPi.GPIO
    gunicorn
    pytest
    pytest-cov
    ```
  - [ ] Create `.env.example` with all variables and documented defaults (see TSD §8)
  - [ ] Create `src/__init__.py` (empty)
  - [ ] Create `tests/__init__.py` (empty) and `tests/conftest.py` with shared fixtures

- [ ] **Step 1.2 — Configuration Loader**
  - [ ] Create `src/config.py`
  - [ ] Define `@dataclass class Config` with all `.env` fields and proper types
  - [ ] Implement `load_config()` — reads `.env` via `dotenv_values()`, applies defaults
  - [ ] Convert string values to `int`, `float`, `bool` as needed
  - [ ] Parse `MCP23017_ADDRESSES` comma-separated hex string into list of ints
  - [ ] Parse `RATE_LIMIT` string (e.g., `10/15min`) into count and window values
  - [ ] Add `is_enabled(feature: str) -> bool` helper for toggle checks
  - [ ] Write `tests/test_config.py` — test loading, defaults, type conversion, address parsing

- [ ] **Step 1.3 — SQLite Database Module**
  - [ ] Create `src/database.py`
  - [ ] Implement `get_connection(db_path)` with WAL mode pragma
  - [ ] Implement `init_db(conn)` — creates all 5 tables (see TSD §3):
    - `io_states` — current I/O pin states with safe values
    - `data_logs` — time-series I/O value samples
    - `programs` — uploaded PLC program metadata
    - `alarms` — alarm history with acknowledgement tracking
    - `settings` — key/value runtime configuration
  - [ ] Implement CRUD functions:
    - `upsert_io_state(conn, pin_data)` / `get_io_state(conn, pin_name)` / `list_io_states(conn)`
    - `insert_data_log(conn, pin_name, value)` / `get_data_logs(conn, pin_name, start, end)`
    - `delete_old_logs(conn, retention_days)`
    - `insert_program(conn, program_data)` / `get_program(conn, program_id)` / `list_programs(conn)`
    - `set_active_program(conn, program_id)` / `get_active_program(conn)`
    - `insert_alarm(conn, alarm_data)` / `get_active_alarms(conn)` / `get_alarm_history(conn, limit, offset)`
    - `acknowledge_alarm(conn, alarm_id, username)`
    - `get_setting(conn, key)` / `set_setting(conn, key, value)`
  - [ ] Use parameterized queries for all DB operations
  - [ ] Write `tests/test_database.py` — test schema creation, all CRUD ops, WAL mode

- [ ] **Step 1.4 — OpenPLC Runtime Install Script**
  - [ ] Create `scripts/install_openplc.sh`:
    ```bash
    #!/bin/bash
    # Clone OpenPLC Runtime
    git clone https://github.com/thiagoralves/OpenPLC_v3.git /opt/openplc
    cd /opt/openplc
    # Install for Raspberry Pi (Linux ARM with GPIO support)
    ./install.sh rpi
    # Enable and start the service
    sudo systemctl enable openplc
    sudo systemctl start openplc
    ```
  - [ ] Verify runtime accessible at `http://localhost:8080`

- [ ] **Step 1.5 — PLC Runtime Bridge**
  - [ ] Create `src/plc_runtime.py`
  - [ ] Implement `PLCRuntime` class:
    - `__init__(config)` — load GPIO pin mapping from config
    - `get_status() -> dict` — query OpenPLC Runtime API for run/stop state
    - `upload_program(filepath)` — POST program file to Runtime API
    - `start()` / `stop()` / `restart()` — Runtime lifecycle commands
    - `get_io_map() -> dict` — read current I/O address mapping
    - `read_inputs() -> dict` — read all digital input states from GPIO
    - `write_outputs(states: dict)` — write digital outputs to GPIO
  - [ ] Define default GPIO pin mapping:
    ```
    DI_0=GPIO17, DI_1=GPIO27, DI_2=GPIO22, DI_3=GPIO23
    DO_0=GPIO24, DO_1=GPIO25, DO_2=GPIO5, DO_3=GPIO6
    ```
  - [ ] Implement mock mode: simulate read/write without GPIO hardware

- [ ] **Step 1.6 — Mock Mode**
  - [ ] Add `MockGPIO` class — simulates `RPi.GPIO` interface (stores pin states in dict)
  - [ ] Add `MockSMBus` class — simulates `smbus2.SMBus` for MCP23017 testing
  - [ ] Add `MockModbusServer` — returns predefined register values
  - [ ] Activate all mocks when `MOCK_MODE=true`
  - [ ] Write `tests/conftest.py` fixtures that inject mocks automatically

- [ ] **Step 1.7 — Phase 1 Tests**
  - [ ] `tests/test_config.py` — config loading, defaults, type conversion, feature toggles
  - [ ] `tests/test_database.py` — schema creation, all 5 tables, CRUD operations, WAL mode
  - [ ] `tests/test_plc_runtime.py` — GPIO mapping, runtime bridge, mock mode

---

## Phase 2 — I/O Layer & Watchdog

**Goal:** Build the I/O abstraction layer, MCP23017 expansion driver, and fail-safe watchdog system.

- [ ] **Step 2.1 — Digital Output Control**
  - [ ] Initialize GPIO output pins with `RPi.GPIO.setup(pin, GPIO.OUT)`
  - [ ] Implement `set_output(pin_name, value)`:
    - Validate pin_name exists in output map
    - Check if pin is force-overridden (`is_forced` flag)
    - Write value to GPIO
    - Update `io_states` table with new `current_value` and `last_change_at`
  - [ ] Support active-high and active-low relay configurations (configurable per pin)
  - [ ] Implement `get_all_outputs() -> dict` — return current output states

- [ ] **Step 2.2 — Digital Input Reading**
  - [ ] Initialize GPIO input pins with configurable pull-up/pull-down
  - [ ] Implement `read_input(pin_name) -> int`:
    - Read GPIO pin state
    - Apply software debounce filter (configurable delay, default 50ms)
    - Update `io_states` table on value change
  - [ ] Implement edge-triggered callbacks using `GPIO.add_event_detect()`
  - [ ] Implement `read_all_inputs() -> dict` — poll all inputs

- [ ] **Step 2.3 — MCP23017 I2C Expansion Driver**
  - [ ] Create `src/io_expansion.py`
  - [ ] Implement `MCP23017` class:
    - `__init__(bus, address)` — open I2C bus, verify chip presence
    - `configure_pin(pin, direction, pullup)` — set pin as input/output
    - `read_pin(pin) -> int` / `write_pin(pin, value)` — single pin operations
    - `read_port(port) -> int` / `write_port(port, value)` — 8-bit port operations
    - `read_all() -> dict` — read all 16 pins
  - [ ] Implement `IOExpansionManager` class:
    - `__init__(config)` — initialize all configured MCP23017 chips
    - `read_expanded_inputs()` / `write_expanded_outputs(states)` — unified I/O
  - [ ] Handle I2C bus errors with retry logic (3 retries, 100ms delay)
  - [ ] Toggle via `ENABLE_IO_EXPANSION`
  - [ ] Mock: `MockSMBus` returns simulated register values

- [ ] **Step 2.4 — Watchdog Timer Manager**
  - [ ] Create `src/watchdog.py`
  - [ ] Implement `WatchdogManager` class:
    - `__init__(config, io_layer)` — set timeout, reference to I/O layer
    - `start()` — begin watchdog timer thread
    - `kick()` — reset timer (called each PLC scan cycle)
    - `on_trip()` — drive all outputs to `safe_value` from `io_states` table
    - `is_tripped() -> bool` — check current watchdog state
    - `reset()` — clear trip state and resume normal operation
  - [ ] Implement hardware watchdog integration (`/dev/watchdog`) if available
  - [ ] Log watchdog trip events as `watchdog` alarm in `alarms` table
  - [ ] Toggle via `ENABLE_WATCHDOG`

- [ ] **Step 2.5 — Phase 2 Tests**
  - [ ] `tests/test_io.py` — digital output set/get, digital input read/debounce
  - [ ] `tests/test_io_expansion.py` — MCP23017 pin/port read/write, bus error retry
  - [ ] `tests/test_watchdog.py` — timer kick, trip, safe-state activation, reset

---

## Phase 3 — Modbus Communication

**Goal:** Implement full Modbus TCP/RTU master and slave communication.

- [ ] **Step 3.1 — Modbus TCP Slave**
  - [ ] Create `src/modbus_handler.py`
  - [ ] Implement `ModbusTCPSlave` class:
    - `__init__(config, io_layer)` — configure host/port/slave_id
    - `start()` — launch pymodbus TCP server in background thread
    - `build_register_map()` — map `io_states` pins to Modbus addresses:
      - Coils (0xxxx): digital outputs (read/write)
      - Discrete Inputs (1xxxx): digital inputs (read-only)
      - Holding Registers (4xxxx): analog outputs / setpoints (read/write)
      - Input Registers (3xxxx): analog inputs / process values (read-only)
    - `sync_registers()` — update registers from `io_states` table (called each cycle)
    - `on_write(address, value)` — update `io_states` on remote Modbus write
    - `stop()` — shutdown server cleanly
  - [ ] Toggle via `ENABLE_MODBUS_TCP`

- [ ] **Step 3.2 — Modbus TCP Master**
  - [ ] Implement `ModbusTCPMaster` class:
    - `__init__(config)` — configured remote device list
    - `add_device(ip, port, slave_id, registers)` — add polling target
    - `poll_device(device) -> dict` — read registers from remote slave
    - `poll_all()` — poll all configured devices
    - `start(interval)` — begin scheduled polling loop
    - `on_comm_loss(device)` — generate `comm_loss` alarm
  - [ ] Store polled values in `io_states` table with `source='modbus'`

- [ ] **Step 3.3 — Modbus RTU Slave**
  - [ ] Implement `ModbusRTUSlave` class:
    - Same register mapping as TCP slave
    - Configure serial port, baud rate, parity, stop bits from `.env`
    - Launch pymodbus RTU server on configured serial port
  - [ ] Toggle via `ENABLE_MODBUS_RTU`

- [ ] **Step 3.4 — Modbus RTU Master**
  - [ ] Implement `ModbusRTUMaster` class:
    - Same polling logic as TCP master
    - Manage RS-485 direction control if needed
    - Handle serial timeouts and retries
  - [ ] Toggle via `ENABLE_MODBUS_RTU`

- [ ] **Step 3.5 — Phase 3 Tests**
  - [ ] `tests/test_modbus.py`:
    - TCP slave register read/write
    - TCP master polling with mock slave
    - RTU slave/master with mock serial
    - Register map ↔ io_states synchronization
    - Communication loss alarm generation

---

## Phase 4 — Web Dashboard & Authentication

**Goal:** Build the authenticated dark-themed dashboard with real-time I/O monitoring.

- [ ] **Step 4.1 — Flask App Factory**
  - [ ] Create `src/app.py`:
    - `create_app(config)` factory function
    - Initialize SocketIO with eventlet async mode
    - Register auth blueprint, dashboard blueprint, API blueprint
    - Call `init_db()` on startup
    - Start background I/O scan cycle thread
    - Configure CSRF protection
  - [ ] Add entry point: `python -m src.app` starts the server

- [ ] **Step 4.2 — bcrypt Authentication**
  - [ ] Create `src/auth.py`:
    - `hash_password(password: str) -> str` — bcrypt with auto salt
    - `verify_password(password: str, hash: str) -> bool`
    - `login()` view — validates credentials, creates session
    - `logout()` view — clears session
    - `@login_required` decorator — redirects to login if no valid session
    - Rate limiter: track failed attempts per IP in memory dict
      - Block after 10 failures within 15-minute window
      - Return 429 with retry-after header
    - Session expiry: set `session.permanent = True`, `PERMANENT_SESSION_LIFETIME = 24h`
  - [ ] Add CSRF token generation and validation

- [ ] **Step 4.3 — Dark Theme Templates & CSS**
  - [ ] Create `templates/base.html`:
    - Dark background (#1a1a2e), card backgrounds (#16213e), accent (#0f3460)
    - Navigation sidebar with links to all pages
    - Flash message display area
    - SocketIO client script include
  - [ ] Create `static/css/style.css` — full dark theme stylesheet
  - [ ] Create `templates/login.html` — centered login form

- [ ] **Step 4.4 — I/O Monitoring Dashboard**
  - [ ] Create `templates/dashboard.html`:
    - System status overview (runtime state, scan cycle time, uptime)
    - I/O summary cards (total inputs, outputs, forced, in alarm)
    - Active alarm count with severity breakdown
    - Quick links to detail pages
  - [ ] Create `templates/io_monitor.html`:
    - Table of all I/O pins with columns: name, type, source, value, forced, last change
    - Color indicators: green=normal, red=alarm, yellow=forced, gray=disabled
    - Force/override controls for outputs (button per pin)
  - [ ] Create `static/js/dashboard.js`:
    - SocketIO connection for live I/O updates
    - DOM updates on `io_update` events
    - Auto-reconnect on disconnect

- [ ] **Step 4.5 — Program Management Page**
  - [ ] Create `templates/programs.html`:
    - Table of uploaded programs (name, language, active, uploaded date)
    - File upload form (accept `.st` files)
    - Activate/deactivate buttons
    - Library section with pre-built programs

- [ ] **Step 4.6 — Modbus Configuration Page**
  - [ ] Create `templates/modbus.html`:
    - Modbus register map table (address, pin mapping, read/write)
    - Remote device list with connection status
    - Add/edit/remove remote polling targets
  - [ ] Create `static/js/modbus.js`

- [ ] **Step 4.7 — Alarm Viewer Page**
  - [ ] Create `templates/alarms.html`:
    - Active alarms table (severity icon, pin, message, time, acknowledge button)
    - Alarm history with date-range filter and severity filter
    - Acknowledge endpoint: POST with alarm ID and username

- [ ] **Step 4.8 — Settings Panel**
  - [ ] Create `templates/settings.html`:
    - Feature toggle display (read from `.env` and `settings` table)
    - Runtime-adjustable settings (log interval, watchdog timeout)
    - System info: Python version, uptime, I/O pin count, DB size, scan cycle avg

- [ ] **Step 4.9 — Phase 4 Tests**
  - [ ] `tests/test_auth.py` — login, logout, rate limiting, session expiry, CSRF
  - [ ] `tests/test_api.py` — I/O read, force output, program upload, alarm acknowledge
  - [ ] `tests/test_dashboard.py` — page rendering, template context

---

## Phase 5 — Data Logging, Alarms & OPC-UA

**Goal:** Add data logging, alarm engine, OPC-UA server, and program library.

- [ ] **Step 5.1 — Data Logger**
  - [ ] Create `src/data_logger.py`
  - [ ] Implement `DataLogger` class:
    - `__init__(config, db)` — configure interval and retention
    - `start()` — begin background sampling thread
    - `sample()` — read all `io_states`, insert into `data_logs`
    - `rotate()` — delete entries older than `LOG_RETENTION_DAYS`
    - `export_csv(pin_name, start, end) -> str` — generate CSV data
    - `stop()` — stop sampling thread
  - [ ] Run `rotate()` once per hour
  - [ ] Toggle via `ENABLE_DATA_LOGGING`

- [ ] **Step 5.2 — Alarm Engine**
  - [ ] Implement `AlarmEngine` class (in `src/data_logger.py`):
    - `check_thresholds(io_states)` — compare values against configured limits
    - `check_state_changes(prev_states, curr_states)` — detect digital transitions
    - `raise_alarm(pin, type, severity, message, value, threshold)`
    - `clear_alarm(alarm_id)` — mark alarm inactive when condition clears
    - `get_active() -> list` — return all active alarms
  - [ ] Emit SocketIO `alarm` event on new alarm (for dashboard notification)
  - [ ] Toggle via `ENABLE_ALARMS`

- [ ] **Step 5.3 — Data Log Viewer**
  - [ ] Create `templates/data_logs.html`:
    - Pin selector dropdown
    - Time-range picker (last 1h, 6h, 24h, 7d, custom)
    - Chart area (line chart of values over time)
    - CSV download button
  - [ ] Create `static/js/charts.js`:
    - Fetch log data from API endpoint
    - Render time-series chart (Canvas-based or simple SVG)
  - [ ] API: `GET /api/data_logs?pin=<name>&start=<iso>&end=<iso>` → JSON

- [ ] **Step 5.4 — OPC-UA Server**
  - [ ] Create `src/opcua_server.py`
  - [ ] Implement `OPCUAServer` class:
    - `__init__(config, io_layer)` — configure endpoint URL
    - `setup_address_space()` — create OPC-UA nodes for each I/O pin:
      - Node per pin under `Objects/OpenPLC/IO/<pin_name>`
      - Data type: Float for analog, Boolean for digital
    - `start()` — launch OPC-UA server
    - `update_values()` — sync node values from `io_states` (called each cycle)
    - `on_write(node, value)` — handle remote write (if `OPCUA_READ_ONLY=false`)
    - `stop()` — shutdown server
  - [ ] Toggle via `ENABLE_OPCUA`

- [ ] **Step 5.5 — Pre-Built Program Library**
  - [ ] Create `programs/traffic_light.st`:
    - State machine: RED(30s) → GREEN(25s) → YELLOW(5s) → RED
    - Pedestrian crossing button input with walk signal
    - Uses TON timers for timing
  - [ ] Create `programs/motor_start_stop.st`:
    - Start/Stop pushbuttons with seal-in logic
    - Overload relay input for trip protection
    - Emergency stop (NC contact) with reset requirement
    - Run indicator output
  - [ ] Create `programs/tank_level.st`:
    - Analog level sensor input (0-100%)
    - PID controller for fill pump speed
    - High level alarm at 90%, low level alarm at 10%
    - Overflow protection: stop pump at 95%
  - [ ] Create `programs/conveyor_belt.st`:
    - Multi-zone start/stop with upstream interlock
    - Photoelectric sensor for jam detection
    - Auto-stop on jam with alarm
    - Speed control output

- [ ] **Step 5.6 — Program Library Manager**
  - [ ] Create `src/program_library.py`
  - [ ] Implement `ProgramLibrary` class:
    - `scan_library()` — read `programs/` directory, register in DB with `is_library=1`
    - `get_library_programs() -> list` — return all library programs with descriptions
    - `load_program(program_id)` — upload library program to OpenPLC Runtime
  - [ ] Toggle via `ENABLE_PROGRAM_LIBRARY`

- [ ] **Step 5.7 — Phase 5 Tests**
  - [ ] `tests/test_data_logger.py` — sampling, rotation, CSV export
  - [ ] `tests/test_alarms.py` — threshold triggers, state-change, raise/clear
  - [ ] `tests/test_opcua.py` — server startup, tag browse, read/write
  - [ ] `tests/test_program_library.py` — scan, register, load

---

## Phase 6 — ScadaBR, Deployment & Documentation

**Goal:** Integrate ScadaBR, finalize deployment, and complete documentation.

- [ ] **Step 6.1 — ScadaBR Install Script**
  - [ ] Create `scripts/install_scadabr.sh`:
    ```bash
    #!/bin/bash
    # Install Java
    sudo apt install -y default-jdk
    # Download and install ScadaBR
    wget <scadabr-release-url> -O /tmp/scadabr.zip
    unzip /tmp/scadabr.zip -d /opt/scadabr
    # Configure and start
    sudo systemctl enable scadabr
    sudo systemctl start scadabr
    ```
  - [ ] Verify ScadaBR accessible at `http://localhost:9090`

- [ ] **Step 6.2 — ScadaBR Bridge**
  - [ ] Create `src/scada_bridge.py`
  - [ ] Implement `ScadaBridge` class:
    - `configure_data_source()` — create Modbus TCP data source in ScadaBR pointing to `127.0.0.1:502`
    - `sync_data_points()` — create ScadaBR data points for each `io_states` pin
    - `verify_connection()` — check ScadaBR is polling and receiving data
  - [ ] Toggle via `ENABLE_SCADABR`

- [ ] **Step 6.3 — Deployment Scripts**
  - [ ] Create `deploy/deploy_to_pi.sh`:
    ```bash
    #!/bin/bash
    rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude 'data/*.db' \
      ./ rasp-pi:~/openplc-pi/
    ssh rasp-pi 'cd ~/openplc-pi && source .venv/bin/activate && pip install -r requirements.txt'
    ssh rasp-pi 'sudo systemctl restart openplc-dashboard'
    ```
  - [ ] Create `scripts/install_deps.sh`:
    ```bash
    #!/bin/bash
    sudo apt update && sudo apt install -y \
      python3 python3-pip python3-venv \
      i2c-tools python3-smbus \
      sqlite3
    sudo raspi-config nonint do_i2c 0  # Enable I2C
    ```
  - [ ] Create `scripts/generate_password_hash.sh`

- [ ] **Step 6.4 — systemd Service**
  - [ ] Create service unit file:
    ```ini
    [Unit]
    Description=OpenPLC Pi Controller Dashboard
    After=network.target openplc.service

    [Service]
    Type=simple
    User=pi
    WorkingDirectory=/home/pi/openplc-pi
    Environment=PATH=/home/pi/openplc-pi/.venv/bin
    ExecStart=/home/pi/openplc-pi/.venv/bin/python -m src.app
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target
    ```

- [ ] **Step 6.5 — Documentation**
  - [ ] Create `docs/wiring_guide.md`:
    - GPIO pinout table with BCM numbering
    - Relay module wiring diagram (Pi → relay → load)
    - Optocoupled input wiring (field device → opto module → Pi)
    - MCP23017 I2C wiring (SDA, SCL, address pins, interrupt pins)
    - Power supply recommendations
  - [ ] Create `docs/modbus_reference.md`:
    - Register map table (address, description, type, read/write)
    - Function code reference (01-06, 15-16)
    - Example client configurations (ScadaBR, Node-RED, SCADA software)
  - [ ] Create `docs/program_guide.md`:
    - OpenPLC Editor installation and setup
    - Writing a basic Structured Text program
    - Compiling and uploading to runtime
    - Testing with mock mode

- [ ] **Step 6.6 — Final Integration Testing**
  - [ ] Full scan cycle test: inputs → logic → outputs
  - [ ] Modbus TCP/RTU communication with simulated devices
  - [ ] ScadaBR polling and live data display
  - [ ] OPC-UA client connection and tag browsing
  - [ ] Watchdog trip → safe state → reset flow
  - [ ] Alarm generation → dashboard notification → acknowledge
  - [ ] Data logging → chart rendering → CSV export
  - [ ] Deploy script end-to-end on fresh Pi
  - [ ] Update README with final instructions and verified quickstart
