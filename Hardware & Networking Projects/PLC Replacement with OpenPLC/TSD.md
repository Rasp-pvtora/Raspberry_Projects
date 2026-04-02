# Technical Specification Document — PLC Replacement with OpenPLC

## 1. Scope

### In Scope

- OpenPLC Runtime installation and GPIO mapping on Raspberry Pi 4/5
- IEC 61131-3 programming (Ladder Logic, Structured Text, Function Block Diagram)
- ScadaBR SCADA visualization and HMI via Modbus polling
- Modbus TCP master/slave communication
- Modbus RTU master/slave communication (RS-485/RS-232)
- I/O expansion via MCP23017 over I2C (up to 128 additional I/O points)
- Fail-safe watchdog timers with configurable safe-state outputs
- Pre-built PLC program library (traffic light, motor, tank level, conveyor)
- OPC-UA server for industrial software integration
- Data logging to SQLite with configurable interval and retention
- Dark-themed Flask + SocketIO web dashboard for monitoring
- bcrypt authentication with rate limiting and session expiry
- Alarm management (threshold-based, state-change, watchdog)
- Mock mode for development/testing without hardware
- All features toggled via `.env`
- SQLite for persistence (WAL mode)
- Deployment via rsync to `rasp-pi` (192.168.216.90)

### Out of Scope

- OpenPLC Editor (runs on desktop PC, not on the Pi itself)
- Analog I/O without PiXtend HAT (Pi has no native ADC/DAC)
- Safety Integrity Level (SIL) certification
- Redundant PLC failover (future enhancement)
- Cloud connectivity or remote access beyond LAN
- PLC-to-PLC networking (IEC 61131-5)
- Proprietary PLC protocol translation (e.g., Profibus, EtherNet/IP)
- Non-Linux host OS for the Pi
- Commercial licensing or paid features
- Mobile app for monitoring

---

## 2. MVP Features (P0)

| ID | Feature | Priority |
|----|---------|----------|
| P0-1 | OpenPLC Runtime installation and GPIO pin mapping | P0 |
| P0-2 | Structured Text program upload and execution | P0 |
| P0-3 | Digital output control via relay modules | P0 |
| P0-4 | Digital input reading via optocoupled modules | P0 |
| P0-5 | Modbus TCP slave (expose I/O as registers) | P0 |
| P0-6 | Fail-safe watchdog timer with output disable | P0 |
| P0-7 | SQLite data logging (I/O states at configurable interval) | P0 |
| P0-8 | Web dashboard (dark theme, I/O monitor, program management) | P0 |
| P0-9 | Authentication (bcrypt, rate limiting 10/15min, 24h session) | P0 |
| P0-10 | SQLite database (schema: io_states, data_logs, programs, alarms, settings) | P0 |
| P0-11 | Alarm generation (high/low threshold, state change) | P0 |
| P0-12 | Mock mode (simulated I/O for dev/testing) | P0 |
| P0-13 | Deploy script (rsync to rasp-pi) | P0 |

### Nice-to-Have (P1/P2)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| P1-1 | ScadaBR SCADA integration | P1 | Requires Java, separate install |
| P1-2 | Modbus TCP master (poll remote slaves) | P1 | Read external sensors/actuators |
| P1-3 | Modbus RTU master/slave | P1 | Serial RS-485 devices |
| P1-4 | MCP23017 I/O expansion | P1 | 16 extra GPIO per chip via I2C |
| P1-5 | Pre-built program library (4 programs) | P1 | Traffic light, motor, tank, conveyor |
| P1-6 | OPC-UA server | P1 | Industrial software integration |
| P1-7 | Ladder Logic program support | P1 | Graphical relay logic |
| P1-8 | Function Block Diagram support | P1 | Graphical dataflow |
| P2-1 | Data log CSV export | P2 | Download historical data |
| P2-2 | Dashboard chart visualization | P2 | Time-series I/O plots |
| P2-3 | PiXtend HAT driver integration | P2 | Analog I/O channels |
| P2-4 | Email/webhook alarm notifications | P2 | Send alerts on alarm trigger |

---

## 3. Database Schema

SQLite with WAL mode enabled. All timestamps stored as ISO-8601 UTC.

