# Pi-Hole Network-wide Ad-Blocker

Turn a Raspberry Pi into a DNS-based ad blocker for the entire network. Blocks ads, trackers, and malware domains for every device — phones, tablets, smart TVs, and IoT devices — without installing software on each one. Includes Unbound recursive DNS, encrypted DNS queries, high availability, and Grafana monitoring.

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Quickstart — Install Pi-hole](#quickstart--install-pi-hole)
4. [Configure your router to use Pi-hole](#configure-your-router-to-use-pi-hole)
5. [Pi-hole admin dashboard](#pi-hole-admin-dashboard)
6. [Set up Unbound as recursive DNS](#set-up-unbound-as-recursive-dns)
7. [Encrypt DNS queries (DNS-over-HTTPS)](#encrypt-dns-queries-dns-over-https)
8. [DHCP server mode](#dhcp-server-mode)
9. [Custom blocklists and whitelists](#custom-blocklists-and-whitelists)
10. [High availability with two Pi-holes](#high-availability-with-two-pi-holes)
11. [Monitoring with Grafana and Prometheus](#monitoring-with-grafana-and-prometheus)
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
| Raspberry Pi 3B+ / 4 / 5 / Zero 2W | Yes | Even a Pi Zero 2W handles DNS for a home network |
| microSD card (8 GB+) | Yes | For the OS |
| Ethernet cable | Recommended | More reliable than WiFi for a DNS server |
| Power supply (official) | Yes | 5V 2.5A+ |
| Second Raspberry Pi | Optional | For high availability setup |

---

## Quickstart — Install Pi-hole

**1. Flash Raspberry Pi OS Lite and enable SSH**

Use Raspberry Pi Imager to flash the OS. Enable SSH in the imager settings.

**2. Update the system**

```bash
sudo apt update && sudo apt upgrade -y
```

**3. Set a static IP address**

Edit `/etc/dhcpcd.conf`:

```bash
sudo nano /etc/dhcpcd.conf
```

Add (adjust for your network):

```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=127.0.0.1
```

Reboot:

```bash
sudo reboot
```

**4. Install Pi-hole**

```bash
curl -sSL https://install.pi-hole.net | bash
```

Follow the interactive installer:
- Select your network interface (`eth0` recommended).
- Choose an upstream DNS provider (will be replaced by Unbound later).
- Accept the default blocklist.
- Install the web admin interface.
- **Note the admin password** displayed at the end.

**5. Set a new admin password**

```bash
pihole -a -p
```

**6. Verify Pi-hole is running**

Open a browser and navigate to:

```
http://192.168.1.100/admin
```

---

## Configure your router to use Pi-hole

For Pi-hole to block ads network-wide, all devices must use it as their DNS server.

**Option A — Change DNS on the router (recommended)**

1. Log in to your router's admin panel.
2. Find the DHCP / DNS settings.
3. Set the **Primary DNS** to the Pi's IP (e.g., `192.168.1.100`).
4. Remove or leave blank the Secondary DNS (or point it to a second Pi-hole — see [High availability](#high-availability-with-two-pi-holes)).
5. Renew DHCP leases on client devices (reconnect to WiFi or reboot).

> **Important:** If you set a secondary DNS to a non-Pi-hole server (e.g., `8.8.8.8`), devices may bypass Pi-hole for some queries.

**Option B — Configure individual devices**

Set each device's DNS server to the Pi's IP manually. This is less convenient but useful if you cannot change the router settings.

---

## Pi-hole admin dashboard

The web dashboard at `http://<pi-ip>/admin` shows:

- **Total queries** — how many DNS queries have been processed.
- **Queries blocked** — number and percentage of blocked queries.
- **Blocklist size** — total number of domains on your blocklists.
- **Top blocked domains** — which ad/tracking domains are hit most.
- **Top clients** — which devices make the most queries.
- **Query log** — real-time log of all DNS queries with allow/block status.

Use the dashboard to:
- Whitelist domains that are incorrectly blocked.
- Blacklist specific domains.
- View long-term statistics.
- Manage group-based filtering.

---

## Set up Unbound as recursive DNS

Instead of forwarding queries to a third-party DNS provider (Google, Cloudflare), run your own recursive resolver. This means **no external company sees your DNS queries**.

**1. Install Unbound**

```bash
sudo apt install unbound -y
```

**2. Download the root hints file**

```bash
sudo wget -O /var/lib/unbound/root.hints https://www.internic.net/domain/named.root
```

Set up a monthly cron job to keep it updated:

```bash
sudo crontab -e
```

Add:

```
0 3 1 * * wget -O /var/lib/unbound/root.hints https://www.internic.net/domain/named.root && systemctl restart unbound
```

**3. Configure Unbound**

```bash
sudo nano /etc/unbound/unbound.conf.d/pi-hole.conf
```

Paste:

```yaml
server:
    verbosity: 0

    interface: 127.0.0.1
    port: 5335
    do-ip4: yes
    do-udp: yes
    do-tcp: yes
    do-ip6: no

    # Security
    harden-glue: yes
    harden-dnssec-stripped: yes
    use-caps-for-id: no
    edns-buffer-size: 1232
    prefetch: yes
    num-threads: 1

    # Privacy
    hide-identity: yes
    hide-version: yes
    minimal-responses: yes
    qname-minimisation: yes

    # Access control
    access-control: 127.0.0.0/8 allow
    access-control: 0.0.0.0/0 refuse

    # Cache
    cache-min-ttl: 3600
    cache-max-ttl: 86400

    private-address: 192.168.0.0/16
    private-address: 172.16.0.0/12
    private-address: 10.0.0.0/8
```

**4. Restart and test Unbound**

```bash
sudo systemctl restart unbound
dig google.com @127.0.0.1 -p 5335
```

You should see a valid DNS response.

**5. Configure Pi-hole to use Unbound**

In the Pi-hole admin dashboard:
1. Go to **Settings → DNS**.
2. Uncheck all upstream DNS servers.
3. In **Custom 1 (IPv4)**, enter: `127.0.0.1#5335`
4. Save.

Pi-hole now uses Unbound as its upstream resolver. No third-party DNS provider is involved.

---

## Encrypt DNS queries (DNS-over-HTTPS)

If you prefer to use an upstream provider (instead of Unbound), encrypt your queries so your ISP cannot snoop on them.

**1. Install cloudflared**

```bash
# Download for ARM
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
sudo mv cloudflared-linux-arm64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
```

**2. Configure cloudflared as a DNS proxy**

```bash
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

Paste:

```yaml
proxy-dns: true
proxy-dns-port: 5053
proxy-dns-upstream:
  - https://1.1.1.1/dns-query
  - https://1.0.0.1/dns-query
```

**3. Create a systemd service**

```bash
sudo nano /etc/systemd/system/cloudflared.service
```

Paste:

```ini
[Unit]
Description=cloudflared DNS over HTTPS proxy
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/cloudflared --config /etc/cloudflared/config.yml
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

**4. Configure Pi-hole to use cloudflared**

In Pi-hole admin → **Settings → DNS**:
- Uncheck all upstream servers.
- Set **Custom 1 (IPv4)** to `127.0.0.1#5053`.

> **Note:** Choose either Unbound OR cloudflared — not both. Unbound gives you full independence (no third party). Cloudflared gives you encrypted forwarding to Cloudflare.

---

## DHCP server mode

Let Pi-hole handle DHCP instead of your router. This gives Pi-hole accurate per-device statistics (instead of all queries appearing from the router's IP).

**1. Disable DHCP on your router**

Log in to your router's admin panel and disable the built-in DHCP server.

**2. Enable DHCP in Pi-hole**

In the Pi-hole admin dashboard:
1. Go to **Settings → DHCP**.
2. Enable **DHCP server**.
3. Set the IP range (e.g., `192.168.1.50` to `192.168.1.200`).
4. Set the Gateway IP (your router: `192.168.1.1`).
5. Save.

**3. Renew leases on all devices**

Reconnect devices to the network or reboot them. They will now get their IP and DNS from Pi-hole.

> **Warning:** If the Pi goes down while it is the DHCP server, devices will not be able to get new IP addresses. Consider the high availability setup below.

---

## Custom blocklists and whitelists

**Recommended blocklists:**

Add these in **Group Management → Adlists**:

| List | URL |
|---|---|
| Steven Black Unified | `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts` |
| OISD (Full) | `https://big.oisd.nl/` |
| Energized Basic | `https://energized.pro/basic/formats/hosts` |
| Firebog Tick List | `https://v.firebog.nl/hosts/lists.php?type=tick` (multiple lists) |

After adding lists, update gravity:

```bash
pihole -g
```

**Common whitelist entries:**

Some blocklists may break legitimate services. Whitelist these if needed:

```bash
pihole -w s.youtube.com
pihole -w video-stats.l.google.com
pihole -w connectivitycheck.gstatic.com
pihole -w clients4.google.com
pihole -w clients2.google.com
```

---

## High availability with two Pi-holes

Run two Pis with Pi-hole so ad blocking continues if one Pi fails.

**1. Set up a second Pi with Pi-hole**

Repeat the [Quickstart](#quickstart--install-pi-hole) on a second Raspberry Pi with a different static IP (e.g., `192.168.1.101`).

**2. Sync blocklists with Gravity Sync**

Install [Gravity Sync](https://github.com/vmstan/gravity-sync) on both Pis:

```bash
curl -sSL https://raw.githubusercontent.com/vmstan/gravity-sync/master/deploy.sh | bash
```

Follow the configuration wizard to connect the two Pis. Gravity Sync replicates blocklists, whitelists, blacklists, and group settings.

**3. Configure your router**

Set **both** Pi IPs as DNS servers on your router:
- **Primary DNS:** `192.168.1.100`
- **Secondary DNS:** `192.168.1.101`

If the primary Pi goes down, the router automatically uses the secondary.

---

## Monitoring with Grafana and Prometheus

For detailed long-term analytics beyond the built-in Pi-hole dashboard.

**1. Install Prometheus**

```bash
sudo apt install prometheus -y
```

**2. Install the Pi-hole Exporter**

```bash
# Using Docker (recommended)
docker run -d \
    --name pihole-exporter \
    -p 9617:9617 \
    -e PIHOLE_HOSTNAME=127.0.0.1 \
    -e PIHOLE_API_TOKEN=<your-pihole-api-token> \
    ekofr/pihole-exporter

# Or install from source:
# https://github.com/eko/pihole-exporter
```

Get the API token from Pi-hole admin → **Settings → API → Show API token**.

**3. Configure Prometheus to scrape the exporter**

```bash
sudo nano /etc/prometheus/prometheus.yml
```

Add to `scrape_configs`:

```yaml
  - job_name: 'pihole'
    static_configs:
      - targets: ['127.0.0.1:9617']
```

```bash
sudo systemctl restart prometheus
```

**4. Install Grafana**

```bash
sudo apt install -y adduser libfontconfig1
wget https://dl.grafana.com/oss/release/grafana_10.4.0_arm64.deb
sudo dpkg -i grafana_10.4.0_arm64.deb
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

Access Grafana at `http://<pi-ip>:3000` (default: `admin` / `admin`).

**5. Add Prometheus as a data source in Grafana**

1. Go to **Configuration → Data Sources → Add → Prometheus**.
2. Set URL to `http://127.0.0.1:9090`.
3. Save & Test.

**6. Import a Pi-hole dashboard**

1. Go to **Dashboards → Import**.
2. Enter dashboard ID `10176` (or search for "Pi-hole" on Grafana.com).
3. Select the Prometheus data source.
4. Click Import.

You now have a beautiful dashboard with query rates, block percentages, top domains, and historical trends.

---

## Security notes

- **Set a strong admin password** for the Pi-hole web interface.
- **Use a static IP** so the Pi's address does not change and break DNS resolution.
- **Keep Pi-hole updated:**
  ```bash
  pihole -up
  ```
- **Firewall:** Allow only DNS (53) and HTTP (80) for the admin panel. Block access to the admin panel from outside the LAN.
  ```bash
  sudo ufw allow 22/tcp
  sudo ufw allow 53
  sudo ufw allow 80/tcp
  sudo ufw enable
  ```
- **HTTPS for the admin panel:** Pi-hole supports HTTPS via lighttpd; configure it if accessing the dashboard remotely.
- If using Unbound, **DNSSEC validation** is enabled by default (`harden-dnssec-stripped: yes`), protecting against DNS spoofing.
- The Pi-hole query log contains a record of every website visited by every device on your network. **Protect it accordingly.**

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Ads still appearing after setup | Clear browser cache; check that the device is using the Pi's IP for DNS: `nslookup google.com` |
| A website is broken | Whitelist the blocked domain: `pihole -w domain.com`. Check the query log to find which domain is blocked. |
| Pi-hole dashboard shows all queries from router IP | Enable Pi-hole DHCP mode (see [DHCP server mode](#dhcp-server-mode)) or configure the router to send individual client addresses. |
| Unbound fails to start | Check config syntax: `unbound-checkconf`. Check logs: `journalctl -u unbound -e`. |
| DNS resolution stops after Pi reboot | Verify static IP configuration. Check Pi-hole and Unbound services: `pihole status`, `systemctl status unbound`. |
| Gravity update fails | Check internet connectivity. Run `pihole -g` manually and check for errors. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- [Pi-hole Documentation](https://docs.pi-hole.net/) — official Pi-hole docs.
- [Unbound Documentation](https://unbound.docs.nlnetlabs.nl/) — Unbound configuration reference.
- [Pi-hole Discourse](https://discourse.pi-hole.net/) — community forum for questions and discussion.
