<img width="415" height="454" alt="image" src="https://github.com/user-attachments/assets/fd324ffc-f77a-49ae-90d8-ec3643dc97c5" /># 📜 Control Raspberry Pi GPIOs from a website

### 🪙 Donations are Welcome!
If you find this project helpful, you can support my work with a small donation. 

₿ Bitcoin donation: bc1q...


# Overview
The Control GPIOs from a Website project is a Raspberry Pi-based system that enables users to control General Purpose Input/Output (GPIO) pins remotely via a secure web interface, allowing automation and interaction with physical devices such as LEDs, relays, motors, or sensors in real-world applications like home automation, smart agriculture, or small-scale industrial control.
The system uses a Raspberry Pi to interface with GPIO-connected devices, hosted on a Flask web server with real-time updates via WebSocket for responsive control. It supports user authentication, logging of GPIO actions for auditing, and integration with IoT devices for scalable automation. The project is ideal for scenarios requiring remote device control, such as turning on lights, activating irrigation pumps, or monitoring sensor states from anywhere.

# Legal Disclaimer:
**Rasp-pvtora is not responsible for the legal use of this software. Users (*you, the reader of this repo*) are advised to consult with a legal professional to ensure compliance with local laws and regulations. While this software is functional, *you* are solely responsible for the legal use of this software in your jurisdiction and for your specific application (e.g., displaying required CCTV signs, securing employee consent for surveillance, etc.).**

# Functionality
- **Remote GPIO Control**: Users access a web interface to toggle GPIO pins (e.g., turn on/off a relay controlling a light or motor) or read sensor states (e.g., temperature from a DHT22 sensor).
- **Real-Time Updates**: WebSocket ensures instant feedback on the web interface when GPIO states change, reflecting device status (e.g., "Light ON").
- **User Authentication**: Secures the web interface with login credentials (username/password) to prevent unauthorized access, critical for home or industrial use.
- **Action Logging**: Logs all GPIO operations (e.g., pin toggled, timestamp, user) to a SQLite database for auditing and troubleshooting.
- **Device Integration**: Supports controlling multiple devices (e.g., relays, LEDs, servos) and reading inputs from sensors (e.g., motion, temperature) via GPIO pins.
- **Responsive Interface**: The web interface is mobile-friendly, built with HTML/CSS/JavaScript and Tailwind CSS, allowing control from smartphones or desktops.
- **Automation Rules**: Allows users to define simple rules (e.g., "turn on fan if temperature > 25°C") via the web interface, stored in the database.
- **Alert Notifications**: Sends alerts via email or Telegram for critical events (e.g., motion sensor triggered, GPIO failure).

## folder structure:
    gpio_control/
    ├── app.py
    ├── gpio_control.py
    ├── database.py
    ├── notifications.py
    ├── automation.py
    ├── config.py
    ├── templates/
    │   ├── index.html
    │   ├── login.html
    │   ├── logs.html
    │   ├── analytics.html
    ├── static/
    │   ├── chart.js (manually download or use CDN)
    ├── test_gpio_control.py
    ├── test_database.py
    ├── test_notifications.py
    ├── test_automation.py

