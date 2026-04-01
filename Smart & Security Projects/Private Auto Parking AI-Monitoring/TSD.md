# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for **Private Auto Parking AI-Monitoring**.

---

## 1. Scope

This project builds an AI-driven parking monitoring system using Raspberry Pi cameras. It combines YOLOv11n vehicle detection, PaddleOCR license plate recognition, zone-based occupancy tracking, and a real-time web dashboard to provide a comprehensive solution for managing private parking spaces. Features include an interactive parking map, entry/exit gate integration, violation detection, multi-camera support, and analytics.

**Key goals:**
- Real-time vehicle detection and parking spot occupancy tracking.
- License plate recognition for access control and logging.
- Interactive parking map with live spot status.
- GPIO-controlled barrier gate for authorized vehicles.
- Violation detection (overtime, unauthorized, no-parking zone).
- Multi-camera support for full lot coverage.
- Analytics dashboard with occupancy trends and reports.
- MQTT integration for IoT platforms.

---

## 2. Minimum Viable Features (MVP)

### 2.1 Detection Pipeline

| Stage | Component | Tool | Description |
|---|---|---|---|
| **Capture** | Camera Manager | Picamera2 / OpenCV | Captures frames from Pi Camera or USB webcams |
| **Detect** | Vehicle Detector | YOLOv11n (ultralytics) | Detects vehicles (car, truck, motorcycle, bus) |
| **Track** | Occupancy Tracker | Polygon zone logic | Maps detections to defined parking spots |
| **Read plate** | Plate Reader | PaddleOCR | OCR on detected vehicle to read plate text |
| **Log** | Vehicle Log | SQLite/PostgreSQL | Entry/exit with plate, timestamp, spot, duration |
| **Violations** | Violation Detector | Rule engine | Overtime, no-parking, unauthorized |
| **Gate** | Gate Controller | GPIO relay | Auto-open for authorized plates |
| **Notify** | Notification Service | Telegram/Email/MQTT | Alerts on violations and events |
| **Stream** | WebSocket | Flask-SocketIO | Real-time dashboard updates |

### 2.2 Vehicle Detection (YOLOv11n)

- COCO vehicle classes: car, truck, motorcycle, bus, bicycle.
- Configurable classes and confidence threshold.
- Vehicle type classification (compact, SUV, truck, motorcycle).

### 2.3 Parking Occupancy Tracking

- Each spot defined as a polygon zone on the camera frame.
- Spot status: free (green), occupied (red), violation (yellow), disabled (gray).
- Real-time occupancy count.
- Zone drawing from the dashboard.

### 2.4 License Plate Recognition

- PaddleOCR engine for plate text extraction.
- Authorized plate whitelist for gate control.
- Vehicle log with plate, entry/exit time, duration.
- Dashboard search by plate number.

### 2.5 Parking Map Visualization

- Interactive SVG/Canvas map on the dashboard.
- Color-coded spots with real-time updates.
- Click a spot for details (plate, duration, vehicle type).
- Draw/configure spots from the dashboard.

### 2.6 Entry/Exit Gate Integration

- GPIO relay controls barrier gate motor.
- Auto-open for whitelisted plates.
- Manual override from dashboard.
- Configurable open duration.

### 2.7 Violation Detection

- Overtime: vehicle exceeds max parking duration.
- No-parking zone: vehicle in marked no-parking area.
- Unauthorized: plate not in whitelist (if whitelist mode).
- Wrong spot type: large vehicle in compact-only spot.
- Violation log with management (resolve, export).

### 2.8 Multi-Camera Support

- Independent detection pipeline per camera.
- Unified parking map and vehicle log.
- Pi Camera, USB webcams, RTSP/IP cameras.
- Multi-Pi support for large lots (shared PostgreSQL).

### 2.9 Analytics Dashboard

- Occupancy over time (line chart).
- Peak hours (bar chart).
- Average parking duration.
- Vehicle type distribution (pie chart).
- Monthly summary reports.
- CSV/PDF export.

### 2.10 Web Dashboard (Flask + SocketIO + Jinja2)

