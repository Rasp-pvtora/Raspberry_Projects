# 📐 Technical Specification Document — Smart Pet Feeder & Health Monitor

---

## 1. Database Schema (SQLite)

### Table: `users`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | NOT NULL UNIQUE |
| password_hash | TEXT | NOT NULL |
| role | TEXT | DEFAULT 'admin' |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| last_login | DATETIME | |

### Table: `pets`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL |
| species | TEXT | DEFAULT 'dog' (dog/cat/other) |
| breed | TEXT | |
| birth_date | DATE | |
| photo_path | TEXT | |
| rfid_tag_uid | TEXT | UNIQUE |
| default_portion_g | REAL | NOT NULL DEFAULT 50 |
| feed_times | TEXT | JSON array of HH:MM strings |
| dietary_notes | TEXT | |
| active | BOOLEAN | DEFAULT 1 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `feedings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| pet_id | INTEGER | FK → pets.id |
| portion_grams | REAL | NOT NULL |
| trigger_type | TEXT | NOT NULL (scheduled/manual/rfid/recognition) |
| dispensed_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| consumed_grams | REAL | |
| eating_duration_sec | INTEGER | |
| eating_speed_g_sec | REAL | |
| slow_feed_triggered | BOOLEAN | DEFAULT 0 |

### Table: `weight_logs`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| pet_id | INTEGER | FK → pets.id |
| weight_grams | REAL | NOT NULL |
| measured_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| source | TEXT | DEFAULT 'auto' (auto/manual) |

### Table: `water_readings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| level_cm | REAL | NOT NULL |
| level_pct | REAL | |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `hopper_readings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| is_low | BOOLEAN | NOT NULL |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `health_alerts`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| pet_id | INTEGER | FK → pets.id |
| alert_type | TEXT | NOT NULL (missed_meal/overeating/weight_change/low_water/low_hopper) |
| severity | TEXT | DEFAULT 'warning' (info/warning/critical) |
| message | TEXT | NOT NULL |
| acknowledged | BOOLEAN | DEFAULT 0 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `medication_schedules`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| pet_id | INTEGER | FK → pets.id |
| medication_name | TEXT | NOT NULL |
| dose_description | TEXT | |
| times | TEXT | JSON array of HH:MM strings |
| active | BOOLEAN | DEFAULT 1 |

### Table: `medication_logs`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| schedule_id | INTEGER | FK → medication_schedules.id |
| dispensed_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| status | TEXT | DEFAULT 'dispensed' (dispensed/skipped/late) |

### Table: `motion_events`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| detected_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| pet_identified | TEXT | |
| confidence | REAL | |

### Table: `feature_toggles`
| Column | Type | Constraints |
|--------|------|------------|
| feature_key | TEXT | PRIMARY KEY |
| enabled | BOOLEAN | NOT NULL DEFAULT 0 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_by | INTEGER | FK → users.id |

---

## 2. `.env.default` Template

> See full template in [README.md → Environment Variables](README.md#-environment-variables)

Total environment variables: **~50**

---

## 3. API Route Specifications

### Authentication
```
POST /api/auth/login
  Body: { "username": "...", "password": "..." }
  Response: { "token": "jwt...", "expires_in": 86400 }
  Rate Limit: 10 attempts / 15 min per IP
```

### Pet Profiles
```
GET /api/pets
  Response: [{ "id": 1, "name": "Buddy", "species": "dog", "default_portion_g": 50, ... }]

POST /api/pets
  Body: { "name": "Buddy", "species": "dog", "default_portion_g": 50, "feed_times": ["08:00","18:00"] }
  Response: { "id": 1, "message": "Pet created" }

PUT /api/pets/<id>
  Body: { "default_portion_g": 60 }
  Response: { "message": "Pet updated" }

DELETE /api/pets/<id>
  Response: { "message": "Pet deactivated" }
```

### Feeding Control
```
POST /api/feed/now
  Body: { "pet_id": 1, "portion_g": 50 }
  Response: { "status": "dispensing", "portion_g": 50 }

GET /api/feed/schedule
  Response: [{ "pet_id": 1, "times": ["08:00","18:00"], "portion_g": 50 }]

