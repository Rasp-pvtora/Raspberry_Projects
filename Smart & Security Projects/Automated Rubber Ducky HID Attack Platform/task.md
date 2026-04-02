# Task List — Automated Rubber Ducky HID Attack Platform

## Phase 1 — Project Foundation & USB HID Gadget

- [ ] **1.1 Initialize project structure**
  - [ ] Create directory tree (`src/`, `templates/`, `static/`, `tests/`, `deploy/`, `scripts/`, `docs/`, `data/`, `payloads/recon/`, `payloads/exfiltration/`, `payloads/configuration/`)
  - [ ] Create `pyproject.toml` with project metadata
  - [ ] Create `requirements.txt` with all dependencies
  - [ ] Create `.env.example` with all variables and defaults
  - [ ] Create `src/__init__.py`
  - [ ] Create `tests/__init__.py` and `tests/conftest.py`

- [ ] **1.2 Implement configuration loader**
  - [ ] Create `src/config.py` with dataclass for all `.env` variables
  - [ ] Load and validate `.env` using `python-dotenv`
  - [ ] Type conversion for int, float, bool values
  - [ ] Defaults for all optional settings
  - [ ] Feature-toggle helper method (`is_enabled("feature_name")`)

- [ ] **1.3 Implement SQLite database module**
  - [ ] Create `src/database.py` with connection manager
  - [ ] Enable WAL mode on connection
  - [ ] Create `payloads` table schema
  - [ ] Create `execution_logs` table schema
  - [ ] Create `keystroke_logs` table schema
  - [ ] Create `settings` table schema
  - [ ] Implement `init_db()` to create all tables
  - [ ] Implement CRUD helpers for each table
  - [ ] Implement parameterized queries for all DB operations

- [ ] **1.4 Implement ConfigFS USB HID gadget**
  - [ ] Create `src/hid_gadget.py`
  - [ ] Implement `setup_gadget()` — create ConfigFS gadget at `/sys/kernel/config/usb_gadget/rubber_ducky/`
  - [ ] Configure USB descriptor (VID, PID, manufacturer, product strings)
  - [ ] Write HID keyboard report descriptor (boot protocol compatible)
  - [ ] Create HID function (`hid.usb0`) and link to configuration
  - [ ] Bind gadget to UDC (USB Device Controller)
  - [ ] Implement `teardown_gadget()` — reverse setup cleanly
  - [ ] Implement `is_gadget_active() -> bool` — check gadget state
  - [ ] Handle permission errors and missing kernel modules gracefully

- [ ] **1.5 Implement keystroke execution engine**
  - [ ] Create `src/executor.py`
  - [ ] Implement HID keyboard report structure (8-byte report: modifier, reserved, keycodes[6])
  - [ ] Implement keycode lookup table (US keyboard layout)
  - [ ] Implement `send_keystroke(key, modifiers=[])` — write HID report to `/dev/hidg0`
  - [ ] Implement `send_string(text)` — type a string character by character
  - [ ] Implement `release_keys()` — send empty report (key release)
  - [ ] Implement configurable inter-keystroke delay (`DEFAULT_DELAY_MS`)
  - [ ] Handle special keys (ENTER, TAB, ESC, arrows, F-keys, etc.)

- [ ] **1.6 Implement mock mode**
  - [ ] Add `MockExecutor` class to `src/executor.py`
  - [ ] Log keystrokes to stdout/file instead of writing to `/dev/hidg0`
  - [ ] Simulate timing delays for realistic testing
  - [ ] Activate via `MOCK_MODE=true` in config
  - [ ] Allow full dashboard and editor testing without hardware

- [ ] **1.7 Create USB gadget setup script**
  - [ ] Create `scripts/setup_usb_gadget.sh`
  - [ ] Load `libcomposite` kernel module
  - [ ] Load `dwc2` overlay (Pi 4 USB OTG)
  - [ ] Add `dtoverlay=dwc2` to `/boot/config.txt` if not present
  - [ ] Add `dwc2` and `libcomposite` to `/etc/modules` if not present
  - [ ] Verify gadget device `/dev/hidg0` exists after setup
  - [ ] Print success/failure message

