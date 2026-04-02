# Technical Specification Document — LoRa Gateway & Mesh Communication Hub

## 1. Scope

### In Scope

- Dual-mode LoRa operation: LoRaWAN gateway mode and Meshtastic mesh mode
- Live mode switching via web dashboard (`LORA_MODE=gateway|mesh|both`)
- LoRaWAN 8-channel gateway using RAK2287/RAK5146 SX1302/SX1303 concentrator HAT
- ChirpStack v4 self-hosted LoRaWAN server (Docker: network server, app server, gateway bridge)
- Optional TTN (The Things Network) cloud integration
- Sensor data ingestion, storage, charting, and threshold alerting
- Meshtastic mesh radio control via Python API (serial)
- Browser-based Meshtastic chat with real-time SocketIO delivery
- GPS node position tracking and Leaflet.js map view
- MQTT bridge via Mosquitto (gateway + mesh topics unified)
- Emergency alert broadcast on mesh (priority messages)
- Geofencing engine with enter/exit alerts for mesh nodes
- Solar power monitoring via INA219/INA260 I2C sensor
- Dark-themed Flask + SocketIO web dashboard
- bcrypt authentication with rate limiting and session expiry
- Mock mode for development/testing without hardware
- All features toggled via `.env`
- SQLite for persistence
- Deployment via rsync to `rasp-pi` (192.168.216.90)

### Out of Scope

- Custom LoRa PHY-layer firmware development
- Single-channel gateway support (SX1276 — insufficient for LoRaWAN)
- Production LoRaWAN roaming or peering with commercial operators
- End-to-end encryption key management for LoRaWAN (handled by ChirpStack)
- Mobile app development (web dashboard only)
- Meshtastic firmware modification (uses stock firmware)
- Cloud hosting or SaaS deployment
- Commercial licensing or paid features
- Non-Linux host OS for the Pi
- Custom PCB design for concentrator modules
- LoRa frequency certification or regulatory compliance testing

---

## 2. MVP Features (P0)

| ID | Feature | Priority |
|----|---------|----------|
| P0-1 | Mode manager (gateway / mesh / both) with live switching | P0 |
| P0-2 | LoRaWAN gateway engine (RAK2287/5146 packet forwarder) | P0 |
| P0-3 | ChirpStack Docker integration (NS + AS + GW bridge) | P0 |
| P0-4 | Sensor data ingestion from ChirpStack uplink events | P0 |
| P0-5 | Sensor dashboard (live charts, device list, latest readings) | P0 |
| P0-6 | Meshtastic mesh controller (serial radio, send/receive) | P0 |
| P0-7 | Meshtastic web chat (browser chat via SocketIO) | P0 |
| P0-8 | MQTT bridge (Mosquitto, gateway + mesh topic hierarchy) | P0 |
| P0-9 | Web dashboard (dark theme, mode selector, tabs) | P0 |
| P0-10 | Authentication (bcrypt, rate limiting 10/15min, 24h session) | P0 |
| P0-11 | SQLite database (schema for devices, sensors, messages, nodes) | P0 |
| P0-12 | Configuration loader (.env with LORA_MODE and all toggles) | P0 |
| P0-13 | Mock mode (simulated radio/sensors for dev/testing) | P0 |
| P0-14 | Deploy script (rsync to rasp-pi) | P0 |

### Nice-to-Have (P1/P2)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| P1-1 | GPS node position tracking (gpsd) | P1 | Leaflet.js map view |
| P1-2 | Geofencing (enter/exit alerts) | P1 | Circular zones, per-node rules |
| P1-3 | Emergency alert broadcast (mesh priority) | P1 | SOS, weather, evacuation types |
| P1-4 | Sensor alert thresholds (configurable per type) | P1 | Temperature, humidity, etc. |
| P1-5 | Multi-channel gateway (8-channel SX1302/SX1303) | P1 | Regional freq plan auto-config |
| P1-6 | TTN cloud integration (alternative to self-hosted) | P1 | TTN v3 API |
| P2-1 | Power monitoring (INA219/INA260 I2C) | P2 | Solar panel + battery |
| P2-2 | Data export (CSV sensor data) | P2 | Historical download |
| P2-3 | MQTT TLS encryption | P2 | For external MQTT clients |
| P2-4 | Grafana/InfluxDB push | P2 | Advanced analytics |

