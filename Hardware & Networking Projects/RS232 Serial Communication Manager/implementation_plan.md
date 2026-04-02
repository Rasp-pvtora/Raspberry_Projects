# 🗺️ Implementation Plan — RS232 Serial Communication Manager

---

## Phase 1: Project Setup & Authentication (Day 1)

### Step 1.1 — Initialize project
```bash
mkdir -p src/routes src/templates static/css static/js data/recordings data/scripts config/parsers deploy docs tests
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
pyserial==3.5.*
crcmod==1.7.*
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

from routes import auth_routes, port_routes, modbus_routes, bridge_routes
from routes import macro_routes, response_routes, profile_routes
from routes import recording_routes, protocol_routes, script_routes
from routes import analytics_routes, settings_routes
app.register_blueprint(auth_routes.bp)
app.register_blueprint(port_routes.bp)
app.register_blueprint(modbus_routes.bp)
app.register_blueprint(bridge_routes.bp)
app.register_blueprint(macro_routes.bp)
app.register_blueprint(response_routes.bp)
app.register_blueprint(profile_routes.bp)
app.register_blueprint(recording_routes.bp)
app.register_blueprint(protocol_routes.bp)
app.register_blueprint(script_routes.bp)
app.register_blueprint(analytics_routes.bp)
app.register_blueprint(settings_routes.bp)

if __name__ == '__main__':
    socketio.run(app, host=os.getenv('HOST', '0.0.0.0'),
                 port=int(os.getenv('PORT', 5000)))
```

### Step 1.4 — Database init (`src/init_db.py`)
```python
import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'data/serial_manager.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        created_at TEXT DEFAULT (datetime('now')),
        last_login TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS port_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_path TEXT NOT NULL,
        display_name TEXT,
        baud_rate INTEGER DEFAULT 9600,
        data_bits INTEGER DEFAULT 8,
        parity TEXT DEFAULT 'N',
        stop_bits REAL DEFAULT 1.0,
        flow_control TEXT DEFAULT 'none',
        timeout_sec REAL DEFAULT 1.0,
        auto_open INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS feature_toggles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_key TEXT UNIQUE NOT NULL,
        enabled INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now'))
    )''')

    # Insert default feature toggles
    features = [
        ('auto_detect', 1), ('multi_port', 1), ('hex_view', 1),
        ('msg_builder', 1), ('modbus_rtu', 1), ('auto_response', 1),
        ('tcp_bridge', 1), ('data_plotting', 1), ('macros', 1),
        ('rest_api', 1), ('protocol_analyzer', 1), ('session_recording', 1),
        ('port_profiles', 1), ('notifications', 1), ('conn_stats', 1),
        ('scripting', 0)
    ]
    for key, default in features:
        c.execute(
            'INSERT OR IGNORE INTO feature_toggles (feature_key, enabled) VALUES (?, ?)',
            (key, default))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DB_PATH}")
```

---

## Phase 2: Port Manager & Auto-Detection (Day 1–2)

### Step 2.1 — Port manager (`src/port_manager.py`)
```python
import serial
import serial.tools.list_ports
import threading
import time
import os

class PortManager:
    def __init__(self, socketio):
        self.socketio = socketio
        self.ports = {}  # device_path → PortHandler
        self.max_ports = int(os.getenv('MAX_PORTS', 8))
        self.scan_interval = 3
        self._known_ports = set()
        self._scan_thread = None
        self._running = False

    def start_auto_detect(self):
        self._running = True
        self._scan_thread = threading.Thread(
            target=self._scan_loop, daemon=True)
        self._scan_thread.start()

    def _scan_loop(self):
        while self._running:
            current = set()
            for port_info in serial.tools.list_ports.comports():
                current.add(port_info.device)
                if port_info.device not in self._known_ports:
                    self.socketio.emit('port_detected', {
                        'port': port_info.device,
                        'description': port_info.description,
                        'hwid': port_info.hwid
                    })
            # Detect removals
            removed = self._known_ports - current
            for device in removed:
                self.socketio.emit('port_removed', {'port': device})
                if device in self.ports:
                    self.ports[device].close()
                    del self.ports[device]
            self._known_ports = current
            time.sleep(self.scan_interval)

    def list_ports(self):
        return [
            {
                'device': p.device,
                'description': p.description,
                'hwid': p.hwid,
                'is_open': p.device in self.ports and self.ports[p.device].is_open
            }
            for p in serial.tools.list_ports.comports()
        ]

    def open_port(self, device, config):
        if len(self.ports) >= self.max_ports:
            raise RuntimeError(f"Maximum {self.max_ports} ports exceeded")
        handler = PortHandler(device, config, self.socketio)
        handler.open()
        self.ports[device] = handler
        return handler

    def close_port(self, device):
        if device in self.ports:
            self.ports[device].close()
            del self.ports[device]

    def stop(self):
        self._running = False
        for handler in self.ports.values():
            handler.close()
```

