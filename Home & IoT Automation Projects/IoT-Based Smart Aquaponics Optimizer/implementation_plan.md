# 🗺️ Implementation Plan — IoT-Based Smart Aquaponics Optimizer

---

## Phase 1: Project Setup & Authentication (Day 1)

### Step 1.1 — Initialize project structure
```bash
mkdir -p src/{sensors,controllers,ai,routes,templates} static/{css,js} data/plant_photos models deploy docs grafana/dashboards tests
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
scikit-learn==1.5.*
joblib==1.4.*
numpy==1.26.*
RPi.GPIO==0.7.*
atlas-i2c==0.3.*
w1thermsensor==2.3.*
adafruit-circuitpython-ina219==3.4.*
influxdb-client==1.44.*
python-telegram-bot==21.*
requests==2.32.*
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

from routes import (auth_routes, sensor_routes, water_routes, dosing_routes,
                    fish_routes, plant_routes, light_routes, health_routes,
                    prediction_routes, harvest_routes, settings_routes)

for bp_module in [auth_routes, sensor_routes, water_routes, dosing_routes,
                  fish_routes, plant_routes, light_routes, health_routes,
                  prediction_routes, harvest_routes, settings_routes]:
    app.register_blueprint(bp_module.bp)

if __name__ == '__main__':
    socketio.run(app, host=os.getenv('HOST', '0.0.0.0'),
                 port=int(os.getenv('PORT', 5000)))
```

### Step 1.4 — Authentication (same pattern as previous projects)
```python
# src/auth.py — bcrypt + JWT + rate limiting
# Identical pattern to Garage Door / Pet Feeder auth module
```

---

## Phase 2: Atlas Scientific Sensor Integration (Day 1–2)

### Step 2.1 — pH probe (`src/sensors/atlas_ph.py`)
```python
from atlas_i2c import atlas_i2c
import os

class PHSensor:
    def __init__(self):
        self.address = int(os.getenv('PH_I2C_ADDRESS', '0x63'), 16)
        self.sensor = atlas_i2c.AtlasI2C(address=self.address)
        self.interval = int(os.getenv('PH_CHECK_INTERVAL_SEC', 60))

    def read(self):
        """Read pH value from Atlas Scientific EZO pH circuit."""
        response = self.sensor.query('R')
        return float(response.data.decode().strip())

    def calibrate(self, point, value):
        """
        Calibrate pH probe.
        point: 'mid' (pH 7), 'low' (pH 4), 'high' (pH 10)
        """
        self.sensor.query(f'Cal,{point},{value}')
```

### Step 2.2 — EC probe (`src/sensors/atlas_ec.py`)
```python
from atlas_i2c import atlas_i2c
import os

class ECSensor:
    def __init__(self):
        self.address = int(os.getenv('EC_I2C_ADDRESS', '0x64'), 16)
        self.sensor = atlas_i2c.AtlasI2C(address=self.address)

    def read(self):
        """Read EC in µS/cm."""
        response = self.sensor.query('R')
        return float(response.data.decode().strip())
```

### Step 2.3 — DO probe (`src/sensors/atlas_do.py`)
```python
from atlas_i2c import atlas_i2c
import os

class DOSensor:
    def __init__(self):
        self.address = int(os.getenv('DO_I2C_ADDRESS', '0x61'), 16)
        self.sensor = atlas_i2c.AtlasI2C(address=self.address)

    def read(self):
        """Read dissolved oxygen in mg/L."""
        response = self.sensor.query('R')
        return float(response.data.decode().strip())
```

