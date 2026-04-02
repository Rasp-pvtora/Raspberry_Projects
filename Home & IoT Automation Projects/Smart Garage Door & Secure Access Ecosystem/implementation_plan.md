# 🗺️ Implementation Plan — Smart Garage Door & Secure Access Ecosystem

---

## Phase 1: Project Setup & Authentication (Day 1)

### Step 1.1 — Initialize project
```bash
mkdir -p src/routes src/templates static/css static/js data deploy docs tests
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
Pillow==10.4.*
picamera2==0.3.*
opencv-python-headless==4.9.*
openalpr==2.3.*
adafruit-circuitpython-dht==4.0.*
adafruit-circuitpython-ina219==3.4.*
RPi.GPIO==0.7.*
python-telegram-bot==21.*
slack-sdk==3.33.*
pymsteams==0.2.*
qrcode==8.0.*
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

# Import routes after app creation
from routes import auth_routes, door_routes, settings_routes
app.register_blueprint(auth_routes.bp)
app.register_blueprint(door_routes.bp)
app.register_blueprint(settings_routes.bp)

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
        token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
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

## Phase 2: GPIO Relay Control & Reed Switches (Day 1–2)

### Step 2.1 — GPIO controller (`src/gpio_controller.py`)
```python
import RPi.GPIO as GPIO
import os
import threading

