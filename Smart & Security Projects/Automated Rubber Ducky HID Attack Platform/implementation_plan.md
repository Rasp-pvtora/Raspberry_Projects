# Implementation Plan — Automated Rubber Ducky HID Attack Platform

## Phase 1 — Project Foundation & USB HID Gadget

**Goal:** Scaffold the project, configure environment loading, set up the database, and build the core USB HID gadget with basic keystroke execution.

- [ ] **Step 1.1 — Initialize Project Structure**
  - [ ] Create directory tree:
    ```
    src/, templates/, static/css/, static/js/, tests/, deploy/, scripts/, docs/, data/, payloads/recon/, payloads/exfiltration/, payloads/configuration/
    ```
  - [ ] Create `pyproject.toml` with project name, version, Python ≥3.11, and entry point `src.app`
  - [ ] Create `requirements.txt`:
    ```
    flask
    flask-socketio
    eventlet
    bcrypt
    python-dotenv
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
  - [ ] Add `is_enabled(feature: str) -> bool` helper for toggle checks
  - [ ] Write `tests/test_config.py` — test loading, defaults, type conversion, missing keys

- [ ] **Step 1.3 — SQLite Database Module**
  - [ ] Create `src/database.py`
  - [ ] Implement `get_connection(db_path)` with WAL mode pragma
  - [ ] Implement `init_db(conn)` — creates all 4 tables (see TSD §3)
  - [ ] Implement CRUD functions:
    - `insert_payload(conn, payload_data)` / `update_payload(conn, payload_id, data)`
    - `get_payload(conn, payload_id)` / `list_payloads(conn, category, target_os)`
    - `delete_payload(conn, payload_id)`
    - `insert_execution_log(conn, log_data)` / `update_execution_log(conn, log_id, data)`
    - `insert_keystroke_log(conn, keystroke_data)`
    - `get_execution_logs(conn, limit, offset, filters)`
    - `get_keystroke_logs(conn, execution_id)`
    - `get_setting(conn, key)` / `set_setting(conn, key, value)`
  - [ ] Use parameterized queries for all DB operations
  - [ ] Write `tests/test_database.py` — test schema creation, all CRUD ops, WAL mode

- [ ] **Step 1.4 — ConfigFS USB HID Gadget**
  - [ ] Create `src/hid_gadget.py`
  - [ ] Implement `HIDGadget` class:
    - `setup()` — create gadget directory structure under `/sys/kernel/config/usb_gadget/rubber_ducky/`
    - Write `idVendor`, `idProduct`, `bcdDevice`, `bcdUSB` to gadget dir
    - Create `strings/0x409/` with `manufacturer`, `product`, `serialnumber`
    - Create `configs/c.1/strings/0x409/` with `configuration`
    - Create `functions/hid.usb0/` with `protocol=1`, `subclass=1`, `report_length=8`
    - Write HID keyboard report descriptor to `functions/hid.usb0/report_desc`
    - Symlink function to config: `configs/c.1/ -> functions/hid.usb0`
    - Write UDC name to `UDC` file to bind gadget
    - `teardown()` — unlink, remove function, remove config, remove gadget
    - `is_active() -> bool` — check if `/dev/hidg0` exists and gadget bound
  - [ ] Handle `PermissionError` (not root), missing kernel modules, existing gadget
  - [ ] Toggle via `ENABLE_HID_GADGET`

- [ ] **Step 1.5 — Keystroke Execution Engine**
  - [ ] Create `src/executor.py`
  - [ ] Implement US keyboard layout keycode table:
    - Letters a–z: `0x04`–`0x1D`
    - Numbers 0–9: `0x27`, `0x1E`–`0x26`
    - Symbols (shift variants): `!@#$%^&*()` etc.
    - Special keys: ENTER (`0x28`), ESC (`0x29`), BACKSPACE (`0x2A`), TAB (`0x2B`)
    - Arrow keys: RIGHT (`0x4F`), LEFT (`0x50`), DOWN (`0x51`), UP (`0x52`)
    - F-keys: F1–F12 (`0x3A`–`0x45`)
    - Modifiers: CTRL (`0x01`), SHIFT (`0x02`), ALT (`0x04`), GUI (`0x08`)
  - [ ] Implement `KeystrokeExecutor` class:
    - `__init__(device_path, default_delay_ms)` — open `/dev/hidg0`
    - `send_report(modifier_byte, keycode)` — write 8-byte HID report
    - `send_key(key, modifiers=[])` — lookup keycode, build report, send + release
    - `send_string(text, delay_ms=None)` — iterate chars, send each with delay
    - `release_all()` — send all-zero report (no keys pressed)
    - `close()` — close device file descriptor
  - [ ] Configurable inter-keystroke delay (`DEFAULT_DELAY_MS`)
  - [ ] Write `tests/test_executor.py` — test keycode mapping, report construction, string sending

