# Implementation Plan — LoRa Gateway & Mesh Communication Hub

## Phase 1 — Project Foundation & Dual-Mode Engine

**Goal:** Scaffold the project, configure environment loading, set up the database, and build the core mode manager with LoRaWAN gateway and Meshtastic mesh controllers.

- [ ] **Step 1.1 — Initialize Project Structure**
  - [ ] Create directory tree:
    ```
    src/, templates/, static/css/, static/js/, tests/, deploy/, scripts/, docs/, data/
    ```
  - [ ] Create `pyproject.toml` with project name, version, Python ≥3.11, and entry point `src.app`
  - [ ] Create `requirements.txt`:
    ```
    flask
    flask-socketio
    eventlet
    bcrypt
    python-dotenv
    chirpstack-api
    meshtastic
    paho-mqtt
    gpsd-py3
    Jinja2
    gunicorn
    smbus2
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
  - [ ] Parse `LORA_MODE` string into validated enum (`gateway`, `mesh`, `both`)
  - [ ] Parse `SENSOR_ALERT_THRESHOLD` JSON string into `dict[str, float]`
  - [ ] Parse `POWER_I2C_ADDRESS` hex string to int
  - [ ] Add `is_enabled(feature: str) -> bool` helper for toggle checks
  - [ ] Add `is_gateway_mode() -> bool` and `is_mesh_mode() -> bool` convenience methods
  - [ ] Write `tests/test_config.py` — test loading, defaults, type conversion, mode parsing

- [ ] **Step 1.3 — SQLite Database Module**
  - [ ] Create `src/database.py`
  - [ ] Implement `get_connection(db_path)` with WAL mode pragma
  - [ ] Implement `init_db(conn)` — creates all 8 tables (see TSD §3)
  - [ ] Implement CRUD functions:
    - `insert_device(conn, data)` / `update_device(conn, dev_eui, data)` / `get_device(conn, dev_eui)` / `list_devices(conn)`
    - `insert_sensor_data(conn, data)` / `get_sensor_latest(conn, device_id, type, limit)` / `get_sensor_history(conn, device_id, type, start, end)`
    - `insert_message(conn, data)` / `get_messages(conn, channel, limit, offset)`
    - `insert_node(conn, data)` / `update_node(conn, node_id, data)` / `get_node(conn, node_id)` / `list_nodes(conn)`
    - `insert_alert(conn, data)` / `acknowledge_alert(conn, alert_id)` / `get_alerts(conn, limit, acknowledged)`
    - `insert_geofence(conn, data)` / `delete_geofence(conn, id)` / `list_geofences(conn)`
    - `insert_power_log(conn, data)` / `get_power_history(conn, start, end)`
    - `get_setting(conn, key)` / `set_setting(conn, key, value)`
  - [ ] Use parameterized queries for all DB operations
  - [ ] Write `tests/test_database.py` — test schema creation, all CRUD ops, WAL mode

- [ ] **Step 1.4 — Mode Manager**
  - [ ] Create `src/mode_manager.py` with `ModeManager` class:
    - `__init__(config, gateway_engine, mesh_controller)`:
      - Store references to both engines
      - Initialize current mode from `config.LORA_MODE`
      - Threading lock for safe mode transitions
    - `start() -> None`:
      - Start engine(s) matching current mode
      - Log mode activation
    - `stop() -> None`:
      - Gracefully stop all active engines
      - Log shutdown
    - `switch_mode(new_mode: str) -> bool`:
      - Acquire lock
      - Validate new_mode (`gateway`, `mesh`, `both`)
      - Stop current engine(s) not needed in new mode
      - Start engine(s) needed in new mode but not already running
      - Update current mode state
      - Emit SocketIO `mode_changed` event
      - Release lock
      - Return success
    - `get_status() -> dict`:
      - Return: `{mode, gateway_active, mesh_active, gateway_status, mesh_status}`
  - [ ] Write `tests/test_mode_manager.py` — test start, stop, switch modes, concurrent access

- [ ] **Step 1.5 — LoRaWAN Gateway Engine**
  - [ ] Create `src/gateway.py` with `GatewayEngine` class:
    - `__init__(config)`:
      - Store concentrator model, region, SPI config
      - Track running state
    - `start() -> None`:
      - Verify SPI interface available
      - Start packet forwarder process (subprocess or library)
      - Configure frequency plan from `LORA_REGION`
      - Log startup with concentrator model
    - `stop() -> None`:
      - Terminate packet forwarder process
      - Release SPI interface
      - Log shutdown
    - `get_status() -> dict`:
      - Return: `{running, concentrator_model, region, uplink_count, downlink_count}`
    - `is_running() -> bool`
  - [ ] Configure for RAK2287 (SX1302) and RAK5146 (SX1303) models
  - [ ] Handle concentrator reset GPIO pin
  - [ ] Write `tests/test_gateway.py` — test start/stop with mocked hardware

- [ ] **Step 1.6 — Meshtastic Mesh Controller**
  - [ ] Create `src/mesh.py` with `MeshController` class:
    - `__init__(config)`:
      - Store serial device path, default channel
      - Initialize meshtastic interface reference (None until started)
    - `start() -> None`:
      - Connect to Meshtastic radio via `meshtastic.serial_interface.SerialInterface`
      - Register `on_receive` callback for incoming packets
      - Log connection with device path
    - `stop() -> None`:
      - Close serial interface cleanly
      - Log disconnect
    - `send_text(text: str, channel: int = 0, destination: str = None) -> bool`:
      - Send text message via interface
      - Set destination to broadcast if None
      - Return success
    - `send_priority(text: str, channel: int = 0) -> bool`:
      - Send with priority flag (for emergency)
    - `get_nodes() -> list[dict]`:
      - Return node list from interface's nodesByNum
    - `get_node_info(node_id: str) -> dict`:
      - Return detailed info for specific node
    - `get_status() -> dict`:
      - Return: `{connected, device, channel, node_count}`
    - `on_receive(packet)`:
      - Internal callback — dispatch to registered handlers
    - `register_handler(handler: callable)`:
      - Register external callback for incoming packets
  - [ ] Write `tests/test_mesh.py` — test connect/disconnect, send/receive with mocked serial

- [ ] **Step 1.7 — Mock Mode**
  - [ ] Implement `MockGatewayEngine` class — simulates periodic uplink events with random sensor data
  - [ ] Implement `MockMeshController` class — simulates incoming messages and node positions
  - [ ] Implement `MockMQTTBridge` class — logs publish/subscribe to stdout
  - [ ] Implement `MockPowerMonitor` class — returns randomized voltage/current readings
  - [ ] Implement `MockGPS` class — returns static test coordinates
  - [ ] Factory functions: `create_gateway(config)`, `create_mesh(config)`, `create_mqtt(config)`
  - [ ] Activate via `MOCK_MODE=true`
  - [ ] Allow full dashboard and feature testing without hardware

- [ ] **Step 1.8 — Phase 1 Tests**
  - [ ] `tests/test_config.py` — loading, defaults, type conversion, LORA_MODE, feature toggles
  - [ ] `tests/test_database.py` — schema creation, CRUD for all 8 tables, WAL mode
  - [ ] `tests/test_mode_manager.py` — start, stop, switch (gateway→mesh, mesh→both, etc.), concurrent switch rejection
  - [ ] `tests/test_gateway.py` — start/stop, status, mocked SPI/subprocess
  - [ ] `tests/test_mesh.py` — connect/disconnect, send/receive, get_nodes, mocked serial

**Checkpoint:** Mode manager orchestrates gateway and mesh engines. Live mode switching works. Both engines start/stop independently. Config loader handles LORA_MODE and all toggles. Database stores all 8 table schemas.

---

## Phase 2 — ChirpStack Integration & Sensor Dashboard

**Goal:** Integrate with ChirpStack for LoRaWAN device management, build sensor data ingestion pipeline, and establish the MQTT bridge.

- [ ] **Step 2.1 — ChirpStack API Client**
  - [ ] Create `src/chirpstack.py` with `ChirpStackClient` class:
    - `__init__(config)`:
      - Store API URL and API key
      - Initialize gRPC channel or REST session
    - `connect() -> bool`:
      - Establish connection to ChirpStack API
      - Verify API key is valid
      - Return success
    - `list_devices() -> list[dict]`:
      - Fetch all registered devices via API
      - Return: `[{dev_eui, name, last_seen_at, ...}]`
    - `get_device(dev_eui: str) -> dict`:
      - Fetch single device details and activation status
    - `get_device_events(dev_eui: str, limit: int = 20) -> list[dict]`:
      - Fetch recent uplink events for device
      - Return decoded payloads with metadata
    - `enqueue_downlink(dev_eui: str, payload: bytes, port: int = 1) -> bool`:
      - Schedule downlink command to device
    - `subscribe_events(callback: callable) -> None`:
      - Open streaming gRPC connection for real-time uplink events
      - Call callback(event) on each uplink
    - `disconnect() -> None`:
      - Close gRPC channel / REST session
  - [ ] Toggle via `ENABLE_CHIRPSTACK`

- [ ] **Step 2.2 — Sensor Data Ingestion**
  - [ ] Create `src/sensors.py` with `SensorManager` class:
    - `__init__(config, db, mqtt_bridge)`:
      - Store references to database and MQTT bridge
      - Load alert thresholds from config
    - `process_uplink(event: dict) -> list[SensorReading]`:
      - Extract device EUI, payload, metadata from ChirpStack event
      - Decode payload (CayenneLPP, custom JSON, raw hex)
      - Return list of `SensorReading(sensor_type, value, unit)`
    - `store_reading(device_id: int, sensor_type: str, value: float, unit: str) -> int`:
      - Insert into `sensor_data` table
      - Return reading ID
    - `ingest_uplink(event: dict) -> None`:
      - Orchestrate: process → store → check thresholds → publish MQTT → emit SocketIO
      - Update device `last_seen_at`, `rssi`, `snr`
    - `get_latest(device_id: int, sensor_type: str, limit: int = 10) -> list[dict]`:
      - Return last N readings
    - `get_history(device_id: int, sensor_type: str, start: str, end: str) -> list[dict]`:
      - Return time-range query results
    - `export_csv(device_id: int, sensor_type: str, start: str, end: str) -> str`:
      - Generate CSV string from history query
  - [ ] Support payload decoders: CayenneLPP (binary), JSON, raw hex with codec config

- [ ] **Step 2.3 — Sensor Threshold Alerting**
  - [ ] Implement `check_thresholds(reading: SensorReading, device_id: int) -> Alert | None`:
    - Compare reading value against `SENSOR_ALERT_THRESHOLD[sensor_type]`
    - If exceeded: create `Alert` record with severity based on margin
    - Publish to MQTT topic `lora-hub/alerts/sensor_threshold`
    - Emit SocketIO `sensor_alert` event
    - Return Alert object or None
  - [ ] Configurable per sensor type from `SENSOR_ALERT_THRESHOLD` JSON

- [ ] **Step 2.4 — MQTT Bridge**
  - [ ] Create `src/mqtt_bridge.py` with `MQTTBridge` class:
    - `__init__(config)`:
      - Store broker host, port, credentials, topic prefix
      - Initialize paho-mqtt Client
    - `connect() -> bool`:
      - Connect to Mosquitto with optional username/password
      - Set up `on_connect`, `on_disconnect`, `on_message` callbacks
      - Start network loop in background thread
      - Return success
    - `disconnect() -> None`:
      - Stop network loop, disconnect from broker
    - `publish(topic: str, payload: dict, qos: int = 1) -> bool`:
      - Publish JSON-serialized payload to `{prefix}/{topic}`
      - Return success
    - `subscribe(topic: str, callback: callable, qos: int = 1) -> None`:
      - Subscribe to `{prefix}/{topic}` with callback
    - `publish_sensor(dev_eui: str, reading: dict) -> bool`:
      - Publish to `lora-hub/gateway/{dev_eui}/rx`
    - `publish_chat(channel: int, message: dict) -> bool`:
      - Publish to `lora-hub/mesh/chat/{channel}`
    - `publish_position(node_id: str, position: dict) -> bool`:
      - Publish to `lora-hub/mesh/position/{node_id}`
    - `publish_alert(alert_type: str, alert: dict) -> bool`:
      - Publish to `lora-hub/alerts/{alert_type}`
    - `publish_power(metric: str, value: float) -> bool`:
      - Publish to `lora-hub/power/{metric}`
  - [ ] Handle automatic reconnection on broker disconnect
  - [ ] Toggle via `ENABLE_MQTT_BRIDGE`

- [ ] **Step 2.5 — Phase 2 Tests**
  - [ ] `tests/test_chirpstack.py`:
    - Test connect with valid/invalid API key (mocked gRPC)
    - Test list_devices, get_device, get_device_events
    - Test enqueue_downlink
    - Test subscribe_events callback
  - [ ] `tests/test_sensors.py`:
    - Test process_uplink (CayenneLPP, JSON, raw hex payloads)
    - Test store_reading and DB insertion
    - Test get_latest and get_history queries
    - Test threshold check (within range, exceeded, alert creation)
    - Test export_csv format
  - [ ] `tests/test_mqtt_bridge.py`:
    - Test connect/disconnect (mocked paho-mqtt)
    - Test publish to each topic type
    - Test subscribe and callback invocation
    - Test reconnection on disconnect

**Checkpoint:** ChirpStack integration receives LoRaWAN uplinks and stores sensor data. Threshold alerts fire on breach. MQTT bridge publishes all events to organized topic hierarchy. Sensor history queryable with time ranges.

---

## Phase 3 — Meshtastic Chat, GPS & Emergency

**Goal:** Build the web chat, GPS tracking, geofencing, and emergency alert features for mesh mode.

- [ ] **Step 3.1 — Chat Message Handler**
  - [ ] Create `src/chat.py` with `ChatHandler` class:
    - `__init__(config, db, mesh_controller, mqtt_bridge)`:
      - Store references to mesh controller, database, MQTT bridge
      - Register as mesh controller message handler
    - `send_message(text: str, channel: int = 0, destination: str = None) -> bool`:
      - Call mesh controller `send_text()`
      - Store outbound message in `messages` table (direction='outbound')
      - Publish to MQTT `lora-hub/mesh/chat/{channel}`
      - Return success
    - `on_message_received(packet: dict) -> None`:
      - Extract node_id, text, channel from mesh packet
      - Resolve node name from `nodes` table
      - Store inbound message in `messages` table (direction='inbound')
      - Publish to MQTT
      - Emit SocketIO `chat_message` event
    - `get_history(channel: int, limit: int = 50, offset: int = 0) -> list[dict]`:
      - Return paginated message history with node names
  - [ ] Toggle via `ENABLE_WEB_CHAT`

- [ ] **Step 3.2 — GPS Position Tracker**
  - [ ] Create `src/gps.py` with `GPSTracker` class:
    - `__init__(config, db, mqtt_bridge)`:
      - Store references
      - Initialize gpsd connection (if ENABLE_GPS and local GPS module)
    - `on_position_received(node_id: str, lat: float, lon: float, alt: float = None) -> None`:
      - Update `nodes` table with new position
      - Publish to MQTT `lora-hub/mesh/position/{node_id}`
      - Emit SocketIO `node_position` event
      - Trigger geofence check if geofencing enabled
    - `get_all_positions() -> list[dict]`:
      - Return all nodes with latest lat/lon/alt
    - `get_node_track(node_id: str, limit: int = 100) -> list[dict]`:
      - Return position history for one node (requires position log table or reuse nodes.updated_at)
    - `get_local_position() -> dict | None`:
      - Read from gpsd if local GPS module attached
      - Return `{lat, lon, alt}` or None

- [ ] **Step 3.3 — Geofencing Engine**
  - [ ] Create `src/geofence.py` with `GeofenceEngine` class:
    - `__init__(config, db, mqtt_bridge)`:
      - Load active geofences from database
      - Track node in/out state for each fence
    - `add_geofence(name: str, lat: float, lon: float, radius_m: float, node_id: str = None) -> int`:
      - Insert into `geofences` table
      - Return geofence ID
    - `remove_geofence(geofence_id: int) -> bool`:
      - Delete from `geofences` table
    - `check_position(node_id: str, lat: float, lon: float) -> list[Alert]`:
      - For each active geofence (matching node_id or global):
        - Calculate Haversine distance from center
        - Compare to radius
        - Detect state change (was inside → now outside = exit; vice versa)
        - Create Alert for enter/exit events
      - Publish alerts to MQTT `lora-hub/alerts/geofence_{enter|exit}`
      - Emit SocketIO `geofence_alert` event
      - Return list of triggered alerts
    - `haversine(lat1, lon1, lat2, lon2) -> float`:
      - Calculate great-circle distance in meters
    - `list_geofences() -> list[dict]`:
      - Return all configured geofences
  - [ ] Toggle via `ENABLE_GEOFENCING`

- [ ] **Step 3.4 — Emergency Alert Broadcast**
  - [ ] Create `src/emergency.py` with `EmergencyBroadcast` class:
    - `__init__(config, db, mesh_controller, mqtt_bridge)`:
      - Store references
    - `send_alert(message: str, alert_type: str = 'custom') -> bool`:
      - Validate alert_type: `sos`, `weather`, `evacuation`, `custom`
      - Send via mesh controller with priority flag (`send_priority()`)
      - Store in `messages` table with `is_emergency=1`
      - Create `Alert` record with `alert_type='emergency'`, severity='critical'
      - Publish to MQTT `lora-hub/alerts/emergency`
      - Emit SocketIO `emergency_alert` event
      - Return success
    - `get_history(limit: int = 20) -> list[dict]`:
      - Return past emergency messages with timestamps and types

- [ ] **Step 3.5 — Phase 3 Tests**
  - [ ] `tests/test_chat.py`:
    - Test send_message (store, MQTT publish, mesh send)
    - Test on_message_received (store, node resolution, SocketIO emit)
    - Test get_history (pagination, channel filter)
  - [ ] `tests/test_gps.py`:
    - Test on_position_received (node update, MQTT publish)
    - Test get_all_positions (multiple nodes)
    - Test get_node_track (history query)
  - [ ] `tests/test_geofence.py`:
    - Test add/remove geofence
    - Test Haversine calculation (known distances)
    - Test check_position inside fence (no alert)
    - Test check_position outside fence (exit alert)
    - Test state transition detection (enter ↔ exit)
    - Test global vs per-node geofences
  - [ ] `tests/test_emergency.py`:
    - Test send_alert (mesh priority send, alert creation, MQTT publish)
    - Test alert type validation (valid types, invalid type rejection)
    - Test get_history

**Checkpoint:** Meshtastic web chat sends/receives messages with history. GPS positions update node map data. Geofencing detects enter/exit with Haversine math. Emergency broadcast sends priority alerts to all mesh nodes. All events publish to MQTT and emit SocketIO.

---

## Phase 4 — Web Dashboard & Authentication

**Goal:** Build the authenticated dark-themed dashboard with mode selector, sensor charts, chat, map, and emergency panels.

- [ ] **Step 4.1 — Flask App Factory**
  - [ ] Create `src/app.py`:
    - `create_app(config)` factory pattern
    - Initialize Flask-SocketIO with eventlet mode
    - Register route handlers
    - Initialize database on startup
    - Create mode manager, gateway, mesh, chirpstack, sensors, chat, GPS, geofence, emergency, power, MQTT instances
    - Wire dependencies between components
    - Start mode manager (activates initial LORA_MODE)
    - Implement `__main__` block to run the app
    - Bind to `DASHBOARD_HOST:DASHBOARD_PORT`
  - [ ] Toggle dashboard via `ENABLE_WEB_DASHBOARD`

- [ ] **Step 4.2 — Authentication Module**
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

- [ ] **Step 4.3 — Dark Theme Templates & CSS**
  - [ ] Create `templates/base.html`:
    - HTML5 boilerplate with dark background (`#1a1a2e`)
    - Navigation bar (app title, mode indicator badge, active tab highlight, logout)
    - Tab navigation: Dashboard, Sensors, Chat, Map, Emergency, Power, Settings
    - Content block, script block
    - SocketIO client script
  - [ ] Create `static/css/style.css`:
    - Dark palette: background `#1a1a2e`, cards `#16213e`, text `#e0e0e0`, accent `#0f3460`
    - Mode badges: Gateway (green), Mesh (blue), Both (purple)
    - Status badges: online (green pulse), offline (gray), alert (red), warning (yellow)
    - Chart container styling, map container (full-width)
    - Chat message bubbles (inbound left, outbound right)
    - Emergency alert styling (red border, pulsing icon)
    - Table styling, responsive grid, form inputs
    - Gauge displays for power readings

