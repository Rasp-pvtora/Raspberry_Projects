/**
 * Dashboard page — real-time charts + status cards.
 */
(function () {
  const tempData = [];
  const memData = [];
  const labels = [];
  const MAX_POINTS = 60;

  // --- Charts ---
  const tempCtx = document.getElementById('tempChart');
  const memCtx = document.getElementById('memChart');

  const chartOpts = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    scales: {
      x: { display: false },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9090b0' } }
    },
    plugins: { legend: { display: false } }
  };

  const tempChart = new Chart(tempCtx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data: tempData,
        borderColor: '#ff5555',
        backgroundColor: 'rgba(255,85,85,0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 0
      }]
    },
    options: { ...chartOpts, scales: { ...chartOpts.scales, y: { ...chartOpts.scales.y, suggestedMin: 30, suggestedMax: 80 } } }
  });

  const memChart = new Chart(memCtx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data: memData,
        borderColor: '#8be9fd',
        backgroundColor: 'rgba(139,233,253,0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 0
      }]
    },
    options: { ...chartOpts, scales: { ...chartOpts.scales, y: { ...chartOpts.scales.y, suggestedMin: 0, suggestedMax: 100 } } }
  });

  // --- Real-time updates from WebSocket ---
  window.addEventListener('system-stats', (e) => {
    const d = e.detail;
    const now = new Date().toLocaleTimeString();

    // Update dashboard cards
    const t = document.getElementById('dash-temp');
    const m = document.getElementById('dash-mem');
    const c = document.getElementById('dash-cpu');
    if (t) t.textContent = d.temperature + '°C';
    if (m) m.textContent = d.memory.percent + '%';
    if (c) c.textContent = d.cpu['1min'];

    // Update charts
    labels.push(now);
    tempData.push(parseFloat(d.temperature) || 0);
    memData.push(parseFloat(d.memory.percent) || 0);

    if (labels.length > MAX_POINTS) {
      labels.shift();
      tempData.shift();
      memData.shift();
    }

    tempChart.update();
    memChart.update();
  });

  // --- Load initial full stats ---
  async function loadDashboard() {
    try {
      const stats = await api('/api/system/stats');

      // Uptime
      const up = document.getElementById('dash-uptime');
      if (up) up.textContent = stats.uptime.formatted;

      // Network table
      const tbody = document.querySelector('#dash-network tbody');
      if (tbody && stats.network.length > 0) {
        tbody.innerHTML = stats.network.map(n =>
          `<tr><td>${n.interface}</td><td>${n.address}</td><td>${n.mac}</td></tr>`
        ).join('');
      }
    } catch (_) {}

    // Tor status
    try {
      const tor = await api('/api/tor/status');
      const el = document.getElementById('dash-tor-status');
      if (el) {
        el.innerHTML = `
          <div class="status-row"><span>Status:</span>
            <span class="badge ${tor.running ? 'badge-success' : 'badge-danger'}">${tor.running ? 'Running' : 'Stopped'}</span>
          </div>
          <div class="status-row"><span>.onion:</span>
            <code class="onion-addr">${tor.onionAddress || 'Not configured'}</code>
          </div>`;
      }
    } catch (_) {}

    // AP status
    try {
      const ap = await api('/api/ap/status');
      const el = document.getElementById('dash-ap-status');
      if (el) {
        el.innerHTML = `
          <div class="status-row"><span>Status:</span>
            <span class="badge ${ap.active ? 'badge-success' : 'badge-danger'}">${ap.active ? 'Active' : 'Inactive'}</span>
          </div>
          <div class="status-row"><span>SSID:</span><span>${ap.ssid}</span></div>
          <div class="status-row"><span>Clients:</span><span>${ap.connectedClients}</span></div>`;
      }
    } catch (_) {}
  }

  loadDashboard();
})();