PUT /api/feed/schedule
  Body: { "pet_id": 1, "times": ["08:00","12:00","18:00"], "portion_g": 40 }
  Response: { "message": "Schedule updated" }

GET /api/feed/log?pet_id=1&days=30
  Response: [{ "dispensed_at": "...", "portion_grams": 50, "consumed_grams": 48, "eating_speed_g_sec": 2.1 }]
```

### Weight Tracking
```
GET /api/weight/<pet_id>?days=90
  Response: [{ "weight_grams": 12500, "measured_at": "..." }]

POST /api/weight/<pet_id>/manual
  Body: { "weight_grams": 12600 }
  Response: { "message": "Weight logged" }
```

### Sensors
```
GET /api/water/level
  Response: { "level_cm": 8.5, "level_pct": 56, "is_low": false }

GET /api/hopper/level
  Response: { "is_low": false, "last_refill": "..." }

GET /api/climate
  Response: { "temperature_c": 23.1, "humidity_pct": 50 }
```

### Treat & Medication
```
POST /api/treat/launch
  Response: { "status": "launched", "message": "Treat dispensed!" }

POST /api/medication/dispense
  Body: { "schedule_id": 1 }
  Response: { "status": "dispensed" }

GET /api/medication/schedules
  Response: [{ "id": 1, "pet_id": 1, "medication_name": "Antibiotics", "times": ["09:00"] }]
```

### Health & Analytics
```
GET /api/health/alerts?active=true
  Response: [{ "id": 1, "pet_id": 1, "alert_type": "missed_meal", "severity": "warning" }]

PUT /api/health/alerts/<id>/acknowledge
  Response: { "acknowledged": true }

GET /api/analytics/summary?pet_id=1&days=30
  Response: { "avg_portion_g": 48.5, "total_feedings": 60, "weight_trend": "+200g" }

GET /api/analytics/export?pet_id=1&format=csv
  Response: CSV file download

GET /api/analytics/export?pet_id=1&format=pdf
  Response: PDF vet report download
```

### Feature Toggles (Dashboard-driven)
```
GET /api/settings/features
  Response: { "ENABLE_SCHEDULED_FEEDING": true, "ENABLE_PET_RECOGNITION": false, ... }

PUT /api/settings/features
  Body: { "ENABLE_PET_RECOGNITION": true, "ENABLE_RFID_FEEDING": true }
  Response: { "updated": ["ENABLE_PET_RECOGNITION", "ENABLE_RFID_FEEDING"] }
  Note: Updates both SQLite and .env file in real-time
