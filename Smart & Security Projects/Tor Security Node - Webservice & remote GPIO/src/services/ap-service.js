const { exec, execSync } = require('child_process');
const os = require('os');

const AP_INTERFACE = process.env.AP_INTERFACE || 'wlan0';
const AP_SSID = process.env.AP_SSID || 'TorSecurityNode';
const AP_PASSPHRASE = process.env.AP_PASSPHRASE || 'changeme123';
const AP_SUBNET = process.env.AP_SUBNET || '10.3.141';
const UPSTREAM = process.env.AP_UPSTREAM_INTERFACE || 'eth0';
const TOR_TRANSPORT = process.env.TOR_TRANSPORT_PORT || '9040';
const TOR_DNS = process.env.TOR_DNS_PORT || '5353';
const CAPTIVE_PORTAL_ENABLED = (process.env.CAPTIVE_PORTAL_ENABLED || 'true') === 'true';
const DASHBOARD_PORT = parseInt(process.env.PORT, 10) || 3000;

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

    // Add captive portal iptables rules if enabled
    if (CAPTIVE_PORTAL_ENABLED) {
      // Insert captive portal rules BEFORE the Tor rules
      // Allow traffic to the dashboard port to pass through
      commands.splice(5, 0,
        `sudo iptables -t nat -A PREROUTING -i ${AP_INTERFACE} -p tcp --dport 80 -d ${AP_SUBNET}.1 -j ACCEPT`,
        `sudo iptables -t nat -A PREROUTING -i ${AP_INTERFACE} -p tcp --dport ${DASHBOARD_PORT} -j ACCEPT`,
        // Redirect HTTP (port 80) to the dashboard for captive portal detection
        `sudo iptables -t nat -A PREROUTING -i ${AP_INTERFACE} -p tcp --dport 80 ! -d ${AP_SUBNET}.1 -j DNAT --to-destination ${AP_SUBNET}.1:${DASHBOARD_PORT}`
      );
    }

    runCommandsSequentially(commands)
      .then(() => resolve({ success: true, message: 'Tor Access Point started' + (CAPTIVE_PORTAL_ENABLED ? ' (captive portal enabled)' : '') }))
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
  stopAP,
  scanUsbWifiAdapters,
  getWifiNetworks,
  startTravelMode,
  stopTravelMode,
  getTravelModeStatus
};

/**
 * Scan for USB WiFi adapters connected to the system.
 * Returns an array of detected USB WiFi interfaces.
 */
function scanUsbWifiAdapters() {
  const adapters = [];
  try {
    // List USB devices to find WiFi adapters
    const lsusb = execSync('lsusb 2>/dev/null', { encoding: 'utf8' });
    const usbWifiKeywords = ['wireless', 'wifi', 'wlan', '802.11', 'rtl8', 'mt76', 'ath9k', 'ralink'];

    for (const line of lsusb.split('\n')) {
      const lower = line.toLowerCase();
      if (usbWifiKeywords.some(kw => lower.includes(kw))) {
        adapters.push({ raw: line.trim(), type: 'usb-wifi' });
      }
    }
  } catch (_) { /* lsusb not available */ }

  // Check which network interfaces are USB WiFi (exclude built-in wlan0)
  const interfaces = [];
  try {
    const iwOutput = execSync('iw dev 2>/dev/null', { encoding: 'utf8' });
    const ifaceRegex = /Interface\s+(\S+)/g;
    let match;
    while ((match = ifaceRegex.exec(iwOutput)) !== null) {
      const iface = match[1];
      // Check if interface is USB-based by checking /sys/class/net/<iface>/device
      try {
        const devPath = execSync(`readlink -f /sys/class/net/${iface}/device 2>/dev/null`, { encoding: 'utf8' }).trim();
        const isUsb = devPath.includes('/usb');
        interfaces.push({ interface: iface, usb: isUsb, path: devPath });
      } catch (_) {
        interfaces.push({ interface: iface, usb: false, path: '' });
      }
    }
  } catch (_) { /* iw not available */ }

  // Fallback: check /sys/class/net for wlan interfaces
  if (interfaces.length === 0) {
    const netInterfaces = os.networkInterfaces();
    for (const name of Object.keys(netInterfaces)) {
      if (name.startsWith('wlan') || name.startsWith('wlx')) {
        interfaces.push({ interface: name, usb: name !== 'wlan0', path: '' });
      }
    }
  }

  return {
    usbDevices: adapters,
    wifiInterfaces: interfaces,
    usbWifiInterfaces: interfaces.filter(i => i.usb),
    available: interfaces.filter(i => i.usb).length > 0
  };
}

/**
 * Scan available WiFi networks using a specific interface.
 */
function getWifiNetworks(iface) {
  return new Promise((resolve, reject) => {
    const scanIface = iface || 'wlan0';
    exec(`sudo iwlist ${scanIface} scan 2>/dev/null | grep -E '(ESSID|Signal level|Encryption)'`,
      { encoding: 'utf8', timeout: 15000 },
      (err, stdout) => {
        if (err) return resolve([]);

        const networks = [];
        const lines = stdout.split('\n').map(l => l.trim()).filter(Boolean);
        let current = {};

        for (const line of lines) {
          if (line.includes('ESSID:')) {
            if (current.ssid) networks.push(current);
            const ssid = line.match(/ESSID:"(.*)"/);
            current = { ssid: ssid ? ssid[1] : '', signal: '', encrypted: false };
          }
          if (line.includes('Signal level')) {
            const sig = line.match(/Signal level[=:]?\s*(-?\d+)/);
            current.signal = sig ? sig[1] + ' dBm' : '';
          }
          if (line.includes('Encryption key:on')) {
            current.encrypted = true;
          }
        }
        if (current.ssid) networks.push(current);

        // De-duplicate by SSID
        const unique = [];
        const seen = new Set();
        for (const n of networks) {
          if (n.ssid && !seen.has(n.ssid)) {
            seen.add(n.ssid);
            unique.push(n);
          }
        }
        resolve(unique);
      });
  });
}

