# 🗺️ Implementation Plan — OPC-UA Industrial Gateway

---

## Phase 1: Project Setup & Authentication (Day 1)

### Step 1.1 — Initialize project
```bash
mkdir -p src/routes src/templates src/plugins static/css static/js data/nodered_flows config certs/trusted scripts deploy docs tests
python3 -m venv venv && source venv/bin/activate
```

### Step 1.2 — Core dependencies (`requirements.txt`)
```text
Flask==3.1.*
Flask-SocketIO==5.3.*
flask-limiter==3.5.*
flask-cors==4.0.*
PyJWT==2.9.*
bcrypt==4.2.*
python-dotenv==1.0.*
asyncua==1.1.*
RPi.GPIO==0.7.*
python-can==4.4.*
cantools==39.*
pyserial==3.5.*
pymodbus==3.7.*
cryptography==43.*
python-telegram-bot==21.*
slack-sdk==3.33.*
gunicorn==22.*
```

### Step 1.3 — Flask app skeleton (`src/app.py`)
```python
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='../static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
socketio = SocketIO(app, cors_allowed_origins="*")

from routes import auth_routes, opcua_routes, node_routes, mapping_routes
from routes import history_routes, alarm_routes, cert_routes
from routes import rest_proxy_routes, diag_routes, analytics_routes, settings_routes
app.register_blueprint(auth_routes.bp)
app.register_blueprint(opcua_routes.bp)
app.register_blueprint(node_routes.bp)
app.register_blueprint(mapping_routes.bp)
app.register_blueprint(history_routes.bp)
app.register_blueprint(alarm_routes.bp)
app.register_blueprint(cert_routes.bp)
app.register_blueprint(rest_proxy_routes.bp)
app.register_blueprint(diag_routes.bp)
app.register_blueprint(analytics_routes.bp)
app.register_blueprint(settings_routes.bp)

if __name__ == '__main__':
    socketio.run(app, host=os.getenv('HOST', '0.0.0.0'),
                 port=int(os.getenv('PORT', 5000)))
```

---

## Phase 2: OPC-UA Server Bootstrap (Day 1–2)

### Step 2.1 — OPC-UA server (`src/opcua_server.py`)
```python
import asyncio
from asyncua import Server, ua
import os

class OPCUAGatewayServer:
    def __init__(self):
        self.server = Server()
        self.endpoint = os.getenv('OPCUA_ENDPOINT',
                                  'opc.tcp://0.0.0.0:4840/ua/server')
        self.namespace_uri = os.getenv('OPCUA_NAMESPACE',
                                       'urn:raspberry:opcua:gateway')
        self.idx = None
        self.folders = {}

    async def init(self):
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name(
            os.getenv('OPCUA_SERVER_NAME', 'RaspberryPi OPC-UA Gateway'))

        # Register namespace
        self.idx = await self.server.register_namespace(self.namespace_uri)

        # Create base folder structure
        objects = self.server.nodes.objects
        self.folders['gpio'] = await objects.add_folder(self.idx, 'GPIO')
        self.folders['can'] = await objects.add_folder(self.idx, 'CAN')
        self.folders['serial'] = await objects.add_folder(self.idx, 'Serial')
        self.folders['modbus'] = await objects.add_folder(self.idx, 'Modbus')
        self.folders['custom'] = await objects.add_folder(self.idx, 'Custom')

        # Configure security (optional)
        if os.getenv('ENABLE_CERT_SECURITY', 'true').lower() == 'true':
            await self._setup_security()

    async def _setup_security(self):
        cert_path = os.getenv('OPCUA_CERT_PATH', 'certs/server_cert.pem')
        key_path = os.getenv('OPCUA_KEY_PATH', 'certs/server_key.pem')
        if os.path.exists(cert_path) and os.path.exists(key_path):
            await self.server.load_certificate(cert_path)
            await self.server.load_private_key(key_path)
            self.server.set_security_policy([
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt
            ])

    async def start(self):
        await self.server.start()

    async def stop(self):
        await self.server.stop()

    async def add_variable(self, folder_name, name, initial_value, data_type=None):
        """Add a variable node to a folder"""
        folder = self.folders.get(folder_name)
        if folder is None:
            raise ValueError(f"Unknown folder: {folder_name}")
        var = await folder.add_variable(self.idx, name, initial_value)
        await var.set_writable()
        return var

    async def update_variable(self, node, value):
        """Update variable value"""
        await node.write_value(value)
```

---

## Phase 3: GPIO Data Source Plugin (Day 2–3)

