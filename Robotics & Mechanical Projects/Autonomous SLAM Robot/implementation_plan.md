# Implementation Plan
## Autonomous SLAM Robot

---

## Executive Summary

Build a wheeled robot with RPLidar A1 and L298N motor driver, powered by a Raspberry Pi running ROS 2 Humble. The robot uses slam_toolbox for real-time SLAM mapping, Nav2 for autonomous click-to-goal navigation, and rosbridge + roslibjs for a dark-themed web teleoperation interface. Optional features include ultrasonic/IR backup sensors, AprilTag docking station, camera object detection projected onto the map, and battery monitoring with auto-dock. All features are `.env` toggleable.

**Budget:** ~$165–190 | **Timeline:** 10–14 days | **Difficulty:** 10/10

---

## Phase 1: OS & ROS 2 Foundation (Day 1)

### 1.1 Flash & Configure Pi

```bash
# Flash Ubuntu 22.04 Server (64-bit) — ROS 2 Humble requires Ubuntu 22.04
# Enable SSH during flash (Raspberry Pi Imager advanced options)

# Boot, connect, SSH
ssh rasp-pi          # alias for pi@192.168.216.90

# Full system update
sudo apt update && sudo apt upgrade -y

# Set locale (required for ROS 2)
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 1.2 Install ROS 2 Humble

```bash
# Add ROS 2 GPG key
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update

# Install ROS 2 Humble desktop (includes RViz2, rqt, demos)
# For minimal: ros-humble-ros-base
sudo apt install ros-humble-desktop -y

# Source ROS 2
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc

# Install build tools
sudo apt install python3-colcon-common-extensions python3-rosdep2 python3-pip -y
rosdep update

# Verify
ros2 topic list
# Expect: /rosout, /parameter_events
```

### 1.3 Install Navigation Packages

```bash
# SLAM
sudo apt install ros-humble-slam-toolbox -y

# Nav2
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup -y

# RPLidar driver
sudo apt install ros-humble-rplidar-ros -y

# rosbridge (web interface)
sudo apt install ros-humble-rosbridge-suite -y

# Robot state publisher
sudo apt install ros-humble-robot-state-publisher ros-humble-joint-state-publisher -y

# Map server
sudo apt install ros-humble-nav2-map-server -y

# TF tools
sudo apt install ros-humble-tf2-tools -y

# Python dependencies
pip3 install python-dotenv RPi.GPIO pigpio adafruit-circuitpython-ads1x15
```

**Milestone:** Pi running Ubuntu 22.04 with full ROS 2 Humble + SLAM + Nav2 installed.

---

## Phase 2: RPLidar A1 Integration (Day 2 — Morning)

### 2.1 Connect & Configure

```bash
# Plug RPLidar A1 into Pi USB port
ls /dev/ttyUSB*
# Expect: /dev/ttyUSB0

# Add user to dialout group
sudo usermod -aG dialout $USER
# Reboot or re-login
```

### 2.2 udev Rule for Persistent Device Name

```bash
# Create udev rule
cat | sudo tee /etc/udev/rules.d/99-slam-robot.rules << 'EOF'
# RPLidar A1 (Silicon Labs CP210x)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", MODE="0666"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger

# Verify
ls -la /dev/rplidar
# Should point to ttyUSB0
```

### 2.3 Test RPLidar

```bash
# Launch RPLidar driver
ros2 launch rplidar_ros rplidar_a1_launch.py serial_port:=/dev/rplidar

# In another terminal:
ros2 topic echo /scan --once
# Expect: LaserScan message with ~360 ranges

