# 🗺️ Implementation Plan — CAN Bus & CANopen Communication Hub

---

## Phase 1: Project Setup & Authentication (Day 1)

### Step 1.1 — Initialize project
```bash
mkdir -p src/routes src/templates static/css static/js data/dbc data/eds data/recordings deploy docs tests
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
python-can==4.4.*
cantools==39.*
canopen==2.3.*
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

from routes import auth_routes, can_routes, dbc_routes, recorder_routes
from routes import canopen_routes, diag_routes, analytics_routes, settings_routes
app.register_blueprint(auth_routes.bp)
app.register_blueprint(can_routes.bp)
app.register_blueprint(dbc_routes.bp)
app.register_blueprint(recorder_routes.bp)
app.register_blueprint(canopen_routes.bp)
app.register_blueprint(diag_routes.bp)
app.register_blueprint(analytics_routes.bp)
app.register_blueprint(settings_routes.bp)

if __name__ == '__main__':
    socketio.run(app, host=os.getenv('HOST', '0.0.0.0'),
                 port=int(os.getenv('PORT', 5000)))
```

---

## Phase 2: SocketCAN Auto-Configuration (Day 1–2)

### Step 2.1 — CAN interface manager (`src/can_interface.py`)
```python
import subprocess
import os
import can

class CANInterface:
    def __init__(self):
        self.interface = os.getenv('CAN_INTERFACE', 'can0')
        self.bitrate = int(os.getenv('CAN_BITRATE', 500000))
        self.bus = None

    def setup(self):
        """Configure and bring up SocketCAN interface"""
        # Set bitrate
        subprocess.run([
            'ip', 'link', 'set', self.interface,
            'type', 'can', 'bitrate', str(self.bitrate)
        ], check=True)
        # Bring up
        subprocess.run([
            'ip', 'link', 'set', self.interface, 'up'
        ], check=True)

    def connect(self):
        """Create python-can bus instance"""
        self.bus = can.interface.Bus(
            channel=self.interface,
            interface='socketcan'
        )
        return self.bus

    def disconnect(self):
        if self.bus:
            self.bus.shutdown()
            self.bus = None

    def status(self):
        """Read SocketCAN interface status"""
        result = subprocess.run(
            ['ip', '-details', '-statistics', 'link', 'show', self.interface],
            capture_output=True, text=True
        )
        return self._parse_status(result.stdout)

    def _parse_status(self, output):
        import re
        state = 'down'
        if 'state UP' in output:
            state = 'up'
        bitrate_match = re.search(r'bitrate\s+(\d+)', output)
        return {
            'interface': self.interface,
            'state': state,
            'bitrate': int(bitrate_match.group(1)) if bitrate_match else 0
        }

    def restart(self):
        subprocess.run(['ip', 'link', 'set', self.interface, 'down'], check=False)
        self.setup()
```

---

## Phase 3: CAN Receiver & Live Viewer (Day 2–3)

### Step 3.1 — CAN receiver (`src/can_receiver.py`)
```python
import threading
import can
from datetime import datetime

class CANReceiver:
    def __init__(self, bus, db, ws_callback, filter_callback=None):
        self.bus = bus
        self.db = db
        self.ws = ws_callback
        self.filter_fn = filter_callback
        self.running = False
        self.msg_count = 0
        self.error_count = 0

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()

    def stop(self):
        self.running = False

    def _receive_loop(self):
        while self.running:
            msg = self.bus.recv(timeout=1.0)
            if msg is None:
                continue
            if msg.is_error_frame:
                self.error_count += 1
                continue
            if self.filter_fn and not self.filter_fn(msg):
                continue

            self.msg_count += 1
            frame = {
                'arb_id': hex(msg.arbitration_id),
                'dlc': msg.dlc,
                'data': msg.data.hex().upper(),
                'is_extended': msg.is_extended_id,
                'direction': 'rx',
                'timestamp': msg.timestamp
            }
            self.db.store_message(frame)
            self.ws('can_message', frame)

    def get_stats(self):
        return {
            'msg_count': self.msg_count,
            'error_count': self.error_count
        }
```

### Step 3.2 — CAN sender (`src/can_sender.py`)
```python
import can
import threading
import time

class CANSender:
    def __init__(self, bus, db):
        self.bus = bus
        self.db = db

    def send(self, arb_id, data_hex, extended=False, remote=False):
        """Send a single CAN frame"""
        data = bytes.fromhex(data_hex.replace(' ', ''))
        msg = can.Message(
            arbitration_id=arb_id,
            data=data,
            is_extended_id=extended,
            is_remote_frame=remote
        )
        self.bus.send(msg)
        self.db.store_message({
            'arb_id': hex(arb_id),
            'dlc': len(data),
            'data': data_hex.upper(),
            'direction': 'tx',
            'timestamp': msg.timestamp
        })

    def send_repeated(self, arb_id, data_hex, interval_ms, count, extended=False):
        """Send repeated CAN frames in background"""
        def _repeat():
            for i in range(count):
                self.send(arb_id, data_hex, extended)
                time.sleep(interval_ms / 1000.0)
        thread = threading.Thread(target=_repeat, daemon=True)
        thread.start()
```