### Step 2.4 — pH calibration script (`calibrate_ph.py`)
```python
from src.sensors.atlas_ph import PHSensor

def calibrate():
    ph = PHSensor()

    print("=== Atlas Scientific pH Calibration ===")
    print("Step 1: Place probe in pH 7.0 buffer solution. Press Enter...")
    input()
    ph.calibrate('mid', 7.0)
    print(f"Mid-point calibrated. Current reading: {ph.read()}")

    print("Step 2: Place probe in pH 4.0 buffer solution. Press Enter...")
    input()
    ph.calibrate('low', 4.0)
    print(f"Low-point calibrated. Current reading: {ph.read()}")

    print("Step 3: Place probe in pH 10.0 buffer solution. Press Enter...")
    input()
    ph.calibrate('high', 10.0)
    print(f"High-point calibrated. Current reading: {ph.read()}")

    print("✅ Calibration complete!")

if __name__ == '__main__':
    calibrate()
```

---

## Phase 3: Temperature Probes & Thermal Control (Day 2)

### Step 3.1 — DS18B20 multi-probe reader (`src/sensors/ds18b20.py`)
```python
from w1thermsensor import W1ThermSensor
import os

class TemperatureMonitor:
    def __init__(self):
        self.sensors = W1ThermSensor.get_available_sensors()
        self.target = float(os.getenv('TEMP_TARGET_C', 24.0))
        self.tolerance = float(os.getenv('TEMP_TOLERANCE_C', 2.0))

    def read_all(self):
        """Read all connected DS18B20 probes."""
        readings = {}
        for sensor in self.sensors:
            readings[sensor.id] = round(sensor.get_temperature(), 1)
        return readings

    def get_average(self):
        readings = self.read_all()
        return round(sum(readings.values()) / len(readings), 1) if readings else None
```

### Step 3.2 — Temperature controller (`src/controllers/temp_controller.py`)
```python
import RPi.GPIO as GPIO
import os

class TempController:
    def __init__(self, temp_monitor):
        self.temp_monitor = temp_monitor
        self.heater_pin = int(os.getenv('HEATER_GPIO', 17))
        self.chiller_pin = int(os.getenv('CHILLER_GPIO', 27))
        self.target = float(os.getenv('TEMP_TARGET_C', 24.0))
        self.tolerance = float(os.getenv('TEMP_TOLERANCE_C', 2.0))

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.heater_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.chiller_pin, GPIO.OUT, initial=GPIO.LOW)

    def regulate(self):
        """Check temperature and activate heater/chiller as needed."""
        temp = self.temp_monitor.get_average()
        if temp is None:
            return

        if temp < self.target - self.tolerance:
            GPIO.output(self.heater_pin, GPIO.HIGH)
            GPIO.output(self.chiller_pin, GPIO.LOW)
            return 'heating'
        elif temp > self.target + self.tolerance:
            GPIO.output(self.heater_pin, GPIO.LOW)
            GPIO.output(self.chiller_pin, GPIO.HIGH)
            return 'cooling'
        else:
            GPIO.output(self.heater_pin, GPIO.LOW)
            GPIO.output(self.chiller_pin, GPIO.LOW)
            return 'stable'
```

---

## Phase 4: Database & InfluxDB Pipeline (Day 2–3)

### Step 4.1 — SQLite initialization (`init_db.py`)
```python
import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'data/aquaponics.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create all tables as defined in TSD
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME)''')

    c.execute('''CREATE TABLE IF NOT EXISTS systems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        volume_liters REAL,
        active BOOLEAN DEFAULT 1)''')

    c.execute('''CREATE TABLE IF NOT EXISTS dosing_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_id INTEGER REFERENCES systems(id),
        substance TEXT NOT NULL,
        amount_ml REAL NOT NULL,
        trigger_type TEXT NOT NULL,
        before_value REAL,
        after_value REAL,
        dosed_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_id INTEGER REFERENCES systems(id),
        alert_type TEXT NOT NULL,
        severity TEXT DEFAULT 'warning',
        message TEXT NOT NULL,
        sensor_value REAL,
        threshold REAL,
        acknowledged BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS harvests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_id INTEGER,
        weight_grams REAL NOT NULL,
        quality_score INTEGER,
        notes TEXT,
        harvested_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS feature_toggles (
        feature_key TEXT PRIMARY KEY,
        enabled BOOLEAN NOT NULL DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER REFERENCES users(id))''')

    # Additional tables...
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
```

