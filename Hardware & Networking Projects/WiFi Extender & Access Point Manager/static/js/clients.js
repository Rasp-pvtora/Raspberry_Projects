/* clients.js — Client list page logic */

async function refreshClients() {
    try {
        const resp = await fetch('/api/clients');
        if (!resp.ok) return;
        const clients = await resp.json();
        const tbody = document.getElementById('clientsBody');

        if (!clients.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No clients connected</td></tr>';
            return;
        }

        tbody.innerHTML = clients.map(c => `<tr>
            <td>${esc(c.hostname || '—')}</td>
            <td><code>${esc(c.mac)}</code></td>
            <td>${esc(c.ip)}</td>
            <td>${c.signal_dbm || '—'} dBm</td>
            <td>${formatBytes(c.rx_bytes || 0)}</td>
            <td>${formatBytes(c.tx_bytes || 0)}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="disconnectClient('${esc(c.mac)}')">
                    Disconnect
                </button>
            </td>
        </tr>`).join('');
    } catch (e) {
        console.error('Failed to load clients:', e);
    }
}

async function disconnectClient(mac) {
    if (!confirm(`Disconnect ${mac}?`)) return;
    try {
        const resp = await fetch(`/api/clients/${encodeURIComponent(mac)}/disconnect`, { method: 'POST' });
        if (resp.ok) {
            refreshClients();
        } else {
            const data = await resp.json();
            alert(data.error || 'Failed to disconnect');
        }
    } catch (e) {
        alert('Failed to disconnect client');
    }
}

// Real-time updates
socket.on('client_connected', () => refreshClients());
socket.on('client_disconnected', () => refreshClients());

// Initial load & periodic refresh
refreshClients();
setInterval(refreshClients, 15000);
