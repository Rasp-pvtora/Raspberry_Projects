# Technical Specification Document — Autonomous SLAM Robot

## 1. Scope

### In Scope

- Wheeled robot (2WD + caster) with Raspberry Pi 4/5 as main controller
- RPLidar A1 360° Lidar for laser scanning
- ROS 2 Humble as the middleware (nodes, topics, services, actions, launch files)
- SLAM via `slam_toolbox` (online asynchronous mode) to build occupancy grid maps
- Nav2 autonomous navigation stack (global planner, local controller, recovery behaviors)
- Web teleoperation via `rosbridge_suite` + `roslibjs` (virtual joystick + live map)
- L298N motor driver with DC motors + Hall effect encoders for differential drive
- Wheel odometry published as `nav_msgs/Odometry`
- `robot_localization` EKF for fusing odometry (+ optional IMU)
- `twist_mux` for velocity command prioritization (safety > teleop > Nav2)
- Multi-floor mapping with named map database
- HC-SR04 ultrasonic sensors (front/rear) for backup collision avoidance
- IR obstacle/cliff sensors for edge detection
- AprilTag-based docking station with visual servo approach
- Pi Camera object detection (MobileNet SSD / YOLOv8-nano) with map annotation
- ADS1115 ADC battery voltage monitoring with auto-dock on low battery
- Dark-themed web interface served by a ROS 2 node (static files, no Flask)
- URDF robot model for tf2 transform tree
- All features toggled via `.env` (loaded as ROS 2 launch arguments)
- Mock mode for desktop development/testing without hardware
- Deployment via rsync to `rasp-pi` (192.168.216.90)
- systemd services for production auto-start

### Out of Scope

- Full Gazebo simulation package (user can set up separately)
- ROS 2 Control (ros2_control) hardware interface — uses direct GPIO for simplicity
- Custom PCB or motor controller design
- SLAM algorithms beyond slam_toolbox (cartographer mentioned as alternative, not implemented)
- Cloud-based mapping or remote SLAM processing
- Mobile app development
- Arm manipulation (separate project)
- GPS/RTK outdoor navigation
- Commercial deployment or fleet management

---

## 2. MVP Features (P0)

| ID | Feature | Priority |
|----|---------|----------|
| P0-1 | ROS 2 Humble installed and configured on Pi | P0 |
| P0-2 | RPLidar A1 driver (`rplidar_ros`) publishing `/scan` | P0 |
| P0-3 | L298N motor driver node with encoder odometry (`/odom`) | P0 |
| P0-4 | URDF model + static transforms (tf2) | P0 |
| P0-5 | `robot_localization` EKF (fuse wheel odom) | P0 |
| P0-6 | `slam_toolbox` online SLAM (publishes `/map`) | P0 |
| P0-7 | `twist_mux` velocity prioritization | P0 |
| P0-8 | `rosbridge_websocket` for web interface | P0 |
| P0-9 | Web interface: virtual joystick (nipplejs → `/cmd_vel_teleop`) | P0 |
| P0-10 | Web interface: live SLAM map rendering (Canvas) | P0 |
| P0-11 | Map save/load via `nav2_map_server` | P0 |
| P0-12 | Dark theme web UI | P0 |
| P0-13 | `.env` toggleable features (launch arguments) | P0 |
| P0-14 | Deploy script (rsync to rasp-pi) | P0 |

### Nice-to-Have (P1/P2)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| P1-1 | Nav2 autonomous navigation (click-to-goal) | P1 | Full Nav2 stack with costmaps |
| P1-2 | Keyboard controls on web page | P1 | WASD + arrow keys |
| P1-3 | Ultrasonic sensors (front/rear) | P1 | Nav2 costmap layer integration |
| P1-4 | IR cliff/obstacle sensors | P1 | Safety controller e-stop |
| P1-5 | Safety controller (emergency stop) | P1 | Highest twist_mux priority |
| P1-6 | Battery monitoring (ADS1115) | P1 | Web widget + `/battery_state` |
| P1-7 | Multi-floor mapping | P1 | Named map database with floor switching |
| P2-1 | AprilTag docking station | P2 | Visual servo approach + contact detection |
| P2-2 | Auto-dock on low battery | P2 | Requires P2-1 + P1-6 |
| P2-3 | Pi Camera object detection | P2 | MobileNet SSD or YOLOv8-nano |
| P2-4 | Object annotation on map | P2 | MarkerArray in RViz/web |
| P2-5 | Camera feed on web interface | P2 | Compressed image via rosbridge |
| P2-6 | Speed slider on web interface | P2 | Dynamic max velocity adjustment |

