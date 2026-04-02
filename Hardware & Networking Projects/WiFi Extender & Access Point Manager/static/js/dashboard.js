/* dashboard.js — Dashboard page logic */

let bandwidthChart;

async function loadAPStatus() {
    try {
        const resp = await fetch('/api/ap/status');
        if (!resp.ok) return;
        const data = await resp.json();

        document.getElementById('apStatusBadge').textContent = data.running ? 'Running' : 'Stopped';
        document.getElementById('apStatusBadge').classList.toggle('badge-success', data.running);
        document.getElementById('apStatusBadge').classList.toggle('badge-danger', !data.running);
        document.getElementById('apSSID').textContent = data.ssid || '—';
        document.getElementById('apChannel').textContent = data.channel || '—';
        document.getElementById('apInterface').textContent = data.interface || '—';
        document.getElementById('clientCount').textContent = data.clients_count || 0;
    } catch (e) {
        console.error('Failed to load AP status:', e);
    }
}

async function loadBandwidth() {
    try {
        const resp = await fetch('/api/bandwidth');
        if (!resp.ok) return;
        const data = await resp.json();

        document.getElementById('totalRx').textContent = data.total.rx_kbps + ' kbps';
        document.getElementById('totalTx').textContent = data.total.tx_kbps + ' kbps';
    } catch (e) {
        console.error('Failed to load bandwidth:', e);
    }
}

async function loadHealth() {
    try {
        const resp = await fetch('/api/health');
        if (!resp.ok) return;
        const data = await resp.json();

        const statusEl = document.getElementById('internetStatus');
        statusEl.textContent = data.internet_up ? '✅ Online' : '❌ Offline';
        statusEl.style.color = data.internet_up ? '#22c55e' : '#ef4444';

        document.getElementById('latency').textContent =
            data.latency_ms >= 0 ? data.latency_ms + ' ms' : 'N/A';
        document.getElementById('packetLoss').textContent = data.packet_loss_pct + '%';
    } catch (e) {
        console.error('Failed to load health:', e);
    }
}

async function loadBandwidthChart() {
    try {
        const resp = await fetch('/api/bandwidth/history?hours=24');
        if (!resp.ok) return;
        const data = await resp.json();

        const ctx = document.getElementById('bandwidthChart').getContext('2d');
        if (bandwidthChart) bandwidthChart.destroy();

        bandwidthChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels.map(l => {
                    const d = new Date(l);
                    return d.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
                }),
                datasets: [
                    {
                        label: 'Download (kbps)',
                        data: data.total_rx,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.3,
                    },
                    {
                        label: 'Upload (kbps)',
                        data: data.total_tx,
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        fill: true,
                        tension: 0.3,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: '#e2e8f0' } },
                },
                scales: {
                    x: { ticks: { color: '#94a3b8', maxTicksLimit: 12 }, grid: { color: 'rgba(51,65,85,0.5)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51,65,85,0.5)' } },
                },
            },
        });
    } catch (e) {
        console.error('Failed to load bandwidth chart:', e);
    }
}

async function restartAP() {
    if (!confirm('Restart the Access Point? Connected clients will be briefly disconnected.')) return;
    try {
        const resp = await fetch('/api/ap/restart', { method: 'POST' });
        const data = await resp.json();
        alert(data.status === 'restarting' ? 'AP is restarting...' : 'Error: ' + (data.error || 'Unknown'));
        setTimeout(loadAPStatus, 10000);
    } catch (e) {
        alert('Failed to restart AP');
    }
}

// Real-time updates
socket.on('bandwidth_update', (data) => {
    document.getElementById('totalRx').textContent = data.total_rx_kbps + ' kbps';
    document.getElementById('totalTx').textContent = data.total_tx_kbps + ' kbps';
});

socket.on('ap_status_change', (data) => {
    document.getElementById('apStatusBadge').textContent = data.status === 'running' ? 'Running' : 'Stopped';
});

socket.on('client_connected', () => {
    loadAPStatus();
});

socket.on('client_disconnected', () => {
    loadAPStatus();
});

// Initial load
loadAPStatus();
loadBandwidth();
loadHealth();
loadBandwidthChart();

// Periodic refresh
setInterval(loadAPStatus, 15000);
setInterval(loadBandwidth, 10000);
setInterval(loadHealth, 30000);
