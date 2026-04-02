/* ─── compare.js — Document comparison interface ──────────────── */

(function () {
    const selectA = document.getElementById('doc-a');
    const selectB = document.getElementById('doc-b');
    const compareBtn = document.getElementById('compare-btn');
    const resultDiv = document.getElementById('compare-result');
    const contentDiv = document.getElementById('compare-content');

    // Load documents into dropdowns
    fetch('/documents/list')
        .then(r => r.json())
        .then(docs => {
            const opts = docs.map(d => `<option value="${d.id}">${escapeHtml(d.filename)}</option>`).join('');
            selectA.innerHTML = '<option value="">Select document</option>' + opts;
            selectB.innerHTML = '<option value="">Select document</option>' + opts;
        });

    compareBtn.addEventListener('click', () => {
        const a = selectA.value;
        const b = selectB.value;
        if (!a || !b) { alert('Select two documents'); return; }
        if (a === b) { alert('Select two different documents'); return; }

        contentDiv.textContent = 'Comparing...';
        resultDiv.style.display = 'block';

        fetch('/compare/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ document_a: parseInt(a), document_b: parseInt(b) }),
        })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    contentDiv.textContent = data.error;
                } else {
                    contentDiv.innerHTML = `<pre style="white-space:pre-wrap">${escapeHtml(data.answer)}</pre>`;
                }
            });
    });
})();