---

## 3. ROS 2 Node Architecture

### Node Graph

| Node | Package | Publishes | Subscribes | Parameters |
|------|---------|-----------|------------|------------|
| `rplidar_node` | rplidar_ros | `/scan` | — | `serial_port`, `frame_id`, `scan_frequency` |
| `motor_driver_node` | slam_robot_hardware | `/odom`, `/tf` (odom→base) | `/cmd_vel` | GPIO pins, `wheel_radius`, `wheel_separation`, `ticks_per_rev` |
| `ultrasonic_node` | slam_robot_hardware | `/ultrasonic/front`, `/ultrasonic/rear` | — | GPIO pins, `poll_rate`, `max_range` |
| `ir_sensor_node` | slam_robot_hardware | `/ir/left_cliff`, `/ir/right_cliff` | — | GPIO pins |
| `battery_monitor_node` | slam_robot_hardware | `/battery_state` | — | `voltage_divider_ratio`, `full_voltage`, `empty_voltage`, `poll_rate` |
| `robot_state_publisher` | robot_state_publisher | `/tf_static`, `/robot_description` | — | URDF file |
| `ekf_node` | robot_localization | `/odometry/filtered`, `/tf` (odom→base) | `/odom`, (optional `/imu`) | EKF config yaml |
| `slam_toolbox_node` | slam_toolbox | `/map`, `/tf` (map→odom) | `/scan`, `/tf` | SLAM params yaml |
| `nav2_stack` | nav2_bringup | `/cmd_vel_nav`, costmaps | `/scan`, `/map`, `/tf`, `/goal_pose` | Nav2 params yaml |
| `twist_mux` | twist_mux | `/cmd_vel` | `/cmd_vel_teleop`, `/cmd_vel_nav`, `/cmd_vel_safety` | Priority config |
| `rosbridge_websocket` | rosbridge_suite | — | — | `port: 9090` |
| `web_server_node` | slam_robot_web | — | — | `port: 8080`, `web_dir` |
| `safety_controller` | slam_robot_nav | `/cmd_vel_safety` | `/ultrasonic/*`, `/ir/*` | Thresholds |
| `multi_floor_manager` | slam_robot_nav | — | — | Map database path |
| `docking_controller` | slam_robot_nav | `/cmd_vel_dock` | `/apriltag/detections`, `/ultrasonic/front` | Dock approach params |
| `auto_dock_node` | slam_robot_nav | — | `/battery_state` | Voltage threshold, dock pose |
| `object_detector_node` | slam_robot_perception | `/detections` | `/camera/image_raw` | Model path, confidence threshold |
| `apriltag_detector_node` | slam_robot_perception | `/apriltag/detections` | `/camera/image_raw` | Tag family, tag size |
| `map_annotator_node` | slam_robot_perception | `/map_annotations` | `/detections`, `/tf` | Persistence time |

### Transform Tree (tf2)

```
map
 └── odom                          (slam_toolbox → map→odom correction)
      └── base_footprint           (ekf_node → odom→base_footprint)
           └── base_link           (static: identity or small offset)
                ├── laser_frame    (static: Lidar mount position)
                ├── camera_link    (static: camera mount position)
                ├── left_wheel     (continuous: encoder rotation)
                ├── right_wheel    (continuous: encoder rotation)
                ├── ultrasonic_front_link  (static)
                └── ultrasonic_rear_link   (static)
```

---

## 4. Environment Configuration (.env.default)

