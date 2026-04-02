# 🗺️ Implementation Plan — GPIO Data Logger & Pin Manager

---

## Phase 1: Project Setup & Authentication (Day 1)

### Step 1.1 — Initialize project
```bash
mkdir -p src/routes src/templates static/css static/js data/csv data/json data/archive deploy docs tests
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
RPi.GPIO==0.7.*
gpiozero==2.0.*
spidev==3.6.*
adafruit-circuitpython-mcp3xxx==1.4.*
python-telegram-bot==21.*
slack-sdk==3.33.*
pymsteams==0.2.*
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

from routes import auth_routes, pin_routes, settings_routes, readings_routes
from routes import analytics_routes, export_routes, alert_routes, group_routes
app.register_blueprint(auth_routes.bp)
app.register_blueprint(pin_routes.bp)
app.register_blueprint(settings_routes.bp)
app.register_blueprint(readings_routes.bp)
app.register_blueprint(analytics_routes.bp)
app.register_blueprint(export_routes.bp)
app.register_blueprint(alert_routes.bp)
app.register_blueprint(group_routes.bp)

if __name__ == '__main__':
    socketio.run(app, host=os.getenv('HOST', '0.0.0.0'),
                 port=int(os.getenv('PORT', 5000)))
```

### Step 1.4 — Authentication module (`src/auth.py`)
```python
import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify

SECRET = os.getenv('SECRET_KEY')
SESSION_HOURS = int(os.getenv('AUTH_SESSION_HOURS', 24))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_token(user_id: int) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token') or \
                request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        try:
            payload = jwt.decode(token, SECRET, algorithms=['HS256'])
            request.user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated
```

---

## Phase 2: Pin Configuration File (Day 1–2)

### Step 2.1 — Pin config parser (`src/pin_config.py`)
```python
import json
import os
import threading

class PinConfigManager:
    def __init__(self, config_path=None):
        self.config_path = config_path or os.getenv('PIN_CONFIG_PATH', 'pins.json')
        self.lock = threading.Lock()
        self.pins = []
        self.load()

    def load(self):
        with self.lock:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            self.pins = data.get('pins', [])
            self._validate()

    def _validate(self):
        gpio_set = set()
        adc_set = set()
        for pin in self.pins:
            if 'gpio' in pin:
                if pin['gpio'] in gpio_set:
                    raise ValueError(f"Duplicate GPIO pin: {pin['gpio']}")
                gpio_set.add(pin['gpio'])
            if 'adc_channel' in pin:
                if pin['adc_channel'] in adc_set:
                    raise ValueError(f"Duplicate ADC channel: {pin['adc_channel']}")
                adc_set.add(pin['adc_channel'])

    def get_enabled_pins(self):
        return [p for p in self.pins if p.get('enabled', False)]

    def get_pin(self, gpio):
        return next((p for p in self.pins if p.get('gpio') == gpio), None)

    def update_pin(self, gpio, updates):
        with self.lock:
            for pin in self.pins:
                if pin.get('gpio') == gpio:
                    pin.update(updates)
                    break
            self._save()

    def _save(self):
        data = {'version': 1, 'pins': self.pins}
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def sync_to_db(self, db):
        """Sync pins.json → SQLite pin_configs table"""
        for pin in self.pins:
            db.upsert_pin_config(pin)
```

### Step 2.2 — Default pin config (`pins.default.json`)
```json
{
  "version": 1,
  "description": "GPIO Pin Configuration — Copy to pins.json and edit",
  "pins": [
    {
      "gpio": 4,
      "name": "Sensor Temperature B100",
      "type": "digital_input",
      "enabled": true,
      "poll_interval_ms": 2000,
      "group": "Default",
      "thresholds": { "high": null, "low": null }
    },
    {
      "gpio": 17,
      "name": "Button 1",
      "type": "digital_input",
      "enabled": false,
      "poll_interval_ms": 100,
      "edge_trigger": "rising"
    },
    {
      "gpio": 23,
      "name": "Status LED",
      "type": "digital_output",
      "enabled": false,
      "default_state": 0
    }
  ]
}
```

---

## Phase 3: GPIO Digital Input Reading (Day 2)

