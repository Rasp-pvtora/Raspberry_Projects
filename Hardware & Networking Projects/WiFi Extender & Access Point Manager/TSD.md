# 📐 Technical Specification Document — WiFi Extender & Access Point Manager

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

### Table: `clients`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| mac_address | TEXT | NOT NULL UNIQUE |
| hostname | TEXT | |
| friendly_name | TEXT | |
| ip_address | TEXT | |
| interface | TEXT | (wlan0/wlan1) |
| first_seen | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| last_seen | DATETIME | |
| is_blocked | BOOLEAN | DEFAULT 0 |

### Table: `connection_log`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| client_id | INTEGER | FK → clients.id |
| event_type | TEXT | NOT NULL (connect/disconnect/blocked) |
| ip_address | TEXT | |
| signal_dbm | INTEGER | |
| timestamp | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `bandwidth_readings`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| client_id | INTEGER | FK → clients.id (NULL for total) |
| rx_bytes | INTEGER | NOT NULL |
| tx_bytes | INTEGER | NOT NULL |
| rx_rate_kbps | REAL | |
| tx_rate_kbps | REAL | |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `mac_filter`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| mac_address | TEXT | NOT NULL UNIQUE |
| list_type | TEXT | NOT NULL (whitelist/blacklist) |
| description | TEXT | |
| added_by | INTEGER | FK → users.id |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `qos_rules`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| client_id | INTEGER | FK → clients.id |
| mac_address | TEXT | NOT NULL |
| down_limit_kbps | INTEGER | |
| up_limit_kbps | INTEGER | |
| priority | INTEGER | DEFAULT 5 (1=highest, 10=lowest) |
| enabled | BOOLEAN | DEFAULT 1 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### Table: `wifi_schedule`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| day_of_week | TEXT | NOT NULL (mon/tue/wed/thu/fri/sat/sun) |
| on_time | TEXT | NOT NULL (HH:MM) |
| off_time | TEXT | NOT NULL (HH:MM) |
| enabled | BOOLEAN | DEFAULT 1 |

### Table: `health_checks`
| Column | Type | Constraints |
|--------|------|------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| latency_ms | REAL | |
| packet_loss_pct | REAL | |
| dns_resolve_ms | REAL | |
| internet_up | BOOLEAN | |
| checked_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

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

Total environment variables: **~55**

---

## 3. API Route Specifications

### Authentication
```
POST /api/auth/login
  Body: { "username": "...", "password": "..." }
  Response: { "token": "jwt...", "expires_in": 86400 }
  Rate Limit: 10 attempts / 15 min per IP
```

### Access Point Control
```
GET /api/ap/status
  Response: { "running": true, "ssid": "RaspberryPi-AP", "channel": 6,
              "clients_count": 5, "uptime_sec": 86400, "interface": "wlan0" }

POST /api/ap/restart
  Response: { "status": "restarting", "eta_sec": 10 }

PUT /api/ap/config
  Body: { "ssid": "MyNewSSID", "password": "NewPass123!", "channel": 11, "hidden": false }
  Response: { "updated": true, "restart_required": true }
```

### Client Management
```
GET /api/clients
  Response: [{ "mac": "AA:BB:CC:DD:EE:FF", "hostname": "iPhone-John",
               "ip": "10.0.0.15", "signal_dbm": -42, "rx_kbps": 1200,
               "tx_kbps": 350, "connected_since": "2026-04-02T08:30:00Z" }]

GET /api/clients/<mac>
  Response: { "mac": "AA:BB:CC:DD:EE:FF", "hostname": "iPhone-John",
              "total_rx_mb": 524, "total_tx_mb": 89, "sessions": 42 }

POST /api/clients/<mac>/disconnect
  Response: { "disconnected": true, "mac": "AA:BB:CC:DD:EE:FF" }
```

### Bandwidth
```
GET /api/bandwidth
  Response: { "total": { "rx_kbps": 5400, "tx_kbps": 1200 },
              "per_client": [{ "mac": "...", "rx_kbps": 1200, "tx_kbps": 350 }] }

GET /api/bandwidth/history?hours=24
  Response: { "labels": [...], "total_rx": [...], "total_tx": [...] }
```