```

---

## 4. WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `feeding_started` | Server → Client | `{ "pet_id": 1, "portion_g": 50 }` |
| `feeding_complete` | Server → Client | `{ "pet_id": 1, "consumed_g": 48, "duration_sec": 120 }` |
| `weight_update` | Server → Client | `{ "pet_id": 1, "weight_g": 12500 }` |
| `water_level` | Server → Client | `{ "level_pct": 56, "is_low": false }` |
| `hopper_alert` | Server → Client | `{ "is_low": true }` |
| `health_alert` | Server → Client | `{ "pet_id": 1, "type": "missed_meal", "severity": "warning" }` |
| `motion_detected` | Server → Client | `{ "pet_identified": "Buddy", "confidence": 89 }` |
| `medication_due` | Server → Client | `{ "pet_id": 1, "medication": "Antibiotics" }` |
| `treat_launched` | Server → Client | `{ "status": "success" }` |
| `toggle_feature` | Client → Server | `{ "feature": "ENABLE_PET_RECOGNITION", "enabled": true }` |
| `feature_toggled` | Server → Client | `{ "feature": "ENABLE_PET_RECOGNITION", "enabled": true }` |

---

## 5. Threat Model

| # | Threat | Mitigation |
|---|--------|-----------|
| 1 | Brute-force login | bcrypt + 10 attempts/15min rate limit + account lockout |
| 2 | JWT token theft | 24h expiry, httpOnly secure cookies, token rotation |
| 3 | Unauthorized feeding | Auth required on all feed endpoints, per-pet RFID validation |
| 4 | Camera feed interception | Authenticated MJPEG stream, HTTPS enforced |
| 5 | Servo motor overfeeding | Software max-portion cap + daily caloric limit per pet |
| 6 | Load cell tampering | Tare validation, anomaly detection on weight readings |
| 7 | RFID cloning | UID + challenge-response for advanced tags, logging unknown UIDs |
| 8 | .env file exposure | File permissions 600, not served by web server, gitignored |
| 9 | SQL injection | Parameterized queries exclusively |
| 10 | Man-in-the-middle | HTTPS/TLS on all endpoints |
| 11 | DoS on feeding endpoint | Rate limit feed requests (max 1/minute per pet) |
| 12 | Audio eavesdropping | Two-way audio requires authenticated WebSocket session |

---

## 6. Development Phases

| Phase | Description | Days |
|-------|-------------|------|
| 1 | Project setup, Flask skeleton, auth system | Day 1 |
| 2 | Servo food dispenser + portion calibration | Day 1–2 |
| 3 | Scheduled feeding engine (APScheduler/cron) | Day 2 |
| 4 | SQLite schema, feeding log, pet CRUD | Day 2–3 |
| 5 | Web dashboard (dark theme, pet cards, quick-feed) | Day 3 |
| 6 | HX711 load cell weight tracking | Day 3–4 |
| 7 | Eating speed analysis + slow-feed mode | Day 4 |
| 8 | Water level (HC-SR04) + hopper monitor (IR) | Day 4 |
| 9 | Pi Camera MJPEG stream + night IR mode | Day 5 |
| 10 | Pet facial recognition (TFLite training + inference) | Day 5–6 |
| 11 | RFID collar tag reading + multi-pet authorization | Day 6 |
| 12 | Behavioral health alerts + notification system | Day 7 |
| 13 | Feature toggle system (dashboard ↔ .env sync) | Day 7 |
| 14 | Treat launcher + medication dispenser | Day 8 |
| 15 | Two-way audio (mic + speaker) | Day 8–9 |
| 16 | Analytics engine + Chart.js + vet export (CSV/PDF) | Day 9 |
| 17 | Motion detection + activity logging | Day 9 |
| 18 | Deployment, systemd, testing, hardening | Day 10 |

---

## 7. File Structure

```
Smart Pet Feeder & Health Monitor/
├── README.md
├── TSD.md
├── task.md
├── implementation_plan.md
├── requirements.txt
├── .env.default
├── init_db.py
├── calibrate_scale.py
├── train_pet_model.py
├── deploy/
│   ├── deploy_to_pi.sh
│   └── pet-feeder.service
├── docs/
│   └── threat_model.md
├── data/
│   ├── petfeeder.db
│   └── pet_photos/
├── models/
│   └── pet_model.tflite
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── auth.py
│   ├── servo_controller.py
│   ├── feeding_scheduler.py
│   ├── weight_tracker.py
│   ├── eating_analyzer.py
│   ├── water_monitor.py
│   ├── hopper_monitor.py
│   ├── camera_stream.py
│   ├── pet_recognition.py
│   ├── rfid_reader.py
│   ├── health_alerts.py
│   ├── notification_service.py
│   ├── treat_launcher.py
│   ├── medication_dispenser.py
│   ├── audio_manager.py
│   ├── motion_detector.py
│   ├── analytics.py
│   ├── feature_toggles.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── pet_routes.py
│   │   ├── feed_routes.py
│   │   ├── weight_routes.py
│   │   ├── sensor_routes.py
│   │   ├── treat_routes.py
│   │   ├── health_routes.py
│   │   ├── analytics_routes.py
│   │   └── settings_routes.py
│   └── templates/
│       ├── layout.html
│       ├── login.html
│       ├── dashboard.html
│       ├── pet_profiles.html
│       ├── feeding_log.html
│       ├── weight_chart.html
│       ├── health_alerts.html
│       ├── live_camera.html
│       ├── treat_game.html
│       ├── analytics.html
│       └── settings.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── dashboard.js
│       ├── pets.js
│       ├── feeding.js
│       ├── weight.js
│       ├── camera.js
│       ├── treat.js
│       ├── analytics.js
│       └── settings.js
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    ├── test_feeding.py
    ├── test_weight.py
    ├── test_health.py
    ├── test_recognition.py
    └── test_toggles.py
```
