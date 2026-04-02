# Task List — LoRa Gateway & Mesh Communication Hub

## Phase 1 — Project Foundation & Dual-Mode Engine

- [ ] **1.1 Initialize project structure**
  - [ ] Create directory tree (`src/`, `templates/`, `static/css/`, `static/js/`, `tests/`, `deploy/`, `scripts/`, `docs/`, `data/`)
  - [ ] Create `pyproject.toml` with project metadata
  - [ ] Create `requirements.txt` with all dependencies
  - [ ] Create `.env.example` with all variables and defaults
  - [ ] Create `src/__init__.py`
  - [ ] Create `tests/__init__.py` and `tests/conftest.py`

- [ ] **1.2 Implement configuration loader**
  - [ ] Create `src/config.py` with dataclass for all `.env` variables
  - [ ] Load and validate `.env` using `python-dotenv`
  - [ ] Type conversion for int, float, bool values
  - [ ] Parse `LORA_MODE` into enum (`gateway`, `mesh`, `both`)
  - [ ] Parse `SENSOR_ALERT_THRESHOLD` JSON string into dict
  - [ ] Parse `POWER_I2C_ADDRESS` hex string to int
  - [ ] Defaults for all optional settings
  - [ ] Feature-toggle helper method (`is_enabled("feature_name")`)

- [ ] **1.3 Implement SQLite database module**
  - [ ] Create `src/database.py` with connection manager
  - [ ] Enable WAL mode on connection
  - [ ] Create `devices` table schema
  - [ ] Create `sensor_data` table schema
  - [ ] Create `messages` table schema
  - [ ] Create `nodes` table schema
  - [ ] Create `alerts` table schema
  - [ ] Create `geofences` table schema
  - [ ] Create `power_logs` table schema
  - [ ] Create `settings` table schema
  - [ ] Implement `init_db()` to create all tables
  - [ ] Implement CRUD helpers for each table
  - [ ] Implement parameterized queries for all DB operations

- [ ] **1.4 Implement mode manager**
  - [ ] Create `src/mode_manager.py`
  - [ ] Implement `ModeManager` class with current mode state
  - [ ] Implement `start_mode(mode)` — activate gateway, mesh, or both
  - [ ] Implement `stop_mode()` — gracefully stop active mode(s)
  - [ ] Implement `switch_mode(new_mode)` — stop current, start new (live switching)
  - [ ] Implement `get_status()` — return active mode(s) and component health
  - [ ] Thread-safe mode transitions with locking
  - [ ] Emit SocketIO events on mode change
  - [ ] Read initial mode from `LORA_MODE` env variable

- [ ] **1.5 Implement LoRaWAN gateway engine**
  - [ ] Create `src/gateway.py`
  - [ ] Implement `GatewayEngine` class
  - [ ] Implement `start()` — initialize concentrator HAT, start packet forwarder
  - [ ] Implement `stop()` — gracefully stop packet forwarder
  - [ ] Implement `get_status()` — concentrator state, uplink/downlink counts
  - [ ] Interface with ChirpStack concentratord or UDP packet forwarder
  - [ ] Configure regional frequency plan from `LORA_REGION`
  - [ ] Support RAK2287 and RAK5146 concentrator models
  - [ ] Toggle via `LORA_MODE` containing `gateway`

- [ ] **1.6 Implement Meshtastic mesh controller**
  - [ ] Create `src/mesh.py`
  - [ ] Implement `MeshController` class
  - [ ] Implement `start()` — connect to Meshtastic radio via serial
  - [ ] Implement `stop()` — disconnect cleanly
  - [ ] Implement `send_text(text, channel, destination)` — send mesh message
  - [ ] Implement `on_receive(callback)` — register message receive handler
  - [ ] Implement `get_nodes()` — list known mesh nodes
  - [ ] Implement `get_node_info(node_id)` — detailed node information
  - [ ] Implement `get_status()` — radio connection state, channel info
  - [ ] Configure serial device from `MESHTASTIC_DEVICE`
  - [ ] Toggle via `LORA_MODE` containing `mesh`