<!--
How to run:
1. Setup: Clone folder, **pip install -r requirements.txt**, create config.py with tokens.
2. Test each modules individually: e.g., **python detection.py** or **py detection.py**.
3. Run main core: **python main.py** (starts camera loop, logging, alerts).
4. Run web: **python web_app.py** (dashboard at http://localhost:5000; add owners/watchlist).

## Setup instructions:
1. **Install Raspberry Pi OS:**
    - Enable camera: **sudo raspi-config > Interface > Camera > Enable**.
    - Update: **sudo apt update && sudo apt upgrade**.
    - Install system deps: **sudo apt install python3-pip libatlas-base-dev libopenjp2-7 libtiff5 tesseract-ocr libcamera-apps**.
    - Create virtual env: **python3 -m venv venv; source venv/bin/activate**.
    - Install required libraries: **pip install -r requirements.txt**.
2. **YOLOv8 Setup:** Run **from ultralytics import YOLO; model = YOLO('yolov8n.pt')** to auto-download pre-trained model. For plates/vehicles: Use COCO pre-trained (has 'car', 'truck'); fine-tune later with a dataset like https://universe.roboflow.com/browse/license-plates (download manually, train via Ultralytics docs).
3. **Database:** SQLite file auto-created as 'access.db'.
4. **Modify config.py:** is necessary to insert your Token and information  (as **Telegram BOT Token**, the **Gmail app password Token** and the **Encryption Key** generated with Fernet.generate_key() function)
5. **Test and tune the system.** Start indoor and with a stable light (in a close enviroment like an underground gate/parking or in office using a Video/Photos).
6. **GDPR Notes: Users are advised to consult with a legal professional to ensure compliance with local laws and regulations. While this software is functional, you are solely responsible for the legal use of this software in your jurisdiction and for your specific application (e.g., displaying required CCTV signs, securing employee consent for surveillance, etc.).**
-->


# Hardware Requirements
- **Raspberry Pi 5 or 4**: For processing web requests and handling GPIO operations (~€60-€80).
- **GPIO Breakout Board (e.g., T-Cobbler Plus)**: Simplifies GPIO connections (~€10).
- **Relay Module (4-channel, 5V)**: For controlling high-power devices like lights or pumps (~€10).
- **DHT22 Temperature/Humidity Sensor**: For reading environmental data (~€5).
- **LEDs and Resistors**: For testing GPIO outputs (~€5).
- **PIR Motion Sensor**: For detecting movement (~€5).
- **Servo Motor (e.g., SG90)**: For mechanical control (e.g., opening a valve) (~€5).
- **WiFi Module**: Built-in on Raspberry Pi 4/5 for network connectivity.
- **UPS (Uninterruptible Power Supply)**: Ensures reliability during power outages (e.g., 10000mAh power bank, ~€20).
- **Breadboard and Jumper Wires**: For prototyping connections (~€10).

# Software Requirements
- **Raspbian OS**: Lightweight OS for Raspberry Pi, optimized for IoT and AI tasks.
- **Python 3**: Core language for scripting GPIO control and web server logic.
- **Flask**: Web framework for hosting the control interface.
- **Flask-SocketIO**: For real-time WebSocket communication between the Pi and web clients.
- **RPi.GPIO**: Python library for controlling Raspberry Pi GPIO pins.
- **SQLite**: Lightweight database for storing GPIO actions and automation rules.
- **Adafruit CircuitPython DHT**: Library for reading DHT22 sensor data.
- **Tailwind CSS**: For styling a responsive, mobile-friendly web interface.
- **Nginx**: Reverse proxy for serving the Flask app with HTTPS encryption.
- **Telegram Bot API**: For sending alerts to users.
- **Passlib**: For secure password hashing (user authentication).
- **Gunicorn**: WSGI server for production deployment of Flask.

# Budget
- Raspberry Pi 5: ~€80
  Raspberry Pi 4: ~€40
- GPIO Breakout Board: €10
- Relay Module: €10
- DHT22 Sensor: €5
- LEDs and Resistors: €5
- PIR Motion Sensor: €5
- Servo Motor: €5
- UPS Power Bank: €20
- Breadboard and Jumper Wires: €10
 
**Total**: ~€150.

# Detailed Functionality:
- ### Web Interface Control:
    - A Flask-based web interface displays buttons or sliders for each GPIO pin (e.g., "Toggle Relay 1", "Read DHT22").
    - Users log in with credentials, verified against hashed passwords in SQLite.
    - Clicking a button sends a WebSocket message to toggle a GPIO pin (e.g., set pin 18 HIGH to activate a relay).
    - Real-time updates reflect the current state (e.g., "Relay 1: ON") using Flask-SocketIO.

- ### GPIO Interaction:
    - Outputs: Control devices like relays (for lights, pumps) or servos (for valves) by setting GPIO pins HIGH/LOW.
    - Inputs: Read sensor states (e.g., DHT22 for temperature/humidity, PIR for motion) and display on the web interface.
    - Supports PWM (Pulse Width Modulation) for precise control (e.g., servo angles).

- ### Automation Rules:
    - Users define rules via the web interface (e.g., "If DHT22 temperature > 25°C, set Relay 2 HIGH").
    - Rules are stored in SQLite and evaluated periodically by a background thread.
    - Rules can trigger GPIO actions or send alerts (e.g., motion detected by PIR sensor).

- ### Action Logging:
    - Every GPIO operation (e.g., pin toggle, sensor read) is logged to SQLite with timestamp, user, and action details.
    - Logs can be queried via the web interface (e.g., "Show all relay toggles today").

- ### Security and Reliability:
    - Uses HTTPS (via Nginx) to secure web access.
    - Stores passwords with bcrypt hashing (via Passlib).
    - Implements rate limiting on API endpoints to prevent abuse.
    - UPS ensures continuous operation during power outages.

- ### Notifications:
    - Sends Telegram or email alerts for critical events (e.g., motion detected, GPIO failure).
    - Alerts include context (e.g., "Motion detected at 15:30 on Pin 17").

- ### Scalability:
    - Supports multiple GPIO devices (e.g., 4 relays, 2 sensors) on a single Pi.
    - Integrates with MQTT for IoT ecosystems (e.g., Home Assistant) to control external devices.

<!--
# Function Description:
- Function: **Extract_PlateNumber(image)**
    - Purpose: Processes an image to extract the license plate number.
    - Input: image (numpy array from OpenCV, representing a frame from the Pi Camera or thermal camera).Output: plate_number string, e.g., "XYZ123") or None if no plate is detected.
    - Implementation:
        - Use YOLOv9 to detect the license plate region in the image.
        - Crop the region and pass it to Tesseract OCR for text extraction.
        - Apply regex to validate plate format (e.g., [A-Z0-9]{5,8}, suitable for alphanumeric plates.).
        - Return the extracted plate number or "None" if invalid (in this case allert for manual approval).
    - Interaction: Called in the main video processing loop; output passed to Search_Existing_Plate.