```bash
###############################################################################
# AUTONOMOUS SLAM ROBOT — ENVIRONMENT CONFIGURATION
# Copy to .env and customize before deployment
# All features are toggleable via ENABLE_* flags
# Values are loaded as ROS 2 launch arguments
###############################################################################

# ===========================================================================
# CORE SETTINGS
# ===========================================================================

# Robot name (used in topic namespaces if multi-robot)
ROBOT_NAME=slam_robot

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Mock mode — simulated sensors for desktop development
ENABLE_MOCK_MODE=false

# ===========================================================================
# RPLIDAR CONFIGURATION
# ===========================================================================

# RPLidar serial port (use udev symlink)
RPLIDAR_SERIAL_PORT=/dev/rplidar

# Lidar frame ID in tf2
RPLIDAR_FRAME_ID=laser_frame

# Scan frequency (Hz) — A1 supports 1-10 Hz
RPLIDAR_SCAN_FREQUENCY=5.5

# Invert scan direction (depending on mounting orientation)
RPLIDAR_INVERTED=false

# ===========================================================================
# MOTOR DRIVER (L298N) — GPIO PINS
# ===========================================================================

# Left motor
MOTOR_LEFT_IN1=17
MOTOR_LEFT_IN2=27
MOTOR_LEFT_ENA=12

# Right motor
MOTOR_RIGHT_IN3=22
MOTOR_RIGHT_IN4=23
MOTOR_RIGHT_ENB=13

# PWM frequency for motor speed control (Hz)
MOTOR_PWM_FREQUENCY=1000

# ===========================================================================
# WHEEL ENCODERS — GPIO PINS
# ===========================================================================

# Left encoder
ENCODER_LEFT_A=5
ENCODER_LEFT_B=6

# Right encoder
ENCODER_RIGHT_A=16
ENCODER_RIGHT_B=26

# Encoder ticks per full wheel revolution
ENCODER_TICKS_PER_REV=1440

# ===========================================================================
# ROBOT DIMENSIONS (meters)
# ===========================================================================

# Wheel radius (m)
WHEEL_RADIUS=0.033

# Distance between wheel centers (m)
WHEEL_SEPARATION=0.17

# Odometry covariance multiplier (increase if odom drifts)
ODOM_COVARIANCE_SCALE=1.0

# ===========================================================================
# VELOCITY LIMITS
# ===========================================================================

# Maximum linear velocity (m/s)
MAX_LINEAR_VEL=0.5

# Maximum angular velocity (rad/s)
MAX_ANGULAR_VEL=1.5

# Teleop speed scale (fraction of max, adjustable in web UI)
TELEOP_SPEED_SCALE=0.5

# ===========================================================================
# SLAM (slam_toolbox)
# ===========================================================================

# Enable SLAM (real-time mapping)
ENABLE_SLAM=true

# Map resolution (meters per grid cell)
SLAM_RESOLUTION=0.05

# Max laser range to use (meters, clip beyond this)
SLAM_MAX_LASER_RANGE=12.0

# Minimum travel distance before inserting new scan (meters)
SLAM_MIN_TRAVEL_DISTANCE=0.3

# Minimum rotation before inserting new scan (radians)
SLAM_MIN_TRAVEL_HEADING=0.3

# SLAM mode: online_async (default) or online_sync
SLAM_MODE=online_async

# Map save directory
SLAM_MAP_DIR=~/slam_robot/slam_robot_ws/src/slam_robot_bringup/maps

# ===========================================================================
# NAV2 (AUTONOMOUS NAVIGATION)
# ===========================================================================

# Enable Nav2 autonomous navigation stack
ENABLE_NAV2=true

# Global planner plugin (NavfnPlanner, ThetaStarPlanner, SmacPlanner)
NAV2_GLOBAL_PLANNER=NavfnPlanner

# Local controller plugin (DWBLocalPlanner, MPPIController, RPP)
NAV2_LOCAL_CONTROLLER=DWBLocalPlanner

# Costmap obstacle inflation radius (meters)
NAV2_INFLATION_RADIUS=0.30

# Robot radius for costmap footprint (meters)
NAV2_ROBOT_RADIUS=0.15

# Goal tolerance — position (meters) and orientation (radians)
NAV2_GOAL_XY_TOLERANCE=0.10
NAV2_GOAL_YAW_TOLERANCE=0.15

# ===========================================================================
# WEB TELEOPERATION
# ===========================================================================

# Enable rosbridge + web interface
ENABLE_WEB_TELEOP=true

# rosbridge WebSocket port
ROSBRIDGE_PORT=9090

# Web server HTTP port (serves static files)
WEB_SERVER_PORT=8080

# ===========================================================================
# MULTI-FLOOR MAPPING
# ===========================================================================

# Enable multi-floor map management
ENABLE_MULTI_FLOOR=false

# Floor map database directory
MULTI_FLOOR_DB_DIR=~/slam_robot/floor_maps

# ===========================================================================
# ULTRASONIC SENSORS (HC-SR04)
# ===========================================================================

# Enable ultrasonic backup sensors
ENABLE_ULTRASONIC=false

# Front sensor GPIO
ULTRASONIC_FRONT_TRIGGER=20
ULTRASONIC_FRONT_ECHO=21

# Rear sensor GPIO
ULTRASONIC_REAR_TRIGGER=19
ULTRASONIC_REAR_ECHO=25

# Polling rate (Hz)
ULTRASONIC_POLL_RATE=10

# Max detection range (meters)
ULTRASONIC_MAX_RANGE=2.0

# Min detection range (meters)
ULTRASONIC_MIN_RANGE=0.02

# ===========================================================================
# IR OBSTACLE / CLIFF SENSORS
# ===========================================================================

# Enable IR sensors
ENABLE_IR_SENSORS=false

# Left cliff sensor GPIO
IR_LEFT_CLIFF_GPIO=24

# Right cliff sensor GPIO
IR_RIGHT_CLIFF_GPIO=8

# ===========================================================================
# SAFETY CONTROLLER
# ===========================================================================

# Emergency stop distance (meters) — ultrasonic threshold
SAFETY_STOP_DISTANCE=0.20

# Slowdown distance (meters) — reduce speed in this zone
SAFETY_SLOWDOWN_DISTANCE=0.50

# Cliff detection enables immediate stop
SAFETY_CLIFF_STOP=true

# ===========================================================================
# DOCKING STATION (AprilTag)
# ===========================================================================

# Enable AprilTag docking
ENABLE_DOCKING=false

# AprilTag family (tag36h11 recommended)
DOCK_TAG_FAMILY=tag36h11

# AprilTag ID for dock marker
DOCK_TAG_ID=0

# AprilTag physical size (meters, outer edge to outer edge)
DOCK_TAG_SIZE=0.16

# Docking approach speed (m/s)
DOCK_APPROACH_SPEED=0.08

# Final approach distance (meters — switch to ultrasonic precision)
DOCK_FINAL_APPROACH_DISTANCE=0.30

# Dock pose on map (x, y, yaw) — where the dock is located
DOCK_MAP_X=0.0
DOCK_MAP_Y=0.0
DOCK_MAP_YAW=0.0

# ===========================================================================
# CAMERA & OBJECT DETECTION
# ===========================================================================

# Enable Pi Camera
ENABLE_CAMERA=false

# Camera resolution
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=15

# Enable object detection
ENABLE_OBJECT_DETECTION=false

# Detection model (mobilenet_ssd or yolov8_nano)
DETECTION_MODEL=mobilenet_ssd

# Confidence threshold (0.0 - 1.0)
DETECTION_CONFIDENCE=0.5

# Model file path
DETECTION_MODEL_PATH=~/slam_robot/models/mobilenet_ssd.tflite

# ===========================================================================
# BATTERY MONITORING
# ===========================================================================

# Enable battery voltage monitoring via ADS1115
ENABLE_BATTERY_MONITOR=false

# ADS1115 I2C address (default 0x48)
BATTERY_ADC_ADDRESS=0x48

# ADC channel for battery voltage
BATTERY_ADC_CHANNEL=0

# Voltage divider ratio (actual_voltage = adc_reading * ratio)
BATTERY_VOLTAGE_DIVIDER_RATIO=4.0

# Battery full voltage (V)
BATTERY_FULL_VOLTAGE=12.6

# Battery empty voltage (V) — do NOT discharge below this
BATTERY_EMPTY_VOLTAGE=9.6

# Polling rate (Hz)
BATTERY_POLL_RATE=1

# ===========================================================================
# AUTO-DOCK
# ===========================================================================

# Enable auto-dock on low battery
ENABLE_AUTO_DOCK=false

# Voltage threshold to trigger auto-dock (V)
AUTO_DOCK_VOLTAGE_THRESHOLD=10.2

# Percentage threshold to trigger auto-dock (fallback if voltage not used)
AUTO_DOCK_PERCENTAGE_THRESHOLD=15

# ===========================================================================
# DEPLOYMENT
# ===========================================================================

# Target Pi SSH alias (must match ~/.ssh/config)
DEPLOY_HOST=rasp-pi
DEPLOY_PATH=~/slam_robot
```