- [ ] **1.7 Implement mock mode**
  - [ ] Add mock gateway class (simulates uplinks from fake sensors)
  - [ ] Add mock mesh controller (simulates message receive/send)
  - [ ] Add mock MQTT client (logs instead of publishing)
  - [ ] Add mock power sensor (returns randomized readings)
  - [ ] Add mock GPS (returns static test coordinates)
  - [ ] Activate via `MOCK_MODE=true` in config
  - [ ] Allow full dashboard testing without hardware

- [ ] **1.8 Write Phase 1 tests**
  - [ ] Test config loader (valid `.env`, missing values, type conversion, LORA_MODE parsing)
  - [ ] Test database schema creation and CRUD operations for all 8 tables
  - [ ] Test mode manager (start/stop/switch, concurrent access, status reporting)
  - [ ] Test gateway engine (start/stop, status, mocked concentrator)
  - [ ] Test mesh controller (connect/disconnect, send/receive, mocked serial)
  - [ ] Test mock mode activation and output

---

## Phase 2 — ChirpStack Integration & Sensor Dashboard

- [ ] **2.1 Implement ChirpStack API client**
  - [ ] Create `src/chirpstack.py`
  - [ ] Implement `ChirpStackClient` class
  - [ ] Implement `connect(api_url, api_key)` — establish gRPC/REST connection
  - [ ] Implement `list_devices()` — fetch all registered LoRaWAN devices
  - [ ] Implement `get_device(dev_eui)` — fetch device details and activation status
  - [ ] Implement `get_device_events(dev_eui, limit)` — fetch recent uplink events
  - [ ] Implement `enqueue_downlink(dev_eui, payload, port)` — schedule downlink
  - [ ] Implement `subscribe_events(callback)` — stream uplink events in real time
  - [ ] Handle API authentication and error responses
  - [ ] Toggle via `ENABLE_CHIRPSTACK`

- [ ] **2.2 Implement sensor data ingestion**
  - [ ] Create `src/sensors.py`
  - [ ] Implement `SensorManager` class
  - [ ] Implement `process_uplink(event)` — decode payload, extract sensor readings
  - [ ] Implement `store_reading(device_id, sensor_type, value, unit)` — write to `sensor_data`
  - [ ] Implement `get_latest(device_id, sensor_type)` — last N readings
  - [ ] Implement `get_history(device_id, sensor_type, start, end)` — time-range query
  - [ ] Support common payload formats (CayenneLPP, custom JSON, raw hex)
  - [ ] Update `devices` table on each uplink (last_seen, rssi, snr)

- [ ] **2.3 Implement sensor threshold alerting**
  - [ ] Implement `check_thresholds(reading)` — compare against `SENSOR_ALERT_THRESHOLD`
  - [ ] Create alert record in `alerts` table when threshold exceeded
  - [ ] Emit SocketIO `sensor_alert` event to dashboard
  - [ ] Publish alert to MQTT topic `lora-hub/alerts/sensor_threshold`
  - [ ] Configurable per sensor type from `.env` JSON map
  - [ ] Toggle via `ENABLE_SENSOR_DASHBOARD`

- [ ] **2.4 Implement MQTT bridge**
  - [ ] Create `src/mqtt_bridge.py`
  - [ ] Implement `MQTTBridge` class using `paho-mqtt`
  - [ ] Implement `connect()` — connect to Mosquitto with optional auth
  - [ ] Implement `publish(topic, payload)` — publish message to MQTT topic
  - [ ] Implement `subscribe(topic, callback)` — subscribe to MQTT topic
  - [ ] Implement topic hierarchy:
    - `lora-hub/gateway/{dev_eui}/rx` — sensor uplinks
    - `lora-hub/gateway/{dev_eui}/tx` — downlinks
    - `lora-hub/mesh/chat/{channel}` — mesh messages
    - `lora-hub/mesh/position/{node_id}` — GPS positions
    - `lora-hub/alerts/{type}` — alerts
    - `lora-hub/power/{metric}` — power readings
  - [ ] Configurable topic prefix from `MQTT_TOPIC_PREFIX`
  - [ ] Handle reconnection on broker disconnect
  - [ ] Toggle via `ENABLE_MQTT_BRIDGE`

