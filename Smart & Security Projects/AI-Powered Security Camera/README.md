# AI-Powered Security Camera

An intelligent security camera system for Raspberry Pi that uses machine learning for object detection, facial recognition, and pet/animal detection. Only sends notifications when a person, specific object, or known face is detected — reducing false alarms. Includes zone-based detection, multi-camera support, custom face enrollment, event timeline with video clips, and a real-time web dashboard.

🪙 **Donations are Welcome!**
If you find this project helpful, you can support my work with a small donation.
₿ Bitcoin donation: `bc1q...`

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Budget](#budget)
4. [Libraries and dependencies](#libraries-and-dependencies)
5. [Detection model comparison — YOLOv11n vs TFLite](#detection-model-comparison--yolov11n-vs-tflite)
6. [Quickstart — Laptop (development)](#quickstart--laptop-development)
7. [Environment configuration (.env)](#environment-configuration-env)
8. [Detection pipeline overview](#detection-pipeline-overview)
9. [Feature 1 — Object detection (YOLOv11n)](#feature-1--object-detection-yolov11n)
10. [Feature 2 — Facial recognition and enrollment](#feature-2--facial-recognition-and-enrollment)
11. [Feature 3 — Pet and animal detection](#feature-3--pet-and-animal-detection)
12. [Feature 4 — Zone-based detection](#feature-4--zone-based-detection)
13. [Feature 5 — Multi-camera support](#feature-5--multi-camera-support)
14. [Feature 6 — Event timeline with video clips](#feature-6--event-timeline-with-video-clips)
15. [Feature 7 — Night vision (Pi NoIR + IR)](#feature-7--night-vision-pi-noir--ir)
16. [Feature 8 — Web dashboard](#feature-8--web-dashboard)
17. [Notifications](#notifications)
18. [Hardware acceleration (future upgrade)](#hardware-acceleration-future-upgrade)
19. [Authentication](#authentication)
20. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
21. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
22. [Real-world applications](#real-world-applications)
23. [Security notes](#security-notes)
24. [Troubleshooting](#troubleshooting)
25. [Where to next](#where-to-next)

---

## Project structure

```
.
├── app.py                     ← Python entry point (Flask + WebSocket)
├── requirements.txt           ← Python dependencies
├── .env.default               ← Environment variable template (copy to .env)
├── .gitignore                 ← Git ignore rules
├── src/
│   ├── detection/
│   │   ├── yolo_detector.py   ← YOLOv11n object detection engine
│   │   ├── face_recognizer.py ← Face recognition and enrollment
│   │   ├── zone_manager.py    ← Zone-based detection (inclusion/exclusion)
│   │   └── pet_detector.py    ← Pet/animal classification (COCO classes)
│   ├── camera/
│   │   ├── camera_manager.py  ← Multi-camera management
│   │   ├── picamera_source.py ← Pi Camera (Picamera2) source
│   │   └── usb_camera_source.py ← USB webcam (OpenCV) source
│   ├── recording/
│   │   ├── clip_recorder.py   ← Event-triggered video clip recording
│   │   └── storage_manager.py ← Clip storage, rotation, and cleanup
│   ├── notifications/
│   │   ├── telegram_notify.py ← Telegram Bot notifications
│   │   ├── email_notify.py    ← SMTP email notifications
│   │   └── mqtt_notify.py     ← MQTT publish notifications
│   ├── routes/
│   │   ├── auth.py            ← Login / logout routes
│   │   ├── dashboard.py       ← Dashboard and live stream API
│   │   ├── events.py          ← Event timeline API
│   │   ├── faces.py           ← Face enrollment API
│   │   ├── zones.py           ← Zone configuration API
│   │   ├── cameras.py         ← Camera management API
│   │   └── settings.py        ← Settings API
│   └── services/
│       ├── event_service.py   ← Event logging and retrieval
│       ├── system_service.py  ← System info (temp, memory, disk)
│       └── db.py              ← SQLite database initialization
├── models/                    ← Detection models (auto-downloaded)
│   ├── yolov11n.pt            ← YOLOv11n weights
│   └── face_encodings.pkl     ← Enrolled face encodings
├── clips/                     ← Recorded event video clips
├── templates/                 ← Jinja2 HTML templates
│   ├── layout.html            ← Base layout with sidebar navigation
│   ├── login.html             ← Login page
│   ├── dashboard.html         ← Live stream + detection overlay
│   ├── events.html            ← Event timeline with clips
│   ├── faces.html             ← Face enrollment and management
│   ├── zones.html             ← Zone drawing interface
│   ├── cameras.html           ← Multi-camera configuration
│   └── settings.html          ← Notification and detection settings
├── static/                    ← Static frontend assets
│   ├── css/style.css          ← Dark theme dashboard stylesheet
│   └── js/
│       ├── main.js            ← WebSocket client for live stream
│       ├── dashboard.js       ← Dashboard detection overlay logic
│       ├── events.js          ← Event timeline logic
│       ├── faces.js           ← Face enrollment UI logic
│       ├── zones.js           ← Zone drawing canvas logic
│       └── cameras.js         ← Camera management logic
├── scripts/
│   ├── setup-camera.sh        ← Camera module setup (enable CSI)
│   ├── download-models.sh     ← Download YOLOv11n weights
│   └── setup-ir.sh            ← IR LED board setup (optional)
├── deploy/
│   └── deploy_to_pi.sh        ← rsync-based deploy script
├── docs/
│   └── threat_model.md        ← Threat model and mitigations
├── tests/                     ← Test directory
├── README.md                  ← This file
├── TSD.md                     ← Technical Specification Description
└── task.md                    ← Engineering checklist
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB+) / Pi 5 | Yes | Pi 5 recommended for inference speed; 4 GB minimum |
| microSD card (32 GB+) | Yes | For OS, models, and event clip storage |
| Pi Camera Module v2 or v3 | Yes | CSI camera; or use a USB webcam |
| Power supply (official) | Yes | 5V 3A for Pi 4, 5V 5A for Pi 5 |
| Ethernet or WiFi | Yes | For notifications and remote dashboard access |
| Pi NoIR Camera + IR LED board | Optional | For night vision capability |
| USB webcam(s) | Optional | For multi-camera support or as primary camera |
| Google Coral USB Accelerator | Optional | For hardware-accelerated inference (future upgrade) |

---

## Budget

| Item | Estimated Price (USD) | Notes |
|---|---|---|
| Pi Camera Module v2 | $25 – $30 | Standard CSI camera; v3 is ~$35 |
| Camera ribbon cable | $3 – $5 | Included with most Pi camera modules |
| Camera mount / case | $5 – $15 | 3D-printed or purchased enclosure |
| **Optional:** Pi NoIR Camera Module v2 | $25 – $30 | No IR filter — required for night vision |
| **Optional:** IR LED board (850nm) | $5 – $10 | Provides invisible illumination for night vision |
| **Optional:** Additional USB webcam | $15 – $30 | For multi-camera setup |
| **Optional:** Google Coral USB Accelerator | $60 – $75 | 10x faster inference (future upgrade) |
| **Total (minimum)** | **~$33 – $50** | Pi Camera + cable + mount |

> **Note:** The Raspberry Pi itself, microSD card, and power supply are not included in the budget above.

---

## Libraries and dependencies

### Python dependencies

| Library | Version | Purpose |
|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | ^3.1.0 | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | ^5.4.0 | WebSocket for live video stream |
| [Jinja2](https://jinja.palletsprojects.com/) | ^3.1.4 | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ^1.0.1 | Load environment variables from `.env` |
| [ultralytics](https://github.com/ultralytics/ultralytics) | ^8.3.0 | YOLOv11n object detection |
| [opencv-python-headless](https://pypi.org/project/opencv-python-headless/) | ^4.10.0 | Video capture, processing, and encoding |
| [face_recognition](https://github.com/ageitgame/face_recognition) | ^1.3.0 | Face detection and recognition (dlib) |
| [numpy](https://numpy.org/) | ^1.26.0 | Array operations for image processing |
| [Pillow](https://python-pillow.org/) | ^10.4.0 | Image manipulation |
| [picamera2](https://github.com/raspberrypi/picamera2) | ^0.3.0 | Pi Camera interface (Pi only) |
| [bcrypt](https://pypi.org/project/bcrypt/) | ^4.2.0 | Password hashing |
| [paho-mqtt](https://pypi.org/project/paho-mqtt/) | ^2.1.0 | MQTT notifications |
| [python-telegram-bot](https://python-telegram-bot.org/) | ^21.0 | Telegram Bot notifications |

### Dev dependencies

| Library | Version | Purpose |
|---|---|---|
| [pytest](https://docs.pytest.org/) | ^8.3.0 | Testing framework |

### System packages (installed on the Pi)

| Package | Purpose |
|---|---|
| `libcamera-apps` | Camera stack for Pi Camera Module |
| `cmake`, `build-essential` | Compiling dlib (required by face_recognition) |
| `libatlas-base-dev` | BLAS library for numpy/dlib |
| `libhdf5-dev` | HDF5 for model storage |
| `Python 3.11+` | Python runtime |

---

## Detection model comparison — YOLOv11n vs TFLite

This project uses **YOLOv11n** as the default detection engine. Here is a comparison to help choose the right model for your use case:

| Feature | YOLOv11n | TFLite (MobileNetV2-SSD) |
|---|---|---|
| **Velocity** | 8–13 FPS | 15–20 FPS |
| **Precision** | Very high | Average |
| **Easy-to-use** | `ultralytics` library (few lines) | More complex setup |
| **Tasks supported** | Detection, Segmentation, Pose, OBB | Detection only |

### When to use YOLOv11n (default — recommended)

- **Maximum precision** — YOLOv11n detects and distinguishes similar objects with high accuracy. Critical for security cameras where you need to tell a person from a shadow.
- **Fast development** — The `ultralytics` library provides training, validation, and model export in just a few lines of Python:
  ```python
  from ultralytics import YOLO
  model = YOLO("yolo11n.pt")
  results = model.predict(frame)
  ```
- **Multi-task support** — Beyond detection, YOLOv11n supports segmentation (pixel-level masks), pose estimation (body keypoints), and oriented bounding boxes (OBB) — useful for future upgrades.
- **Custom model training** — Train on your own dataset (e.g., specific pet breeds, vehicles) with the same `ultralytics` API.

### When to use TFLite (MobileNetV2-SSD)

- **Maximum frame rate** — If you need 15–20 FPS for tracking fast-moving objects (e.g., vehicles in a parking lot).
- **Google ecosystem** — Native integration with TensorFlow, TensorFlow Lite, and Google Cloud services.
- **Hardware acceleration** — TFLite natively supports the **Google Coral Edge TPU**, which can push inference to 50+ FPS. If you plan to use a Coral USB Accelerator in the future, TFLite is the natural path.
- **Lower memory footprint** — MobileNetV2-SSD uses less RAM than YOLO, leaving more room for other services.

> **This project defaults to YOLOv11n.** TFLite integration is documented in the TSD as an alternative for users who prioritize frame rate or plan to use Coral hardware.

---

## Quickstart — Laptop (development)

**1. Clone the repository**

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/AI-Powered Security Camera"
```

**2. Create the `.env` file from the template**

```bash
# Linux / macOS
cp .env.default .env

# Windows
copy .env.default .env
```

Edit `.env` and set your values (at minimum, change `SESSION_SECRET` and `ADMIN_PASSWORD`).

**3. Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

**4. Download the YOLOv11n model**

```bash
bash scripts/download-models.sh
```

**5. Start the development server**

```bash
python app.py
```

**6. Open the dashboard**

Navigate to `http://localhost:5000` in your browser.

- **Username:** `admin` (or whatever you set in `.env`)
- **Password:** `changeme` (or whatever you set in `.env`)

> **Note:** On a laptop, the system uses the built-in webcam (if available). Pi Camera features are simulated. All dashboard features (zones, faces, events, settings) work fully.

---

## Environment configuration (.env)

Copy `.env.default` to `.env` and edit it. **Never commit `.env` to git.**

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Dashboard web server port |
| `HOST` | `0.0.0.0` | Listen address |
| `SESSION_SECRET` | `CHANGE_ME...` | Random string for session encryption |
| `ADMIN_USERNAME` | `admin` | Dashboard login username |
| `ADMIN_PASSWORD` | `changeme` | Dashboard login password |
| `CAMERA_SOURCE` | `picamera` | Camera source: `picamera`, `usb`, or device index (`0`, `1`) |
| `CAMERA_RESOLUTION` | `1280x720` | Camera resolution (WxH) |
| `CAMERA_FPS` | `15` | Target capture frame rate |
| `DETECTION_MODEL` | `yolov11n` | Detection model: `yolov11n` or `tflite` |
| `DETECTION_CONFIDENCE` | `0.5` | Minimum detection confidence (0.0–1.0) |
| `DETECTION_CLASSES` | `person,cat,dog,car` | Comma-separated COCO classes to detect |
| `FACE_RECOGNITION_ENABLED` | `true` | Enable facial recognition |
| `FACE_RECOGNITION_TOLERANCE` | `0.6` | Face match tolerance (lower = stricter) |
| `ZONE_ENABLED` | `true` | Enable zone-based detection |
| `CLIP_RECORDING_ENABLED` | `true` | Record video clips on detection events |
| `CLIP_DURATION_SEC` | `10` | Duration of each event clip (seconds) |
| `CLIP_PRE_BUFFER_SEC` | `3` | Seconds of video to keep before detection trigger |
| `CLIP_STORAGE_MAX_GB` | `10` | Maximum storage for clips (auto-rotate oldest) |
| `NIGHT_VISION_ENABLED` | `false` | Enable IR camera mode (Pi NoIR + IR LEDs) |
| `IR_GPIO_PIN` | `18` | GPIO pin connected to IR LED board |
| `NOTIFY_TELEGRAM_ENABLED` | `false` | Enable Telegram notifications |
| `NOTIFY_TELEGRAM_TOKEN` | `` | Telegram Bot API token |
| `NOTIFY_TELEGRAM_CHAT_ID` | `` | Telegram chat ID for notifications |
| `NOTIFY_EMAIL_ENABLED` | `false` | Enable email notifications |
| `NOTIFY_EMAIL_SMTP` | `smtp.gmail.com` | SMTP server |
| `NOTIFY_EMAIL_PORT` | `587` | SMTP port |
| `NOTIFY_EMAIL_USER` | `` | SMTP username |
| `NOTIFY_EMAIL_PASSWORD` | `` | SMTP password (use app-specific password) |
| `NOTIFY_EMAIL_TO` | `` | Recipient email address |
| `NOTIFY_MQTT_ENABLED` | `false` | Enable MQTT notifications |
| `NOTIFY_MQTT_BROKER` | `localhost` | MQTT broker address |
| `NOTIFY_MQTT_TOPIC` | `security/camera/events` | MQTT topic for events |

---

## Detection pipeline overview

| Stage | Component | Tool | What it does |
|---|---|---|---|
| **1. Capture** | Camera Manager | Picamera2 / OpenCV | Captures video frames from Pi Camera or USB webcam |
| **2. Detect** | YOLOv11n | ultralytics | Detects objects (person, car, animal) with bounding boxes |
| **3. Recognize** | Face Recognizer | face_recognition (dlib) | Identifies known faces from enrolled database |
| **4. Zone check** | Zone Manager | Custom polygon logic | Checks if detection is inside an inclusion/exclusion zone |
| **5. Record** | Clip Recorder | OpenCV VideoWriter | Saves a 10-second video clip with pre-buffer |
| **6. Notify** | Notification Service | Telegram / Email / MQTT | Sends alert with snapshot and detection details |
| **7. Log** | Event Service | SQLite | Stores event metadata (time, class, confidence, face, zone) |
| **8. Stream** | WebSocket | Flask-SocketIO | Sends annotated frame to the dashboard in real time |

---

## Feature 1 — Object detection (YOLOv11n)

The default detection engine uses YOLOv11n (nano) — the latest YOLO generation optimized for edge devices.

- **COCO-trained:** Detects 80 object classes out of the box (person, car, truck, bicycle, cat, dog, bird, etc.).
- **Configurable classes:** Set `DETECTION_CLASSES` in `.env` to only detect specific classes (e.g., `person,car`).
- **Confidence threshold:** Adjust `DETECTION_CONFIDENCE` to filter weak detections.
- **Bounding boxes with labels:** Each detection is drawn on the video stream with class name and confidence.

**From the dashboard:**
- See live detections overlaid on the camera feed.
- Filter the feed by detection class.
- View detection statistics (count by class over time).

---

## Feature 2 — Facial recognition and enrollment

Identify known people by face, not just detect "a person."

- **Face enrollment from the dashboard:**
  - Upload photos of known people (name + one or more photos).
  - Or capture a face directly from the live camera feed — click "Enroll" on a detected face.
  - The system computes and stores a 128-dimensional face encoding.
- **Real-time matching:**
  - When a person is detected, the face recognizer compares the face against all enrolled encodings.
  - If a match is found (within `FACE_RECOGNITION_TOLERANCE`), the person's name is shown instead of "Unknown person."
- **Notification customization:**
  - Configure different notification rules per person (e.g., notify on unknown faces only, or when a specific person arrives).

**From the dashboard:**
- Manage enrolled faces (add, remove, update photos).
- View a gallery of enrolled people with their photos.
- See match history for each enrolled person.

---

## Feature 3 — Pet and animal detection

Detect household pets and animals using the COCO-trained model.

- **Built-in COCO animal classes:** cat, dog, bird, horse, sheep, cow, elephant, bear, zebra, giraffe.
- **Reduce false alarms:** Configure to only notify on `person` — ignore pet detections silently, or log them separately.
- **Custom pet classification (advanced):** Train a custom model to recognize your specific pets via transfer learning:
  1. Capture 50–100 photos of your pet from the dashboard.
  2. Run the training script on a laptop/desktop with GPU.
  3. Export the fine-tuned model to the Pi.
  4. The system now recognizes "Luna the cat" vs "unknown cat."

---

## Feature 4 — Zone-based detection

Draw inclusion and exclusion zones directly on the camera feed to control where detections trigger alerts.

- **Inclusion zones:** Only trigger alerts when a detection occurs inside this zone (e.g., the front door area).
- **Exclusion zones:** Ignore detections in this zone (e.g., a public sidewalk visible in the frame).
- **Zone drawing:** Click points on the live camera feed in the dashboard to define polygon zones.
- **Multiple zones:** Create multiple inclusion and exclusion zones per camera.
- **Zone labels:** Name each zone (e.g., "Front door", "Driveway", "Garden").
- **Zone-specific rules:** Configure different notification rules per zone.

**From the dashboard (Zones page):**
- Draw zones on the live camera feed by clicking points.
- Edit, rename, or delete existing zones.
- Toggle zones active/inactive.
- View zone hit counts.

---

## Feature 5 — Multi-camera support

Connect multiple cameras to the Pi and monitor them from a single dashboard.

- **Supported sources:**
  - Pi Camera Module (CSI) — up to 2 on Pi 5 (dual CSI lanes).
  - USB webcams — multiple via USB ports.
  - RTSP/IP cameras — network cameras (configurable URL).
- **Independent detection:** Each camera runs its own detection pipeline with separate zones and rules.
- **Dashboard grid view:** View all camera feeds simultaneously in a grid layout.
- **Per-camera settings:** Each camera has its own resolution, FPS, detection classes, and zones.

---

## Feature 6 — Event timeline with video clips

Every detection event is recorded with a video clip and metadata.

- **Pre-buffer recording:** The system keeps a rolling buffer (default 3 seconds). When a detection triggers, the clip starts from before the event.
- **Clip duration:** Configurable (default 10 seconds). Extends if the detection continues.
- **Storage management:** Old clips are automatically deleted when storage exceeds `CLIP_STORAGE_MAX_GB`.
- **Event metadata:** Each event stores: timestamp, camera, detection class, confidence, face match (if any), zone, snapshot image, and video clip path.
- **Dashboard toggle:** Enable/disable clip recording with an on/off button on the dashboard.

**From the dashboard (Events page):**
- Chronological timeline of all detection events.
- Filter by date range, camera, detection class, face, or zone.
- Click an event to view the video clip and snapshot.
- Download clips.
- Delete individual events or bulk-delete.

---

## Feature 7 — Night vision (Pi NoIR + IR)

Use a Pi NoIR (No IR filter) camera with an IR LED board for night-time detection.

- **Pi NoIR Camera Module:** Same as the regular Pi Camera but without the infrared filter — can see IR light.
- **IR LED board:** Provides invisible illumination (850nm or 940nm) that the NoIR camera can see.
- **Auto-switch:** The system can automatically enable IR LEDs when ambient light drops below a threshold (using frame brightness analysis).
- **GPIO control:** The IR LED board is controlled via a GPIO pin (`IR_GPIO_PIN` in `.env`). The system turns LEDs on/off as needed.
- **Dashboard control:** Manual IR LED toggle from the dashboard.

**Setup:**
1. Connect the IR LED board's signal pin to the GPIO pin configured in `.env`.
2. Set `NIGHT_VISION_ENABLED=true` in `.env`.
3. Replace the standard Pi Camera with the NoIR version.

---

## Feature 8 — Web dashboard

A real-time web interface for monitoring cameras, managing detections, and configuring the system.

| Section | Description |
|---|---|
| **Dashboard** | Live camera feed with detection overlay, alert feed, system stats |
| **Events** | Chronological event timeline with video clips and snapshots |
| **Faces** | Face enrollment gallery — upload, capture, remove faces |
| **Zones** | Draw inclusion/exclusion zones on the camera feed |
| **Cameras** | Multi-camera management — add, configure, remove cameras |
| **Settings** | Detection, notification, recording, and system settings |

**Real-time features:**
- **Live stream** — camera feed with bounding boxes and labels via WebSocket.
- **Alert feed** — new detection events appear in real time.
- **System stats** — CPU temperature, memory, disk usage, FPS counter.

---

## Notifications

The system sends alerts when a detection matches the configured rules.

| Channel | Setup | Notes |
|---|---|---|
| **Telegram** | Create a bot via BotFather, set token and chat ID in `.env` | Free, instant, includes snapshot image |
| **Email** | Configure SMTP server in `.env` | Use app-specific password for Gmail |
| **MQTT** | Set broker address and topic in `.env` | For Home Assistant / IoT integration |

**Notification content:**
- Snapshot image of the detection.
- Detection class and confidence (e.g., "Person detected (92%)").
- Face match if recognized (e.g., "John Doe detected").
- Zone name (e.g., "Front door zone").
- Timestamp.
- Link to the event in the dashboard.

---

## Hardware acceleration (future upgrade)

For users who need higher frame rates, the system can be upgraded with hardware accelerators:

| Accelerator | FPS Improvement | Notes |
|---|---|---|
| **Google Coral USB Accelerator** | 50+ FPS with TFLite models | Plugs into USB 3.0; requires TFLite model format |
| **Raspberry Pi AI HAT+ (Pi 5)** | 30+ FPS with Hailo-8L | NPU add-on HAT for Pi 5; 13 TOPS |
| **Intel Neural Compute Stick 2** | 20–30 FPS | USB stick; supports OpenVINO models |

> **Note:** Hardware acceleration is a future upgrade. The default YOLOv11n runs at 8–13 FPS on Pi 4/5 without any accelerator, which is sufficient for most security camera use cases.

---

## Authentication

The web dashboard is protected by session-based authentication.

- Credentials are stored in `.env` (`ADMIN_USERNAME` and `ADMIN_PASSWORD`).
- Login attempts are rate-limited (10 attempts per 15 minutes) to prevent brute-force.
- Sessions expire after 24 hours.
- Passwords can be changed from **Settings → Change Password** in the dashboard.

---

## How to deploy to Raspberry Pi

Your SSH config is already set up at `~/.ssh/config`:

```
Host rasp-pi
    HostName 192.168.216.90
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

**Method A — Use the deploy script (recommended)**

From the project directory on your laptop:

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/SecurityCamera
```

This will:
1. Create the remote directory.
2. Rsync all project files (excludes `venv`, `.env`, `.git`, `models/`, `clips/`).
3. Create a virtual environment and install dependencies on the Pi.
4. Create `.env` from `.env.default` if it does not exist.

**Method B — Manual rsync**

```bash
rsync -avz --delete \
  --exclude='venv/' \
  --exclude='.env' \
  --exclude='.git/' \
  --exclude='models/' \
  --exclude='clips/' \
  ./ \
  rasp-pi:/home/pi/Projects/SecurityCamera/

ssh rasp-pi "cd /home/pi/Projects/SecurityCamera && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
```

---

## How to run on the Raspberry Pi

**1. SSH into the Pi**

```bash
ssh rasp-pi
```

**2. Go to the project directory**

```bash
cd /home/pi/Projects/SecurityCamera
```

**3. Edit the .env file**

```bash
nano .env
```

Set `SESSION_SECRET` to a random string and change `ADMIN_PASSWORD`.

**4. Enable the camera**

```bash
sudo bash scripts/setup-camera.sh
```

This enables the CSI camera interface and installs `libcamera`.

**5. Download the YOLOv11n model**

```bash
bash scripts/download-models.sh
```

**6. Start the security camera**

```bash
source venv/bin/activate
python app.py
```

Access the dashboard at `http://192.168.216.90:5000`.

**7. (Optional) Set up night vision**

Connect the IR LED board and run:

```bash
sudo bash scripts/setup-ir.sh
```

Set `NIGHT_VISION_ENABLED=true` in `.env`.

**8. (Optional) Run as a systemd service**

```bash
sudo nano /etc/systemd/system/security-camera.service
```

```ini
[Unit]
Description=AI-Powered Security Camera
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/SecurityCamera
ExecStart=/home/pi/Projects/SecurityCamera/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable security-camera
sudo systemctl start security-camera
```

---

## Real-world applications

| Application | Who uses it | Why |
|---|---|---|
| **Home security** | Homeowners | Detect intruders, recognize family members, ignore pets, record events |
| **Package delivery monitoring** | Online shoppers | Detect delivery person at the door and send a notification with snapshot |
| **Pet monitoring** | Pet owners | Watch pets while away, detect unusual behavior, record activity |
| **Baby monitor upgrade** | Parents | Person detection in the crib area; face recognition to distinguish caregiver |
| **Small business security** | Shop owners | Monitor entrance, detect after-hours intruders, zone-based alerts |
| **Wildlife monitoring** | Nature enthusiasts | Detect and identify animals visiting a garden or bird feeder |
| **Elderly care** | Caregivers | Detect falls (pose estimation upgrade), monitor activity in specific zones |
| **Maker/IoT security** | Hardware hobbyists | Build a custom security system integrated with Home Assistant via MQTT |
| **Education / ML lab** | Teachers, students | Hands-on computer vision, YOLO training, face recognition in one project |

---

## Security notes

- **Change the default password immediately** after first login. Use the Settings page or edit `.env`.
- **Generate a strong `SESSION_SECRET`** — run: `python -c "import secrets; print(secrets.token_hex(32))"`
- **The `.env` file contains sensitive data** (passwords, API tokens). It is in `.gitignore` and should never be committed. Protect it with: `chmod 600 .env`
- **Face encodings are sensitive biometric data.** The `models/face_encodings.pkl` file should be protected. It is stored locally only — never uploaded to any cloud.
- **Video clips may contain private footage.** The `clips/` directory is in `.gitignore`. Manage storage carefully and consider encryption for sensitive environments.
- **Rate limiting** is enabled on the login endpoint (10 attempts per 15 minutes).
- **Camera access requires the `video` group on the Pi.** Add the user: `sudo usermod -aG video pi`
- **Notification tokens** (Telegram, SMTP) are stored in `.env` — treat them as secrets.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Camera not detected | Ensure the ribbon cable is firmly connected. Run `libcamera-hello` to test. Enable the camera: `sudo raspi-config` → Interface Options → Camera. |
| Low FPS / slow detection | Reduce resolution (`CAMERA_RESOLUTION=640x480`). Use Pi 5 for better performance. Consider Google Coral for hardware acceleration. |
| Face not recognized | Enroll more photos (different angles, lighting). Lower `FACE_RECOGNITION_TOLERANCE` (e.g., `0.5`). Ensure face is well-lit. |
| Too many false alarms | Increase `DETECTION_CONFIDENCE` (e.g., `0.7`). Use exclusion zones to mask high-movement areas. Filter detection classes. |
| Clips not recording | Check `CLIP_RECORDING_ENABLED=true`. Check disk space: `df -h`. Check `CLIP_STORAGE_MAX_GB` limit. |
| Night vision not working | Check IR LED board wiring. Verify `IR_GPIO_PIN` matches the connected pin. Ensure Pi NoIR camera is installed (not standard). |
| Telegram notification not sending | Verify bot token and chat ID. Send a test message via `curl`. Check internet connection. |
| `pip install face_recognition` fails | Install build tools: `sudo apt install cmake build-essential libatlas-base-dev`. This library compiles dlib from source. |
| Out of memory | Reduce camera resolution. Close other services. Use Pi 5 with 8 GB for multi-camera setups. |
| Dashboard not loading | Check if the server is running. Verify the Pi's IP and port. Check `python app.py` output for errors. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- See [task.md](task.md) for the engineering checklist with step-by-step implementation tasks.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model and mitigations.