### Step 3.1 — GPIO reader (`src/gpio_reader.py`)
```python
import RPi.GPIO as GPIO
import os

class GPIOReader:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self._configured_pins = {}

    def setup_input(self, gpio, pull='up'):
        pud = GPIO.PUD_UP if pull == 'up' else GPIO.PUD_DOWN
        GPIO.setup(gpio, GPIO.IN, pull_up_down=pud)
        self._configured_pins[gpio] = 'input'

    def setup_output(self, gpio, default=0):
        GPIO.setup(gpio, GPIO.OUT, initial=default)
        self._configured_pins[gpio] = 'output'

    def read(self, gpio):
        return GPIO.input(gpio)

    def write(self, gpio, state):
        GPIO.output(gpio, GPIO.HIGH if state else GPIO.LOW)

    def add_edge_callback(self, gpio, edge, callback, bounce_ms=200):
        edge_map = {
            'rising': GPIO.RISING,
            'falling': GPIO.FALLING,
            'both': GPIO.BOTH
        }
        GPIO.add_event_detect(gpio, edge_map[edge],
                              callback=callback,
                              bouncetime=bounce_ms)

    def cleanup(self):
        GPIO.cleanup()
```

### Step 3.2 — Polling scheduler (`src/polling_scheduler.py`)
```python
import threading
import time

class PollingScheduler:
    def __init__(self, reader, logger_callback, ws_callback):
        self.reader = reader
        self.log = logger_callback
        self.ws = ws_callback
        self.tasks = {}
        self.running = False

    def add_pin(self, gpio, interval_ms):
        self.tasks[gpio] = {
            'interval': interval_ms / 1000.0,
            'thread': None
        }

    def start(self):
        self.running = True
        for gpio, task in self.tasks.items():
            t = threading.Thread(target=self._poll_loop,
                                 args=(gpio, task['interval']),
                                 daemon=True)
            t.start()
            task['thread'] = t

    def stop(self):
        self.running = False

    def _poll_loop(self, gpio, interval):
        while self.running:
            value = self.reader.read(gpio)
            self.log(gpio, value)
            self.ws(gpio, value)
            time.sleep(interval)
```

---

## Phase 4: Database & Reading Storage (Day 2–3)

### Step 4.1 — Database initialization (`init_db.py`)
```python
import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'data/gpio_logger.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME)''')

    c.execute('''CREATE TABLE IF NOT EXISTS pin_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gpio_pin INTEGER UNIQUE,
        adc_channel INTEGER UNIQUE,
        name TEXT NOT NULL,
        pin_type TEXT NOT NULL,
        enabled BOOLEAN DEFAULT 1,
        poll_interval_ms INTEGER DEFAULT 1000,
        edge_trigger TEXT,
        unit TEXT DEFAULT '',
        formula TEXT,
        threshold_high REAL,
        threshold_low REAL,
        group_id INTEGER REFERENCES pin_groups(id),
        default_state INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS pin_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        color TEXT DEFAULT '#58a6ff',
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pin_config_id INTEGER NOT NULL REFERENCES pin_configs(id),
        value REAL NOT NULL,
        raw_value REAL,
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE INDEX IF NOT EXISTS idx_readings_pin_date
                 ON readings(pin_config_id, recorded_at)''')

    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pin_config_id INTEGER NOT NULL REFERENCES pin_configs(id),
        alert_type TEXT NOT NULL,
        value REAL NOT NULL,
        threshold REAL,
        acknowledged BOOLEAN DEFAULT 0,
        notified BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS feature_toggles (
        feature_key TEXT PRIMARY KEY,
        enabled BOOLEAN NOT NULL DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER REFERENCES users(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS export_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        format TEXT NOT NULL,
        pin_filter TEXT,
        date_from DATETIME,
        date_to DATETIME,
        file_path TEXT,
        status TEXT DEFAULT 'pending',
        created_by INTEGER REFERENCES users(id),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME)''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
```

---

## Phase 5: Web Dashboard — Dark Theme (Day 3)