- [ ] **Step 1.6 — Mock Mode**
  - [ ] Implement `MockExecutor` in `src/executor.py`:
    - Same interface as `KeystrokeExecutor`
    - Writes keystrokes to in-memory buffer and logging output instead of `/dev/hidg0`
    - Simulates timing delays
    - Records all sent reports for test assertion
  - [ ] Factory function: `create_executor(config) -> KeystrokeExecutor | MockExecutor`
  - [ ] Activate via `MOCK_MODE=true`
  - [ ] Write `tests/test_mock.py` — test mock output, timing simulation, report recording

- [ ] **Step 1.7 — USB Gadget Setup Script**
  - [ ] Create `scripts/setup_usb_gadget.sh`:
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    # Load kernel modules
    modprobe libcomposite
    # Check dtoverlay
    if ! grep -q "dtoverlay=dwc2" /boot/config.txt; then
        echo "dtoverlay=dwc2" >> /boot/config.txt
        echo "[!] Added dwc2 overlay — REBOOT REQUIRED"
    fi
    # Add to /etc/modules if not present
    grep -q "dwc2" /etc/modules || echo "dwc2" >> /etc/modules
    grep -q "libcomposite" /etc/modules || echo "libcomposite" >> /etc/modules
    echo "[✓] USB gadget prerequisites configured"
    ```
  - [ ] Make executable (`chmod +x`)

- [ ] **Step 1.8 — Phase 1 Tests**
  - [ ] `tests/test_config.py` — loading, defaults, type conversion, feature toggles
  - [ ] `tests/test_database.py` — schema creation, CRUD for all tables, WAL mode
  - [ ] `tests/test_executor.py` — keycode table, HID report construction, string-to-keystrokes
  - [ ] `tests/test_mock.py` — mock executor output, timing, report buffer
  - [ ] `tests/test_hid_gadget.py` — setup/teardown with mocked filesystem, error handling

**Checkpoint:** USB HID gadget configurable, keystroke executor can type strings via HID reports (real or mock). Config and DB fully tested.

---

## Phase 2 — DuckyScript Interpreter & Payload Library

**Goal:** Build a full Hak5-compatible DuckyScript interpreter and categorized payload management system.

- [ ] **Step 2.1 — DuckyScript Parser**
  - [ ] Create `src/duckyscript.py` with `DuckyScriptParser` class
  - [ ] Implement `parse(script_text: str) -> list[Instruction]`:
    - Split into lines, strip whitespace
    - Skip empty lines and `REM` comment lines
    - Tokenize each line: `command argument` (split on first space)
    - Validate command against known command set
    - Return list of `Instruction(command, argument, line_number)` named tuples
  - [ ] Implement `validate(script_text: str) -> list[Error]`:
    - Check for unknown commands
    - Check for missing required arguments (e.g., `STRING` needs text)
    - Check `DELAY` argument is numeric
    - Return error list with line numbers and messages

- [ ] **Step 2.2 — DuckyScript Command Execution**
  - [ ] Implement `DuckyScriptRunner(executor, logger)`:
    - `execute(instructions: list, variables: dict)` — iterate instructions and dispatch
    - Command handlers:
      - `_handle_string(text)` — `executor.send_string(text)`
      - `_handle_delay(ms)` — `time.sleep(ms / 1000)`
      - `_handle_key(key)` — `executor.send_key(key)` (ENTER, TAB, etc.)
      - `_handle_combo(keys)` — `executor.send_key(key, modifiers)` (GUI r, CTRL ALT DELETE)
      - `_handle_default_delay(ms)` — update global delay
      - `_handle_repeat(n)` — re-execute previous instruction N times
    - Support abort flag (checked between commands)
    - Emit SocketIO events per command for live dashboard updates

- [ ] **Step 2.3 — Variable Substitution**
  - [ ] Implement `substitute_variables(text: str, variables: dict) -> str`:
    - Replace `$TARGET_OS` with detected OS
    - Replace `$TIMESTAMP` with ISO-8601 current time
    - Replace `$HOSTNAME` with `socket.gethostname()`
    - Replace `$PAYLOAD_NAME` with current payload name
  - [ ] Call substitution on `STRING` arguments before sending

- [ ] **Step 2.4 — Conditional Execution**
  - [ ] Implement `IFOS <OS>` / `ENDIF` block handling:
    - When `IFOS <OS>` encountered, check if `variables['TARGET_OS']` matches `<OS>`
    - If match: execute enclosed commands normally
    - If no match: skip commands until matching `ENDIF`
    - Track nesting depth (max 3) to handle nested IFOS blocks
    - Raise error for unmatched IFOS/ENDIF

- [ ] **Step 2.5 — Payload Manager**
  - [ ] Create `src/payload_manager.py` with `PayloadManager` class:
    - `__init__(config, db_conn)` — set payload directory, init DB
    - `list_payloads(category=None, target_os=None) -> list[dict]` — query DB with filters
    - `get_payload(payload_id: int) -> dict` — return payload with content loaded from file
    - `create_payload(name, content, category, target_os, description, risk_level) -> int`:
      - Sanitize filename from name (slug)
      - Write content to `payloads/<category>/<filename>.txt`
      - Insert DB record, return ID
    - `update_payload(payload_id, **fields)` — update file and DB record
    - `delete_payload(payload_id)` — remove file and DB record
    - `sync_filesystem()` — scan `payloads/` tree, add missing files to DB, remove orphan records
    - `import_payload(file_path) -> int` — read external file, create payload
    - `export_payload(payload_id) -> str` — return raw content
  - [ ] Toggle via `ENABLE_PAYLOAD_LIBRARY`

- [ ] **Step 2.6 — Sample Payloads**
  - [ ] Create category directories: `payloads/recon/`, `payloads/exfiltration/`, `payloads/configuration/`
  - [ ] Write sample payloads with `REM` headers documenting purpose, target OS, risk level, and authorization requirement:
    - `recon/system_info_windows.txt` — open PowerShell, run `systeminfo`, save to file
    - `recon/wifi_passwords_windows.txt` — `netsh wlan show profiles` + key extraction
    - `recon/system_info_linux.txt` — open terminal, run `uname -a`, `ifconfig`, etc.
    - `configuration/install_tool_windows.txt` — silent software installation template
    - `configuration/set_wallpaper_windows.txt` — harmless desktop wallpaper change (demo)
    - `exfiltration/copy_to_storage.txt` — copy specified files to mass storage device

- [ ] **Step 2.7 — Phase 2 Tests**
  - [ ] `tests/test_duckyscript.py`:
    - Test parser: valid scripts, malformed lines, empty script, comments only
    - Test all commands: STRING, DELAY, ENTER, GUI, ALT, CTRL, combos, F-keys
    - Test DEFAULT_DELAY and REPEAT directives
    - Test variable substitution (all 4 variables, missing variable graceful handling)
    - Test conditional execution (matching OS, non-matching, nested, unmatched ENDIF)
    - Test syntax validation (unknown command, missing argument, invalid delay)
  - [ ] `tests/test_payload_manager.py`:
    - Test CRUD: create, read, update, delete payloads
    - Test filesystem sync (new file detected, orphan removed)
    - Test import/export round-trip
    - Test category and OS filtering

**Checkpoint:** Full DuckyScript interpreter with variables and conditionals. Payload library with categorized sample scripts. All parsed and manageable via PayloadManager.

---

## Phase 3 — Web Dashboard & Authentication

**Goal:** Build the authenticated dark-themed web dashboard with payload editor and real-time execution status.

- [ ] **Step 3.1 — Flask App Factory**
  - [ ] Create `src/app.py`:
    - `create_app(config)` factory pattern
    - Initialize Flask-SocketIO with eventlet mode
    - Register route handlers
    - Initialize database on startup
    - Initialize HID gadget on startup (if enabled and not mock mode)
    - Implement `__main__` block to run the app
  - [ ] Toggle dashboard via `ENABLE_WEB_DASHBOARD`

- [ ] **Step 3.2 — Authentication Module**
  - [ ] Create `src/auth.py`:
    - `verify_password(plaintext, bcrypt_hash) -> bool`
    - `login_user(session, username)` — set session data with expiry timestamp
    - `logout_user(session)` — clear session
    - `is_authenticated(session) -> bool` — check session validity and expiry
    - `login_required(f)` — decorator redirecting to `/login`
  - [ ] Route `GET /login` — render login form
  - [ ] Route `POST /login` — verify credentials, rate limit check, set session
  - [ ] Route `POST /logout` — clear session, redirect to login
  - [ ] Rate limiter: store attempt counts per IP in memory dict with 15-min window
  - [ ] Session expiry: check `SESSION_EXPIRY_HOURS` (default 24h) on each request

- [ ] **Step 3.3 — Dark Theme Templates & CSS**
  - [ ] Create `templates/base.html`:
    - HTML5 boilerplate with dark background (`#1a1a2e`)
    - Navigation bar (app title, HID status indicator, trigger mode badge, logout)
    - Content block, script block
    - SocketIO client script, CodeMirror CDN (on editor pages)
    - Legal disclaimer footer
  - [ ] Create `static/css/style.css`:
    - Dark palette: background `#1a1a2e`, cards `#16213e`, text `#e0e0e0`, accent `#0f3460`
    - Status badges: running (green pulse), completed (green), aborted (yellow), error (red)
    - Risk level badges: critical (red), high (orange), medium (yellow), low (blue)
    - Category badges: recon (blue), exfiltration (red), configuration (green), custom (gray)
    - Table styling, responsive grid, form inputs, code editor container
    - Mobile-responsive layout for phone-based payload editing