- [ ] **Step 4.4 — Login Page**
  - [ ] Create `templates/login.html` extending base
  - [ ] Centered login card with username/password fields
  - [ ] CSRF token hidden field
  - [ ] Flash message area for errors ("Invalid credentials", "Rate limited")
  - [ ] Hub status indicator at bottom (mode, uptime)

- [ ] **Step 4.5 — Main Dashboard Page**
  - [ ] Create `templates/dashboard.html` extending base
  - [ ] Mode selector: three radio buttons (Gateway / Mesh / Both) with "Apply" button
  - [ ] Confirmation modal on mode switch ("Switch to {mode}? Active connections may reset.")
  - [ ] Summary cards: Active Mode, LoRaWAN Devices, Mesh Nodes, Active Alerts
  - [ ] Component health indicators: Concentrator, Meshtastic Radio, MQTT, ChirpStack (green/red dots)
  - [ ] Recent activity feed (last 10 events: uplinks, messages, alerts)

- [ ] **Step 4.6 — Sensor Dashboard Page**
  - [ ] Create `templates/sensors.html` extending base
  - [ ] Device list table: name, EUI, last seen, RSSI, SNR, battery
  - [ ] Chart.js line graphs for selected sensor type
  - [ ] Sensor type dropdown: temperature, humidity, soil_moisture, pressure, etc.
  - [ ] Device selector dropdown
  - [ ] Time range buttons: 1h, 6h, 24h, 7d, custom date range
  - [ ] Alert indicator badges on devices exceeding thresholds
  - [ ] CSV export button (download link)
  - [ ] SocketIO real-time chart point injection

