/* ─── models.js — Model management interface ─────────────────── */

(function () {
    const tbody = document.getElementById('models-body');
    const activeEl = document.getElementById('active-model');
    const pullBtn = document.getElementById('pull-btn');
    const pullInput = document.getElementById('pull-model-name');

    function loadModels() {
        fetch('/models/list')
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    tbody.innerHTML = `<tr><td colspan="4">${data.error}</td></tr>`;
                    return;
                }
                activeEl.textContent = data.active || '—';
                const models = data.models || [];
                if (models.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4">No models found. Pull one first.</td></tr>';
                    return;
                }
                tbody.innerHTML = models.map(m => `
                    <tr>
                        <td>${escapeHtml(m.name || m.model || '—')}</td>
                        <td>${m.size ? (m.size / 1e9).toFixed(1) + ' GB' : '—'}</td>
                        <td>${m.modified_at || '—'}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="switchModel('${escapeHtml(m.name || m.model)}')">Use</button>
                        </td>
                    </tr>
                `).join('');
            });
    }

    window.switchModel = function (name) {
        fetch('/models/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name }),
        })
            .then(r => r.json())
            .then(data => {
                activeEl.textContent = data.active || name;
                loadModels();
            });
    };

    pullBtn.addEventListener('click', () => {
        const name = pullInput.value.trim();
        if (!name) { alert('Enter a model name'); return; }
        fetch('/models/pull', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name }),
        })
            .then(r => r.json())
            .then(data => {
                alert(data.message || data.error);
                loadModels();
            });
    });

    loadModels();
})();
