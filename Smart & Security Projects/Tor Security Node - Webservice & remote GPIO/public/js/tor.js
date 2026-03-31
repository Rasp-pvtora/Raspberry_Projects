/**
 * Tor Website page — manage hidden service and edit website files.
 */
let currentEditFile = null;

async function loadTorStatus() {
  try {
    const status = await api('/api/tor/status');
    const badge = document.getElementById('tor-running');
    badge.textContent = status.running ? 'Running' : 'Stopped';
    badge.className = 'badge ' + (status.running ? 'badge-success' : 'badge-danger');

    const addr = document.getElementById('onion-address');
    addr.textContent = status.onionAddress || 'Not configured — click Configure torrc first';
  } catch (e) {
    document.getElementById('tor-running').textContent = 'Error';
  }
}

async function torAction(action) {
  const msg = document.getElementById('tor-message');
  msg.textContent = 'Processing...';
  msg.className = 'message';
  try {
    const url = action === 'configure' ? '/api/tor/configure' : `/api/tor/${action}`;
    const r = await api(url, { method: 'POST' });
    msg.textContent = r.message || r.error || 'Done';
    msg.className = 'message ' + (r.success ? 'success' : 'error');
    setTimeout(loadTorStatus, 1000);
  } catch (e) {
    msg.textContent = e.message;
    msg.className = 'message error';
  }
}

function copyOnion() {
  const text = document.getElementById('onion-address').textContent;
  if (text && !text.startsWith('Not')) {
    navigator.clipboard.writeText(text);
  }
}

async function loadWebsiteFiles() {
  try {
    const files = await api('/api/tor/website/files');
    const container = document.getElementById('website-files');
    if (files.length === 0) {
      container.innerHTML = '<p>No website files found.</p>';
      return;
    }
    container.innerHTML = files
      .filter(f => f.type === 'file')
      .map(f => `<div class="file-item" onclick="editFile('${f.path}')">
        <i class="fas fa-file-code"></i> ${f.path} <small style="color: var(--text-secondary)">(${fileSize(f.size)})</small>
      </div>`).join('');
  } catch (e) {
    document.getElementById('website-files').innerHTML = '<p>Error loading files</p>';
  }
}

async function editFile(path) {
  try {
    const data = await api(`/api/tor/website/file?path=${encodeURIComponent(path)}`);
    document.getElementById('file-editor').value = data.content;
    document.getElementById('editing-file').textContent = path;
    currentEditFile = path;
  } catch (e) {
    document.getElementById('editing-file').textContent = 'Error: ' + e.message;
  }
}

async function saveFile() {
  const msg = document.getElementById('save-message');
  if (!currentEditFile) { msg.textContent = 'No file selected'; msg.className = 'message error'; return; }
  try {
    const content = document.getElementById('file-editor').value;
    const r = await api('/api/tor/website/file', {
      method: 'PUT',
      body: JSON.stringify({ path: currentEditFile, content })
    });
    msg.textContent = r.success ? 'Saved!' : (r.error || 'Error');
    msg.className = 'message ' + (r.success ? 'success' : 'error');
  } catch (e) {
    msg.textContent = e.message;
    msg.className = 'message error';
  }
}

// Init
loadTorStatus();
loadWebsiteFiles();
setInterval(loadTorStatus, 5000);
