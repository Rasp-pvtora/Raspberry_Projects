# Task Tracker
## Autonomous SLAM Robot

---

## Phase 1: OS & ROS 2 Installation
- [ ] Flash Ubuntu 22.04 Server (64-bit) to SD card (ROS 2 Humble requires Ubuntu 22.04)
- [ ] Enable SSH, set hostname, configure Wi-Fi + Ethernet
- [ ] Boot Pi and connect via `ssh rasp-pi` (192.168.216.90)
- [ ] Run `sudo apt update && sudo apt upgrade -y`
- [ ] Set locale: `sudo locale-gen en_US en_US.UTF-8 && sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8`
- [ ] Add ROS 2 apt repository and GPG key
- [ ] Install ROS 2 Humble: `sudo apt install ros-humble-desktop`
- [ ] Source setup: `echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc`
- [ ] Install colcon: `sudo apt install python3-colcon-common-extensions`
- [ ] Install rosdep: `sudo apt install python3-rosdep2 && rosdep update`
- [ ] Verify: `ros2 topic list` (should show `/rosout`, `/parameter_events`)
- [ ] Install python3-dotenv: `pip3 install python-dotenv`

## Phase 2: RPLidar A1 Setup
- [ ] Connect RPLidar A1 via USB
- [ ] Check device: `ls /dev/ttyUSB*` (expect `/dev/ttyUSB0`)
- [ ] Add user to dialout: `sudo usermod -aG dialout $USER` and reboot
- [ ] Install RPLidar ROS 2 driver: `sudo apt install ros-humble-rplidar-ros`
- [ ] Create udev rule for persistent `/dev/rplidar` name
- [ ] Write `99-slam-robot.rules` → `SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", SYMLINK+="rplidar"`
- [ ] Apply: `sudo udevadm control --reload-rules && sudo udevadm trigger`
- [ ] Test: `ros2 launch rplidar_ros rplidar_a1_launch.py serial_port:=/dev/rplidar`
- [ ] Verify `/scan` topic: `ros2 topic echo /scan --once`
- [ ] Verify scan in RViz2 (from desktop): `rviz2` → Add LaserScan → topic `/scan`

## Phase 3: Motor Driver & Odometry
- [ ] Wire L298N motor driver to Pi GPIO pins (per wiring diagram)
- [ ] Wire DC motor encoders to Pi GPIO pins
- [ ] Connect 12V battery to L298N power input
- [ ] Install GPIO library: `sudo apt install python3-lgpio` or `pip3 install RPi.GPIO pigpio`
- [ ] Create ROS 2 workspace: `mkdir -p ~/slam_robot/slam_robot_ws/src`
- [ ] Create `slam_robot_driver` package: `ros2 pkg create --build-type ament_python slam_robot_driver`
- [ ] Implement `motor_driver.py` — low-level L298N GPIO + PWM control
- [ ] Implement `encoder.py` — wheel encoder tick counting (interrupt-driven)
- [ ] Implement `motor_driver_node.py` — ROS 2 node: subscribes `/cmd_vel`, publishes `/odom`
- [ ] Implement differential drive kinematics (encoder ticks → odometry)
- [ ] Implement motor watchdog (stop if no `/cmd_vel` for 500ms)
- [ ] Build: `cd ~/slam_robot/slam_robot_ws && colcon build --packages-select slam_robot_driver`
- [ ] Test: `ros2 run slam_robot_driver motor_driver_node`
- [ ] Verify `/odom` with: `ros2 topic echo /odom`
- [ ] Test `/cmd_vel`: `ros2 topic pub /cmd_vel geometry_msgs/Twist '{linear: {x: 0.1}}'`
- [ ] Verify motors spin and robot moves forward
- [ ] Calibrate encoder ticks per revolution (physical measurement)
- [ ] Calibrate wheel diameter and wheelbase (physical measurement)

