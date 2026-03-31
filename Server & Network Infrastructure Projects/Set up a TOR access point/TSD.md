# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for the **Set up a TOR Access Point** project.

---

## 1. Scope

This project configures a Raspberry Pi as a WiFi access point that transparently routes all connected client traffic through the Tor network. Any device that connects to the hotspot gets automatic Tor anonymization without needing to install any software. The setup includes DNS leak prevention, MAC address randomization, a physical GPIO toggle switch, travel router mode (WiFi-to-WiFi), and bandwidth monitoring.

---

## 2. Minimum Viable Features (MVP)

- **WiFi access point with hostapd:**
  - Configure the Pi's built-in WiFi radio (`wlan0`) as a WPA2-secured hotspot using `hostapd`.
  - Assign a static IP (`10.3.141.1/24`) to the `wlan0` interface.
  - Upstream internet connection via Ethernet (`eth0`).

- **DHCP server with dnsmasq:**
  - Provide IP addresses to connected clients in the `10.3.141.50–150` range.
  - Forward DNS queries to Tor's DNS port (`5353`).

- **Tor transparent proxy:**
  - Install and configure Tor with `TransPort` (port 9040) and `DNSPort` (port 5353).
  - Use `iptables` to transparently redirect all TCP traffic from `wlan0` clients to Tor's TransPort.
  - Redirect all DNS queries to Tor's DNS resolver.
  - Block UDP traffic (except DNS) since Tor only supports TCP.

- **DNS leak prevention:**
  - Redirect all DNS queries (UDP and TCP port 53) from clients to Tor's DNS port.
  - Drop any DNS packets that somehow bypass the PREROUTING redirect.
  - Verify with check.torproject.org and dnsleaktest.com.

- **MAC address randomization:**
  - Install `macchanger` and create a systemd service that randomizes the Pi's upstream MAC address (`eth0`) on every boot.
  - Prevents the Pi's hardware identity from being exposed on the upstream network.

- **Captive portal / splash page:**
  - Install Nginx on the AP interface to serve a welcome page.
  - Inform users they are on the Tor network, set expectations about speed and limitations.
  - Basic HTML page — no authentication or session tracking.

- **Physical toggle switch (GPIO):**
  - Wire a push button to GPIO 17.
  - Python script using `gpiozero` toggles between Tor routing (all traffic via Tor) and normal routing (standard NAT masquerade).
  - Run as a systemd service on boot.
  - Allows instant switching between anonymous and normal mode without SSH.

- **Travel router mode (WiFi-to-WiFi):**
  - Use a USB WiFi adapter (`wlan1`) to connect to an upstream WiFi network (hotel, café).
  - The built-in radio (`wlan0`) continues serving the access point.
  - Configure `wpa_supplicant` for `wlan1` with upstream credentials.
  - Update iptables to work without Ethernet (all traffic routes through Tor regardless of upstream interface).

- **Bandwidth monitoring:**
  - Install `vnstat` for lightweight traffic monitoring.
  - Provide commands for real-time, daily, and monthly traffic statistics per interface.

- **Automatic Tor updates:**
  - Enable `unattended-upgrades` for automatic security patches.
  - Optionally add the official Tor project APT repository for the latest stable releases.

---

## 3. Nice-to-Have Features

- **Tor Bridge / obfs4 obfuscation:**
  - Configure Tor to use bridge relays with obfs4 pluggable transports to bypass Tor censorship in restrictive networks (e.g., countries that block Tor). Requires obtaining bridge addresses from the Tor Project (free but manual process).

- **Web-based management panel:**
  - A lightweight web interface (e.g., Flask or Node.js) to manage the AP settings, view Tor status, toggle routing modes, and monitor bandwidth — without needing SSH.

- **VPN fallback:**
  - If Tor performance is unacceptable, offer a mode that routes traffic through a VPN (WireGuard/OpenVPN) instead. Requires a paid VPN subscription.

- **Multi-hop Tor + VPN:**
  - Route traffic through VPN first, then Tor (Tor over VPN) for users who want their ISP to not even see Tor usage. Requires a paid VPN provider.

---

## 4. High-level Architecture

```
   Client Devices (Phone, Laptop, Tablet)
         │
         │  WiFi (WPA2)
         ▼
   ┌──────────────────────────────────────────┐
   │  wlan0 (10.3.141.1) — Access Point       │
   │        │                                  │
   │        ▼                                  │
   │  dnsmasq (DHCP: 10.3.141.50–150)         │
   │        │                                  │
   │        ▼                                  │
   │  iptables (PREROUTING)                    │
   │  ├── UDP:53 → REDIRECT → Tor DNS (5353)  │
   │  └── TCP:*  → REDIRECT → TransPort (9040)│
   │        │                                  │
   │        ▼                                  │
   │  Tor Daemon                               │
   │  ├── TransPort 9040 (transparent TCP)     │
   │  └── DNSPort 5353 (DNS over Tor)          │
   │        │                                  │
   │        ▼                                  │
   │  eth0 / wlan1 (upstream internet)         │
   │  (MAC randomized via macchanger)          │
   └──────────────────────────────────────────┘
         │
         ▼
   Tor Network (3 relays) → Exit Node → Internet
```