---

## 5. URDF Robot Model

The robot model defines the physical structure and sensor positions for `tf2`:

```xml
<!-- slam_robot.urdf.xacro (simplified) -->
<robot name="slam_robot" xmlns:xacro="http://www.ros.org/wiki/xacro">

  <!-- Base link — robot body center -->
  <link name="base_footprint"/>
  <link name="base_link">
    <visual>
      <geometry><box size="0.20 0.18 0.08"/></geometry>
    </visual>
    <collision>
      <geometry><cylinder radius="0.15" length="0.08"/></geometry>
    </collision>
  </link>
  <joint name="base_joint" type="fixed">
    <parent link="base_footprint"/>
    <child link="base_link"/>
    <origin xyz="0 0 0.04"/>
  </joint>

  <!-- Left wheel -->
  <link name="left_wheel">
    <visual>
      <geometry><cylinder radius="${wheel_radius}" length="0.026"/></geometry>
    </visual>
  </link>
  <joint name="left_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel"/>
    <origin xyz="0 ${wheel_separation/2} 0" rpy="${-pi/2} 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <!-- Right wheel (mirrored) -->
  <link name="right_wheel">
    <visual>
      <geometry><cylinder radius="${wheel_radius}" length="0.026"/></geometry>
    </visual>
  </link>
  <joint name="right_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="right_wheel"/>
    <origin xyz="0 ${-wheel_separation/2} 0" rpy="${-pi/2} 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <!-- RPLidar mount -->
  <link name="laser_frame"/>
  <joint name="lidar_joint" type="fixed">
    <parent link="base_link"/>
    <child link="laser_frame"/>
    <origin xyz="0.05 0 0.10" rpy="0 0 0"/>
  </joint>

  <!-- Camera mount (optional) -->
  <link name="camera_link"/>
  <joint name="camera_joint" type="fixed">
    <parent link="base_link"/>
    <child link="camera_link"/>
    <origin xyz="0.10 0 0.06" rpy="0 0 0"/>
  </joint>

  <!-- Caster wheel -->
  <link name="caster_wheel">
    <visual>
      <geometry><sphere radius="0.015"/></geometry>
    </visual>
  </link>
  <joint name="caster_joint" type="fixed">
    <parent link="base_link"/>
    <child link="caster_wheel"/>
    <origin xyz="-0.08 0 -0.025"/>
  </joint>

</robot>
```