## Phase 4: Robot URDF & TF Tree
- [ ] Create URDF file with base_link, laser, left_wheel, right_wheel, caster
- [ ] Set laser frame offset (RPLidar mounting height and orientation)
- [ ] Install robot_state_publisher: `sudo apt install ros-humble-robot-state-publisher`
- [ ] Add `robot_state_publisher` to launch file
- [ ] Verify TF tree: `ros2 run tf2_tools view_frames`
- [ ] Confirm tree: map → odom → base_link → laser

## Phase 5: SLAM (slam_toolbox)
- [ ] Install slam_toolbox: `sudo apt install ros-humble-slam-toolbox`
- [ ] Create `slam_toolbox_params.yaml` config file
- [ ] Set resolution, range, mode (online_async) from `.env` values
- [ ] Create `slam.launch.py` — launches slam_toolbox with params
- [ ] Launch: `ros2 launch slam_robot_bringup slam.launch.py`
- [ ] Drive robot around room using teleop_twist_keyboard
- [ ] Verify `/map` topic updates: `ros2 topic echo /map --once`
- [ ] Visualize map in RViz2 (desktop): Add OccupancyGrid → `/map`
- [ ] Verify map quality — walls should be straight, no ghosting
- [ ] Save map: `ros2 run nav2_map_server map_saver_cli -f maps/floor1`
- [ ] Verify saved files: `floor1.pgm` + `floor1.yaml`
- [ ] Test localization-only mode with saved map

## Phase 6: Nav2 Autonomous Navigation
- [ ] Install Nav2: `sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup`
- [ ] Create `nav2_params.yaml` with planner, controller, costmap config
- [ ] Configure costmap layers (static, obstacle, inflation)
- [ ] Set robot radius, inflation radius, velocity limits from `.env`
- [ ] Create `nav2.launch.py` — launches full Nav2 stack with params
- [ ] Launch Nav2 with saved map: `ros2 launch slam_robot_bringup nav2.launch.py map:=maps/floor1.yaml`
- [ ] Set initial pose in RViz2: 2D Pose Estimate tool
- [ ] Send goal in RViz2: 2D Nav Goal tool
- [ ] Verify robot navigates autonomously to goal
- [ ] Test obstacle avoidance — place objects in path
- [ ] Test recovery behaviors — put robot in tight space
- [ ] Verify costmap updates with live lidar data
- [ ] Test goal cancellation: `ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose --cancel`