- [ ] **2.5 Write Phase 2 tests**
  - [ ] Test ChirpStack client (list devices, get events, enqueue downlink, mocked API)
  - [ ] Test sensor ingestion (decode uplink, store reading, query history)
  - [ ] Test threshold alerting (within range, exceeded, alert creation)
  - [ ] Test MQTT bridge (connect, publish, subscribe, topic hierarchy)
  - [ ] Test reconnection behavior on MQTT disconnect

---

## Phase 3 — Meshtastic Chat, GPS & Emergency

- [ ] **3.1 Implement chat message handler**
  - [ ] Create `src/chat.py`
  - [ ] Implement `ChatHandler` class
  - [ ] Implement `send_message(text, channel, destination)` — send via mesh controller
  - [ ] Implement `on_message_received(packet)` — process incoming mesh text
  - [ ] Implement `store_message(node_id, content, direction, channel)` — write to `messages`
  - [ ] Implement `get_history(channel, limit, offset)` — paginated message history
  - [ ] Resolve node names from `nodes` table
  - [ ] Publish to MQTT topic `lora-hub/mesh/chat/{channel}`
  - [ ] Emit SocketIO `chat_message` event to web clients
  - [ ] Toggle via `ENABLE_WEB_CHAT`

- [ ] **3.2 Implement GPS position tracker**
  - [ ] Create `src/gps.py`
  - [ ] Implement `GPSTracker` class
  - [ ] Implement `on_position_received(node_id, lat, lon, alt)` — update node position
  - [ ] Implement `update_node(node_id, position_data)` — write to `nodes` table
  - [ ] Implement `get_all_positions()` — return all nodes with latest lat/lon
  - [ ] Implement `get_node_track(node_id, limit)` — position history for one node
  - [ ] Integrate with gpsd for local GPS receiver (optional hub GPS)
  - [ ] Publish positions to MQTT topic `lora-hub/mesh/position/{node_id}`
  - [ ] Emit SocketIO `node_position` event for map updates
  - [ ] Toggle via `ENABLE_GPS`

- [ ] **3.3 Implement geofencing engine**
  - [ ] Create `src/geofence.py`
  - [ ] Implement `GeofenceEngine` class
  - [ ] Implement `add_geofence(name, lat, lon, radius_m, node_id)` — create zone
  - [ ] Implement `remove_geofence(geofence_id)` — delete zone
  - [ ] Implement `check_position(node_id, lat, lon)` — test against all active fences
  - [ ] Implement Haversine distance calculation for boundary check
  - [ ] Create alert on enter/exit events
  - [ ] Publish geofence alerts to MQTT topic `lora-hub/alerts/geofence_{enter|exit}`
  - [ ] Emit SocketIO `geofence_alert` event
  - [ ] Toggle via `ENABLE_GEOFENCING`

- [ ] **3.4 Implement emergency alert broadcast**
  - [ ] Create `src/emergency.py`
  - [ ] Implement `EmergencyBroadcast` class
  - [ ] Implement `send_alert(message, alert_type)` — broadcast priority message on mesh
  - [ ] Implement `get_alert_history(limit)` — list past emergency alerts
  - [ ] Alert types: `sos`, `weather`, `evacuation`, `custom`
  - [ ] Set Meshtastic priority flag for immediate relay
  - [ ] Store emergency messages in `messages` table with `is_emergency=1`
  - [ ] Create alert record in `alerts` table
  - [ ] Publish to MQTT topic `lora-hub/alerts/emergency`
  - [ ] Emit SocketIO `emergency_alert` event
  - [ ] Toggle via `ENABLE_EMERGENCY_ALERTS`

