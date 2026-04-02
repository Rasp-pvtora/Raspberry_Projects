# 📐 Technical Specification Document — GPIO Data Logger & Pin Manager

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

### Table: `pin_configs`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| gpio_pin | INTEGER | UNIQUE (NULL for ADC) |
| adc_channel | INTEGER | UNIQUE (NULL for GPIO) |
| name | TEXT | NOT NULL |
| pin_type | TEXT | NOT NULL (digital_input/digital_output/analog_input/pwm_output) |
| enabled | BOOLEAN | DEFAULT 1 |
| poll_interval_ms | INTEGER | DEFAULT 1000 |
| edge_trigger | TEXT | (none/rising/falling/both) |
| unit | TEXT | DEFAULT '' |
| formula | TEXT | (conversion formula for analog) |
| threshold_high | REAL | |
| threshold_low | REAL | |
| group_id | INTEGER | FK → pin_groups.id |
| default_state | INTEGER | DEFAULT 0 (for outputs) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `pin_groups`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL UNIQUE |
| description | TEXT | |
| color | TEXT | DEFAULT '#58a6ff' |
| sort_order | INTEGER | DEFAULT 0 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `readings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| pin_config_id | INTEGER | FK → pin_configs.id, NOT NULL |
| value | REAL | NOT NULL |
| raw_value | REAL | (original ADC value before formula) |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `alerts`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| pin_config_id | INTEGER | FK → pin_configs.id, NOT NULL |
| alert_type | TEXT | NOT NULL (high_threshold/low_threshold/edge_change) |
| value | REAL | NOT NULL |
| threshold | REAL | |
| acknowledged | BOOLEAN | DEFAULT 0 |
| notified | BOOLEAN | DEFAULT 0 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `feature_toggles`
| Column | Type | Constraints |
|--------|------|------------|
| feature_key | TEXT | PRIMARY KEY |
| enabled | BOOLEAN | NOT NULL DEFAULT 0 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_by | INTEGER | FK → users.id |

### Table: `export_jobs`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| format | TEXT | NOT NULL (csv/json/sqlite) |
| pin_filter | TEXT | (JSON array of pin IDs or null for all) |
| date_from | DATETIME | |
| date_to | DATETIME | |
| file_path | TEXT | |
| status | TEXT | DEFAULT 'pending' (pending/running/done/error) |
| created_by | INTEGER | FK → users.id |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| completed_at | DATETIME | |

---

## 2. Pin Configuration File Format (`pins.json`)

```json
{
  "version": 1,
  "description": "GPIO Pin Configuration — Operator editable",
  "pins": [
    {
      "gpio": 4,
      "name": "Sensor Temperature B100",
      "type": "digital_input",
      "enabled": true,
      "poll_interval_ms": 2000,
      "group": "Kitchen Sensors",
      "thresholds": { "high": null, "low": null },
      "notes": "DHT22 connected to GPIO 4"
    }
  ]
}
```

On startup, the application:
1. Reads `pins.json` to discover pin configuration
2. Syncs pins.json → `pin_configs` SQLite table
3. Dashboard changes update both SQLite AND `pins.json` (bidirectional sync)
4. If `pins.json` is edited by hand, changes are picked up on next restart or via API reload

---

## 3. `.env.default` Template

> See full template in [README.md → Environment Variables](README.md#-environment-variables)

Total environment variables: **~42**

---

## 4. API Route Specifications

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

### Pin Management
```
GET /api/pins
  Response: [{ "id": 1, "gpio": 4, "name": "Sensor Temperature B100",
               "type": "digital_input", "enabled": true, "value": 22.5,
               "poll_interval_ms": 2000, "group": "Kitchen Sensors" }]

GET /api/pins/<gpio>
  Response: { "id": 1, "gpio": 4, "name": "...", "latest_value": 22.5,
              "readings_count": 4521, "last_read": "2026-04-02T10:30:00Z" }

POST /api/pins
  Body: { "gpio": 17, "name": "Front Door Button", "type": "digital_input",
          "poll_interval_ms": 100, "edge_trigger": "rising" }
  Response: { "id": 2, "gpio": 17, "created": true }

PUT /api/pins/<gpio>
  Body: { "name": "New Name", "enabled": false, "poll_interval_ms": 5000 }
  Response: { "gpio": 4, "updated": ["name", "enabled", "poll_interval_ms"] }