## Phase 7: Web Teleoperation (rosbridge + roslibjs)
- [ ] Install rosbridge: `sudo apt install ros-humble-rosbridge-suite`
- [ ] Test rosbridge: `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`
- [ ] Verify WebSocket: `ws://192.168.216.90:9090` accessible from browser
- [ ] Create `slam_robot_web` package for static web files
- [ ] Implement `index.html` — dark theme main page layout
- [ ] Implement `style.css` — dark theme CSS (background: #1a1a2e, accent: #0f3460)
- [ ] Download `roslibjs`, `ros2djs`/`nav2djs`, `nipplejs` (CDN or local)
- [ ] Implement `app.js` — ROSLIB.Ros connection, topic subscriptions
- [ ] Implement `teleop.js` — nipplejs joystick → `/cmd_vel` Twist messages
- [ ] Implement `map_view.js` — subscribe to `/map`, render occupancy grid on canvas
- [ ] Implement `nav_goals.js` — click on map → publish `PoseStamped` to `/goal_pose`
- [ ] Create `web_interface.launch.py` — rosbridge + Python HTTP server
- [ ] Build and launch: `ros2 launch slam_robot_web web_interface.launch.py`
- [ ] Open `http://192.168.216.90:8080` in browser
- [ ] Test joystick — robot should move
- [ ] Test live map — should see occupancy grid updating
- [ ] Test click-to-goal — click on map, robot navigates
- [ ] Add robot position marker on map (from `/tf`)
- [ ] Add connection status indicator (WebSocket connected/disconnected)

## Phase 8: Custom Messages & Services
- [ ] Create `slam_robot_msgs` package (ament_cmake)
- [ ] Define `BatteryState.msg`
- [ ] Define `DockStatus.msg`
- [ ] Define `DetectedObject.msg`
- [ ] Define `SaveMap.srv`
- [ ] Define `LoadMap.srv`
- [ ] Define `SwitchFloor.srv`
- [ ] Define `StartDocking.srv`
- [ ] Add message/service dependencies to `CMakeLists.txt` and `package.xml`
- [ ] Build: `colcon build --packages-select slam_robot_msgs`
- [ ] Verify: `ros2 interface show slam_robot_msgs/msg/BatteryState`

## Phase 9: Ultrasonic Sensors (ENABLE_ULTRASONIC=true)
- [ ] Wire HC-SR04 sensors to Pi GPIO (with voltage divider on Echo: 5V → 3.3V)
- [ ] Create `slam_robot_sensors` package
- [ ] Implement `ultrasonic_node.py` — trigger/echo GPIO, publishes `sensor_msgs/Range`
- [ ] Publish on `/range/front_left` and `/range/front_right`
- [ ] Add ultrasonic as observation source in Nav2 costmap config
- [ ] Implement emergency stop distance (≤10cm → zero `/cmd_vel`)
- [ ] Test: `ros2 topic echo /range/front_left`
- [ ] Verify obstacles below lidar plane are detected
- [ ] Add range circles overlay to web UI map

## Phase 10: IR Cliff Sensors (ENABLE_IR_CLIFF=true)
- [ ] Wire IR cliff sensors to Pi GPIO
- [ ] Implement `ir_sensor_node.py` — GPIO digital read, publishes `std_msgs/Bool`
- [ ] Publish on `/cliff/left` and `/cliff/right`
- [ ] Implement emergency stop on cliff detection (overrides all motion)
- [ ] Test: place robot at table edge, verify motors stop
- [ ] Add cliff alert to web UI

## Phase 11: Battery Monitoring (ENABLE_BATTERY_MONITOR=true)
- [ ] Wire ADS1115 ADC via I2C (SDA/SCL)
- [ ] Wire voltage divider from 12V battery to ADS1115 A0 input
- [ ] Install library: `pip3 install adafruit-circuitpython-ads1x15`
- [ ] Verify I2C: `i2cdetect -y 1` (expect 0x48)
- [ ] Implement `battery_monitor_node.py` — reads ADC, publishes `BatteryState.msg`
- [ ] Calibrate voltage divider ratio with multimeter
- [ ] Test: `ros2 topic echo /battery_state`
- [ ] Implement `battery_widget.js` — battery percentage + bar on web UI
- [ ] Add low battery warning indicator (yellow < 30%, red < 15%)

## Phase 12: Docking Station (ENABLE_DOCKING=true)
- [ ] Connect Pi Camera via CSI ribbon cable
- [ ] Verify camera: `libcamera-hello`
- [ ] Install AprilTag library: `pip3 install dt-apriltags`
- [ ] Print AprilTag (tag36h11, ID 0) and mount at docking station
- [ ] Implement `apriltag_dock_node.py` — camera capture + tag detection + pose estimation
- [ ] Publish tag pose on `/dock/tag_pose`
- [ ] Implement `docking_controller_node.py` — proportional approach controller
- [ ] Approach: navigate near dock → slow approach → final alignment
- [ ] Implement `/start_docking` service
- [ ] Test docking: `ros2 service call /start_docking slam_robot_msgs/srv/StartDocking "{force: true}"`
- [ ] Verify robot aligns and contacts dock
- [ ] Publish `DockStatus.msg` on `/dock/status`
- [ ] Add dock status to web UI

## Phase 13: Auto-Dock on Low Battery (ENABLE_AUTO_DOCK=true)
- [ ] Implement `auto_dock_node.py` — subscribes `/battery_state`, triggers docking
- [ ] When battery < BATTERY_LOW_THRESHOLD → cancel current Nav2 goal
- [ ] Navigate to dock position (DOCK_MAP_X/Y/YAW) using Nav2
- [ ] Initiate AprilTag docking approach
- [ ] When battery ≤ BATTERY_CRITICAL_THRESHOLD → emergency stop all motion
- [ ] Test: lower threshold temporarily, verify auto-dock triggers
- [ ] Add auto-dock status to web UI

## Phase 14: Object Detection on Map (ENABLE_OBJECT_DETECTION=true)
- [ ] Install TFLite: `pip3 install tflite-runtime`
- [ ] Download SSD MobileNet model: `wget` TFLite model from TF Hub
- [ ] Implement `detection_node.py` — camera frame → TFLite inference → detected objects
- [ ] Project detections onto SLAM map using TF tree (camera_link → map)
- [ ] Publish `DetectedObject.msg` on `/detected_objects`
- [ ] Implement `detection_overlay.js` — object markers on web UI map
- [ ] Configure detection classes and threshold via `.env`
- [ ] Test: place objects, verify markers appear on map
- [ ] Limit detection rate to control CPU usage (default 2 Hz)

## Phase 15: Multi-Floor Mapping (ENABLE_MULTI_FLOOR=true)
- [ ] Implement `SaveMap` service wrapper (calls slam_toolbox + map_saver_cli)
- [ ] Implement `LoadMap` service wrapper (calls map_server)
- [ ] Implement `SwitchFloor` service (save current → load target)
- [ ] Store floor metadata in YAML files (floor name, file paths, saved date)
- [ ] Add maps management page to web UI (`/maps`)
- [ ] Test: map floor 1 → save → go to floor 2 → map → save → switch back

## Phase 16: Main Bringup Launch File
- [ ] Create `slam_robot_bringup` package with all launch files
- [ ] Implement `robot_bringup.launch.py` — reads `.env`, conditionally launches all nodes
- [ ] Test with all features enabled
- [ ] Test with minimal features (SLAM + motors only)
- [ ] Test with each feature toggled individually
- [ ] Verify no errors in `ros2 doctor`

## Phase 17: systemd Services
- [ ] Create `/etc/systemd/system/slam-robot.service`
- [ ] Configure: `ExecStart=/bin/bash -c 'source /opt/ros/humble/setup.bash && source ~/slam_robot/slam_robot_ws/install/setup.bash && ros2 launch slam_robot_bringup robot_bringup.launch.py'`
- [ ] Create `/etc/systemd/system/slam-robot-web.service` (if separate from bringup)
- [ ] Enable and start: `sudo systemctl enable --now slam-robot`
- [ ] Verify auto-start on boot
- [ ] Test full power cycle — robot should come up and start SLAM automatically

## Phase 18: Testing & Calibration
- [ ] Run odometry calibration: `bash scripts/calibrate_odom.sh`
- [ ] Drive robot in 1m straight line — verify odometry reads ~1m
- [ ] Drive robot in 360° spin — verify odometry reads ~360°
- [ ] Write unit tests for motor driver (kinematics math)
- [ ] Write unit tests for sensor nodes (range conversion, threshold logic)
- [ ] Write unit tests for battery monitor (voltage → percentage)
- [ ] Write unit tests for docking controller (approach logic)
- [ ] Write unit tests for detection node (TFLite inference)
- [ ] Test mock mode — all nodes publish fake data without hardware
- [ ] Test Nav2 full cycle: SLAM → save map → localization → navigate to 5 goals
- [ ] Test web interface on mobile browser (joystick, map, goals)
- [ ] Run `colcon test` — all tests pass

## Phase 19: Documentation & Deployment
- [ ] Write `docs/wiring_diagram.md` — full pin-by-pin wiring guide
- [ ] Write `docs/assembly_guide.md` — chassis + sensor mounting
- [ ] Write `docs/ros2_cheatsheet.md` — common ROS 2 commands for this robot
- [ ] Write `docs/calibration_guide.md` — odometry + sensor calibration
- [ ] Review and finalize `README.md`
- [ ] Deploy to Pi via `bash deploy/deploy_to_pi.sh`
- [ ] Final smoke test: full autonomous exploration of a room
- [ ] Verify all `.env` toggles work (enable/disable each feature)