---

## 3. Database Schema

SQLite with WAL mode enabled. All timestamps stored as ISO-8601 UTC.

### Table: `devices`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique device ID |
| dev_eui | TEXT | NOT NULL, UNIQUE, INDEX | LoRaWAN device EUI (hex) |
| name | TEXT | NOT NULL | Human-readable device name |
| device_type | TEXT | NOT NULL, DEFAULT 'sensor' | `sensor`, `actuator`, `tracker` |
| join_method | TEXT | DEFAULT 'OTAA' | `OTAA` or `ABP` |
| application_id | TEXT | | ChirpStack application ID |
| last_seen_at | TEXT | | ISO-8601 last uplink timestamp |
| rssi | INTEGER | | Last received signal strength (dBm) |
| snr | REAL | | Last signal-to-noise ratio (dB) |
| battery_level | REAL | | Last reported battery (0–100%) |
| is_active | INTEGER | DEFAULT 1 | 1 if device is active |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |
| updated_at | TEXT | NOT NULL | ISO-8601 last modification timestamp |

### Table: `sensor_data`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique reading ID |
| device_id | INTEGER | FK → devices.id, INDEX | Source device reference |
| sensor_type | TEXT | NOT NULL, INDEX | `temperature`, `humidity`, `soil_moisture`, `pressure`, etc. |
| value | REAL | NOT NULL | Sensor reading value |
| unit | TEXT | NOT NULL | Measurement unit (`°C`, `%`, `hPa`, etc.) |
| raw_payload | TEXT | | Raw LoRaWAN payload (hex) |
| received_at | TEXT | NOT NULL, INDEX | ISO-8601 reception timestamp |

### Table: `messages`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique message ID |
| node_id | TEXT | NOT NULL, INDEX | Meshtastic node ID (hex) |
| node_name | TEXT | | Node long name or alias |
| channel | INTEGER | NOT NULL, DEFAULT 0 | Meshtastic channel index |
| content | TEXT | NOT NULL | Message text content |
| direction | TEXT | NOT NULL | `inbound` or `outbound` |
| is_emergency | INTEGER | DEFAULT 0 | 1 if priority/emergency message |
| delivered | INTEGER | DEFAULT 0 | 1 if delivery confirmed (mesh ACK) |
| sent_at | TEXT | NOT NULL | ISO-8601 send/receive timestamp |

### Table: `nodes`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique node record ID |
| node_id | TEXT | NOT NULL, UNIQUE, INDEX | Meshtastic node ID (hex) |
| long_name | TEXT | | Node long name |
| short_name | TEXT | | Node short name (4-char) |
| hw_model | TEXT | | Hardware model string |
| latitude | REAL | | Last known latitude |
| longitude | REAL | | Last known longitude |
| altitude | REAL | | Last known altitude (meters) |
| battery_level | REAL | | Battery percentage (0–100) |
| snr | REAL | | Last signal-to-noise ratio |
| last_heard_at | TEXT | | ISO-8601 last heard timestamp |
| is_online | INTEGER | DEFAULT 1 | 1 if node is considered online |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |
| updated_at | TEXT | NOT NULL | ISO-8601 last update timestamp |

### Table: `alerts`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique alert ID |
| alert_type | TEXT | NOT NULL | `sensor_threshold`, `geofence_exit`, `geofence_enter`, `emergency`, `low_voltage` |
| source_type | TEXT | NOT NULL | `device` (LoRaWAN) or `node` (mesh) |
| source_id | TEXT | NOT NULL | Device EUI or node ID |
| message | TEXT | NOT NULL | Alert description text |
| severity | TEXT | NOT NULL, DEFAULT 'warning' | `info`, `warning`, `critical` |
| acknowledged | INTEGER | DEFAULT 0 | 1 if alert has been acknowledged |
| acknowledged_at | TEXT | | ISO-8601 acknowledgment timestamp |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |

### Table: `geofences`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique geofence ID |
| name | TEXT | NOT NULL | Geofence zone name |
| center_lat | REAL | NOT NULL | Center latitude |
| center_lon | REAL | NOT NULL | Center longitude |
| radius_m | REAL | NOT NULL | Radius in meters |
| node_id | TEXT | | Specific node ID (NULL = all nodes) |
| is_active | INTEGER | DEFAULT 1 | 1 if geofence is active |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |

### Table: `power_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique log ID |
| voltage | REAL | NOT NULL | Battery/panel voltage (V) |
| current_ma | REAL | NOT NULL | Current draw (mA) |
| power_mw | REAL | NOT NULL | Power consumption (mW) |
| source | TEXT | NOT NULL, DEFAULT 'battery' | `battery`, `solar`, `usb` |
| recorded_at | TEXT | NOT NULL, INDEX | ISO-8601 recording timestamp |

### Table: `settings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | TEXT | PK | Setting name |
| value | TEXT | | Setting value (JSON-encoded) |
| updated_at | TEXT | NOT NULL | ISO-8601 last update time |

---

## 4. High-Level Architecture

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4/5 — LoRa Hub                                │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                Mode Manager (LORA_MODE=gateway|mesh|both)               │  │
│  │                                                                         │  │
│  │    LORA_MODE=gateway          LORA_MODE=mesh         LORA_MODE=both    │  │
│  │    ┌──────────────┐          ┌──────────────┐       ┌──────────────┐   │  │
│  │    │ Gateway only │          │ Mesh only    │       │ Gateway+Mesh │   │  │
│  │    └──────┬───────┘          └──────┬───────┘       └──┬────────┬──┘   │  │
│  └───────────┼─────────────────────────┼──────────────────┼────────┼──────┘  │
│              │                         │                  │        │          │
│  ┌───────────▼──────────┐    ┌─────────▼─────────┐       │        │          │
│  │ LoRaWAN Gateway       │    │ Meshtastic Mesh    │  ◄───┘        └──►      │
│  │                       │    │                    │  (both modules active)   │
│  │ RAK2287/5146 HAT      │    │ Serial radio API   │                         │
│  │ SX1302/SX1303         │    │ /dev/ttyUSB0       │                         │
│  │ 8-ch concentrator     │    │                    │                         │
│  │ Packet Forwarder      │    │ ┌────────────────┐ │                         │
│  │          │            │    │ │ Chat handler   │ │                         │
│  │ ┌────────▼──────────┐│    │ │ GPS tracker    │ │                         │
│  │ │ ChirpStack Docker ││    │ │ Node manager   │ │                         │
│  │ │ NS + AS + GW Br.  ││    │ │ Emergency tx   │ │                         │
│  │ │ gRPC/REST API     ││    │ │ Geofence check │ │                         │
│  │ └────────┬──────────┘│    │ └────────┬───────┘ │                         │
│  │          │           │    │          │         │                          │
│  │ ┌────────▼──────────┐│    └──────────┼─────────┘                          │
│  │ │ Sensor Ingestion  ││               │                                    │
│  │ │ Decode, store,    ││               │                                    │
│  │ │ alert on threshold││               │                                    │
│  │ └────────┬──────────┘│               │                                    │
│  └──────────┼───────────┘               │                                    │
│             │                           │                                    │
│  ┌──────────▼───────────────────────────▼──────────────────────────────────┐ │
│  │                     MQTT Bridge (Mosquitto on Pi)                        │ │
│  │  lora-hub/gateway/{dev_eui}/rx      lora-hub/mesh/chat/{channel}        │ │
│  │  lora-hub/gateway/{dev_eui}/tx      lora-hub/mesh/position/{node_id}    │ │
│  │  lora-hub/alerts/{type}             lora-hub/power/{metric}             │ │
│  └──────────────────────────┬──────────────────────────────────────────────┘ │
│                             │                                                │
│  ┌──────────────────────────▼──────────────────────────────────────────────┐ │
│  │                       SQLite Database (WAL mode)                         │ │
│  │ devices | sensor_data | messages | nodes | alerts | geofences           │ │
│  │ power_logs | settings                                                   │ │
│  └──────────────────────────┬──────────────────────────────────────────────┘ │
│                             │                                                │
│  ┌──────────────────────────▼──────────────────────────────────────────────┐ │
│  │          Flask + SocketIO Dashboard (0.0.0.0:5000, dark theme)           │ │
│  │  - bcrypt auth (rate limit 10/15min, 24h session)                       │ │
│  │  - Mode selector: Gateway | Mesh | Both (live switch)                   │ │
│  │  - Sensor charts, alert panel, device list                              │ │
│  │  - Meshtastic chat, GPS map, emergency broadcast                        │ │
│  │  - Power monitoring gauges                                              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌───────────────┐   ┌───────────────┐   ┌──────────────────────┐           │
│  │ Power Monitor  │   │ GPS Module    │   │ INA219/INA260 (I2C)  │           │
│  │ (optional)     │   │ (optional)    │   │ Solar/Battery sensor │           │
│  └───────────────┘   └───────────────┘   └──────────────────────┘           │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Threat Model

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| Brute-force dashboard login | Unauthorized mode control | Medium | bcrypt, rate limiting (10/15min), session expiry (24h) |
| MQTT without auth exposed to network | Data interception/injection | High | Configure MQTT user/pass, restrict port 1883 to LAN, TLS for external |
| ChirpStack API key leak | Device management takeover | Medium | Rotate API key, restrict to localhost, never commit to VCS |
| Malicious LoRaWAN join (rogue device) | Unauthorized network access | Low | OTAA with unique AppKey per device, monitor join requests |
| Meshtastic channel PSK bruteforce | Mesh chat interception | Low | Use strong channel PSK (256-bit), rotate periodically |
| CSRF on mode switching | Unauthorized mode change | Medium | CSRF tokens on all POST forms, mode switch requires auth |
| Flask SECRET_KEY leak | Session hijacking | Medium | Generate strong key, never commit to VCS, rotate periodically |
| SQL injection on sensor queries | Data leak or corruption | Low | Parameterized queries for all DB operations |
| Denial of service (flood uplinks) | Gateway overload | Low | Rate-limit per device in ChirpStack, monitor uplink counts |
| Physical theft of Pi | Credentials on disk | Medium | Encrypt `.env`, restrict file permissions, consider Luks-encrypted partition |
| GPS spoofing of mesh nodes | False geofence alerts | Low | Cross-reference node position history, anomaly detection |
| Man-in-the-middle on MQTT | Sensor data tampering | Medium | TLS on MQTT, certificate pinning for external clients |