ros2 topic hz /scan
# Expect: ~5-10 Hz (scans per second, not individual points)
```

### 2.4 Visualize in RViz2 (from Desktop)

```bash
# On desktop machine with ROS 2 installed:
export ROS_DOMAIN_ID=42   # Match the Pi
rviz2
# Add → By Topic → /scan → LaserScan
# Set Fixed Frame to "laser"
# Should see 360° point cloud
```

**Milestone:** RPLidar A1 publishing laser scans on `/scan` with persistent device name.

---

## Phase 3: Motor Driver & Odometry (Day 2 — Afternoon + Day 3)

### 3.1 Physical Wiring

Wire per the wiring diagram in README.md:
- L298N IN1-IN4 → GPIO 17, 27, 22, 23
- L298N ENA, ENB → GPIO 12, 13 (hardware PWM)
- Encoder channels → GPIO 5, 6, 16, 20
- 12V battery → L298N power terminals
- Common ground between Pi and L298N

### 3.2 Create ROS 2 Workspace & Motor Package

```bash
mkdir -p ~/slam_robot/slam_robot_ws/src
cd ~/slam_robot/slam_robot_ws/src

# Create motor driver package
ros2 pkg create --build-type ament_python slam_robot_driver \
  --dependencies rclpy geometry_msgs nav_msgs sensor_msgs std_msgs

cd slam_robot_driver/slam_robot_driver/
```

### 3.3 Implement Motor Driver

```python
# motor_driver.py — Low-level L298N GPIO control
# - set_motors(left_pwm, right_pwm) → sets direction + PWM duty
# - stop() → all PWM to 0
# - cleanup() → release GPIO

# encoder.py — Wheel encoder reader
# - Uses GPIO interrupts for tick counting
# - get_ticks() → returns (left_ticks, right_ticks) since last call
# - Handles quadrature decoding (A+B channels)

# motor_driver_node.py — ROS 2 node
# - Subscribes to /cmd_vel (geometry_msgs/Twist)
# - Converts (linear.x, angular.z) → (left_speed, right_speed) via diff drive kinematics
# - Reads encoder ticks, computes odometry
# - Publishes /odom (nav_msgs/Odometry)
# - Broadcasts odom → base_link TF
# - Watchdog: stops motors if no /cmd_vel for 500ms
```

### 3.4 Build & Test

```bash
cd ~/slam_robot/slam_robot_ws
colcon build --packages-select slam_robot_driver
source install/setup.bash

# Run motor driver node
ros2 run slam_robot_driver motor_driver_node

# Test: send velocity command
ros2 topic pub /cmd_vel geometry_msgs/Twist '{linear: {x: 0.1}}' -r 10
# Robot should drive forward

# Verify odometry
ros2 topic echo /odom --once
# Expect: position updating as robot moves

# Stop
ros2 topic pub /cmd_vel geometry_msgs/Twist '{}'
```

### 3.5 Calibrate Odometry

```bash
# Mark start position on floor with tape
# Drive robot forward 1 meter:
ros2 topic pub /cmd_vel geometry_msgs/Twist '{linear: {x: 0.15}}' -r 10
# (wait until robot travels ~1m, then stop)

# Check odometry:
ros2 topic echo /odom --field pose.pose.position.x
# Should read ~1.0 — adjust WHEEL_DIAMETER_M and ENCODER_TICKS_PER_REV in .env

# Spin test: rotate robot 360°
# Check odometry theta returns to ~0 — adjust WHEEL_BASE_M
```

**Milestone:** Robot drives on command with calibrated wheel odometry.

---

## Phase 4: URDF & TF Tree (Day 3 — Afternoon)

### 4.1 Create URDF

Create a minimal URDF describing the robot's physical layout:
- `base_link` at center of robot
- `laser` joint offset to RPLidar mounting position
- `left_wheel`, `right_wheel` joints at correct wheelbase
- `camera_link` if using Pi Camera

### 4.2 Launch robot_state_publisher

```bash
# In launch file:
robot_state_publisher_node = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    parameters=[{'robot_description': urdf_content}]
)
```

### 4.3 Verify TF Tree

```bash
ros2 run tf2_tools view_frames
# Output: frames.pdf
# Expected tree:
# map → odom → base_link → laser
#                        → left_wheel
#                        → right_wheel
#                        → camera_link (if present)
```

**Milestone:** Complete TF tree ready for SLAM and Nav2.

---

## Phase 5: SLAM with slam_toolbox (Day 4)

### 5.1 Configure slam_toolbox

Create `slam_toolbox_params.yaml` based on TSD §6. Key settings:
- `mode: online_async` (best for real-time on Pi)
- `resolution: 0.05` (5cm per pixel)
- `max_laser_range: 12.0` (RPLidar A1 max)
- Frames: `map_frame: map`, `odom_frame: odom`, `base_frame: base_link`

### 5.2 Create SLAM Launch File

```python
# slam.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            parameters=['config/slam_toolbox_params.yaml'],
            output='screen'
        )
    ])