DELETE /api/pins/<gpio>
  Response: { "gpio": 4, "deleted": true, "readings_archived": 4521 }

POST /api/pins/<gpio>/output
  Body: { "state": 1 }
  Response: { "gpio": 23, "state": "HIGH" }

POST /api/pins/reload
  Response: { "message": "Pin configuration reloaded from pins.json", "pins": 5 }
```

### Pin Groups
```
GET /api/groups
  Response: [{ "id": 1, "name": "Kitchen Sensors", "pin_count": 3, "color": "#58a6ff" }]

POST /api/groups
  Body: { "name": "Garden Sensors", "color": "#3fb950" }
  Response: { "id": 2, "created": true }

PUT /api/groups/<id>
  Body: { "name": "Updated Name" }
  Response: { "id": 2, "updated": true }

DELETE /api/groups/<id>
  Response: { "id": 2, "deleted": true, "pins_ungrouped": 2 }
```

### Readings & Data
```
GET /api/pins/<gpio>/readings?from=2026-03-01&to=2026-04-01&limit=1000
  Response: { "pin": 4, "count": 1000, "readings": [{ "value": 22.5, "recorded_at": "..." }] }

GET /api/readings?pins=4,17,22&from=...&to=...&limit=5000
  Response: { "total": 5000, "readings": [{ "pin_gpio": 4, "value": 22.5, "recorded_at": "..." }] }
```

### Analytics
```
GET /api/analytics/summary?pin=4&period=week
  Response: { "pin": 4, "period": "week", "min": 18.2, "max": 28.1,
              "avg": 22.4, "stddev": 2.1, "count": 6048 }

GET /api/analytics/heatmap?pin=4&days=30
  Response: { "pin": 4, "matrix": [[...hour 0-23 values for each day...]] }

GET /api/analytics/trends?pins=4,0&days=90
  Response: { "labels": ["2026-01-01", ...], "datasets": [{ "pin": 4, "data": [...] }] }
```

### Export
```
GET /api/export?format=csv&pins=4,17&from=2026-03-01&to=2026-04-01
  Response: CSV file download

GET /api/export?format=json&pins=all&from=2026-03-01
  Response: JSON file download

GET /api/export?format=sqlite
  Response: SQLite database file download
```

### Alerts & Thresholds
```
GET /api/alerts?acknowledged=false
  Response: [{ "id": 1, "pin_gpio": 4, "type": "high_threshold",
               "value": 35.2, "threshold": 30.0, "created_at": "..." }]

POST /api/alerts/thresholds
  Body: { "gpio": 4, "high": 30.0, "low": 10.0 }
  Response: { "gpio": 4, "thresholds_updated": true }

PUT /api/alerts/<id>/acknowledge
  Response: { "id": 1, "acknowledged": true }
```

### Feature Toggles (Dashboard-driven)
```
GET /api/settings/features
  Response: { "ENABLE_PIN_CONFIG": true, "ENABLE_CSV_LOGGING": true, ... }

PUT /api/settings/features
  Body: { "ENABLE_ADC": true, "ENABLE_EDGE_LOGGING": true }
  Response: { "updated": ["ENABLE_ADC", "ENABLE_EDGE_LOGGING"], "message": "Features updated" }
  Note: Updates both SQLite and .env file in real-time
