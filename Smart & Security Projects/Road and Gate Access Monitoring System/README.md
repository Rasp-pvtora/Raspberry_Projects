# 📜 Road/Gate Access Monitoring System (AI-Powered)

This is an open source repository that contains projects made for a raspberry.

### 🪙 Donations are Welcome!
If you find this project helpful, you can support my work with a small donation. 

₿ Bitcoin donation: bc1q...


# Overview
The Road/Gate Access Monitoring System is a Raspberry Pi-based solution designed to enhance security in private areas (e.g., residential communities, gated company premises, or high-crime zones) by monitoring vehicles passing through a road or gate. The primary aim is to provide comprehensive, automated vehicle surveillance for private communities, commercial premises, or even for use by law enforcement.
The system uses AI-powered image processing to automatically detect and log vehicle details, including license plate number, car type, color, and entry/exit timestamps into a secure database. The system allows manual input of owner details (e.g., name, surname, address) for tracking purposes, making it valuable for community security or law enforcement applications (e.g., monitoring suspicious activity in drug/crime-related areas) helping to identify unusual activity or for police to monitor specific areas and track vehicles associated with criminal or suspicious activities.
A crucial security function is the "watchlist" feature. The operator can input one or more specific license plate numbers, and the system will actively monitor for these vehicles. If a match is detected, it will immediately trigger a real-time alert via Telegram or email, allowing for swift action. The system is enhanced with thermal imaging for reliable 24/7 operation, ensuring no activity is missed, regardless of lighting conditions.

# Functionality
Vehicle Detection and Logging: Uses a high-resolution Pi Camera with AI (OpenCV and YOLOv9) to detect vehicles, extract license plate numbers, and classify car type (e.g., sedan, SUV) and color. Logs entry/exit times and vehicle details to a PostgreSQL database.
Manual Owner Data Input: Provides a web interface for operators to manually enter owner details (name, surname, address) associated with detected license plates, enabling tracking of frequent visitors or suspicious vehicles.
Flagged Plate Alerts: Allows operators to input specific license plates (e.g., wanted vehicles) via the web interface. The system checks each detected plate against this list and sends instant alerts via Telegram or email if a match is found.
24/7 Operation: Incorporates a thermal camera for nighttime or low-light conditions, ensuring continuous monitoring regardless of environmental factors.
Real-Time Analytics: Generates live heatmaps of vehicle activity (e.g., frequency of entries by hour) on a web dashboard, accessible securely by authorized personnel (e.g., security teams or police).
Security Integration: Supports integration with external systems like police databases or smart locks for gate control, enhancing its utility in high-security scenarios.
Geofencing: Defines specific monitoring zones (e.g., within 100 meters of the gate) to filter relevant vehicle activity and reduce false positives.

## folder structure:
    road_gate_monitor/
    ├── config.py          # Settings, tokens (git ignore this!)
    ├── detection.py       # Vehicle detection, plate extraction
    ├── database.py        # DB operations (SQLite)
    ├── alerts.py          # Watchlist checks, send alerts
    ├── analytics.py       # Heatmaps, reports
    ├── web_app.py         # Flask web interface (run separately)
    ├── main.py            # Core loop for camera processing
    ├── requirements.txt   # Dependencies
    ├── Command.txt        # Command description to run the script
    ├── LICENSE            # License for this Repository
    └── README.md          # Infos