```

### 5.3 Test SLAM

```bash
# Launch RPLidar + motor driver + URDF + slam_toolbox
ros2 launch slam_robot_bringup slam.launch.py

# Drive robot around the room with teleop_twist_keyboard
sudo apt install ros-humble-teleop-twist-keyboard
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Watch map build in RViz2:
# On desktop: rviz2 → Add OccupancyGrid → /map
# Map should grow as robot explores
```

### 5.4 Save Map

```bash
# Save completed map
ros2 run nav2_map_server map_saver_cli -f ~/slam_robot/slam_robot_ws/src/slam_robot_bringup/maps/floor1

# Verify
ls maps/
# floor1.pgm  floor1.yaml
```

**Milestone:** Robot builds real-time maps of its environment using lidar SLAM.

---

## Phase 6: Nav2 Autonomous Navigation (Day 5)

### 6.1 Configure Nav2

Create `nav2_params.yaml` based on TSD §6. Configure:
- Global planner: NavfnPlanner
- Local controller: DWBLocalPlanner
- Costmap layers: static + obstacle (lidar) + inflation
- Robot radius: 0.15m
- Inflation radius: 0.25m
- Recovery behaviors: spin, backup, wait

### 6.2 Launch Nav2 Stack

```bash
# Launch with saved map for localization + navigation
ros2 launch slam_robot_bringup nav2.launch.py \
  map:=~/slam_robot/slam_robot_ws/src/slam_robot_bringup/maps/floor1.yaml
```

### 6.3 Test Autonomous Navigation

```bash
# From RViz2:
# 1. Set initial pose: 2D Pose Estimate tool → click/drag on map
# 2. Send goal: 2D Nav Goal tool → click/drag on map
# 3. Robot should plan path and navigate autonomously

# From CLI:
ros2 topic pub --once /goal_pose geometry_msgs/PoseStamped \
  '{header: {frame_id: "map"}, pose: {position: {x: 2.0, y: 1.0}, orientation: {w: 1.0}}}'

# Watch robot navigate, avoid obstacles, reach goal
```

### 6.4 Test Recovery Behaviors

- Place robot in a tight corner → should spin/backup to escape
- Block path with obstacle → should replan around it
- Send unreachable goal → should report failure after max retries

**Milestone:** Robot autonomously navigates to goals while avoiding obstacles.

---

## Phase 7: Web Interface — rosbridge + roslibjs (Day 6–7)

### 7.1 Set Up rosbridge

```bash
# Launch rosbridge WebSocket server
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=9090

# Verify from browser devtools:
# new WebSocket('ws://192.168.216.90:9090')
# Should connect without error
```

### 7.2 Create Web Interface Package

```bash
cd ~/slam_robot/slam_robot_ws/src
ros2 pkg create --build-type ament_python slam_robot_web
```

### 7.3 Implement Dark Theme HTML

```html
<!-- index.html — Main page layout -->
<!-- Dark theme: background #1a1a2e, panels #16213e, accent #0f3460, text #e0e0e0 -->
<!-- Sections: -->
<!--   - Header: robot name, connection status, battery widget -->
<!--   - Left panel: virtual joystick (nipplejs) -->
<!--   - Center: live SLAM map (canvas) + click-to-goal overlay -->
<!--   - Right panel: sensor readings, Nav2 status, dock status -->
<!--   - Footer: coordinate display, active goals, speed -->
```

### 7.4 Implement JavaScript Modules

```javascript
// app.js — ROS 2 connection
var ros = new ROSLIB.Ros({ url: 'ws://192.168.216.90:9090' });
ros.on('connection', () => { /* update status indicator */ });
ros.on('error', (error) => { /* show error */ });
ros.on('close', () => { /* reconnect logic */ });

