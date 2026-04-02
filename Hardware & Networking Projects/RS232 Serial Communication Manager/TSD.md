# 📐 Technical Specification Document — RS232 Serial Communication Manager

---

## 1. Database Schema (SQLite)

### Table: `users`
```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    UNIQUE NOT NULL,
    password_hash   TEXT    NOT NULL,
    role            TEXT    DEFAULT 'admin',
    created_at      TEXT    DEFAULT (datetime('now')),
    last_login      TEXT
);
```

### Table: `port_configs`
```sql
CREATE TABLE port_configs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    device_path     TEXT    NOT NULL,
    display_name    TEXT,
    baud_rate       INTEGER DEFAULT 9600,
    data_bits       INTEGER DEFAULT 8,
    parity          TEXT    DEFAULT 'N',
    stop_bits       REAL    DEFAULT 1.0,
    flow_control    TEXT    DEFAULT 'none',
    timeout_sec     REAL    DEFAULT 1.0,
    auto_open       INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now'))
);
```

### Table: `port_profiles`
```sql
CREATE TABLE port_profiles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    UNIQUE NOT NULL,
    description     TEXT,
    baud_rate       INTEGER NOT NULL,
    data_bits       INTEGER NOT NULL,
    parity          TEXT    NOT NULL,
    stop_bits       REAL    NOT NULL,
    flow_control    TEXT    NOT NULL,
    timeout_sec     REAL    NOT NULL,
    created_at      TEXT    DEFAULT (datetime('now'))
);
```

### Table: `macros`
```sql
CREATE TABLE macros (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    description     TEXT,
    data_hex        TEXT    NOT NULL,
    encoding        TEXT    DEFAULT 'hex',
    delay_ms        INTEGER DEFAULT 0,
    repeat_count    INTEGER DEFAULT 1,
    category        TEXT    DEFAULT 'general',
    hotkey          TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);
```

### Table: `auto_response_rules`
```sql
CREATE TABLE auto_response_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    port_filter     TEXT,
    match_type      TEXT    DEFAULT 'contains',
    match_pattern   TEXT    NOT NULL,
    match_encoding  TEXT    DEFAULT 'hex',
    response_data   TEXT    NOT NULL,
    response_encoding TEXT  DEFAULT 'hex',
    delay_ms        INTEGER DEFAULT 0,
    enabled         INTEGER DEFAULT 1,
    priority        INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now'))
);
```

### Table: `tcp_bridges`
```sql
CREATE TABLE tcp_bridges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_port     TEXT    NOT NULL,
    tcp_port        INTEGER NOT NULL,
    protocol        TEXT    DEFAULT 'raw',
    max_clients     INTEGER DEFAULT 10,
    ip_whitelist    TEXT,
    auto_start      INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now'))
);
```

### Table: `recordings`
```sql
CREATE TABLE recordings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    port            TEXT    NOT NULL,
    filename        TEXT    NOT NULL,
    format          TEXT    DEFAULT 'both',
    start_time      TEXT    NOT NULL,
    end_time        TEXT,
    bytes_captured  INTEGER DEFAULT 0,
    status          TEXT    DEFAULT 'recording',
    created_at      TEXT    DEFAULT (datetime('now'))
);
```

### Table: `scripts`
```sql
CREATE TABLE scripts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    description     TEXT,
    code            TEXT    NOT NULL,
    language        TEXT    DEFAULT 'python',
    last_run        TEXT,
    last_result     TEXT,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now'))
);
```

### Table: `connection_stats`
```sql
CREATE TABLE connection_stats (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    port            TEXT    NOT NULL,
    timestamp       TEXT    DEFAULT (datetime('now')),
    bytes_tx        INTEGER DEFAULT 0,
    bytes_rx        INTEGER DEFAULT 0,
    errors          INTEGER DEFAULT 0,
    throughput_tx   REAL    DEFAULT 0.0,
    throughput_rx   REAL    DEFAULT 0.0,
    uptime_sec      INTEGER DEFAULT 0
);
```

### Table: `feature_toggles`
```sql
CREATE TABLE feature_toggles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_key     TEXT    UNIQUE NOT NULL,
    enabled         INTEGER DEFAULT 1,
    updated_at      TEXT    DEFAULT (datetime('now'))
);

-- Default feature toggles
INSERT INTO feature_toggles (feature_key, enabled) VALUES
    ('auto_detect', 1), ('multi_port', 1), ('hex_view', 1),
    ('msg_builder', 1), ('modbus_rtu', 1), ('auto_response', 1),
    ('tcp_bridge', 1), ('data_plotting', 1), ('macros', 1),
    ('rest_api', 1), ('protocol_analyzer', 1), ('session_recording', 1),
    ('port_profiles', 1), ('notifications', 1), ('conn_stats', 1),
    ('scripting', 0);
```

---

## 2. API Route Specifications

### `POST /api/auth/login`
- **Body**: `{ "username": "admin", "password": "..." }`
- **Response**: `{ "token": "jwt...", "expires_in": 86400 }`
- **Rate limit**: 10 requests per 15 minutes

