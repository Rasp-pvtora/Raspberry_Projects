# 🗺️ Implementation Plan — Smart Pet Feeder & Health Monitor

---

## Phase 1: Project Setup & Authentication (Day 1)

### Step 1.1 — Initialize project structure
```bash
mkdir -p src/routes src/templates static/css static/js data/pet_photos models deploy docs tests
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
APScheduler==3.10.*
picamera2==0.3.*
opencv-python-headless==4.9.*
tflite-runtime==2.14.*
RPi.GPIO==0.7.*
hx711==1.1.*
mfrc522==0.0.7
adafruit-circuitpython-dht==4.0.*
python-telegram-bot==21.*
qrcode==8.0.*
reportlab==4.2.*
PyAudio==0.2.*
pygame==2.5.*
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

from routes import auth_routes, pet_routes, feed_routes, settings_routes
app.register_blueprint(auth_routes.bp)
app.register_blueprint(pet_routes.bp)
app.register_blueprint(feed_routes.bp)
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

## Phase 2: Servo Food Dispenser & Calibration (Day 1–2)

### Step 2.1 — Servo controller (`src/servo_controller.py`)
```python
import RPi.GPIO as GPIO
import time
import os

class ServoController:
    def __init__(self, gpio_pin, freq=50):
        self.pin = gpio_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, freq)
        self.pwm.start(0)

    def dispense(self, portion_grams, calibration_factor):
        """Rotate servo proportional to desired grams."""
        rotation_time = portion_grams / calibration_factor
        max_rotation = float(os.getenv('MAX_PORTION_GRAMS', 200)) / calibration_factor
        rotation_time = min(rotation_time, max_rotation)

        self.pwm.ChangeDutyCycle(7.5)  # Mid position → dispense
        time.sleep(rotation_time)
        self.pwm.ChangeDutyCycle(2.5)  # Return to closed
        time.sleep(0.5)
        self.pwm.ChangeDutyCycle(0)

    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup(self.pin)

class FoodDispenser(ServoController):
    def __init__(self):
        super().__init__(int(os.getenv('SERVO_FOOD_GPIO', 12)))
        self.calibration_factor = float(os.getenv('LOAD_CELL_CALIBRATION_FACTOR', 420.5))

    def feed(self, portion_grams):
        self.dispense(portion_grams, self.calibration_factor)
```

### Step 2.2 — Calibration script (`calibrate_scale.py`)
```python
from hx711 import HX711
import RPi.GPIO as GPIO
import os

def calibrate():
    hx = HX711(dout_pin=int(os.getenv('HX711_DT_GPIO', 5)),
               pd_sck_pin=int(os.getenv('HX711_SCK_GPIO', 6)))
    hx.reset()

    print("Remove all weight from scale. Press Enter...")
    input()
    hx.tare()
    offset = hx.get_offset()
    print(f"Offset: {offset}")

    print("Place known weight (e.g., 100g) on scale. Press Enter...")
    input()
    known_weight = float(input("Enter weight in grams: "))
    raw = hx.get_raw_data(times=10)
    avg_raw = sum(raw) / len(raw)
    factor = (avg_raw - offset) / known_weight
    print(f"Calibration factor: {factor}")
    print(f"Update .env: LOAD_CELL_CALIBRATION_FACTOR={factor}")
    print(f"Update .env: LOAD_CELL_OFFSET={offset}")

if __name__ == '__main__':
    calibrate()
    GPIO.cleanup()
```

---

## Phase 3: Scheduled Feeding Engine (Day 2)

### Step 3.1 — Feeding scheduler (`src/feeding_scheduler.py`)
```python
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import os