---

## 6. Tech Stack

| Layer | Technology | Version / Notes |
|-------|-----------|-----------------|
| Language | Python 3.11+ | Type hints throughout |
| Web framework | Flask | 3.x with app factory pattern |
| Real-time | Flask-SocketIO | eventlet async mode |
| LoRaWAN server | ChirpStack v4 | Docker (NS + AS + GW Bridge + PostgreSQL + Redis) |
| LoRa concentrator | RAK2287 / RAK5146 | SX1302/SX1303, 8-channel, SPI interface |
| Packet forwarder | chirpstack-concentratord | Or Semtech UDP packet forwarder |
| Meshtastic | meshtastic (Python) | Serial API to Meshtastic radio |
| MQTT | Mosquitto + paho-mqtt | Local broker + Python client |
| GPS | gpsd + gpsd-py3 | GPS daemon integration |
| Auth | bcrypt | Password hashing |
| Config | python-dotenv | `.env` loader |
| Database | SQLite3 | WAL mode, stdlib `sqlite3` |
| Frontend charts | Chart.js | Sensor data visualization |
| Frontend maps | Leaflet.js | GPS node map |
| CSS | Custom dark theme | No framework |
| Deployment | rsync + systemd | SSH alias `rasp-pi` |
| Testing | pytest + pytest-cov | Mocking with unittest.mock |