### `GET /api/ports`
- **Auth**: JWT required
- **Response**: 
```json
{
  "ports": [
    {
      "device": "/dev/ttyUSB0",
      "description": "FTDI USB-to-Serial",
      "hwid": "USB VID:PID=0403:6001",
      "is_open": true,
      "config": {
        "baud_rate": 9600,
        "data_bits": 8,
        "parity": "N",
        "stop_bits": 1.0,
        "flow_control": "none"
      }
    }
  ]
}
```

### `POST /api/ports/:id/open`
- **Body**: `{ "baud_rate": 115200, "data_bits": 8, "parity": "N", "stop_bits": 1, "flow_control": "none" }`
- **Response**: `{ "status": "opened", "device": "/dev/ttyUSB0" }`
- **WebSocket**: Emits `port_opened` to all clients

### `POST /api/ports/:id/send`
- **Body**: `{ "data": "48656C6C6F", "encoding": "hex" }` or `{ "data": "Hello", "encoding": "ascii" }`
- **Response**: `{ "bytes_sent": 5 }`
- **Validation**: Max payload 64KB, encoding must be `hex` or `ascii`

### `POST /api/modbus/read-holding`
- **Body**: `{ "port": "/dev/ttyUSB0", "slave_id": 1, "start_address": 0, "count": 10 }`
- **Response**: `{ "registers": [0, 100, 255, ...], "raw_hex": "010300140..." }`

### `POST /api/bridge`
- **Body**: `{ "serial_port": "/dev/ttyUSB0", "tcp_port": 9000, "max_clients": 5 }`
- **Response**: `{ "bridge_id": 1, "status": "active", "tcp_endpoint": "0.0.0.0:9000" }`
- **Validation**: TCP port 1024–65535, serial port must be open

### `POST /api/protocol/decode`
- **Body**: `{ "data": "010300020064...", "protocol": "modbus_rtu" }`
- **Response**: `{ "decoded": { "slave_id": 1, "function": "Read Holding Registers", "address": 2, "count": 100 } }`

### `PUT /api/settings/features`
- **Body**: `{ "auto_detect": true, "scripting": false, ... }`
- **Response**: `{ "updated": ["auto_detect", "scripting"], "synced_env": true }`
- **Side effects**: Updates `.env` file, broadcasts `feature_toggled` via WebSocket

---

## 3. WebSocket Architecture

```
Client (browser)
    ↕ Socket.IO namespace: /serial
    
Events flow:
1. Client opens port → open_port → server starts read thread
2. Serial data arrives → pyserial read → server emits serial_data
3. Client sends data → send_data → server writes to port
4. Stats collected → periodic timer → stats_update emitted
5. Protocol frame decoded → protocol_decoded emitted
6. Auto-response triggered → auto_response_fired emitted
```

### Data Format for `serial_data` Event
```json
{
  "port": "/dev/ttyUSB0",
  "direction": "rx",
  "hex": "48 65 6C 6C 6F 0D 0A",
  "ascii": "Hello\\r\\n",
  "timestamp": "2025-01-15T10:30:45.123Z",
  "length": 7
}
```

---

## 4. Port Manager Architecture

```python
# Threaded architecture per port
PortManager
├── _scan_thread (auto-detection loop)
├── ports: Dict[str, PortHandler]
│   ├── PortHandler("/dev/ttyUSB0")
│   │   ├── serial.Serial instance
│   │   ├── _read_thread (blocking read loop)
│   │   ├── _write_queue (thread-safe queue)
│   │   ├── stats: ConnectionStats
│   │   └── recording: SessionRecorder (optional)
│   └── PortHandler("/dev/ttyUSB1")
│       └── ...
└── auto_response_engine (pattern matching)
```

---

## 5. CRC Calculator Specifications

| Algorithm | Polynomial | Init | Reflect | XOR Out | Use Case |
|-----------|-----------|------|---------|---------|----------|
| CRC-8 | 0x07 | 0x00 | No | 0x00 | Simple protocols |
| CRC-16/Modbus | 0x8005 | 0xFFFF | Yes | 0x0000 | Modbus RTU |
| CRC-16/CCITT | 0x1021 | 0xFFFF | No | 0x0000 | XMODEM, PPP |
| CRC-32 | 0x04C11DB7 | 0xFFFFFFFF | Yes | 0xFFFFFFFF | General |

---

## 6. Modbus RTU Frame Format

```
┌──────────┬──────────────┬──────────────────┬───────────┐
│ Slave ID │ Function Code│ Data             │ CRC-16    │
│ 1 byte   │ 1 byte       │ N bytes          │ 2 bytes   │
└──────────┴──────────────┴──────────────────┴───────────┘
```