- [ ] **3.5 Write Phase 3 tests**
  - [ ] Test chat handler (send, receive, store, history query)
  - [ ] Test GPS tracker (position update, node track, get all positions)
  - [ ] Test geofencing (add zone, check inside, check outside, enter/exit alerts)
  - [ ] Test Haversine distance calculation accuracy
  - [ ] Test emergency broadcast (send, store, alert creation)
  - [ ] Test MQTT publishing for chat, GPS, geofence, emergency topics

---

## Phase 4 — Web Dashboard & Authentication

- [ ] **4.1 Implement Flask app factory**
  - [ ] Create `src/app.py` with `create_app()` factory
  - [ ] Initialize Flask-SocketIO with eventlet
  - [ ] Register blueprints/routes
  - [ ] Integrate config and database initialization
  - [ ] Initialize mode manager on startup
  - [ ] Implement `__main__` entry point
  - [ ] Bind to `DASHBOARD_HOST:DASHBOARD_PORT`

- [ ] **4.2 Implement authentication**
  - [ ] Create `src/auth.py`
  - [ ] Implement bcrypt password verification
  - [ ] Implement login route (`POST /login`)
  - [ ] Implement logout route (`POST /logout`)
  - [ ] Implement rate limiting (10 attempts per 15 minutes per IP)
  - [ ] Implement session with 24-hour expiry
  - [ ] Implement `@login_required` decorator for all protected routes
  - [ ] Read `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` from config

- [ ] **4.3 Create dark theme templates and CSS**
  - [ ] Create `templates/base.html` with dark theme layout
  - [ ] Create `static/css/style.css` with dark color scheme
  - [ ] Responsive layout with tab navigation
  - [ ] Navigation bar with mode indicator, active tab highlight, logout button

- [ ] **4.4 Build login page**
  - [ ] Create `templates/login.html`
  - [ ] Username and password form with CSRF token
  - [ ] Error message display for failed login
  - [ ] Rate limit warning display

- [ ] **4.5 Build main dashboard page**
  - [ ] Create `templates/dashboard.html`
  - [ ] Mode selector: Gateway | Mesh | Both (radio buttons + Apply)
  - [ ] Summary cards: Active Mode, Devices Online, Mesh Nodes, Alerts
  - [ ] Component health indicators (concentrator, radio, MQTT, ChirpStack)
  - [ ] Quick links to sensor, chat, map, emergency tabs

- [ ] **4.6 Build sensor dashboard page**
  - [ ] Create `templates/sensors.html`
  - [ ] Device list with last seen, RSSI, SNR, battery
  - [ ] Chart.js line graphs for sensor data (time-series)
  - [ ] Sensor type selector (temperature, humidity, etc.)
  - [ ] Time range selector (1h, 6h, 24h, 7d, custom)
  - [ ] Alert indicator badges on threshold breaches
  - [ ] CSV export button

- [ ] **4.7 Build Meshtastic chat page**
  - [ ] Create `templates/chat.html`
  - [ ] Chat message list with sender name, timestamp, content
  - [ ] Message input form with send button
  - [ ] Channel selector dropdown
  - [ ] Destination selector (broadcast or specific node)
  - [ ] Emergency message toggle (checkbox)
  - [ ] Real-time message delivery via SocketIO

- [ ] **4.8 Build GPS node map page**
  - [ ] Create `templates/map.html`
  - [ ] Leaflet.js map with tile layer
  - [ ] Node markers with popup (name, battery, last heard)
  - [ ] Geofence zone circles overlay
  - [ ] Auto-center on known nodes
  - [ ] Real-time position updates via SocketIO

- [ ] **4.9 Build emergency alert page**
  - [ ] Create `templates/emergency.html`
  - [ ] Alert composer form (message, type selector, confirm button)
  - [ ] Confirmation modal before broadcast ("This will alert ALL mesh nodes")
  - [ ] Alert history table (past broadcasts with timestamps and types)
  - [ ] Status indicator for last broadcast delivery

- [ ] **4.10 Build settings panel**
  - [ ] Create `templates/settings.html`
  - [ ] Active mode display with switch controls
  - [ ] Feature toggle display (read-only from `.env`)
  - [ ] Concentrator status (model, region, channels)
  - [ ] Meshtastic radio status (device, channel, node count)
  - [ ] MQTT broker status (connected/disconnected)
  - [ ] ChirpStack status (API reachable, device count)
  - [ ] Power monitoring status (if enabled)