---

## 7. Development Phases

### Phase 1 — Project Foundation & Dual-Mode Engine

**Goal:** Scaffold the project, configure environment loading, set up the database, and build the core mode manager with gateway/mesh controllers.

| # | Task | Deliverable |
|---|------|-------------|
| 1.1 | Initialize project structure (dirs, `pyproject.toml`, `requirements.txt`) | Repo skeleton |
| 1.2 | Implement `.env` config loader with dataclass validation | `src/config.py` |
| 1.3 | Implement SQLite database module with schema creation (WAL mode) | `src/database.py` |
| 1.4 | Implement mode manager (gateway/mesh/both orchestrator) | `src/mode_manager.py` |
| 1.5 | Implement LoRaWAN gateway engine (packet forwarder interface) | `src/gateway.py` |
| 1.6 | Implement Meshtastic mesh controller (serial radio API) | `src/mesh.py` |
| 1.7 | Implement mock mode (simulated radio/sensors for dev/testing) | Mock paths |
| 1.8 | Write unit tests for config, database, mode manager, gateway, mesh | `tests/` |

### Phase 2 — ChirpStack Integration & Sensor Dashboard

**Goal:** Integrate with ChirpStack for LoRaWAN device management and build the sensor data dashboard.

| # | Task | Deliverable |
|---|------|-------------|
| 2.1 | Implement ChirpStack API client (gRPC/REST) | `src/chirpstack.py` |
| 2.2 | Implement sensor data ingestion (uplink event processing) | `src/sensors.py` |
| 2.3 | Implement sensor threshold alerting | `src/sensors.py` |
| 2.4 | Implement MQTT bridge (Mosquitto pub/sub) | `src/mqtt_bridge.py` |
| 2.5 | Write unit tests for ChirpStack, sensors, MQTT | `tests/` |

### Phase 3 — Meshtastic Chat, GPS & Emergency

**Goal:** Build the web chat, GPS tracking, geofencing, and emergency alert features.

| # | Task | Deliverable |
|---|------|-------------|
| 3.1 | Implement chat message handler (send/receive/store) | `src/chat.py` |
| 3.2 | Implement GPS position tracker (gpsd) | `src/gps.py` |
| 3.3 | Implement geofencing engine (boundary calculations) | `src/geofence.py` |
| 3.4 | Implement emergency alert broadcast | `src/emergency.py` |
| 3.5 | Write unit tests for chat, GPS, geofence, emergency | `tests/` |

### Phase 4 — Web Dashboard & Authentication

**Goal:** Build the authenticated dark-themed dashboard with all feature tabs.

| # | Task | Deliverable |
|---|------|-------------|
| 4.1 | Implement Flask app factory with SocketIO | `src/app.py` |
| 4.2 | Implement bcrypt auth with rate limiting (10/15min) and session (24h) | `src/auth.py` |
| 4.3 | Create dark-theme base template and CSS | `templates/`, `static/` |
| 4.4 | Build login page | `templates/login.html` |
| 4.5 | Build main dashboard (mode selector, overview cards) | `templates/dashboard.html` |
| 4.6 | Build sensor dashboard (charts, device list, alerts) | `templates/sensors.html` |
| 4.7 | Build Meshtastic chat page | `templates/chat.html` |
| 4.8 | Build GPS node map page | `templates/map.html` |
| 4.9 | Build emergency alert page | `templates/emergency.html` |
| 4.10 | Build settings panel (mode switch, feature toggles) | `templates/settings.html` |
| 4.11 | Implement SocketIO real-time events | `static/js/` |
| 4.12 | Write API endpoint and auth tests | `tests/` |

