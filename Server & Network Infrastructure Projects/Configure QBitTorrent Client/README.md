# Configure QBitTorrent Client

A headless qBittorrent setup on Raspberry Pi with a web interface for remote torrent management, VPN integration, automated media organization, and external storage support. Turns the Pi into a low-power, always-on download machine.

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Quickstart — Install qBittorrent-nox](#quickstart--install-qbittorrent-nox)
4. [Configure the Web UI](#configure-the-web-ui)
5. [Set up as a systemd service](#set-up-as-a-systemd-service)
6. [Mount external storage](#mount-external-storage)
7. [Secure the Web UI with HTTPS (Nginx reverse proxy)](#secure-the-web-ui-with-https-nginx-reverse-proxy)
8. [RSS feed automation](#rss-feed-automation)
9. [Bandwidth scheduling](#bandwidth-scheduling)
10. [Automatic media organization (Sonarr / Radarr / Prowlarr)](#automatic-media-organization-sonarr--radarr--prowlarr)
11. [VPN kill-switch (nice-to-have)](#vpn-kill-switch-nice-to-have)
12. [Security notes](#security-notes)
13. [Troubleshooting](#troubleshooting)
14. [Where to next](#where-to-next)

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
| Raspberry Pi 3B+ / 4 / 5 | Yes | Pi 4 (2 GB+) recommended for best performance |
| microSD card (16 GB+) | Yes | For the OS |
| USB HDD or SSD | Recommended | For torrent downloads (avoids wearing out the SD card) |
| Ethernet cable | Recommended | More stable than WiFi for always-on downloading |
| Power supply (official) | Yes | 5V 3A for Pi 4/5 |

---

## Quickstart — Install qBittorrent-nox

**1. Update the system**

```bash
sudo apt update && sudo apt upgrade -y
```

**2. Install qBittorrent-nox (headless, no GUI)**

```bash
sudo apt install qbittorrent-nox -y
```

**3. Create a dedicated user (security best practice)**

```bash
sudo adduser --system --group --no-create-home qbtuser
sudo mkdir -p /home/qbtuser/Downloads
sudo chown qbtuser:qbtuser /home/qbtuser/Downloads
```

**4. Start qBittorrent-nox for first-time setup**

```bash
sudo -u qbtuser qbittorrent-nox
```

Accept the legal notice when prompted, then press `Ctrl+C` to stop.

**5. Verify the Web UI is accessible**

Open a browser on any device on the same network and navigate to:

```
http://<raspberry-pi-ip>:8080
```

Default credentials:
- **Username:** `admin`
- **Password:** `adminadmin`

> **Important:** Change the default password immediately after first login.

---

## Configure the Web UI

**1. Change the default admin password**

Go to **Tools → Options → Web UI** and set a strong password.

**2. Configure download paths**

Go to **Tools → Options → Downloads**:
- Set **Default Save Path** to your external storage mount (e.g., `/mnt/external/downloads`)
- Optionally set a **Temp path** for incomplete downloads

**3. Set connection limits**

Go to **Tools → Options → Connection**:
- **Global maximum number of connections:** `200` (adjust based on your network)
- **Maximum number of connections per torrent:** `50`
- **Global maximum upload slots:** `20`

**4. Configure seeding ratios**

Go to **Tools → Options → BitTorrent**:
- **When ratio reaches:** `2.0` (seed to 2x the downloaded amount)
- **Then:** Pause torrent (or remove)

**5. Set the listening port**

Go to **Tools → Options → Connection**:
- Set a port (e.g., `6881`) and configure port forwarding on your router for best connectivity
- Enable **UPnP / NAT-PMP** if your router supports it

---

## Set up as a systemd service

Create a service file so qBittorrent starts automatically on boot.

**1. Create the service file**

```bash
sudo nano /etc/systemd/system/qbittorrent-nox.service
```

Paste:

```ini
[Unit]
Description=qBittorrent-nox Daemon
Documentation=man:qbittorrent-nox(1)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=qbtuser
Group=qbtuser
ExecStart=/usr/bin/qbittorrent-nox --webui-port=8080
Restart=on-failure
RestartSec=5
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

**2. Enable and start the service**

```bash
sudo systemctl daemon-reload
sudo systemctl enable qbittorrent-nox
sudo systemctl start qbittorrent-nox
```

**3. Verify it is running**

```bash
sudo systemctl status qbittorrent-nox
```

---

## Mount external storage

Downloading to the microSD card will wear it out quickly. Use a USB drive instead.

**1. Identify the drive**

```bash
lsblk
```

Look for your USB drive (e.g., `/dev/sda1`).

**2. Create a mount point**

```bash
sudo mkdir -p /mnt/external
```

**3. Format the drive (if needed — WARNING: erases all data)**

```bash
sudo mkfs.ext4 /dev/sda1
```

**4. Mount the drive**

```bash
sudo mount /dev/sda1 /mnt/external
```

**5. Set ownership**

```bash
sudo chown -R qbtuser:qbtuser /mnt/external
```

**6. Auto-mount on boot via fstab**

Get the UUID:

```bash
sudo blkid /dev/sda1
```

Edit `/etc/fstab`:

```bash
sudo nano /etc/fstab
```

Add this line (replace the UUID with yours):

```
UUID=your-uuid-here  /mnt/external  ext4  defaults,nofail  0  2
```

**7. Test the fstab entry**

```bash
sudo mount -a
```

**8. Update qBittorrent download path**

In the Web UI, change the default save path to `/mnt/external/downloads`.

---

## Secure the Web UI with HTTPS (Nginx reverse proxy)

By default, qBittorrent's Web UI sends credentials in plaintext over HTTP. Add a reverse proxy with TLS.

**1. Install Nginx**

```bash
sudo apt install nginx -y
```

**2. Generate a self-signed certificate**

```bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/qbt.key \
    -out /etc/nginx/ssl/qbt.crt \
    -subj "/CN=qbittorrent"
```

**3. Create the Nginx configuration**

```bash
sudo nano /etc/nginx/sites-available/qbittorrent
```

Paste:

```nginx
server {
    listen 443 ssl;
    server_name _;

    ssl_certificate     /etc/nginx/ssl/qbt.crt;
    ssl_certificate_key /etc/nginx/ssl/qbt.key;

    location / {
        proxy_pass         http://127.0.0.1:8080;
        proxy_set_header   Host               $host;
        proxy_set_header   X-Real-IP          $remote_addr;
        proxy_set_header   X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto  $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";
    }
}
```

**4. Enable the site and restart Nginx**

```bash
sudo ln -s /etc/nginx/sites-available/qbittorrent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**5. Optional — Disable direct HTTP access**

Bind qBittorrent to localhost only so it is accessible only through the Nginx proxy. Edit the qBittorrent config:

```bash
sudo -u qbtuser nano /home/qbtuser/.config/qBittorrent/qBittorrent.conf
```

Set:

```ini
WebUI\Address=127.0.0.1
```

Restart the service:

```bash
sudo systemctl restart qbittorrent-nox
```

Now access the Web UI at `https://<raspberry-pi-ip>`.

---

## RSS feed automation

qBittorrent has a built-in RSS downloader to automatically fetch new torrents.

**1. Enable RSS in the Web UI**

Go to **Tools → Options → RSS**:
- Enable **RSS Reader**
- Set **RSS refresh interval** (e.g., every 30 minutes)

**2. Add RSS feeds**

In the Web UI, go to the **RSS** tab and click **New subscription**. Paste the feed URL.

**3. Create download rules**

Go to **RSS → RSS Downloader**:
- Click **New Rule**
- Set a **filter** (e.g., a show name, quality like `1080p`)
- Assign it to a specific feed
- Set the save path

qBittorrent will now automatically download matching torrents as they appear in the feed.

---

## Bandwidth scheduling

Limit download speeds during the day so other devices are not affected, and use full speed at night.

**1. Enable alternative speed limits**

Go to **Tools → Options → Speed**:
- Set **Alternative upload/download rate limits** (e.g., 1 MB/s down, 256 KB/s up)

**2. Schedule the limits**

In the same section:
- Enable **Schedule the use of alternative rate limits**
- Set the schedule (e.g., active from `08:00` to `23:00` on weekdays)
- Outside the schedule, full speed is used

---

## Automatic media organization (Sonarr / Radarr / Prowlarr)

For automated TV and movie downloading with proper naming and library organization.

**1. Install Prowlarr (indexer manager)**

Prowlarr manages torrent indexers and connects them to Sonarr and Radarr.

```bash
# Follow the official Prowlarr installation guide for Linux:
# https://wiki.servarr.com/prowlarr/installation/linux
wget --content-disposition 'https://prowlarr.servarr.com/v1/update/master/updatefile?os=linux&runtime=netcore&arch=arm64'
tar -xvzf Prowlarr*.linux*.tar.gz
sudo mv Prowlarr /opt/
```

Create a systemd service for Prowlarr (similar pattern to qBittorrent).

**2. Install Sonarr (TV shows)**

```bash
# Follow the official Sonarr installation guide:
# https://wiki.servarr.com/sonarr/installation/linux
```

Access at `http://<pi-ip>:8989`.

**3. Install Radarr (movies)**

```bash
# Follow the official Radarr installation guide:
# https://wiki.servarr.com/radarr/installation/linux
```

Access at `http://<pi-ip>:7878`.

**4. Connect the tools**

- In Prowlarr: add your preferred indexers and connect Sonarr/Radarr as applications.
- In Sonarr/Radarr: add qBittorrent as a **Download Client** (Settings → Download Clients → Add → qBittorrent). Use `127.0.0.1:8080` with your qBittorrent credentials.
- Set media root folders on your external storage (e.g., `/mnt/external/tv`, `/mnt/external/movies`).

---

## VPN kill-switch (nice-to-have)

> **Note:** This feature requires a VPN subscription from a third-party provider (e.g., Mullvad, ProtonVPN, NordVPN). WireGuard and OpenVPN are free and open-source, but the VPN service itself is typically a paid subscription.

Route all torrent traffic through a VPN so your ISP cannot see what you are downloading. If the VPN drops, the kill-switch blocks all traffic to prevent leaks.

**1. Install WireGuard**

```bash
sudo apt install wireguard -y
```

**2. Import your VPN provider's configuration**

Copy the `.conf` file from your VPN provider:

```bash
sudo cp your-vpn.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
```

**3. Start the VPN**

```bash
sudo wg-quick up wg0
```

**4. Verify the VPN is active**

```bash
curl https://ifconfig.me
```

The IP should be the VPN server's IP, not your home IP.

**5. Enable on boot**

```bash
sudo systemctl enable wg-quick@wg0
```

**6. Configure the kill-switch with iptables**

Block all traffic that does not go through the VPN tunnel:

```bash
# Allow loopback
sudo iptables -A OUTPUT -o lo -j ACCEPT
# Allow traffic to VPN server
sudo iptables -A OUTPUT -d <vpn-server-ip> -j ACCEPT
# Allow traffic through the VPN tunnel
sudo iptables -A OUTPUT -o wg0 -j ACCEPT
# Allow LAN access (for Web UI)
sudo iptables -A OUTPUT -d 192.168.0.0/16 -j ACCEPT
# Block everything else
sudo iptables -A OUTPUT -j DROP
```

**7. Persist iptables rules**

```bash
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

**8. Bind qBittorrent to the VPN interface**

In the qBittorrent Web UI, go to **Tools → Options → Advanced**:
- Set **Network Interface** to `wg0`

---

## Security notes

- **Change the default Web UI password immediately** after installation. Use a strong, unique password.
- **Run qBittorrent as a dedicated user** (`qbtuser`) with no sudo privileges. Never run it as root.
- **Use HTTPS** for the Web UI via the Nginx reverse proxy to protect credentials on the network.
- **External storage permissions**: ensure only the `qbtuser` has write access to the download directory.
- **Keep the system updated**: run `sudo apt update && sudo apt upgrade` regularly.
- **Firewall**: consider enabling `ufw` and allowing only the necessary ports (SSH, Web UI HTTPS, torrent listening port).

```bash
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 443/tcp       # HTTPS Web UI
sudo ufw allow 6881/tcp      # qBittorrent listening port
sudo ufw enable
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Web UI not accessible | Check if the service is running: `sudo systemctl status qbittorrent-nox`. Verify the Pi's IP and port 8080 are reachable. |
| Permission denied on download folder | Run `sudo chown -R qbtuser:qbtuser /mnt/external/downloads` |
| Slow download speeds | Enable port forwarding on your router for the listening port. Check connection limits. |
| SD card wearing out | Move downloads to external USB storage (see [Mount external storage](#mount-external-storage)). |
| VPN drops and torrents leak | Ensure the iptables kill-switch is configured and persistent (see [VPN kill-switch](#vpn-kill-switch-nice-to-have)). |
| Service fails to start after reboot | Check logs: `journalctl -u qbittorrent-nox -e` |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- [qBittorrent Wiki](https://github.com/qbittorrent/qBittorrent/wiki) — official documentation.
- [Servarr Wiki](https://wiki.servarr.com/) — Sonarr, Radarr, Prowlarr documentation.