// teleop.js — Virtual joystick → /cmd_vel
// Uses nipplejs library
// Maps joystick position to Twist.linear.x and Twist.angular.z
// Publishes at 10 Hz while joystick active, sends zero on release

// map_view.js — Subscribe to /map, render on canvas
// OccupancyGrid: -1 = unknown (gray), 0 = free (dark), 100 = occupied (light)
// Show robot position from /tf (base_link in map frame)
// Auto-refresh at MAP_DISPLAY_RATE Hz

// nav_goals.js — Click on map → PoseStamped
// Convert canvas pixel coordinates to map coordinates
// Publish to /goal_pose
// Show goal marker and planned path on map

// detection_overlay.js — Subscribe to /detected_objects
// Show labeled markers at map coordinates
// Color-coded by object class

// battery_widget.js — Subscribe to /battery_state
// Battery icon with percentage fill
// Color: green (>50%), yellow (20-50%), red (<20%)
```

### 7.5 Serve Web Files

```python
# Simple HTTP server for static files (no Flask needed)
# Launch via web_interface.launch.py:
#   - rosbridge_websocket on port 9090
#   - Python http.server on port 8080 serving slam_robot_web/web/
```

### 7.6 Test Web Interface

1. Open `http://192.168.216.90:8080` in browser
2. Verify WebSocket connection indicator turns green
3. Test joystick — drag to drive, robot moves
4. Verify SLAM map renders and updates
5. Click on map — robot navigates to clicked point
6. Verify battery widget shows voltage/percentage
7. Test on mobile browser (touch joystick)
8. Test on tablet (landscape mode for better map view)

**Milestone:** Full web-based teleoperation with live SLAM map and click-to-goal navigation.

---

## Phase 8: Sensor Nodes — Ultrasonic & IR (Day 8)

### 8.1 Ultrasonic Sensors (HC-SR04)

```bash
# Wire HC-SR04 with voltage divider on Echo pin (5V → 3.3V):
# Echo → 1kΩ → GPIO → 2kΩ → GND
```

```python
# ultrasonic_node.py
# - Trigger pulse: GPIO HIGH for 10µs
# - Measure echo duration
# - Distance = (echo_time * 343) / 2
# - Publish sensor_msgs/Range on /range/front_left, /range/front_right
# - Emergency stop if distance < US_EMERGENCY_STOP_DISTANCE
```

### 8.2 IR Cliff Sensors

```python
# ir_sensor_node.py
# - Read digital GPIO (HIGH = floor detected, LOW = cliff)
# - Publish std_msgs/Bool on /cliff/left, /cliff/right
# - Emergency stop: publish zero Twist to /cmd_vel_safety
#   (cmd_vel multiplexer gives priority to safety stop)
```

### 8.3 Add to Nav2 Costmap

Configure ultrasonic sensors as an observation source in the costmap:
```yaml
# In nav2_params.yaml:
obstacle_layer:
  observation_sources: scan ultrasonic
  ultrasonic:
    topic: /range/front_left
    data_type: Range
    clearing: false
    marking: true
    obstacle_max_range: 2.0
```

**Milestone:** Backup sensors provide additional safety beyond lidar.

---

## Phase 9: Battery Monitoring (Day 9 — Morning)

### 9.1 ADS1115 ADC Setup