### Step 2.2 — Port handler (`src/port_handler.py`)
```python
import serial
import threading
import queue
import time

class PortHandler:
    def __init__(self, device, config, socketio):
        self.device = device
        self.config = config
        self.socketio = socketio
        self.serial = None
        self.is_open = False
        self._read_thread = None
        self._write_queue = queue.Queue()
        self._running = False
        self.stats = {
            'bytes_tx': 0, 'bytes_rx': 0,
            'errors': 0, 'opened_at': None
        }

    def open(self):
        self.serial = serial.Serial(
            port=self.device,
            baudrate=self.config.get('baud_rate', 9600),
            bytesize=self.config.get('data_bits', 8),
            parity=self.config.get('parity', 'N'),
            stopbits=self.config.get('stop_bits', 1),
            timeout=self.config.get('timeout_sec', 1)
        )
        self.is_open = True
        self.stats['opened_at'] = time.time()
        self._running = True
        self._read_thread = threading.Thread(
            target=self._read_loop, daemon=True)
        self._read_thread.start()

    def _read_loop(self):
        while self._running and self.serial and self.serial.is_open:
            try:
                data = self.serial.read(self.serial.in_waiting or 1)
                if data:
                    self.stats['bytes_rx'] += len(data)
                    hex_str = ' '.join(f'{b:02X}' for b in data)
                    ascii_str = ''.join(
                        chr(b) if 32 <= b < 127 else '.' for b in data)
                    self.socketio.emit('serial_data', {
                        'port': self.device,
                        'direction': 'rx',
                        'hex': hex_str,
                        'ascii': ascii_str,
                        'timestamp': time.time(),
                        'length': len(data)
                    })
            except serial.SerialException as e:
                self.stats['errors'] += 1
                self.socketio.emit('port_error', {
                    'port': self.device, 'error': str(e)})
                break

    def send(self, data, encoding='hex'):
        if encoding == 'hex':
            raw = bytes.fromhex(data.replace(' ', ''))
        else:
            raw = data.encode('utf-8')
        self.serial.write(raw)
        self.stats['bytes_tx'] += len(raw)
        return len(raw)

    def close(self):
        self._running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.is_open = False
```

---

## Phase 3: CRC Calculator (Day 3)

### Step 3.1 — CRC module (`src/crc_calculator.py`)
```python
import crcmod

class CRCCalculator:
    ALGORITHMS = {
        'crc8': {'poly': 0x107, 'init': 0x00, 'rev': False, 'xor': 0x00},
        'crc16_modbus': {'poly': 0x18005, 'init': 0xFFFF, 'rev': True, 'xor': 0x0000},
        'crc16_ccitt': {'poly': 0x11021, 'init': 0xFFFF, 'rev': False, 'xor': 0x0000},
        'crc32': {'poly': 0x104C11DB7, 'init': 0xFFFFFFFF, 'rev': True, 'xor': 0xFFFFFFFF},
    }

    @classmethod
    def calculate(cls, data: bytes, algorithm: str) -> int:
        if algorithm not in cls.ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        cfg = cls.ALGORITHMS[algorithm]
        crc_func = crcmod.mkCrcFun(
            cfg['poly'], initCrc=cfg['init'], rev=cfg['rev'], xorOut=cfg['xor'])
        return crc_func(data)

    @classmethod
    def append_crc(cls, data: bytes, algorithm: str) -> bytes:
        crc = cls.calculate(data, algorithm)
        if algorithm.startswith('crc8'):
            return data + crc.to_bytes(1, 'big')
        elif algorithm.startswith('crc16'):
            return data + crc.to_bytes(2, 'little')  # Modbus is little-endian
        else:
            return data + crc.to_bytes(4, 'little')

    @classmethod
    def verify(cls, data: bytes, algorithm: str) -> bool:
        """Verify CRC at end of data"""
        if algorithm.startswith('crc8'):
            payload, expected = data[:-1], int.from_bytes(data[-1:], 'big')
        elif algorithm.startswith('crc16'):
            payload, expected = data[:-2], int.from_bytes(data[-2:], 'little')
        else:
            payload, expected = data[:-4], int.from_bytes(data[-4:], 'little')
        return cls.calculate(payload, algorithm) == expected
```