### Table: `io_states`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique I/O state record ID |
| pin_name | TEXT | NOT NULL, INDEX | Logical pin name (e.g., `DO_0`, `DI_3`, `EXP_A0`) |
| pin_type | TEXT | NOT NULL | `digital_input`, `digital_output`, `analog_input`, `analog_output` |
| source | TEXT | NOT NULL, DEFAULT 'gpio' | `gpio`, `mcp23017`, `pixtend`, `modbus` |
| address | INTEGER | NOT NULL | Physical GPIO number or MCP23017 pin or Modbus register |
| current_value | REAL | NOT NULL, DEFAULT 0 | Current I/O value (0/1 for digital, raw for analog) |
| safe_value | REAL | NOT NULL, DEFAULT 0 | Watchdog fail-safe value |
| is_forced | INTEGER | DEFAULT 0 | 1 if value is manually forced/overridden |
| last_change_at | TEXT | | ISO-8601 timestamp of last value change |
| updated_at | TEXT | NOT NULL | ISO-8601 last update timestamp |

### Table: `data_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique log entry ID |
| pin_name | TEXT | NOT NULL, INDEX | I/O pin name reference |
| value | REAL | NOT NULL | Logged value at sample time |
| timestamp | TEXT | NOT NULL, INDEX | ISO-8601 sample timestamp |

### Table: `programs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique program ID |
| name | TEXT | NOT NULL, UNIQUE | Program display name |
| filename | TEXT | NOT NULL, UNIQUE | File path relative to `programs/` directory |
| language | TEXT | NOT NULL | `ST` (Structured Text), `LD` (Ladder), `FBD` (Function Block) |
| description | TEXT | | Program description |
| is_active | INTEGER | DEFAULT 0 | 1 if currently loaded in OpenPLC Runtime |
| is_library | INTEGER | DEFAULT 0 | 1 if part of pre-built program library |
| uploaded_at | TEXT | NOT NULL | ISO-8601 upload timestamp |
| activated_at | TEXT | | ISO-8601 last activation timestamp |

### Table: `alarms`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique alarm ID |
| pin_name | TEXT | NOT NULL, INDEX | I/O pin that triggered the alarm |
| alarm_type | TEXT | NOT NULL | `high_threshold`, `low_threshold`, `state_change`, `watchdog`, `comm_loss` |
| severity | TEXT | NOT NULL, DEFAULT 'warning' | `info`, `warning`, `critical` |
| message | TEXT | NOT NULL | Human-readable alarm description |
| value_at_trigger | REAL | | I/O value when alarm triggered |
| threshold | REAL | | Configured threshold value (for threshold alarms) |
| is_active | INTEGER | DEFAULT 1 | 1 if alarm is currently active |
| acknowledged | INTEGER | DEFAULT 0 | 1 if operator acknowledged |
| acknowledged_by | TEXT | | Username who acknowledged |
| triggered_at | TEXT | NOT NULL | ISO-8601 alarm trigger timestamp |
| cleared_at | TEXT | | ISO-8601 alarm clear timestamp |
| acknowledged_at | TEXT | | ISO-8601 acknowledgement timestamp |

### Table: `settings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | TEXT | PK | Setting name |
| value | TEXT | | Setting value (JSON-encoded) |
| updated_at | TEXT | NOT NULL | ISO-8601 last update time |

---