- [ ] **1.8 Write Phase 1 tests**
  - [ ] Test config loader (valid `.env`, missing values, type conversion)
  - [ ] Test database schema creation and CRUD operations
  - [ ] Test HID report construction (keycode mapping, modifier keys)
  - [ ] Test executor string-to-keystroke conversion
  - [ ] Test mock mode output
  - [ ] Test gadget setup/teardown (mocked filesystem)

---

## Phase 2 — DuckyScript Interpreter & Payload Library

- [ ] **2.1 Implement DuckyScript parser**
  - [ ] Create `src/duckyscript.py`
  - [ ] Implement line-by-line tokenizer (strip comments via `REM`)
  - [ ] Parse command and argument from each line
  - [ ] Build instruction list (command, argument, line number)
  - [ ] Handle `DEFAULT_DELAY` directive (set global delay)
  - [ ] Handle `REPEAT` directive (repeat previous command N times)
  - [ ] Validate syntax and report errors with line numbers

- [ ] **2.2 Implement standard DuckyScript commands**
  - [ ] `STRING <text>` — type a string
  - [ ] `DELAY <ms>` — wait N milliseconds
  - [ ] `ENTER` / `RETURN` — press Enter
  - [ ] `GUI` / `WINDOWS` — press Windows/Command key
  - [ ] `ALT`, `CTRL`, `SHIFT` — modifier keys (solo or combined)
  - [ ] `TAB`, `ESCAPE`, `CAPSLOCK`, `DELETE`, `INSERT`
  - [ ] `PAGEUP`, `PAGEDOWN`, `HOME`, `END`
  - [ ] `UPARROW`, `DOWNARROW`, `LEFTARROW`, `RIGHTARROW`
  - [ ] `F1` through `F12`
  - [ ] `PRINTSCREEN`, `SCROLLLOCK`, `PAUSE`, `MENU`/`APP`
  - [ ] Combo keys: `CTRL ALT DELETE`, `GUI r`, `ALT F4`, etc.
  - [ ] `DEFAULT_DELAY <ms>` — set delay between all subsequent commands
  - [ ] `REPEAT <n>` — repeat previous command N times

- [ ] **2.3 Implement variable substitution**
  - [ ] `$TARGET_OS` — replaced with detected OS name
  - [ ] `$TIMESTAMP` — replaced with current ISO-8601 timestamp
  - [ ] `$HOSTNAME` — replaced with Pi's hostname
  - [ ] `$PAYLOAD_NAME` — replaced with current payload name
  - [ ] Substitute variables in `STRING` arguments before execution

- [ ] **2.4 Implement conditional execution**
  - [ ] `IFOS WINDOWS` ... `ENDIF` — execute block only on Windows
  - [ ] `IFOS MACOS` ... `ENDIF` — execute block only on macOS
  - [ ] `IFOS LINUX` ... `ENDIF` — execute block only on Linux
  - [ ] Support nesting (up to 3 levels)
  - [ ] Skip commands when condition is false

- [ ] **2.5 Implement payload manager**
  - [ ] Create `src/payload_manager.py`
  - [ ] `list_payloads(category=None, target_os=None)` — query with optional filters
  - [ ] `get_payload(payload_id)` — retrieve single payload with content
  - [ ] `create_payload(name, content, category, target_os, description)` — save to file + DB
  - [ ] `update_payload(payload_id, content, ...)` — update file + DB record
  - [ ] `delete_payload(payload_id)` — remove file + DB record
  - [ ] `sync_filesystem()` — scan `payloads/` directory and sync with DB
  - [ ] `import_payload(file_path)` — import `.txt` file into library
  - [ ] `export_payload(payload_id)` — return content for download
  - [ ] Toggle via `ENABLE_PAYLOAD_LIBRARY`