---

## Phase 4: Modbus RTU Engine (Day 3–4)

### Step 4.1 — Modbus RTU (`src/modbus_rtu.py`)
```python
import struct
import time
from .crc_calculator import CRCCalculator

class ModbusRTU:
    def __init__(self, port_handler, slave_id=1, timeout_ms=1000, retries=3):
        self.port = port_handler
        self.slave_id = slave_id
        self.timeout = timeout_ms / 1000
        self.retries = retries

    def read_holding_registers(self, start_addr, count):
        """FC03 — Read Holding Registers"""
        request = struct.pack('>BBhh',
            self.slave_id, 0x03, start_addr, count)
        request = CRCCalculator.append_crc(request, 'crc16_modbus')
        return self._transact(request, expected_bytes=5 + count * 2)

    def write_single_register(self, address, value):
        """FC06 — Write Single Register"""
        request = struct.pack('>BBhh',
            self.slave_id, 0x06, address, value)
        request = CRCCalculator.append_crc(request, 'crc16_modbus')
        return self._transact(request, expected_bytes=8)

    def _transact(self, request, expected_bytes):
        for attempt in range(self.retries):
            self.port.serial.write(request)
            self.port.stats['bytes_tx'] += len(request)
            time.sleep(0.05)  # Inter-frame delay

            response = self.port.serial.read(expected_bytes)
            if not response:
                continue

            # Verify CRC
            if not CRCCalculator.verify(response, 'crc16_modbus'):
                continue

            # Check for exception response
            if response[1] & 0x80:
                error_code = response[2]
                raise ModbusException(response[1] & 0x7F, error_code)

            return self._parse_response(response)
        raise TimeoutError("No valid response after retries")

    def _parse_response(self, response):
        fc = response[1]
        if fc in (0x01, 0x02, 0x03, 0x04):
            byte_count = response[2]
            data = response[3:3 + byte_count]
            if fc in (0x03, 0x04):
                registers = [
                    struct.unpack('>H', data[i:i+2])[0]
                    for i in range(0, len(data), 2)
                ]
                return {'registers': registers}
            return {'data': list(data)}
        elif fc in (0x05, 0x06):
            addr = struct.unpack('>H', response[2:4])[0]
            value = struct.unpack('>H', response[4:6])[0]
            return {'address': addr, 'value': value}
        return {'raw': response.hex()}

class ModbusException(Exception):
    CODES = {
        1: 'Illegal Function', 2: 'Illegal Data Address',
        3: 'Illegal Data Value', 4: 'Server Device Failure',
        5: 'Acknowledge', 6: 'Server Device Busy'
    }
    def __init__(self, fc, code):
        self.fc = fc
        self.code = code
        super().__init__(f"Modbus Exception FC{fc:02X}: {self.CODES.get(code, 'Unknown')}")
```

---

## Phase 5: TCP Bridge (Day 5–6)

