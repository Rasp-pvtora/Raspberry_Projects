# 📐 Technical Specification Document — OPC-UA Industrial Gateway

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

### Table: `opcua_nodes`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| node_id | TEXT | NOT NULL UNIQUE |
| browse_name | TEXT | NOT NULL |
| display_name | TEXT | |
| node_class | TEXT | NOT NULL (Variable/Object/Method) |
| data_type | TEXT | (Double/Int32/String/Boolean) |
| parent_node_id | TEXT | FK → opcua_nodes.node_id |
| source_plugin | TEXT | (gpio/can/serial/modbus/manual) |
| source_ref | TEXT | (plugin-specific reference) |
| writable | BOOLEAN | DEFAULT 0 |
| historizing | BOOLEAN | DEFAULT 0 |
| current_value | TEXT | |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | |

### Table: `source_mappings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| source_type | TEXT | NOT NULL (gpio/can/serial/modbus) |
| source_key | TEXT | NOT NULL (e.g., "GPIO_4", "CAN_0x123_RPM") |
| node_id | TEXT | FK → opcua_nodes.node_id |
| transform | TEXT | (optional formula) |
| poll_interval_ms | INTEGER | DEFAULT 1000 |
| enabled | BOOLEAN | DEFAULT 1 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `historical_data`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| node_id | TEXT | NOT NULL |
| value | TEXT | NOT NULL |
| quality | INTEGER | DEFAULT 0 (OPC-UA StatusCode) |
| source_timestamp | REAL | NOT NULL (epoch microseconds) |
| server_timestamp | REAL | NOT NULL |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `alarms`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| node_id | TEXT | FK → opcua_nodes.node_id |
| alarm_type | TEXT | NOT NULL (high/hihi/low/lolo/change) |
| severity | INTEGER | DEFAULT 500 (1-1000) |
| limit_value | REAL | |
| current_value | REAL | |
| active | BOOLEAN | DEFAULT 1 |
| acknowledged | BOOLEAN | DEFAULT 0 |
| ack_by | INTEGER | FK → users.id |
| triggered_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| ack_at | DATETIME | |

### Table: `alarm_configs`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| node_id | TEXT | FK → opcua_nodes.node_id |
| alarm_type | TEXT | NOT NULL |
| limit_value | REAL | NOT NULL |
| severity | INTEGER | DEFAULT 500 |
| enabled | BOOLEAN | DEFAULT 1 |
| deadband | REAL | DEFAULT 0 |

### Table: `certificates`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| thumbprint | TEXT | NOT NULL UNIQUE |
| subject | TEXT | |
| issuer | TEXT | |
| valid_from | DATETIME | |
| valid_to | DATETIME | |
| trusted | BOOLEAN | DEFAULT 0 |
| file_path | TEXT | |
| uploaded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `server_sessions`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| session_id | TEXT | NOT NULL |
| client_name | TEXT | |
| client_cert_thumbprint | TEXT | |
| security_policy | TEXT | |
| connected_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| disconnected_at | DATETIME | |
| subscriptions | INTEGER | DEFAULT 0 |

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

Total environment variables: **~60**

---

## 3. API Route Specifications

### Authentication
```
POST /api/auth/login
  Body: { "username": "...", "password": "..." }
  Response: { "token": "jwt...", "expires_in": 86400 }
  Rate Limit: 10 attempts / 15 min per IP
```

### OPC-UA Server Control
```
GET /api/opcua/status
  Response: { "running": true, "endpoint": "opc.tcp://...:4840",
              "sessions": 3, "subscriptions": 12, "uptime_sec": 86400 }

POST /api/opcua/start
  Response: { "status": "starting" }

POST /api/opcua/stop
  Response: { "status": "stopping" }
```

### Address Space / Node Management
```
GET /api/nodes?parent=ns=2;s=GPIO
  Response: [{ "node_id": "ns=2;s=GPIO.Pin4_Temp", "browse_name": "Pin4_Temp",
               "node_class": "Variable", "value": 22.5, "data_type": "Double" }]

GET /api/nodes/<node_id>
  Response: { "node_id": "...", "browse_name": "...", "data_type": "Double",
              "value": 22.5, "historizing": true, "source": "gpio:4" }

POST /api/nodes
  Body: { "browse_name": "CustomVar", "parent": "ns=2;s=Custom",
          "data_type": "Double", "writable": true }
  Response: { "node_id": "ns=2;s=Custom.CustomVar", "created": true }

PUT /api/nodes/<node_id>
  Body: { "value": 42.0 }
  Response: { "written": true }

DELETE /api/nodes/<node_id>
  Response: { "deleted": true }
```