- [ ] **2.6 Create sample payloads**
  - [ ] `payloads/recon/system_info_windows.txt` — gather system info on Windows
  - [ ] `payloads/recon/wifi_passwords_windows.txt` — extract saved WiFi passwords
  - [ ] `payloads/recon/system_info_linux.txt` — gather system info on Linux
  - [ ] `payloads/configuration/install_tool_windows.txt` — silent install example
  - [ ] `payloads/configuration/set_wallpaper_windows.txt` — change wallpaper (harmless demo)
  - [ ] `payloads/exfiltration/copy_to_storage.txt` — copy files to mass storage device
  - [ ] Include `REM` header in each with description, target OS, risk level, and authorization reminder

- [ ] **2.7 Write Phase 2 tests**
  - [ ] Test DuckyScript parser (valid scripts, syntax errors, empty lines, comments)
  - [ ] Test all standard commands (STRING, DELAY, modifiers, combos, F-keys)
  - [ ] Test variable substitution ($TARGET_OS, $TIMESTAMP, etc.)
  - [ ] Test conditional execution (IFOS matching, non-matching, nested)
  - [ ] Test REPEAT and DEFAULT_DELAY directives
  - [ ] Test payload CRUD operations (create, read, update, delete)
  - [ ] Test payload filesystem sync
  - [ ] Test payload import/export

---

## Phase 3 — Web Dashboard & Authentication

- [ ] **3.1 Implement Flask app factory**
  - [ ] Create `src/app.py` with `create_app()` factory
  - [ ] Initialize Flask-SocketIO with eventlet
  - [ ] Register blueprints/routes
  - [ ] Integrate config and database initialization
  - [ ] Start HID gadget on startup (if enabled)
  - [ ] Implement `__main__` entry point

- [ ] **3.2 Implement authentication**
  - [ ] Create `src/auth.py`
  - [ ] Implement bcrypt password verification
  - [ ] Implement login route (`POST /login`)
  - [ ] Implement logout route (`POST /logout`)
  - [ ] Implement rate limiting (10 attempts per 15 minutes per IP)
  - [ ] Implement session with 24-hour expiry
  - [ ] Implement `@login_required` decorator for all protected routes
  - [ ] Read `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` from config

- [ ] **3.3 Create dark theme templates and CSS**
  - [ ] Create `templates/base.html` with dark theme layout
  - [ ] Create `static/css/style.css` with dark color scheme
  - [ ] Responsive layout for desktop, tablet, and mobile
  - [ ] Navigation bar with app title, status indicators, and logout button

- [ ] **3.4 Build login page**
  - [ ] Create `templates/login.html`
  - [ ] Username and password form with CSRF token
  - [ ] Error message display for failed login
  - [ ] Rate limit warning display
  - [ ] Legal disclaimer notice on login page

- [ ] **3.5 Build dashboard page**
  - [ ] Create `templates/dashboard.html`
  - [ ] Summary cards: Active Payload, Trigger Mode, HID Status, Executions Today
  - [ ] Recent payloads list with quick-execute buttons
  - [ ] Current execution status panel (idle/running/completed)
  - [ ] Recent execution log feed (last 10 executions)
  - [ ] USB connection status indicator
  - [ ] Target OS display (if detected)

- [ ] **3.6 Build payload editor page**
  - [ ] Create `templates/editor.html`
  - [ ] CodeMirror integration with DuckyScript syntax highlighting
  - [ ] Save, load, and new payload buttons
  - [ ] Payload metadata fields (name, category, target OS, description, risk level)
  - [ ] Syntax validation panel (errors with line numbers)
  - [ ] Preview: show translated keystroke sequence
  - [ ] Execute button (trigger selected payload from editor)

- [ ] **3.7 Build payload library page**
  - [ ] Create `templates/library.html`
  - [ ] Grid/list view of all payloads
  - [ ] Filter by category (recon, exfiltration, configuration, custom)
  - [ ] Filter by target OS (any, windows, macos, linux)
  - [ ] Search by name/description
  - [ ] Sort by name, category, execution count, last executed
  - [ ] Quick actions: edit, duplicate, delete, execute

