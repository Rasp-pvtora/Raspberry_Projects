/* qos.js — QoS traffic shaping page logic */

async function loadQoSRules() {
    try {
        const resp = await fetch('/api/qos/rules');
        if (!resp.ok) return;
        const rules = await resp.json();
        const tbody = document.getElementById('qosRules');

        if (!rules.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No QoS rules configured</td></tr>';
            return;
        }

        tbody.innerHTML = rules.map(r => `<tr>
            <td><code>${esc(r.mac_address)}</code></td>
            <td>${r.down_limit_kbps || '—'}</td>
            <td>${r.up_limit_kbps || '—'}</td>
            <td>${r.priority || 5}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteQoS('${esc(r.mac_address)}')">Delete</button>
            </td>
        </tr>`).join('');
    } catch (e) {
        console.error('Failed to load QoS rules:', e);
    }
}

function showAddQoS() {
    document.getElementById('qosMac').value = '';
    document.getElementById('qosDown').value = '10000';
    document.getElementById('qosUp').value = '5000';
    document.getElementById('qosPriority').value = '5';
    document.getElementById('qosModal').style.display = 'flex';
}

function closeQoSModal() {
    document.getElementById('qosModal').style.display = 'none';
}

async function saveQoS() {
    const mac = document.getElementById('qosMac').value.toUpperCase();
    const down = parseInt(document.getElementById('qosDown').value);
    const up = parseInt(document.getElementById('qosUp').value);
    const priority = parseInt(document.getElementById('qosPriority').value);

    if (!mac) { alert('MAC address required'); return; }

    try {
        const resp = await fetch(`/api/qos/rules/${encodeURIComponent(mac)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ down_limit_kbps: down, up_limit_kbps: up, priority }),
        });

        if (resp.ok) {
            closeQoSModal();
            loadQoSRules();
        } else {
            const data = await resp.json();
            alert(data.error || 'Failed to save rule');
        }
    } catch (e) {
        alert('Failed to save QoS rule');
    }
}

async function deleteQoS(mac) {
    if (!confirm(`Delete QoS rule for ${mac}?`)) return;
    try {
        await fetch(`/api/qos/rules/${encodeURIComponent(mac)}`, { method: 'DELETE' });
        loadQoSRules();
    } catch (e) {
        alert('Failed to delete rule');
    }
}

// Initial load
loadQoSRules();