### MAC Filtering
```
GET /api/mac-filter
  Response: { "mode": "whitelist",
              "entries": [{ "mac": "AA:BB:CC:DD:EE:FF", "description": "John's Phone" }] }

POST /api/mac-filter
  Body: { "mac": "AA:BB:CC:DD:EE:FF", "description": "John's Phone" }

DELETE /api/mac-filter/<mac>
  Response: { "removed": true }

PUT /api/mac-filter/mode
  Body: { "mode": "blacklist" }
  Response: { "mode": "blacklist", "active_entries": 3 }
```

### QoS
```
GET /api/qos/rules
  Response: [{ "mac": "...", "down_limit_kbps": 5000, "up_limit_kbps": 2000, "priority": 3 }]

PUT /api/qos/rules/<mac>
  Body: { "down_limit_kbps": 5000, "up_limit_kbps": 2000, "priority": 3 }
  Response: { "applied": true }
```

### WiFi Schedule
```
GET /api/schedule
  Response: [{ "day": "mon", "on_time": "07:00", "off_time": "23:00", "enabled": true }]

PUT /api/schedule
  Body: [{ "day": "mon", "on_time": "07:00", "off_time": "23:00", "enabled": true }]
```

### Feature Toggles (Dashboard-driven)
```
GET /api/settings/features
  Response: { "ENABLE_AUTO_SETUP": true, "ENABLE_MAC_FILTER": false, ... }

PUT /api/settings/features
  Body: { "ENABLE_QOS": true, "ENABLE_CAPTIVE_PORTAL": true }
  Response: { "updated": ["ENABLE_QOS", "ENABLE_CAPTIVE_PORTAL"] }
  Note: Updates both SQLite and .env file in real-time
```

---

## 4. WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `client_connected` | Server → Client | `{ "mac": "...", "hostname": "...", "ip": "...", "signal_dbm": -42 }` |
| `client_disconnected` | Server → Client | `{ "mac": "...", "hostname": "..." }` |
| `bandwidth_update` | Server → Client | `{ "total_rx_kbps": 5400, "total_tx_kbps": 1200, "clients": [...] }` |
| `health_update` | Server → Client | `{ "latency_ms": 12, "packet_loss": 0, "internet_up": true }` |
| `ap_status_change` | Server → Client | `{ "status": "running", "ssid": "...", "channel": 6 }` |
| `mac_blocked` | Server → Client | `{ "mac": "...", "reason": "blacklisted" }` |
| `toggle_feature` | Client → Server | `{ "feature": "ENABLE_QOS", "enabled": true }` |
| `feature_toggled` | Server → Client | `{ "feature": "ENABLE_QOS", "enabled": true }` |

---

## 5. System Configuration Files

### hostapd configuration template (`config/hostapd.conf.template`)
```
interface={{AP_INTERFACE}}
driver=nl80211
ssid={{AP_SSID}}
hw_mode={{AP_HW_MODE}}
channel={{AP_CHANNEL}}
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid={{AP_HIDDEN}}
wpa={{AP_WPA}}
wpa_passphrase={{AP_PASSWORD}}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
country_code={{AP_COUNTRY_CODE}}
```

### dnsmasq configuration template (`config/dnsmasq.conf.template`)
```
interface={{AP_INTERFACE}}
dhcp-range={{DHCP_RANGE_START}},{{DHCP_RANGE_END}},{{DHCP_LEASE_TIME}}
server={{DNS_PRIMARY}}
server={{DNS_SECONDARY}}
```

---

## 6. Threat Model

| # | Threat | Mitigation |
|---|--------|-----------|
| 1 | Brute-force login | bcrypt + 10 attempts/15min rate limit + account lockout |
| 2 | JWT token theft | 24h expiry, httpOnly secure cookies, token rotation |
| 3 | Rogue client access | MAC filtering (whitelist mode), captive portal gate |
| 4 | WiFi password cracking | WPA2/WPA3 enforcement, strong password requirements |
| 5 | ARP spoofing | Client isolation option in hostapd, ARP monitoring |
| 6 | DNS hijacking | Validate upstream DNS, DNSSEC when available |
| 7 | Bandwidth abuse | QoS per-client limits, bandwidth alerts |
| 8 | Unauthorized AP config | Dashboard auth required, config change audit log |
| 9 | Man-in-the-middle | HTTPS/TLS on dashboard, self-signed cert generation |
| 10 | .env file exposure | File permissions 600, not served by web server, gitignored |
| 11 | SQL injection | Parameterized queries exclusively |
| 12 | DoS on API | Flask-Limiter per-endpoint rate limiting |