class DoorController:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.doors = {}
        self._setup_door(1, int(os.getenv('RELAY_DOOR1_GPIO', 17)),
                         int(os.getenv('REED_DOOR1_GPIO', 22)))
        if os.getenv('ENABLE_MULTI_DOOR', 'false').lower() == 'true':
            self._setup_door(2, int(os.getenv('RELAY_DOOR2_GPIO', 27)),
                             int(os.getenv('REED_DOOR2_GPIO', 23)))

    def _setup_door(self, door_id, relay_pin, reed_pin):
        GPIO.setup(relay_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(reed_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.doors[door_id] = {'relay': relay_pin, 'reed': reed_pin}

    def open_door(self, door_id):
        pin = self.doors[door_id]['relay']
        GPIO.output(pin, GPIO.HIGH)

    def close_door(self, door_id):
        pin = self.doors[door_id]['relay']
        GPIO.output(pin, GPIO.LOW)

    def get_status(self, door_id):
        pin = self.doors[door_id]['reed']
        return 'open' if GPIO.input(pin) == GPIO.HIGH else 'closed'

    def cleanup(self):
        GPIO.cleanup()
```

### Step 2.2 — Auto-close background thread
```python
import time

class AutoCloseManager:
    def __init__(self, controller, delay_sec, callback):
        self.controller = controller
        self.delay = int(os.getenv('AUTO_CLOSE_DELAY_SEC', delay_sec))
        self.callback = callback
        self.timers = {}

    def schedule_close(self, door_id):
        self.cancel(door_id)
        timer = threading.Timer(self.delay, self._execute_close, [door_id])
        timer.start()
        self.timers[door_id] = timer

    def cancel(self, door_id):
        if door_id in self.timers:
            self.timers[door_id].cancel()

    def _execute_close(self, door_id):
        self.controller.close_door(door_id)
        self.callback(door_id, 'auto_close')
```

---

## Phase 3: Database & Event Logging (Day 2)

### Step 3.1 — Database initialization (`init_db.py`)
```python
import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'data/garage.db')

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

    c.execute('''CREATE TABLE IF NOT EXISTS doors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        relay_gpio INTEGER NOT NULL,
        reed_gpio INTEGER NOT NULL,
        status TEXT DEFAULT 'closed',
        last_changed DATETIME)''')

    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        door_id INTEGER REFERENCES doors(id),
        event_type TEXT NOT NULL,
        trigger_source TEXT NOT NULL,
        plate_number TEXT,
        plate_photo_path TEXT,
        user_id INTEGER REFERENCES users(id),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS feature_toggles (
        feature_key TEXT PRIMARY KEY,
        enabled BOOLEAN NOT NULL DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER REFERENCES users(id))''')

    # Create remaining tables...
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
```

---

## Phase 4: Web Dashboard — Dark Theme (Day 2–3)

### Step 4.1 — Base layout (`src/templates/layout.html`)
```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Garage Access{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
</head>
<body>
    <nav class="sidebar">
        <div class="logo">🚪 GaragePi</div>
        <a href="/dashboard">Dashboard</a>
        <a href="/camera">Live Camera</a>
        <a href="/access-log">Access Log</a>
        <a href="/guest-codes">Guest Codes</a>
        <a href="/analytics">Analytics</a>
        <a href="/climate">Climate</a>
        <a href="/settings">Settings</a>
        <a href="/emergency" class="emergency-btn">🆘 Emergency</a>
    </nav>
    <main>{% block content %}{% endblock %}</main>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

### Step 4.2 — Dark theme CSS (`static/css/style.css`)
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
.status-open { color: var(--success); }
.status-closed { color: var(--danger); }
```

---

## Phase 5: ALPR Integration (Day 3–4)

### Step 5.1 — ALPR engine (`src/alpr_engine.py`)
```python
import cv2
import os
from picamera2 import Picamera2

class ALPREngine:
    def __init__(self, whitelist_db):
        self.confidence_threshold = int(os.getenv('ALPR_CONFIDENCE_THRESHOLD', 75))
        self.region = os.getenv('ALPR_REGION', 'eu')
        self.check_interval = int(os.getenv('ALPR_CHECK_INTERVAL_SEC', 2))
        self.whitelist_db = whitelist_db
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_still_configuration())

    def detect_plate(self, frame):
        """Run OCR on frame, return (plate_text, confidence) or None."""
        # OpenALPR or Tesseract pipeline
        # Returns highest confidence result above threshold
        pass

    def check_whitelist(self, plate_text):
        """Check if plate is in whitelist database."""
        return self.whitelist_db.is_whitelisted(plate_text)

    def run_detection_loop(self, on_match_callback, on_unknown_callback):
        """Continuous detection loop — runs in background thread."""
        import time
        self.camera.start()
        consecutive_reads = {}
        while True:
            frame = self.camera.capture_array()
            result = self.detect_plate(frame)
            if result:
                plate, confidence = result
                consecutive_reads[plate] = consecutive_reads.get(plate, 0) + 1
                if consecutive_reads[plate] >= 3:  # Multi-frame verification
                    if self.check_whitelist(plate):
                        on_match_callback(plate, confidence, frame)
                    else:
                        on_unknown_callback(plate, confidence, frame)
                    consecutive_reads.clear()
            time.sleep(self.check_interval)
```

---

## Phase 6: Camera Stream & Night Mode (Day 4)

### Step 6.1 — MJPEG stream route
```python
from flask import Response

def generate_frames(camera):
    while True:
        frame = camera.capture_array()
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@bp.route('/api/camera/stream')
@require_auth
def video_feed():
    return Response(generate_frames(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
```

### Step 6.2 — Night mode IR control
```python
def set_night_mode(enabled):
    ir_pin = int(os.getenv('NIGHT_IR_GPIO', 18))
    GPIO.setup(ir_pin, GPIO.OUT)
    GPIO.output(ir_pin, GPIO.HIGH if enabled else GPIO.LOW)
```

---

## Phase 7: Notification System (Day 5)

### Step 7.1 — Notification dispatcher (`src/notification_service.py`)
```python
import os
import smtplib
from email.mime.text import MIMEText

class NotificationService:
    def __init__(self):
        self.channels = []
        if os.getenv('TELEGRAM_BOT_TOKEN'):
            self.channels.append(self._send_telegram)
        if os.getenv('SLACK_WEBHOOK_URL'):
            self.channels.append(self._send_slack)
        if os.getenv('TEAMS_WEBHOOK_URL'):
            self.channels.append(self._send_teams)
        if os.getenv('SMTP_USER'):
            self.channels.append(self._send_email)

    def notify(self, title, message, priority='normal'):
        for channel in self.channels:
            try:
                channel(title, message)
            except Exception as e:
                print(f"Notification error: {e}")

    def _send_telegram(self, title, message):
        import telegram
        bot = telegram.Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        bot.send_message(chat_id=os.getenv('TELEGRAM_CHAT_ID'),
                         text=f"*{title}*\n{message}", parse_mode='Markdown')

    def _send_slack(self, title, message):
        from slack_sdk.webhook import WebhookClient
        webhook = WebhookClient(os.getenv('SLACK_WEBHOOK_URL'))
        webhook.send(text=f"*{title}*\n{message}")

    def _send_teams(self, title, message):
        import pymsteams
        msg = pymsteams.connectorcard(os.getenv('TEAMS_WEBHOOK_URL'))
        msg.title(title)
        msg.text(message)
        msg.send()

    def _send_email(self, title, message):
        msg = MIMEText(message)
        msg['Subject'] = title
        msg['From'] = os.getenv('SMTP_USER')
        msg['To'] = os.getenv('SMTP_TO')
        with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT'))) as s:
            s.starttls()
            s.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
            s.send_message(msg)
```

---

## Phase 8: Feature Toggle System (Day 5)

### Step 8.1 — Toggle service (`src/feature_toggles.py`)
```python
import os
import sqlite3

class FeatureToggleService:
    FEATURES = [
        'ENABLE_ALPR', 'ENABLE_GEOFENCING', 'ENABLE_DELIVERY_MODE',
        'ENABLE_NOTIFICATIONS', 'ENABLE_VACATION_MODE', 'ENABLE_TAMPER_DETECTION',
        'ENABLE_VOICE_CONTROL', 'ENABLE_NIGHT_CAMERA', 'ENABLE_CLIMATE_MONITOR',
        'ENABLE_MULTI_DOOR', 'ENABLE_GUEST_ACCESS', 'ENABLE_UPS_MONITOR',
        'ENABLE_AUTO_CLOSE', 'ENABLE_ANALYTICS', 'ENABLE_EMERGENCY_LOCK'
    ]

    def __init__(self, db_path):
        self.db_path = db_path
        self._sync_from_env()

    def _sync_from_env(self):
        """Initialize DB toggles from .env values on startup."""
        conn = sqlite3.connect(self.db_path)
        for key in self.FEATURES:
            val = os.getenv(key, 'false').lower() == 'true'
            conn.execute('''INSERT OR IGNORE INTO feature_toggles (feature_key, enabled)
                           VALUES (?, ?)''', (key, val))
        conn.commit()
        conn.close()

    def is_enabled(self, feature_key):
        conn = sqlite3.connect(self.db_path)
        row = conn.execute('SELECT enabled FROM feature_toggles WHERE feature_key = ?',
                          (feature_key,)).fetchone()
        conn.close()
        return bool(row[0]) if row else False

    def set_toggle(self, feature_key, enabled, user_id=None):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''UPDATE feature_toggles SET enabled = ?, updated_at = CURRENT_TIMESTAMP,
                       updated_by = ? WHERE feature_key = ?''',
                    (enabled, user_id, feature_key))
        conn.commit()
        conn.close()
        self._update_env_file(feature_key, enabled)

    def _update_env_file(self, key, enabled):
        """Sync toggle change back to .env file."""
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith(f'{key}='):
                        f.write(f'{key}={"true" if enabled else "false"}\n')
                    else:
                        f.write(line)

    def get_all(self):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute('SELECT feature_key, enabled FROM feature_toggles').fetchall()
        conn.close()
        return {row[0]: bool(row[1]) for row in rows}