- [ ] **Step 4.7 — Meshtastic Chat Page**
  - [ ] Create `templates/chat.html` extending base
  - [ ] Chat message list: sender (with icon), timestamp, content
  - [ ] Emergency messages highlighted with red border
  - [ ] Message input: text field + send button
  - [ ] Channel dropdown selector
  - [ ] Destination dropdown: Broadcast, or specific node names
  - [ ] Node online status indicators next to names
  - [ ] SocketIO real-time message delivery (append to list, scroll to bottom)

- [ ] **Step 4.8 — GPS Node Map Page**
  - [ ] Create `templates/map.html` extending base
  - [ ] Leaflet.js map with OpenStreetMap tiles
  - [ ] Node markers: icon with node name popup (name, battery, last heard, snr)
  - [ ] Color-coded markers: online (green), offline (gray), emergency (red)
  - [ ] Geofence zones: dashed circle overlay with name label
  - [ ] Auto-fit bounds to show all nodes
  - [ ] SocketIO real-time marker position updates
  - [ ] Geofence management: add zone (click center, set radius), delete zone

- [ ] **Step 4.9 — Emergency Alert Page**
  - [ ] Create `templates/emergency.html` extending base
  - [ ] Alert composer: message text area, type selector (SOS, Weather, Evacuation, Custom)
  - [ ] Large red "BROADCAST" button
  - [ ] Confirmation modal: "This will send a priority alert to ALL mesh nodes. Confirm?"
  - [ ] Alert history table: timestamp, type, message, delivery status
  - [ ] Total alerts sent counter