### Step 3.1 — Base plugin interface (`src/plugins/base_plugin.py`)
```python
from abc import ABC, abstractmethod

class DataSourcePlugin(ABC):
    def __init__(self, config, server):
        self.config = config
        self.server = server
        self.nodes = {}
        self.running = False

    @abstractmethod
    async def start(self):
        """Start polling/listening for data"""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the data source"""
        pass

    @abstractmethod
    def get_status(self) -> dict:
        """Return plugin status"""
        pass

    @abstractmethod
    def get_values(self) -> dict:
        """Return current values"""
        pass
```

### Step 3.2 — GPIO plugin (`src/plugins/gpio_plugin.py`)
```python
import asyncio
import json
import os
import RPi.GPIO as GPIO
from .base_plugin import DataSourcePlugin

class GPIOPlugin(DataSourcePlugin):
    def __init__(self, config, server):
        super().__init__(config, server)
        GPIO.setmode(GPIO.BCM)
        self.poll_interval = int(os.getenv('GPIO_POLL_INTERVAL_MS', 1000)) / 1000
        self.pin_config = self._load_config()

    def _load_config(self):
        config_path = os.getenv('GPIO_PIN_CONFIG', 'config/gpio_sources.json')
        with open(config_path) as f:
            return json.load(f)

    async def start(self):
        self.running = True
        # Setup GPIO pins
        for pin in self.pin_config.get('pins', []):
            gpio = pin['gpio']
            if pin['type'] == 'input':
                GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            elif pin['type'] == 'output':
                GPIO.setup(gpio, GPIO.OUT)

            # Create OPC-UA variable node
            node = await self.server.add_variable(
                'gpio', pin['name'], 0.0 if pin['type'] == 'input' else False
            )
            self.nodes[gpio] = {'node': node, 'config': pin}

        # Start polling loop
        asyncio.create_task(self._poll_loop())

    async def _poll_loop(self):
        while self.running:
            for gpio, info in self.nodes.items():
                value = GPIO.input(gpio)
                await self.server.update_variable(info['node'], value)
            await asyncio.sleep(self.poll_interval)

    async def stop(self):
        self.running = False
        GPIO.cleanup()

    def get_status(self):
        return {
            'source': 'gpio',
            'status': 'running' if self.running else 'stopped',
            'pins': len(self.nodes)
        }

    def get_values(self):
        return {f"GPIO_{g}": GPIO.input(g) for g in self.nodes}
```

---

## Phase 4: Historical Data Access (Day 5–6)

### Step 4.1 — HDA storage (`src/historical_access.py`)
```python
import sqlite3
import os
import time
from datetime import datetime, timedelta

class HistoricalAccess:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv('DB_PATH', 'data/opcua_gateway.db')
        self.retention_days = int(os.getenv('HDA_RETENTION_DAYS', 90))

    def store(self, node_id, value, quality=0):
        """Store a historical value"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            '''INSERT INTO historical_data
               (node_id, value, quality, source_timestamp, server_timestamp)
               VALUES (?, ?, ?, ?, ?)''',
            (node_id, str(value), quality, time.time(), time.time())
        )
        conn.commit()
        conn.close()

    def read(self, node_id, start_time, end_time, max_points=10000):
        """Read historical values for a node"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            '''SELECT value, quality, source_timestamp, server_timestamp
               FROM historical_data
               WHERE node_id = ? AND source_timestamp BETWEEN ? AND ?
               ORDER BY source_timestamp ASC
               LIMIT ?''',
            (node_id, start_time.timestamp(), end_time.timestamp(), max_points)
        )
        results = [
            {
                'value': row[0],
                'quality': row[1],
                'source_timestamp': row[2],
                'server_timestamp': row[3]
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return results

    def purge_old_data(self):
        """Remove data older than retention period"""
        cutoff = time.time() - (self.retention_days * 86400)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            'DELETE FROM historical_data WHERE source_timestamp < ?', (cutoff,))
        conn.commit()
        conn.close()
```

---

## Phase 5: Alarm Manager (Day 8–9)

