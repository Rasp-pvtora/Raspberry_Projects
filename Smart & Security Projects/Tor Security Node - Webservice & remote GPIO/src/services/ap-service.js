const { exec, execSync } = require('child_process');

const AP_INTERFACE = process.env.AP_INTERFACE || 'wlan0';
const AP_SSID = process.env.AP_SSID || 'TorSecurityNode';
const AP_PASSPHRASE = process.env.AP_PASSPHRASE || 'changeme123';
const AP_SUBNET = process.env.AP_SUBNET || '10.3.141';
const UPSTREAM = process.env.AP_UPSTREAM_INTERFACE || 'eth0';
const TOR_TRANSPORT = process.env.TOR_TRANSPORT_PORT || '9040';
const TOR_DNS = process.env.TOR_DNS_PORT || '5353';

/**
 * Get current state of the Tor access point.
 */
function getAPStatus() {
  const hostapdActive = isActive('hostapd');
  const dnsmasqActive = isActive('dnsmasq');
  const torActive = isActive('tor');

  let connectedClients = 0;
  try {
    const output = execSync(`arp -i ${AP_INTERFACE} 2>/dev/null | grep -v incomplete | tail -n +2 | wc -l`, { encoding: 'utf8' });
    connectedClients = parseInt(output.trim(), 10) || 0;
  } catch (_) { /* not available */ }

  return {
    active: hostapdActive && dnsmasqActive && torActive,
    hostapd: hostapdActive,
    dnsmasq: dnsmasqActive,
    tor: torActive,
    ssid: AP_SSID,
    interface: AP_INTERFACE,
    subnet: AP_SUBNET,
    upstream: UPSTREAM,
    connectedClients
  };
}

function isActive(service) {
  try {
    return execSync(`systemctl is-active ${service} 2>/dev/null`, { encoding: 'utf8' }).trim() === 'active';
  } catch (_) {
    return false;
  }
}

/**
 * Generate hostapd.conf content.
 */
function generateHostapdConf() {
  return `interface=${AP_INTERFACE}
driver=nl80211
ssid=${AP_SSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=${AP_PASSPHRASE}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
`;
}

/**
 * Generate dnsmasq.conf content for the AP.
 */
function generateDnsmasqConf() {
  return `interface=${AP_INTERFACE}
listen-address=${AP_SUBNET}.1
dhcp-range=${AP_SUBNET}.50,${AP_SUBNET}.150,12h
bind-interfaces
server=127.0.0.1#${TOR_DNS}
log-queries
log-dhcp
`;
}

/**
 * Write configuration files and start the access point.
 */
function startAP() {
  return new Promise((resolve, reject) => {
    const commands = [
      // Write hostapd config
      `echo '${generateHostapdConf()}' | sudo tee /etc/hostapd/hostapd.conf`,
      // Write dnsmasq config
      `echo '${generateDnsmasqConf()}' | sudo tee /etc/dnsmasq.d/tor-ap.conf`,
      // Set static IP on AP interface
      `sudo ip addr flush dev ${AP_INTERFACE} 2>/dev/null; sudo ip addr add ${AP_SUBNET}.1/24 dev ${AP_INTERFACE}`,
      // Enable IP forwarding
      `sudo sysctl -w net.ipv4.ip_forward=1`,
      // Flush and set iptables for Tor transparent proxy
      `sudo iptables -t nat -F PREROUTING`,
      `sudo iptables -t nat -A PREROUTING -i ${AP_INTERFACE} -p udp --dport 53 -j REDIRECT --to-ports ${TOR_DNS}`,
      `sudo iptables -t nat -A PREROUTING -i ${AP_INTERFACE} -p tcp --dport 53 -j REDIRECT --to-ports ${TOR_DNS}`,
      `sudo iptables -t nat -A PREROUTING -i ${AP_INTERFACE} -p tcp --syn -j REDIRECT --to-ports ${TOR_TRANSPORT}`,
      // Start services
      `sudo systemctl restart dnsmasq`,
      `sudo systemctl restart hostapd`,
      `sudo systemctl restart tor`
    ];

    runCommandsSequentially(commands)
      .then(() => resolve({ success: true, message: 'Tor Access Point started' }))
      .catch((err) => reject(err));
  });
}

/**
 * Stop the access point and clean up.
 */
function stopAP() {
  return new Promise((resolve, reject) => {
    const commands = [
      `sudo systemctl stop hostapd`,
      `sudo systemctl stop dnsmasq`,
      // Flush Tor iptables rules
      `sudo iptables -t nat -F PREROUTING`,
      // Remove static IP
      `sudo ip addr flush dev ${AP_INTERFACE} 2>/dev/null`
    ];

    runCommandsSequentially(commands)
      .then(() => resolve({ success: true, message: 'Tor Access Point stopped' }))
      .catch((err) => reject(err));
  });
}

/**
 * Run shell commands one after another.
 */
function runCommandsSequentially(commands) {
  return commands.reduce((promise, cmd) => {
    return promise.then(() => {
      return new Promise((resolve, reject) => {
        exec(cmd, (err) => {
          // Don't reject on non-critical errors
          resolve();
        });
      });
    });
  }, Promise.resolve());
}

module.exports = {
  getAPStatus,
  startAP,
  stopAP
};
