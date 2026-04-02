# ✅ Task List — WiFi Extender & Access Point Manager

## Phase 1: Project Setup & Authentication (Day 1)
- [ ] Initialize Python project with virtual environment
- [ ] Create `requirements.txt` with all dependencies
- [ ] Set up Flask app skeleton with Flask-SocketIO
- [ ] Create `.env.default` template with all variables
- [ ] Implement bcrypt user authentication system
- [ ] Add login rate limiting (10 attempts / 15 min)
- [ ] Implement JWT session management (24h expiry)
- [ ] Create login page (dark theme)
- [ ] Test auth flow with curl / Postman

## Phase 2: hostapd + dnsmasq Auto-Setup (Day 1–2)
- [ ] Install hostapd and dnsmasq system packages
- [ ] Create `hostapd.conf.template` with Jinja2-style placeholders
- [ ] Create `dnsmasq.conf.template` with DHCP range config
- [ ] Implement `setup_ap.py` to generate configs from `.env`
- [ ] Auto-detect WiFi interface (wlan0) and Ethernet (eth0)
- [ ] Configure IP forwarding (`/proc/sys/net/ipv4/ip_forward`)
- [ ] Set up iptables NAT masquerade (eth0 → wlan0)
- [ ] Create `ap_manager.py` for hostapd start/stop/restart
- [ ] Test AP creation and client connection

## Phase 3: Network & IP Forwarding (Day 2)
- [ ] Configure static IP for wlan0 (10.0.0.1)
- [ ] Set up iptables FORWARD rules
- [ ] Save iptables rules to persist on reboot
- [ ] Verify internet access from WiFi clients
- [ ] Test with multiple simultaneous clients

## Phase 4: Database & Client Discovery (Day 2–3)
- [ ] Create SQLite schema with all tables (`init_db.py`)
- [ ] Implement `client_monitor.py` using `iw` and ARP table
- [ ] Parse hostapd station list for signal strength
- [ ] Auto-discover new clients with hostname resolution
- [ ] Log connection/disconnection events
- [ ] Create paginated connection log API
- [ ] Test client discovery with phones and laptops

## Phase 5: Web Dashboard (Day 3)
- [ ] Create `layout.html` base template (dark theme, sidebar nav)
- [ ] Build dashboard page with AP status card
- [ ] Display connected clients count + bandwidth summary
- [ ] Add internet health indicator (green/yellow/red)
- [ ] Create real-time client list with WebSocket updates
- [ ] Add responsive CSS for mobile/tablet
- [ ] Test dashboard from WiFi client browser

## Phase 6: Bandwidth Monitoring (Day 3–4)
- [ ] Implement `bandwidth_tracker.py` using iptables byte counters
- [ ] Create per-client iptables chains for tracking
- [ ] Calculate real-time rx/tx rates (kbps)
- [ ] Store bandwidth readings in SQLite
- [ ] Build bandwidth dashboard page with Chart.js
- [ ] Add per-client bandwidth breakdown
- [ ] Create historical bandwidth charts (24h, 7d, 30d)
- [ ] Test accuracy with speed tests

## Phase 7: SSID & Channel Management (Day 4)
- [ ] Implement SSID change via hostapd config rewrite
- [ ] Add password change with strength validation
- [ ] Add channel change (1-13 for 2.4GHz, 36-165 for 5GHz)
- [ ] Implement `channel_scanner.py` using `iw scan`
- [ ] Auto-select least congested channel
- [ ] Add encryption mode selection (WPA2/WPA3)
- [ ] Build SSID/channel settings UI
- [ ] Test channel scan and auto-selection

## Phase 8: MAC Address Filtering (Day 4–5)
- [ ] Implement `mac_filter.py` with whitelist/blacklist modes
- [ ] Add MAC entries to hostapd accept/deny files
- [ ] Create MAC filter management API endpoints
- [ ] Build MAC filter UI page with add/remove/import
- [ ] Add auto-block on suspicious activity (optional)
- [ ] Reload hostapd on filter change
- [ ] Test blocking and allowing specific devices

## Phase 9: QoS Traffic Shaping (Day 5)
- [ ] Implement `qos_manager.py` using tc (traffic control)
- [ ] Create HTB (Hierarchical Token Bucket) qdisc setup
- [ ] Add per-client bandwidth limits
- [ ] Implement priority levels (1-10)
- [ ] Build QoS configuration UI page
- [ ] Add real-time QoS status display
- [ ] Test speed limits with iperf3