```bash
# Wire ADS1115 to Pi I2C (SDA → GPIO 2, SCL → GPIO 3)
# Wire voltage divider from 12V battery to ADS1115 A0 input
# Voltage divider: R1=20kΩ, R2=10kΩ → ratio 0.333 → 12V reads as 4V (safe for ADC)

# Verify I2C
sudo i2cdetect -y 1
# Expect: 0x48 for ADS1115
```

### 9.2 Battery Monitor Node

```python
# battery_monitor_node.py
# - Read ADC value via adafruit_ads1x15
# - Convert to voltage: adc_voltage / BATTERY_VOLTAGE_DIVIDER_RATIO
# - Map to percentage: (voltage - empty) / (full - empty) * 100
# - Publish BatteryState.msg on /battery_state
# - Set low_battery flag if < BATTERY_LOW_THRESHOLD
```

### 9.3 Web UI Battery Widget

- Green bar when > 50%
- Yellow bar with "LOW BATTERY" text when 20–50%
- Red flashing bar when < 20%
- Voltage displayed in small text below bar

**Milestone:** Real-time battery level on web UI.

---

## Phase 10: Docking Station (Day 9 — Afternoon + Day 10)

### 10.1 AprilTag Setup

```bash
# Install AprilTag library
pip3 install dt-apriltags

# Enable Pi Camera
sudo raspi-config  # Interface Options → Camera → Enable

# Print tag36h11 ID 0 (16cm × 16cm recommended for 2m detection range)
# Mount tag at docking station at robot camera height
```

### 10.2 AprilTag Detection Node

```python
# apriltag_dock_node.py
# - Capture frames from Pi Camera (picamera2 or OpenCV)
# - Detect AprilTag using dt-apriltags library
# - Estimate 6DOF pose of tag relative to camera
# - Transform tag pose to base_link frame using TF
# - Publish PoseStamped on /dock/tag_pose
```

### 10.3 Docking Controller

```python
# docking_controller_node.py
# Docking sequence:
# 1. Navigate near dock using Nav2 (to DOCK_MAP_X/Y position)
# 2. Switch to visual servoing: use /dock/tag_pose for approach
# 3. Proportional controller:
#    linear.x  = Kp_linear * distance_to_tag
#    angular.z = Kp_angular * angle_to_tag
# 4. Reduce speed as distance decreases (min: DOCK_APPROACH_SPEED)
# 5. Docked when distance < DOCK_ALIGNMENT_TOLERANCE
# 6. Timeout after DOCK_TIMEOUT seconds → report failure
```

**Milestone:** Robot can autonomously dock at the charging station.

---

## Phase 11: Auto-Dock on Low Battery (Day 10 — Afternoon)

### 11.1 Auto-Dock Node

```python
# auto_dock_node.py
# - Subscribe to /battery_state
# - When percentage < BATTERY_LOW_THRESHOLD:
#     1. Cancel any active Nav2 goal
#     2. Navigate to dock pre-approach position (DOCK_MAP_X/Y/YAW)
#     3. Call /start_docking service
# - When percentage ≤ BATTERY_CRITICAL_THRESHOLD:
#     Emergency stop all motion (publish zero Twist continuously)
```

**Milestone:** Battery-aware autonomous operation.

---

## Phase 12: Object Detection on Map (Day 11)

### 12.1 TFLite Detection Node

```python
# detection_node.py
# 1. Capture camera frame at DETECTION_RATE Hz
# 2. Run TFLite SSD MobileNet inference
# 3. For each detection above DETECTION_CONFIDENCE_THRESHOLD:
#    a. Estimate distance from bounding box size (approximate)
#    b. Compute bearing from bbox center in camera frame
#    c. Transform to map frame using TF (camera_link → map)
#    d. Publish DetectedObject.msg on /detected_objects
```

### 12.2 Map Overlay

```javascript
// detection_overlay.js
// Subscribe to /detected_objects
// For each detected object:
//   - Convert map coordinates to canvas pixels
//   - Draw labeled marker (icon + text)
//   - Color by class (person=blue, furniture=brown, animal=green)
//   - Fade markers after 30 seconds without re-detection
```

