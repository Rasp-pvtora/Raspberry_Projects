# 📐 Technical Specification Document — IoT-Based Smart Aquaponics Optimizer

---

## 1. Database Schema

### SQLite Tables (relational data)

#### Table: `users`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | NOT NULL UNIQUE |
| password_hash | TEXT | NOT NULL |
| role | TEXT | DEFAULT 'admin' |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| last_login | DATETIME | |

#### Table: `systems`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL |
| type | TEXT | NOT NULL (fish_tank/grow_bed) |
| volume_liters | REAL | |
| active | BOOLEAN | DEFAULT 1 |

#### Table: `fish_profiles`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| system_id | INTEGER | FK → systems.id |
| species | TEXT | NOT NULL |
| count | INTEGER | |
| feed_times | TEXT | JSON array |
| feed_portion_g | REAL | DEFAULT 5 |

#### Table: `plant_profiles`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| system_id | INTEGER | FK → systems.id |
| name | TEXT | NOT NULL |
| variety | TEXT | |
| planted_date | DATE | |
| expected_harvest_days | INTEGER | |
| status | TEXT | DEFAULT 'growing' |

#### Table: `dosing_log`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| system_id | INTEGER | FK → systems.id |
| substance | TEXT | NOT NULL (ph_up/ph_down/nutrient_a/nutrient_b) |
| amount_ml | REAL | NOT NULL |
| trigger_type | TEXT | NOT NULL (auto/manual) |
| before_value | REAL | |
| after_value | REAL | |
| dosed_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

#### Table: `fish_feedings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| system_id | INTEGER | FK → systems.id |
| portion_g | REAL | NOT NULL |
| trigger_type | TEXT | NOT NULL (scheduled/manual) |
| fed_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

#### Table: `harvests`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| plant_id | INTEGER | FK → plant_profiles.id |
| weight_grams | REAL | NOT NULL |
| quality_score | INTEGER | (1–5) |
| notes | TEXT | |
| harvested_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

#### Table: `alerts`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| system_id | INTEGER | FK → systems.id |
| alert_type | TEXT | NOT NULL |
| severity | TEXT | DEFAULT 'warning' (info/warning/critical) |
| message | TEXT | NOT NULL |
| sensor_value | REAL | |
| threshold | REAL | |
| acknowledged | BOOLEAN | DEFAULT 0 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

#### Table: `maintenance_tasks`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| system_id | INTEGER | FK → systems.id |
| task_type | TEXT | NOT NULL (pump_service/filter_clean/sensor_calibrate/water_change) |
| priority | TEXT | DEFAULT 'normal' |
| predicted_date | DATE | |
| completed_date | DATE | |
| status | TEXT | DEFAULT 'pending' |

#### Table: `feature_toggles`
| Column | Type | Constraints |
|--------|------|------------|
| feature_key | TEXT | PRIMARY KEY |
| enabled | BOOLEAN | NOT NULL DEFAULT 0 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_by | INTEGER | FK → users.id |

### InfluxDB Measurements (time-series)

| Measurement | Tags | Fields |
|-------------|------|--------|
| `water_chemistry` | `system_id`, `sensor` | `ph`, `ec_us`, `do_mg_l` |
| `temperature` | `system_id`, `probe_id` | `temp_c` |
| `water_flow` | `system_id` | `flow_lpm` |
| `water_level` | `system_id` | `level_cm`, `level_pct` |
| `solar_power` | | `voltage_v`, `current_ma`, `power_mw` |
| `air_pump` | `system_id` | `state` (0/1) |
| `grow_light` | `system_id` | `intensity_pct`, `state` (0/1) |
| `health_score` | `system_id` | `score`, `ph_component`, `temp_component`, `do_component` |
| `ammonia_prediction` | `system_id` | `predicted_nh3`, `confidence` |
| `plant_health` | `system_id`, `plant_id` | `health_score`, `disease_detected`, `deficiency` |

---

## 2. `.env.default` Template