class FeedingScheduler:
    def __init__(self, dispenser, db_path, socketio):
        self.dispenser = dispenser
        self.db_path = db_path
        self.socketio = socketio
        self.scheduler = BackgroundScheduler()

    def load_schedules(self):
        conn = sqlite3.connect(self.db_path)
        pets = conn.execute('SELECT id, name, default_portion_g, feed_times FROM pets WHERE active = 1').fetchall()
        conn.close()

        for pet_id, name, portion, times_json in pets:
            import json
            times = json.loads(times_json) if times_json else []
            for t in times:
                hour, minute = map(int, t.split(':'))
                self.scheduler.add_job(
                    self._feed_pet, 'cron', hour=hour, minute=minute,
                    args=[pet_id, name, portion],
                    id=f'feed_{pet_id}_{t}', replace_existing=True)

    def _feed_pet(self, pet_id, name, portion_g):
        self.dispenser.feed(portion_g)
        self.socketio.emit('feeding_started', {
            'pet_id': pet_id, 'portion_g': portion_g})
        # Log to database
        conn = sqlite3.connect(self.db_path)
        conn.execute('''INSERT INTO feedings (pet_id, portion_grams, trigger_type)
                       VALUES (?, ?, 'scheduled')''', (pet_id, portion_g))
        conn.commit()
        conn.close()

    def start(self):
        self.load_schedules()
        self.scheduler.start()

    def reload(self):
        self.scheduler.remove_all_jobs()
        self.load_schedules()
```

---

## Phase 4: Database & Pet CRUD (Day 2–3)

### Step 4.1 — Database initialization (`init_db.py`)
```python
import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'data/petfeeder.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME)''')

    c.execute('''CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        species TEXT DEFAULT 'dog',
        breed TEXT,
        birth_date DATE,
        photo_path TEXT,
        rfid_tag_uid TEXT UNIQUE,
        default_portion_g REAL NOT NULL DEFAULT 50,
        feed_times TEXT,
        dietary_notes TEXT,
        active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS feedings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER REFERENCES pets(id),
        portion_grams REAL NOT NULL,
        trigger_type TEXT NOT NULL,
        dispensed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        consumed_grams REAL,
        eating_duration_sec INTEGER,
        eating_speed_g_sec REAL,
        slow_feed_triggered BOOLEAN DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS weight_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER REFERENCES pets(id),
        weight_grams REAL NOT NULL,
        measured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        source TEXT DEFAULT 'auto')''')

    c.execute('''CREATE TABLE IF NOT EXISTS health_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER REFERENCES pets(id),
        alert_type TEXT NOT NULL,
        severity TEXT DEFAULT 'warning',
        message TEXT NOT NULL,
        acknowledged BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS feature_toggles (
        feature_key TEXT PRIMARY KEY,
        enabled BOOLEAN NOT NULL DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER REFERENCES users(id))''')

    # Additional tables: water_readings, hopper_readings, medication_schedules, etc.
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
```

---

## Phase 5: Web Dashboard — Dark Theme (Day 3)

### Step 5.1 — Dashboard with pet cards
```html
{% extends "layout.html" %}
{% block content %}
<div class="dashboard-grid">
    {% for pet in pets %}
    <div class="card pet-card">
        <img src="{{ pet.photo_path or '/static/img/default-pet.png' }}" alt="{{ pet.name }}">
        <h3>{{ pet.name }}</h3>
        <p class="species">{{ pet.species }} — {{ pet.breed }}</p>
        <div class="next-feed">Next feed: <span id="countdown-{{ pet.id }}">--:--</span></div>
        <div class="stats">
            <span>Portion: {{ pet.default_portion_g }}g</span>
            <span>Weight: {{ pet.last_weight or '--' }}g</span>
        </div>
        <button class="btn btn-primary" onclick="feedNow({{ pet.id }})">🍽️ Feed Now</button>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

### Step 5.2 — Dark theme CSS
```css
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-card: #1c2128;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --accent: #f0883e;
    --success: #3fb950;
    --danger: #f85149;
    --warning: #d29922;
    --border: #30363d;
}
body { background: var(--bg-primary); color: var(--text-primary); }
.pet-card { text-align: center; }
.pet-card img { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; }
.dashboard-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; }
```

---

## Phase 6: Weight Tracking — HX711 Load Cell (Day 3–4)

