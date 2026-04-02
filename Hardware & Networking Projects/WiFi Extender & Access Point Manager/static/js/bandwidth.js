/* bandwidth.js — Bandwidth monitoring page logic */

let bwChart;

async function loadCurrentBandwidth() {
    try {
        const resp = await fetch('/api/bandwidth');
        if (!resp.ok) return;
        const data = await resp.json();

        document.getElementById('totalDownload').textContent = data.total.rx_kbps + ' kbps';
        document.getElementById('totalUpload').textContent = data.total.tx_kbps + ' kbps';

        const tbody = document.getElementById('perClientBw');
        if (!data.per_client.length) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">No data</td></tr>';
            return;
        }
        tbody.innerHTML = data.per_client.map(c => `<tr>
            <td>${esc(c.ip)}</td>
            <td>${c.rx_kbps}</td>
            <td>${c.tx_kbps}</td>
        </tr>`).join('');
    } catch (e) {
        console.error('Failed to load bandwidth:', e);
    }
}

async function loadHistory(hours) {
    hours = hours || 24;
    try {
        const resp = await fetch(`/api/bandwidth/history?hours=${hours}`);
        if (!resp.ok) return;
        const data = await resp.json();

        const ctx = document.getElementById('bwChart').getContext('2d');
        if (bwChart) bwChart.destroy();

        bwChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels.map(l => {
                    const d = new Date(l);
                    return hours <= 24
                        ? d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
                        : d.toLocaleDateString([], {month:'short', day:'numeric'});
                }),
                datasets: [
                    {
                        label: 'Download (kbps)', data: data.total_rx,
                        borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)',
                        fill: true, tension: 0.3,
                    },
                    {
                        label: 'Upload (kbps)', data: data.total_tx,
                        borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.1)',
                        fill: true, tension: 0.3,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: '#e2e8f0' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8', maxTicksLimit: 12 }, grid: { color: 'rgba(51,65,85,0.5)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51,65,85,0.5)' } },
                },
            },
        });
    } catch (e) {
        console.error('Failed to load history:', e);
    }
}

// Real-time updates
socket.on('bandwidth_update', (data) => {
    document.getElementById('totalDownload').textContent = data.total_rx_kbps + ' kbps';
    document.getElementById('totalUpload').textContent = data.total_tx_kbps + ' kbps';
});

// Initial load
loadCurrentBandwidth();
loadHistory(24);
setInterval(loadCurrentBandwidth, 10000);