/**
 * Travel mode: connect USB WiFi to an upstream WiFi network,
 * then share it through the built-in wlan0 as a Tor AP.
 */
function startTravelMode(usbInterface, ssid, password) {
  return new Promise((resolve, reject) => {
    if (!usbInterface || !ssid) {
      return reject(new Error('USB interface and SSID are required'));
    }

    // Generate wpa_supplicant config for the upstream WiFi
    const wpaConf = `/tmp/travel_wpa_${usbInterface}.conf`;
    let wpaContent = `ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\ncountry=US\n\nnetwork={\n  ssid="${ssid}"\n`;
    if (password) {
      wpaContent += `  psk="${password}"\n  key_mgmt=WPA-PSK\n`;
    } else {
      wpaContent += `  key_mgmt=NONE\n`;
    }
    wpaContent += `}\n`;

    const commands = [
      // Write wpa_supplicant config
      `echo '${wpaContent}' | sudo tee ${wpaConf}`,
      // Kill any existing wpa_supplicant on the USB interface
      `sudo wpa_cli -i ${usbInterface} terminate 2>/dev/null || true`,
      // Connect to upstream WiFi via USB adapter
      `sudo wpa_supplicant -B -i ${usbInterface} -c ${wpaConf}`,
      // Get IP via DHCP on the USB interface
      `sudo dhclient ${usbInterface} -timeout 15 2>/dev/null || sudo dhcpcd ${usbInterface} 2>/dev/null || true`,
      // Now start the AP on the built-in interface, using USB as upstream
      `echo '${generateHostapdConf()}' | sudo tee /etc/hostapd/hostapd.conf`,
      `echo '${generateDnsmasqConf()}' | sudo tee /etc/dnsmasq.d/tor-ap.conf`,
      `sudo ip addr flush dev ${AP_INTERFACE} 2>/dev/null; sudo ip addr add ${AP_SUBNET}.1/24 dev ${AP_INTERFACE}`,
      `sudo sysctl -w net.ipv4.ip_forward=1`,
      `sudo iptables -t nat -F PREROUTING`,
      `sudo iptables -t nat -A PREROUTING -i ${AP_INTERFACE} -p udp --dport 53 -j REDIRECT --to-ports ${TOR_DNS}`,
      `sudo iptables -t nat -A PREROUTING -i ${AP_INTERFACE} -p tcp --dport 53 -j REDIRECT --to-ports ${TOR_DNS}`,
      `sudo iptables -t nat -A PREROUTING -i ${AP_INTERFACE} -p tcp --syn -j REDIRECT --to-ports ${TOR_TRANSPORT}`,
      `sudo systemctl restart dnsmasq`,
      `sudo systemctl restart hostapd`,
      `sudo systemctl restart tor`
    ];

    runCommandsSequentially(commands)
      .then(() => resolve({
        success: true,
        message: `Travel mode started: ${usbInterface} → ${ssid} → ${AP_INTERFACE} (Tor AP)`
      }))
      .catch((err) => reject(err));
  });
}

/**
 * Stop travel mode and disconnect the USB WiFi adapter.
 */
function stopTravelMode(usbInterface) {
  return new Promise((resolve, reject) => {
    const commands = [
      `sudo systemctl stop hostapd`,
      `sudo systemctl stop dnsmasq`,
      `sudo iptables -t nat -F PREROUTING`,
      `sudo ip addr flush dev ${AP_INTERFACE} 2>/dev/null`,
      `sudo wpa_cli -i ${usbInterface || 'wlan1'} terminate 2>/dev/null || true`,
      `sudo dhclient -r ${usbInterface || 'wlan1'} 2>/dev/null || true`
    ];

    runCommandsSequentially(commands)
      .then(() => resolve({ success: true, message: 'Travel mode stopped' }))
      .catch((err) => reject(err));
  });
}

/**
 * Check travel mode status.
 */
function getTravelModeStatus() {
  const scan = scanUsbWifiAdapters();
  let upstreamConnected = false;
  let upstreamSSID = '';

  // Check if any USB WiFi interface has an IP (i.e. connected to upstream)
  for (const usbIf of scan.usbWifiInterfaces) {
    try {
      const ipOut = execSync(`ip -4 addr show ${usbIf.interface} 2>/dev/null`, { encoding: 'utf8' });
      if (ipOut.includes('inet ')) {
        upstreamConnected = true;
        // Try to get SSID
        try {
          const iwOut = execSync(`iwgetid ${usbIf.interface} -r 2>/dev/null`, { encoding: 'utf8' }).trim();
          if (iwOut) upstreamSSID = iwOut;
        } catch (_) {}
        break;
      }
    } catch (_) {}
  }

  return {
    available: scan.available,
    usbAdapters: scan.usbWifiInterfaces.length,
    upstreamConnected,
    upstreamSSID,
    apActive: isActive('hostapd') && isActive('dnsmasq')
  };
}