```

### Step 8.2 — Settings route with dashboard toggle API
```python
@bp.route('/api/settings/features', methods=['GET'])
@require_auth
def get_features():
    return jsonify(toggle_service.get_all())

@bp.route('/api/settings/features', methods=['PUT'])
@require_auth
def update_features():
    data = request.get_json()
    updated = []
    for key, val in data.items():
        if key in FeatureToggleService.FEATURES:
            toggle_service.set_toggle(key, bool(val), request.user_id)
            updated.append(key)
            socketio.emit('feature_toggled', {'feature': key, 'enabled': bool(val)})
    return jsonify({'updated': updated})
```

---

## Phase 9: Guest Access System (Day 6)

### Step 9.1 — Guest code generator (`src/guest_access.py`)
```python
import secrets
import qrcode
from io import BytesIO

class GuestAccessManager:
    def generate_pin(self, door_id, valid_hours, max_uses=1, created_by=None):
        code = f"{secrets.randbelow(900000) + 100000}"
        # Store in guest_codes table with valid_from, valid_until, max_uses
        return code

    def generate_qr(self, code):
        qr = qrcode.make(f"garage-access:{code}")
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        return buffer.getvalue()

    def validate_code(self, code):
        # Check: exists, not revoked, within time bounds, use_count < max_uses
        # If valid: increment use_count, return door_id
        # If invalid: return None
        pass
```

---

## Phase 10: Climate & UPS Monitoring (Day 6–7)

### Step 10.1 — Climate monitor (`src/climate_monitor.py`)
```python
import adafruit_dht
import board
import os

class ClimateMonitor:
    def __init__(self):
        gpio = int(os.getenv('DHT22_GPIO', 4))
        pin_map = {4: board.D4, 17: board.D17, 27: board.D27}
        self.dht = adafruit_dht.DHT22(pin_map.get(gpio, board.D4))

    def read(self):
        try:
            return {
                'temperature_c': self.dht.temperature,
                'humidity_pct': self.dht.humidity
            }
        except RuntimeError:
            return None
```

### Step 10.2 — UPS monitor (`src/ups_monitor.py`)
```python
from adafruit_ina219 import INA219
import board
import busio

class UPSMonitor:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        addr = int(os.getenv('UPS_I2C_ADDRESS', '0x40'), 16)
        self.sensor = INA219(i2c, addr=addr)

    def read(self):
        return {
            'voltage_v': round(self.sensor.bus_voltage, 2),
            'current_ma': round(self.sensor.current, 2),
            'power_mw': round(self.sensor.power, 2)
        }
```

---

## Phase 11: Analytics Engine (Day 7)

### Step 11.1 — Analytics aggregation (`src/analytics.py`)
```python
import sqlite3
from collections import Counter

