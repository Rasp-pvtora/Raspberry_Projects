/**
 * System Monitor page — full system details.
 */
(function () {
  const SERVICES = ['tor', 'nginx', 'hostapd', 'dnsmasq'];

  // Real-time updates
  window.addEventListener('system-stats', (e) => {
    const d = e.detail;
    setText('sys-temp', d.temperature + '°C');
    setText('sys-cpu', d.cpu['1min'] + ' / ' + d.cpu['5min'] + ' / ' + d.cpu['15min']);
    setText('sys-mem', d.memory.used + ' / ' + d.memory.total + ' MB (' + d.memory.percent + '%)');
  });

  async function loadSystem() {
    try {
      const s = await api('/api/system/stats');

      // Uptime
      setText('sys-uptime', s.uptime.formatted);

      // Host info
      const host = document.getElementById('sys-host');
      if (host) {
        host.querySelector('tbody').innerHTML = `
          <tr><td>Hostname</td><td>${s.host.hostname}</td></tr>
          <tr><td>Platform</td><td>${s.host.platform} (${s.host.arch})</td></tr>
          <tr><td>Kernel</td><td>${s.host.release}</td></tr>
          <tr><td>CPU</td><td>${s.host.model} (${s.host.cpus} cores)</td></tr>`;
      }

      // Network
      const net = document.querySelector('#sys-network tbody');
      if (net && s.network.length > 0) {
        net.innerHTML = s.network.map(n =>
          `<tr><td>${n.interface}</td><td>${n.address}</td><td>${n.mac}</td></tr>`
        ).join('');
      }

      // Disk
      const disk = document.querySelector('#sys-disk tbody');
      if (disk && s.disks.length > 0) {
        disk.innerHTML = s.disks.map(d =>
          `<tr><td>${d.mountpoint}</td><td>${d.size}</td><td>${d.used}</td><td>${d.available}</td><td>${d.percent}</td></tr>`
        ).join('');
      }

      // Processes
      const procs = document.querySelector('#sys-procs tbody');
      if (procs && s.processes.length > 0) {
        procs.innerHTML = s.processes.map(p =>
          `<tr><td>${p.pid}</td><td>${p.user}</td><td>${p.cpu}%</td><td>${p.mem}%</td><td>${escHtml(p.command)}</td></tr>`
        ).join('');
      }

      // Services
      const svcEl = document.getElementById('sys-services');
      if (svcEl) {
        svcEl.innerHTML = SERVICES.map(name => {
          // We'll check services via individual queries
          return `<div class="service-item" id="svc-${name}">
            <span class="service-dot inactive"></span> ${name}
            <button class="btn btn-sm btn-success" onclick="svcAction('${name}','start')">Start</button>
            <button class="btn btn-sm btn-danger" onclick="svcAction('${name}','stop')">Stop</button>
            <button class="btn btn-sm btn-warning" onclick="svcAction('${name}','restart')">Restart</button>
          </div>`;
        }).join('');
      }
    } catch (_) {}
  }

  loadSystem();
  setInterval(loadSystem, 10000);
})();

async function svcAction(name, action) {
  try {
    await api('/api/system/service', {
      method: 'POST',
      body: JSON.stringify({ name, action })
    });
  } catch (_) {}
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function escHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
