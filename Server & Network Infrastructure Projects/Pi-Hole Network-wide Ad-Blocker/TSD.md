# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for the **Pi-Hole Network-wide Ad-Blocker** project.

---

## 1. Scope

This project deploys Pi-hole on a Raspberry Pi to act as a DNS sinkhole that blocks advertisements, trackers, and malware domains for every device on the local network. The setup includes a recursive DNS resolver (Unbound) for maximum privacy, optional encrypted DNS forwarding, DHCP server mode for accurate per-device statistics, high availability with two Pi-holes, and long-term monitoring via Grafana and Prometheus.

---

## 2. Minimum Viable Features (MVP)

- **Pi-hole installation and configuration:**
  - Install Pi-hole via the official installer on Raspberry Pi OS Lite.
  - Configure a static IP address for the Pi.
  - Set up the web admin dashboard with a strong password.
  - Configure the router to use the Pi as the primary DNS server for all devices.

- **Unbound recursive DNS resolver:**
  - Install Unbound as a local recursive DNS resolver on port `5335`.
  - Configure Pi-hole to use Unbound as its upstream DNS server.
  - Eliminates dependency on any third-party DNS provider — queries go directly to the authoritative name servers.
  - Enable DNSSEC validation, QNAME minimization, and privacy hardening.
  - Set up a cron job to update the root hints file monthly.

- **Encrypted DNS queries (DNS-over-HTTPS):**
  - Install `cloudflared` as a DNS-over-HTTPS proxy on port `5053`.
  - Configure it to forward to Cloudflare's `1.1.1.1` (or another provider).
  - Provided as an alternative to Unbound for users who prefer encrypted forwarding over full recursion.
  - Prevents the ISP from sniffing DNS traffic.