### Data Source Mappings
```
GET /api/mappings
  Response: [{ "id": 1, "source_type": "gpio", "source_key": "GPIO_4",
               "node_id": "ns=2;s=GPIO.Pin4_Temp", "enabled": true }]

POST /api/mappings
  Body: { "source_type": "modbus", "source_key": "HR_40001",
          "node_id": "ns=2;s=Modbus.Holding40001", "poll_interval_ms": 500 }
  Response: { "id": 5, "created": true }
```

### Historical Data
```
GET /api/history/<node_id>?from=2026-03-01&to=2026-04-01&limit=1000
  Response: { "node_id": "...", "count": 1000,
              "values": [{ "value": 22.5, "timestamp": "...", "quality": 0 }] }
```

### Alarms
```
GET /api/alarms?active=true
  Response: [{ "id": 1, "node_id": "...", "type": "high", "severity": 800,
               "value": 95.2, "limit": 90.0, "acknowledged": false }]

POST /api/alarms/config
  Body: { "node_id": "...", "alarm_type": "high", "limit_value": 90.0, "severity": 800 }

PUT /api/alarms/<id>/ack
  Response: { "acknowledged": true }
```

### REST Proxy
```
GET /api/rest/GPIO/Pin4_Temp
  Response: { "value": 22.5, "data_type": "Double", "timestamp": "...", "quality": "Good" }

PUT /api/rest/GPIO/Pin4_Temp
  Body: { "value": 25.0 }
  Response: { "written": true }
```

### Feature Toggles
```
GET /api/settings/features
  Response: { "ENABLE_OPCUA_SERVER": true, "ENABLE_GPIO_SOURCE": true, ... }

PUT /api/settings/features
  Body: { "ENABLE_CAN_SOURCE": true, "ENABLE_MODBUS_SOURCE": true }
  Response: { "updated": ["ENABLE_CAN_SOURCE", "ENABLE_MODBUS_SOURCE"] }
```

---

## 4. WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `node_value_update` | Server → Client | `{ "node_id": "ns=2;s=GPIO.Pin4", "value": 22.5 }` |
| `alarm_triggered` | Server → Client | `{ "node_id": "...", "type": "high", "value": 95.2, "limit": 90.0 }` |
| `alarm_cleared` | Server → Client | `{ "node_id": "...", "type": "high" }` |
| `session_connected` | Server → Client | `{ "session_id": "...", "client": "UaExpert" }` |
| `session_disconnected` | Server → Client | `{ "session_id": "..." }` |
| `source_status` | Server → Client | `{ "source": "can", "status": "connected", "msg_rate": 450 }` |
| `server_diag` | Server → Client | `{ "sessions": 3, "subscriptions": 12, "memory_mb": 128 }` |
| `toggle_feature` | Client → Server | `{ "feature": "ENABLE_CAN_SOURCE", "enabled": true }` |
| `feature_toggled` | Server → Client | `{ "feature": "ENABLE_CAN_SOURCE", "enabled": true }` |

---

## 5. Data Source Plugin Architecture

Each data source plugin implements a common interface:

```python
class DataSourcePlugin:
    def __init__(self, config, address_space):
        """Initialize with plugin config and OPC-UA address space reference"""
    
    def start(self):
        """Start polling/listening for data"""
    
    def stop(self):
        """Stop the data source"""
    
    def get_status(self) -> dict:
        """Return plugin status (connected, error count, last update)"""
    
    def get_values(self) -> dict:
        """Return current values as {source_key: value}"""
    
    def write_value(self, source_key, value):
        """Write value to data source (if supported)"""
```

Plugins register at startup and push values to mapped OPC-UA nodes.

---

## 6. Threat Model

| # | Threat | Mitigation |
|---|--------|-----------|
| 1 | Brute-force login | bcrypt + 10 attempts/15min rate limit + account lockout |
| 2 | JWT token theft | 24h expiry, httpOnly secure cookies, token rotation |
| 3 | Unauthorized OPC-UA access | X.509 certificate trust, security policies, session auth |
| 4 | OPC-UA address space manipulation | Node write permissions, audit log, writable flag |
| 5 | Untrusted client certificates | Certificate trust list, auto-reject unknown certs |
| 6 | Data source injection (CAN/Serial) | Input validation, range checks, data type enforcement |
| 7 | REST proxy abuse | JWT auth required, rate limiting, read-only by default |
| 8 | Node-RED flow tampering | Auth on Node-RED editor, flow backup |
| 9 | Man-in-the-middle | OPC-UA SignAndEncrypt, HTTPS/TLS on web dashboard |
| 10 | .env file exposure | File permissions 600, not served by web, gitignored |
| 11 | SQL injection | Parameterized queries exclusively |
| 12 | Historical data tampering | Append-only HDA, integrity checksums |