- [ ] **Step 3.4 — Login Page**
  - [ ] Create `templates/login.html` extending base
  - [ ] Centered login card with username/password fields
  - [ ] CSRF token hidden field
  - [ ] Flash message area for errors ("Invalid credentials", "Rate limited")
  - [ ] Legal disclaimer notice below login form

- [ ] **Step 3.5 — Dashboard Page**
  - [ ] Create `templates/dashboard.html` extending base
  - [ ] Summary cards row: Active Payload, Trigger Mode, HID Status, Executions Today
  - [ ] Recent payloads list with quick-execute buttons
  - [ ] Current execution status panel: idle / running (progress) / last result
  - [ ] Recent execution log feed (last 10 entries with status badges)
  - [ ] USB connection indicator (target connected/disconnected)
  - [ ] Target OS badge (if detected)

- [ ] **Step 3.6 — Payload Editor Page**
  - [ ] Create `templates/editor.html` extending base
  - [ ] CodeMirror 6 integration with custom DuckyScript syntax highlighting mode
  - [ ] Toolbar: Save, Save As, Load (dropdown), New, Validate, Execute
  - [ ] Metadata panel: name, category (dropdown), target OS (dropdown), description, risk level
  - [ ] Syntax validation panel below editor (errors with clickable line numbers)
  - [ ] Keystroke preview panel (show translated HID commands)
  - [ ] Create `static/js/editor.js` — editor initialization, save/load AJAX, validation

