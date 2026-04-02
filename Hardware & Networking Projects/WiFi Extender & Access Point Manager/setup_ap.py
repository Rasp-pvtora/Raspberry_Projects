#!/usr/bin/env python3
"""One-time AP setup: configure interfaces, hostapd, dnsmasq, NAT."""

import subprocess
import os
import sys
from dotenv import load_dotenv

# Ensure we can import src modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from src.ap_manager import APManager


def setup():
    interface = os.getenv('AP_INTERFACE', 'wlan0')
    gateway = os.getenv('AP_GATEWAY', '10.0.0.1')

    print(f"Setting up AP on {interface} with gateway {gateway}...")

    # Set static IP on WiFi interface
    subprocess.run(
        ['ip', 'addr', 'add', f'{gateway}/24', 'dev', interface],
        check=False
    )
    subprocess.run(['ip', 'link', 'set', interface, 'up'], check=True)

    # Ensure IP forwarding is persistent
    with open('/etc/sysctl.d/99-wifi-extender.conf', 'w') as f:
        f.write('net.ipv4.ip_forward=1\n')
    subprocess.run(['sysctl', '-p', '/etc/sysctl.d/99-wifi-extender.conf'], check=True)

    # Generate configs and set up NAT
    ap = APManager()
    ap.generate_hostapd_config()
    ap.generate_dnsmasq_config()
    ap.setup_nat()

    # Save iptables rules for persistence
    try:
        result = subprocess.run(
            ['iptables-save'],
            capture_output=True, text=True, check=True
        )
        with open('/etc/iptables/rules.v4', 'w') as f:
            f.write(result.stdout)
        print("iptables rules saved")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Could not save iptables rules (install iptables-persistent)")

    # Enable and start services
    subprocess.run(['systemctl', 'unmask', 'hostapd'], check=False)
    ap.start()

    ssid = os.getenv('AP_SSID', 'RaspberryPi-AP')
    print(f"AP started on {interface} — SSID: {ssid}")
    print(f"Dashboard will be available at http://{gateway}:5000")


if __name__ == '__main__':
    if os.geteuid() != 0:
        print("Error: This script must be run as root (sudo)")
        sys.exit(1)
    setup()
