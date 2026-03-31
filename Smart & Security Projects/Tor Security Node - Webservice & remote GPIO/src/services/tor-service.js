const { exec, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const HIDDEN_SERVICE_DIR = process.env.TOR_HIDDEN_SERVICE_DIR || '/var/lib/tor/tor-security-node';
const WEBSITE_DIR = path.resolve(process.env.TOR_WEBSITE_DIR || './website');

/**
 * Get the current .onion address if it exists.
 */
function getOnionAddress() {
  try {
    const hostnameFile = path.join(HIDDEN_SERVICE_DIR, 'hostname');
    return fs.readFileSync(hostnameFile, 'utf8').trim();
  } catch (_) {
    return null;
  }
}

/**
 * Check if the Tor service is running.
 */
function isTorRunning() {
  try {
    const result = execSync('systemctl is-active tor 2>/dev/null', { encoding: 'utf8' }).trim();
    return result === 'active';
  } catch (_) {
    return false;
  }
}

/**
 * Get Tor service status details.
 */
function getTorStatus() {
  const running = isTorRunning();
  const onionAddress = getOnionAddress();
  return {
    running,
    onionAddress,
    hiddenServiceDir: HIDDEN_SERVICE_DIR,
    websiteDir: WEBSITE_DIR
  };
}

/**
 * Start the Tor service.
 */
function startTor() {
  return new Promise((resolve, reject) => {
    exec('sudo systemctl start tor', (err, stdout, stderr) => {
      if (err) reject(new Error(stderr || err.message));
      else resolve({ success: true, message: 'Tor service started' });
    });
  });
}

/**
 * Stop the Tor service.
 */
function stopTor() {
  return new Promise((resolve, reject) => {
    exec('sudo systemctl stop tor', (err, stdout, stderr) => {
      if (err) reject(new Error(stderr || err.message));
      else resolve({ success: true, message: 'Tor service stopped' });
    });
  });
}

/**
 * Restart the Tor service (to reload hidden service config).
 */
function restartTor() {
  return new Promise((resolve, reject) => {
    exec('sudo systemctl restart tor', (err, stdout, stderr) => {
      if (err) reject(new Error(stderr || err.message));
      else resolve({ success: true, message: 'Tor service restarted' });
    });
  });
}

/**
 * Configure the Tor hidden service in torrc.
 * Adds the HiddenServiceDir and HiddenServicePort lines.
 */
function configureHiddenService(port = 80) {
  return new Promise((resolve, reject) => {
    const torrcPath = '/etc/tor/torrc';
    const marker = '# --- Tor Security Node Hidden Service ---';
    const config = `
${marker}
HiddenServiceDir ${HIDDEN_SERVICE_DIR}
HiddenServicePort ${port} 127.0.0.1:${port}
${marker} END`;

    exec(`sudo grep -q "${marker}" ${torrcPath}`, (err) => {
      if (!err) {
        // Already configured
        resolve({ success: true, message: 'Hidden service already configured in torrc' });
        return;
      }
      // Append config to torrc
      exec(`echo '${config}' | sudo tee -a ${torrcPath}`, (err2, stdout, stderr) => {
        if (err2) reject(new Error(stderr || err2.message));
        else resolve({ success: true, message: 'Hidden service configured in torrc' });
      });
    });
  });
}

/**
 * Get the list of website files.
 */
function getWebsiteFiles() {
  try {
    if (!fs.existsSync(WEBSITE_DIR)) return [];
    return listDirRecursive(WEBSITE_DIR, WEBSITE_DIR);
  } catch (_) {
    return [];
  }
}

function listDirRecursive(dir, base) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    const relativePath = path.relative(base, fullPath);
    if (entry.isDirectory()) {
      files.push({ name: entry.name, path: relativePath, type: 'directory' });
      files.push(...listDirRecursive(fullPath, base));
    } else {
      const stat = fs.statSync(fullPath);
      files.push({
        name: entry.name,
        path: relativePath,
        type: 'file',
        size: stat.size
      });
    }
  }
  return files;
}

/**
 * Read website file content (for editing in dashboard).
 */
function readWebsiteFile(relativePath) {
  const safePath = path.resolve(WEBSITE_DIR, relativePath);
  if (!safePath.startsWith(path.resolve(WEBSITE_DIR))) {
    throw new Error('Path traversal denied');
  }
  return fs.readFileSync(safePath, 'utf8');
}

/**
 * Write website file content (for editing in dashboard).
 */
function writeWebsiteFile(relativePath, content) {
  const safePath = path.resolve(WEBSITE_DIR, relativePath);
  if (!safePath.startsWith(path.resolve(WEBSITE_DIR))) {
    throw new Error('Path traversal denied');
  }
  fs.writeFileSync(safePath, content, 'utf8');
}

module.exports = {
  getOnionAddress,
  isTorRunning,
  getTorStatus,
  startTor,
  stopTor,
  restartTor,
  configureHiddenService,
  getWebsiteFiles,
  readWebsiteFile,
  writeWebsiteFile
};
