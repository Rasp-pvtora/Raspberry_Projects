/* settings.js — Settings page logic */

const FEATURE_LABELS = {
    'ENABLE_AUTO_SETUP': '🔧 Auto-Setup',
    'ENABLE_SSID_MANAGER': '📛 SSID Manager',
    'ENABLE_CLIENT_LIST': '👥 Client List',
    'ENABLE_BANDWIDTH_MONITOR': '📊 Bandwidth Monitor',
    'ENABLE_MAC_FILTER': '🛡️ MAC Filtering',
    'ENABLE_CAPTIVE_PORTAL': '🌐 Captive Portal',
    'ENABLE_QOS': '⚡ QoS Traffic Shaping',
    'ENABLE_WIFI_SCHEDULE': '🕐 WiFi Schedule',
    'ENABLE_AUTO_CHANNEL': '📡 Auto Channel',
    'ENABLE_DNS_CONFIG': '🔗 DNS Configuration',
    'ENABLE_DUAL_BAND': '📻 Dual-Band',
    'ENABLE_VPN_PASSTHROUGH': '🔒 VPN Passthrough',
    'ENABLE_NOTIFICATIONS': '🔔 Notifications',
    'ENABLE_CONNECTION_LOG': '📋 Connection Log',
    'ENABLE_HEALTH_MONITOR': '💚 Health Monitor',
};

let toggleStates = {};

async function loadFeatures() {
    try {
        const resp = await fetch('/api/settings/features');
        if (!resp.ok) return;
        toggleStates = await resp.json();
        renderToggles();
    } catch (e) {
        console.error('Failed to load features:', e);
    }
}

function renderToggles() {
    const grid = document.getElementById('toggleGrid');
    grid.innerHTML = Object.entries(FEATURE_LABELS).map(([key, label]) => {
        const checked = toggleStates[key] ? 'checked' : '';
        return `<div class="toggle-item">
            <span class="toggle-item-label">${label}</span>
            <label class="toggle">
                <input type="checkbox" ${checked} onchange="toggleStates['${key}']=this.checked; toggleFeature('${key}', this.checked)">
                <span class="toggle-slider"></span>
            </label>
        </div>`;
    }).join('');
}

function toggleFeature(key, enabled) {
    // Send via WebSocket for real-time
    socket.emit('toggle_feature', { feature: key, enabled: enabled });
}

async function saveToggles() {
    try {
        const resp = await fetch('/api/settings/features', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(toggleStates),
        });
        if (resp.ok) {
            const data = await resp.json();
            alert(`Updated ${data.updated.length} feature(s)`);
        } else {
            alert('Failed to save toggles');
        }
    } catch (e) {
        alert('Failed to save toggles');
    }
}

async function loadAPConfig() {
    try {
        const resp = await fetch('/api/ap/status');
        if (!resp.ok) return;
        const data = await resp.json();
        document.getElementById('cfgSSID').value = data.ssid || '';
        if (data.channel) {
            document.getElementById('cfgChannel').value = data.channel;
        }
    } catch (e) {
        console.error('Failed to load AP config:', e);
    }
}

async function saveAPConfig() {
    const ssid = document.getElementById('cfgSSID').value;
    const password = document.getElementById('cfgPassword').value;
    const channel = document.getElementById('cfgChannel').value;
    const hidden = document.getElementById('cfgHidden').checked;

    if (!confirm('Save config and restart AP? Connected clients will be briefly disconnected.')) return;

    try {
        const body = { hidden };
        if (ssid) body.ssid = ssid;
        if (password) body.password = password;
        if (channel !== 'auto') body.channel = parseInt(channel);

        await fetch('/api/ap/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        await fetch('/api/ap/restart', { method: 'POST' });
        alert('AP config saved and restarting...');
    } catch (e) {
        alert('Failed to save AP config');
    }
}

async function changePassword() {
    const current = document.getElementById('currentPass').value;
    const newPass = document.getElementById('newPass').value;

    if (!current || !newPass) { alert('Both fields required'); return; }
    if (newPass.length < 8) { alert('Password must be at least 8 characters'); return; }

    try {
        const resp = await fetch('/api/auth/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_password: current, new_password: newPass }),
        });
        const data = await resp.json();
        if (resp.ok) {
            alert('Password changed successfully');
            document.getElementById('currentPass').value = '';
            document.getElementById('newPass').value = '';
        } else {
            alert(data.error || 'Failed to change password');
        }
    } catch (e) {
        alert('Failed to change password');
    }
}

// Listen for feature toggles from other clients
socket.on('feature_toggled', (data) => {
    toggleStates[data.feature] = data.enabled;
    renderToggles();
});

// Initial load
loadFeatures();
loadAPConfig();