- Function: **Search_Existing_Plate(plate_number)**
    - Purpose: Checks if a license plate exists in the database and retrieves associated data.
    - Input: plate_number (string, e.g., "XYZ123").
    - Output: vehicle_data (dictionary with ID, type, color, owner details) or None if not found.
    - Implementation:
        - Query PostgreSQL table vehicles with SELECT * FROM vehicles WHERE plate_number = ?.
        - If no match, call Add_New_Plate(plate_number).
        - Return vehicle data or None.
    - Interaction: Called after Extract_PlateNumber; triggers Check_Watchlist if plate exists.

- Function: **Add_New_Plate(plate_number)**
    - Purpose: Adds a new license plate to the database with initial details.
    - Input: plate_number (string, e.g., "XYZ123").
    - Output: vehicle_id (integer, unique ID of the new entry).
    - Implementation:
        - Insert into vehicles table: INSERT INTO vehicles (plate_number, first_seen) VALUES (?, NOW()).
        - Log initial timestamp and return the generated ID.
    - Interaction: Called by Search_Existing_Plate when a plate is not found; triggers logging to entries table.

- Function: **Check_Watchlist(plate_number)**
    - Purpose: Checks if a plate is on the watchlist and triggers alerts if matched.
    - Input: plate_number (string, e.g., "XYZ123").
    - Output: is_flagged (boolean, True if on watchlist).
    - Implementation:
        - Query watchlist table: SELECT * FROM watchlist WHERE plate_number = ?.
        - If match found, call Send_Alert(plate_number, timestamp, location).
        - Return True if flagged, False otherwise.
    - Interaction: Called after Search_Existing_Plate; integrates with Telegram API.

- Function: **Send_Alert(plate_number, timestamp, location)**
    - Purpose: Sends a notification for flagged plates or suspicious activity.
    - Input: plate_number (string), timestamp (datetime), location (string, e.g., "Main Gate").
    - Output: None.
    - Implementation:
        - Format message: "Flagged plate {plate_number} detected at {location} on {timestamp}".
        - Send via Telegram Bot API and/or SMTP for email.
        - Log alert to alerts table: INSERT INTO alerts (plate_number, timestamp, location).
    - Interaction: Called by Check_Watchlist or anomaly detection routines.