### Step 5.1 — TCP bridge server (`src/tcp_bridge.py`)
```python
import socket
import threading
import os

class TCPBridge:
    def __init__(self, port_handler, tcp_port, socketio,
                 max_clients=10, whitelist=None):
        self.port_handler = port_handler
        self.tcp_port = tcp_port
        self.socketio = socketio
        self.max_clients = max_clients
        self.whitelist = set(whitelist) if whitelist else None
        self.clients = []
        self.server_socket = None
        self._running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.tcp_port))
        self.server_socket.listen(self.max_clients)
        self._running = True

        # Accept thread
        threading.Thread(target=self._accept_loop, daemon=True).start()
        # Serial→TCP forwarding thread
        threading.Thread(target=self._serial_to_tcp, daemon=True).start()

    def _accept_loop(self):
        while self._running:
            try:
                client, addr = self.server_socket.accept()
                if self.whitelist and addr[0] not in self.whitelist:
                    client.close()
                    continue
                if len(self.clients) >= self.max_clients:
                    client.close()
                    continue
                self.clients.append(client)
                self.socketio.emit('bridge_client', {
                    'bridge_id': self.tcp_port,
                    'client': f"{addr[0]}:{addr[1]}",
                    'event': 'connected'
                })
                # TCP→Serial thread per client
                threading.Thread(
                    target=self._tcp_to_serial,
                    args=(client, addr), daemon=True).start()
            except OSError:
                break

    def _tcp_to_serial(self, client, addr):
        try:
            while self._running:
                data = client.recv(4096)
                if not data:
                    break
                self.port_handler.serial.write(data)
        finally:
            self.clients.remove(client)
            client.close()
            self.socketio.emit('bridge_client', {
                'bridge_id': self.tcp_port,
                'client': f"{addr[0]}:{addr[1]}",
                'event': 'disconnected'
            })

    def _serial_to_tcp(self):
        while self._running:
            if self.port_handler.serial and self.port_handler.serial.in_waiting:
                data = self.port_handler.serial.read(
                    self.port_handler.serial.in_waiting)
                for client in list(self.clients):
                    try:
                        client.sendall(data)
                    except OSError:
                        pass

    def stop(self):
        self._running = False
        for client in self.clients:
            client.close()
        if self.server_socket:
            self.server_socket.close()
```

---

## Phase 6: Auto-Response Engine (Day 5)

### Step 6.1 — Auto-response (`src/auto_response.py`)
```python
import re
import time
import threading

class AutoResponseEngine:
    def __init__(self, db, port_manager, socketio):
        self.db = db
        self.ports = port_manager
        self.socketio = socketio
        self.rules = []
        self.reload_rules()

    def reload_rules(self):
        self.rules = self.db.get_auto_response_rules(enabled_only=True)
        self.rules.sort(key=lambda r: r['priority'])

    def check(self, port_device, data_bytes):
        hex_str = data_bytes.hex()
        ascii_str = data_bytes.decode('ascii', errors='replace')

        for rule in self.rules:
            if rule['port_filter'] and rule['port_filter'] != port_device:
                continue

            match_data = hex_str if rule['match_encoding'] == 'hex' else ascii_str
            matched = self._match(rule['match_type'], rule['match_pattern'], match_data)

            if matched:
                threading.Timer(
                    rule['delay_ms'] / 1000,
                    self._send_response,
                    args=(port_device, rule)
                ).start()
                return True
        return False

    def _match(self, match_type, pattern, data):
        if match_type == 'contains':
            return pattern.lower() in data.lower()
        elif match_type == 'starts_with':
            return data.lower().startswith(pattern.lower())
        elif match_type == 'ends_with':
            return data.lower().endswith(pattern.lower())
        elif match_type == 'exact':
            return data.lower() == pattern.lower()
        elif match_type == 'regex':
            return bool(re.search(pattern, data, re.IGNORECASE))
        return False

    def _send_response(self, port_device, rule):
        handler = self.ports.ports.get(port_device)
        if handler and handler.is_open:
            handler.send(rule['response_data'], rule['response_encoding'])
            self.socketio.emit('auto_response_fired', {
                'port': port_device,
                'rule_name': rule['name'],
                'response': rule['response_data']
            })
```

---

## Phase 7: Protocol Analyzer (Day 8–9)