---

## 7. Development Phases

| Phase | Description | Days |
|-------|-------------|------|
| 1 | Project setup, Flask skeleton, auth system | Day 1 |
| 2 | hostapd + dnsmasq auto-configuration | Day 1–2 |
| 3 | iptables NAT masquerade + IP forwarding | Day 2 |
| 4 | SQLite schema, client discovery, connection log | Day 2–3 |
| 5 | Web dashboard (dark theme, AP status, client list) | Day 3 |
| 6 | Bandwidth monitoring (iptables counters + parsing) | Day 3–4 |
| 7 | SSID/password/channel management + auto-channel scan | Day 4 |
| 8 | MAC address filtering (whitelist/blacklist) | Day 4–5 |
| 9 | QoS traffic shaping with tc | Day 5 |
| 10 | Captive portal with iptables redirect | Day 5–6 |
| 11 | WiFi schedule (cron-based on/off) | Day 6 |
| 12 | DNS configuration management | Day 6 |
| 13 | VPN passthrough (WireGuard/OpenVPN routing) | Day 7 |
| 14 | Dual-band support (second hostapd instance) | Day 7 |
| 15 | Network health monitoring (ping, DNS, latency) | Day 8 |
| 16 | Notification system (Telegram, Slack, email) | Day 8 |
| 17 | Feature toggle system (dashboard ↔ .env sync) | Day 8–9 |
| 18 | systemd service + deploy script + hardening | Day 9 |
| 19 | Testing, documentation, final review | Day 9–10 |

---

## 8. File Structure

```
WiFi Extender & Access Point Manager/
├── README.md
├── TSD.md
├── task.md
├── implementation_plan.md
├── requirements.txt
├── .env.default
├── init_db.py
├── setup_ap.py
├── config/
│   ├── hostapd.conf.template
│   ├── dnsmasq.conf.template
│   ├── mac_whitelist.txt
│   └── mac_blacklist.txt
├── deploy/
│   ├── deploy_to_pi.sh
│   └── wifi-extender.service
├── docs/
│   └── threat_model.md
├── data/
│   └── wifi_extender.db
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── auth.py
│   ├── ap_manager.py
│   ├── client_monitor.py
│   ├── bandwidth_tracker.py
│   ├── mac_filter.py
│   ├── captive_portal.py
│   ├── qos_manager.py
│   ├── wifi_scheduler.py
│   ├── channel_scanner.py
│   ├── dns_manager.py
│   ├── vpn_passthrough.py
│   ├── health_monitor.py
│   ├── notification_service.py
│   ├── feature_toggles.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── ap_routes.py
│   │   ├── client_routes.py
│   │   ├── bandwidth_routes.py
│   │   ├── mac_filter_routes.py
│   │   ├── qos_routes.py
│   │   ├── schedule_routes.py
│   │   ├── dns_routes.py
│   │   ├── health_routes.py
│   │   └── settings_routes.py
│   └── templates/
│       ├── layout.html
│       ├── login.html
│       ├── dashboard.html
│       ├── clients.html
│       ├── bandwidth.html
│       ├── mac_filter.html
│       ├── captive_portal.html
│       ├── qos.html
│       ├── schedule.html
│       ├── dns.html
│       ├── health.html
│       ├── connection_log.html
│       └── settings.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── dashboard.js
│       ├── clients.js
│       ├── bandwidth.js
│       ├── qos.js
│       └── settings.js
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    ├── test_ap_manager.py
    ├── test_client_monitor.py
    ├── test_bandwidth.py
    ├── test_mac_filter.py
    ├── test_qos.py
    └── test_toggles.py
```
