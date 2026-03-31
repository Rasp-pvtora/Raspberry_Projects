# Set up a TOR Access Point

Configure a Raspberry Pi as a WiFi access point that routes all connected traffic through the Tor network for enhanced anonymity. Any device that connects to this hotspot gets automatic Tor routing — no software installation or configuration needed on the client device. Includes DNS leak prevention, MAC randomization, a physical toggle switch, and travel router mode.

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [How it works](#how-it-works)
4. [Quickstart — Set up the Tor access point](#quickstart--set-up-the-tor-access-point)
5. [Configure hostapd (WiFi hotspot)](#configure-hostapd-wifi-hotspot)
6. [Configure dnsmasq (DHCP server)](#configure-dnsmasq-dhcp-server)
7. [Install and configure Tor](#install-and-configure-tor)
8. [Set up transparent proxying with iptables](#set-up-transparent-proxying-with-iptables)
9. [DNS leak prevention](#dns-leak-prevention)
10. [MAC address randomization](#mac-address-randomization)
11. [Captive portal / splash page](#captive-portal--splash-page)
12. [Physical toggle switch (GPIO)](#physical-toggle-switch-gpio)
13. [Travel router mode (WiFi-to-WiFi)](#travel-router-mode-wifi-to-wifi)
14. [Bandwidth monitoring](#bandwidth-monitoring)
15. [Auto-update Tor](#auto-update-tor)
16. [Security notes](#security-notes)
17. [Troubleshooting](#troubleshooting)
18. [Where to next](#where-to-next)

---

## Project structure

```
.
├── README.md           ← This file
├── TSD.md              ← Technical Specification Description
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 3B+ / 4 / 5 | Yes | Built-in WiFi for the access point |
| microSD card (8 GB+) | Yes | For the OS |
| Ethernet cable | Yes (basic mode) | Upstream internet via Ethernet |
| USB WiFi adapter | Only for travel mode | Second WiFi interface for upstream WiFi connection |
| Power supply (official) | Yes | 5V 3A for Pi 4/5 |
| Push button + jumper wires | Optional | For the physical Tor toggle switch (GPIO) |

---

## How it works

```
                        ┌──────────────────────────┐
   Phone/Laptop ──WiFi──► Raspberry Pi (AP: wlan0)  │
                        │     │                     │
                        │     ▼                     │
                        │  iptables                 │
                        │  (transparent proxy)      │
                        │     │                     │
                        │     ▼                     │
                        │  Tor (SOCKS + TransPort)  │
                        │     │                     │
                        │     ▼                     │
                        │  eth0 (or wlan1) ─────────┼──► Internet
                        └──────────────────────────┘
```

1. The Pi creates a WiFi hotspot using its built-in radio (`wlan0`).
2. Client devices connect to the hotspot and get an IP via `dnsmasq` (DHCP).
3. `iptables` redirects all TCP traffic from clients to Tor's TransPort.
4. DNS queries are redirected to Tor's DNS port.
5. All traffic exits through the Tor network — the client's real IP is hidden.
6. UDP traffic (except DNS) is blocked, since Tor only supports TCP.

---

## Quickstart — Set up the Tor access point

**1. Flash Raspberry Pi OS Lite and enable SSH**

Use Raspberry Pi Imager. Connect the Pi to the internet via Ethernet.

**2. Update the system**

```bash
sudo apt update && sudo apt upgrade -y
```

**3. Install required packages**

```bash
sudo apt install hostapd dnsmasq tor iptables-persistent -y
```

**4. Stop services while configuring**

```bash
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```

---

## Configure hostapd (WiFi hotspot)

**1. Configure the wireless interface**

Assign a static IP to the WiFi interface:

```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:

```
interface wlan0
    static ip_address=10.3.141.1/24
    nohook wpa_supplicant
```

**2. Create the hostapd configuration**

```bash
sudo nano /etc/hostapd/hostapd.conf
```

Paste:

```
interface=wlan0
driver=nl80211
ssid=TorAccessPoint
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=YourStrongPassword
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

> **Important:** Replace `YourStrongPassword` with a strong WiFi passphrase (at least 12 characters).

**3. Point hostapd to the configuration**

```bash
sudo nano /etc/default/hostapd
```

Set:

```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

**4. Unmask and enable hostapd**

```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
```

---

## Configure dnsmasq (DHCP server)

**1. Back up the default config and create a new one**

```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.bak
sudo nano /etc/dnsmasq.conf
```

Paste:

```
interface=wlan0
listen-address=10.3.141.1
dhcp-range=10.3.141.50,10.3.141.150,12h
bind-interfaces
server=127.0.0.1#5353
log-queries
log-dhcp
```

> The DNS server is set to `127.0.0.1#5353`, which will be Tor's DNS port.

**2. Enable dnsmasq**

```bash
sudo systemctl enable dnsmasq
```

---

## Install and configure Tor

**1. Edit the Tor configuration**

```bash
sudo nano /etc/tor/torrc
```

Add these lines:

```
Log notice file /var/log/tor/notices.log
VirtualAddrNetworkIPv4 10.192.0.0/10
AutomapHostsSuffixes .onion,.exit
AutomapHostsOnResolve 1
TransPort 10.3.141.1:9040
DNSPort 10.3.141.1:5353
```

**2. Enable and restart Tor**

```bash
sudo systemctl enable tor
sudo systemctl restart tor
```

---

## Set up transparent proxying with iptables

These rules redirect all traffic from WiFi clients through Tor.

**1. Enable IP forwarding**

```bash
sudo nano /etc/sysctl.conf
```

Uncomment or add:

```
net.ipv4.ip_forward=1
```

Apply:

```bash
sudo sysctl -p
```

**2. Configure iptables rules**

```bash
# Flush existing rules for the nat and filter tables
sudo iptables -t nat -F
sudo iptables -F

# --- NAT table ---
# Redirect DNS queries from wlan0 clients to Tor's DNS port
sudo iptables -t nat -A PREROUTING -i wlan0 -p udp --dport 53 -j REDIRECT --to-ports 5353
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 53 -j REDIRECT --to-ports 5353

# Redirect all TCP traffic from wlan0 clients to Tor's TransPort
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --syn -j REDIRECT --to-ports 9040

# --- Filter table ---
# Allow established connections
sudo iptables -A FORWARD -i wlan0 -o eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT

# Block all other forwarding (no non-Tor traffic leaks)
sudo iptables -A FORWARD -i wlan0 -j DROP

# Block UDP from clients (Tor only supports TCP)
sudo iptables -A INPUT -i wlan0 -p udp --dport 5353 -j ACCEPT
sudo iptables -A INPUT -i wlan0 -p udp -j DROP
```

**3. Save the rules**

```bash
sudo netfilter-persistent save
```

---

## DNS leak prevention

Ensure DNS queries from connected clients **never** bypass Tor.

The iptables rules above already redirect DNS to Tor's DNS port (`5353`). Additional hardening:

**1. Block direct DNS to external servers**

```bash
# Block any DNS that somehow bypasses the PREROUTING redirect
sudo iptables -A FORWARD -i wlan0 -p udp --dport 53 -j DROP
sudo iptables -A FORWARD -i wlan0 -p tcp --dport 53 -j DROP
sudo netfilter-persistent save
```

**2. Verify DNS is Tor-routed**

From a device connected to the hotspot, visit [https://check.torproject.org](https://check.torproject.org). It should say "Congratulations. This browser is configured to use Tor."

Also check DNS:
- Visit [https://dnsleaktest.com](https://dnsleaktest.com) and run the extended test.
- The DNS servers should not be your ISP — they should be Tor exit node resolvers.

---

## MAC address randomization

Randomize the Pi's MAC address on the upstream network (Ethernet or WiFi) so the Pi's hardware identity is not exposed.

**1. Install macchanger**

```bash
sudo apt install macchanger -y
```

During installation, select **No** when asked to change MAC automatically.

**2. Create a systemd service to randomize MAC on boot**

```bash
sudo nano /etc/systemd/system/macchanger.service
```

Paste:

```ini
[Unit]
Description=Randomize MAC address on eth0
Before=network-pre.target
Wants=network-pre.target

[Service]
Type=oneshot
ExecStart=/usr/bin/macchanger -r eth0
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable macchanger
```

**3. Verify on next boot**

```bash
macchanger -s eth0
```

The MAC should be different from the factory MAC.

---

## Captive portal / splash page

Show a welcome page to users when they first connect, warning them that they are on the Tor network.

**1. Install Nginx**

```bash
sudo apt install nginx -y
```

**2. Create the splash page**

```bash
sudo mkdir -p /var/www/splash
sudo nano /var/www/splash/index.html
```

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Tor Access Point</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; background: #1a1a2e; color: #e0e0e0; }
        h1 { color: #7b68ee; }
        .warning { background: #333; padding: 20px; border-radius: 10px; max-width: 600px; margin: 20px auto; }
    </style>
</head>
<body>
    <h1>You are connected to a Tor Access Point</h1>
    <div class="warning">
        <p>All your internet traffic is being routed through the <strong>Tor network</strong>.</p>
        <p><strong>What this means:</strong></p>
        <ul style="text-align: left;">
            <li>Your real IP address is hidden from the websites you visit.</li>
            <li>Internet speeds will be slower than usual.</li>
            <li>Some websites may block Tor exit nodes.</li>
            <li>UDP-based services (gaming, video calls) will not work.</li>
        </ul>
        <p>Use responsibly and in accordance with local laws.</p>
    </div>
</body>
</html>
```

**3. Configure Nginx**

```bash
sudo nano /etc/nginx/sites-available/splash
```

```nginx
server {
    listen 10.3.141.1:80;
    server_name _;

    root /var/www/splash;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/splash /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

> **Note:** This is a simple splash page, not a true captive portal with authentication. Devices will see it when they first try to access an HTTP site. HTTPS sites will not trigger the splash page due to certificate mismatch.

---

## Physical toggle switch (GPIO)

Wire a push button to a GPIO pin to toggle Tor routing on and off instantly.

**1. Wire the button**

Connect a push button between **GPIO 17** (pin 11) and **GND** (pin 9).

**2. Create the toggle script**

```bash
sudo nano /usr/local/bin/tor-toggle.py
```

```python
#!/usr/bin/env python3
"""Toggle Tor routing on/off with a physical GPIO button."""

import subprocess
import time

try:
    from gpiozero import Button
except ImportError:
    print("Install gpiozero: sudo apt install python3-gpiozero")
    raise SystemExit(1)

button = Button(17, bounce_time=0.3)
tor_enabled = True


def toggle_tor():
    global tor_enabled
    if tor_enabled:
        # Disable Tor routing — switch to normal NAT
        subprocess.run(["sudo", "iptables", "-t", "nat", "-F", "PREROUTING"], check=True)
        subprocess.run([
            "sudo", "iptables", "-t", "nat", "-A", "PREROUTING",
            "-i", "wlan0", "-o", "eth0", "-j", "MASQUERADE"
        ], check=False)
        subprocess.run([
            "sudo", "iptables", "-t", "nat", "-A", "POSTROUTING",
            "-o", "eth0", "-j", "MASQUERADE"
        ], check=True)
        subprocess.run(["sudo", "iptables", "-F", "FORWARD"], check=True)
        subprocess.run([
            "sudo", "iptables", "-A", "FORWARD",
            "-i", "wlan0", "-o", "eth0", "-j", "ACCEPT"
        ], check=True)
        subprocess.run([
            "sudo", "iptables", "-A", "FORWARD",
            "-i", "eth0", "-o", "wlan0",
            "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"
        ], check=True)
        print("Tor DISABLED — normal routing active")
        tor_enabled = False
    else:
        # Re-enable Tor routing
        subprocess.run(["sudo", "iptables", "-t", "nat", "-F"], check=True)
        subprocess.run(["sudo", "iptables", "-F", "FORWARD"], check=True)
        subprocess.run([
            "sudo", "iptables", "-t", "nat", "-A", "PREROUTING",
            "-i", "wlan0", "-p", "udp", "--dport", "53",
            "-j", "REDIRECT", "--to-ports", "5353"
        ], check=True)
        subprocess.run([
            "sudo", "iptables", "-t", "nat", "-A", "PREROUTING",
            "-i", "wlan0", "-p", "tcp", "--syn",
            "-j", "REDIRECT", "--to-ports", "9040"
        ], check=True)
        subprocess.run([
            "sudo", "iptables", "-A", "FORWARD", "-i", "wlan0", "-j", "DROP"
        ], check=True)
        print("Tor ENABLED — all traffic routed through Tor")
        tor_enabled = True


button.when_pressed = toggle_tor

print("Tor toggle switch active. Press the button to switch modes.")
while True:
    time.sleep(1)
```

**3. Make it executable and run on boot**

```bash
sudo chmod +x /usr/local/bin/tor-toggle.py
```

Create a systemd service:

```bash
sudo nano /etc/systemd/system/tor-toggle.service
```

```ini
[Unit]
Description=Tor Toggle Switch (GPIO)
After=network.target tor.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/tor-toggle.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable tor-toggle
sudo systemctl start tor-toggle
```

---

## Travel router mode (WiFi-to-WiFi)

Use the Pi as a portable Tor router that connects to upstream WiFi (hotel, café) instead of Ethernet.

**Requirements:** A USB WiFi adapter for the upstream connection (the built-in radio is used for the hotspot).

**1. Plug in the USB WiFi adapter**

Verify it is detected:

```bash
iw dev
```

You should see two wireless interfaces: `wlan0` (built-in) and `wlan1` (USB).

**2. Connect wlan1 to the upstream WiFi**

```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant-wlan1.conf
```

```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={
    ssid="HotelWiFi"
    psk="hotel-password"
}
```

```bash
sudo systemctl enable wpa_supplicant@wlan1
sudo systemctl start wpa_supplicant@wlan1
```

**3. Configure dhcpcd for wlan1**

```bash
sudo nano /etc/dhcpcd.conf
```

Ensure `wlan1` gets a dynamic IP (do NOT assign a static IP):

```
# wlan1 uses DHCP from the upstream network (no static config needed)
```

**4. Update iptables rules**

Replace `eth0` with `wlan1` in all iptables rules. Or make the rules dynamic:

```bash
# Clear existing rules
sudo iptables -t nat -F
sudo iptables -F

# DNS redirect
sudo iptables -t nat -A PREROUTING -i wlan0 -p udp --dport 53 -j REDIRECT --to-ports 5353
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 53 -j REDIRECT --to-ports 5353

# TCP redirect to Tor
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --syn -j REDIRECT --to-ports 9040

# Block forwarding (all traffic goes through Tor, not forwarded)
sudo iptables -A FORWARD -i wlan0 -j DROP

sudo netfilter-persistent save
```

**5. Reboot and test**

Connect a phone to the `TorAccessPoint` WiFi and visit [https://check.torproject.org](https://check.torproject.org).

---

## Bandwidth monitoring

Monitor Tor traffic usage with a lightweight tool.

**1. Install vnStat**

```bash
sudo apt install vnstat -y
```

**2. Start monitoring**

```bash
sudo systemctl enable vnstat
sudo systemctl start vnstat
```

**3. View statistics**

```bash
# Real-time traffic
vnstat -l -i wlan0

# Daily summary
vnstat -d -i wlan0

# Monthly summary
vnstat -m -i wlan0
```

---

## Auto-update Tor

Keep the Tor daemon updated automatically for security patches.

**1. Enable unattended upgrades**

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

**2. Add the Tor project repository (optional, for latest releases)**

```bash
sudo nano /etc/apt/sources.list.d/tor.list
```

Add (for Raspberry Pi OS / Debian):

```
deb [signed-by=/usr/share/keyrings/tor-archive-keyring.gpg] https://deb.torproject.org/torproject.org bookworm main
```

Import the signing key:

```bash
wget -qO- https://deb.torproject.org/torproject.org/A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89.asc | gpg --dearmor | sudo tee /usr/share/keyrings/tor-archive-keyring.gpg > /dev/null
sudo apt update
sudo apt install tor deb.torproject.org-keyring -y
```

The unattended-upgrades system will now automatically apply Tor security updates.

---

## Security notes

- **Use a strong WiFi passphrase** for the access point (WPA2, 12+ characters). Anyone with the passphrase can connect and use your Tor proxy.
- **Tor only routes TCP.** UDP traffic (video calls, gaming, some VoIP) will not work and is blocked by the iptables rules.
- **Tor provides anonymity, not encryption.** If you visit a plain HTTP site, the Tor exit node can see the traffic. Always use HTTPS.
- **Some websites block Tor exit nodes.** This is expected behavior.
- **Speeds will be slower.** Tor routes traffic through multiple relays. Expect 1–10 Mbps depending on the circuit.
- **Do not use this for illegal activities.** Tor is a privacy tool, not an invisibility cloak. Law enforcement has techniques to de-anonymize Tor users who engage in illegal activity.
- **Keep Tor updated.** Security vulnerabilities in Tor can compromise your anonymity. Use automatic updates.
- **DNS leak prevention is critical.** Always verify at [dnsleaktest.com](https://dnsleaktest.com) and [check.torproject.org](https://check.torproject.org).
- **Physical access:** If someone has physical access to the Pi, they can modify the configuration. Secure it physically.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Cannot connect to the WiFi hotspot | Check `sudo systemctl status hostapd`. Verify `wlan0` has IP `10.3.141.1`. |
| Connected but no internet | Check `sudo systemctl status tor`. Verify iptables rules: `sudo iptables -t nat -L`. |
| DNS leak detected | Verify DNS redirect rules are active. Run `sudo iptables -t nat -L PREROUTING`. |
| check.torproject.org says "not using Tor" | Verify TransPort redirect: `sudo iptables -t nat -L PREROUTING`. Check Tor is running on port 9040. |
| Very slow speeds | Normal for Tor. Try restarting Tor for a new circuit: `sudo systemctl restart tor`. |
| hostapd fails to start | Check for `rfkill` blocks: `rfkill list`. Unblock with `rfkill unblock wlan`. |
| USB WiFi adapter not detected (travel mode) | Run `lsusb` to verify. Install firmware: `sudo apt install firmware-ralink` (or appropriate driver). |
| Toggle switch not responding | Check GPIO wiring. Test with `gpio readall` or `pinctrl get 17`. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- [Tor Project](https://www.torproject.org/) — official Tor documentation.
- [hostapd documentation](https://w1.fi/hostapd/) — WiFi access point daemon.
- [Raspberry Pi Networking](https://www.raspberrypi.com/documentation/computers/configuration.html) — official networking docs.