### Phase 5 — Power Monitoring & Advanced Features

**Goal:** Add solar power monitoring, data export, MQTT TLS, and polish.

| # | Task | Deliverable |
|---|------|-------------|
| 5.1 | Implement power monitoring (INA219/INA260 I2C) | `src/power.py` |
| 5.2 | Build power monitoring page | `templates/power.html` |
| 5.3 | Implement sensor data CSV export | `src/sensors.py` |
| 5.4 | Implement MQTT TLS configuration | `src/mqtt_bridge.py` |
| 5.5 | Write power monitoring and export tests | `tests/` |

### Phase 6 — Deployment & Documentation

**Goal:** Finalize deploy pipeline, setup scripts, and all documentation.

| # | Task | Deliverable |
|---|------|-------------|
| 6.1 | Create deploy script (rsync to rasp-pi) | `deploy/deploy_to_pi.sh` |
| 6.2 | Create OS dependency installer script | `scripts/install_deps.sh` |
| 6.3 | Create ChirpStack Docker setup script | `scripts/setup_chirpstack.sh` |
| 6.4 | Create Mosquitto configuration script | `scripts/setup_mosquitto.sh` |
| 6.5 | Write systemd service unit | docs / README |
| 6.6 | Write mode switching guide | `docs/mode_switching.md` |
| 6.7 | Write ChirpStack setup guide | `docs/chirpstack_setup.md` |
| 6.8 | Write antenna guide | `docs/antenna_guide.md` |
| 6.9 | Write MQTT topics documentation | `docs/mqtt_topics.md` |
| 6.10 | Final integration testing on Raspberry Pi hardware | Test report |
| 6.11 | Update README with final instructions | `README.md` |

---

## 8. `.env.default` Reference

```ini
# ─── Flask & Security ──────────────────────────────────────
SECRET_KEY=change-me-to-a-random-string
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...  # bcrypt hash of your password

# ─── Database ──────────────────────────────────────────────
DB_PATH=data/lora_hub.db

# ─── LoRa Mode ─────────────────────────────────────────────
LORA_MODE=gateway
# Operational mode: gateway | mesh | both
# gateway = LoRaWAN gateway only (ChirpStack + sensors)
# mesh    = Meshtastic mesh only (chat + GPS + emergency)
# both    = Simultaneous gateway + mesh

# ─── LoRa Hardware ─────────────────────────────────────────
CONCENTRATOR_MODEL=RAK5146
# Supported: RAK2287, RAK5146
LORA_REGION=EU868
# Frequency plan: EU868, US915, AS923, AU915, IN865, KR920, etc.
ENABLE_MULTI_CHANNEL=true

# ─── ChirpStack (Gateway Mode) ────────────────────────────
ENABLE_CHIRPSTACK=true
CHIRPSTACK_API_URL=http://localhost:8080
CHIRPSTACK_API_KEY=your-chirpstack-api-key-here
# ChirpStack runs in Docker: NS + AS + Gateway Bridge + PostgreSQL + Redis

# ─── Sensor Dashboard ─────────────────────────────────────
ENABLE_SENSOR_DASHBOARD=true
SENSOR_ALERT_THRESHOLD={"temperature": 40, "humidity": 90}
# JSON map of sensor_type -> threshold value

# ─── Meshtastic (Mesh Mode) ───────────────────────────────
ENABLE_MESHTASTIC=true
MESHTASTIC_DEVICE=/dev/ttyUSB0
# Serial port for Meshtastic radio (USB or UART)
MESHTASTIC_CHANNEL=0
# Default channel index (0 = primary)

# ─── Web Chat ─────────────────────────────────────────────
ENABLE_WEB_CHAT=true

# ─── MQTT Bridge ──────────────────────────────────────────
ENABLE_MQTT_BRIDGE=true
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC_PREFIX=lora-hub
# Topic hierarchy:
#   lora-hub/gateway/{dev_eui}/rx   (sensor uplinks)
#   lora-hub/gateway/{dev_eui}/tx   (downlinks)
#   lora-hub/mesh/chat/{channel}    (mesh messages)
#   lora-hub/mesh/position/{node}   (GPS positions)
#   lora-hub/alerts/{type}          (threshold/geofence/emergency)
#   lora-hub/power/{metric}         (voltage/current/power)

# ─── GPS Tracking ─────────────────────────────────────────
ENABLE_GPS=false
GPSD_HOST=localhost
GPSD_PORT=2947

# ─── Geofencing ───────────────────────────────────────────
ENABLE_GEOFENCING=false
GEOFENCE_RADIUS_M=1000
GEOFENCE_CENTER_LAT=
GEOFENCE_CENTER_LON=

# ─── Emergency Alerts ─────────────────────────────────────
ENABLE_EMERGENCY_ALERTS=true
EMERGENCY_PRIORITY=high
# Priority level for emergency mesh broadcasts

# ─── Power Monitoring ─────────────────────────────────────
ENABLE_POWER_MONITORING=false
POWER_I2C_ADDRESS=0x40
POWER_LOW_THRESHOLD_V=11.5
# Low voltage alert threshold (volts)

# ─── Web Dashboard ────────────────────────────────────────
ENABLE_WEB_DASHBOARD=true
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
SESSION_EXPIRY_HOURS=24
RATE_LIMIT=10/15min

# ─── Development ──────────────────────────────────────────
MOCK_MODE=false
LOG_LEVEL=INFO
```