### Step 6.1 — Weight tracker (`src/weight_tracker.py`)
```python
from hx711 import HX711
import os
import sqlite3
import threading
import time

class WeightTracker:
    def __init__(self, db_path, socketio):
        self.hx = HX711(
            dout_pin=int(os.getenv('HX711_DT_GPIO', 5)),
            pd_sck_pin=int(os.getenv('HX711_SCK_GPIO', 6)))
        self.offset = int(os.getenv('LOAD_CELL_OFFSET', 8340))
        self.factor = float(os.getenv('LOAD_CELL_CALIBRATION_FACTOR', 420.5))
        self.hx.set_offset(self.offset)
        self.hx.set_scale_ratio(self.factor)
        self.db_path = db_path
        self.socketio = socketio

    def read_weight(self):
        """Read current weight in grams."""
        raw = self.hx.get_weight_mean(times=5)
        return max(0, round(raw, 1))

    def log_weight(self, pet_id, weight_g, source='auto'):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''INSERT INTO weight_logs (pet_id, weight_grams, source)
                       VALUES (?, ?, ?)''', (pet_id, weight_g, source))
        conn.commit()
        conn.close()
        self.socketio.emit('weight_update', {'pet_id': pet_id, 'weight_g': weight_g})
```

---

## Phase 7: Eating Speed Analysis (Day 4)

### Step 7.1 — Eating analyzer (`src/eating_analyzer.py`)
```python
import time
import os

class EatingAnalyzer:
    def __init__(self, weight_tracker, dispenser, socketio):
        self.weight_tracker = weight_tracker
        self.dispenser = dispenser
        self.socketio = socketio
        self.slow_feed_threshold = float(os.getenv('SLOW_FEED_THRESHOLD_G_PER_SEC', 5))

    def monitor_eating(self, pet_id, portion_g):
        """Monitor bowl weight decrease after dispensing."""
        start_weight = self.weight_tracker.read_weight()
        start_time = time.time()
        samples = []

        while True:
            time.sleep(2)
            current = self.weight_tracker.read_weight()
            elapsed = time.time() - start_time
            consumed = start_weight - current

            if consumed > 0:
                speed = consumed / elapsed
                samples.append(speed)

                if speed > self.slow_feed_threshold:
                    self.socketio.emit('slow_feed_warning', {'pet_id': pet_id, 'speed': round(speed, 2)})

            # Eating complete if weight stable for 30s
            if len(samples) > 15 and abs(samples[-1] - samples[-5]) < 0.1:
                break
            if elapsed > 600:  # 10min timeout
                break

        total_consumed = start_weight - self.weight_tracker.read_weight()
        duration = time.time() - start_time
        avg_speed = total_consumed / duration if duration > 0 else 0

        return {
            'consumed_grams': round(total_consumed, 1),
            'duration_sec': int(duration),
            'avg_speed_g_sec': round(avg_speed, 2),
            'slow_feed_triggered': avg_speed > self.slow_feed_threshold
        }
```

---

## Phase 8: Water Level & Hopper Monitor (Day 4)

### Step 8.1 — Sensors (`src/water_monitor.py`)
```python
import RPi.GPIO as GPIO
import time
import os

class WaterMonitor:
    def __init__(self):
        self.trig = int(os.getenv('ULTRASONIC_TRIG_GPIO', 23))
        self.echo = int(os.getenv('ULTRASONIC_ECHO_GPIO', 24))
        self.full_cm = float(os.getenv('WATER_FULL_CM', 15))
        self.low_threshold = float(os.getenv('WATER_LOW_THRESHOLD_CM', 3))
        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)

    def read_level(self):
        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)
        start = time.time()
        while GPIO.input(self.echo) == 0:
            start = time.time()
        while GPIO.input(self.echo) == 1:
            end = time.time()
        distance = (end - start) * 17150
        level_cm = max(0, self.full_cm - distance)
        level_pct = min(100, (level_cm / self.full_cm) * 100)
        return {'level_cm': round(level_cm, 1), 'level_pct': round(level_pct), 'is_low': level_cm < self.low_threshold}
```

---

## Phase 9: Pi Camera & Night Mode (Day 5)