**Toggle switch modes:**

| Mode | Behavior |
|---|---|
| **Tor ON** (default) | All TCP → Tor TransPort. All DNS → Tor DNS. UDP blocked. |
| **Tor OFF** (toggle) | Standard NAT masquerade. Traffic flows directly to the internet. |

---

## 5. Security and Threat Model

**Primary assets:**
- Client traffic privacy (IP address, browsing activity).
- Pi identity on the upstream network (MAC, IP).
- Access point security (WiFi credentials).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| DNS leaks (real DNS queries bypass Tor) | iptables redirects all DNS to Tor; DROP rules for any bypassed DNS |
| UDP leaks | All UDP except DNS is blocked; Tor only supports TCP |
| MAC address fingerprinting on upstream | `macchanger` randomizes eth0/wlan1 MAC on every boot |
| Weak WiFi password gives unauthorized access | Enforce WPA2 with a strong 12+ character passphrase |
| Tor exit node sniffing HTTP traffic | User responsibility: always use HTTPS. Tor provides anonymity, not encryption |
| Traffic correlation attacks | Operational security; do not generate identifying traffic alongside Tor usage |
| Physical access to the Pi | Physical security; consider full-disk encryption for high-threat scenarios |
| Tor blocked by upstream network | Use Tor bridges with obfs4 transports (nice-to-have) |
| Stale Tor version with vulnerabilities | Automatic updates via `unattended-upgrades` |

**Operational guidance:**
- Verify Tor is working after every configuration change using check.torproject.org.
- Do not use the Pi simultaneously for non-Tor activities that could link your identity.
- In travel mode, connect to upstream WiFi before clients connect to the AP.

---

## 6. Suggested Tech Stack

| Tool | Purpose |
|---|---|
| Raspberry Pi OS (Lite) | Operating system (headless) |
| `hostapd` | WiFi access point daemon |
| `dnsmasq` | DHCP server and DNS forwarder |
| `tor` | Tor daemon (TransPort + DNSPort) |
| `iptables` / `iptables-persistent` | Transparent proxying and firewall |
| `macchanger` | MAC address randomization |
| `nginx` | Captive portal / splash page |
| `python3` + `gpiozero` | GPIO toggle switch script |
| `vnstat` | Bandwidth monitoring |
| `unattended-upgrades` | Automatic security updates |
| `wpa_supplicant` | Upstream WiFi connection (travel mode) |

---

## 7. Development Phases & Concrete Steps

### Phase A — Base access point (Day 1)

1. Flash Raspberry Pi OS Lite and enable SSH.
2. Connect to the internet via Ethernet.
3. Install `hostapd`, `dnsmasq`, and `tor`.
4. Configure a static IP on `wlan0`.
5. Set up `hostapd` with WPA2 security.
6. Configure `dnsmasq` for DHCP on the AP subnet.
7. Verify a device can connect to the WiFi hotspot and get an IP.

### Phase B — Tor transparent proxy (Day 1–2)

1. Configure Tor with `TransPort` and `DNSPort`.
2. Enable IP forwarding.
3. Set up iptables rules for transparent proxying.
4. Redirect DNS to Tor's DNS port.
5. Block UDP except DNS.
6. Save iptables rules with `netfilter-persistent`.
7. Test: verify check.torproject.org confirms Tor usage.
8. Test: verify dnsleaktest.com shows no DNS leaks.

### Phase C — Hardening and enhancements (Day 2–3)

1. Install and configure `macchanger` with systemd service.
2. Add extra iptables rules for DNS leak prevention.
3. Set up the Nginx captive portal splash page.
4. Wire the GPIO toggle button and deploy the Python script.
5. Create the systemd service for the toggle script.
6. Test toggle between Tor and normal routing.

### Phase D — Travel mode and monitoring (Day 3–4)

1. Plug in a USB WiFi adapter and verify detection.
2. Configure `wpa_supplicant` for `wlan1` (upstream WiFi).
3. Update iptables for WiFi-to-WiFi mode.
4. Test travel mode with a phone as a client.
5. Install and configure `vnstat` for bandwidth monitoring.
6. Enable `unattended-upgrades` and configure Tor APT repo.

### Phase E — Documentation and testing

1. Document all steps in README.md.
2. Test the complete setup from a fresh Pi.
3. Verify all features work together (Tor, toggle, travel mode, monitoring).

---

## 8. Deliverables

- Working Tor access point routing all client traffic through Tor.
- DNS leak prevention with verified iptables rules.
- MAC address randomization on upstream interface.
- Captive portal splash page.
- Physical GPIO toggle switch for Tor on/off.
- Travel router mode (WiFi-to-WiFi).
- vnStat bandwidth monitoring.
- Automatic Tor updates.
- `README.md` with full setup guide.
- `TSD.md` (this document).

---

## 9. Open Questions

- Which USB WiFi adapter do you plan to use for travel mode? Compatibility varies.
- Do you need Tor bridge/obfs4 support for censored networks?
- Should the AP be hidden (not broadcasting SSID) for stealth?
- Do you want a web-based management panel, or is SSH sufficient?