### Supported Function Codes
| FC | Name | Request | Response |
|----|------|---------|----------|
| 01 | Read Coils | addr(2) + qty(2) | count(1) + data(N) |
| 02 | Read Discrete Inputs | addr(2) + qty(2) | count(1) + data(N) |
| 03 | Read Holding Registers | addr(2) + qty(2) | count(1) + data(N×2) |
| 04 | Read Input Registers | addr(2) + qty(2) | count(1) + data(N×2) |
| 05 | Write Single Coil | addr(2) + value(2) | echo |
| 06 | Write Single Register | addr(2) + value(2) | echo |
| 15 | Write Multiple Coils | addr(2) + qty(2) + count(1) + data(N) | addr(2) + qty(2) |
| 16 | Write Multiple Registers | addr(2) + qty(2) + count(1) + data(N×2) | addr(2) + qty(2) |

---

## 7. TCP Bridge Protocol

### Raw Mode
Direct byte-for-byte forwarding between TCP socket and serial port. No framing.

### RFC 2217 Compatibility
```
IAC (0xFF) + SB (0xFA) + COM_PORT_OPTION (0x2C) + subcommand + IAC (0xFF) + SE (0xF0)
```
Supported subcommands: SET-BAUDRATE, SET-DATASIZE, SET-PARITY, SET-STOPSIZE, SET-CONTROL.

---

## 8. Threat Model Summary

| Threat | Vector | Mitigation |
|--------|--------|------------|
| Unauthorized port access | Network access to API | JWT auth + rate limiting |
| Malicious serial injection | Crafted messages via API | Input validation + encoding check |
| TCP bridge abuse | Open TCP ports | IP whitelist + max clients + timeout |
| Script injection | Scripting engine | Sandboxed exec + restricted imports + timeout |
| Data exfiltration | Recording files | Auth required for download + retention policy |
| DoS via port flooding | Rapid send requests | Write queue with rate limit + buffer size cap |
| Credential brute force | Login endpoint | 10 attempts/15min + bcrypt |

---

## 9. File Structure

```
RS232 Serial Communication Manager/
├── README.md
├── TSD.md
├── task.md
├── implementation_plan.md
├── requirements.txt
├── .env.example
├── deploy/
│   └── deploy_to_pi.sh
├── docs/
│   └── threat_model.md
├── config/
│   ├── port_profiles.json
│   └── parsers/
│       ├── modbus_rtu.json
│       └── nmea_0183.json
├── src/
│   ├── app.py
│   ├── init_db.py
│   ├── database.py
│   ├── auth.py
│   ├── port_manager.py
│   ├── port_handler.py
│   ├── crc_calculator.py
│   ├── modbus_rtu.py
│   ├── tcp_bridge.py
│   ├── auto_response.py
│   ├── protocol_analyzer.py
│   ├── session_recorder.py
│   ├── scripting_engine.py
│   ├── notification_service.py
│   ├── feature_toggles.py
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── port_routes.py
│   │   ├── modbus_routes.py
│   │   ├── bridge_routes.py
│   │   ├── macro_routes.py
│   │   ├── response_routes.py
│   │   ├── profile_routes.py
│   │   ├── recording_routes.py
│   │   ├── protocol_routes.py
│   │   ├── script_routes.py
│   │   ├── analytics_routes.py
│   │   └── settings_routes.py
│   └── templates/
│       ├── layout.html
│       ├── login.html
│       ├── dashboard.html
│       ├── terminal.html
│       ├── modbus.html
│       ├── macros.html
│       ├── plotting.html
│       ├── bridge.html
│       ├── recordings.html
│       ├── protocol.html
│       ├── scripts.html
│       └── settings.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── terminal.js
│       ├── hex_view.js
│       ├── modbus.js
│       ├── macros.js
│       ├── plotting.js
│       ├── bridge.js
│       └── settings.js
├── data/
│   ├── serial_manager.db
│   ├── recordings/
│   └── scripts/
└── tests/
    ├── test_port_manager.py
    ├── test_crc.py
    ├── test_modbus.py
    ├── test_tcp_bridge.py
    ├── test_auto_response.py
    ├── test_protocol.py
    └── test_api.py
```

---

## 10. Development Phases

| Phase | Scope | Duration |
|-------|-------|----------|
| 1 | Project setup, auth, database | Day 1 |
| 2 | Port manager, auto-detect | Day 1–2 |
| 3 | Hex/ASCII terminal view | Day 2–3 |
| 4 | CRC calculator, message builder | Day 3 |
| 5 | Modbus RTU engine | Day 3–4 |
| 6 | Session recording | Day 4–5 |
| 7 | Auto-response rules | Day 5 |
| 8 | TCP bridge (raw + RFC 2217) | Day 5–6 |
| 9 | Data plotting | Day 7 |
| 10 | Message macros | Day 7–8 |
| 11 | Port profiles | Day 8 |
| 12 | Protocol analyzer | Day 8–9 |
| 13 | Scripting engine | Day 9–10 |
| 14 | Connection statistics | Day 10 |
| 15 | Notifications | Day 10–11 |
| 16 | Feature toggles + settings | Day 11 |
| 17 | Dashboard polish, dark theme | Day 11–12 |
| 18 | Deploy script, systemd | Day 12 |
| 19 | Testing + documentation | Day 13–14 |