## 4. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                Raspberry Pi 4/5 — OpenPLC Controller                     │
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  OpenPLC Runtime  │    │  PLC Programs     │    │  Modbus Handler  │   │
│  │  IEC 61131-3      │<──>│  LD / ST / FBD    │    │  TCP + RTU       │   │
│  │  Scan Cycle Engine│    │  Program Library   │    │  Master + Slave  │   │
│  └────────┬──────────┘    └──────────────────┘    └────────┬─────────┘   │
│           │                                                │             │
│  ┌────────▼──────────────────────────────────────────────────────────┐   │
│  │                     GPIO / I/O Layer                               │   │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ Pi GPIO │  │ MCP23017 │  │ Relay Module │  │ Opto Inputs  │  │   │
│  │  └─────────┘  └──────────┘  └──────────────┘  └──────────────┘  │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ OPC-UA Server│ │ Data Logger  │ │ Watchdog Mgr │ │ Alarm Engine │   │
│  │ python-opcua │ │ SQLite 5s    │ │ Fail-safe    │ │ Threshold +  │   │
│  │              │ │ interval     │ │ output off   │ │ State-change │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │              SQLite Database (WAL mode)                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐│   │
│  │  │io_states │ │data_logs │ │programs  │ │alarms  │ │settings  ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘ └──────────┘│   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  Flask + SocketIO Dashboard (:5000)                               │   │
│  │  bcrypt auth · 10/15min rate limit · 24h session · dark theme     │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────┐                                                   │
│  │  ScadaBR (:9090)  │ ← Modbus polling → OpenPLC (:8080)              │
│  └──────────────────┘                                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Threat Model

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| Unauthorized dashboard access | Change I/O states, upload programs | Medium | bcrypt auth, rate limiting, session expiry |
| Malicious PLC program upload | Dangerous output states, equipment damage | Medium | Auth-protected upload, watchdog fail-safe |
| Modbus replay/injection on LAN | Fake sensor readings, unauthorized output changes | Medium | Network segmentation, firewall rules |
| Brute-force login | Account compromise | Low | bcrypt, 10/15min rate limit, 24h session expiry |
| SQL injection | Data corruption, information disclosure | Low | Parameterized queries throughout |
| CSRF on output force/program upload | Unauthorized state changes | Low | CSRF tokens on all forms |
| Watchdog failure | Outputs stuck in dangerous state | Low | Hardware + software watchdog layers |
| I2C bus interference (MCP23017) | I/O expansion data corruption | Low | Bus pull-ups, error detection, retry logic |
| OPC-UA unauthorized write | Remote setpoint manipulation | Medium | OPC-UA authentication, read-only mode default |
| Physical tampering with relay wiring | Bypassed safety interlocks | Medium | Physical enclosure, tamper-evident seals, DIN rail case |

---

## 6. Tech Stack

| Layer | Technology | Version / Notes |
|-------|-----------|-----------------|
| Language | Python 3.11+ | Type hints throughout |
| PLC Runtime | OpenPLC Runtime | Latest, compiled on Pi |
| PLC Editor | OpenPLC Editor | Desktop app (not on Pi) |
| SCADA | ScadaBR | Java-based, Modbus polling |
| Web framework | Flask | 3.x with app factory pattern |
| Real-time | Flask-SocketIO | eventlet async mode |
| Modbus | pymodbus | TCP + RTU master/slave |
| OPC-UA | python-opcua | Server mode |
| I2C | smbus2 | MCP23017 I/O expansion |
| GPIO | RPi.GPIO | Direct pin access, watchdog |
| Auth | bcrypt | Password hashing |
| Config | python-dotenv | `.env` loader |
| Database | SQLite3 | WAL mode, stdlib `sqlite3` |
| CSS | Custom dark theme | No framework |
| Deployment | rsync + systemd | SSH alias `rasp-pi` |
| Testing | pytest + pytest-cov | Mocking with unittest.mock |

---

## 7. Development Phases

### Phase 1 — Project Foundation & OpenPLC Setup

**Goal:** Scaffold the project, configure environment loading, set up the database, install OpenPLC Runtime, and map Pi GPIOs.

| # | Task | Deliverable |
|---|------|-------------|
| 1.1 | Initialize project structure (dirs, `pyproject.toml`, `requirements.txt`) | Repo skeleton |
| 1.2 | Implement `.env` config loader with dataclass validation | `src/config.py` |
| 1.3 | Implement SQLite database module with schema creation (WAL mode) | `src/database.py` |
| 1.4 | Create OpenPLC Runtime install script | `scripts/install_openplc.sh` |
| 1.5 | Implement PLC runtime bridge (GPIO pin mapping, scan cycle status) | `src/plc_runtime.py` |
| 1.6 | Implement mock mode (simulated I/O for dev/testing) | Mock paths |
| 1.7 | Write unit tests for config, database, runtime bridge | `tests/` |

### Phase 2 — I/O Layer & Watchdog

**Goal:** Build the I/O abstraction layer, MCP23017 expansion driver, and fail-safe watchdog system.

| # | Task | Deliverable |
|---|------|-------------|
| 2.1 | Implement digital output control (relay modules via GPIO) | `src/plc_runtime.py` |
| 2.2 | Implement digital input reading (optocoupled modules) | `src/plc_runtime.py` |
| 2.3 | Implement MCP23017 I2C expansion driver | `src/io_expansion.py` |
| 2.4 | Implement watchdog timer manager (software + hardware) | `src/watchdog.py` |
| 2.5 | Implement safe-state output logic on watchdog trip | `src/watchdog.py` |
| 2.6 | Write I/O and watchdog tests | `tests/` |

