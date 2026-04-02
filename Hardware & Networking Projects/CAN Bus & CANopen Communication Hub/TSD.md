# 📐 Technical Specification Document — CAN Bus & CANopen Communication Hub

---

## 1. Database Schema (SQLite)

### Table: `users`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | NOT NULL UNIQUE |
| password_hash | TEXT | NOT NULL |
| role | TEXT | DEFAULT 'user' |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| last_login | DATETIME | |

### Table: `can_messages`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| arb_id | INTEGER | NOT NULL |
| is_extended | BOOLEAN | DEFAULT 0 |
| is_remote | BOOLEAN | DEFAULT 0 |
| is_error | BOOLEAN | DEFAULT 0 |
| dlc | INTEGER | NOT NULL |
| data_hex | TEXT | NOT NULL |
| direction | TEXT | NOT NULL (rx/tx) |
| channel | TEXT | DEFAULT 'can0' |
| timestamp | REAL | NOT NULL (epoch with microseconds) |
| decoded_signals | TEXT | (JSON if DBC loaded) |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `dbc_files`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| filename | TEXT | NOT NULL |
| file_path | TEXT | NOT NULL |
| description | TEXT | |
| message_count | INTEGER | |
| signal_count | INTEGER | |
| uploaded_by | INTEGER | FK → users.id |
| uploaded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `recordings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| filename | TEXT | NOT NULL |
| file_path | TEXT | NOT NULL |
| format | TEXT | DEFAULT 'asc' (asc/blf/csv) |
| size_bytes | INTEGER | |
| message_count | INTEGER | |
| duration_sec | REAL | |
| started_at | DATETIME | |
| stopped_at | DATETIME | |
| created_by | INTEGER | FK → users.id |

### Table: `canopen_nodes`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| node_id | INTEGER | NOT NULL UNIQUE (1-127) |
| name | TEXT | |
| vendor_id | INTEGER | |
| product_code | INTEGER | |
| nmt_state | TEXT | DEFAULT 'unknown' (init/pre-op/op/stopped) |
| heartbeat_ms | INTEGER | |
| eds_file_id | INTEGER | FK → eds_files.id |
| last_heartbeat | DATETIME | |
| discovered_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `eds_files`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| filename | TEXT | NOT NULL |
| file_path | TEXT | NOT NULL |
| node_id | INTEGER | |
| object_count | INTEGER | |
| uploaded_by | INTEGER | FK → users.id |
| uploaded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `bus_diagnostics`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| channel | TEXT | DEFAULT 'can0' |
| bus_load_pct | REAL | |
| tx_error_count | INTEGER | |
| rx_error_count | INTEGER | |
| error_frames | INTEGER | |
| bus_state | TEXT | (active/warning/passive/bus-off) |
| msg_per_sec | REAL | |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `message_filters`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL |
| filter_type | TEXT | NOT NULL (accept/reject) |
| id_start | INTEGER | NOT NULL |
| id_end | INTEGER | NOT NULL |
| mask | INTEGER | DEFAULT 0x7FF |
| enabled | BOOLEAN | DEFAULT 1 |
| created_by | INTEGER | FK → users.id |

### Table: `feature_toggles`
| Column | Type | Constraints |
|--------|------|------------|
| feature_key | TEXT | PRIMARY KEY |
| enabled | BOOLEAN | NOT NULL DEFAULT 0 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_by | INTEGER | FK → users.id |

---

## 2. `.env.default` Template

> See full template in [README.md → Environment Variables](README.md#-environment-variables)

Total environment variables: **~50**

---

## 3. API Route Specifications

### Authentication
```
POST /api/auth/login
  Body: { "username": "...", "password": "..." }
  Response: { "token": "jwt...", "expires_in": 86400 }
  Rate Limit: 10 attempts / 15 min per IP
```

### CAN Interface
```
GET /api/can/status
  Response: { "interface": "can0", "state": "up", "bitrate": 500000,
              "bus_load_pct": 23.4, "msg_per_sec": 450, "error_frames": 0 }

POST /api/can/setup
  Body: { "bitrate": 500000, "fd": false }
  Response: { "interface": "can0", "state": "up", "bitrate": 500000 }

POST /api/can/send
  Body: { "arb_id": "0x123", "data": "DEADBEEF01020304", "extended": false, "repeat": 0 }
  Response: { "sent": true, "arb_id": "0x123" }