- [ ] **Step 3.7 — Payload Library Page**
  - [ ] Create `templates/library.html` extending base
  - [ ] Card grid view of all payloads (name, category badge, OS badge, risk badge)
  - [ ] Filter bar: category buttons, OS dropdown, search input
  - [ ] Sort options: name, category, execution count, last executed, risk level
  - [ ] Card actions: Edit (→ editor), Duplicate, Delete (with confirmation), Execute
  - [ ] Empty state message when no payloads match filters

- [ ] **Step 3.8 — SocketIO Real-time Events**
  - [ ] Server emits:
    - `execution_start` — `{payload_name, trigger_mode, timestamp}`
    - `keystroke_sent` — `{command, argument, sequence_num, timestamp}` (per keystroke)
    - `execution_complete` — `{status, duration_ms, keystrokes_sent}`
    - `execution_error` — `{error_message, line_number}`
    - `hid_status` — `{active: bool, device_path}`
    - `usb_connected` — `{connected: bool, target_os}`
  - [ ] Create `static/js/dashboard.js`:
    - Connect to SocketIO namespace
    - Handle all events — update status panels, execution feed, badges
    - Animate execution progress (keystroke counter, elapsed time)

- [ ] **Step 3.9 — Settings Panel**
  - [ ] Create `templates/settings.html` extending base
  - [ ] Trigger mode selector (radio buttons: immediate, button, timed, manual)
  - [ ] Timed trigger delay input (only shown when timed selected)
  - [ ] Default keystroke delay slider
  - [ ] Feature status table (read-only, showing `.env` toggle states)
  - [ ] HID gadget status card with reset/reinitialize button
  - [ ] WiFi AP status card (SSID, connected clients, if enabled)
  - [ ] Route `POST /settings/trigger-mode` — save trigger mode to settings table