### Step 9.1 — MJPEG stream with IR control
```python
from picamera2 import Picamera2
import cv2
import RPi.GPIO as GPIO
import os

camera = Picamera2()
camera.configure(camera.create_video_configuration(
    main={"size": tuple(map(int, os.getenv('CAMERA_RESOLUTION', '1280x720').split('x')))}))
camera.start()

def set_night_mode(enabled):
    ir_pin = int(os.getenv('IR_LED_GPIO', 18))
    GPIO.setup(ir_pin, GPIO.OUT)
    GPIO.output(ir_pin, GPIO.HIGH if enabled else GPIO.LOW)

def generate_frames():
    while True:
        frame = camera.capture_array()
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
```

---

## Phase 10: Pet Facial Recognition (Day 5–6)

### Step 10.1 — Training script (`train_pet_model.py`)
```python
import tensorflow as tf
import os

def train(photos_dir, epochs=20):
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    base_model.trainable = False

    model = tf.keras.Sequential([
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(len(os.listdir(photos_dir)), activation='softmax')
    ])

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    data = tf.keras.utils.image_dataset_from_directory(
        photos_dir, image_size=(224, 224), batch_size=16)

    model.fit(data, epochs=epochs)

    # Export to TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open('models/pet_model.tflite', 'wb') as f:
        f.write(tflite_model)
    print("Model exported to models/pet_model.tflite")
```

### Step 10.2 — Inference engine (`src/pet_recognition.py`)
```python
import tflite_runtime.interpreter as tflite
import numpy as np
import cv2
import os

class PetRecognition:
    def __init__(self):
        model_path = os.getenv('PET_MODEL_PATH', 'models/pet_model.tflite')
        self.threshold = int(os.getenv('PET_CONFIDENCE_THRESHOLD', 70))
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

    def identify(self, frame):
        resized = cv2.resize(frame, (224, 224))
        input_data = np.expand_dims(resized.astype(np.float32) / 255.0, axis=0)
        input_details = self.interpreter.get_input_details()
        output_details = self.interpreter.get_output_details()
        self.interpreter.set_tensor(input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(output_details[0]['index'])[0]
        confidence = int(np.max(output) * 100)
        pet_index = int(np.argmax(output))
        if confidence >= self.threshold:
            return pet_index, confidence
        return None, confidence
```

---

## Phase 11: RFID Collar System (Day 6)

### Step 11.1 — RFID reader (`src/rfid_reader.py`)
```python
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

class RFIDReader:
    def __init__(self):
        self.reader = SimpleMFRC522()

    def read_tag(self):
        try:
            uid, _ = self.reader.read_no_block()
            return str(uid) if uid else None
        except Exception:
            return None

    def start_monitoring(self, on_tag_callback):
        import time
        while True:
            uid = self.read_tag()
            if uid:
                on_tag_callback(uid)
            time.sleep(0.5)
```

---

## Phase 12: Health Alerts & Notifications (Day 7)