### Step 5.1 — Alarm manager (`src/alarm_manager.py`)
```python
import threading
import time

class AlarmManager:
    def __init__(self, db, ws_callback, notification_service):
        self.db = db
        self.ws = ws_callback
        self.notify = notification_service
        self.configs = {}
        self.active_alarms = {}

    def load_configs(self):
        """Load alarm configurations from database"""
        self.configs = self.db.get_alarm_configs()

    def check_value(self, node_id, value):
        """Check a value against configured alarm limits"""
        if node_id not in self.configs:
            return

        for config in self.configs[node_id]:
            if not config['enabled']:
                continue
            alarm_key = f"{node_id}_{config['alarm_type']}"
            triggered = self._evaluate(config, value)

            if triggered and alarm_key not in self.active_alarms:
                # New alarm
                alarm = self.db.create_alarm(
                    node_id, config['alarm_type'],
                    config['severity'], config['limit_value'], value
                )
                self.active_alarms[alarm_key] = alarm
                self.ws('alarm_triggered', {
                    'node_id': node_id,
                    'type': config['alarm_type'],
                    'severity': config['severity'],
                    'value': value,
                    'limit': config['limit_value']
                })
                self.notify.send(
                    f"⚠️ Alarm: {config['alarm_type']} on {node_id}\n"
                    f"Value: {value} (limit: {config['limit_value']})"
                )
            elif not triggered and alarm_key in self.active_alarms:
                # Alarm cleared
                self.db.clear_alarm(self.active_alarms[alarm_key]['id'])
                del self.active_alarms[alarm_key]
                self.ws('alarm_cleared', {
                    'node_id': node_id,
                    'type': config['alarm_type']
                })

    def _evaluate(self, config, value):
        alarm_type = config['alarm_type']
        limit = config['limit_value']
        deadband = config.get('deadband', 0)
        if alarm_type in ('high', 'hihi'):
            return value > (limit + deadband)
        elif alarm_type in ('low', 'lolo'):
            return value < (limit - deadband)
        return False
```

---

## Phase 6: Certificate Manager & REST Proxy (Day 9–10)

### Step 6.1 — Certificate generation (`scripts/generate_certs.py`)
```python
#!/usr/bin/env python3
"""Generate self-signed X.509 certificate for OPC-UA server"""
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import os

def generate_cert(cert_path='certs/server_cert.pem',
                  key_path='certs/server_key.pem'):
    os.makedirs(os.path.dirname(cert_path), exist_ok=True)

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, 'RaspberryPi OPC-UA Gateway'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Raspberry Projects'),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.UniformResourceIdentifier(
                    'urn:raspberry:opcua:gateway'),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    with open(key_path, 'wb') as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Certificate: {cert_path}")
    print(f"Private key: {key_path}")

if __name__ == '__main__':
    generate_cert()
```

### Step 6.2 — REST API proxy (`src/rest_proxy.py`)
```python
from flask import Blueprint, jsonify, request
from src.auth import require_auth

class RESTProxy:
    def __init__(self, opcua_server):
        self.server = opcua_server
        self.bp = Blueprint('rest_proxy', __name__, url_prefix='/api/rest')
        self._register_routes()

    def _register_routes(self):
        @self.bp.route('/<path:browse_path>', methods=['GET'])
        @require_auth
        async def read_value(browse_path):
            """Read OPC-UA node value by browse path"""
            parts = browse_path.split('/')
            node = await self._resolve_path(parts)
            if node is None:
                return jsonify({'error': 'Node not found'}), 404
            value = await node.read_value()
            data_type = await node.read_data_type_as_variant_type()
            return jsonify({
                'value': value,
                'data_type': str(data_type),
                'timestamp': str(await node.read_data_value()),
                'quality': 'Good'
            })

        @self.bp.route('/<path:browse_path>', methods=['PUT'])
        @require_auth
        async def write_value(browse_path):
            """Write OPC-UA node value by browse path"""
            parts = browse_path.split('/')
            node = await self._resolve_path(parts)
            if node is None:
                return jsonify({'error': 'Node not found'}), 404
            value = request.json.get('value')
            await node.write_value(value)
            return jsonify({'written': True})

    async def _resolve_path(self, parts):
        """Resolve browse path to OPC-UA node"""
        current = self.server.folders.get(parts[0].lower())
        for part in parts[1:]:
            children = await current.get_children()
            current = next(
                (c for c in children
                 if (await c.read_browse_name()).Name == part), None)
            if current is None:
                return None
        return current
```

---

## Phases 7–10: Remaining Phases

- **Phase 7** (Node-RED): Install + iframe embed + sample flow with node-red-contrib-opcua
- **Phase 8** (CODESYS Info): Runtime status polling + IEC variable type mapping hints
- **Phase 9** (Feature Toggles + Notifications): Bidirectional `.env` ↔ SQLite sync, Telegram/Slack/email
- **Phase 10** (Deployment): systemd service, certificate generation, firewall rules, testing

Each phase follows the same pattern: module implementation → API routes → dashboard UI → WebSocket integration → testing.
