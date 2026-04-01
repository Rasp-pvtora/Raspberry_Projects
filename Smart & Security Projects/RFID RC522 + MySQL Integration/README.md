# RFID RC522 + MySQL Integration

A secure, keyless entry system for doors and cabinets using an MFRC522 RFID reader, Raspberry Pi, and MariaDB database. Logs all access attempts with timestamps, supports time-based access rules, temporary guest codes, anti-passback, and real-time notifications. Includes a web dashboard for managing authorized tags, viewing access logs, and configuring access rules.

🪙 **Donations are Welcome!**
If you find this project helpful, you can support my work with a small donation.
₿ Bitcoin donation: `bc1q...`

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Budget](#budget)
4. [Libraries and dependencies](#libraries-and-dependencies)
5. [Quickstart — Laptop (development)](#quickstart--laptop-development)
6. [Environment configuration (.env)](#environment-configuration-env)
7. [System overview](#system-overview)
8. [Feature 1 — RFID tag reading and authentication](#feature-1--rfid-tag-reading-and-authentication)
9. [Feature 2 — Access logging and audit trail](#feature-2--access-logging-and-audit-trail)
10. [Feature 3 — Time-based access rules](#feature-3--time-based-access-rules)
11. [Feature 4 — Temporary access codes](#feature-4--temporary-access-codes)
12. [Feature 5 — Anti-passback protection](#feature-5--anti-passback-protection)
13. [Feature 6 — Multi-door support](#feature-6--multi-door-support)
14. [Feature 7 — Web dashboard](#feature-7--web-dashboard)
15. [Feature 8 — Notifications](#feature-8--notifications)
16. [Wiring diagram](#wiring-diagram)
17. [Authentication](#authentication)
18. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
19. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
20. [Real-world applications](#real-world-applications)
21. [Security notes](#security-notes)
22. [Troubleshooting](#troubleshooting)
23. [Where to next](#where-to-next)

---

## Project structure

```
.
├── app.py                     ← Python entry point (Flask + RFID reader)
├── requirements.txt           ← Python dependencies
├── .env.default               ← Environment variable template (copy to .env)
├── .gitignore                 ← Git ignore rules
├── src/
│   ├── rfid/
│   │   ├── reader.py          ← MFRC522 RFID reader interface
│   │   ├── auth_engine.py     ← Tag authentication and access rules
│   │   └── mock_reader.py     ← Mock RFID reader for development
│   ├── lock/
│   │   ├── lock_controller.py ← GPIO relay control for door locks
│   │   └── buzzer.py          ← Piezo buzzer feedback (accept/deny)
│   ├── routes/
│   │   ├── auth.py            ← Login / logout routes
│   │   ├── dashboard.py       ← Dashboard API
│   │   ├── tags.py            ← Tag management API
│   │   ├── access_log.py      ← Access log API
│   │   ├── rules.py           ← Time-based rules API
│   │   ├── doors.py           ← Multi-door management API
│   │   └── settings.py        ← Settings API
│   └── services/
│       ├── db.py              ← MariaDB connection and schema
│       ├── access_service.py  ← Access control logic
│       ├── notification_service.py ← Telegram/email alerts
│       └── system_service.py  ← System info (temp, memory, disk)
├── templates/                 ← Jinja2 HTML templates
│   ├── layout.html            ← Base layout with sidebar navigation
│   ├── login.html             ← Login page
│   ├── dashboard.html         ← Live access status and recent events
│   ├── tags.html              ← Tag management (add, remove, assign)
│   ├── access_log.html        ← Full access log with filters
│   ├── rules.html             ← Time-based access rules
│   ├── doors.html             ← Multi-door configuration
│   └── settings.html          ← System and notification settings
├── static/                    ← Static frontend assets
│   ├── css/style.css          ← Dark theme dashboard stylesheet
│   └── js/
│       ├── main.js            ← WebSocket client for real-time events
│       ├── dashboard.js       ← Dashboard logic
│       ├── tags.js            ← Tag management logic
│       ├── access_log.js      ← Access log filters and export
│       └── rules.js           ← Rule configuration logic
├── sql/
│   └── schema.sql             ← MariaDB schema (tables, indexes)
├── scripts/
│   ├── setup-spi.sh           ← Enable SPI interface on the Pi
│   ├── setup-mariadb.sh       ← Install and configure MariaDB
│   └── setup-gpio.sh          ← GPIO permissions setup
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
| Raspberry Pi 3B+ / 4 / 5 | Yes | Any model with SPI support; Pi 4 recommended |
| microSD card (16 GB+) | Yes | For OS, project files, and database |
| MFRC522 RFID reader module | Yes | 13.56 MHz RFID/NFC reader via SPI |
| RFID tags/cards (13.56 MHz) | Yes | Mifare Classic 1K compatible; usually included with the reader |
| Relay module (5V, 1-channel) | Yes | Controls the electric strike / solenoid lock |
| Electric strike or solenoid lock | Yes | Door lock actuated by the relay |
| Power supply (official) | Yes | 5V 3A for Pi 4/5 |
| Jumper wires (female-to-female) | Yes | For SPI and GPIO connections |
| Piezo buzzer | Optional | Audio feedback for access granted/denied |
| LED indicators (green + red) | Optional | Visual feedback for access status |
| Second MFRC522 module | Optional | For multi-door or entry/exit setup |

---

## Budget

| Item | Estimated Price (USD) | Notes |
|---|---|---|
| MFRC522 RFID reader module | $3 – $5 | Usually includes 1 card + 1 keyfob |
| Additional RFID cards/keyfobs (10-pack) | $5 – $8 | Mifare Classic 1K, 13.56 MHz |
| 1-channel relay module (5V) | $2 – $4 | Optocoupler-isolated recommended |
| Electric strike lock (12V) | $15 – $30 | For door frame installation |
| 12V power supply for lock | $5 – $10 | Separate from Pi power supply |
| Jumper wires (40-pack F/F) | $2 – $3 | Female-to-female for SPI/GPIO |
| Piezo buzzer | $1 – $2 | 3.3V or 5V active buzzer |
| LED (green + red) + resistors | $1 – $2 | 220Ω resistors for 3.3V GPIO |
| **Optional:** Solenoid lock (for cabinet) | $8 – $15 | Smaller, for cabinet/drawer locks |
| **Optional:** Second MFRC522 module | $3 – $5 | For multi-door or anti-passback |
| **Total (minimum)** | **~$33 – $62** | Reader + relay + lock + wires |

> **Note:** The Raspberry Pi itself, microSD card, and power supply are not included in the budget above.

---

## Libraries and dependencies

### Python dependencies

| Library | Version | Purpose |
|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | ^3.1.0 | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | ^5.4.0 | WebSocket for real-time access events |
| [Jinja2](https://jinja.palletsprojects.com/) | ^3.1.4 | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ^1.0.1 | Load environment variables from `.env` |
| [mysqlclient](https://pypi.org/project/mysqlclient/) | ^2.2.0 | MariaDB/MySQL Python connector |
| [spidev](https://pypi.org/project/spidev/) | ^3.6 | SPI interface for MFRC522 |
| [mfrc522](https://pypi.org/project/mfrc522/) | ^0.0.7 | MFRC522 RFID reader library |
| [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) | ^0.7.1 | GPIO control for relay and LEDs |
| [bcrypt](https://pypi.org/project/bcrypt/) | ^4.2.0 | Password hashing |
| [python-telegram-bot](https://python-telegram-bot.org/) | ^21.0 | Telegram Bot notifications |

### Dev dependencies

| Library | Version | Purpose |
|---|---|---|
| [pytest](https://docs.pytest.org/) | ^8.3.0 | Testing framework |

### System packages (installed on the Pi)

| Package | Purpose |
|---|---|
| `mariadb-server` | MySQL-compatible database server |
| `libmariadb-dev` | Development headers for mysqlclient |
| `python3-spidev` | SPI interface library |
| `Python 3.11+` | Python runtime |

---

## Quickstart — Laptop (development)

**1. Clone the repository**

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/RFID RC522 + MySQL Integration"
```

**2. Create the `.env` file from the template**

```bash
# Linux / macOS
cp .env.default .env

# Windows
copy .env.default .env
```

Edit `.env` and set your values (at minimum, change `SESSION_SECRET`, `ADMIN_PASSWORD`, and `DB_PASSWORD`).

**3. Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

**4. Set up the database**

Install MariaDB (or MySQL) on your laptop and create the database:

```bash
mysql -u root -p < sql/schema.sql
```

**5. Start the development server**

```bash
python app.py
```

**6. Open the dashboard**

Navigate to `http://localhost:5000` in your browser.

- **Username:** `admin` (or whatever you set in `.env`)
- **Password:** `changeme` (or whatever you set in `.env`)

> **Note:** On a laptop without SPI hardware, the RFID reader runs in mock mode — you can simulate tag scans from the dashboard. All other features (database, access logs, rules, dashboard) work fully.

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
| `DB_HOST` | `localhost` | MariaDB host |
| `DB_PORT` | `3306` | MariaDB port |
| `DB_NAME` | `rfid_access` | Database name |
| `DB_USER` | `rfid_user` | Database username |
| `DB_PASSWORD` | `changeme` | Database password |
| `RFID_READER_PIN` | `25` | GPIO pin for MFRC522 RST (SDA is CE0/GPIO8 by default) |
| `RELAY_GPIO_PIN` | `17` | GPIO pin connected to the relay module |
| `RELAY_ACTIVE_HIGH` | `true` | Relay trigger polarity (`true` = HIGH activates) |
| `LOCK_OPEN_DURATION_SEC` | `5` | How long the lock stays open after valid scan |
| `BUZZER_GPIO_PIN` | `27` | GPIO pin for piezo buzzer (optional) |
| `LED_GREEN_GPIO_PIN` | `22` | GPIO pin for green LED (optional) |
| `LED_RED_GPIO_PIN` | `23` | GPIO pin for red LED (optional) |
| `ANTI_PASSBACK_ENABLED` | `false` | Enable anti-passback (requires entry + exit reader) |
| `NOTIFY_TELEGRAM_ENABLED` | `false` | Enable Telegram notifications |
| `NOTIFY_TELEGRAM_TOKEN` | `` | Telegram Bot API token |
| `NOTIFY_TELEGRAM_CHAT_ID` | `` | Telegram chat ID |
| `NOTIFY_EMAIL_ENABLED` | `false` | Enable email notifications |
| `NOTIFY_EMAIL_SMTP` | `smtp.gmail.com` | SMTP server |
| `NOTIFY_EMAIL_PORT` | `587` | SMTP port |
| `NOTIFY_EMAIL_USER` | `` | SMTP username |
| `NOTIFY_EMAIL_PASSWORD` | `` | SMTP password |
| `NOTIFY_EMAIL_TO` | `` | Recipient email |

---

## System overview

| Stage | Component | Tool | What it does |
|---|---|---|---|
| **1. Scan** | MFRC522 Reader | `mfrc522` library via SPI | Reads RFID tag UID when presented |
| **2. Authenticate** | Auth Engine | Python + MariaDB | Checks tag UID against authorized tags, applies time rules |
| **3. Actuate** | Lock Controller | RPi.GPIO → Relay | Opens the electric strike/solenoid for configured duration |
| **4. Feedback** | Buzzer + LEDs | RPi.GPIO | Beep + green LED (granted) or double-beep + red LED (denied) |
| **5. Log** | Access Service | MariaDB | Logs event: timestamp, tag UID, owner, door, allow/deny, rule |
| **6. Notify** | Notification Service | Telegram / Email | Alerts on unauthorized attempts or specific tag usage |
| **7. Dashboard** | Web Server | Flask + WebSocket | Real-time access events, tag management, logs, rules |

**How an access scan works:**

```
Tag presented → MFRC522 reads UID
    → Auth Engine checks: Is this tag registered?
    → Auth Engine checks: Is it within allowed time window?
    → Auth Engine checks: Is anti-passback OK?
    → YES: Relay activates lock (5 sec) + green LED + beep
    → NO:  Lock stays closed + red LED + double-beep
    → Event logged to MariaDB
    → Dashboard updated via WebSocket
    → Notification sent (if configured for this event type)
```

---

## Feature 1 — RFID tag reading and authentication

The MFRC522 module reads 13.56 MHz RFID tags via SPI.

- **Tag UID:** Each RFID card/keyfob has a unique 4-byte or 7-byte UID.
- **Registration:** Tags are registered from the dashboard — scan an unknown tag, then assign it an owner name and permissions.
- **Access decision:** The auth engine checks the tag against the database:
  1. Is the tag registered and active?
  2. Does the tag have access to this specific door?
  3. Is the current time within the tag's allowed hours?
  4. Is anti-passback satisfied (if enabled)?
- **Mock mode:** On laptops without SPI, a mock reader simulates tag scans from the dashboard (for development).

---

## Feature 2 — Access logging and audit trail

Every tag scan (granted or denied) is logged to MariaDB with full metadata.

**Log fields:**
- Timestamp
- Tag UID
- Owner name
- Door/reader ID
- Access result (granted / denied)
- Denial reason (if denied: unknown tag, expired, time restriction, anti-passback)
- Rule that was applied

**From the dashboard (Access Log page):**
- Filterable by date range, tag owner, door, result (granted/denied).
- Sortable columns.
- Export to CSV for external reporting.
- Real-time: new events appear instantly via WebSocket.

---

## Feature 3 — Time-based access rules

Restrict tag access to specific days and hours.

- **Per-tag schedules:** Each tag can have a custom weekly schedule (e.g., Monday–Friday 8:00–18:00).
- **Default rule:** If no specific rule is set, the tag has 24/7 access.
- **Multiple rules per tag:** A tag can have different rules for different doors.
- **Holiday/override dates:** Block access on specific dates regardless of the schedule.

**From the dashboard (Rules page):**
- Create, edit, delete time rules.
- Assign rules to tags and doors.
- Visual weekly schedule editor (click time blocks).

---

## Feature 4 — Temporary access codes

Generate time-limited RFID authorizations for guests.

- **Guest tags:** Register a physical RFID tag with a temporary validity window (e.g., valid for 24 hours, or until a specific date).
- **Auto-expire:** The tag automatically becomes inactive after the validity period.
- **Notification:** Optionally notify when a temporary tag is used.
- **Revocable:** Deactivate a temporary tag immediately from the dashboard.

**From the dashboard:**
- Click "Create Temporary Access" — select a tag (or register new one), set start/end dates.
- View all active temporary authorizations with remaining time.

---

## Feature 5 — Anti-passback protection

Prevent a tag from being used twice in a row without an exit scan.

- **How it works:** After a tag scans "in," it cannot scan "in" again until it scans "out." This prevents sharing a tag or tailgating.
- **Requires:** Two MFRC522 readers — one for entry, one for exit.
- **Soft anti-passback:** Log the violation but still allow entry.
- **Hard anti-passback:** Deny entry on violation.
- **Configurable:** Enable/disable per door via `ANTI_PASSBACK_ENABLED` in `.env`.

---

## Feature 6 — Multi-door support

Control multiple doors or cabinets from a single Pi.

- **Multiple MFRC522 readers:** Each reader on a different SPI chip-select (CE0, CE1) or via I2C multiplexer.
- **Per-door configuration:** Each door has its own relay pin, authorized tags, and time rules.
- **Dashboard:** Switch between doors to view live status and access logs.
- **Scalability:** For more than 2–3 doors, consider additional Pis with a shared MariaDB database.

---

## Feature 7 — Web dashboard

A real-time web interface for access management.

| Section | Description |
|---|---|
| **Dashboard** | Live access status, recent events, door status (locked/unlocked), system stats |
| **Tags** | Register new tags, assign owners, activate/deactivate, view all tags |
| **Access Log** | Full audit trail with filters, export to CSV |
| **Rules** | Time-based access rules with visual schedule editor |
| **Doors** | Multi-door configuration, per-door settings |
| **Settings** | Notification config, lock duration, anti-passback, password change |

**Real-time features:**
- Access events appear instantly via WebSocket.
- Door status (locked/unlocked) updates live.
- Unknown tag alerts trigger a registration prompt.

---

## Feature 8 — Notifications

Get alerts for security events.

| Channel | Events | Notes |
|---|---|---|
| **Telegram** | Unauthorized access attempt, temporary tag used, anti-passback violation | Free, instant |
| **Email** | Daily access log summary, unauthorized attempt alerts | Configurable schedule |

**Configurable event triggers:**
- Notify on unknown tag only.
- Notify on denied access.
- Notify when a specific tag is used (e.g., VIP/boss arrives).
- Daily summary email with access statistics.

---

## Wiring diagram

### MFRC522 to Raspberry Pi (SPI)

| MFRC522 Pin | Pi GPIO Pin | Pi Physical Pin | Notes |
|---|---|---|---|
| SDA (SS) | GPIO 8 (CE0) | Pin 24 | SPI chip select |
| SCK | GPIO 11 (SCLK) | Pin 23 | SPI clock |
| MOSI | GPIO 10 (MOSI) | Pin 19 | SPI data out |
| MISO | GPIO 9 (MISO) | Pin 21 | SPI data in |
| IRQ | — | — | Not used |
| GND | GND | Pin 6 | Ground |
| RST | GPIO 25 | Pin 22 | Reset (configurable in `.env`) |
| 3.3V | 3.3V | Pin 1 | Power (**3.3V only — do NOT use 5V!**) |

### Relay module

| Relay Pin | Pi GPIO Pin | Notes |
|---|---|---|
| IN | GPIO 17 | Signal (configurable in `.env`) |
| VCC | 5V (Pin 2) | Relay power |
| GND | GND (Pin 9) | Ground |

### Electric lock

| From | To | Notes |
|---|---|---|
| Relay COM | 12V power supply + | Common terminal |
| Relay NO | Lock + | Normally open (lock opens when relay activates) |
| Lock − | 12V power supply − | Complete the circuit |

### Optional: Buzzer and LEDs

| Component | Pi GPIO Pin | Notes |
|---|---|---|
| Piezo buzzer + | GPIO 27 | Signal pin (configurable in `.env`) |
| Green LED (anode) | GPIO 22 | Via 220Ω resistor |
| Red LED (anode) | GPIO 23 | Via 220Ω resistor |
| All GND | GND | Common ground |

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
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/RFIDAccess
```

This will:
1. Create the remote directory.
2. Rsync all project files (excludes `venv`, `.env`, `.git`).
3. Create a virtual environment and install dependencies on the Pi.
4. Create `.env` from `.env.default` if it does not exist.

**Method B — Manual rsync**

```bash
rsync -avz --delete \
  --exclude='venv/' \
  --exclude='.env' \
  --exclude='.git/' \
  ./ \
  rasp-pi:/home/pi/Projects/RFIDAccess/

ssh rasp-pi "cd /home/pi/Projects/RFIDAccess && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
```

---

## How to run on the Raspberry Pi

**1. SSH into the Pi**

```bash
ssh rasp-pi
```

**2. Go to the project directory**

```bash
cd /home/pi/Projects/RFIDAccess
```

**3. Enable SPI and install MariaDB**

```bash
sudo bash scripts/setup-spi.sh
sudo bash scripts/setup-mariadb.sh
```

**4. Initialize the database**

```bash
mysql -u root -p < sql/schema.sql
```

**5. Edit the .env file**

```bash
nano .env
```

Set `SESSION_SECRET`, `ADMIN_PASSWORD`, and `DB_PASSWORD`.

**6. Start the access control system**

```bash
source venv/bin/activate
python app.py
```

Access the dashboard at `http://192.168.216.90:5000`.

**7. (Optional) Run as a systemd service**

```bash
sudo nano /etc/systemd/system/rfid-access.service
```

```ini
[Unit]
Description=RFID Access Control System
After=network-online.target mariadb.service
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/RFIDAccess
ExecStart=/home/pi/Projects/RFIDAccess/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable rfid-access
sudo systemctl start rfid-access
```

---

## Real-world applications

| Application | Who uses it | Why |
|---|---|---|
| **Home door lock** | Homeowners | Keyless entry with RFID card; no keys to lose |
| **Office access control** | Small businesses | Track employee access with time rules; audit trail |
| **Server room security** | IT departments | Restrict and log access to sensitive equipment |
| **Cabinet/locker security** | Labs, libraries | Secure cabinets with individual access per user |
| **Makerspace tool checkout** | Hackerspaces | Track which member accessed which tool and when |
| **Student attendance** | Schools, universities | Students scan at door entry; automatic attendance log |
| **Guest management** | Hotels, Airbnb | Temporary access tags for guests that auto-expire |
| **Garage/gate control** | Property owners | RFID-triggered gate opening with access logging |
| **Education project** | Teachers, students | Learn SPI, databases, GPIO, web development in one project |

---

## Security notes

- **Change the default password immediately** after first login. Use the Settings page or edit `.env`.
- **Generate a strong `SESSION_SECRET`** — run: `python -c "import secrets; print(secrets.token_hex(32))"`
- **The `.env` file contains sensitive data** (passwords, DB credentials, API tokens). It is in `.gitignore` and should never be committed. Protect it: `chmod 600 .env`
- **Database credentials:** Use a dedicated database user (`rfid_user`) with access only to the `rfid_access` database — not the MariaDB root user.
- **MFRC522 reads UIDs in plaintext.** The UID is not encrypted on the tag. For higher security, use Mifare DESFire tags or NFC with challenge-response authentication (beyond the scope of this project).
- **Relay safety:** The relay controls a physical lock. Ensure the lock has a manual override (key or handle) for safety in case of power failure or system malfunction.
- **Rate limiting** is enabled on the web login endpoint (10 attempts per 15 minutes).
- **GPIO access requires root on the Pi.** Run the app with appropriate permissions or add the `pi` user to the `gpio` and `spi` groups.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| RFID reader not detected | Check wiring (especially 3.3V — not 5V!). Enable SPI: `sudo raspi-config` → Interface Options → SPI. Run `ls /dev/spidev*`. |
| Tag not reading | Hold the tag closer (within 3 cm). Check the RST pin configuration. Try a different tag. |
| Relay not clicking | Check GPIO pin number matches `.env`. Check relay module power (VCC to 5V). Test pin with `gpio write`. |
| Lock not opening | Check relay wiring (COM/NO). Verify 12V power supply is connected. Check `RELAY_ACTIVE_HIGH` polarity. |
| Database connection error | Check MariaDB is running: `sudo systemctl status mariadb`. Verify credentials in `.env`. Run `mysql -u rfid_user -p`. |
| Dashboard not loading | Check if the server is running. Verify the Pi's IP and port. Check `python app.py` output. |
| "Permission denied: /dev/spidev0.0" | Add user to spi group: `sudo usermod -aG spi pi`. Reboot. |
| Mock mode on Pi | Ensure `spidev` and `mfrc522` are installed: `pip install spidev mfrc522`. Check SPI is enabled. |
| Anti-passback violation | The tag scanned "in" but never "out." Use the dashboard to reset the passback state. |
| `pip install mysqlclient` fails | Install headers: `sudo apt install libmariadb-dev python3-dev`. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- See [task.md](task.md) for the engineering checklist with step-by-step implementation tasks.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model and mitigations.
