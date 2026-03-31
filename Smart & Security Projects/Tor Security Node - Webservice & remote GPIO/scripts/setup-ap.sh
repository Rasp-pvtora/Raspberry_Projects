#!/usr/bin/env bash
# =============================================================================
# setup-ap.sh — Install and configure Tor Access Point on Raspberry Pi
# Run with: sudo bash scripts/setup-ap.sh
# =============================================================================
set -euo pipefail

# Configuration (override via environment variables)
AP_INTERFACE="${AP_INTERFACE:-wlan0}"
AP_SSID="${AP_SSID:-TorSecurityNode}"
AP_PASSPHRASE="${AP_PASSPHRASE:-changeme123}"
AP_SUBNET="${AP_SUBNET:-10.3.141}"
UPSTREAM="${AP_UPSTREAM_INTERFACE:-eth0}"
TOR_TRANSPORT="${TOR_TRANSPORT_PORT:-9040}"
TOR_DNS="${TOR_DNS_PORT:-5353}"

echo "=== Tor Access Point Setup ==="

# 1. Install required packages
echo "[1/6] Installing hostapd, dnsmasq, tor..."
apt-get update -qq
apt-get install -y hostapd dnsmasq tor iptables-persistent

# 2. Configure static IP on AP interface
echo "[2/6] Configuring static IP on $AP_INTERFACE..."
if ! grep -q "interface $AP_INTERFACE" /etc/dhcpcd.conf; then
    cat >> /etc/dhcpcd.conf <<EOF

# Tor Access Point — static IP
interface $AP_INTERFACE
    static ip_address=${AP_SUBNET}.1/24
    nohook wpa_supplicant
EOF
fi

# 3. Configure hostapd
echo "[3/6] Configuring hostapd..."
cat > /etc/hostapd/hostapd.conf <<EOF
interface=$AP_INTERFACE
driver=nl80211
ssid=$AP_SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$AP_PASSPHRASE
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd 2>/dev/null || true
systemctl unmask hostapd

# 4. Configure dnsmasq
echo "[4/6] Configuring dnsmasq..."
cat > /etc/dnsmasq.d/tor-ap.conf <<EOF
interface=$AP_INTERFACE
listen-address=${AP_SUBNET}.1
dhcp-range=${AP_SUBNET}.50,${AP_SUBNET}.150,12h
bind-interfaces
server=127.0.0.1#${TOR_DNS}
EOF

# 5. Configure Tor TransPort and DNSPort
echo "[5/6] Configuring Tor transparent proxy..."
MARKER="# --- Tor Security Node Access Point ---"
if ! grep -q "$MARKER" /etc/tor/torrc; then
    cat >> /etc/tor/torrc <<EOF

$MARKER
VirtualAddrNetworkIPv4 10.192.0.0/10
AutomapHostsSuffixes .onion,.exit
AutomapHostsOnResolve 1
TransPort ${AP_SUBNET}.1:${TOR_TRANSPORT}
DNSPort ${AP_SUBNET}.1:${TOR_DNS}
$MARKER END
EOF
fi

# 6. Configure iptables
echo "[6/6] Configuring iptables for transparent Tor proxy..."
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf 2>/dev/null || true

# Flush existing PREROUTING rules
iptables -t nat -F PREROUTING 2>/dev/null || true

# Redirect DNS to Tor
iptables -t nat -A PREROUTING -i "$AP_INTERFACE" -p udp --dport 53 -j REDIRECT --to-ports "$TOR_DNS"
iptables -t nat -A PREROUTING -i "$AP_INTERFACE" -p tcp --dport 53 -j REDIRECT --to-ports "$TOR_DNS"
# Redirect TCP to Tor TransPort
iptables -t nat -A PREROUTING -i "$AP_INTERFACE" -p tcp --syn -j REDIRECT --to-ports "$TOR_TRANSPORT"
# Block UDP leaks
iptables -A FORWARD -i "$AP_INTERFACE" -p udp -j DROP 2>/dev/null || true

# Save rules
netfilter-persistent save

echo ""
echo "=== Setup Complete ==="
echo "Start the access point with:"
echo "  sudo systemctl start hostapd dnsmasq tor"
echo ""
echo "SSID: $AP_SSID"
echo "AP IP: ${AP_SUBNET}.1"
echo ""