---

## Phase 4: DBC Signal Decoder (Day 4)

### Step 4.1 — DBC decoder (`src/dbc_decoder.py`)
```python
import cantools
import os

class DBCDecoder:
    def __init__(self, dbc_dir='data/dbc/'):
        self.dbc_dir = dbc_dir
        self.databases = []
        os.makedirs(dbc_dir, exist_ok=True)

    def load_file(self, filepath):
        db = cantools.database.load_file(filepath)
        self.databases.append(db)
        return {
            'messages': len(db.messages),
            'signals': sum(len(m.signals) for m in db.messages)
        }

    def decode(self, arb_id, data_bytes):
        """Try to decode CAN frame against all loaded DBC databases"""
        for db in self.databases:
            try:
                msg = db.get_message_by_frame_id(arb_id)
                decoded = msg.decode(data_bytes)
                return {
                    'message_name': msg.name,
                    'signals': [
                        {
                            'name': name,
                            'value': value,
                            'unit': next(
                                (s.unit for s in msg.signals if s.name == name), '')
                        }
                        for name, value in decoded.items()
                    ]
                }
            except (KeyError, cantools.database.DecodeError):
                continue
        return None

    def list_messages(self):
        """List all known messages across loaded DBC files"""
        messages = []
        for db in self.databases:
            for msg in db.messages:
                messages.append({
                    'name': msg.name,
                    'frame_id': hex(msg.frame_id),
                    'dlc': msg.length,
                    'signals': [s.name for s in msg.signals]
                })
        return messages
```

---

## Phase 5: Recorder & Replay (Day 4–5)

### Step 5.1 — CAN recorder (`src/recorder.py`)
```python
import can
import os
from datetime import datetime

class CANRecorder:
    def __init__(self, output_dir='data/recordings/', format='asc'):
        self.output_dir = output_dir
        self.format = format
        self.writer = None
        self.filename = None
        self.msg_count = 0
        self.recording = False
        os.makedirs(output_dir, exist_ok=True)

    def start(self, can_bus):
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        self.filename = f"can_{timestamp}.{self.format}"
        filepath = os.path.join(self.output_dir, self.filename)

        if self.format == 'asc':
            self.writer = can.ASCWriter(filepath)
        elif self.format == 'blf':
            self.writer = can.BLFWriter(filepath)
        elif self.format == 'csv':
            self.writer = can.CSVWriter(filepath)

        self.recording = True
        self.msg_count = 0

    def write(self, msg):
        if self.recording and self.writer:
            self.writer.on_message_received(msg)
            self.msg_count += 1

    def stop(self):
        self.recording = False
        if self.writer:
            self.writer.stop()
            self.writer = None
        return {
            'filename': self.filename,
            'messages': self.msg_count
        }
```

### Step 5.2 — Replay engine (`src/replay_engine.py`)
```python
import can
import threading
import time

class ReplayEngine:
    def __init__(self, can_bus, ws_callback):
        self.bus = can_bus
        self.ws = ws_callback
        self.replaying = False
        self.progress = 0

    def start(self, filepath, speed_factor=1.0):
        self.replaying = True
        thread = threading.Thread(
            target=self._replay, args=(filepath, speed_factor), daemon=True)
        thread.start()

    def _replay(self, filepath, speed_factor):
        reader = can.LogReader(filepath)
        messages = list(reader)
        total = len(messages)

        for i, msg in enumerate(messages):
            if not self.replaying:
                break
            self.bus.send(msg)
            self.progress = int((i + 1) / total * 100)
            self.ws('replay_progress', {
                'progress_pct': self.progress,
                'messages_sent': i + 1
            })
            if i < total - 1:
                delay = (messages[i + 1].timestamp - msg.timestamp) / speed_factor
                if delay > 0:
                    time.sleep(delay)

        self.replaying = False

    def stop(self):
        self.replaying = False
```

---

## Phase 6: CANopen Integration (Day 6–8)

### Step 6.1 — CANopen NMT manager (`src/canopen_nmt.py`)
```python
import canopen

class CANopenNMTManager:
    def __init__(self, network):
        self.network = network

    def send_command(self, node_id, command):
        """Send NMT command to a node"""
        nmt_commands = {
            'start': 0x01,        # Start Remote Node
            'stop': 0x02,         # Stop Remote Node
            'pre_op': 0x80,       # Enter Pre-Operational
            'reset_node': 0x81,   # Reset Node
            'reset_comm': 0x82    # Reset Communication
        }
        cmd = nmt_commands.get(command)
        if cmd is None:
            raise ValueError(f"Unknown NMT command: {command}")
        self.network.send_message(0x000, [cmd, node_id])

    def get_node_state(self, node_id):
        node = self.network.get(node_id)
        if node:
            return node.nmt.state
        return 'unknown'

    def discover_nodes(self):
        """Scan for nodes using NMT boot-up messages"""
        self.network.scanner.search()
        import time
        time.sleep(2)
        return list(self.network.scanner.nodes)
```