### Step 4.2 — InfluxDB client (`src/influxdb_client.py`)
```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os

class TimeSeriesDB:
    def __init__(self):
        self.enabled = os.getenv('ENABLE_INFLUXDB', 'false').lower() == 'true'
        if self.enabled:
            self.client = InfluxDBClient(
                url=os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
                token=os.getenv('INFLUXDB_TOKEN', ''),
                org=os.getenv('INFLUXDB_ORG', 'aquaponics'))
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.bucket = os.getenv('INFLUXDB_BUCKET', 'sensors')

    def write_sensor(self, measurement, tags, fields):
        if not self.enabled:
            return
        point = Point(measurement)
        for k, v in tags.items():
            point.tag(k, v)
        for k, v in fields.items():
            point.field(k, v)
        self.write_api.write(bucket=self.bucket, record=point)

    def query_sensor(self, measurement, field, hours=24):
        if not self.enabled:
            return []
        query = f'''from(bucket: "{self.bucket}")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r._measurement == "{measurement}")
            |> filter(fn: (r) => r._field == "{field}")'''
        result = self.client.query_api().query(query)
        return [{'time': r.get_time().isoformat(), 'value': r.get_value()}
                for table in result for r in table.records]
```

---

## Phase 5: Web Dashboard (Day 3–4)

### Step 5.1 — Dashboard with health score gauge
```html
{% extends "layout.html" %}
{% block content %}
<div class="health-score-container">
    <div class="gauge" id="health-gauge">
        <span class="score" id="health-score">--</span>
        <span class="label">System Health</span>
    </div>
</div>
<div class="sensor-grid">
    <div class="card sensor-card" id="ph-card">
        <h4>🧪 pH</h4>
        <span class="value" id="ph-value">--</span>
        <span class="target">Target: {{ config.PH_TARGET }}</span>
    </div>
    <div class="card sensor-card" id="ec-card">
        <h4>⚡ EC</h4>
        <span class="value" id="ec-value">-- µS</span>
    </div>
    <div class="card sensor-card" id="do-card">
        <h4>💨 DO</h4>
        <span class="value" id="do-value">-- mg/L</span>
    </div>
    <div class="card sensor-card" id="temp-card">
        <h4>🌡️ Temp</h4>
        <span class="value" id="temp-value">--°C</span>
    </div>
</div>
<div class="quick-actions">
    <button class="btn" onclick="feedFish()">🐟 Feed Fish</button>
    <button class="btn" onclick="dosePhUp()">⬆️ pH Up</button>
    <button class="btn" onclick="dosePhDown()">⬇️ pH Down</button>
    <button class="btn" onclick="triggerTopOff()">💧 Top Off</button>
</div>
{% endblock %}
```

### Step 5.2 — Real-time WebSocket handler (`static/js/dashboard.js`)
```javascript
const socket = io();

socket.on('sensor_update', (data) => {
    document.getElementById('ph-value').textContent = data.ph?.toFixed(2) || '--';
    document.getElementById('ec-value').textContent = (data.ec_us || '--') + ' µS';
    document.getElementById('do-value').textContent = (data.do_mg_l?.toFixed(1) || '--') + ' mg/L';
    document.getElementById('temp-value').textContent = (data.temp_c?.toFixed(1) || '--') + '°C';
    colorCodeSensors(data);
});

socket.on('health_score', (data) => {
    const el = document.getElementById('health-score');
    el.textContent = data.score;
    el.className = `score ${data.score >= 80 ? 'green' : data.score >= 50 ? 'yellow' : 'red'}`;
});
```

---

## Phase 6: pH Auto-Dosing (Day 4)