**Milestone:** Objects detected by camera appear as markers on the live SLAM map.

---

## Phase 13: Multi-Floor Mapping (Day 12 — Morning)

### 13.1 Map Management Services

```python
# Implement SaveMap, LoadMap, SwitchFloor services
# SaveMap:
#   1. Call slam_toolbox serialize_map service
#   2. Call map_saver_cli to save .pgm/.yaml
#   3. Record metadata (floor name, timestamp, file paths)

# LoadMap:
#   1. Load map via map_server
#   2. Reconfigure Nav2 with new static layer
#   3. Reset localization (AMCL initial pose)

# SwitchFloor:
#   1. SaveMap current floor
#   2. LoadMap target floor
#   3. Update active floor state
```

### 13.2 Web UI Maps Page

- List saved maps with thumbnails
- Save / Load / Delete buttons
- Active floor indicator
- Map preview (scaled-down occupancy grid)

**Milestone:** Seamless multi-floor operation.

---

## Phase 14: Main Launch File & Feature Toggles (Day 12 — Afternoon)

### 14.1 Bringup Launch File

```python
# robot_bringup.launch.py
# - Reads .env via python-dotenv
# - Always launches: rplidar, motor_driver, robot_state_publisher
# - Conditionally launches based on ENABLE_* flags:
#   ENABLE_SLAM → slam_toolbox
#   ENABLE_NAV2 → Nav2 stack
#   ENABLE_WEB_TELEOP → rosbridge + web server
#   ENABLE_ULTRASONIC → ultrasonic_node
#   ENABLE_IR_CLIFF → ir_sensor_node
#   ENABLE_BATTERY_MONITOR → battery_monitor_node
#   ENABLE_DOCKING → apriltag_dock_node + docking_controller_node
#   ENABLE_AUTO_DOCK → auto_dock_node
#   ENABLE_OBJECT_DETECTION → detection_node
```

### 14.2 Test All Combinations

```bash
# Full stack
ros2 launch slam_robot_bringup robot_bringup.launch.py

# Minimal (SLAM + teleop only)
ENABLE_NAV2=false ENABLE_ULTRASONIC=false ENABLE_IR_CLIFF=false \
  ros2 launch slam_robot_bringup robot_bringup.launch.py

# Navigation only (localization mode, no SLAM)
SLAM_MODE=localization ENABLE_DOCKING=false ENABLE_OBJECT_DETECTION=false \
  ros2 launch slam_robot_bringup robot_bringup.launch.py
```

**Milestone:** Single launch command brings up the entire robot with configurable features.

---

## Phase 15: systemd & Production (Day 13)

### 15.1 Create systemd Service

```bash
sudo tee /etc/systemd/system/slam-robot.service << 'EOF'
[Unit]
Description=Autonomous SLAM Robot — ROS 2 Bringup
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/slam_robot
Environment="HOME=/home/pi"
ExecStart=/bin/bash -c '\
  source /opt/ros/humble/setup.bash && \
  source /home/pi/slam_robot/slam_robot_ws/install/setup.bash && \
  ros2 launch slam_robot_bringup robot_bringup.launch.py'
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now slam-robot
```

### 15.2 Deploy Script

```bash
# deploy/deploy_to_pi.sh
#!/bin/bash
rsync -avz --progress \
  --exclude 'build' --exclude 'install' --exclude 'log' \
  --exclude '__pycache__' --exclude '.git' \
  . rasp-pi:~/slam_robot/

echo "Rebuilding workspace on Pi..."
ssh rasp-pi 'cd ~/slam_robot/slam_robot_ws && \
  source /opt/ros/humble/setup.bash && \
  colcon build --symlink-install'

echo "Restarting service..."
ssh rasp-pi 'sudo systemctl restart slam-robot'
```

**Milestone:** Robot auto-starts on boot and can be deployed with one command.

---