- **Authentication:** Session-based login with rate limiting.
- **Dashboard:** Occupancy overview, alerts, key stats, mini parking map.
- **Parking Map:** Interactive full map with spot status.
- **Vehicles:** Entry/exit log, plate search, duration history.
- **Violations:** Violation list, management, resolution.
- **Analytics:** Charts with Chart.js.
- **Cameras:** Multi-camera configuration.
- **Settings:** Detection, gate, notifications, spot config.

### 2.11 Notifications

- Telegram: violations, unauthorized vehicle, lot full.
- Email: daily reports, violation summary.
- MQTT: all events for IoT integration.

### 2.12 MQTT Integration

- Publish occupancy changes, entry/exit, violations, gate actions.
- Compatible with Home Assistant and other IoT platforms.

### 2.13 Environment Configuration

- All configuration via `.env` file.
- Settings page provides web-based editor.

### 2.14 Deployment

- `deploy/deploy_to_pi.sh` script.
- Setup scripts for camera, models, PaddleOCR.
- Systemd service file.

---

## 3. Nice-to-Have Features

### 3.1 Cloud LPR API

- Use a cloud OCR service (e.g., [Plate Recognizer API](https://platerecognizer.com/)) for higher accuracy.
- Free tier: 2,500 lookups/month. Paid for more.
- Falls back to local PaddleOCR if cloud is unreachable.

### 3.2 ANPR Camera Integration

- Professional ANPR (Automatic Number Plate Recognition) cameras with built-in LPR.
- Higher accuracy and speed than software-based OCR.
- Significantly more expensive ($200–$1,000+ per camera).

### 3.3 Mobile App

- Companion mobile app for parking spot availability and gate remote control.
- Requires mobile development (Flutter/React Native) and push notifications.

### 3.4 Payment Integration

- Hourly/daily parking fees calculated automatically.
- Payment gateway integration (Stripe, PayPal).
- Requires business account and PCI compliance.

### 3.5 Traffic Flow Heatmap

- Heatmap visualization of vehicle movement patterns across the lot.
- Requires vehicle tracking across frames (object tracking, not just detection).

---

## 4. High-Level Architecture

```
                      ┌────────────────────────────────────────────────────┐
                      │            Raspberry Pi                            │
                      │                                                    │
  Browser ─HTTP────► │  Flask (port 5000)                                  │
  Browser ──WS─────► │  ├── Session auth + rate limiting                   │
                      │  ├── Jinja2 templates (dashboard, map, etc.)       │
                      │  ├── REST API (/api/parking, /api/vehicles, etc.)  │
                      │  ├── SocketIO (live map + alerts)                  │
                      │  └── Static files (CSS, JS, parking map)           │
                      │                                                    │
                      │  Detection Pipeline:                                │
                      │  ┌──────────────────────────────────────────┐      │
                      │  │ Camera → YOLOv11n (detect vehicles)     │      │
                      │  │       → PaddleOCR (read plates)          │      │
                      │  │       → Occupancy Tracker (spot status)  │      │
                      │  │       → Violation Detector (rules)       │      │
                      │  │       → Gate Controller (GPIO relay)     │      │
                      │  │       → Vehicle Log (DB)                 │      │
                      │  │       → WebSocket (dashboard update)     │      │
                      │  │       → MQTT (IoT publish)               │      │
                      │  └──────────────────────────────────────────┘      │
                      │                                                    │
                      │  Storage:                                           │
                      │  ├── SQLite/PostgreSQL (vehicles, violations)       │
                      │  └── models/ (YOLO weights)                        │
                      │                                                    │
                      │  Hardware:                                          │
                      │  ├── Camera(s) (Pi Camera, USB, RTSP)              │
                      │  └── GPIO relay → barrier gate motor               │
                      └────────────────────────────────────────────────────┘
```

---

## 5. Security and Threat Model

**Primary assets:**
- Dashboard credentials and session tokens.
- License plate data (PII).
- Vehicle entry/exit logs.
- Authorized plate whitelist.
- Gate GPIO control (physical security).
- `.env` file (all secrets).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Brute-force login | Rate limiting; strong password |
| Session hijacking | `httpOnly`, `sameSite` cookies; strong session secret |
| License plate data leak | Local storage only; data retention policies; access-controlled |
| Gate unauthorized control | Authentication required; GPIO protected |
| Camera feed interception | LAN-only; authentication required; no public stream |
| MQTT data exposure | MQTT broker with authentication; encrypted transport (TLS) |
| SQL injection | Parameterized queries only |
| XSS via plate data | HTML-escape all output in templates |
| `.env` exposure | `.gitignore`; `chmod 600` |
| Data retention (GDPR/privacy) | Configurable auto-delete for old records; data minimization |

See [docs/threat_model.md](docs/threat_model.md) for the complete analysis.

---

## 6. Suggested Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| Backend | Python 3.11+ / Flask | Mature, great ML ecosystem |
| Real-time | Flask-SocketIO | WebSocket for live map and alerts |
| Templating | Jinja2 | Server-side rendering, no build step |
| Detection | ultralytics (YOLOv11n) | State-of-the-art, easy training |
| OCR | PaddleOCR | Open-source, good plate accuracy |
| Database | SQLite (single Pi) / PostgreSQL (multi-Pi) | Lightweight or scalable |
| Charts | Chart.js (CDN) | Lightweight, responsive analytics |
| Gate control | RPi.GPIO | Standard Pi GPIO |
| IoT | paho-mqtt | Standard MQTT client |
| Notifications | Telegram Bot API, SMTP | Free channels |
| Auth | Session-based + bcrypt | Simple, single-user |
| CSS | Custom dark theme | Lightweight |

---

## 7. Development Phases & Concrete Steps

### Phase A — Project scaffold and vehicle detection (Week 1)

1. Initialize Python project with `requirements.txt` and virtual environment.
2. Create `.env.default` template and `.gitignore`.
3. Implement Flask server with Jinja2 layout and sidebar navigation.
4. Implement session-based authentication.
5. Create dark-themed CSS and login page.
6. Integrate YOLOv11n for vehicle detection.
7. Implement camera manager (Pi Camera + USB fallback).
8. Build Dashboard page with live camera feed.

### Phase B — Parking map and occupancy (Week 1–2)

1. Implement parking spot zone definitions (polygon areas).
2. Implement occupancy tracker (map detections to spots).
3. Build Parking Map page with interactive SVG/Canvas.
4. Implement spot drawing/configuration from dashboard.
5. Implement WebSocket for real-time map updates.

### Phase C — LPR and vehicle logging (Week 2)

1. Integrate PaddleOCR for license plate recognition.
2. Implement vehicle log service (entry/exit, plate, duration, spot).
3. Build Vehicles page (log, plate search, history).
4. Implement authorized plate whitelist.

### Phase D — Gate, violations, and notifications (Week 2–3)

1. Implement gate controller (GPIO relay).
2. Implement auto-gate for authorized plates.
3. Implement violation detector (overtime, unauthorized, no-parking).
4. Build Violations page (list, management, export).
5. Implement Telegram, email, and MQTT notifications.
6. Implement MQTT publisher for all events.

### Phase E — Multi-camera and analytics (Week 3)

1. Implement multi-camera support (independent pipelines).
2. Build Cameras page (add, configure, remove cameras).
3. Implement analytics service (occupancy trends, peak hours, reports).
4. Build Analytics page with Chart.js charts.
5. Implement CSV/PDF export for reports.
6. Build Settings page (all configurations).

### Phase F — Deployment and documentation (Week 3–4)

1. Create setup scripts (camera, models, PaddleOCR).
2. Write deployment script `deploy/deploy_to_pi.sh`.
3. Create systemd service file.
4. Test on Raspberry Pi 4 and Pi 5.
5. Write `README.md`, `TSD.md`, `task.md`, `docs/threat_model.md`.

---

## 8. Deliverables

- Full working parking monitoring system with YOLOv11n vehicle detection.
- License plate recognition with PaddleOCR.
- Interactive parking map with real-time occupancy.
- GPIO-controlled barrier gate for authorized plates.
- Violation detection and management.
- Multi-camera support.
- Analytics dashboard with Chart.js.
- MQTT integration for IoT platforms.
- Notifications via Telegram, email, and MQTT.
- Web dashboard with parking map, vehicles, violations, analytics.
- Deploy script for Raspberry Pi (SSH alias: `rasp-pi` at `192.168.216.90`).
- `README.md`, `TSD.md`, `task.md`, `docs/threat_model.md`.