### Step 5.1 — Base layout (`src/templates/layout.html`)
```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}GPIO Logger{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
</head>
<body>
    <nav class="sidebar">
        <div class="logo">🧾 GPIO Logger</div>
        <a href="/dashboard">Dashboard</a>
        <a href="/pin-manager">Pin Manager</a>
        <a href="/live-charts">Live Charts</a>
        <a href="/data-browser">Data Browser</a>
        <a href="/analytics">Analytics</a>
        <a href="/alerts">Alerts</a>
        <a href="/export">Export</a>
        <a href="/settings">Settings</a>
    </nav>
    <main>{% block content %}{% endblock %}</main>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

### Step 5.2 — Dark theme CSS (`static/css/style.css`)
```css
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-card: #1c2128;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --accent: #58a6ff;
    --success: #3fb950;
    --danger: #f85149;
    --warning: #d29922;
    --border: #30363d;
}
body { background: var(--bg-primary); color: var(--text-primary); font-family: -apple-system, sans-serif; }
.sidebar { position: fixed; left: 0; top: 0; width: 220px; height: 100vh; background: var(--bg-secondary); padding: 1rem; }
main { margin-left: 240px; padding: 2rem; }
.card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }
.pin-enabled { color: var(--success); }
.pin-disabled { color: var(--text-secondary); }
.alert-active { color: var(--danger); }
```

---

## Phase 6: Pin Manager UI (Day 3–4)

### Step 6.1 — Visual GPIO header layout
```javascript
// static/js/pin_manager.js
class PinManagerUI {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.socket = io();
        this.pinConfig = {};
        this.init();
    }

    init() {
        this.loadPinConfig();
        this.renderGPIOHeader();
        this.setupDragDrop();
    }

    renderGPIOHeader() {
        // Render 40-pin Raspberry Pi header layout
        const header = document.createElement('div');
        header.className = 'gpio-header';
        const pins = [
            // Left column (odd pins 1-39)
            [1, '3V3'], [3, 'GPIO2/SDA'], [5, 'GPIO3/SCL'],
            [7, 'GPIO4'], [9, 'GND'], [11, 'GPIO17'],
            // ... full 40-pin layout
        ];
        // Render interactive pin cells with click-to-configure
    }

    async loadPinConfig() {
        const resp = await fetch('/api/pins',
            { headers: { 'Authorization': `Bearer ${getToken()}` }});
        this.pinConfig = await resp.json();
        this.updatePinStates();
    }

    setupDragDrop() {
        // Drag pin to group zone for assignment
    }
}
```

---

## Phase 7: CSV & JSON Logging (Day 4)

### Step 7.1 — CSV logger (`src/csv_logger.py`)
```python
import csv
import os
from datetime import datetime

class CSVLogger:
    def __init__(self, output_dir, rotation_hours=24, max_files=365):
        self.output_dir = output_dir
        self.rotation_hours = rotation_hours
        self.max_files = max_files
        os.makedirs(output_dir, exist_ok=True)
        self._current_file = None
        self._writer = None
        self._rotate()

    def log(self, gpio, value, unit=''):
        timestamp = datetime.utcnow().isoformat()
        self._writer.writerow([timestamp, gpio, value, unit])
        self._current_file.flush()

    def _rotate(self):
        if self._current_file:
            self._current_file.close()
        filename = f"gpio_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.output_dir, filename)
        self._current_file = open(filepath, 'w', newline='')
        self._writer = csv.writer(self._current_file)
        self._writer.writerow(['timestamp', 'gpio_pin', 'value', 'unit'])
        self._cleanup_old_files()

    def _cleanup_old_files(self):
        files = sorted(os.listdir(self.output_dir))
        while len(files) > self.max_files:
            os.remove(os.path.join(self.output_dir, files.pop(0)))
```

### Step 7.2 — JSON logger (`src/json_logger.py`)
```python
import json
import os
from datetime import datetime

class JSONLogger:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def log(self, gpio, value, unit=''):
        filename = f"gpio_log_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        filepath = os.path.join(self.output_dir, filename)
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'gpio': gpio,
            'value': value,
            'unit': unit
        }
        with open(filepath, 'a') as f:
            f.write(json.dumps(record) + '\n')
```

---

## Phase 8: MCP3008 ADC Analog Support (Day 4–5)

### Step 8.1 — ADC reader (`src/adc_reader.py`)
```python
import spidev
import os

class MCP3008Reader:
    def __init__(self):
        self.spi = spidev.SpiDev()
        bus = int(os.getenv('ADC_SPI_BUS', 0))
        device = int(os.getenv('ADC_SPI_DEVICE', 0))
        self.spi.open(bus, device)
        self.spi.max_speed_hz = 1350000
        self.vref = float(os.getenv('ADC_VREF', 3.3))

    def read_channel(self, channel):
        """Read raw 10-bit value from MCP3008 channel (0-7)"""
        if channel < 0 or channel > 7:
            raise ValueError(f"Invalid channel: {channel}")
        cmd = [1, (8 + channel) << 4, 0]
        data = self.spi.xfer2(cmd)
        raw = ((data[1] & 3) << 8) + data[2]
        return raw

    def read_voltage(self, channel):
        """Read voltage from MCP3008 channel"""
        raw = self.read_channel(channel)
        return (raw / 1023.0) * self.vref

    def apply_formula(self, raw, formula):
        """Apply conversion formula from pin config"""
        value = raw  # noqa: F841 — used in eval
        return eval(formula)  # formula validated at config load time

    def close(self):
        self.spi.close()