### Step 7.1 — Protocol analyzer (`src/protocol_analyzer.py`)
```python
import json
import struct
import os
from .crc_calculator import CRCCalculator

class ProtocolAnalyzer:
    def __init__(self):
        self.parsers = {}
        self._load_builtin_parsers()
        self._load_custom_parsers()

    def _load_builtin_parsers(self):
        self.parsers['modbus_rtu'] = self._decode_modbus
        self.parsers['nmea_0183'] = self._decode_nmea

    def _load_custom_parsers(self):
        parser_dir = os.getenv('CUSTOM_PARSER_DIR', 'config/parsers')
        if os.path.isdir(parser_dir):
            for f in os.listdir(parser_dir):
                if f.endswith('.json'):
                    path = os.path.join(parser_dir, f)
                    with open(path) as fh:
                        definition = json.load(fh)
                    name = os.path.splitext(f)[0]
                    self.parsers[name] = lambda data, d=definition: \
                        self._decode_custom(data, d)

    def decode(self, data: bytes, protocol: str) -> dict:
        parser = self.parsers.get(protocol)
        if not parser:
            return {'error': f'Unknown protocol: {protocol}'}
        return parser(data)

    def _decode_modbus(self, data: bytes) -> dict:
        if len(data) < 4:
            return {'error': 'Frame too short'}
        if not CRCCalculator.verify(data, 'crc16_modbus'):
            return {'error': 'CRC mismatch'}
        slave_id = data[0]
        fc = data[1]
        fc_names = {
            1: 'Read Coils', 2: 'Read Discrete Inputs',
            3: 'Read Holding Registers', 4: 'Read Input Registers',
            5: 'Write Single Coil', 6: 'Write Single Register',
            15: 'Write Multiple Coils', 16: 'Write Multiple Registers'
        }
        result = {
            'protocol': 'Modbus RTU',
            'slave_id': slave_id,
            'function_code': fc,
            'function_name': fc_names.get(fc, f'Unknown (0x{fc:02X})'),
        }
        # Parse based on function code
        if fc in (1, 2, 3, 4) and len(data) >= 8:
            addr = struct.unpack('>H', data[2:4])[0]
            qty = struct.unpack('>H', data[4:6])[0]
            result.update({'start_address': addr, 'quantity': qty})
        return result

    def _decode_nmea(self, data: bytes) -> dict:
        text = data.decode('ascii', errors='replace').strip()
        if not text.startswith('$'):
            return {'error': 'Not an NMEA sentence'}
        parts = text.split('*')
        sentence = parts[0][1:]
        fields = sentence.split(',')
        return {
            'protocol': 'NMEA 0183',
            'talker': fields[0][:2],
            'sentence_type': fields[0][2:],
            'fields': fields[1:],
            'checksum': parts[1] if len(parts) > 1 else None
        }
```

---

## Phase 8: Scripting Engine (Day 9–10)

### Step 8.1 — Sandboxed engine (`src/scripting_engine.py`)
```python
import threading
import time
import io
import contextlib

SAFE_BUILTINS = {
    'print': print, 'len': len, 'range': range, 'int': int,
    'float': float, 'str': str, 'bytes': bytes, 'bytearray': bytearray,
    'hex': hex, 'bin': bin, 'ord': ord, 'chr': chr,
    'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
    'True': True, 'False': False, 'None': None,
    'enumerate': enumerate, 'zip': zip, 'map': map,
}

SAFE_IMPORTS = {'time', 'struct', 'binascii', 're', 'json', 'math'}

class ScriptingEngine:
    def __init__(self, port_manager, timeout=30):
        self.ports = port_manager
        self.timeout = timeout

    def execute(self, code, port_device=None):
        output = io.StringIO()
        result = {'success': False, 'output': '', 'error': None}

        # Prepare safe globals
        safe_globals = {'__builtins__': SAFE_BUILTINS}

        # Provide serial API
        if port_device and port_device in self.ports.ports:
            handler = self.ports.ports[port_device]
            safe_globals['serial'] = SerialAPI(handler)

        # Add safe imports
        import importlib
        for mod_name in SAFE_IMPORTS:
            safe_globals[mod_name] = importlib.import_module(mod_name)

        def _run():
            nonlocal result
            try:
                with contextlib.redirect_stdout(output):
                    exec(code, safe_globals)
                result['success'] = True
                result['output'] = output.getvalue()
            except Exception as e:
                result['error'] = f"{type(e).__name__}: {e}"
                result['output'] = output.getvalue()

        thread = threading.Thread(target=_run)
        thread.start()
        thread.join(timeout=self.timeout)

        if thread.is_alive():
            result['error'] = f"Script timed out after {self.timeout}s"

        return result

class SerialAPI:
    """Safe serial API exposed to scripts"""
    def __init__(self, handler):
        self._handler = handler

    def send(self, data, encoding='hex'):
        return self._handler.send(data, encoding)

    def read(self, size=1024, timeout=1.0):
        old_timeout = self._handler.serial.timeout
        self._handler.serial.timeout = timeout
        data = self._handler.serial.read(size)
        self._handler.serial.timeout = old_timeout
        return data

    def wait(self, seconds):
        time.sleep(min(seconds, 10))  # Cap at 10 seconds
```