How to run:
1. Setup: Clone folder, **pip install -r requirements.txt**, create config.py with tokens.
2. Test each modules individually: e.g., **python detection.py** or **py detection.py**.
3. Run main core: **python main.py** (starts camera loop, logging, alerts).
4. Run web: **python web_app.py** (dashboard at http://localhost:5000; add owners/watchlist).

# Hardware Requirements
- **Raspberry Pi 5**: For enhanced processing power to handle AI tasks and real-time analytics.
  Raspberry Pi 4: Switching to Raspberry Pi 4 is possible but it has less CPU/GPU than Pi 5, so is necessary to lower video resolution to 640x480, process every few frames to avoid overload and use YOLOv8n that is a lighter version.
- **Pi Camera Module 3**: High-resolution camera for clear license plate and vehicle detection in daylight.
- **Thermal Camera (e.g., FLIR Lepton)**: For nighttime or low-light vehicle detection.
There is a possibility to use Pi Camera's night mode (via auto-exposure in picamera2 library) to handle low-light, eliminating the thermal camera and reducing budget.
- **WiFi Module**: For cloud connectivity and remote access (built-in on Raspberry Pi 5).
- **UPS (Uninterruptible Power Supply)**: Ensures continuous operation during power outages (e.g., 10000mAh power bank, ~€20).
- **Weatherproof Enclosure**: To protect hardware in outdoor environments (~€15).
- Optional **RFID Reader** (e.g., RC522): For secondary authentication of authorized vehicles (~€5).
- Optional **4G/LTE Module**: For remote deployments without WiFi (~€30).

# Software Requirements
- **Raspbian OS**: Lightweight OS for Raspberry Pi, optimized for IoT and AI tasks.
- **OpenCV**: For real-time image processing and vehicle detection.
- **YOLOv8n**: Advanced AI model for license plate detection and vehicle classification.
- **Tesseract OCR**: For extracting text from license plates.
- **PostgreSQL**: Secure relational database for storing vehicle and owner data.
- **Python 3**: For scripting the core application logic and API integrations.
- **Flask**: For creating a secure web interface for manual data input and dashboard visualization.
- **Telegram Bot API**: For sending real-time alerts to operators.
- **LoRaWAN Library** (optional): For long-range communication in rural setups (e.g., pylorawan).
- **Mosquitto MQTT**: For secure communication with external systems like smart locks.
- **Nginx**: For hosting the web dashboard with HTTPS encryption.
- **Fernet symmetric encryption**: basic **GDPR compliance** to Encrypt sensitive owner details (name, surname, address, ...)

# Budget
- Raspberry Pi 5: ~€80
  Raspberry Pi 4: ~€40
- Pi Camera Module 3: €25 (can also work for night view, but lower quality!)
- Thermal Camera (FLIR Lepton): €150
- UPS Power Bank: €20
- Weatherproof Enclosure: €15
- RFID Reader (RC522): €5
- 4G/LTE Module (optional): €30
  
**Total**: ~€295 (using Pi5 and FLIR Lepton camera for night view)

***Cheaper budget***: ~€105 (using Pi4, Pi-Camera for night view and no 4G module)

# Detailed Functionality:
- ### Vehicle Detection and Classification:
    - The Pi Camera captures live video feed of the road or gate area.
    - OpenCV preprocesses frames to detect vehicles, followed by YOLOv9 to classify car type (e.g., sedan, truck) and color (e.g., red, black).
    - Tesseract OCR extracts license plate numbers from detected regions.
    - Data (plate number, type, color, timestamp) is logged to a PostgreSQL database with a unique entry ID.

- ### Manual Data Input:
    - A Flask-based web interface allows operators to input owner details (name, surname, address) for specific license plates, stored in the database with a foreign key linking to vehicle entries.
    - Supports CSV upload for bulk data entry (e.g., resident vehicle lists).

- ### Flagged Plate Monitoring:
    - Operators can add plate numbers to a "watchlist" table via the web interface.
    - Each detected plate is checked against the watchlist; matches trigger immediate Telegram or email alerts with details (plate, timestamp, location).

- ### Nighttime Operation:
    - The thermal camera activates in low-light conditions (detected via light sensor or time-based schedule).
    - Processes thermal images to detect vehicle shapes, supplementing visible-light data for continuous monitoring.

- ### Analytics and Visualization:
    - A Flask dashboard displays real-time vehicle activity (e.g., entries per hour) and heatmaps of peak times.
    - Historical data can be queried (e.g., "show all entries for plate XYZ123 in the last month").
    - Exports reports as CSV for external analysis (e.g., by police).

- ### Integration with External Systems:
    - Uses MQTT to communicate with smart locks for automated gate control.
    - Integrates with police APIs (if available) for real-time suspect tracking.
    - Supports LoRaWAN for rural deployments, sending data to a central server.

- ### Security Features:
    - Encrypts database with AES-256 for sensitive data (e.g., owner details).
    - Secures web dashboard with HTTPS and OAuth2 authentication.
    - Implements rate limiting on Telegram alerts to prevent abuse.


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

<!--
Repository Links:

https://github.com/ageitgey/face_recognition (base for vehicle and plate recognition)
https://github.com/ultralytics/yolov9 (advanced AI for detection)
https://github.com/tesseract-ocr/tesseract (OCR for plate text extraction)
https://github.com/jackpal/Torch (thermal imaging support)
https://github.com/pgjdbc/pgjdbc (PostgreSQL driver for Python)
-->