---

## 6. Launch File Architecture

### `robot_bringup.launch.py` (Master Launch)

```
robot_bringup.launch.py
├── Load .env → launch arguments
├── robot_state_publisher (URDF)
├── rplidar_node (if not MOCK_MODE)
├── motor_driver_node (if not MOCK_MODE)
├── ekf_node (robot_localization)
├── Include: slam.launch.py (if ENABLE_SLAM)
├── Include: nav2.launch.py (if ENABLE_NAV2)
├── Include: teleop_web.launch.py (if ENABLE_WEB_TELEOP)
├── Include: sensors.launch.py (if ENABLE_ULTRASONIC or ENABLE_IR)
├── Include: docking.launch.py (if ENABLE_DOCKING)
├── twist_mux
├── safety_controller (if ultrasonic or IR enabled)
├── battery_monitor_node (if ENABLE_BATTERY_MONITOR)
├── object_detector_node (if ENABLE_OBJECT_DETECTION)
├── map_annotator_node (if ENABLE_OBJECT_DETECTION)
└── auto_dock_node (if ENABLE_AUTO_DOCK)
```

### Feature Dependencies

| Feature | Requires |
|---------|----------|
| Nav2 | SLAM (or pre-loaded map) |
| Docking | Camera + Nav2 |
| Auto-dock | Docking + Battery Monitor |
| Object Detection | Camera |
| Map Annotations | Object Detection |
| Multi-floor | SLAM |

---

## 7. Costmap Configuration

### Global Costmap Layers

| Layer | Source | Purpose |
|-------|--------|---------|
| `static_layer` | `/map` (from SLAM or map_server) | Known obstacles from the map |
| `obstacle_layer` | `/scan` (Lidar) | Dynamic obstacle detection |
| `ultrasonic_layer` | `/ultrasonic/*` (if enabled) | Close-range obstacle buffer |
| `inflation_layer` | Computed | Inflates obstacles by robot radius + safety margin |