GET /api/can/messages?limit=100&id_filter=0x100-0x1FF
  Response: [{ "arb_id": "0x123", "dlc": 8, "data": "DE AD BE EF 01 02 03 04",
               "direction": "rx", "timestamp": 1712044800.123456 }]

POST /api/can/filter
  Body: { "name": "Motor Messages", "type": "accept", "id_start": 256, "id_end": 511 }
  Response: { "id": 1, "created": true }
```

### DBC Decoder
```
GET /api/dbc
  Response: [{ "id": 1, "filename": "car.dbc", "message_count": 42, "signal_count": 180 }]

POST /api/dbc/upload
  Body: multipart/form-data (DBC file)
  Response: { "id": 1, "messages_parsed": 42, "signals_parsed": 180 }

GET /api/dbc/decode/0x123
  Response: { "message_name": "EngineStatus", "signals": [
    { "name": "RPM", "value": 3500, "unit": "rpm", "min": 0, "max": 8000 },
    { "name": "Temperature", "value": 85, "unit": "°C" }] }
```

### Recorder & Replay
```
POST /api/recorder/start
  Body: { "format": "asc", "filter": null }
  Response: { "recording": true, "filename": "can_2026-04-02_10-30-00.asc" }

POST /api/recorder/stop
  Response: { "recording": false, "filename": "...", "messages": 45000, "duration_sec": 120 }

GET /api/recorder/files
  Response: [{ "filename": "...", "format": "asc", "size_mb": 12.3, "messages": 45000 }]

POST /api/replay/start
  Body: { "filename": "...", "speed_factor": 1.0 }
  Response: { "replaying": true, "estimated_duration_sec": 120 }
```

### CANopen
```
GET /api/canopen/nodes
  Response: [{ "node_id": 1, "name": "Motor Controller", "nmt_state": "operational",
               "last_heartbeat": "2026-04-02T10:30:00Z" }]

POST /api/canopen/nmt
  Body: { "node_id": 1, "command": "start" }
  Response: { "sent": true, "command": "start_remote_node", "cob_id": "0x000" }

POST /api/canopen/sdo/read
  Body: { "node_id": 1, "index": "0x6040", "subindex": 0 }
  Response: { "value": 6, "data_hex": "0006", "data_type": "UNSIGNED16" }

POST /api/canopen/sdo/write
  Body: { "node_id": 1, "index": "0x6040", "subindex": 0, "value": 15, "data_type": "UNSIGNED16" }
  Response: { "written": true }
```

### Feature Toggles
```
GET /api/settings/features
  Response: { "ENABLE_SOCKETCAN_SETUP": true, "ENABLE_LIVE_VIEWER": true, ... }

PUT /api/settings/features
  Body: { "ENABLE_CANOPEN_NMT": true, "ENABLE_DBC_DECODER": true }
  Response: { "updated": ["ENABLE_CANOPEN_NMT", "ENABLE_DBC_DECODER"] }