- [ ] **3.8 Implement SocketIO real-time updates**
  - [ ] Emit `execution_start` event when payload begins
  - [ ] Emit `keystroke_sent` event for each keystroke (live feed)
  - [ ] Emit `execution_complete` event with summary
  - [ ] Emit `execution_error` event on failure
  - [ ] Emit `hid_status` event (gadget active/inactive)
  - [ ] Emit `usb_connected` event (target plugged/unplugged)
  - [ ] Client-side handler in `static/js/dashboard.js`

- [ ] **3.9 Build settings panel**
  - [ ] Create `templates/settings.html`
  - [ ] Trigger mode selector (immediate, button, timed, manual)
  - [ ] Default delay adjustment
  - [ ] Feature toggle display (read-only from `.env`)
  - [ ] HID gadget status and reset button
  - [ ] WiFi AP status (if enabled)
  - [ ] Log retention / cleanup controls

- [ ] **3.10 Write Phase 3 tests**
  - [ ] Test login (valid credentials, invalid credentials, rate limiting)
  - [ ] Test session expiry (24-hour window)
  - [ ] Test protected route access (authenticated vs unauthenticated)
  - [ ] Test dashboard data API endpoints
  - [ ] Test payload editor save/load/validate endpoints
  - [ ] Test payload library CRUD via web
  - [ ] Test SocketIO event emission
  - [ ] Test CSRF protection on forms

---

## Phase 4 — Trigger Modes & Execution Logging

- [ ] **4.1 Implement trigger mode manager**
  - [ ] Create `src/trigger.py` with `TriggerManager` class
  - [ ] Abstract trigger interface: `arm()`, `disarm()`, `on_trigger(callback)`
  - [ ] Read default mode from `TRIGGER_MODE` config
  - [ ] Allow runtime mode switching from dashboard

- [ ] **4.2 Implement immediate trigger**
  - [ ] Detect USB connection to target (monitor UDC state changes)
  - [ ] Auto-execute active payload on connection
  - [ ] Configurable safety delay (minimum 2 seconds)
  - [ ] Warning log entry for immediate mode activation

- [ ] **4.3 Implement GPIO button trigger**
  - [ ] Set up GPIO input on `GPIO_TRIGGER_PIN` with pull-up resistor
  - [ ] Debounce button input (50ms debounce window)
  - [ ] Single press: execute active payload
  - [ ] Long press (3 seconds): abort current execution
  - [ ] Toggle via `ENABLE_GPIO_TRIGGER`
  - [ ] Graceful skip when GPIO unavailable (dev machine)

- [ ] **4.4 Implement timed trigger**
  - [ ] Start countdown timer on arm (`TRIGGER_DELAY_SECONDS`)
  - [ ] Execute active payload when timer expires
  - [ ] Cancel timer if disarmed before expiry
  - [ ] SocketIO countdown broadcast to dashboard
  - [ ] LED blink pattern during countdown (if enabled)

- [ ] **4.5 Implement manual trigger (web UI)**
  - [ ] Route `POST /api/execute` — trigger execution of specified payload
  - [ ] Route `POST /api/abort` — abort current execution
  - [ ] CSRF protection on both routes
  - [ ] Return execution ID on trigger
  - [ ] SocketIO status updates during execution

- [ ] **4.6 Implement execution logging**
  - [ ] Create `src/logger.py` with `ExecutionLogger` class
  - [ ] `start_execution(payload_id, trigger_mode)` — create `execution_logs` record
  - [ ] `log_keystroke(execution_id, command, argument, hid_report)` — append to `keystroke_logs`
  - [ ] `complete_execution(execution_id, status)` — finalize record with duration and count
  - [ ] Calculate `duration_ms` and `keystrokes_sent` on completion
  - [ ] All timestamps in ISO-8601 UTC with microsecond precision
  - [ ] Toggle per-keystroke logging via `LOG_KEYSTROKES`
  - [ ] Toggle all logging via `ENABLE_EXECUTION_LOGGING`

