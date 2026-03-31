/**
 * Access Point page — start/stop Tor AP.
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

// Init
loadAPStatus();
setInterval(loadAPStatus, 5000);