### Phase 3 — Modbus Communication

**Goal:** Implement full Modbus TCP/RTU master and slave communication.

| # | Task | Deliverable |
|---|------|-------------|
| 3.1 | Implement Modbus TCP slave (expose I/O as registers) | `src/modbus_handler.py` |
| 3.2 | Implement Modbus TCP master (poll remote devices) | `src/modbus_handler.py` |
| 3.3 | Implement Modbus RTU slave (serial communication) | `src/modbus_handler.py` |
| 3.4 | Implement Modbus RTU master (serial polling) | `src/modbus_handler.py` |
| 3.5 | Implement Modbus register mapping to I/O states | `src/modbus_handler.py` |
| 3.6 | Write Modbus communication tests | `tests/` |

### Phase 4 — Web Dashboard & Authentication

**Goal:** Build the authenticated dark-themed dashboard with real-time I/O monitoring.

| # | Task | Deliverable |
|---|------|-------------|
| 4.1 | Implement Flask app factory with SocketIO | `src/app.py` |
| 4.2 | Implement bcrypt auth with rate limiting (10/15min) and session (24h) | `src/auth.py` |
| 4.3 | Create dark-theme base template and CSS | `templates/`, `static/` |
| 4.4 | Build login page | `templates/login.html` |
| 4.5 | Build I/O monitoring dashboard | `templates/dashboard.html`, `templates/io_monitor.html` |
| 4.6 | Build program management page | `templates/programs.html` |
| 4.7 | Build Modbus configuration page | `templates/modbus.html` |
| 4.8 | Build alarm viewer page | `templates/alarms.html` |
| 4.9 | Build settings panel | `templates/settings.html` |
| 4.10 | Implement SocketIO real-time I/O updates | `src/app.py`, `static/js/` |
| 4.11 | Write API endpoint and auth tests | `tests/` |

### Phase 5 — Data Logging, Alarms & OPC-UA

**Goal:** Add data logging, alarm engine, OPC-UA server, and program library.

| # | Task | Deliverable |
|---|------|-------------|
| 5.1 | Implement data logger (SQLite at configurable interval) | `src/data_logger.py` |
| 5.2 | Implement alarm engine (threshold, state-change, watchdog) | `src/data_logger.py` |
| 5.3 | Build data log viewer with charts | `templates/data_logs.html`, `static/js/charts.js` |
| 5.4 | Implement OPC-UA server with I/O tag browsing | `src/opcua_server.py` |
| 5.5 | Create pre-built program library (4 programs) | `programs/*.st` |
| 5.6 | Implement program library manager | `src/program_library.py` |
| 5.7 | Write data logging, alarm, and OPC-UA tests | `tests/` |

### Phase 6 — ScadaBR, Deployment & Documentation

**Goal:** Integrate ScadaBR, finalize deployment, and complete documentation.

| # | Task | Deliverable |
|---|------|-------------|
| 6.1 | Create ScadaBR install script | `scripts/install_scadabr.sh` |
| 6.2 | Implement ScadaBR bridge (Modbus data exchange config) | `src/scada_bridge.py` |
| 6.3 | Create deploy script (rsync to rasp-pi) | `deploy/deploy_to_pi.sh` |
| 6.4 | Create OS dependency installer script | `scripts/install_deps.sh` |
| 6.5 | Write systemd service unit file | docs / README |
| 6.6 | Write wiring guide | `docs/wiring_guide.md` |
| 6.7 | Write Modbus register reference | `docs/modbus_reference.md` |
| 6.8 | Write PLC programming guide | `docs/program_guide.md` |
| 6.9 | Final integration testing on Raspberry Pi hardware | Test report |
| 6.10 | Update README with final instructions | `README.md` |

---

## 8. `.env.default` Reference