class AnalyticsEngine:
    def __init__(self, db_path):
        self.db_path = db_path

    def summary(self, period_days=7):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute('''SELECT event_type, trigger_source,
               strftime('%H', timestamp) as hour FROM events
               WHERE timestamp > datetime('now', ?)''',
               (f'-{period_days} days',)).fetchall()
        conn.close()
        hours = [int(r[2]) for r in rows]
        sources = Counter(r[1] for r in rows)
        return {
            'total_events': len(rows),
            'peak_hour': max(set(hours), key=hours.count) if hours else None,
            'by_source': dict(sources)
        }
```

---

## Phase 12: Geofencing & Voice Control (Day 8–9)

### Step 12.1 — Geofencing endpoint
```python
from math import radians, sin, cos, sqrt, atan2

GARAGE_LAT = float(os.getenv('GARAGE_LAT', 0))
GARAGE_LON = float(os.getenv('GARAGE_LON', 0))
GEOFENCE_RADIUS = int(os.getenv('GEOFENCE_RADIUS_METERS', 50))

@bp.route('/api/geofence/ping', methods=['POST'])
@require_auth
def geofence_ping():
    data = request.get_json()
    dist = haversine(data['lat'], data['lon'], GARAGE_LAT, GARAGE_LON)
    if dist <= GEOFENCE_RADIUS:
        door_controller.open_door(1)
        return jsonify({'action': 'opened', 'distance_m': dist})
    return jsonify({'action': 'none', 'distance_m': dist})
```

---

## Phase 13: Vacation Mode & Emergency Lock (Day 9)

### Step 13.1 — Vacation mode scheduler
```python
import random

class VacationMode:
    def __init__(self, controller):
        self.controller = controller
        self.min_interval = int(os.getenv('VACATION_MIN_INTERVAL_MIN', 60))
        self.max_interval = int(os.getenv('VACATION_MAX_INTERVAL_MIN', 240))

    def schedule_next(self, door_id):
        delay = random.randint(self.min_interval, self.max_interval) * 60
        action = random.choice(['open', 'close'])
        # Schedule via threading.Timer
        return {'door_id': door_id, 'action': action, 'delay_sec': delay}
```

### Step 13.2 — Emergency lock
```python
@bp.route('/api/doors/lock-all', methods=['POST'])
@require_auth
def emergency_lock():
    for door_id in door_controller.doors:
        door_controller.close_door(door_id)
    notification_service.notify("🆘 EMERGENCY LOCK", "All doors locked immediately!", priority='critical')
    return jsonify({'status': 'locked', 'doors_affected': len(door_controller.doors)})
```

---

## Phase 14: Multi-Door Support & Deployment (Day 10)

### Step 14.1 — Deploy script (`deploy/deploy_to_pi.sh`)
```bash
#!/bin/bash
set -e
PI_HOST="rasp-pi"
REMOTE_DIR="/opt/garage-access"

echo "🚀 Deploying Smart Garage Door..."
ssh $PI_HOST "mkdir -p $REMOTE_DIR"
rsync -avz --exclude='venv' --exclude='data/*.db' ./ $PI_HOST:$REMOTE_DIR/
ssh $PI_HOST "cd $REMOTE_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
ssh $PI_HOST "sudo systemctl restart garage-door"
echo "✅ Deployment complete!"
```

### Step 14.2 — Systemd service (`deploy/garage-door.service`)
```ini
[Unit]
Description=Smart Garage Door Access System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/garage-access
ExecStart=/opt/garage-access/venv/bin/python -m src.app
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

---

## Phase 15: Testing & Hardening (Day 10–11)

### Step 15.1 — Test authentication
```python
def test_login_rate_limit(client):
    for i in range(11):
        resp = client.post('/api/auth/login',
                          json={'username': 'admin', 'password': 'wrong'})
    assert resp.status_code == 429  # Too Many Requests

def test_jwt_expiry(client):
    # Create token with 0-second expiry, ensure 401
    pass
```

### Step 15.2 — Test feature toggles via dashboard
```python
def test_toggle_feature(auth_client):
    resp = auth_client.put('/api/settings/features',
                           json={'ENABLE_ALPR': False})
    assert resp.status_code == 200
    assert 'ENABLE_ALPR' in resp.json['updated']

    # Verify ALPR is now disabled
    resp = auth_client.get('/api/settings/features')
    assert resp.json['ENABLE_ALPR'] is False
```

### Step 15.3 — Security checklist
- [ ] All queries use parameterized statements
- [ ] Passwords hashed with bcrypt (cost factor ≥ 12)
- [ ] JWT tokens in httpOnly secure cookies
- [ ] HTTPS enforced on all routes
- [ ] .env file has 600 permissions
- [ ] Rate limiting on all auth endpoints
- [ ] Input validation on all API inputs
- [ ] CORS restricted to known origins
- [ ] No secrets in git history
- [ ] Camera stream requires authentication