### Step 12.1 — Health alert engine (`src/health_alerts.py`)
```python
import sqlite3
import os
from datetime import datetime, timedelta

class HealthAlertEngine:
    def __init__(self, db_path, notification_service, socketio):
        self.db_path = db_path
        self.notifier = notification_service
        self.socketio = socketio
        self.missed_threshold_h = int(os.getenv('MISSED_MEAL_THRESHOLD_HOURS', 4))
        self.weight_alert_pct = float(os.getenv('WEIGHT_CHANGE_ALERT_PCT', 10))
        self.overeat_mult = float(os.getenv('OVEREATING_MULTIPLIER', 1.5))

    def check_missed_meals(self, pet_id):
        conn = sqlite3.connect(self.db_path)
        last = conn.execute('''SELECT MAX(dispensed_at) FROM feedings WHERE pet_id = ?''',
                           (pet_id,)).fetchone()[0]
        conn.close()
        if last:
            last_dt = datetime.fromisoformat(last)
            if datetime.now() - last_dt > timedelta(hours=self.missed_threshold_h):
                self._create_alert(pet_id, 'missed_meal', 'warning',
                    f'No feeding detected in {self.missed_threshold_h}h')

    def check_weight_anomaly(self, pet_id):
        conn = sqlite3.connect(self.db_path)
        weights = conn.execute('''SELECT weight_grams FROM weight_logs
                                 WHERE pet_id = ? ORDER BY measured_at DESC LIMIT 10''',
                              (pet_id,)).fetchall()
        conn.close()
        if len(weights) >= 2:
            latest, previous = weights[0][0], weights[1][0]
            pct_change = abs(latest - previous) / previous * 100
            if pct_change > self.weight_alert_pct:
                direction = 'gained' if latest > previous else 'lost'
                self._create_alert(pet_id, 'weight_change', 'warning',
                    f'Pet {direction} {pct_change:.1f}% weight ({previous}g → {latest}g)')

    def _create_alert(self, pet_id, alert_type, severity, message):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''INSERT INTO health_alerts (pet_id, alert_type, severity, message)
                       VALUES (?, ?, ?, ?)''', (pet_id, alert_type, severity, message))
        conn.commit()
        conn.close()
        self.notifier.notify(f"🚨 Pet Health Alert: {alert_type}", message)
        self.socketio.emit('health_alert', {
            'pet_id': pet_id, 'type': alert_type, 'severity': severity})
```

---

## Phase 13: Feature Toggle System (Day 7)

### Step 13.1 — Toggle service (same pattern as Garage Door project)
```python
class FeatureToggleService:
    FEATURES = [
        'ENABLE_SCHEDULED_FEEDING', 'ENABLE_PORTION_CONTROL', 'ENABLE_PET_RECOGNITION',
        'ENABLE_MULTI_PET', 'ENABLE_RFID_FEEDING', 'ENABLE_WEIGHT_TRACKING',
        'ENABLE_EATING_ANALYSIS', 'ENABLE_HEALTH_ALERTS', 'ENABLE_WATER_MONITOR',
        'ENABLE_HOPPER_MONITOR', 'ENABLE_TREAT_LAUNCHER', 'ENABLE_MEDICATION',
        'ENABLE_LIVE_CAMERA', 'ENABLE_TWO_WAY_AUDIO', 'ENABLE_MOTION_DETECT',
        'ENABLE_ANALYTICS'
    ]
    # Same implementation as Phase 8 in Garage Door project
    # Dashboard ↔ .env bidirectional sync
```

---

## Phase 14: Treat Launcher & Medication (Day 8)

### Step 14.1 — Treat launcher (`src/treat_launcher.py`)
```python
from servo_controller import ServoController
import os

class TreatLauncher:
    def __init__(self):
        self.servo = ServoController(int(os.getenv('SERVO_TREAT_GPIO', 13)))

    def launch(self):
        """Quick flick to launch a single treat."""
        self.servo.pwm.ChangeDutyCycle(12.5)  # Max angle
        import time
        time.sleep(0.3)
        self.servo.pwm.ChangeDutyCycle(2.5)   # Return
        time.sleep(0.3)
        self.servo.pwm.ChangeDutyCycle(0)
        return True
```

### Step 14.2 — Medication dispenser (`src/medication_dispenser.py`)
```python
class MedicationDispenser:
    def __init__(self):
        self.servo = ServoController(int(os.getenv('SERVO_MEDICATION_GPIO', 19)))

    def dispense(self):
        """Precise single-dose medication dispense."""
        self.servo.pwm.ChangeDutyCycle(7.5)
        import time
        time.sleep(0.5)
        self.servo.pwm.ChangeDutyCycle(2.5)
        time.sleep(0.3)
        self.servo.pwm.ChangeDutyCycle(0)
```

---

## Phase 15: Two-Way Audio (Day 8–9)