### Step 6.2 — CANopen SDO client (`src/canopen_sdo.py`)
```python
class CANopenSDOClient:
    def __init__(self, network):
        self.network = network

    def read(self, node_id, index, subindex=0):
        """SDO upload (read from node)"""
        node = self.network.add_node(node_id)
        data = node.sdo.upload(index, subindex)
        return {
            'value': int.from_bytes(data, 'little') if len(data) <= 4 else data.hex(),
            'data_hex': data.hex(),
            'size': len(data)
        }

    def write(self, node_id, index, subindex, value, data_type='UNSIGNED16'):
        """SDO download (write to node)"""
        node = self.network.add_node(node_id)
        size_map = {
            'UNSIGNED8': 1, 'UNSIGNED16': 2, 'UNSIGNED32': 4,
            'INTEGER8': 1, 'INTEGER16': 2, 'INTEGER32': 4
        }
        size = size_map.get(data_type, 2)
        data = value.to_bytes(size, 'little')
        node.sdo.download(index, subindex, data)
        return {'written': True}
```

---

## Phase 7: Bus Diagnostics & TCP Bridge (Day 5–9)

### Step 7.1 — Bus diagnostics (`src/bus_diagnostics.py`)
```python
import os
import threading
import time

class BusDiagnostics:
    def __init__(self, interface, db, ws_callback, interval=1):
        self.interface = interface
        self.db = db
        self.ws = ws_callback
        self.interval = interval
        self.running = False
        self.prev_msg_count = 0

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._diag_loop, daemon=True)
        thread.start()

    def _diag_loop(self):
        while self.running:
            stats = self._read_stats()
            self.db.store_diagnostics(stats)
            self.ws('bus_diag', stats)
            time.sleep(self.interval)

    def _read_stats(self):
        base = f'/sys/class/net/{self.interface}/statistics'
        try:
            tx_errors = int(open(f'{base}/tx_errors').read().strip())
            rx_errors = int(open(f'{base}/rx_errors').read().strip())
            tx_packets = int(open(f'{base}/tx_packets').read().strip())
            rx_packets = int(open(f'{base}/rx_packets').read().strip())
        except FileNotFoundError:
            return {'error': 'Interface not found'}

        total = tx_packets + rx_packets
        msg_per_sec = (total - self.prev_msg_count) / self.interval
        self.prev_msg_count = total

        # Bus load = (msg_rate * avg_bits_per_msg) / bitrate * 100
        bus_load = min(100, (msg_per_sec * 130) / 500000 * 100)

        return {
            'bus_load_pct': round(bus_load, 1),
            'msg_per_sec': round(msg_per_sec, 1),
            'tx_error_count': tx_errors,
            'rx_error_count': rx_errors,
            'bus_state': self._get_bus_state(tx_errors, rx_errors)
        }

    def _get_bus_state(self, tx_err, rx_err):
        max_err = max(tx_err, rx_err)
        if max_err > 255:
            return 'bus-off'
        elif max_err > 127:
            return 'passive'
        elif max_err > 95:
            return 'warning'
        return 'active'
```

### Step 7.2 — CAN↔TCP bridge (`src/tcp_bridge.py`)
```python
import asyncio
import json
import os

class CANTCPBridge:
    def __init__(self, can_bus, host='0.0.0.0', port=29536, max_clients=5):
        self.can_bus = can_bus
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.clients = set()

    async def start(self):
        server = await asyncio.start_server(
            self._handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader, writer):
        if len(self.clients) >= self.max_clients:
            writer.close()
            return

        self.clients.add(writer)
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                # Parse incoming command and send to CAN bus
                frame = json.loads(data.decode())
                self._send_to_can(frame)
        finally:
            self.clients.discard(writer)
            writer.close()

    def broadcast(self, frame):
        """Forward CAN frame to all TCP clients"""
        data = json.dumps(frame).encode() + b'\n'
        for writer in list(self.clients):
            try:
                writer.write(data)
            except Exception:
                self.clients.discard(writer)

    def _send_to_can(self, frame):
        import can
        msg = can.Message(
            arbitration_id=int(frame['arb_id'], 16),
            data=bytes.fromhex(frame['data'])
        )
        self.can_bus.send(msg)
```

---

## Phases 8–10: Remaining Phases

Phases 8–10 follow the same implementation pattern:
- **Phase 8** (Analytics): Message rate trends, per-ID frequency, bus load history with Chart.js
- **Phase 9** (Feature Toggles + Notifications): Bidirectional `.env` ↔ SQLite sync, Telegram/Slack/email
- **Phase 10** (Deployment): systemd service, MCP2515 auto-load, TLS certs, testing

Each phase follows the same pattern: module implementation → API routes → dashboard UI → WebSocket integration → testing.