### Step 6.1 — Dosing controller (`src/controllers/dosing_controller.py`)
```python
import RPi.GPIO as GPIO
import time
import os
import sqlite3
from datetime import datetime, timedelta

class DosingController:
    def __init__(self, ph_sensor, db_path, socketio):
        self.ph_sensor = ph_sensor
        self.db_path = db_path
        self.socketio = socketio

        self.ph_target = float(os.getenv('PH_TARGET', 6.8))
        self.ph_tolerance = float(os.getenv('PH_TOLERANCE', 0.3))
        self.dose_ml = float(os.getenv('PH_DOSE_ML', 2))
        self.ph_up_pin = int(os.getenv('PH_UP_PUMP_GPIO', 25))
        self.ph_down_pin = int(os.getenv('PH_DOWN_PUMP_GPIO', 5))
        self.cooldown_sec = 300  # 5 minutes between doses
        self.daily_max_ml = 50
        self.last_dose_time = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.ph_up_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ph_down_pin, GPIO.OUT, initial=GPIO.LOW)

    def check_and_dose(self):
        """Auto-dose pH based on current reading vs target."""
        current_ph = self.ph_sensor.read()

        # Cooldown check
        if self.last_dose_time and (datetime.now() - self.last_dose_time).seconds < self.cooldown_sec:
            return None

        # Daily limit check
        if self._daily_total() >= self.daily_max_ml:
            return None

        if current_ph < self.ph_target - self.ph_tolerance:
            self._dose(self.ph_up_pin, 'ph_up', current_ph)
            return 'ph_up'
        elif current_ph > self.ph_target + self.ph_tolerance:
            self._dose(self.ph_down_pin, 'ph_down', current_ph)
            return 'ph_down'
        return None

    def _dose(self, pin, substance, before_value):
        """Activate pump for calibrated duration."""
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(self.dose_ml * 0.5)  # ~0.5s per mL (calibrate per pump)
        GPIO.output(pin, GPIO.LOW)
        self.last_dose_time = datetime.now()

        # Log
        conn = sqlite3.connect(self.db_path)
        conn.execute('''INSERT INTO dosing_log (system_id, substance, amount_ml, trigger_type, before_value)
                       VALUES (1, ?, ?, 'auto', ?)''', (substance, self.dose_ml, before_value))
        conn.commit()
        conn.close()

        self.socketio.emit('dosing_event', {
            'substance': substance, 'ml': self.dose_ml, 'triggered_by': 'auto'})

    def _daily_total(self):
        conn = sqlite3.connect(self.db_path)
        result = conn.execute('''SELECT COALESCE(SUM(amount_ml), 0) FROM dosing_log
                                WHERE dosed_at > datetime('now', '-1 day')''').fetchone()
        conn.close()
        return result[0]
```

---

## Phase 7: Grow Light PWM Control (Day 4–5)

### Step 7.1 — Light controller (`src/controllers/light_controller.py`)
```python
import RPi.GPIO as GPIO
import os
from datetime import datetime

class LightController:
    def __init__(self):
        self.pin = int(os.getenv('GROW_LIGHT_GPIO', 12))
        self.intensity = int(os.getenv('LIGHT_INTENSITY_PCT', 80))
        self.on_time = os.getenv('LIGHT_ON_TIME', '06:00')
        self.off_time = os.getenv('LIGHT_OFF_TIME', '22:00')

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 1000)  # 1 kHz
        self.pwm.start(0)

    def set_intensity(self, pct):
        self.intensity = max(0, min(100, pct))
        self.pwm.ChangeDutyCycle(self.intensity)

    def check_schedule(self):
        now = datetime.now().strftime('%H:%M')
        if self.on_time <= now < self.off_time:
            self.set_intensity(self.intensity)
            return True
        else:
            self.set_intensity(0)
            return False
```

---

## Phase 8–10: Water Flow, Level & Air Pump (Day 5–6)