```

---

## 4. WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `can_message` | Server → Client | `{ "arb_id": "0x123", "dlc": 8, "data": "DEADBEEF", "dir": "rx" }` |
| `can_decoded` | Server → Client | `{ "arb_id": "0x123", "signals": [{ "name": "RPM", "value": 3500 }] }` |
| `bus_diag` | Server → Client | `{ "bus_load_pct": 23.4, "msg_per_sec": 450, "errors": 0 }` |
| `node_state` | Server → Client | `{ "node_id": 1, "nmt_state": "operational" }` |
| `heartbeat_timeout` | Server → Client | `{ "node_id": 3, "last_seen": "...", "timeout_ms": 2000 }` |
| `recording_status` | Server → Client | `{ "recording": true, "messages": 12000, "duration_sec": 30 }` |
| `replay_progress` | Server → Client | `{ "progress_pct": 45, "messages_sent": 20000 }` |
| `toggle_feature` | Client → Server | `{ "feature": "ENABLE_DBC_DECODER", "enabled": true }` |
| `feature_toggled` | Server → Client | `{ "feature": "ENABLE_DBC_DECODER", "enabled": true }` |

---

## 5. Threat Model

| # | Threat | Mitigation |
|---|--------|-----------|
| 1 | Brute-force login | bcrypt + 10 attempts/15min rate limit + account lockout |
| 2 | JWT token theft | 24h expiry, httpOnly secure cookies, token rotation |
| 3 | Unauthorized CAN frame injection | Auth gating on send API, audit log of all sent frames |
| 4 | CAN bus flooding via web | Rate limiting on send endpoint, max repeat count |
| 5 | Malicious DBC file upload | File type validation, size limit, sandboxed parsing |
| 6 | Replay attack on live bus | Replay requires explicit auth + confirmation dialog |
| 7 | TCP bridge abuse | Auth token required for TCP bridge, max client limit |
| 8 | SDO write to critical OD entries | Write confirmation for safety-critical indices |
| 9 | Man-in-the-middle | HTTPS/TLS on all endpoints, self-signed cert generation |
| 10 | .env file exposure | File permissions 600, not served by web server, gitignored |
| 11 | SQL injection | Parameterized queries exclusively |
| 12 | Bus-off denial of service | Auto bus-off recovery, alerting, diagnostic monitoring |

---

## 6. Development Phases

| Phase | Description | Days |
|-------|-------------|------|
| 1 | Project setup, Flask skeleton, auth system | Day 1 |
| 2 | SocketCAN auto-config (MCP2515 overlay, bitrate, bring-up) | Day 1–2 |
| 3 | python-can bus interface, receive loop, SQLite storage | Day 2 |
| 4 | Live message viewer (WebSocket real-time stream) | Day 2–3 |
| 5 | Web dashboard (dark theme, bus status, live viewer) | Day 3 |
| 6 | Message sender (hex builder, single/repeat send) | Day 3–4 |
| 7 | DBC file upload + cantools signal decoder | Day 4 |
| 8 | Message recorder (ASC/BLF/CSV) + replay engine | Day 4–5 |
| 9 | Message filtering (hardware mask + software filter) | Day 5 |
| 10 | Bus diagnostics (error counters, bus load, state) | Day 5–6 |
| 11 | CANopen NMT manager + node discovery | Day 6–7 |
| 12 | CANopen SDO client (read/write OD entries) | Day 7 |
| 13 | CANopen PDO mapping viewer + heartbeat monitor | Day 7–8 |
| 14 | Object Dictionary browser (EDS/DCF parser) | Day 8 |
| 15 | CAN↔TCP bridge server | Day 8–9 |
| 16 | Analytics engine (msg rate, bus load trends, per-ID stats) | Day 9 |
| 17 | Notification system (Telegram, Slack, email) | Day 9–10 |
| 18 | Feature toggle system (dashboard ↔ .env sync) | Day 10 |
| 19 | systemd service + deploy script + hardening | Day 10–11 |
| 20 | Testing, documentation, final review | Day 11–12 |

---

## 7. File Structure

```
CAN Bus & CANopen Communication Hub/
├── README.md
├── TSD.md
├── task.md
├── implementation_plan.md
├── requirements.txt
├── .env.default
├── init_db.py
├── deploy/
│   ├── deploy_to_pi.sh
│   └── can-hub.service
├── docs/
│   └── threat_model.md
├── data/
│   ├── can_hub.db
│   ├── dbc/
│   ├── eds/
│   └── recordings/
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── auth.py
│   ├── can_interface.py
│   ├── can_receiver.py
│   ├── can_sender.py
│   ├── dbc_decoder.py
│   ├── recorder.py
│   ├── replay_engine.py
│   ├── message_filter.py
│   ├── bus_diagnostics.py
│   ├── canopen_manager.py
│   ├── canopen_sdo.py
│   ├── canopen_pdo.py
│   ├── canopen_nmt.py
│   ├── od_browser.py
│   ├── heartbeat_monitor.py
│   ├── tcp_bridge.py
│   ├── analytics.py
│   ├── notification_service.py
│   ├── feature_toggles.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── can_routes.py
│   │   ├── dbc_routes.py
│   │   ├── recorder_routes.py
│   │   ├── canopen_routes.py
│   │   ├── diag_routes.py
│   │   ├── analytics_routes.py
│   │   └── settings_routes.py
│   └── templates/
│       ├── layout.html
│       ├── login.html
│       ├── dashboard.html
│       ├── live_viewer.html
│       ├── dbc_decoder.html
│       ├── msg_sender.html
│       ├── recorder.html
│       ├── replay.html
│       ├── canopen.html
│       ├── od_browser.html
│       ├── diagnostics.html
│       ├── analytics.html
│       └── settings.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── dashboard.js
│       ├── live_viewer.js
│       ├── msg_sender.js
│       ├── canopen.js
│       ├── analytics.js
│       └── settings.js
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    ├── test_can_interface.py
    ├── test_dbc_decoder.py
    ├── test_recorder.py
    ├── test_canopen.py
    ├── test_tcp_bridge.py
    └── test_toggles.py
```