- [ ] **4.11 Implement SocketIO real-time events**
  - [ ] Emit `mode_changed` event (new mode, component status)
  - [ ] Emit `sensor_data` event (new reading for chart update)
  - [ ] Emit `sensor_alert` event (threshold breach)
  - [ ] Emit `chat_message` event (new mesh message)
  - [ ] Emit `node_position` event (GPS update for map)
  - [ ] Emit `geofence_alert` event (enter/exit)
  - [ ] Emit `emergency_alert` event (broadcast sent/received)
  - [ ] Emit `power_update` event (voltage/current reading)
  - [ ] Client-side handlers in `static/js/dashboard.js`
  - [ ] Create `static/js/sensors.js` for chart updates
  - [ ] Create `static/js/chat.js` for message delivery
  - [ ] Create `static/js/map.js` for position updates
  - [ ] Create `static/js/emergency.js` for alert UI

- [ ] **4.12 Write Phase 4 tests**
  - [ ] Test login (valid credentials, invalid credentials, rate limiting)
  - [ ] Test session expiry (24-hour window)
  - [ ] Test protected route access (authenticated vs unauthenticated)
  - [ ] Test mode switching API endpoint
  - [ ] Test sensor data API endpoints
  - [ ] Test chat send/receive API endpoints
  - [ ] Test emergency broadcast API endpoint
  - [ ] Test SocketIO event emission
  - [ ] Test CSRF protection on forms

---

## Phase 5 — Power Monitoring & Advanced Features

- [ ] **5.1 Implement power monitoring**
  - [ ] Create `src/power.py`
  - [ ] Implement `PowerMonitor` class
  - [ ] Implement `read_voltage()` — read from INA219/INA260 via I2C
  - [ ] Implement `read_current()` — current draw in mA
  - [ ] Implement `read_power()` — power consumption in mW
  - [ ] Implement `start_logging(interval_sec)` — periodic readings to `power_logs`
  - [ ] Implement `check_low_voltage()` — alert if below `POWER_LOW_THRESHOLD_V`
  - [ ] Publish to MQTT topic `lora-hub/power/{voltage|current|power}`
  - [ ] Emit SocketIO `power_update` event
  - [ ] Toggle via `ENABLE_POWER_MONITORING`

- [ ] **5.2 Build power monitoring page**
  - [ ] Create `templates/power.html`
  - [ ] Voltage/current/power gauge displays
  - [ ] Historical power chart (Chart.js)
  - [ ] Low voltage alert indicator
  - [ ] Source indicator (battery/solar/USB)
  - [ ] Time range selector for history

- [ ] **5.3 Implement sensor data CSV export**
  - [ ] Implement `export_csv(device_id, sensor_type, start, end)` — generate CSV
  - [ ] Add export endpoint (`GET /api/sensors/export`)
  - [ ] Stream response for large datasets
  - [ ] Include headers: timestamp, device, sensor_type, value, unit

- [ ] **5.4 Implement MQTT TLS configuration**
  - [ ] Support TLS certificates in MQTT bridge
  - [ ] Configure CA cert, client cert, client key paths in `.env`
  - [ ] Auto-detect TLS when port is 8883
  - [ ] Document Mosquitto TLS setup

- [ ] **5.5 Write Phase 5 tests**
  - [ ] Test power monitoring (read voltage, current, power — mocked I2C)
  - [ ] Test low voltage alert (threshold check, alert creation)
  - [ ] Test power logging (periodic writes to `power_logs`)
  - [ ] Test CSV export (correct format, headers, data)
  - [ ] Test MQTT TLS connection (mocked)

---

## Phase 6 — Deployment & Documentation

- [ ] **6.1 Create deploy script**
  - [ ] Create `deploy/deploy_to_pi.sh`
  - [ ] rsync project to `rasp-pi` (pi@192.168.216.90)
  - [ ] Exclude `.venv`, `__pycache__`, `.git`, `data/`
  - [ ] Remote `pip install -r requirements.txt`