- [ ] **Step 3.10 — Phase 3 Tests**
  - [ ] `tests/test_auth.py` — login, logout, invalid creds, rate limiting, session expiry
  - [ ] `tests/test_api.py`:
    - Dashboard route (auth required, data populated)
    - Editor save/load/validate API endpoints
    - Library CRUD API (list, create, update, delete)
    - Settings update API
    - SocketIO event emission on execution
  - [ ] Test CSRF protection on all POST routes

**Checkpoint:** Fully functional dark-themed dashboard with payload editor (CodeMirror), library browser, trigger controls, and real-time execution status. All protected by bcrypt auth with rate limiting.

---

## Phase 4 — Trigger Modes & Execution Logging

**Goal:** Implement all four trigger modes and detailed per-keystroke execution logging with export.

- [ ] **Step 4.1 — Trigger Mode Manager**
  - [ ] Create `src/trigger.py` with `TriggerManager` class:
    - `__init__(config, executor, payload_manager, logger)` — initialize with dependencies
    - `set_mode(mode: str)` — switch trigger mode at runtime
    - `arm(payload_id: int)` — arm the selected payload for the current trigger
    - `disarm()` — cancel any pending trigger
    - `on_trigger()` — callback that starts execution
    - `get_status() -> dict` — return current mode, armed state, active payload

- [ ] **Step 4.2 — Immediate Trigger**
  - [ ] Monitor UDC (USB Device Controller) state for target connection:
    - Watch `/sys/class/udc/*/state` for `configured` (target connected)
    - Background thread polling at 500ms intervals
  - [ ] On connection detected: start execution after 2-second safety delay
  - [ ] Log warning: immediate mode is high-risk
  - [ ] Only trigger once per connection cycle (require disconnect + reconnect for re-trigger)

- [ ] **Step 4.3 — GPIO Button Trigger**
  - [ ] Implement `ButtonTrigger` class:
    - Set up GPIO input on `GPIO_TRIGGER_PIN` with `GPIO.PUD_UP`
    - Register falling-edge interrupt with 50ms debounce (`bouncetime=50`)
    - Single press callback: invoke `on_trigger()`
    - Long press detection (3 seconds): invoke abort
    - Cleanup GPIO on disarm
  - [ ] Toggle via `ENABLE_GPIO_TRIGGER`
  - [ ] Graceful fallback when RPi.GPIO unavailable (log warning, skip)

- [ ] **Step 4.4 — Timed Trigger**
  - [ ] Implement `TimedTrigger` class:
    - `arm(delay_seconds)` — start countdown timer in background thread
    - Emit SocketIO `countdown` event every second `{remaining_seconds}`
    - On timer expiry: invoke `on_trigger()`
    - `disarm()` — cancel timer before expiry
    - LED fast blink during countdown (if enabled)

- [ ] **Step 4.5 — Manual Trigger (Web UI)**
  - [ ] Route `POST /api/execute` — accept `{payload_id}`, validate, start execution
  - [ ] Route `POST /api/abort` — set abort flag, wait for current command to finish
  - [ ] CSRF protection on both endpoints
  - [ ] Return `{execution_id, status}` response
  - [ ] Block if execution already in progress (return 409 Conflict)
  - [ ] SocketIO events broadcast execution lifecycle

