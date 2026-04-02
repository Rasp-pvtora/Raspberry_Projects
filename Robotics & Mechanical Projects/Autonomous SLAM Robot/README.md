# Autonomous SLAM Robot

<div align="center">

![ROS 2](https://img.shields.io/badge/ROS_2-Humble-22314E?style=for-the-badge&logo=ros&logoColor=white)
![SLAM](https://img.shields.io/badge/SLAM-slam__toolbox-FF6F00?style=for-the-badge)
![Nav2](https://img.shields.io/badge/Nav2-Autonomous_Navigation-0078D4?style=for-the-badge)
![RPLidar](https://img.shields.io/badge/RPLidar-A1-E91E63?style=for-the-badge)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-4%2F5-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A wheeled robot powered by a Raspberry Pi running ROS 2 Humble with RPLidar A1 for real-time SLAM (Simultaneous Localization and Mapping). Builds occupancy grid maps while tracking position, supports Nav2 click-to-goal autonomous navigation, web teleoperation via rosbridge + roslibjs (virtual joystick + live map), ultrasonic/IR backup sensors, AprilTag docking station, camera-based object detection on map, and battery monitoring with auto-dock. Difficulty: 10/10.**

[Features](#features) • [Hardware](#hardware-requirements) • [Budget](#budget) • [Quick Start](#quick-start) • [Configuration](#environment-configuration) • [Web Interface](#web-teleoperation-interface) • [Troubleshooting](#troubleshooting)

</div>

---

**If you find this project useful, consider supporting development:**

**BTC:** `bc1q...`

---

## Table of Contents

- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Wiring Diagram](#wiring-diagram)
- [Libraries & Dependencies](#libraries--dependencies)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [System Overview](#system-overview)
- [Features](#features)
  - [ROS 2 Humble Navigation Stack](#ros-2-humble-navigation-stack)
  - [RPLidar A1 Lidar Scanning](#rplidar-a1-lidar-scanning)
  - [SLAM (slam_toolbox)](#slam-slam_toolbox)
  - [Nav2 Autonomous Navigation (Click-to-Goal)](#nav2-autonomous-navigation-click-to-goal)
  - [Web Teleoperation (rosbridge + roslibjs)](#web-teleoperation-rosbridge--roslibjs)
  - [Multi-Floor Mapping](#multi-floor-mapping)
  - [Ultrasonic + IR Backup Sensors](#ultrasonic--ir-backup-sensors)
  - [Docking Station (AprilTag Detection)](#docking-station-apriltag-detection)
  - [Camera Object Detection on Map](#camera-object-detection-on-map)
  - [Battery Monitoring + Auto-Dock](#battery-monitoring--auto-dock)
- [Web Teleoperation Interface](#web-teleoperation-interface)
- [ROS 2 Topics & Services](#ros-2-topics--services)
- [Deployment](#deployment)
- [Running the Robot](#running-the-robot)
- [Safety Notes](#safety-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
Autonomous SLAM Robot/
├── README.md                        # This file
├── TSD.md                          # Technical Specification Document
├── task.md                         # Development task checklist
├── implementation_plan.md          # Phased implementation guide
├── .env.example                    # Environment variable template
├── slam_robot_ws/                  # ROS 2 workspace
│   └── src/
│       ├── slam_robot_bringup/     # Main launch package
│       │   ├── package.xml
│       │   ├── setup.py
│       │   ├── launch/
│       │   │   ├── robot_bringup.launch.py        # Full stack launch
│       │   │   ├── slam.launch.py                 # SLAM only
│       │   │   ├── nav2.launch.py                 # Nav2 navigation only
│       │   │   ├── teleop_web.launch.py           # Web teleoperation
│       │   │   ├── sensors.launch.py              # Sensor aggregation
│       │   │   └── docking.launch.py              # Docking + auto-dock
│       │   ├── config/
│       │   │   ├── slam_toolbox_params.yaml       # SLAM parameters
│       │   │   ├── nav2_params.yaml               # Nav2 stack configuration
│       │   │   ├── robot_description.yaml         # URDF parameters
│       │   │   ├── ekf.yaml                       # Robot localization (EKF)
│       │   │   ├── costmap_common.yaml            # Costmap layer config
│       │   │   └── twist_mux.yaml                 # Velocity source priority
│       │   ├── urdf/
│       │   │   └── slam_robot.urdf.xacro          # Robot URDF model
│       │   ├── rviz/
│       │   │   └── slam_robot.rviz                # RViz2 visualization config
│       │   └── maps/
│       │       └── .gitkeep                       # Saved map files
│       ├── slam_robot_hardware/    # Hardware interface package
│       │   ├── package.xml
│       │   ├── setup.py
│       │   └── slam_robot_hardware/
│       │       ├── __init__.py
│       │       ├── motor_driver_node.py           # L298N motor control + encoders
│       │       ├── ultrasonic_node.py             # HC-SR04 ultrasonic sensors
│       │       ├── ir_sensor_node.py              # IR obstacle sensors
│       │       ├── battery_monitor_node.py        # ADC battery voltage reading
│       │       └── config_loader.py               # .env loader for ROS params
│       ├── slam_robot_nav/         # Navigation extensions
│       │   ├── package.xml
│       │   ├── setup.py
│       │   └── slam_robot_nav/
│       │       ├── __init__.py
│       │       ├── multi_floor_manager.py         # Floor switching + map DB
│       │       ├── docking_controller.py          # AprilTag dock approach
│       │       ├── auto_dock_node.py              # Battery-triggered docking
│       │       └── safety_controller.py           # Emergency stop logic
│       ├── slam_robot_perception/  # Camera + detection package
│       │   ├── package.xml
│       │   ├── setup.py
│       │   └── slam_robot_perception/
│       │       ├── __init__.py
│       │       ├── object_detector_node.py        # YOLO/MobileNet detection
│       │       ├── apriltag_detector_node.py      # AprilTag for docking
│       │       └── map_annotator_node.py          # Plot detections on map
│       └── slam_robot_web/         # Web interface package
│           ├── package.xml
│           ├── setup.py
│           ├── slam_robot_web/
│           │   ├── __init__.py
│           │   └── web_server_node.py             # Serve static web files
│           └── web/
│               ├── index.html                     # Dark theme main page
│               ├── css/
│               │   └── style.css                  # Dark theme styles
│               └── js/
│                   ├── app.js                     # Main roslibjs connection
│                   ├── joystick.js                # Virtual joystick (nipplejs)
│                   ├── map_viewer.js              # Live occupancy grid display
│                   ├── nav_goal.js                # Click-to-goal on map
│                   ├── camera_feed.js             # Live camera stream
│                   └── battery_widget.js          # Battery status display
├── docker/
│   ├── Dockerfile.ros2             # ROS 2 Humble container for Pi
│   └── docker-compose.yml         # Optional containerized deployment
├── deploy/
│   └── deploy_to_pi.sh            # rsync deploy script (rasp-pi)
├── scripts/
│   ├── install_ros2.sh            # ROS 2 Humble installation for Pi
│   ├── install_rplidar.sh         # RPLidar ROS 2 driver
│   ├── install_deps.sh            # OS-level dependencies
│   ├── setup_udev.sh             # udev rules for Lidar + motor driver
│   ├── calibrate_odom.sh         # Odometry calibration helper
│   └── save_map.sh               # Save current SLAM map
├── systemd/
│   ├── slam-robot.service         # Main robot systemd service
│   └── rosbridge.service          # rosbridge WebSocket service
└── docs/
    ├── wiring_diagram.md          # Complete wiring reference
    ├── ros2_architecture.md       # Node graph and topic map
    ├── tuning_guide.md            # SLAM + Nav2 parameter tuning
    └── docking_setup.md           # AprilTag docking station build
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4GB+) / Pi 5 | Yes | Pi 5 recommended for Nav2 + SLAM + camera simultaneously |
| RPLidar A1 (360° Lidar) | Yes | USB-connected, 12m range, 8000 samples/sec |
| L298N Motor Driver | Yes | Dual H-bridge for 2 DC motors |
| DC Motors with Encoders ×2 | Yes | Gear motors with Hall effect encoders for odometry |
| Robot Chassis (2WD) | Yes | Acrylic or aluminum platform with mounting holes |
| Caster Wheel | Yes | Rear balance — ball or swivel caster |
| 12V Battery (motors) | Yes | Li-ion or NiMH pack for motor driver |
| LiPo Battery / Power Bank (Pi) | Yes | Separate 5V supply for Pi — avoids motor noise |
| MicroSD Card (32GB+) | Yes | ROS 2 + maps storage |
| Pi Camera Module v2/v3 (optional) | No | Object detection + AprilTag docking |
| HC-SR04 Ultrasonic Sensors ×2 (optional) | No | Front/rear backup collision avoidance |
| IR Obstacle Sensors ×2 (optional) | No | Close-range cliff/edge detection |
| ADS1115 ADC (optional) | No | Battery voltage monitoring (analog → I2C) |
| AprilTag printed marker (optional) | No | Docking station visual target |
| USB Hub (optional) | No | If using Lidar + Camera simultaneously |

---

## Budget

| Item | Estimated Cost |
|---|---|
| RPLidar A1 (360° Lidar scanner) | ~$100 |
| L298N Motor Driver | ~$5 |
| DC Motors with Encoders ×2 | ~$15 |
| Robot Chassis (2WD kit) | $15–25 |
| Caster Wheel | ~$3 |
| 12V Battery Pack (motors) | ~$15 |
| LiPo / Power Bank (Pi) | ~$20 |
| **Total (core build)** | **~$165–190** |

Optional add-ons:

| Item | Estimated Cost |
|---|---|
| Pi Camera Module v2 | ~$25 |
| HC-SR04 Ultrasonic ×2 | ~$3 |
| IR Obstacle Sensors ×2 | ~$3 |
| ADS1115 ADC Module | ~$5 |
| USB Hub | ~$8 |

*(Assumes you already own a Raspberry Pi 4/5 with power supply and MicroSD.)*

---

## Wiring Diagram

### Motor Driver (L298N) → Pi GPIO

| L298N Pin | Pi GPIO | Wire Color (suggested) |
|-----------|---------|----------------------|
| IN1 | GPIO 17 (pin 11) | Yellow |
| IN2 | GPIO 27 (pin 13) | Yellow |
| IN3 | GPIO 22 (pin 15) | Blue |
| IN4 | GPIO 23 (pin 16) | Blue |
| ENA | GPIO 12 (pin 32) — PWM0 | Green |
| ENB | GPIO 13 (pin 33) — PWM1 | Green |
| GND | GND (pin 6) | Black |

### Motor Encoders → Pi GPIO

| Encoder | Pi GPIO | Notes |
|---------|---------|-------|
| Left Encoder A | GPIO 5 (pin 29) | Interrupt-driven |
| Left Encoder B | GPIO 6 (pin 31) | Direction sensing |
| Right Encoder A | GPIO 16 (pin 36) | Interrupt-driven |
| Right Encoder B | GPIO 26 (pin 37) | Direction sensing |

### RPLidar A1 → Pi

| Connection | Detail |
|-----------|--------|
| USB | Pi USB port → RPLidar micro-USB |
| Device | `/dev/ttyUSB0` (or via udev rule: `/dev/rplidar`) |

### Ultrasonic Sensors (HC-SR04) → Pi GPIO

| Sensor | Trigger GPIO | Echo GPIO | Notes |
|--------|-------------|-----------|-------|
| Front | GPIO 20 (pin 38) | GPIO 21 (pin 40) | 5V→3.3V voltage divider on Echo! |
| Rear | GPIO 19 (pin 35) | GPIO 25 (pin 22) | 5V→3.3V voltage divider on Echo! |

### IR Sensors → Pi GPIO

| Sensor | GPIO | Notes |
|--------|------|-------|
| Left cliff | GPIO 24 (pin 18) | Digital output (HIGH = obstacle) |
| Right cliff | GPIO 8 (pin 24) | Digital output (HIGH = obstacle) |

### Battery Monitor (ADS1115) → Pi I2C

| ADS1115 Pin | Connection |
|-------------|-----------|
| SDA | GPIO 2 (pin 3) — I2C SDA |
| SCL | GPIO 3 (pin 5) — I2C SCL |
| VDD | 3.3V (pin 1) |
| GND | GND (pin 9) |
| A0 | Battery voltage via voltage divider (e.g., 12V → ≤3.3V) |

> **Warning:** HC-SR04 Echo pins output 5V. Use a voltage divider (1kΩ + 2kΩ) to bring it down to 3.3V safe for Pi GPIO. The RPLidar A1 is powered via USB 5V — no separate power needed.

---

## Libraries & Dependencies

| Library / Package | Purpose |
|---|---|
| ROS 2 Humble | Robot middleware (nodes, topics, services, actions) |
| slam_toolbox | Online/offline SLAM from lidar scans |
| Nav2 (navigation2) | Autonomous navigation: planning, control, recovery |
| rplidar_ros | ROS 2 driver for RPLidar A1 |
| robot_localization | EKF fusing odometry + IMU for pose estimation |
| rosbridge_suite | WebSocket bridge — exposes ROS topics to web |
| roslibjs | JavaScript ROS client for web interface |
| nipplejs | Virtual joystick library for web teleoperation |
| tf2_ros | Transform tree management (base_link → odom → map) |
| nav2_map_server | Map serving, saving, loading |
| twist_mux | Velocity command priority (teleop vs. nav vs. safety) |
| apriltag_ros | AprilTag detection for docking (optional) |
| image_transport | Compressed camera image transport (optional) |
| RPi.GPIO / gpiozero | GPIO control for motors, sensors |
| adafruit-circuitpython-ads1x15 | ADS1115 ADC for battery monitoring |

---

## Quick Start

```bash
# 1. SSH into the Pi
ssh rasp-pi          # alias for pi@192.168.216.90

# 2. Clone the repo
git clone <repo-url> ~/slam_robot && cd ~/slam_robot

# 3. Install ROS 2 Humble
sudo bash scripts/install_ros2.sh
source /opt/ros/humble/setup.bash

# 4. Install OS-level dependencies
sudo bash scripts/install_deps.sh

# 5. Set up udev rules (RPLidar, GPIO permissions)
sudo bash scripts/setup_udev.sh
sudo udevadm control --reload-rules && sudo udevadm trigger

# 6. Configure environment
cp .env.example .env
nano .env              # Toggle features, set GPIO pins, tune params

# 7. Build the ROS 2 workspace
cd slam_robot_ws
colcon build --symlink-install
source install/setup.bash

# 8. Launch the full robot stack
ros2 launch slam_robot_bringup robot_bringup.launch.py

# 9. Open web interface
# Browse to http://192.168.216.90:8080
# Use virtual joystick to drive, watch live SLAM map

# 10. Save a map
ros2 run nav2_map_server map_saver_cli -f ~/slam_robot/slam_robot_ws/src/slam_robot_bringup/maps/my_house
```

---

## Environment Configuration

See [TSD.md — §4 Environment Configuration](TSD.md#4-environment-configuration-envdefault) for the full `.env.default` block with all toggleable features.

Key toggles:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_SLAM` | `true` | Run slam_toolbox for real-time mapping |
| `ENABLE_NAV2` | `true` | Nav2 autonomous navigation stack |
| `ENABLE_WEB_TELEOP` | `true` | rosbridge + roslibjs web interface |
| `ENABLE_MULTI_FLOOR` | `false` | Multi-floor map management |
| `ENABLE_ULTRASONIC` | `false` | HC-SR04 backup collision sensors |
| `ENABLE_IR_SENSORS` | `false` | IR cliff/obstacle sensors |
| `ENABLE_DOCKING` | `false` | AprilTag docking station |
| `ENABLE_CAMERA` | `false` | Pi Camera for object detection |
| `ENABLE_OBJECT_DETECTION` | `false` | YOLO/MobileNet on camera feed |
| `ENABLE_BATTERY_MONITOR` | `false` | ADC-based battery voltage monitoring |
| `ENABLE_AUTO_DOCK` | `false` | Auto-dock when battery low |
| `ENABLE_MOCK_MODE` | `false` | Simulated sensors for desktop testing |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Web Browser (Dark Theme)                        │
│  ┌────────────┐ ┌──────────────┐ ┌───────────┐ ┌────────────────┐   │
│  │ Virtual     │ │ Live SLAM    │ │ Camera    │ │ Battery Status │   │
│  │ Joystick   │ │ Map Display  │ │ Feed      │ │ + Nav Goals    │   │
│  └──────┬─────┘ └──────┬───────┘ └─────┬─────┘ └───────┬────────┘   │
│         └──────────────┼───────────────┼────────────────┘            │
│                        │ roslibjs (WebSocket)                         │
└────────────────────────┼─────────────────────────────────────────────┘
                         │ ws://192.168.216.90:9090
┌────────────────────────▼─────────────────────────────────────────────┐
│                    Raspberry Pi (ROS 2 Humble)                        │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                     rosbridge_websocket                           │ │
│  │              (WebSocket ↔ ROS 2 topic bridge)                    │ │
│  └──────────────────────────┬───────────────────────────────────────┘ │
│                              │                                        │
│  ┌──────────┐  ┌────────────▼───────┐  ┌───────────────────────────┐ │
│  │ RPLidar  │  │   slam_toolbox     │  │        Nav2 Stack         │ │
│  │ A1 Node  ├──► (online SLAM —     │  │  ┌──────────┐ ┌────────┐ │ │
│  │ /scan    │  │  /map, /tf)        ├──►  │ Planner  │ │Control │ │ │
│  └──────────┘  └────────────────────┘  │  │ (NavFn)  │ │(DWB)   │ │ │
│                                         │  └──────────┘ └────────┘ │ │
│  ┌──────────┐  ┌────────────────────┐  │  ┌──────────┐ ┌────────┐ │ │
│  │ Motor    │  │  robot_localization │  │  │ Costmap  │ │Recovery│ │ │
│  │ Driver   ◄──┤  (EKF: odom+IMU)   │  │  │ 2D      │ │Behaviorsers│ │ │
│  │ L298N    │  └────────────────────┘  │  └──────────┘ └────────┘ │ │
│  └──────────┘                          └───────────────────────────┘ │
│                                                                       │
│  ┌──────────┐  ┌────────────────────┐  ┌───────────────────────────┐ │
│  │ Ultrasonic│  │  Safety Controller │  │   Docking Controller      │ │
│  │ + IR     ├──►  (e-stop, cliff    ├──►  (AprilTag → approach     │ │
│  │ Sensors  │  │   detection)       │  │   → dock → charge)        │ │
│  └──────────┘  └────────────────────┘  └───────────────────────────┘ │
│                                                                       │
│  ┌──────────┐  ┌────────────────────┐  ┌───────────────────────────┐ │
│  │ Pi Camera│  │  Object Detector   │  │   Battery Monitor         │ │
│  │ v2/v3   ├──►  (MobileNet/YOLO   ├──►  (ADS1115 ADC → voltage   │ │
│  │          │  │   → /detections)   │  │   → auto-dock trigger)    │ │
│  └──────────┘  └────────────────────┘  └───────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

Transform Tree (tf2):
  map → odom → base_footprint → base_link
                                    ├── laser_frame (RPLidar)
                                    ├── camera_link (Pi Camera)
                                    ├── ultrasonic_front_link
                                    └── ultrasonic_rear_link
```

---

## Features

### ROS 2 Humble Navigation Stack

The entire robot runs on ROS 2 Humble — the industry-standard robot middleware. All nodes communicate via typed topics, services, and actions. The launch system composes the full stack from modular launch files, and every feature can be enabled/disabled via `.env` parameters passed to launch arguments.

### RPLidar A1 Lidar Scanning

The RPLidar A1 provides 360° laser scans at up to 8000 samples/sec with a 12-meter range. The `rplidar_ros` package publishes `sensor_msgs/LaserScan` on `/scan`. The Lidar connects via USB and is assigned a persistent device path (`/dev/rplidar`) via udev rules.

### SLAM (slam_toolbox)

`slam_toolbox` runs in online asynchronous mode, consuming `/scan` and `/tf` (odometry) to build an occupancy grid map in real-time. The map is published on `/map` as `nav_msgs/OccupancyGrid`. Maps can be saved/loaded via the map_server, enabling persistent mapping across sessions.

Key parameters (tunable via `slam_toolbox_params.yaml`):
- `resolution`: Map grid cell size (default 0.05m = 5cm)
- `max_laser_range`: Clip scan range (default 12.0m for A1)
- `minimum_travel_distance`: Min distance before new scan insertion (0.3m)
- `minimum_travel_heading`: Min rotation before new scan insertion (0.3 rad)

### Nav2 Autonomous Navigation (Click-to-Goal)

The Nav2 stack provides full autonomous navigation:
- **Global Planner** (NavFn / Theta*) — Plans a path from current pose to goal on the global costmap
- **Local Controller** (DWB / MPPI) — Follows the path while avoiding dynamic obstacles
- **Recovery Behaviors** — Spin, backup, wait when stuck
- **Costmap 2D** — Obstacle layers from Lidar + ultrasonic + IR sensors
- **Behavior Trees** — Orchestrates planning → following → recovery

Click any point on the web map interface to send a Nav2 goal. The robot plans a path and autonomously navigates there.

### Web Teleoperation (rosbridge + roslibjs)

The web interface connects to ROS 2 via `rosbridge_websocket` (WebSocket on port 9090). The front-end uses `roslibjs` to subscribe/publish topics:

- **Virtual Joystick** — `nipplejs` widget publishes `geometry_msgs/Twist` to `/cmd_vel_teleop`
- **Live SLAM Map** — Subscribes to `/map` and renders the occupancy grid on HTML5 Canvas
- **Click-to-Goal** — Publishes `geometry_msgs/PoseStamped` to `/goal_pose` (Nav2 action)
- **Camera Feed** — Subscribes to compressed image topic via `ros2-web-video-server` or `web_video_server`
- **Battery Widget** — Subscribes to `/battery_state` for voltage/percentage display

All served from a static web server node — no Flask or backend framework needed. Dark theme with CSS.

### Multi-Floor Mapping

When `ENABLE_MULTI_FLOOR=true`, the `multi_floor_manager` node maintains a database of named maps. Switch between floors via the web interface or ROS service:
- Save current map to a named floor
- Load a different floor's map
- Each floor maintains its own map file and initial pose
- Seamless floor transitions for multi-story buildings

### Ultrasonic + IR Backup Sensors

HC-SR04 ultrasonic sensors (front/rear) and IR cliff sensors provide backup collision avoidance independent of the Lidar:
- Ultrasonic range published as `sensor_msgs/Range` on `/ultrasonic/front` and `/ultrasonic/rear`
- IR digital cliff detection on `/ir/left_cliff` and `/ir/right_cliff`
- Integrated into Nav2 costmap as additional obstacle layers
- Safety controller triggers emergency stop if distance < threshold

### Docking Station (AprilTag Detection)

A printed AprilTag marker on the charging station provides a visual docking target:
1. Robot detects the AprilTag via Pi Camera (`apriltag_ros` package)
2. AprilTag gives precise 6-DoF pose relative to the camera
3. Docking controller aligns the robot and approaches at slow speed
4. Final approach uses ultrasonic for sub-centimeter precision
5. Contact switches or voltage detection confirm docked state

### Camera Object Detection on Map

When `ENABLE_OBJECT_DETECTION=true`:
- Pi Camera runs MobileNet SSD or YOLOv8-nano for real-time detection
- Detected objects (person, chair, pet, etc.) are projected onto the SLAM map using camera-to-map transforms
- `map_annotator_node` publishes `visualization_msgs/MarkerArray` for RViz2 and the web interface
- Objects persist on the map with timestamps

### Battery Monitoring + Auto-Dock

An ADS1115 ADC reads battery voltage via a voltage divider:
- Publishes `sensor_msgs/BatteryState` on `/battery_state`
- Web interface shows voltage, percentage, estimated runtime
- When `ENABLE_AUTO_DOCK=true` and voltage drops below threshold:
  1. Current navigation goal is cancelled
  2. Robot navigates to the docking station's known map position
  3. AprilTag docking sequence executes
  4. Robot enters charging state

---

## Web Teleoperation Interface

The dark-themed web interface runs at `http://192.168.216.90:8080` and connects to `ws://192.168.216.90:9090` (rosbridge).

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  🤖 SLAM Robot — Teleoperation          [Battery: 78%] │
├────────────────────────────────┬────────────────────────┤
│                                │                        │
│     Live SLAM Map              │    Camera Feed         │
│     (occupancy grid canvas)    │    (compressed image)  │
│                                │                        │
│     ● Robot position           │    [Detected: chair]   │
│     ★ Nav goal marker          │    [Detected: person]  │
│     ■ Detected objects         │                        │
│                                │                        │
├────────────────────────────────┼────────────────────────┤
│  Virtual Joystick              │ Controls               │
│  ┌─────────┐                   │ [Start SLAM]           │
│  │    ↑    │                   │ [Stop SLAM]            │
│  │  ← ● → │ (nipplejs)        │ [Save Map]             │
│  │    ↓    │                   │ [Load Map ▼]           │
│  └─────────┘                   │ [Dock Robot]           │
│  Speed: [━━━━━○━━━━] 0.5 m/s  │ [E-STOP] 🔴           │
└────────────────────────────────┴────────────────────────┘
```

### Keyboard Controls (when web page focused)

| Key | Action |
|-----|--------|
| W / ↑ | Forward |
| S / ↓ | Backward |
| A / ← | Turn left |
| D / → | Turn right |
| Space | Emergency stop |
| M | Toggle map/camera fullscreen |

---

## ROS 2 Topics & Services

### Published Topics

| Topic | Type | Source |
|-------|------|--------|
| `/scan` | `sensor_msgs/LaserScan` | rplidar_ros |
| `/odom` | `nav_msgs/Odometry` | motor_driver_node (wheel encoders) |
| `/map` | `nav_msgs/OccupancyGrid` | slam_toolbox |
| `/tf` | `tf2_msgs/TFMessage` | robot_localization, slam_toolbox |
| `/cmd_vel` | `geometry_msgs/Twist` | twist_mux output → motors |
| `/cmd_vel_teleop` | `geometry_msgs/Twist` | Web joystick (via rosbridge) |
| `/cmd_vel_nav` | `geometry_msgs/Twist` | Nav2 controller |
| `/cmd_vel_safety` | `geometry_msgs/Twist` | Safety controller override |
| `/ultrasonic/front` | `sensor_msgs/Range` | ultrasonic_node |
| `/ultrasonic/rear` | `sensor_msgs/Range` | ultrasonic_node |
| `/battery_state` | `sensor_msgs/BatteryState` | battery_monitor_node |
| `/camera/image_raw` | `sensor_msgs/Image` | Pi Camera |
| `/detections` | `vision_msgs/Detection2DArray` | object_detector_node |
| `/map_annotations` | `visualization_msgs/MarkerArray` | map_annotator_node |

### Services

| Service | Type | Description |
|---------|------|-------------|
| `/slam_toolbox/save_map` | `slam_toolbox/SaveMap` | Save current SLAM map |
| `/slam_toolbox/deserialize_map` | `slam_toolbox/DeserializeMap` | Load a saved map |
| `/multi_floor/switch_floor` | `std_srvs/SetBool` | Switch active floor map |
| `/docking/start_dock` | `std_srvs/Trigger` | Begin docking sequence |
| `/safety/emergency_stop` | `std_srvs/Trigger` | Immediate motor stop |

### Actions

| Action | Type | Description |
|--------|------|-------------|
| `/navigate_to_pose` | `nav2_msgs/NavigateToPose` | Nav2 click-to-goal |
| `/dock_robot` | `slam_robot_nav/DockRobot` | Full auto-dock sequence |

---

## Deployment

```bash
# From development machine — deploy to Pi
cd deploy/
bash deploy_to_pi.sh

# The script runs:
# rsync -avz --exclude '.venv' --exclude 'build' --exclude 'install' --exclude 'log' \
#   . rasp-pi:~/slam_robot/
```

After deployment, rebuild on the Pi:
```bash
ssh rasp-pi
cd ~/slam_robot/slam_robot_ws
colcon build --symlink-install
source install/setup.bash
```

---

## Running the Robot

```bash
# Full stack (SLAM + Nav2 + web teleop + sensors)
source /opt/ros/humble/setup.bash
source ~/slam_robot/slam_robot_ws/install/setup.bash
ros2 launch slam_robot_bringup robot_bringup.launch.py

# SLAM only (mapping mode — no autonomous navigation)
ros2 launch slam_robot_bringup slam.launch.py

# Navigation only (load existing map)
ros2 launch slam_robot_bringup nav2.launch.py map:=/path/to/map.yaml

# Web teleop only (manual driving)
ros2 launch slam_robot_bringup teleop_web.launch.py

# Via systemd (production — auto-start on boot)
sudo systemctl enable --now slam-robot
sudo systemctl enable --now rosbridge
```

---

## Safety Notes

- **Emergency stop** is always available via the web E-STOP button or `Space` key — publishes zero velocity and locks motors
- `twist_mux` prioritizes safety controller > teleop > Nav2 — safety always wins
- Ultrasonic sensors provide backup collision avoidance even if Lidar fails
- IR cliff sensors prevent driving off edges (stairs, table)
- Motor driver `ENA`/`ENB` pins can be cut via GPIO for hardware-level stop
- Battery monitor prevents deep discharge — auto-docks before voltage drops too low
- Maximum speed is capped in `.env` (`MAX_LINEAR_VEL`, `MAX_ANGULAR_VEL`)
- Nav2 costmap inflation radius keeps the robot clear of obstacles by a configurable margin

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| RPLidar not found | Check USB connection, verify udev rule: `ls /dev/rplidar`. Restart udev: `sudo udevadm trigger` |
| SLAM map not updating | Verify `/scan` and `/odom` topics are publishing: `ros2 topic hz /scan` — should be ~5-10 Hz |
| Robot drifts / odometry inaccurate | Calibrate wheel encoders: `bash scripts/calibrate_odom.sh`. Check encoder wiring |
| Nav2 planner fails | Ensure map is loaded, costmaps are initialized. Check `ros2 topic echo /map` is non-empty |
| Web interface won't connect | Verify rosbridge running: `ros2 topic list`. Check firewall: port 9090 (WebSocket) and 8080 (HTTP) |
| Motors not spinning | Check L298N wiring, verify `ENA`/`ENB` PWM pins. Test with `ros2 topic pub /cmd_vel geometry_msgs/Twist ...` |
| Camera not detected | Enable camera in `raspi-config`. Verify: `libcamera-hello`. Check `/dev/video0` exists |
| AprilTag not detected | Ensure good lighting, tag printed at correct size. Check camera calibration |
| Battery reading wrong | Calibrate voltage divider ratio in `.env`. Verify ADS1115 I2C: `i2cdetect -y 1` |
| Robot won't dock | Check AprilTag is visible, docking position correct on map. Verify `/apriltag/detections` topic |

---

## Where to Next

- **RViz2 on desktop** — Run `rviz2` on a networked PC with the provided `.rviz` config for full 3D visualization
- **Simulation first** — Test in Gazebo with the URDF before deploying to hardware
- **SLAM algorithms** — Try `cartographer_ros` as an alternative to `slam_toolbox`
- **Outdoor mapping** — Upgrade to RPLidar A2/A3 for longer range outdoor environments
- **IMU fusion** — Add an IMU (MPU6050) for better odometry via `robot_localization` EKF
- **Arm integration** — Mount a robotic arm for pick-and-place while navigating