- [ ] **Step 4.10 — Settings Panel**
  - [ ] Create `templates/settings.html` extending base
  - [ ] Current mode display with switch controls (same as dashboard)
  - [ ] Feature toggles display (read-only, showing current `.env` state)
  - [ ] Concentrator info: model, region, channels, running status
  - [ ] Meshtastic info: device path, channel, node count, connected status
  - [ ] MQTT info: broker host:port, connected status, topics active
  - [ ] ChirpStack info: API URL, reachable status, device count
  - [ ] Power monitoring info: sensor address, threshold, readings (if enabled)
  - [ ] GPS info: gpsd status, local position (if enabled)

- [ ] **Step 4.11 — SocketIO Real-time Events**
  - [ ] Server emits:
    - `mode_changed` — `{mode, gateway_active, mesh_active}`
    - `sensor_data` — `{device_id, sensor_type, value, unit, timestamp}`
    - `sensor_alert` — `{device_id, sensor_type, value, threshold, severity}`
    - `chat_message` — `{node_id, node_name, channel, content, direction, timestamp}`
    - `node_position` — `{node_id, node_name, lat, lon, alt, battery}`
    - `geofence_alert` — `{node_id, geofence_name, event_type, distance}`
    - `emergency_alert` — `{message, alert_type, timestamp}`
    - `power_update` — `{voltage, current_ma, power_mw, source}`
  - [ ] Create `static/js/dashboard.js` — mode selector, summary cards, health indicators
  - [ ] Create `static/js/sensors.js` — Chart.js init, real-time point injection, time range
  - [ ] Create `static/js/chat.js` — message list, send handler, real-time append
  - [ ] Create `static/js/map.js` — Leaflet init, markers, geofence circles, position updates
  - [ ] Create `static/js/emergency.js` — alert form, confirmation modal, history