- [ ] **4.7 Build log viewer page**
  - [ ] Create `templates/logs.html`
  - [ ] Paginated list of execution logs (newest first)
  - [ ] Expandable detail view with keystroke log
  - [ ] Filter by payload, status, trigger mode, date range
  - [ ] Color-coded status badges (running, completed, aborted, error)
  - [ ] Real-time streaming of active execution keystrokes via SocketIO
  - [ ] Client handler in `static/js/logs.js`

- [ ] **4.8 Implement log export**
  - [ ] Route `GET /api/logs/export?format=csv` — export execution logs as CSV
  - [ ] Route `GET /api/logs/export?format=json` — export execution logs as JSON
  - [ ] Include keystroke details in export
  - [ ] Date range filter parameter
  - [ ] Authentication required for export

- [ ] **4.9 Write Phase 4 tests**
  - [ ] Test trigger manager arm/disarm lifecycle
  - [ ] Test immediate trigger (USB connection detection)
  - [ ] Test GPIO button trigger (mocked RPi.GPIO, debounce)
  - [ ] Test timed trigger (countdown, cancellation)
  - [ ] Test manual trigger (web API, CSRF)
  - [ ] Test execution logging (start, keystroke logging, complete)
  - [ ] Test log viewer API (pagination, filters)
  - [ ] Test log export (CSV format, JSON format)
  - [ ] Test abort functionality

---

## Phase 5 — OS Detection, Dual-Mode USB & WiFi AP

- [ ] **5.1 Implement target OS detection**
  - [ ] Create `src/os_detect.py`
  - [ ] Monitor USB descriptor requests during enumeration
  - [ ] Analyze request patterns to identify OS:
    - Windows: specific descriptor order and timing
    - macOS: unique string descriptor requests
    - Linux: minimal descriptor requests
    - ChromeOS: specific WebUSB descriptor requests
  - [ ] Return detected OS string or `unknown`
  - [ ] Log detection result per execution
  - [ ] Toggle via `ENABLE_OS_DETECTION`

- [ ] **5.2 Integrate OS detection into DuckyScript**
  - [ ] Populate `$TARGET_OS` variable from detection result
  - [ ] Enable `IFOS WINDOWS` / `IFOS MACOS` / `IFOS LINUX` conditionals
  - [ ] Log OS-specific branch taken during execution
  - [ ] Fallback: if detection disabled, `$TARGET_OS` = `unknown` and all IFOS blocks skip

- [ ] **5.3 Implement dual-mode USB (composite gadget)**
  - [ ] Create `src/mass_storage.py`
  - [ ] Create disk image file (`dd if=/dev/zero of=data/storage.img bs=1M count=64`)
  - [ ] Format image as FAT32 (`mkfs.vfat`)
  - [ ] Add mass storage function to ConfigFS composite gadget alongside HID
  - [ ] Mount/unmount image locally for file access
  - [ ] Implement `write_to_storage(filename, data)` for exfiltration payloads
  - [ ] Toggle via `ENABLE_MASS_STORAGE`
  - [ ] Configurable image size (`MASS_STORAGE_SIZE_MB`)

- [ ] **5.4 Implement WiFi Access Point**
  - [ ] Create `src/wifi_ap.py`
  - [ ] Generate `hostapd.conf` from config (SSID, password, channel)
  - [ ] Generate `dnsmasq.conf` for DHCP (IP range, gateway, DNS)
  - [ ] Configure network interface (`wlan0`) with static IP
  - [ ] Start/stop hostapd and dnsmasq services
  - [ ] Implement captive portal redirect to dashboard
  - [ ] Toggle via `ENABLE_WIFI_AP`

- [ ] **5.5 Create WiFi AP setup script**
  - [ ] Create `scripts/setup_wifi_ap.sh`
  - [ ] Install `hostapd` and `dnsmasq` if not present
  - [ ] Configure `wlan0` for AP mode
  - [ ] Enable IP forwarding (if internet sharing needed)
  - [ ] Verify AP is broadcasting
  - [ ] Print SSID and dashboard URL

