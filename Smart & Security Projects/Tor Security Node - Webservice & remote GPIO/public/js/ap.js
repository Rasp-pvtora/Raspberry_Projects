/**
 * Access Point page — start/stop Tor AP + WiFi-to-WiFi travel mode.
 */
async function loadAPStatus() {
  try {
    const s = await api('/api/ap/status');
    setBadge('ap-active', s.active);
    setBadge('ap-hostapd', s.hostapd);
    setBadge('ap-dnsmasq', s.dnsmasq);
    setBadge('ap-tor', s.tor);
    setText('ap-ssid', s.ssid);
    setText('ap-clients', s.connectedClients);
  } catch (_) {}
}

function setBadge(id, active) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = active ? 'Active' : 'Inactive';
  el.className = 'badge ' + (active ? 'badge-success' : 'badge-danger');
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

async function apAction(action) {
  const msg = document.getElementById('ap-message');
  msg.textContent = 'Processing... this may take a few seconds.';
  msg.className = 'message';
  try {
    const r = await api(`/api/ap/${action}`, { method: 'POST' });
    msg.textContent = r.message || r.error || 'Done';
    msg.className = 'message ' + (r.success ? 'success' : 'error');
    setTimeout(loadAPStatus, 2000);
  } catch (e) {
    msg.textContent = e.message;
    msg.className = 'message error';
  }
}

// --- Travel Mode (WiFi-to-WiFi) ---

async function scanUsbAdapters() {
  const container = document.getElementById('usb-scan-result');
  container.innerHTML = '<span class="badge badge-unknown">Scanning...</span>';
  try {
    const r = await api('/api/ap/usb-scan');
    if (!r.available) {
      container.innerHTML = '<span class="badge badge-danger">No USB WiFi adapter detected</span>' +
        '<p style="margin-top:0.5rem;font-size:0.85rem;color:var(--text-secondary)">Plug in a USB WiFi adapter and try again.</p>';
      return;
    }
    let html = '<span class="badge badge-success">' + r.usbWifiInterfaces.length + ' USB WiFi adapter(s) found</span>';
    html += '<ul style="margin-top:0.5rem;font-size:0.85rem;">';
    for (const iface of r.usbWifiInterfaces) {
      html += '<li><strong>' + iface.interface + '</strong></li>';
    }
    html += '</ul>';
    container.innerHTML = html;

    // Show travel config section and populate interface dropdown
    document.getElementById('travel-config').style.display = 'block';
    const select = document.getElementById('travel-iface');
    select.innerHTML = '<option value="">Select adapter...</option>';
    for (const iface of r.usbWifiInterfaces) {
      select.innerHTML += '<option value="' + iface.interface + '">' + iface.interface + '</option>';
    }

    // Also load travel status
    loadTravelStatus();
  } catch (e) {
    container.innerHTML = '<span class="badge badge-danger">Scan failed: ' + e.message + '</span>';
  }
}

async function loadTravelStatus() {
  try {
    const s = await api('/api/ap/travel-status');
    const el = document.getElementById('travel-status');
    if (s.upstreamConnected) {
      el.innerHTML = '<span class="badge badge-success">Connected</span> to <strong>' + (s.upstreamSSID || 'unknown') + '</strong>' +
        (s.apActive ? ' — AP is active' : '');
    } else if (s.available) {
      el.innerHTML = '<span class="badge badge-warning">USB adapter found, not connected to upstream</span>';
    } else {
      el.innerHTML = '<span class="badge badge-danger">No USB WiFi adapter</span>';
    }
  } catch (_) {}
}

async function scanWifiNetworks() {
  const iface = document.getElementById('travel-iface').value;
  const container = document.getElementById('wifi-networks');
  if (!iface) {
    container.innerHTML = '<span class="message error">Select a USB WiFi interface first</span>';
    return;
  }
  container.innerHTML = '<span class="badge badge-unknown">Scanning networks (up to 15s)...</span>';
  try {
    const networks = await api('/api/ap/wifi-networks?iface=' + encodeURIComponent(iface));
    if (networks.length === 0) {
      container.innerHTML = '<span class="message error">No networks found. Try again.</span>';
      return;
    }
    let html = '<table class="table"><thead><tr><th>SSID</th><th>Signal</th><th>Encrypted</th><th></th></tr></thead><tbody>';
    for (const n of networks) {
      html += '<tr><td>' + n.ssid + '</td><td>' + n.signal + '</td><td>' +
        (n.encrypted ? '<span class="badge badge-warning">Yes</span>' : '<span class="badge badge-success">Open</span>') +
        '</td><td><button class="btn btn-sm btn-primary" onclick="selectNetwork(\'' + n.ssid.replace(/'/g, "\\'") + '\')">Select</button></td></tr>';
    }
    html += '</tbody></table>';
    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<span class="message error">Scan failed: ' + e.message + '</span>';
  }
}

function selectNetwork(ssid) {
  document.getElementById('travel-ssid').value = ssid;
}

async function startTravelMode() {
  const msg = document.getElementById('travel-message');
  const iface = document.getElementById('travel-iface').value;
  const ssid = document.getElementById('travel-ssid').value;
  const password = document.getElementById('travel-pass').value;
  if (!iface || !ssid) {
    msg.textContent = 'Select a USB adapter and enter the upstream WiFi SSID';
    msg.className = 'message error';
    return;
  }
  msg.textContent = 'Starting travel mode... this may take 30+ seconds.';
  msg.className = 'message';
  try {
    const r = await api('/api/ap/travel-start', {
      method: 'POST',
      body: JSON.stringify({ usbInterface: iface, ssid, password })
    });
    msg.textContent = r.message || r.error || 'Done';
    msg.className = 'message ' + (r.success ? 'success' : 'error');
    setTimeout(() => { loadAPStatus(); loadTravelStatus(); }, 3000);
  } catch (e) {
    msg.textContent = e.message;
    msg.className = 'message error';
  }
}

async function stopTravelMode() {
  const msg = document.getElementById('travel-message');
  const iface = document.getElementById('travel-iface').value;
  msg.textContent = 'Stopping travel mode...';
  msg.className = 'message';
  try {
    const r = await api('/api/ap/travel-stop', {
      method: 'POST',
      body: JSON.stringify({ usbInterface: iface })
    });
    msg.textContent = r.message || r.error || 'Done';
    msg.className = 'message ' + (r.success ? 'success' : 'error');
    setTimeout(() => { loadAPStatus(); loadTravelStatus(); }, 2000);
  } catch (e) {
    msg.textContent = e.message;
    msg.className = 'message error';
  }
}

// Init
loadAPStatus();
setInterval(loadAPStatus, 5000);