```

---

## 5. WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `pin_reading` | Server → Client | `{ "gpio": 4, "value": 22.5, "timestamp": "..." }` |
| `pin_edge` | Server → Client | `{ "gpio": 17, "edge": "rising", "timestamp": "..." }` |
| `threshold_alert` | Server → Client | `{ "gpio": 4, "type": "high", "value": 35.2, "threshold": 30.0 }` |
| `pin_config_changed` | Server → Client | `{ "gpio": 4, "changes": { "name": "New Name" } }` |
| `adc_reading` | Server → Client | `{ "channel": 0, "raw": 512, "converted": 50.1, "unit": "%" }` |
| `export_complete` | Server → Client | `{ "job_id": 1, "format": "csv", "file_path": "..." }` |
| `toggle_feature` | Client → Server | `{ "feature": "ENABLE_ADC", "enabled": true }` |
| `feature_toggled` | Server → Client | `{ "feature": "ENABLE_ADC", "enabled": true }` |

---

## 6. Threat Model

| # | Threat | Mitigation |
|---|--------|-----------|
| 1 | Brute-force login | bcrypt + 10 attempts/15min rate limit + account lockout |
| 2 | JWT token theft | 24h expiry, httpOnly secure cookies, token rotation |
| 3 | Unauthorized GPIO control | JWT required for all API endpoints, role-based access |
| 4 | Pin configuration tampering | File permissions 600 on pins.json, audit log on changes |
| 5 | SQL injection | Parameterized queries exclusively, no raw SQL interpolation |
| 6 | Data exfiltration via export | Export API requires auth, rate limited, logged |
| 7 | ADC data manipulation | Input validation on all sensor readings, range checks |
| 8 | Man-in-the-middle | HTTPS/TLS on all endpoints, self-signed cert generation script |
| 9 | .env file exposure | File permissions 600, not served by web server, gitignored |
| 10 | Disk exhaustion from logging | Data retention policy, rotation, archive + purge |
| 11 | DoS on API | Flask-Limiter per-endpoint rate limiting |
| 12 | GPIO pin conflict | Pin reservation system, validation on startup, lock file |

---

## 7. Development Phases

| Phase | Description | Days |
|-------|-------------|------|
| 1 | Project setup, Flask skeleton, auth system | Day 1 |
| 2 | Pin configuration file parser + validator | Day 1–2 |
| 3 | GPIO digital input reading + polling scheduler | Day 2 |
| 4 | SQLite schema, reading storage, event logging | Day 2–3 |
| 5 | Web dashboard (dark theme, pin cards, live values) | Day 3 |
| 6 | Pin Manager UI (visual GPIO layout, drag-and-drop) | Day 3–4 |
| 7 | CSV + JSON logging engines with rotation | Day 4 |
| 8 | MCP3008 ADC analog input support | Day 4–5 |
| 9 | Edge-triggered logging with interrupt callbacks | Day 5 |
| 10 | Threshold alert system + notification dispatch | Day 5–6 |
| 11 | Real-time Chart.js visualization + WebSocket push | Day 6 |
| 12 | Data retention, rotation, archive policy | Day 6–7 |
| 13 | Export engine (CSV/JSON/SQLite download) | Day 7 |
| 14 | Analytics engine (min/max/avg, heatmap, trends) | Day 7–8 |
| 15 | Pin grouping + group dashboard views | Day 8 |
| 16 | Feature toggle system (dashboard ↔ .env sync) | Day 8–9 |
| 17 | systemd service + deploy script + hardening | Day 9 |
| 18 | Testing, documentation, final review | Day 9–10 |

---

## 8. File Structure

```
GPIO Data Logger & Pin Manager/
├── README.md
├── TSD.md
├── task.md
├── implementation_plan.md
├── requirements.txt
├── .env.default
├── pins.default.json
├── init_db.py
├── deploy/
│   ├── deploy_to_pi.sh
│   └── gpio-logger.service
├── docs/
│   └── threat_model.md
├── data/
│   ├── gpio_logger.db
│   ├── csv/
│   ├── json/
│   └── archive/
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── auth.py
│   ├── pin_config.py
│   ├── gpio_reader.py
│   ├── adc_reader.py
│   ├── polling_scheduler.py
│   ├── edge_detector.py
│   ├── csv_logger.py
│   ├── json_logger.py
│   ├── sqlite_logger.py
│   ├── threshold_monitor.py
│   ├── notification_service.py
│   ├── analytics.py
│   ├── data_export.py
│   ├── data_retention.py
│   ├── feature_toggles.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── pin_routes.py
│   │   ├── group_routes.py
│   │   ├── readings_routes.py
│   │   ├── analytics_routes.py
│   │   ├── export_routes.py
│   │   ├── alert_routes.py
│   │   └── settings_routes.py
│   └── templates/
│       ├── layout.html
│       ├── login.html
│       ├── dashboard.html
│       ├── pin_manager.html
│       ├── live_charts.html
│       ├── data_browser.html
│       ├── analytics.html
│       ├── alerts.html
│       ├── export.html
│       └── settings.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── dashboard.js
│       ├── pin_manager.js
│       ├── live_charts.js
│       ├── analytics.js
│       └── settings.js
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    ├── test_pin_config.py
    ├── test_gpio_reader.py
    ├── test_adc_reader.py
    ├── test_csv_logger.py
    ├── test_analytics.py
    ├── test_export.py
    └── test_toggles.py
```