### Step 15.1 — Audio manager (`src/audio_manager.py`)
```python
import pyaudio
import pygame
import os

class AudioManager:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        pygame.mixer.init()
        self.volume = int(os.getenv('AUDIO_OUTPUT_VOLUME', 80)) / 100

    def start_mic_stream(self):
        stream = self.pa.open(format=pyaudio.paInt16, channels=1,
                              rate=16000, input=True, frames_per_buffer=1024)
        return stream

    def play_audio(self, audio_data):
        # Play received audio bytes through speaker
        pygame.mixer.music.set_volume(self.volume)
        # Stream playback implementation
        pass
```

---

## Phase 16: Analytics & Vet Export (Day 9)

### Step 16.1 — Analytics with export
```python
import csv
import io
from reportlab.pdfgen import canvas

class PetAnalytics:
    def __init__(self, db_path):
        self.db_path = db_path

    def summary(self, pet_id, days=30):
        conn = sqlite3.connect(self.db_path)
        feedings = conn.execute('''SELECT portion_grams, consumed_grams
            FROM feedings WHERE pet_id = ? AND dispensed_at > datetime('now', ?)''',
            (pet_id, f'-{days} days')).fetchall()
        weights = conn.execute('''SELECT weight_grams FROM weight_logs
            WHERE pet_id = ? ORDER BY measured_at DESC LIMIT 2''', (pet_id,)).fetchall()
        conn.close()

        avg_portion = sum(f[0] for f in feedings) / len(feedings) if feedings else 0
        weight_trend = f"{weights[0][0] - weights[1][0]:+.0f}g" if len(weights) >= 2 else "N/A"

        return {
            'total_feedings': len(feedings),
            'avg_portion_g': round(avg_portion, 1),
            'weight_trend': weight_trend
        }

    def export_csv(self, pet_id, days=90):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute('''SELECT dispensed_at, portion_grams, consumed_grams,
            eating_speed_g_sec FROM feedings WHERE pet_id = ?
            ORDER BY dispensed_at DESC''', (pet_id,)).fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Portion (g)', 'Consumed (g)', 'Speed (g/s)'])
        writer.writerows(rows)
        return output.getvalue()
```

---

## Phase 17: Motion Detection (Day 9)

### Step 17.1 — PIR motion detector (`src/motion_detector.py`)
```python
import RPi.GPIO as GPIO
import os

class MotionDetector:
    def __init__(self, socketio):
        self.pir_pin = int(os.getenv('PIR_GPIO', 17))
        self.socketio = socketio
        GPIO.setup(self.pir_pin, GPIO.IN)

    def start(self, callback):
        GPIO.add_event_detect(self.pir_pin, GPIO.RISING,
                             callback=lambda _: callback(),
                             bouncetime=5000)  # 5s debounce
```

---

## Phase 18: Deployment & Hardening (Day 10)

### Step 18.1 — Deploy script (`deploy/deploy_to_pi.sh`)
```bash
#!/bin/bash
set -e
PI_HOST="rasp-pi"
REMOTE_DIR="/opt/pet-feeder"

echo "🐶 Deploying Smart Pet Feeder..."
ssh $PI_HOST "mkdir -p $REMOTE_DIR"
rsync -avz --exclude='venv' --exclude='data/*.db' ./ $PI_HOST:$REMOTE_DIR/
ssh $PI_HOST "cd $REMOTE_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
ssh $PI_HOST "sudo systemctl restart pet-feeder"
echo "✅ Deployment complete!"
```

### Step 18.2 — Systemd service (`deploy/pet-feeder.service`)
```ini
[Unit]
Description=Smart Pet Feeder & Health Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/pet-feeder
ExecStart=/opt/pet-feeder/venv/bin/python -m src.app
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### Step 18.3 — Security checklist
- [ ] All queries use parameterized statements
- [ ] Passwords hashed with bcrypt (cost factor ≥ 12)
- [ ] JWT tokens in httpOnly secure cookies
- [ ] HTTPS enforced on all routes
- [ ] .env file has 600 permissions
- [ ] Rate limiting on all auth and feed endpoints
- [ ] Max portion cap enforced in software
- [ ] Daily caloric limit per pet
- [ ] Camera stream requires authentication
- [ ] Audio stream requires authenticated WebSocket