- [ ] **Step 4.12 — Phase 4 Tests**
  - [ ] `tests/test_auth.py` — login, logout, invalid creds, rate limiting, session expiry
  - [ ] `tests/test_api.py`:
    - Dashboard route (auth required, data populated)
    - Mode switch endpoint (`POST /api/mode` with mode parameter)
    - Sensor data endpoint (`GET /api/sensors/{device_id}`)
    - Chat send endpoint (`POST /api/chat/send`)
    - Chat history endpoint (`GET /api/chat/{channel}`)
    - Emergency broadcast endpoint (`POST /api/emergency`)
    - Geofence CRUD endpoints
    - Settings retrieval endpoint
  - [ ] Test SocketIO event emission for each event type
  - [ ] Test CSRF protection on all POST routes

**Checkpoint:** Fully functional dark-themed dashboard with mode selector, sensor charts, Meshtastic chat, GPS map, emergency broadcast, and settings panel. All protected by bcrypt auth with rate limiting. SocketIO delivers real-time updates for all data streams.

---

## Phase 5 — Power Monitoring & Advanced Features

**Goal:** Add solar power monitoring, sensor data export, MQTT TLS, and final feature polish.

- [ ] **Step 5.1 — Power Monitoring**
  - [ ] Create `src/power.py` with `PowerMonitor` class:
    - `__init__(config, db, mqtt_bridge)`:
      - Store I2C address, alert threshold
      - Initialize smbus2 connection to INA219/INA260
    - `read_voltage() -> float`:
      - Read bus voltage from I2C register
      - Return voltage in volts
    - `read_current() -> float`:
      - Read current from I2C register
      - Return current in mA
    - `read_power() -> float`:
      - Read power from I2C register (or compute V × I)
      - Return power in mW
    - `read_all() -> dict`:
      - Return `{voltage, current_ma, power_mw, source}`
    - `start_logging(interval_sec: int = 60) -> None`:
      - Start background thread: periodically read + store in `power_logs`
      - Publish to MQTT `lora-hub/power/{metric}`
      - Emit SocketIO `power_update`
      - Check low voltage threshold
    - `stop_logging() -> None`:
      - Stop background thread
    - `check_low_voltage(voltage: float) -> Alert | None`:
      - If voltage < `POWER_LOW_THRESHOLD_V`: create alert, publish, emit
  - [ ] Toggle via `ENABLE_POWER_MONITORING`