```ini
# ─── Flask & Security ──────────────────────────────────────
SECRET_KEY=change-me-to-a-random-string
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...  # bcrypt hash of your password

# ─── Database ──────────────────────────────────────────────
DB_PATH=data/openplc_controller.db

# ─── OpenPLC Runtime ──────────────────────────────────────
ENABLE_OPENPLC_RUNTIME=true
OPENPLC_HOST=127.0.0.1
OPENPLC_PORT=8080
OPENPLC_PROGRAMS_DIR=programs/
SCAN_CYCLE_MS=50

# ─── ScadaBR / SCADA ─────────────────────────────────────
ENABLE_SCADABR=true
SCADABR_HOST=127.0.0.1
SCADABR_PORT=9090

# ─── Modbus TCP ──────────────────────────────────────────
ENABLE_MODBUS_TCP=true
MODBUS_TCP_HOST=0.0.0.0
MODBUS_TCP_PORT=502
MODBUS_TCP_SLAVE_ID=1

# ─── Modbus RTU ──────────────────────────────────────────
ENABLE_MODBUS_RTU=false
MODBUS_RTU_PORT=/dev/ttyUSB0
MODBUS_RTU_BAUDRATE=9600
MODBUS_RTU_PARITY=N
MODBUS_RTU_STOPBITS=1

# ─── I/O Expansion (MCP23017) ────────────────────────────
ENABLE_IO_EXPANSION=false
MCP23017_ADDRESSES=0x20
# Comma-separated hex addresses: 0x20,0x21,0x22 (up to 8 chips)
I2C_BUS=1

# ─── Watchdog / Fail-Safe ────────────────────────────────
ENABLE_WATCHDOG=true
WATCHDOG_TIMEOUT_SEC=5
SAFE_STATE_DEFAULT=0
# 0 = outputs OFF on watchdog trip, 1 = outputs ON

# ─── Program Library ─────────────────────────────────────
ENABLE_PROGRAM_LIBRARY=true

# ─── OPC-UA Server ───────────────────────────────────────
ENABLE_OPCUA=false
OPCUA_HOST=0.0.0.0
OPCUA_PORT=4840
OPCUA_ENDPOINT=opc.tcp://0.0.0.0:4840/openplc/
OPCUA_READ_ONLY=true

# ─── Data Logging ────────────────────────────────────────
ENABLE_DATA_LOGGING=true
LOG_INTERVAL_SEC=5
LOG_RETENTION_DAYS=30

# ─── Alarm Engine ────────────────────────────────────────
ENABLE_ALARMS=true

# ─── Web Dashboard ───────────────────────────────────────
ENABLE_WEB_DASHBOARD=true
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
SESSION_EXPIRY_HOURS=24
RATE_LIMIT=10/15min

# ─── Development ─────────────────────────────────────────
MOCK_MODE=false
LOG_LEVEL=INFO
```

---

## 9. Deliverables

| # | Deliverable | Format | Notes |
|---|-------------|--------|-------|
| 1 | OpenPLC Runtime bridge (GPIO mapping, status) | Python module | `src/plc_runtime.py` |
| 2 | Modbus TCP/RTU handler (master + slave) | Python module | `src/modbus_handler.py` |
| 3 | MCP23017 I/O expansion driver | Python module | `src/io_expansion.py` |
| 4 | Watchdog timer manager (fail-safe) | Python module | `src/watchdog.py` |
| 5 | OPC-UA server | Python module | `src/opcua_server.py` |
| 6 | Data logger (SQLite, interval-based) | Python module | `src/data_logger.py` |
| 7 | ScadaBR integration bridge | Python module | `src/scada_bridge.py` |
| 8 | PLC program library manager | Python module | `src/program_library.py` |
| 9 | SQLite database layer | Python module | `src/database.py` |
| 10 | Flask + SocketIO dashboard | Python + HTML/JS/CSS | `src/app.py`, `templates/`, `static/` |
| 11 | bcrypt auth with rate limiting | Python module | `src/auth.py` |
| 12 | Configuration loader | Python module | `src/config.py` |
| 13 | Pre-built PLC programs (4) | Structured Text | `programs/*.st` |
| 14 | OpenPLC Runtime install script | Bash | `scripts/install_openplc.sh` |
| 15 | ScadaBR install script | Bash | `scripts/install_scadabr.sh` |
| 16 | OS dependency installer | Bash | `scripts/install_deps.sh` |
| 17 | Deploy script | Bash | `deploy/deploy_to_pi.sh` |
| 18 | systemd service unit | INI | Documented in README |
| 19 | Test suite (≥80% coverage) | pytest | `tests/` |
| 20 | Wiring guide | Markdown | `docs/wiring_guide.md` |
| 21 | Modbus register reference | Markdown | `docs/modbus_reference.md` |
| 22 | PLC programming guide | Markdown | `docs/program_guide.md` |
| 23 | README & TSD | Markdown | Root-level docs |
