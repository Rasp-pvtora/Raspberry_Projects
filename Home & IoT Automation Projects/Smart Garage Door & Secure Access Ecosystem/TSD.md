# 📐 Technical Specification Document — Smart Garage Door & Secure Access Ecosystem

---

## 1. Database Schema (SQLite)

### Table: `users`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | NOT NULL UNIQUE |
| password_hash | TEXT | NOT NULL |
| role | TEXT | DEFAULT 'user' |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| last_login | DATETIME | |

### Table: `doors`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL |
| relay_gpio | INTEGER | NOT NULL |
| reed_gpio | INTEGER | NOT NULL |
| status | TEXT | DEFAULT 'closed' |
| last_changed | DATETIME | |

### Table: `events`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| door_id | INTEGER | FK → doors.id |
| event_type | TEXT | NOT NULL (open/close/tamper/alarm) |
| trigger_source | TEXT | NOT NULL (alpr/geo/manual/voice/guest/auto/emergency) |
| plate_number | TEXT | |
| plate_photo_path | TEXT | |
| user_id | INTEGER | FK → users.id |
| timestamp | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `alpr_whitelist`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| plate_number | TEXT | NOT NULL UNIQUE |
| owner_name | TEXT | |
| added_by | INTEGER | FK → users.id |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `guest_codes`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| code | TEXT | NOT NULL UNIQUE |
| code_type | TEXT | DEFAULT 'pin' (pin/qr) |
| door_id | INTEGER | FK → doors.id |
| created_by | INTEGER | FK → users.id |
| valid_from | DATETIME | NOT NULL |
| valid_until | DATETIME | NOT NULL |
| max_uses | INTEGER | DEFAULT 1 |
| use_count | INTEGER | DEFAULT 0 |
| revoked | BOOLEAN | DEFAULT 0 |

### Table: `climate_readings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| temperature_c | REAL | |
| humidity_pct | REAL | |
| co_ppm | REAL | |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `feature_toggles`
| Column | Type | Constraints |
|--------|------|------------|
| feature_key | TEXT | PRIMARY KEY |
| enabled | BOOLEAN | NOT NULL DEFAULT 0 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_by | INTEGER | FK → users.id |

### Table: `ups_readings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| voltage_v | REAL | |
| current_ma | REAL | |
| power_mw | REAL | |
| battery_pct | REAL | |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `vacation_schedule`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| door_id | INTEGER | FK → doors.id |
| next_action | TEXT | NOT NULL (open/close) |
| scheduled_at | DATETIME | NOT NULL |
| executed | BOOLEAN | DEFAULT 0 |

---

## 2. `.env.default` Template

