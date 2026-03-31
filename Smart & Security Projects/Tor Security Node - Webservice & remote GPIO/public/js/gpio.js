/**
 * GPIO Control page — interactive pin map and pin management.
 */
const PIN_LAYOUT = {}; // Will be loaded from API

async function loadGPIO() {
  try {
    const status = await api('/api/gpio/status');
    const badge = document.getElementById('gpio-available');
    badge.textContent = status.available ? 'Yes' : 'No (mock mode)';
    badge.className = 'badge ' + (status.available ? 'badge-success' : 'badge-warning');

    // Load full layout
    const layout = await api('/api/gpio/layout');
    renderBoard(layout);
    renderActivePins(status.activePins);

    // Populate GPIO select
    const select = document.getElementById('gpio-select');
    select.innerHTML = '<option value="">Select GPIO...</option>';
    for (let pin = 1; pin <= 40; pin++) {
      const p = layout[pin];
      if (p && p.type === 'gpio' && p.gpio !== null) {
        select.innerHTML += `<option value="${p.gpio}">GPIO ${p.gpio} (Pin ${pin}) — ${p.name}</option>`;
      }
    }
  } catch (e) {
    document.getElementById('gpio-available').textContent = 'Error';
  }
}

function renderBoard(layout) {
  const board = document.getElementById('gpio-board');
  let html = '<div class="gpio-header-pins">';
  for (let pin = 1; pin <= 40; pin += 2) {
    const left = layout[pin];
    const right = layout[pin + 1];
    html += renderPin(left, pin, 'left');
    html += renderPin(right, pin + 1, 'right');
  }
  html += '</div>';
  board.innerHTML = html;
}

function renderPin(info, physical, side) {
  const typeClass = info.type === 'power' ? 'power' :
                    info.type === 'ground' ? 'ground' : 'gpio-type';
  let activeClass = '';
  if (info.active && info.direction === 'out') activeClass = ' active-out';
  if (info.active && info.direction === 'in') activeClass = ' active-in';

  const label = info.gpio !== null ? `GPIO${info.gpio}` : info.name;
  const title = `Pin ${physical}: ${info.name}`;
  const onclick = info.type === 'gpio' && info.gpio !== null
    ? `onclick="quickConfigure(${info.gpio})"`
    : '';

  return `<div class="gpio-pin ${typeClass}${activeClass} ${side}" title="${title}" ${onclick}>
    <span class="pin-dot">${physical}</span>
    <span class="pin-label">${label}</span>
  </div>`;
}

function renderActivePins(pins) {
  const tbody = document.querySelector('#gpio-active tbody');
  if (pins.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4">No pins configured</td></tr>';
    return;
  }
  tbody.innerHTML = pins.map(p => {
    const toggleBtn = p.direction === 'out'
      ? `<button class="btn btn-sm btn-primary" onclick="togglePin(${p.gpio}, ${p.value})">${p.value ? 'HIGH → LOW' : 'LOW → HIGH'}</button>`
      : `<button class="btn btn-sm btn-primary" onclick="refreshPin(${p.gpio})">Read</button>`;
    return `<tr>
      <td>GPIO ${p.gpio}${p.mock ? ' (mock)' : ''}</td>
      <td>${p.direction.toUpperCase()}</td>
      <td><span class="badge ${p.value ? 'badge-success' : 'badge-danger'}">${p.value ? 'HIGH (1)' : 'LOW (0)'}</span></td>
      <td>${toggleBtn} <button class="btn btn-sm btn-danger" onclick="releasePin(${p.gpio})">Release</button></td>
    </tr>`;
  }).join('');
}

function quickConfigure(gpio) {
  document.getElementById('gpio-select').value = gpio;
}

async function configurePin() {
  const msg = document.getElementById('gpio-config-msg');
  const gpio = document.getElementById('gpio-select').value;
  const dir = document.getElementById('gpio-dir').value;
  if (!gpio) { msg.textContent = 'Select a GPIO pin'; msg.className = 'message error'; return; }
  try {
    const r = await api('/api/gpio/configure', {
      method: 'POST',
      body: JSON.stringify({ gpio: parseInt(gpio), direction: dir })
    });
    msg.textContent = `GPIO ${gpio} configured as ${dir}` + (r.mock ? ' (mock)' : '');
    msg.className = 'message success';
    loadGPIO();
  } catch (e) { msg.textContent = e.message; msg.className = 'message error'; }
}

async function togglePin(gpio, currentValue) {
  try {
    await api('/api/gpio/write', {
      method: 'POST',
      body: JSON.stringify({ gpio, value: currentValue ? 0 : 1 })
    });
    loadGPIO();
  } catch (_) {}
}

async function refreshPin(gpio) {
  try {
    await api(`/api/gpio/read/${gpio}`);
    loadGPIO();
  } catch (_) {}
}

async function releasePin(gpio) {
  try {
    await api('/api/gpio/release', {
      method: 'POST',
      body: JSON.stringify({ gpio })
    });
    loadGPIO();
  } catch (_) {}
}

// Init
loadGPIO();