## Phase 16: Testing & Validation (Day 13–14)

### 16.1 Unit Tests

```bash
cd ~/slam_robot/slam_robot_ws
colcon test
colcon test-result --verbose
```

### 16.2 Integration Tests

| Test | Steps | Expected |
|------|-------|----------|
| SLAM mapping | Drive robot around room | Map matches room layout |
| Nav2 goal | Send 5 navigation goals | Robot reaches all 5 within tolerance |
| Obstacle avoidance | Place box in path | Robot replans around obstacle |
| Recovery | Block robot in corner | Spin/backup recovery succeeds |
| Web joystick | Drive from browser | Responsive control, <100ms latency |
| Web map | Observe during SLAM | Map updates in browser every 0.5s |
| Click-to-goal | Click on web map | Robot navigates to clicked point |
| Emergency stop | Trigger cliff sensor | Immediate motor halt |
| Battery auto-dock | Set low threshold | Robot navigates to dock |
| Mock mode | All ENABLE_MOCK_MODE=true | All nodes publish fake data |

### 16.3 Calibration Validation

- Drive 1m straight → odometry reads 1.0 ± 0.05m
- Rotate 360° → odometry reads 0° ± 5°
- SLAM map walls are straight (not curved or double)
- Nav2 costmap inflation matches physical robot clearance

### 16.4 Stress Test

- Run full stack for 1+ hour continuous operation
- Monitor CPU/RAM usage (`htop`)
- Verify no memory leaks in ROS 2 nodes
- Verify map quality doesn't degrade over time

**Milestone:** All tests pass, robot operates reliably.

---

## Phase 17: Documentation & Final Deployment (Day 14)

### 17.1 Documentation

- `docs/wiring_diagram.md` — Pin-by-pin wiring with photos
- `docs/assembly_guide.md` — Physical chassis assembly steps
- `docs/ros2_cheatsheet.md` — Common commands for operating this robot
- `docs/calibration_guide.md` — Odometry and sensor calibration procedures

### 17.2 Final Deployment

```bash
# Deploy
bash deploy/deploy_to_pi.sh

# Full smoke test
ssh rasp-pi
sudo systemctl status slam-robot
# Navigate to http://192.168.216.90:8080
# Test: joystick, SLAM, navigation, sensors, battery
```

### 17.3 Toggle Verification

Test each `.env` flag independently:
- `ENABLE_SLAM=false` → robot drives but no map
- `ENABLE_NAV2=false` → SLAM works but no autonomous navigation
- `ENABLE_WEB_TELEOP=false` → CLI-only operation
- `ENABLE_ULTRASONIC=false` → lidar-only obstacle avoidance
- `ENABLE_DOCKING=false` → no dock approach
- `ENABLE_OBJECT_DETECTION=false` → no camera markers
- `ENABLE_MOCK_MODE=true` → all fake data, no hardware needed

**Milestone:** Project complete — autonomous SLAM robot with web interface and all features toggleable.

---

## Timeline Summary

| Day | Phase | Milestone |
|-----|-------|-----------|
| 1 | OS + ROS 2 install | Pi running ROS 2 Humble |
| 2 | RPLidar + motor driver | Lidar scanning + motors spinning |
| 3 | Odometry + calibration | Calibrated wheel odometry |
| 3-4 | URDF + TF tree | Complete transform tree |
| 4 | SLAM (slam_toolbox) | Real-time map building |
| 5 | Nav2 navigation | Autonomous click-to-goal |
| 6-7 | Web interface | Full web teleoperation |
| 8 | Ultrasonic + IR sensors | Backup safety sensors |
| 9 | Battery monitor + docking | Battery-aware + dock approach |
| 10 | Auto-dock | Autonomous low-battery docking |
| 11 | Object detection | Camera markers on SLAM map |
| 12 | Multi-floor + launch file | Feature toggles working |
| 13 | systemd + testing | Production-ready deployment |
| 14 | Documentation + final test | Project complete |