---

## 7. Development Phases

| Phase | Description | Days |
|-------|-------------|------|
| 1 | Project setup, Flask skeleton, auth system | Day 1 |
| 2 | opcua-asyncio server bootstrap + namespace | Day 1–2 |
| 3 | GPIO data source plugin + node creation | Day 2–3 |
| 4 | SQLite schema, node storage, mapping table | Day 3 |
| 5 | Web dashboard (dark theme, server status, node tree) | Day 3–4 |
| 6 | Address space browser UI (tree-view, attributes) | Day 4 |
| 7 | Dynamic node creation / deletion API + UI | Day 4–5 |
| 8 | Data source mapping editor (drag-and-drop) | Day 5 |
| 9 | Historical data access (HDA storage + read API) | Day 5–6 |
| 10 | CAN bus data source plugin | Day 6–7 |
| 11 | RS232 serial data source plugin | Day 7 |
| 12 | Modbus TCP/RTU data source plugin | Day 7–8 |
| 13 | Alarms & conditions (config, trigger, OPC-UA alarm objects) | Day 8–9 |
| 14 | Certificate security (X.509 gen, trust management) | Day 9 |
| 15 | REST API proxy (browse-path → JSON) | Day 9–10 |
| 16 | Node-RED integration (embedded + opcua nodes) | Day 10 |
| 17 | CODESYS runtime info display | Day 10–11 |
| 18 | Server diagnostics + analytics dashboard | Day 11 |
| 19 | Notification system (Telegram, Slack, email) | Day 11–12 |
| 20 | Feature toggle system (dashboard ↔ .env sync) | Day 12 |
| 21 | systemd service + deploy script + hardening | Day 12–13 |
| 22 | Testing, documentation, final review | Day 13–14 |

---

## 8. File Structure

```
OPC-UA Industrial Gateway/
├── README.md
├── TSD.md
├── task.md
├── implementation_plan.md
├── requirements.txt
├── .env.default
├── init_db.py
├── config/
│   ├── gpio_sources.json
│   ├── alarm_config.json
│   └── can.dbc
├── certs/
│   ├── server_cert.pem
│   ├── server_key.pem
│   └── trusted/
├── scripts/
│   └── generate_certs.py
├── deploy/
│   ├── deploy_to_pi.sh
│   └── opcua-gateway.service
├── docs/
│   └── threat_model.md
├── data/
│   ├── opcua_gateway.db
│   └── nodered_flows/
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── auth.py
│   ├── opcua_server.py
│   ├── address_space.py
│   ├── node_manager.py
│   ├── historical_access.py
│   ├── alarm_manager.py
│   ├── cert_manager.py
│   ├── rest_proxy.py
│   ├── diagnostics.py
│   ├── analytics.py
│   ├── notification_service.py
│   ├── feature_toggles.py
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── base_plugin.py
│   │   ├── gpio_plugin.py
│   │   ├── can_plugin.py
│   │   ├── serial_plugin.py
│   │   └── modbus_plugin.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── opcua_routes.py
│   │   ├── node_routes.py
│   │   ├── mapping_routes.py
│   │   ├── history_routes.py
│   │   ├── alarm_routes.py
│   │   ├── cert_routes.py
│   │   ├── rest_proxy_routes.py
│   │   ├── diag_routes.py
│   │   ├── analytics_routes.py
│   │   └── settings_routes.py
│   └── templates/
│       ├── layout.html
│       ├── login.html
│       ├── dashboard.html
│       ├── address_space.html
│       ├── data_sources.html
│       ├── mapping_editor.html
│       ├── node_manager.html
│       ├── historical.html
│       ├── alarms.html
│       ├── certificates.html
│       ├── nodered.html
│       ├── diagnostics.html
│       ├── analytics.html
│       └── settings.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── dashboard.js
│       ├── address_space.js
│       ├── mapping_editor.js
│       ├── alarms.js
│       ├── analytics.js
│       └── settings.js
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    ├── test_opcua_server.py
    ├── test_gpio_plugin.py
    ├── test_node_manager.py
    ├── test_historical.py
    ├── test_alarms.py
    ├── test_rest_proxy.py
    └── test_toggles.py
```