### Local Costmap Layers

| Layer | Source | Purpose |
|-------|--------|---------|
| `obstacle_layer` | `/scan` (Lidar) | Real-time nearby obstacles |
| `ultrasonic_layer` | `/ultrasonic/*` (if enabled) | Sub-Lidar-range obstacles |
| `inflation_layer` | Computed | Safety inflation around obstacles |

---

## 8. Web Interface Architecture

### Technology Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| ROS Bridge | rosbridge_suite | WebSocket ↔ ROS 2 topic bridge |
| ROS Client | roslibjs | JavaScript ROS 2 topic pub/sub |
| Joystick | nipplejs | Virtual joystick widget |
| Map Rendering | HTML5 Canvas | Draw occupancy grid from `/map` |
| Camera | ros2-web-video-server (or roslibjs image) | Compressed image stream |
| UI | Vanilla HTML/CSS/JS | Dark theme, no framework |

### WebSocket Message Flow

```
Browser (roslibjs)                         rosbridge_websocket
     │                                            │
     │── subscribe('/map') ──────────────────────►│──► slam_toolbox /map
     │◄─ OccupancyGrid JSON ◄────────────────────│
     │                                            │
     │── publish('/cmd_vel_teleop', Twist) ──────►│──► twist_mux → motors
     │                                            │
     │── subscribe('/battery_state') ────────────►│──► battery_monitor_node
     │◄─ BatteryState JSON ◄─────────────────────│
     │                                            │
     │── action('/navigate_to_pose', goal) ──────►│──► Nav2 stack
     │◄─ feedback (distance_remaining) ◄─────────│
     │◄─ result (success/failure) ◄──────────────│
```

---

## 9. Safety Architecture

### twist_mux Priority Table

| Priority | Source | Topic | Condition |
|----------|--------|-------|-----------|
| 1 (highest) | Safety Controller | `/cmd_vel_safety` | Obstacle < SAFETY_STOP_DISTANCE |
| 2 | Web Teleop / Keyboard | `/cmd_vel_teleop` | User active input |
| 3 | Nav2 Controller | `/cmd_vel_nav` | Autonomous navigation active |
| 4 | Docking Controller | `/cmd_vel_dock` | Docking sequence active |

### Emergency Stop Chain

```
E-STOP button (web) → publish Twist(0,0) to /cmd_vel_safety
                     → lock motors (set ENA/ENB LOW)
                     → cancel active Nav2 goal
                     → set robot state to STOPPED
                     → require explicit RESUME to re-enable
```

---

## 10. Performance Expectations

| Metric | Pi 4 (4GB) | Pi 5 (8GB) |
|--------|-----------|-----------|
| SLAM map update rate | ~3 Hz | ~5 Hz |
| Nav2 planning time | ~200ms | ~100ms |
| Object detection (MobileNet) | ~300ms/frame | ~150ms/frame |
| Object detection (YOLOv8-nano) | ~800ms/frame | ~400ms/frame |
| rosbridge latency | ~20ms | ~10ms |
| Max sustained robot speed | 0.5 m/s | 0.5 m/s (motor limited) |
| Battery life (12V 3000mAh) | ~90 min active | ~90 min active |
| Map size (typical house) | ~2-5 MB | ~2-5 MB |

---

## 11. File Format Specifications

### Map Files (nav2_map_server)

```yaml
# map.yaml — map metadata
image: map.pgm
resolution: 0.050000
origin: [-10.0, -10.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

Accompanying `.pgm` file is a grayscale image where:
- White (254) = free space
- Black (0) = occupied
- Gray (205) = unknown

### Floor Database (multi-floor)

```json
{
  "floors": [
    {
      "name": "Ground Floor",
      "map_yaml": "maps/ground_floor.yaml",
      "initial_pose": {"x": 0.0, "y": 0.0, "yaw": 0.0}
    },
    {
      "name": "First Floor",
      "map_yaml": "maps/first_floor.yaml",
      "initial_pose": {"x": 0.0, "y": 0.0, "yaw": 0.0}
    }
  ],
  "active_floor": "Ground Floor"
}
```