- [ ] **Step 4.6 — Execution Logger**
  - [ ] Create `src/logger.py` with `ExecutionLogger` class:
    - `start(payload_id, payload_name, trigger_mode) -> int`:
      - Insert `execution_logs` record with `status='running'`
      - Return execution ID
    - `log_keystroke(execution_id, command, argument, hid_report, sequence_num)`:
      - Insert `keystroke_logs` record (ISO-8601 with microseconds)
      - Only if `LOG_KEYSTROKES=true`
    - `complete(execution_id, status)`:
      - Update `execution_logs` with `completed_at`, `status`, `duration_ms`, `keystrokes_sent`
      - Increment `payloads.execution_count` and set `last_executed_at`
    - `get_log(execution_id) -> dict` — return full log with keystrokes
    - `list_logs(limit, offset, filters) -> list` — paginated log list
  - [ ] Toggle via `ENABLE_EXECUTION_LOGGING`

- [ ] **Step 4.7 — Log Viewer Page**
  - [ ] Create `templates/logs.html` extending base
  - [ ] Paginated table: execution ID, payload name, trigger mode, status badge, duration, keystroke count, timestamp
  - [ ] Expandable row: full keystroke log with sequence numbers, commands, timestamps
  - [ ] Filter panel: payload (dropdown), status (checkboxes), trigger mode, date range
  - [ ] Live execution stream: when execution running, auto-scroll keystroke feed
  - [ ] Create `static/js/logs.js` — pagination, filters, SocketIO keystroke streaming

- [ ] **Step 4.8 — Log Export**
  - [ ] Route `GET /api/logs/export`:
    - Query params: `format` (csv/json), `execution_id` (optional), `from_date`, `to_date`
    - CSV: headers + rows for execution logs (include keystroke counts)
    - JSON: nested structure with execution + keystroke array
    - Filename: `execution_logs_YYYYMMDD_HHMMSS.{csv|json}`
    - Set `Content-Disposition: attachment` header
  - [ ] Authentication required

- [ ] **Step 4.9 — Phase 4 Tests**
  - [ ] `tests/test_trigger.py`:
    - Test manager arm/disarm/mode switch
    - Test immediate trigger (mocked UDC state file)
    - Test GPIO button (mocked RPi.GPIO, debounce, long press)
    - Test timed trigger (countdown, cancel, expiry)
    - Test manual trigger (API endpoint, abort, conflict on duplicate)
  - [ ] `tests/test_logger.py`:
    - Test execution start/complete lifecycle
    - Test keystroke logging (enabled and disabled)
    - Test duration calculation
    - Test log listing (pagination, filters)
    - Test log export (CSV format, JSON format, date range)

**Checkpoint:** All four trigger modes functional. Execution logging captures every keystroke with timestamps. Log viewer with real-time streaming and export for pentest reports.

---

## Phase 5 — OS Detection, Dual-Mode USB & WiFi AP

**Goal:** Add target OS detection, dual-mode USB composite gadget, WiFi AP, and status LED.

- [ ] **Step 5.1 — Target OS Detection**
  - [ ] Create `src/os_detect.py` with `OSDetector` class:
    - `detect() -> str` — analyze USB enumeration and return OS string
    - Monitor USB host descriptor requests via kernel log (`dmesg`) or gadget debug interface
    - Detection heuristics:
      - **Windows:** Requests `Microsoft OS Descriptor` (vendor code 0x01), specific timing patterns
      - **macOS:** Requests Apple-specific string descriptors, unique endpoint polling behavior
      - **Linux:** Minimal descriptor requests, no vendor-specific descriptors
      - **ChromeOS:** WebUSB descriptor requests
    - Return `'windows'`, `'macos'`, `'linux'`, `'chromeos'`, or `'unknown'`
    - Cache result per USB connection cycle
  - [ ] Toggle via `ENABLE_OS_DETECTION`

- [ ] **Step 5.2 — DuckyScript OS Integration**
  - [ ] After OS detection, populate `variables['TARGET_OS']` for the runner
  - [ ] `$TARGET_OS` substitution in `STRING` commands
  - [ ] `IFOS WINDOWS` / `IFOS MACOS` / `IFOS LINUX` conditionals use detected OS
  - [ ] When detection disabled: `$TARGET_OS = 'unknown'`, all `IFOS` blocks skip
  - [ ] Log which OS-specific branches were taken during execution