---

## 9. Deliverables

| # | Deliverable | Format | Notes |
|---|-------------|--------|-------|
| 1 | Mode manager (gateway/mesh/both orchestrator) | Python module | `src/mode_manager.py` |
| 2 | LoRaWAN gateway engine | Python module | `src/gateway.py` |
| 3 | Meshtastic mesh controller | Python module | `src/mesh.py` |
| 4 | ChirpStack API client | Python module | `src/chirpstack.py` |
| 5 | Sensor data ingestion & alerting | Python module | `src/sensors.py` |
| 6 | Chat message handler | Python module | `src/chat.py` |
| 7 | MQTT bridge (Mosquitto) | Python module | `src/mqtt_bridge.py` |
| 8 | GPS position tracker | Python module | `src/gps.py` |
| 9 | Geofencing engine | Python module | `src/geofence.py` |
| 10 | Emergency alert broadcaster | Python module | `src/emergency.py` |
| 11 | Power monitoring | Python module | `src/power.py` |
| 12 | SQLite database layer | Python module | `src/database.py` |
| 13 | Flask + SocketIO dashboard | Python + HTML/JS/CSS | `src/app.py`, `templates/`, `static/` |
| 14 | bcrypt auth with rate limiting | Python module | `src/auth.py` |
| 15 | Configuration loader | Python module | `src/config.py` |
| 16 | Deploy script | Bash | `deploy/deploy_to_pi.sh` |
| 17 | ChirpStack Docker setup script | Bash | `scripts/setup_chirpstack.sh` |
| 18 | Mosquitto configuration script | Bash | `scripts/setup_mosquitto.sh` |
| 19 | OS dependency installer | Bash | `scripts/install_deps.sh` |
| 20 | systemd service unit | INI | Documented in README |
| 21 | Test suite (≥80% coverage) | pytest | `tests/` |
| 22 | Mode switching guide | Markdown | `docs/mode_switching.md` |
| 23 | ChirpStack setup guide | Markdown | `docs/chirpstack_setup.md` |
| 24 | Antenna guide | Markdown | `docs/antenna_guide.md` |
| 25 | MQTT topics documentation | Markdown | `docs/mqtt_topics.md` |
| 26 | README & TSD | Markdown | Root-level docs |