> See full template in [README.md → Environment Variables](README.md#-environment-variables)

Total environment variables: **~45**

---

## 3. API Route Specifications

### Authentication
```
POST /api/auth/login
  Body: { "username": "...", "password": "..." }
  Response: { "token": "jwt...", "expires_in": 86400 }
  Rate Limit: 10 attempts / 15 min per IP

POST /api/auth/logout
  Headers: Authorization: Bearer <token>
  Response: { "message": "Logged out" }
```

### Door Control
```
GET /api/doors
  Response: [{ "id": 1, "name": "Main", "status": "closed", "last_changed": "..." }]

POST /api/doors/<id>/open
  Headers: Authorization: Bearer <token>
  Response: { "status": "opening", "door_id": 1 }

POST /api/doors/<id>/close
  Response: { "status": "closing", "door_id": 1 }

POST /api/doors/lock-all
  Response: { "status": "locked", "doors_affected": 2 }
```

### ALPR Whitelist
```
GET /api/alpr/whitelist
  Response: [{ "plate_number": "AB123CD", "owner_name": "John" }]

POST /api/alpr/whitelist
  Body: { "plate_number": "AB123CD", "owner_name": "John" }

DELETE /api/alpr/whitelist/<plate>
  Response: { "deleted": "AB123CD" }
```

### Guest Access
```
POST /api/guest/generate
  Body: { "door_id": 1, "type": "pin", "valid_hours": 4, "max_uses": 1 }
  Response: { "code": "847291", "valid_until": "..." }

GET /api/guest/codes
  Response: [{ "code": "847291", "use_count": 0, "revoked": false }]

DELETE /api/guest/codes/<id>
  Response: { "revoked": true }
```

### Feature Toggles (Dashboard-driven)
```
GET /api/settings/features
  Response: { "ENABLE_ALPR": true, "ENABLE_GEOFENCING": false, ... }

PUT /api/settings/features
  Body: { "ENABLE_ALPR": true, "ENABLE_GEOFENCING": true }
  Response: { "updated": ["ENABLE_GEOFENCING"], "message": "Features updated" }
  Note: Updates both SQLite and .env file in real-time
```

### Climate & UPS
```
GET /api/climate
  Response: { "temperature_c": 22.5, "humidity_pct": 45, "co_ppm": 1.2 }

GET /api/climate/history?hours=24
  Response: [{ "temperature_c": 22.5, "recorded_at": "..." }, ...]

GET /api/ups/status
  Response: { "voltage_v": 5.1, "battery_pct": 87, "charging": true }
```

### Analytics
```
GET /api/analytics/summary?period=week
  Response: { "total_events": 42, "peak_hour": 8, "by_source": {...} }

GET /api/analytics/chart?type=daily&days=30
  Response: { "labels": [...], "datasets": [...] }
```

---

## 4. WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `door_status` | Server → Client | `{ "door_id": 1, "status": "open" }` |
| `alpr_detection` | Server → Client | `{ "plate": "AB123CD", "confidence": 92, "whitelisted": true }` |
| `tamper_alert` | Server → Client | `{ "door_id": 1, "type": "vibration", "timestamp": "..." }` |
| `climate_update` | Server → Client | `{ "temperature_c": 22.5, "humidity_pct": 45 }` |
| `ups_alert` | Server → Client | `{ "battery_pct": 12, "alert": "low_battery" }` |
| `vacation_event` | Server → Client | `{ "door_id": 1, "action": "open", "simulated": true }` |
| `toggle_feature` | Client → Server | `{ "feature": "ENABLE_ALPR", "enabled": true }` |

---

## 5. Threat Model

| # | Threat | Mitigation |
|---|--------|-----------|
| 1 | Brute-force login | bcrypt + 10 attempts/15min rate limit + account lockout |
| 2 | JWT token theft | 24h expiry, httpOnly secure cookies, token rotation |
| 3 | Relay signal replay | Rolling code validation, timestamp-based nonce |
| 4 | ALPR spoofing (printed plates) | Confidence threshold + multi-frame verification + alert on mismatch |
| 5 | Physical tampering | Vibration sensor + magnetic reed + instant alarm + notification |
| 6 | Guest code abuse | Max-use limits, time bounds, single-door scope, revocation |
| 7 | Man-in-the-middle | HTTPS/TLS on all endpoints, self-signed cert generation script |
| 8 | Camera feed interception | Authenticated MJPEG stream, no public exposure |
| 9 | .env file exposure | File permissions 600, not served by web server, gitignored |
| 10 | SQL injection | Parameterized queries exclusively, no raw SQL interpolation |
| 11 | DoS on API | Flask-Limiter per-endpoint rate limiting |
| 12 | GPIO pin conflict | Pin reservation system, validation on startup |

---

## 6. Development Phases

| Phase | Description | Days |
|-------|-------------|------|
| 1 | Project setup, Flask skeleton, auth system | Day 1 |
| 2 | GPIO relay control + reed switch monitoring | Day 1–2 |
| 3 | SQLite schema, event logging, door CRUD | Day 2 |
| 4 | Web dashboard (dark theme, door cards, live status) | Day 2–3 |
| 5 | ALPR integration (OpenALPR/Tesseract + whitelist) | Day 3–4 |
| 6 | Camera MJPEG stream + night IR mode | Day 4 |
| 7 | Notification system (Telegram, Slack, Teams, email) | Day 5 |
| 8 | Feature toggle system (dashboard ↔ .env sync) | Day 5 |
| 9 | Guest access code generation + validation | Day 6 |
| 10 | Climate monitoring (DHT22, MQ-7) + UPS (INA219) | Day 6–7 |
| 11 | Analytics engine + Chart.js dashboards | Day 7 |
| 12 | Geofencing + voice control + vacation mode | Day 8–9 |
| 13 | Auto-close timer + emergency lock + tamper alarm | Day 9 |
| 14 | Multi-door support + systemd service + deploy | Day 10 |
| 15 | Testing, hardening, documentation | Day 10–11 |

---

## 7. File Structure

```
Smart Garage Door & Secure Access Ecosystem/
├── README.md
├── TSD.md
├── task.md
├── implementation_plan.md
├── requirements.txt
├── .env.default
├── init_db.py
├── deploy/
│   ├── deploy_to_pi.sh
│   └── garage-door.service
├── docs/
│   └── threat_model.md
├── data/
│   └── garage.db
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── auth.py
│   ├── gpio_controller.py
│   ├── alpr_engine.py
│   ├── camera_stream.py
│   ├── climate_monitor.py
│   ├── ups_monitor.py
│   ├── notification_service.py
│   ├── guest_access.py
│   ├── vacation_mode.py
│   ├── geofence.py
│   ├── voice_control.py
│   ├── analytics.py
│   ├── feature_toggles.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── door_routes.py
│   │   ├── alpr_routes.py
│   │   ├── guest_routes.py
│   │   ├── climate_routes.py
│   │   ├── analytics_routes.py
│   │   └── settings_routes.py
│   └── templates/
│       ├── layout.html
│       ├── login.html
│       ├── dashboard.html
│       ├── camera.html
│       ├── access_log.html
│       ├── guest_codes.html
│       ├── analytics.html
│       ├── climate.html
│       ├── settings.html
│       └── emergency.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── dashboard.js
│       ├── camera.js
│       ├── analytics.js
│       └── settings.js
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    ├── test_doors.py
    ├── test_alpr.py
    ├── test_guest.py
    └── test_toggles.py
```