### Step 8.1 — Flow sensor (`src/sensors/flow_sensor.py`)
```python
import RPi.GPIO as GPIO
import time
import os

class FlowSensor:
    def __init__(self):
        self.pin = int(os.getenv('FLOW_SENSOR_GPIO', 16))
        self.low_threshold = float(os.getenv('FLOW_LOW_THRESHOLD_LPM', 2.0))
        self.pulse_count = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self._pulse)

    def _pulse(self, channel):
        self.pulse_count += 1

    def read_flow_lpm(self, sample_sec=1):
        self.pulse_count = 0
        time.sleep(sample_sec)
        # YF-S201: 7.5 pulses per liter per minute
        flow_lpm = (self.pulse_count / 7.5) / sample_sec * 60
        return round(flow_lpm, 2)
```

### Step 9.1 — Water level + top-off (`src/controllers/topoff_controller.py`)
```python
class TopOffController:
    def __init__(self, water_level_sensor, socketio):
        self.sensor = water_level_sensor
        self.solenoid_pin = int(os.getenv('TOPOFF_SOLENOID_GPIO', 24))
        self.max_duration = int(os.getenv('TOPOFF_MAX_SEC', 60))
        self.socketio = socketio
        GPIO.setup(self.solenoid_pin, GPIO.OUT, initial=GPIO.LOW)

    def fill(self, duration_sec=None):
        duration = min(duration_sec or self.max_duration, self.max_duration)
        GPIO.output(self.solenoid_pin, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(self.solenoid_pin, GPIO.LOW)  # Safety: always close
        self.socketio.emit('water_level', self.sensor.read_level())
```

---

## Phase 11: Fish Feeder Servo (Day 6)

### Step 11.1 — Fish feeder (`src/controllers/fish_feeder.py`)
```python
import RPi.GPIO as GPIO
import time
import os

class FishFeeder:
    def __init__(self):
        self.pin = int(os.getenv('FISH_FEED_SERVO_GPIO', 13))
        self.duration = float(os.getenv('FISH_FEED_DURATION_SEC', 1.5))
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 50)
        self.pwm.start(0)

    def feed(self):
        self.pwm.ChangeDutyCycle(7.5)  # Rotate to dispense
        time.sleep(self.duration)
        self.pwm.ChangeDutyCycle(2.5)  # Return
        time.sleep(0.5)
        self.pwm.ChangeDutyCycle(0)
```

---

## Phase 14: System Health Score Engine (Day 7)

### Step 14.1 — Health score calculator (`src/health_score.py`)
```python
import os

class HealthScoreEngine:
    def __init__(self):
        self.weights = {
            'ph': int(os.getenv('HEALTH_WEIGHT_PH', 20)),
            'temp': int(os.getenv('HEALTH_WEIGHT_TEMP', 20)),
            'do': int(os.getenv('HEALTH_WEIGHT_DO', 20)),
            'ec': int(os.getenv('HEALTH_WEIGHT_EC', 15)),
            'flow': int(os.getenv('HEALTH_WEIGHT_FLOW', 15)),
            'level': int(os.getenv('HEALTH_WEIGHT_LEVEL', 10)),
        }

    def calculate(self, readings):
        components = {}

        # pH scoring
        ph_diff = abs(readings.get('ph', 0) - float(os.getenv('PH_TARGET', 6.8)))
        if ph_diff <= 0.3: components['ph'] = 100
        elif ph_diff <= 0.6: components['ph'] = 50
        else: components['ph'] = 0

        # Temperature scoring
        temp_diff = abs(readings.get('temp_c', 0) - float(os.getenv('TEMP_TARGET_C', 24)))
        if temp_diff <= 2: components['temp'] = 100
        elif temp_diff <= 4: components['temp'] = 50
        else: components['temp'] = 0

        # DO scoring
        do_val = readings.get('do_mg_l', 0)
        if do_val >= 6.0: components['do'] = 100
        elif do_val >= 4.0: components['do'] = 50
        else: components['do'] = 0

        # EC scoring
        ec_diff = abs(readings.get('ec_us', 0) - int(os.getenv('EC_TARGET_US', 1200)))
        if ec_diff <= 200: components['ec'] = 100
        elif ec_diff <= 400: components['ec'] = 50
        else: components['ec'] = 0

        # Flow scoring
        flow = readings.get('flow_lpm', 0)
        threshold = float(os.getenv('FLOW_LOW_THRESHOLD_LPM', 2.0))
        if flow >= threshold: components['flow'] = 100
        elif flow >= threshold * 0.5: components['flow'] = 50
        else: components['flow'] = 0

        # Level scoring
        level = readings.get('water_level_pct', 0)
        if level >= 60: components['level'] = 100
        elif level >= 30: components['level'] = 50
        else: components['level'] = 0

        # Weighted total
        score = sum(components.get(k, 0) * self.weights[k] / 100
                    for k in self.weights)

        return {
            'score': round(score),
            'components': {k: round(components.get(k, 0) * self.weights[k] / 100)
                          for k in self.weights}
        }
```