- [ ] **5.6 Implement status LED**
  - [ ] Set up GPIO output on `GPIO_LED_PIN`
  - [ ] Blink patterns: slow = idle, fast = executing, solid = waiting for trigger
  - [ ] Off when disabled or GPIO unavailable
  - [ ] Error pattern (SOS blink) on execution failure
  - [ ] Toggle via `ENABLE_STATUS_LED`

- [ ] **5.7 Write Phase 5 tests**
  - [ ] Test OS detection (mocked USB descriptor data per OS)
  - [ ] Test DuckyScript OS variable and conditional integration
  - [ ] Test mass storage image creation and file write (mocked filesystem)
  - [ ] Test composite gadget configuration (mocked ConfigFS)
  - [ ] Test WiFi AP config generation (hostapd.conf, dnsmasq.conf)
  - [ ] Test WiFi AP start/stop (mocked systemd)
  - [ ] Test LED patterns (mocked GPIO)

---

## Phase 6 — Deployment & Documentation

- [ ] **6.1 Create deploy script**
  - [ ] Create `deploy/deploy_to_pi.sh`
  - [ ] rsync project to `rasp-pi` (pi@192.168.216.90)
  - [ ] Exclude `.venv`, `__pycache__`, `.git`, `data/`
  - [ ] Remote `pip install -r requirements.txt`
  - [ ] Print restart instructions

- [ ] **6.2 Create USB gadget setup script (finalize)**
  - [ ] Ensure `scripts/setup_usb_gadget.sh` handles all edge cases
  - [ ] Idempotent (safe to run multiple times)
  - [ ] Verify `/dev/hidg0` created
  - [ ] Verify mass storage device if enabled

- [ ] **6.3 Create OS dependency installer**
  - [ ] Create `scripts/install_deps.sh`
  - [ ] Install `hostapd`, `dnsmasq`, `python3-venv`, `python3-dev`
  - [ ] Enable `dwc2` overlay for USB OTG
  - [ ] Load `libcomposite` module
  - [ ] Print summary of installed components

- [ ] **6.4 Write systemd service unit**
  - [ ] Create service file for `rubber-ducky`
  - [ ] Configure `After=network-online.target`
  - [ ] Configure `ExecStartPre` for USB gadget setup
  - [ ] Configure restart on failure with 10s delay
  - [ ] Document enable/start commands in README

- [ ] **6.5 Write threat model document**
  - [ ] Create `docs/threat_model.md`
  - [ ] Document all threat vectors and mitigations
  - [ ] Include data flow diagram
  - [ ] Include trust boundary analysis
  - [ ] Legal and ethical considerations
  - [ ] Security recommendations for deployment

- [ ] **6.6 Write DuckyScript reference**
  - [ ] Create `docs/duckyscript_reference.md`
  - [ ] Document all supported commands with examples
  - [ ] Document variable substitution syntax
  - [ ] Document conditional execution (IFOS)
  - [ ] Include example payloads with explanations

- [ ] **6.7 Write anti-detection documentation**
  - [ ] Create `docs/anti_detection.md`
  - [ ] Document how EDR systems detect HID attacks
  - [ ] USB device fingerprinting and VID/PID checking
  - [ ] Keystroke speed analysis and behavioral detection
  - [ ] Kernel-level HID monitoring tools
  - [ ] Defensive recommendations for blue teams

- [ ] **6.8 Final integration testing**
  - [ ] Test full payload execution cycle on Pi 4 with real USB-C connection
  - [ ] Test all trigger modes with real hardware
  - [ ] Test DuckyScript interpreter with sample payloads on Windows, macOS, Linux targets
  - [ ] Test dual-mode USB (HID + mass storage simultaneously)
  - [ ] Test WiFi AP payload editing from phone
  - [ ] Test dashboard under multiple concurrent sessions
  - [ ] Test systemd service lifecycle (start, stop, restart, crash recovery)
  - [ ] Verify execution logs match actual keystrokes sent

- [ ] **6.9 Finalize documentation**
  - [ ] Update README with final usage instructions
  - [ ] Verify all `.env` variables documented
  - [ ] Update TSD with any changes from implementation
  - [ ] Update task.md with completion status
  - [ ] Review and update troubleshooting table