## Phase 10: Captive Portal (Day 5–6)
- [ ] Implement `captive_portal.py` with iptables redirect
- [ ] Create customizable landing page HTML
- [ ] Add terms acceptance flow
- [ ] Add optional password gate
- [ ] Whitelist authenticated clients in iptables
- [ ] Build captive portal preview/editor in dashboard
- [ ] Test portal redirect on new device connection

## Phase 11: WiFi Schedule (Day 6)
- [ ] Implement `wifi_scheduler.py` with APScheduler
- [ ] Add day-of-week + time range configuration
- [ ] Start/stop hostapd on schedule triggers
- [ ] Build visual schedule calendar UI
- [ ] Add override button (force on/off)
- [ ] Test schedule across midnight boundary

## Phase 12: DNS Configuration (Day 6)
- [ ] Implement `dns_manager.py` for dnsmasq config
- [ ] Add custom upstream DNS server selection
- [ ] Add custom local DNS entries
- [ ] Rebuild dnsmasq.conf on change
- [ ] Build DNS settings UI page
- [ ] Test DNS resolution with custom entries

## Phase 13: VPN Passthrough (Day 7)
- [ ] Implement `vpn_passthrough.py` for WireGuard
- [ ] Add OpenVPN support as alternative
- [ ] Route all AP traffic through VPN tunnel
- [ ] Add VPN status monitoring
- [ ] Build VPN settings UI with connect/disconnect
- [ ] Test internet access through VPN tunnel

## Phase 14: Dual-Band Support (Day 7)
- [ ] Detect second WiFi adapter (wlan1)
- [ ] Create second hostapd instance for 5GHz
- [ ] Configure separate SSID and channel
- [ ] Assign DHCP range for second interface
- [ ] Add dual-band status to dashboard
- [ ] Test simultaneous 2.4GHz and 5GHz connections

## Phase 15: Network Health Monitoring (Day 8)
- [ ] Implement `health_monitor.py` with ping + DNS checks
- [ ] Monitor internet latency (ICMP to 1.1.1.1)
- [ ] Monitor packet loss percentage
- [ ] Monitor DNS resolution time
- [ ] Store health checks in SQLite
- [ ] Build health dashboard page with charts
- [ ] Add downtime alerting
- [ ] Test with simulated network interruptions

## Phase 16: Notification System (Day 8)
- [ ] Implement `notification_service.py` dispatcher
- [ ] Add Telegram bot notifications
- [ ] Add Slack webhook notifications
- [ ] Add email (SMTP) notifications
- [ ] Trigger on: new client connect, bandwidth cap, health down
- [ ] Build notification preference settings UI
- [ ] Test all notification channels

## Phase 17: Feature Toggle System (Day 8–9)
- [ ] Create `feature_toggles` database table
- [ ] Implement `feature_toggles.py` service
- [ ] Sync toggle state between `.env` ↔ SQLite
- [ ] Build Settings → Feature Toggles dashboard page
- [ ] Add real-time toggle via WebSocket (`toggle_feature` event)
- [ ] Guard each feature module with toggle check
- [ ] Add `PUT /api/settings/features` API endpoint
- [ ] Test toggling features on/off without restart

## Phase 18: Deployment & Hardening (Day 9)
- [ ] Build `deploy/deploy_to_pi.sh` deployment script
- [ ] Create `deploy/wifi-extender.service` systemd unit
- [ ] Configure auto-start hostapd, dnsmasq, app on boot
- [ ] Generate self-signed TLS certificate script
- [ ] Set file permissions (600 for .env, config files)
- [ ] Add iptables rules persistence across reboots
- [ ] Test full deployment on fresh Raspberry Pi

## Phase 19: Testing & Documentation (Day 9–10)
- [ ] Write unit tests for AP manager and client monitor
- [ ] Write unit tests for bandwidth tracker and MAC filter
- [ ] Write integration tests for API endpoints
- [ ] Test all WebSocket events
- [ ] Test multi-client simultaneous connections
- [ ] Perform security audit (OWASP top 10 checklist)
- [ ] Verify all .env variables load correctly
- [ ] Test feature toggles enable/disable all features
- [ ] Load test with 20 simultaneous clients
- [ ] Final documentation review and cleanup
