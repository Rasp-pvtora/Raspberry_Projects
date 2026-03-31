const { execSync, exec } = require('child_process');
const fs = require('fs');
const os = require('os');

let si;
try { si = require('systeminformation'); } catch (_) { si = null; }

/**
 * Read CPU temperature from sysfs (Raspberry Pi).
 * Falls back to systeminformation on non-Pi systems.
 */
async function getCpuTemperature() {
  try {
    const raw = fs.readFileSync('/sys/class/thermal/thermal_zone0/temp', 'utf8');
    return (parseInt(raw, 10) / 1000).toFixed(1);
  } catch (_) {
    if (si) {
      const t = await si.cpuTemperature();
      return t.main ? t.main.toFixed(1) : 'N/A';
    }
    return 'N/A';
  }
}

/** Memory usage from /proc/meminfo or os module. */
async function getMemoryInfo() {
  const totalBytes = os.totalmem();
  const freeBytes = os.freemem();
  const usedBytes = totalBytes - freeBytes;
  return {
    total: (totalBytes / 1024 / 1024).toFixed(0),
    used: (usedBytes / 1024 / 1024).toFixed(0),
    free: (freeBytes / 1024 / 1024).toFixed(0),
    percent: ((usedBytes / totalBytes) * 100).toFixed(1)
  };
}

/** CPU load average. */
function getCpuLoad() {
  const load = os.loadavg();
  return {
    '1min': load[0].toFixed(2),
    '5min': load[1].toFixed(2),
    '15min': load[2].toFixed(2)
  };
}

/** Disk usage via df. */
function getDiskUsage() {
  try {
    const output = execSync('df -BM --output=source,size,used,avail,pcent,target 2>/dev/null || df -h', { encoding: 'utf8' });
    const lines = output.trim().split('\n');
    const disks = [];
    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i].trim().split(/\s+/);
      if (parts.length >= 6 && !parts[0].startsWith('tmpfs') && !parts[0].startsWith('devtmpfs')) {
        disks.push({
          filesystem: parts[0],
          size: parts[1],
          used: parts[2],
          available: parts[3],
          percent: parts[4],
          mountpoint: parts[5]
        });
      }
    }
    return disks;
  } catch (_) {
    return [];
  }
}

/** Network interfaces and IP addresses. */
function getNetworkInfo() {
  const interfaces = os.networkInterfaces();
  const result = [];
  for (const [name, addrs] of Object.entries(interfaces)) {
    if (name === 'lo') continue;
    for (const addr of addrs) {
      if (addr.family === 'IPv4') {
        result.push({ interface: name, address: addr.address, mac: addr.mac });
      }
    }
  }
  return result;
}

/** System uptime. */
function getUptime() {
  const secs = os.uptime();
  const days = Math.floor(secs / 86400);
  const hours = Math.floor((secs % 86400) / 3600);
  const minutes = Math.floor((secs % 3600) / 60);
  return { seconds: secs, formatted: `${days}d ${hours}h ${minutes}m` };
}

/** Hostname and OS info. */
function getHostInfo() {
  return {
    hostname: os.hostname(),
    platform: os.platform(),
    arch: os.arch(),
    release: os.release(),
    cpus: os.cpus().length,
    model: os.cpus()[0] ? os.cpus()[0].model : 'Unknown'
  };
}

/** Running processes (top 20 by CPU). */
function getProcesses() {
  try {
    const output = execSync('ps aux --sort=-%cpu 2>/dev/null | head -21', { encoding: 'utf8' });
    const lines = output.trim().split('\n');
    const procs = [];
    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i].trim().split(/\s+/);
      if (parts.length >= 11) {
        procs.push({
          user: parts[0],
          pid: parts[1],
          cpu: parts[2],
          mem: parts[3],
          command: parts.slice(10).join(' ')
        });
      }
    }
    return procs;
  } catch (_) {
    return [];
  }
}

/** Quick stats for WebSocket real-time updates. */
async function getQuickStats() {
  const temp = await getCpuTemperature();
  const mem = await getMemoryInfo();
  const load = getCpuLoad();
  return { temperature: temp, memory: mem, cpu: load, timestamp: Date.now() };
}

/** Full system report. */
async function getFullReport() {
  const temp = await getCpuTemperature();
  const mem = await getMemoryInfo();
  const load = getCpuLoad();
  const disks = getDiskUsage();
  const network = getNetworkInfo();
  const uptime = getUptime();
  const host = getHostInfo();
  const processes = getProcesses();
  return { temperature: temp, memory: mem, cpu: load, disks, network, uptime, host, processes };
}

/** Check if a systemd service is active. */
function isServiceActive(serviceName) {
  try {
    const result = execSync(`systemctl is-active ${serviceName} 2>/dev/null`, { encoding: 'utf8' }).trim();
    return result === 'active';
  } catch (_) {
    return false;
  }
}

/** Start/stop/restart a systemd service. */
function manageService(serviceName, action) {
  const allowed = ['start', 'stop', 'restart'];
  if (!allowed.includes(action)) throw new Error('Invalid action');
  const safeNames = ['tor', 'hostapd', 'dnsmasq', 'nginx'];
  if (!safeNames.includes(serviceName)) throw new Error('Service not allowed');
  return new Promise((resolve, reject) => {
    exec(`sudo systemctl ${action} ${serviceName}`, (err, stdout, stderr) => {
      if (err) reject(new Error(stderr || err.message));
      else resolve(stdout);
    });
  });
}

module.exports = {
  getCpuTemperature,
  getMemoryInfo,
  getCpuLoad,
  getDiskUsage,
  getNetworkInfo,
  getUptime,
  getHostInfo,
  getProcesses,
  getQuickStats,
  getFullReport,
  isServiceActive,
  manageService
};