- [ ] **Step 5.3 — Dual-Mode USB (Composite Gadget)**
  - [ ] Create `src/mass_storage.py` with `MassStorageGadget` class:
    - `create_image(path, size_mb)` — `dd` + `mkfs.vfat` to create FAT32 image
    - `setup_gadget()` — add mass storage function to existing composite gadget:
      - Create `functions/mass_storage.usb0/` in ConfigFS
      - Set `lun.0/file` to disk image path
      - Set `lun.0/removable=1`, `lun.0/cdrom=0`
      - Symlink to config alongside HID function
    - `mount_image(mount_point)` — loop mount image for local file access
    - `unmount_image()` — unmount cleanly
    - `write_file(filename, data)` — mount, write, unmount
    - `teardown()` — remove mass storage function from gadget
  - [ ] Toggle via `ENABLE_MASS_STORAGE`

- [ ] **Step 5.4 — WiFi Access Point Manager**
  - [ ] Create `src/wifi_ap.py` with `WiFiAP` class:
    - `generate_hostapd_conf()` — write `hostapd.conf` from config values:
      ```
      interface=wlan0
      ssid={WIFI_AP_SSID}
      hw_mode=g
      channel={WIFI_AP_CHANNEL}
      wpa=2
      wpa_passphrase={WIFI_AP_PASSWORD}
      wpa_key_mgmt=WPA-PSK
      rsn_pairwise=CCMP
      ```
    - `generate_dnsmasq_conf()` — write `dnsmasq.conf`:
      ```
      interface=wlan0
      dhcp-range=10.0.0.10,10.0.0.50,255.255.255.0,24h
      address=/#/{WIFI_AP_IP}
      ```
    - `configure_interface()` — set static IP on wlan0
    - `start()` — start hostapd and dnsmasq (systemd or direct)
    - `stop()` — stop services, release interface
    - `get_status() -> dict` — return running state, connected clients, SSID
  - [ ] Toggle via `ENABLE_WIFI_AP`

- [ ] **Step 5.5 — WiFi AP Setup Script**
  - [ ] Create `scripts/setup_wifi_ap.sh`:
    - Install `hostapd` and `dnsmasq` (`apt install`)
    - Stop default wpa_supplicant on wlan0
    - Configure static IP on wlan0
    - Start hostapd and dnsmasq
    - Verify AP is broadcasting (`iw dev wlan0 info`)
    - Print SSID and dashboard URL

- [ ] **Step 5.6 — Status LED**
  - [ ] Implement LED control in `src/trigger.py`:
    - `set_led(pattern)` — control GPIO LED pin
    - Patterns:
      - `idle`: LED off
      - `armed`: slow blink (1 Hz)
      - `countdown`: fast blink (4 Hz)
      - `executing`: solid on
      - `complete`: 3 quick blinks then off
      - `error`: SOS pattern (··· ——— ···)
    - Background thread for blink patterns
    - Cleanup GPIO on shutdown
  - [ ] Toggle via `ENABLE_STATUS_LED`

- [ ] **Step 5.7 — Phase 5 Tests**
  - [ ] `tests/test_os_detect.py`:
    - Test Windows detection (mocked USB descriptor data)
    - Test macOS detection (mocked descriptor pattern)
    - Test Linux detection (minimal descriptors)
    - Test unknown fallback
    - Test disabled mode (returns 'unknown')
  - [ ] `tests/test_mass_storage.py`:
    - Test image creation (mocked dd/mkfs)
    - Test composite gadget ConfigFS setup (mocked filesystem)
    - Test file write to mounted image (mocked mount)
  - [ ] `tests/test_wifi_ap.py`:
    - Test hostapd.conf generation (verify all fields)
    - Test dnsmasq.conf generation
    - Test start/stop (mocked systemd)
    - Test status reporting

**Checkpoint:** OS detection populates DuckyScript variables. Dual-mode USB presents HID + mass storage. WiFi AP allows wireless payload editing. Status LED provides visual feedback.

---

## Phase 6 — Deployment & Documentation

**Goal:** Finalize deployment pipeline, systemd integration, and all project documentation.