---

## Phase 16: Fish Counter — OpenCV (Day 8)

### Step 16.1 — Fish counter (`src/ai/fish_counter.py`)
```python
import cv2
import numpy as np

class FishCounter:
    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=False)
        self.min_area = 200
        self.max_area = 5000

    def count(self, frame):
        fg_mask = self.bg_subtractor.apply(frame)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        fish_count = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_area < area < self.max_area:
                fish_count += 1

        confidence = min(95, 60 + fish_count * 3)  # Heuristic
        return fish_count, confidence
```

---

## Phase 17: Plant Health CNN (Day 8–9)

### Step 17.1 — Training script (`train_plant_model.py`)
```python
import tensorflow as tf

def train(photos_dir, epochs=30):
    base = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    base.trainable = False

    model = tf.keras.Sequential([
        base,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(5, activation='softmax')
        # Classes: healthy, nitrogen_deficient, phosphorus_deficient, disease, pest_damage
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    data = tf.keras.utils.image_dataset_from_directory(
        photos_dir, image_size=(224, 224), batch_size=16)
    model.fit(data, epochs=epochs)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open('models/plant_model.tflite', 'wb') as f:
        f.write(tflite_model)
```

---

## Phase 18: Ammonia Prediction ML (Day 9–10)

### Step 18.1 — Ammonia predictor (`src/ai/ammonia_predictor.py`)
```python
import joblib
import numpy as np
import os

class AmmoniaPredictor:
    def __init__(self):
        model_path = os.getenv('AMMONIA_MODEL_PATH', 'models/ammonia_predictor.pkl')
        self.model = joblib.load(model_path) if os.path.exists(model_path) else None
        self.predict_hours = int(os.getenv('AMMONIA_PREDICT_HOURS', 12))

    def predict(self, sensor_history):
        """
        Predict ammonia levels using recent sensor trends.
        sensor_history: list of dicts with keys: ph, temp_c, do_mg_l, ec_us, feed_count, hour
        """
        if not self.model or len(sensor_history) < 24:
            return None

        # Extract features: trends, averages, rates of change
        features = self._extract_features(sensor_history)
        prediction = self.model.predict([features])[0]

        risk = 'low' if prediction < 0.05 else 'medium' if prediction < 0.1 else 'high'
        return {
            'predicted_nh3': round(prediction, 3),
            'risk': risk,
            'hours_ahead': self.predict_hours
        }

    def _extract_features(self, history):
        ph_values = [h['ph'] for h in history[-24:]]
        temp_values = [h['temp_c'] for h in history[-24:]]
        do_values = [h['do_mg_l'] for h in history[-24:]]
        return [
            np.mean(ph_values), np.std(ph_values),
            np.mean(temp_values), np.std(temp_values),
            np.mean(do_values), np.std(do_values),
            ph_values[-1] - ph_values[0],  # pH trend
            do_values[-1] - do_values[0],   # DO trend
            sum(h.get('feed_count', 0) for h in history[-24:]),
            history[-1].get('hour', 12)
        ]
```