- [ ] **6.2 Create OS dependency installer**
  - [ ] Create `scripts/install_deps.sh`
  - [ ] Install `python3-venv`, `python3-dev`, `python3-pip`
  - [ ] Install `libgps-dev` (for gpsd-py3)
  - [ ] Install Docker & Docker Compose (for ChirpStack)
  - [ ] Install Mosquitto MQTT broker
  - [ ] Enable SPI interface (for concentrator HAT)
  - [ ] Enable I2C interface (for power monitoring)
  - [ ] Print success message

- [ ] **6.3 Create ChirpStack Docker setup script**
  - [ ] Create `scripts/setup_chirpstack.sh`
  - [ ] Download ChirpStack Docker Compose files
  - [ ] Configure for Pi architecture (arm64)
  - [ ] Set up PostgreSQL and Redis containers
  - [ ] Configure gateway bridge for concentrator
  - [ ] Start Docker stack and verify health

- [ ] **6.4 Create Mosquitto configuration script**
  - [ ] Create `scripts/setup_mosquitto.sh`
  - [ ] Configure listener on port 1883
  - [ ] Set up username/password authentication
  - [ ] Configure ACLs for topic access control
  - [ ] Optional TLS certificate generation
  - [ ] Restart Mosquitto and verify

- [ ] **6.5 Create password hash helper**
  - [ ] Create `scripts/generate_password_hash.sh`
  - [ ] Prompt for password (no echo)
  - [ ] Generate bcrypt hash using Python one-liner
  - [ ] Print hash for inclusion in `.env`

- [ ] **6.6 Write systemd service unit**
  - [ ] Create service file for documentation (in README)
  - [ ] Depend on `docker.service` and `mosquitto.service`
  - [ ] Restart on failure with backoff

- [ ] **6.7 Write mode switching guide**
  - [ ] Create `docs/mode_switching.md`
  - [ ] Explain dual-mode architecture
  - [ ] Dashboard mode switching walkthrough
  - [ ] `.env` mode configuration
  - [ ] Hardware requirements per mode
  - [ ] Troubleshooting mode conflicts

- [ ] **6.8 Write ChirpStack setup guide**
  - [ ] Create `docs/chirpstack_setup.md`
  - [ ] Docker installation prerequisites
  - [ ] Step-by-step ChirpStack deployment
  - [ ] Gateway bridge configuration
  - [ ] Adding first device (OTAA walkthrough)
  - [ ] Payload decoder examples

- [ ] **6.9 Write antenna guide**
  - [ ] Create `docs/antenna_guide.md`
  - [ ] Frequency band selection by country
  - [ ] Antenna types and gain patterns
  - [ ] Placement and mounting best practices
  - [ ] Cable loss considerations

- [ ] **6.10 Write MQTT topics documentation**
  - [ ] Create `docs/mqtt_topics.md`
  - [ ] Full topic hierarchy with payload schemas
  - [ ] Home Assistant integration examples
  - [ ] Node-RED flow examples
  - [ ] QoS levels and retention policies

- [ ] **6.11 Final integration testing**
  - [ ] Test full gateway mode: sensor uplink → ChirpStack → dashboard chart
  - [ ] Test full mesh mode: mesh message → web chat → MQTT
  - [ ] Test both mode: simultaneous gateway + mesh operation
  - [ ] Test live mode switching from dashboard
  - [ ] Test emergency broadcast delivery
  - [ ] Test geofencing alerts on node movement
  - [ ] Test power monitoring readings and alerts
  - [ ] Test MQTT topic publishing for all event types
  - [ ] Verify dashboard auth and rate limiting

- [ ] **6.12 Update README**
  - [ ] Finalize quickstart instructions
  - [ ] Add screenshots of dashboard (mode selector, sensor charts, chat, map)
  - [ ] Verify all feature descriptions match implementation
  - [ ] Update troubleshooting table with real-world issues found during testing