- **DHCP server mode:**
  - Enable Pi-hole's built-in DHCP server as an alternative to the router's DHCP.
  - Provides accurate per-device query statistics (instead of all queries appearing from the router's IP).
  - Document the risk: if the Pi goes down, new devices cannot obtain IP addresses.

- **Custom blocklists and whitelists:**
  - Document recommended third-party blocklists (Steven Black, OISD, Energized, Firebog).
  - Provide common whitelist entries for services that break with aggressive blocklists.
  - Explain the `pihole -g` gravity update process.

- **High availability (two Pi-holes):**
  - Set up a second Raspberry Pi with Pi-hole at a different static IP.
  - Use Gravity Sync to replicate blocklists, whitelists, and group settings between both Pis.
  - Configure the router with both Pi IPs as primary and secondary DNS for failover.

- **Monitoring with Grafana and Prometheus:**
  - Install Prometheus and the Pi-hole Exporter to collect metrics.
  - Install Grafana (self-hosted, free open-source edition) for visualization.
  - Import a pre-built Pi-hole dashboard for query rates, block percentages, top domains, and trends.
  - All components are free and self-hosted.

---

## 3. Nice-to-Have Features

- **Remote access to the admin dashboard:**
  - Configure HTTPS for the Pi-hole lighttpd web server.
  - Set up a VPN (WireGuard) to securely access the admin panel from outside the home network. Alternatively, use a paid DDNS service for a persistent hostname.

- **Cloud-based DNS analytics:**
  - Forward Grafana dashboards or alerts to a cloud monitoring service (e.g., Grafana Cloud paid tier) for remote visibility.

---

## 4. High-level Architecture

```
   ┌─────────────────────────────────────────────────────────────┐
   │                      Home Network                           │
   │                                                             │
   │  Phone ──┐                                                  │
   │  Laptop ─┤                                                  │
   │  Smart TV┤──── Router ──── Pi-hole (Primary: 192.168.1.100)│
   │  IoT ────┘       │         │                                │
   │                   │         ├── Unbound (127.0.0.1:5335)    │
   │                   │         │      └── Root Name Servers    │
   │                   │         │                                │
   │                   │         └── OR cloudflared (DoH)        │
   │                   │                └── 1.1.1.1 (encrypted)  │
   │                   │                                         │
   │                   └─── Pi-hole (Secondary: 192.168.1.101)   │
   │                         │                                   │
   │                         └── Gravity Sync ◄──► Primary       │
   │                                                             │
   │  Grafana (3000) ◄── Prometheus (9090) ◄── Pi-hole Exporter │
   └─────────────────────────────────────────────────────────────┘
```

**DNS query flow:**

1. A device on the network makes a DNS query (e.g., `ads.example.com`).
2. The router forwards the query to Pi-hole.
3. Pi-hole checks the query against its blocklists.
   - **If blocked:** returns `0.0.0.0` (the ad/tracker is silently dropped).
   - **If allowed:** forwards the query to Unbound (or cloudflared).
4. Unbound resolves the query by contacting the authoritative name servers directly.
5. The response is cached and returned to the device.

---

## 5. Security Considerations

**Primary assets:**
- DNS query log (contains a record of every website every device visits).
- Admin dashboard credentials.
- Network DNS integrity (if Pi-hole is compromised, DNS can be poisoned).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Unauthorized access to admin panel | Strong password; firewall restricting port 80/443 to LAN only |
| DNS spoofing / poisoning | DNSSEC validation via Unbound; DoH via cloudflared |
| ISP snooping on DNS queries | Unbound (direct recursion) or cloudflared (encrypted forwarding) |
| Single point of failure (Pi goes down) | High availability with two Pi-holes and Gravity Sync |
| Query log privacy | Query log is stored locally; protect the Pi physically; restrict SSH access |
| Man-in-the-middle on DNS | DNSSEC; DoH/DoT encrypted upstream queries |
| Stale blocklists | Automatic gravity updates via `pihole -g` (default: weekly cron) |

---

## 6. Suggested Tech Stack

| Tool | Purpose |
|---|---|
| Raspberry Pi OS (Lite) | Operating system (headless) |
| Pi-hole | DNS sinkhole / ad blocker |
| Unbound | Recursive DNS resolver (privacy) |
| `cloudflared` | DNS-over-HTTPS proxy (alternative to Unbound) |
| Gravity Sync | Blocklist replication between Pi-holes |
| Prometheus | Metrics collection |
| Pi-hole Exporter | Exports Pi-hole metrics to Prometheus |
| Grafana (OSS) | Metrics visualization and dashboards |
| `ufw` | Firewall |
| `systemd` | Service management |

---

## 7. Development Phases & Concrete Steps

### Phase A — Base installation (Day 1)

1. Flash Raspberry Pi OS Lite and configure SSH and static IP.
2. Install Pi-hole via the official installer.
3. Configure the router's DNS to point to the Pi.
4. Verify ad blocking works from a client device.
5. Change the admin password.

### Phase B — Privacy-focused DNS (Day 1–2)

1. Install and configure Unbound as a recursive resolver.
2. Download root hints and set up the monthly cron update.
3. Configure Pi-hole to use Unbound (port `5335`).
4. Verify DNS resolution and DNSSEC validation.
5. Alternatively, install and configure cloudflared for DoH.

### Phase C — Enhanced features (Day 2–3)

1. Add recommended third-party blocklists and update gravity.
2. Whitelist commonly broken domains.
3. Enable DHCP server mode (if desired) and disable router DHCP.
4. Verify per-device statistics appear correctly in the dashboard.

### Phase D — High availability (Day 3–4)

1. Set up a second Pi with Pi-hole and a different static IP.
2. Install Gravity Sync on both Pis and configure replication.
3. Set both Pi IPs as DNS on the router for failover.
4. Test failover by shutting down the primary Pi.

### Phase E — Monitoring (Day 4–5)

1. Install Prometheus and Pi-hole Exporter.
2. Install Grafana and add Prometheus as a data source.
3. Import a Pi-hole Grafana dashboard.
4. Verify metrics collection and visualization.

---

## 8. Deliverables

- Working Pi-hole installation blocking ads for the entire network.
- Unbound recursive DNS resolver (or cloudflared DoH proxy).
- DHCP server mode documented and configurable.
- Custom blocklists and whitelists configured.
- High availability setup with two Pi-holes and Gravity Sync.
- Grafana + Prometheus monitoring stack.
- `README.md` with full setup guide.
- `TSD.md` (this document).

---

## 9. Open Questions

- Do you prefer Unbound (full recursion, maximum privacy) or cloudflared (encrypted forwarding to Cloudflare)?
- Do you want Pi-hole to handle DHCP, or should the router keep that role?
- Do you have a second Raspberry Pi for the high availability setup?
- How aggressive should the blocklists be? Some lists break streaming services and social media.