- [ ] **Step 5.2 — Power Monitoring Page**
  - [ ] Create `templates/power.html` extending base
  - [ ] Three gauge displays: Voltage (V), Current (mA), Power (mW)
  - [ ] Historical power Chart.js line graph
  - [ ] Time range selector
  - [ ] Low voltage alert indicator (red if below threshold)
  - [ ] Source indicator badge (battery / solar / USB)
  - [ ] SocketIO real-time gauge updates

- [ ] **Step 5.3 — Sensor Data CSV Export**
  - [ ] Implement `export_csv()` in `SensorManager` (if not already done in Step 2.2)
  - [ ] Add route `GET /api/sensors/export?device_id=&type=&start=&end=`
  - [ ] Stream CSV response with proper headers (`Content-Type: text/csv`)
  - [ ] CSV columns: timestamp, device_name, device_eui, sensor_type, value, unit
  - [ ] Limit maximum export range to prevent memory issues

- [ ] **Step 5.4 — MQTT TLS Configuration**
  - [ ] Add `.env` variables: `MQTT_TLS_CA_CERT`, `MQTT_TLS_CLIENT_CERT`, `MQTT_TLS_CLIENT_KEY`
  - [ ] In `MQTTBridge.connect()`: if TLS certs configured, call `client.tls_set()`
  - [ ] Auto-detect TLS when `MQTT_BROKER_PORT=8883`
  - [ ] Document Mosquitto TLS setup in `docs/mqtt_topics.md`