- Function: **Log_Vehicle_Entry(plate_number, car_type, color, timestamp)**
    - Purpose: Logs a vehicle entry with details to the database.
    - Input: plate_number (string), car_type (string, e.g., "Sedan"), color (string, e.g., "Red"), timestamp (datetime).
    - Output: None.
    - Implementation:
        - Insert into entries table: INSERT INTO entries (vehicle_id, car_type, color, entry_time) VALUES ((SELECT id FROM vehicles WHERE plate_number = ?), ?, ?, ?).
        - Update vehicle’s last_seen timestamp in vehicles table.
    - Interaction: Called after Extract_PlateNumber and Search_Existing_Plate.

- Function: **Generate_Heatmap(start_date, end_date)**
    - Purpose: Creates a heatmap of vehicle activity for a given time range.
    - Input: start_date (datetime), end_date (datetime).
    - Output: heatmap_data (dictionary with hourly entry counts).
    - Implementation:
        - Query entries table: SELECT DATE_TRUNC('hour', entry_time), COUNT(*) FROM entries WHERE entry_time BETWEEN ? AND ? GROUP BY DATE_TRUNC('hour', entry_time).
        - Format data for visualization (e.g., JSON for Flask dashboard).
    - Interaction: Called by the web dashboard for analytics display.

- Function: **Process_Thermal_Image(image)**
    - Purpose: Processes thermal camera images to detect vehicles in low-light conditions.
    - Input: image (numpy array from thermal camera).
    - Output: vehicle_detected (boolean, True if vehicle present).
    - Implementation:
        - Use OpenCV to detect heat signatures matching vehicle shapes.
        - Pass detected regions to Extract_PlateNumber if visible.
        - Return True if vehicle detected, False otherwise.
    - Interaction: Called in low-light conditions; supplements Extract_PlateNumber.


# Software Workflow
- The Pi Camera detects and captures a vehicle entering the gate.
- **Extract_PlateNumber(image)** processes the frame, returning "XYZ123".
- **Search_Existing_Plate("XYZ123")** checks the database; if not found, **Add_New_Plate("XYZ123")** creates a new entry.
- **Log_Vehicle_Entry("XYZ123", "Sedan", "Red", NOW())** logs the entry with details from YOLOv9.
- **Check_Watchlist("XYZ123")** verifies if the plate is flagged; if so, **Send_Alert("XYZ123", NOW(), "Main Gate")** notifies operators.
- In low-light, **Process_Thermal_Image(image)** detects vehicles, feeding back to the main loop.
- The web dashboard periodically calls **Generate_Heatmap(today, today+1)** to display activity trends.

### Tips:
- Train YOLOv9 on a dataset of local vehicle types and license plate formats to improve accuracy.
- Use a high-capacity SD card (e.g., 64GB) for local data caching during network outages.
- Regularly update Tesseract OCR models to handle new plate designs.

### Extra Features & Upgrades:
- **Biometric Integration**: Add fingerprint scanners for driver verification, enhancing security.
- **LoRaWAN Support**: Use LoRaWAN for long-range communication in rural areas, reducing reliance on WiFi.
- **Smart Lock Integration**: Control gates with MQTT-enabled smart locks for automated access.
- **Live Heatmaps**: Display real-time vehicle activity on a map-based dashboard for quick insights.
- **Voice Alerts**: Use a speaker to announce alerts locally (e.g., "Unknown vehicle detected", "Suspicious vehicle", ...).
- **Police API Integration**: Sync with law enforcement databases for real-time suspect tracking (subject to legal approval).
-->

<!--
Repository Links:

https://github.com/ageitgey/face_recognition (base for vehicle and plate recognition)
https://github.com/ultralytics/yolov9 (advanced AI for detection)
https://github.com/tesseract-ocr/tesseract (OCR for plate text extraction)
https://github.com/jackpal/Torch (thermal imaging support)
https://github.com/pgjdbc/pgjdbc (PostgreSQL driver for Python)
-->