- [ ] **Step 6.1 — Deploy Script**
  - [ ] Create `deploy/deploy_to_pi.sh`:
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    PI_HOST="rasp-pi"
    REMOTE_DIR="/home/pi/rubber-ducky"
    rsync -avz --exclude '.venv' --exclude '__pycache__' \
        --exclude '*.pyc' --exclude '.git' --exclude 'data/' \
        ./ "${PI_HOST}:${REMOTE_DIR}/"
    ssh "${PI_HOST}" "cd ${REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt"
    echo "[✓] Deploy complete. Restart: sudo systemctl restart rubber-ducky"
    ```
  - [ ] Make executable (`chmod +x`)

- [ ] **Step 6.2 — OS Dependency Installer**
  - [ ] Create `scripts/install_deps.sh`:
    - `sudo apt update`
    - `sudo apt install -y hostapd dnsmasq python3-venv python3-dev`
    - Load `dwc2` overlay and `libcomposite` module
    - Configure `/boot/config.txt` for OTG mode
    - Verify installations
    - Print summary

- [ ] **Step 6.3 — systemd Service**
  - [ ] Create service unit (documented in README):
    ```ini
    [Unit]
    Description=Automated Rubber Ducky HID Attack Platform
    After=network-online.target
    Wants=network-online.target

    [Service]
    Type=simple
    User=root
    WorkingDirectory=/home/pi/rubber-ducky
    EnvironmentFile=/home/pi/rubber-ducky/.env
    ExecStartPre=/bin/bash scripts/setup_usb_gadget.sh
    ExecStart=/home/pi/rubber-ducky/.venv/bin/python -m src.app
    Restart=on-failure
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```
  - [ ] Commands: `daemon-reload`, `enable`, `start`, `journalctl -f`

- [ ] **Step 6.4 — Threat Model Document**
  - [ ] Create `docs/threat_model.md`:
    - Trust boundaries (Pi, USB connection, WiFi AP, target system)
    - Data flow diagram (payload → parser → executor → HID → target)
    - Threat vectors table (unauthorized use, payload tampering, log exposure, WiFi attack)
    - Mitigation strategies for each threat
    - Legal and ethical considerations
    - Security recommendations for deployment

- [ ] **Step 6.5 — DuckyScript Reference**
  - [ ] Create `docs/duckyscript_reference.md`:
    - Full command reference table (command, syntax, description, example)
    - Modifier key combinations
    - Variable substitution syntax and available variables
    - Conditional execution (IFOS/ENDIF) with examples
    - DEFAULT_DELAY and REPEAT usage
    - Payload writing best practices

- [ ] **Step 6.6 — Anti-Detection Documentation**
  - [ ] Create `docs/anti_detection.md`:
    - How EDR detects HID attacks:
      - Keystroke speed profiling (superhuman typing speed)
      - USB device fingerprinting (VID/PID database checks)
      - Behavioral analysis (rapid command execution patterns)
      - USB device insertion event logging
      - Kernel-level HID monitoring (sysmon, USBGuard)
    - Defensive recommendations for blue teams:
      - USB device whitelisting policies
      - Group Policy restrictions on USB HID
      - Endpoint monitoring alert rules
    - Red team considerations (for authorized testing):
      - Realistic typing speed delays
      - Human-like pause patterns
      - Matching VID/PID to expected keyboard model

- [ ] **Step 6.7 — Integration Testing on Hardware**
  - [ ] Test full payload execution on Pi 4 USB-C → Windows target
  - [ ] Test full payload execution on Pi 4 USB-C → macOS target
  - [ ] Test full payload execution on Pi 4 USB-C → Linux target
  - [ ] Test all trigger modes with real hardware (button, immediate, timed, manual)
  - [ ] Test dual-mode USB (HID typing + mass storage file access simultaneously)
  - [ ] Test WiFi AP: connect from phone → edit payload → execute on target
  - [ ] Test OS detection accuracy across all target types
  - [ ] Test execution log completeness (compare log to observed keystrokes)
  - [ ] Test dashboard under multiple concurrent WiFi AP clients
  - [ ] Test systemd service lifecycle (start, stop, restart, crash recovery)

- [ ] **Step 6.8 — Documentation Finalization**
  - [ ] Review and update `README.md` with any implementation changes
  - [ ] Verify all `.env` variables match actual code usage
  - [ ] Update `TSD.md` with final architecture and any schema changes
  - [ ] Mark completed tasks in `task.md`
  - [ ] Review and update troubleshooting table
  - [ ] Verify legal disclaimer is prominently visible

**Checkpoint:** Project fully deployed on Pi 4, running as systemd service, all documentation complete and accurate. All tests passing. Legal disclaimer prominently displayed.