---

## Phase 9: Feature Toggles (Day 11)

### Step 9.1 — Bidirectional sync (`src/feature_toggles.py`)
```python
import sqlite3
import os

FEATURE_ENV_MAP = {
    'auto_detect': 'ENABLE_AUTO_DETECT',
    'multi_port': 'ENABLE_MULTI_PORT',
    'hex_view': 'ENABLE_HEX_VIEW',
    'msg_builder': 'ENABLE_MSG_BUILDER',
    'modbus_rtu': 'ENABLE_MODBUS_RTU',
    'auto_response': 'ENABLE_AUTO_RESPONSE',
    'tcp_bridge': 'ENABLE_TCP_BRIDGE',
    'data_plotting': 'ENABLE_DATA_PLOTTING',
    'macros': 'ENABLE_MACROS',
    'rest_api': 'ENABLE_REST_API',
    'protocol_analyzer': 'ENABLE_PROTOCOL_ANALYZER',
    'session_recording': 'ENABLE_SESSION_RECORDING',
    'port_profiles': 'ENABLE_PORT_PROFILES',
    'notifications': 'ENABLE_NOTIFICATIONS',
    'conn_stats': 'ENABLE_CONN_STATS',
    'scripting': 'ENABLE_SCRIPTING',
}

class FeatureToggles:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_all(self):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            'SELECT feature_key, enabled FROM feature_toggles').fetchall()
        conn.close()
        return {row[0]: bool(row[1]) for row in rows}

    def update(self, feature_key, enabled):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            'UPDATE feature_toggles SET enabled = ?, updated_at = datetime("now") WHERE feature_key = ?',
            (int(enabled), feature_key))
        conn.commit()
        conn.close()
        self._sync_to_env(feature_key, enabled)

    def is_enabled(self, feature_key):
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            'SELECT enabled FROM feature_toggles WHERE feature_key = ?',
            (feature_key,)).fetchone()
        conn.close()
        return bool(row[0]) if row else False

    def _sync_to_env(self, feature_key, enabled):
        env_var = FEATURE_ENV_MAP.get(feature_key)
        if not env_var:
            return
        env_path = os.path.join(os.path.dirname(self.db_path), '..', '.env')
        if not os.path.exists(env_path):
            return
        with open(env_path, 'r') as f:
            lines = f.readlines()
        value = 'true' if enabled else 'false'
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f'{env_var}='):
                lines[i] = f'{env_var}={value}\n'
                updated = True
                break
        if not updated:
            lines.append(f'{env_var}={value}\n')
        with open(env_path, 'w') as f:
            f.writelines(lines)
```

---

## Phase 10: Deployment (Day 12)

### Step 10.1 — Systemd service (`deploy/serial-manager.service`)
```ini
[Unit]
Description=RS232 Serial Communication Manager
After=network.target

[Service]
Type=simple
User=pi
WorkingDir=/home/pi/serial-manager
ExecStart=/home/pi/serial-manager/venv/bin/python src/app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### Step 10.2 — Deploy script (`deploy/deploy_to_pi.sh`)
```bash
#!/bin/bash
set -e
echo "=== RS232 Serial Communication Manager — Deploy ==="

# Add user to dialout group
sudo usermod -aG dialout $USER

# Enable UART
sudo raspi-config nonint do_serial 0

# Install system packages
sudo apt-get update && sudo apt-get install -y python3-venv python3-pip

# Setup application
cd /home/pi/serial-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
python3 src/init_db.py

# Install systemd service
sudo cp deploy/serial-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable serial-manager
sudo systemctl start serial-manager

echo "=== Deployment complete ==="
echo "Access: http://$(hostname -I | awk '{print $1}'):5000"
```

Each phase follows the same pattern: module implementation → API routes → dashboard UI → WebSocket integration → testing.
