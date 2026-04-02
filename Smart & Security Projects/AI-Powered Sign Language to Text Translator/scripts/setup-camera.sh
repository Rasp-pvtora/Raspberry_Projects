#!/usr/bin/env bash
# setup-camera.sh — Enable and configure camera on Raspberry Pi
set -euo pipefail

echo "=== Camera Setup ==="

# Enable camera interface
if command -v raspi-config &>/dev/null; then
    echo "Enabling camera interface..."
    sudo raspi-config nonint do_camera 0
else
    echo "raspi-config not found — skipping interface toggle."
fi

# Install V4L2 utilities
echo "Installing camera dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq libcamera-apps v4l-utils

# Test camera
echo "Testing camera..."
if v4l2-ctl --list-devices 2>/dev/null | grep -q "video"; then
    echo "Camera detected:"
    v4l2-ctl --list-devices
else
    echo "WARNING: No camera detected. Connect a Pi Camera or USB webcam."
fi

# Install OpenGL dependencies for MediaPipe
echo "Installing MediaPipe dependencies..."
sudo apt-get install -y -qq libgl1-mesa-glx libglib2.0-0

echo "=== Camera setup complete ==="
echo "Reboot if you just enabled the camera interface: sudo reboot"