> See full template in [README.md → Environment Variables](README.md#-environment-variables)

Total environment variables: **~90**

---

## 3. API Route Specifications

### Authentication
```
POST /api/auth/login
  Body: { "username": "...", "password": "..." }
  Response: { "token": "jwt...", "expires_in": 86400 }
  Rate Limit: 10 attempts / 15 min per IP
```

### Sensor Readings
```
GET /api/sensors/current
  Response: {
    "ph": 6.8, "ec_us": 1180, "do_mg_l": 6.2,
    "temp_c": [24.1, 23.8], "flow_lpm": 4.5,
    "water_level_pct": 78, "health_score": 87
  }

GET /api/sensors/ph/history?hours=24
  Response: [{ "time": "...", "value": 6.8 }, ...]

GET /api/sensors/ec/history?hours=24
GET /api/sensors/do/history?hours=24
GET /api/sensors/temp/history?hours=24
```

### Water Management
```
GET /api/water/flow
  Response: { "flow_lpm": 4.5, "is_low": false }

GET /api/water/level
  Response: { "level_cm": 23.4, "level_pct": 78, "is_low": false }

POST /api/water/topoff
  Body: { "duration_sec": 30 }
  Response: { "status": "filling", "duration_sec": 30 }
```

### Dosing Control
```
POST /api/dosing/ph-up
  Body: { "amount_ml": 2 }
  Response: { "status": "dosed", "substance": "ph_up", "amount_ml": 2 }

POST /api/dosing/ph-down
  Body: { "amount_ml": 2 }

POST /api/dosing/nutrients
  Body: { "pump": 1, "amount_ml": 5 }

GET /api/dosing/log?days=7
  Response: [{ "substance": "ph_up", "amount_ml": 2, "before_value": 6.2, "after_value": 6.7 }]
```

### Fish Management
```
POST /api/fish/feed
  Body: { "system_id": 1, "portion_g": 5 }
  Response: { "status": "feeding", "portion_g": 5 }

GET /api/fish/count
  Response: { "count": 12, "confidence": 85, "last_counted": "..." }

GET /api/fish/feed-log?days=30
  Response: [{ "fed_at": "...", "portion_g": 5, "trigger_type": "scheduled" }]
```

### Plant Health & Harvest
```
GET /api/plants/health
  Response: [{ "plant_id": 1, "health_score": 85, "issues": ["slight_nitrogen_deficiency"] }]

POST /api/harvest/log
  Body: { "plant_id": 1, "weight_grams": 250, "quality_score": 4 }

GET /api/harvest/history?days=365
  Response: [{ "plant": "Basil", "weight_grams": 250, "harvested_at": "..." }]
```

### Lights & Pumps
```
GET /api/lights/status
  Response: { "state": "on", "intensity_pct": 80, "schedule": { "on": "06:00", "off": "22:00" } }

PUT /api/lights/schedule
  Body: { "on": "06:00", "off": "22:00" }

PUT /api/lights/intensity
  Body: { "intensity_pct": 75 }

GET /api/air-pump/status
  Response: { "state": "on", "schedule": { "on": "06:00", "off": "22:00" } }
```

### Health Score & Predictions
```
GET /api/health-score
  Response: { "score": 87, "components": { "ph": 18, "temp": 20, "do": 17, "ec": 14, "flow": 12, "level": 6 } }

GET /api/predictions/ammonia
  Response: { "current_estimated_nh3": 0.02, "predicted_6h": 0.05, "predicted_12h": 0.08, "risk": "low" }

GET /api/predictions/yield
  Response: [{ "plant": "Basil", "predicted_harvest_date": "...", "estimated_weight_g": 300 }]

GET /api/maintenance/schedule
  Response: [{ "task": "filter_clean", "priority": "high", "predicted_date": "..." }]
```

### Feature Toggles (Dashboard-driven)
```
GET /api/settings/features
  Response: { "ENABLE_PH_MONITOR": true, "ENABLE_AMMONIA_PREDICT": false, ... }

PUT /api/settings/features
  Body: { "ENABLE_AMMONIA_PREDICT": true }
  Response: { "updated": ["ENABLE_AMMONIA_PREDICT"] }
  Note: Updates both SQLite and .env file in real-time
```

---

## 4. WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `sensor_update` | Server → Client | `{ "ph": 6.8, "ec_us": 1180, "do_mg_l": 6.2, "temp_c": 24.1 }` |
| `health_score` | Server → Client | `{ "score": 87, "components": {...} }` |
| `dosing_event` | Server → Client | `{ "substance": "ph_up", "ml": 2, "triggered_by": "auto" }` |
| `fish_count` | Server → Client | `{ "count": 12, "confidence": 85 }` |
| `feeding_event` | Server → Client | `{ "system_id": 1, "portion_g": 5 }` |
| `water_level` | Server → Client | `{ "level_pct": 78, "filling": false }` |
| `flow_alert` | Server → Client | `{ "flow_lpm": 1.2, "alert": "low_flow" }` |
| `plant_health` | Server → Client | `{ "plant_id": 1, "score": 85, "issues": [...] }` |
| `ammonia_alert` | Server → Client | `{ "predicted_nh3": 0.15, "risk": "high", "hours_ahead": 6 }` |
| `maintenance_due` | Server → Client | `{ "task": "filter_clean", "priority": "high" }` |
| `solar_update` | Server → Client | `{ "voltage_v": 14.2, "power_mw": 8500 }` |
| `alert_new` | Server → Client | `{ "type": "ph_low", "severity": "warning", "value": 5.8 }` |
| `toggle_feature` | Client → Server | `{ "feature": "ENABLE_AMMONIA_PREDICT", "enabled": true }` |
| `feature_toggled` | Server → Client | `{ "feature": "ENABLE_AMMONIA_PREDICT", "enabled": true }` |

---

## 5. Threat Model

| # | Threat | Mitigation |
|---|--------|-----------|
| 1 | Brute-force login | bcrypt + 10 attempts/15min rate limit + account lockout |
| 2 | JWT token theft | 24h expiry, httpOnly secure cookies, token rotation |
| 3 | Unauthorized dosing | Auth on all dosing endpoints, dose amount cap, cooldown timer |
| 4 | Pump runaway (overdose) | Max dose per cycle, daily dose limit, pH/EC bounds check |
| 5 | Sensor calibration drift | Auto-detect drift via cross-sensor correlation, alert + flag |
| 6 | Electrical safety (water + electronics) | Waterproof enclosures, GFCI outlets, relay isolation |
| 7 | Camera feed interception | Authenticated MJPEG stream, HTTPS enforced |
| 8 | InfluxDB unauthorized access | Token-based auth, bind to localhost only |
| 9 | .env file exposure | File permissions 600, not served by web server, gitignored |
| 10 | SQL injection | Parameterized queries exclusively |
| 11 | Man-in-the-middle | HTTPS/TLS on all endpoints |
| 12 | DoS on dosing endpoints | Rate limit: 1 dose per 5 minutes per substance |
| 13 | Power failure fish kill | UPS monitor alert, air pump battery backup recommendation |
| 14 | Solenoid valve stuck open | Max top-off duration limit, overflow sensor check |

---

## 6. Development Phases

| Phase | Description | Days |
|-------|-------------|------|
| 1 | Project setup, Flask skeleton, auth system | Day 1 |
| 2 | Atlas Scientific I2C sensor integration (pH, EC, DO) | Day 1–2 |
| 3 | DS18B20 temperature probes + heater/chiller relay control | Day 2 |
| 4 | SQLite schema + InfluxDB setup + data logging pipeline | Day 2–3 |
| 5 | Web dashboard (dark theme, sensor gauges, health score) | Day 3–4 |
| 6 | pH auto-dosing (peristaltic pump + PID logic) | Day 4 |
| 7 | Grow light PWM control + photoperiod scheduler | Day 4–5 |
| 8 | Water flow sensor (YF-S201 pulse counting) | Day 5 |
| 9 | Water level (HC-SR04) + solenoid auto top-off | Day 5 |
| 10 | Air pump relay control + scheduling | Day 5–6 |
| 11 | Fish feeder servo + feeding schedule | Day 6 |
| 12 | Feature toggle system (dashboard ↔ .env sync) | Day 6 |
| 13 | Notification system (Telegram, email) | Day 7 |
| 14 | System health score engine (weighted composite) | Day 7 |
| 15 | Pi Camera MJPEG stream + night mode | Day 7–8 |
| 16 | Fish counter (OpenCV blob detection) | Day 8 |
| 17 | Plant health CNN (TFLite MobileNetV2) | Day 8–9 |
| 18 | Ammonia prediction ML model (scikit-learn) | Day 9–10 |
| 19 | Auto nutrient dosing + multi-pump control | Day 10 |
| 20 | Solar monitor (INA219) + energy dashboard | Day 10–11 |
| 21 | Grafana InfluxDB dashboard integration | Day 11 |
| 22 | Predictive maintenance engine | Day 11–12 |
| 23 | Multi-bed/multi-tank support | Day 12 |
| 24 | Weather API integration | Day 12 |
| 25 | Harvest tracking + yield prediction | Day 13 |
| 26 | Deployment, systemd, testing, hardening | Day 13–14 |

---

## 7. Health Score Algorithm

```
System Health Score (0–100) = Σ (component_score × weight)

Components:
┌────────────────┬────────┬──────────────────────────────┐
│ Component      │ Weight │ Scoring Rule                 │
├────────────────┼────────┼──────────────────────────────┤
│ pH             │ 20%    │ 100 if within ±0.3 of target │
│                │        │ 50 if within ±0.6            │
│                │        │ 0 if outside ±1.0            │
├────────────────┼────────┼──────────────────────────────┤
│ Temperature    │ 20%    │ 100 if within ±2°C of target │
│                │        │ 50 if within ±4°C            │
│                │        │ 0 if outside ±6°C            │
├────────────────┼────────┼──────────────────────────────┤
│ Dissolved O₂   │ 20%    │ 100 if > 6.0 mg/L           │
│                │        │ 50 if > 4.0 mg/L             │
│                │        │ 0 if < 3.0 mg/L (CRITICAL)   │
├────────────────┼────────┼──────────────────────────────┤
│ EC             │ 15%    │ 100 if within ±200 µS target │
│                │        │ 50 if within ±400 µS         │
│                │        │ 0 if outside ±600 µS         │
├────────────────┼────────┼──────────────────────────────┤
│ Water Flow     │ 15%    │ 100 if > threshold LPM       │
│                │        │ 50 if > 50% threshold        │
│                │        │ 0 if stopped                  │
├────────────────┼────────┼──────────────────────────────┤
│ Water Level    │ 10%    │ 100 if > 60%                 │
│                │        │ 50 if > 30%                   │
│                │        │ 0 if < 15% (CRITICAL)         │
└────────────────┴────────┴──────────────────────────────┘
```

---

## 8. File Structure

```
IoT-Based Smart Aquaponics Optimizer/
├── README.md
├── TSD.md
├── task.md
├── implementation_plan.md
├── requirements.txt
├── .env.default
├── init_db.py
├── calibrate_ph.py
├── calibrate_ec.py
├── calibrate_do.py
├── train_plant_model.py
├── deploy/
│   ├── deploy_to_pi.sh
│   └── aquaponics.service
├── docs/
│   └── threat_model.md
├── data/
│   ├── aquaponics.db
│   └── plant_photos/
├── models/
│   ├── plant_model.tflite
│   └── ammonia_predictor.pkl
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── auth.py
│   ├── sensors/
│   │   ├── __init__.py
│   │   ├── atlas_ph.py
│   │   ├── atlas_ec.py
│   │   ├── atlas_do.py
│   │   ├── ds18b20.py
│   │   ├── flow_sensor.py
│   │   ├── water_level.py
│   │   └── solar_monitor.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── dosing_controller.py
│   │   ├── temp_controller.py
│   │   ├── light_controller.py
│   │   ├── air_pump.py
│   │   ├── fish_feeder.py
│   │   └── topoff_controller.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── plant_health.py
│   │   ├── fish_counter.py
│   │   ├── ammonia_predictor.py
│   │   └── yield_predictor.py
│   ├── health_score.py
│   ├── predictive_maintenance.py
│   ├── weather_service.py
│   ├── harvest_tracker.py
│   ├── notification_service.py
│   ├── influxdb_client.py
│   ├── feature_toggles.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── sensor_routes.py
│   │   ├── water_routes.py
│   │   ├── dosing_routes.py
│   │   ├── fish_routes.py
│   │   ├── plant_routes.py
│   │   ├── light_routes.py
│   │   ├── health_routes.py
│   │   ├── prediction_routes.py
│   │   ├── harvest_routes.py
│   │   ├── analytics_routes.py
│   │   └── settings_routes.py
│   └── templates/
│       ├── layout.html
│       ├── login.html
│       ├── dashboard.html
│       ├── water_chemistry.html
│       ├── temperature.html
│       ├── fish_tank.html
│       ├── grow_beds.html
│       ├── water_system.html
│       ├── dosing.html
│       ├── solar.html
│       ├── predictions.html
│       ├── harvest.html
│       ├── grafana.html
│       ├── alerts.html
│       └── settings.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── dashboard.js
│       ├── sensors.js
│       ├── dosing.js
│       ├── fish.js
│       ├── plants.js
│       ├── lights.js
│       ├── predictions.js
│       ├── harvest.js
│       └── settings.js
├── grafana/
│   └── dashboards/
│       ├── aquaponics-overview.json
│       └── water-chemistry.json
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    ├── test_sensors.py
    ├── test_dosing.py
    ├── test_health_score.py
    ├── test_fish.py
    ├── test_predictions.py
    └── test_toggles.py
```