- [ ] **Step 5.5 — Phase 5 Tests**
  - [ ] `tests/test_power.py`:
    - Test read_voltage, read_current, read_power (mocked I2C/smbus2)
    - Test start_logging / stop_logging (background thread)
    - Test check_low_voltage (below threshold → alert, above → no alert)
    - Test power_logs DB insertion
  - [ ] Test CSV export endpoint (format, headers, streaming)
  - [ ] Test MQTT TLS configuration (mocked tls_set call)

**Checkpoint:** Power monitoring reads INA219/INA260 via I2C, logs history, and alerts on low voltage. Sensor data exportable as CSV. MQTT supports TLS for external clients.

---

## Phase 6 — Deployment & Documentation

**Goal:** Finalize deploy pipeline, setup scripts, and all documentation.

- [ ] **Step 6.1 — Deploy Script**
  - [ ] Create `deploy/deploy_to_pi.sh`:
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    PI_HOST="rasp-pi"
    REMOTE_DIR="/home/pi/lora-hub"
    echo "[*] Deploying to ${PI_HOST}:${REMOTE_DIR}"
    rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
        --exclude '.git' --exclude 'data/' \
        ./ "${PI_HOST}:${REMOTE_DIR}/"
    ssh "${PI_HOST}" "cd ${REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt"
    echo "[✓] Deploy complete."
    ```

- [ ] **Step 6.2 — OS Dependency Installer**
  - [ ] Create `scripts/install_deps.sh`:
    - Install `python3-venv`, `python3-dev`, `python3-pip`
    - Install `libgps-dev` (for gpsd-py3)
    - Install `i2c-tools` (for power monitoring)
    - Install Docker & Docker Compose
    - Install Mosquitto (`mosquitto`, `mosquitto-clients`)
    - Enable SPI (`raspi-config` nonint)
    - Enable I2C (`raspi-config` nonint)
    - Print success message

- [ ] **Step 6.3 — ChirpStack Docker Setup Script**
  - [ ] Create `scripts/setup_chirpstack.sh`:
    - Clone/download ChirpStack Docker repo
    - Configure `docker-compose.yml` for arm64
    - Set regional config for concentrator
    - Run `docker compose up -d`
    - Wait for health checks
    - Print ChirpStack web UI URL and default credentials

- [ ] **Step 6.4 — Mosquitto Configuration Script**
  - [ ] Create `scripts/setup_mosquitto.sh`:
    - Configure `mosquitto.conf` (listener, auth, ACLs)
    - Create password file with `mosquitto_passwd`
    - Restart Mosquitto service
    - Test connectivity with `mosquitto_pub` / `mosquitto_sub`

- [ ] **Step 6.5 — Password Hash Helper**
  - [ ] Create `scripts/generate_password_hash.sh`:
    - Read password securely (no echo)
    - Generate bcrypt hash via Python one-liner
    - Print hash for `.env`

- [ ] **Step 6.6 — Mode Switching Guide**
  - [ ] Create `docs/mode_switching.md`:
    - Dual-mode architecture explanation with diagram
    - Dashboard mode switching walkthrough (screenshots placeholder)
    - `.env` `LORA_MODE` configuration
    - Hardware requirements per mode
    - Both mode: separate Meshtastic USB radio + concentrator HAT
    - Troubleshooting mode conflicts and hardware contention

- [ ] **Step 6.7 — ChirpStack Setup Guide**
  - [ ] Create `docs/chirpstack_setup.md`:
    - Docker prerequisites (install, compose)
    - Step-by-step ChirpStack v4 deployment
    - Gateway bridge configuration for RAK2287/5146
    - Creating application, device profile, and device (OTAA)
    - Payload decoder examples (CayenneLPP, custom)
    - Verifying uplinks in ChirpStack web UI

- [ ] **Step 6.8 — Antenna Guide**
  - [ ] Create `docs/antenna_guide.md`:
    - Frequency band selection by country (EU868, US915, etc.)
    - Antenna types: omnidirectional, directional, fiberglass
    - Gain and radiation patterns
    - Mounting height and line-of-sight considerations
    - Cable types and loss per meter (LMR-195, LMR-400)
    - Safety: always attach antenna before powering concentrator

- [ ] **Step 6.9 — MQTT Topics Documentation**
  - [ ] Create `docs/mqtt_topics.md`:
    - Full topic hierarchy with JSON payload schemas
    - Gateway topics (`rx`, `tx`) with example payloads
    - Mesh topics (`chat`, `position`) with example payloads
    - Alert topics with severity levels
    - Power topics with units
    - Home Assistant MQTT discovery config examples
    - Node-RED flow import examples
    - QoS levels and message retention policies

- [ ] **Step 6.10 — Final Integration Testing**
  - [ ] Test gateway mode end-to-end: LoRaWAN sensor → ChirpStack → sensor dashboard
  - [ ] Test mesh mode end-to-end: Meshtastic node → web chat → MQTT
  - [ ] Test both mode: simultaneous gateway and mesh
  - [ ] Test live mode switching: gateway → mesh → both → gateway
  - [ ] Test emergency broadcast: compose → confirm → mesh delivery
  - [ ] Test geofencing: node moves outside radius → alert
  - [ ] Test power monitoring: voltage readings → chart → low voltage alert
  - [ ] Test MQTT topics: subscribe externally, verify payloads
  - [ ] Test authentication: login, rate limiting, session expiry
  - [ ] Test mock mode: full dashboard with simulated data

- [ ] **Step 6.11 — Update README**
  - [ ] Finalize quickstart instructions with tested commands
  - [ ] Add screenshots of dashboard (mode selector, sensor charts, chat, map, emergency, power)
  - [ ] Verify all feature descriptions match implementation
  - [ ] Update troubleshooting table with real-world issues found during testing