```

---

## Phase 9: Edge-Triggered Logging (Day 5)

### Step 9.1 — Edge detector (`src/edge_detector.py`)
```python
import RPi.GPIO as GPIO
from datetime import datetime

class EdgeDetector:
    def __init__(self, logger_callback, ws_callback):
        self.log = logger_callback
        self.ws = ws_callback
        self.monitored_pins = {}

    def register(self, gpio, edge='rising', bounce_ms=200):
        edge_map = {
            'rising': GPIO.RISING,
            'falling': GPIO.FALLING,
            'both': GPIO.BOTH
        }
        GPIO.add_event_detect(
            gpio, edge_map[edge],
            callback=lambda ch: self._on_edge(ch, edge),
            bouncetime=bounce_ms
        )
        self.monitored_pins[gpio] = edge

    def _on_edge(self, channel, edge):
        value = GPIO.input(channel)
        timestamp = datetime.utcnow().isoformat()
        self.log(channel, value, event_type='edge', edge=edge)
        self.ws('pin_edge', {
            'gpio': channel,
            'edge': edge,
            'value': value,
            'timestamp': timestamp
        })

    def unregister(self, gpio):
        GPIO.remove_event_detect(gpio)
        self.monitored_pins.pop(gpio, None)
```

---

## Phase 10: Threshold Alert System (Day 5–6)

### Step 10.1 — Threshold monitor (`src/threshold_monitor.py`)
```python
import time
from datetime import datetime, timedelta

class ThresholdMonitor:
    def __init__(self, db, notification_service, cooldown_sec=300):
        self.db = db
        self.notify = notification_service
        self.cooldown = cooldown_sec
        self.last_alerts = {}

    def check(self, gpio, value, thresholds):
        if not thresholds:
            return
        high = thresholds.get('high')
        low = thresholds.get('low')
        now = datetime.utcnow()

        if high is not None and value > high:
            self._trigger(gpio, 'high_threshold', value, high, now)
        elif low is not None and value < low:
            self._trigger(gpio, 'low_threshold', value, low, now)

    def _trigger(self, gpio, alert_type, value, threshold, now):
        key = f"{gpio}_{alert_type}"
        if key in self.last_alerts:
            if (now - self.last_alerts[key]).total_seconds() < self.cooldown:
                return  # Still in cooldown

        self.last_alerts[key] = now
        self.db.insert_alert(gpio, alert_type, value, threshold)
        self.notify.send(
            f"⚠️ GPIO {gpio} Alert: {alert_type}\n"
            f"Value: {value} (threshold: {threshold})"
        )
```

---

## Phase 11: Real-Time Chart.js Visualization (Day 6)

### Step 11.1 — Live chart WebSocket bridge
```javascript
// static/js/live_charts.js
class LiveChartManager {
    constructor() {
        this.charts = {};
        this.socket = io();
        this.maxPoints = 200;

        this.socket.on('pin_reading', (data) => this.updateChart(data));
        this.socket.on('adc_reading', (data) => this.updateChart(data));
    }

    createChart(gpio, canvasId, label) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        this.charts[gpio] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: label,
                    data: [],
                    borderColor: '#58a6ff',
                    tension: 0.3,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                animation: false,
                scales: {
                    x: { display: true, ticks: { color: '#8b949e' }},
                    y: { display: true, ticks: { color: '#8b949e' }}
                },
                plugins: { legend: { labels: { color: '#e6edf3' }}}
            }
        });
    }

    updateChart(data) {
        const chart = this.charts[data.gpio || data.channel];
        if (!chart) return;
        const ds = chart.data;
        ds.labels.push(new Date(data.timestamp).toLocaleTimeString());
        ds.datasets[0].data.push(data.value || data.converted);
        if (ds.labels.length > this.maxPoints) {
            ds.labels.shift();
            ds.datasets[0].data.shift();
        }
        chart.update('none');
    }
}
```

---

## Phase 12–18: Remaining Phases

Phases 12–18 follow the same implementation pattern:
- **Phase 12** (Data Retention): Background scheduler with configurable purge policy
- **Phase 13** (Export): Format-specific generators with background job queue
- **Phase 14** (Analytics): SQL aggregation queries with Chart.js dashboard
- **Phase 15** (Pin Grouping): CRUD API + dashboard components
- **Phase 16** (Feature Toggles): Bidirectional `.env` ↔ SQLite sync with WebSocket
- **Phase 17** (Deployment): systemd service, TLS certs, file permissions
- **Phase 18** (Testing): Unit + integration tests, OWASP audit, load testing

Each phase follows the same pattern as above: module implementation → API routes → dashboard UI → WebSocket integration → testing.