---

## Phase 22: Predictive Maintenance (Day 11–12)

### Step 22.1 — Maintenance predictor (`src/predictive_maintenance.py`)
```python
class PredictiveMaintenance:
    def __init__(self, db_path):
        self.db_path = db_path

    def check_pump_health(self, flow_history):
        """Detect declining flow rate trend (pump degradation)."""
        if len(flow_history) < 7:
            return None
        weekly_avg = [sum(flow_history[i:i+24])/24
                     for i in range(0, len(flow_history), 24)]
        if len(weekly_avg) >= 2 and weekly_avg[-1] < weekly_avg[0] * 0.85:
            return {'task': 'pump_service', 'priority': 'high',
                    'message': 'Flow rate declined 15%+ — inspect pump'}
        return None

    def check_sensor_drift(self, readings_history):
        """Detect pH/EC sensor drift via moving average divergence."""
        # Compare last 24h average vs last 7-day average
        pass

    def check_filter(self, flow_history, pump_on_history):
        """Flow decreasing despite pump running = filter clogged."""
        pass
```

---

## Phase 25: Harvest Tracking (Day 13)

### Step 25.1 — Harvest tracker (`src/harvest_tracker.py`)
```python
class HarvestTracker:
    def __init__(self, db_path):
        self.db_path = db_path

    def log_harvest(self, plant_id, weight_g, quality, notes=''):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''INSERT INTO harvests (plant_id, weight_grams, quality_score, notes)
                       VALUES (?, ?, ?, ?)''', (plant_id, weight_g, quality, notes))
        conn.commit()
        conn.close()

    def yield_summary(self, days=365):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute('''SELECT p.name, SUM(h.weight_grams), COUNT(h.id), AVG(h.quality_score)
            FROM harvests h JOIN plant_profiles p ON h.plant_id = p.id
            WHERE h.harvested_at > datetime('now', ?) GROUP BY p.name''',
            (f'-{days} days',)).fetchall()
        conn.close()
        return [{'plant': r[0], 'total_g': r[1], 'count': r[2], 'avg_quality': round(r[3], 1)}
                for r in rows]
```

---

## Phase 26: Deployment & Hardening (Day 13–14)

### Step 26.1 — Deploy script (`deploy/deploy_to_pi.sh`)
```bash
#!/bin/bash
set -e
PI_HOST="rasp-pi"
REMOTE_DIR="/opt/aquaponics"

echo "🐟 Deploying Smart Aquaponics..."
ssh $PI_HOST "mkdir -p $REMOTE_DIR"
rsync -avz --exclude='venv' --exclude='data/*.db' ./ $PI_HOST:$REMOTE_DIR/
ssh $PI_HOST "cd $REMOTE_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
ssh $PI_HOST "sudo systemctl restart aquaponics"
echo "✅ Deployment complete!"
```

### Step 26.2 — Systemd service (`deploy/aquaponics.service`)
```ini
[Unit]
Description=IoT Smart Aquaponics Optimizer
After=network.target influxdb.service

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/aquaponics
ExecStart=/opt/aquaponics/venv/bin/python -m src.app
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### Step 26.3 — Security checklist
- [ ] All queries use parameterized statements
- [ ] Passwords hashed with bcrypt (cost factor ≥ 12)
- [ ] JWT tokens in httpOnly secure cookies
- [ ] HTTPS enforced on all routes
- [ ] .env file has 600 permissions
- [ ] Rate limiting: 1 dose per 5min per substance
- [ ] Max dose cap enforced per cycle + daily total limit
- [ ] Solenoid max-duration safety timeout
- [ ] InfluxDB token auth, bound to localhost
- [ ] Camera stream requires authentication
- [ ] Grafana authentication enabled
- [ ] No raw SQL interpolation
- [ ] GPIO pin conflict validation on startup
