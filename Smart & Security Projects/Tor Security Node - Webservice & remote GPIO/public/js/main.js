/**
 * Tor Security Node — main.js
 * Shared utility: WebSocket connection for real-time top-bar stats.
 */
(function () {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}`;
  let ws;
  let reconnectTimer;

  function connect() {
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'system-stats') {
          updateTopBar(msg.data);
          // Dispatch custom event for pages that need real-time data
          window.dispatchEvent(new CustomEvent('system-stats', { detail: msg.data }));
        }
      } catch (_) {}
    };

    ws.onclose = () => {
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
  }

  function updateTopBar(data) {
    const temp = document.getElementById('top-temp');
    const mem = document.getElementById('top-mem');
    const cpu = document.getElementById('top-cpu');
    if (temp) temp.innerHTML = `<i class="fas fa-thermometer-half"></i> ${data.temperature}°C`;
    if (mem) mem.innerHTML = `<i class="fas fa-memory"></i> ${data.memory.percent}%`;
    if (cpu) cpu.innerHTML = `<i class="fas fa-microchip"></i> ${data.cpu['1min']}`;
  }

  connect();
})();

/**
 * Helper: fetch JSON from an API endpoint.
 */
async function api(url, options = {}) {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options
  });
  return resp.json();
}

/**
 * Helper: human-readable file size.
 */
function fileSize(bytes) {
  if (bytes === null || bytes === undefined) return '--';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}
