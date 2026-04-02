/* ─── documents.js — Upload, delete, re-index logic ──────────── */

(function () {
    const dropzone = document.getElementById('upload-dropzone');
    const fileInput = document.getElementById('file-input');
    const progressArea = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const uploadStatus = document.getElementById('upload-status');
    const tbody = document.getElementById('documents-body');

    // ── Load document list ──
    function loadDocuments() {
        fetch('/documents/list')
            .then(r => r.json())
            .then(docs => {
                if (docs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7">No documents uploaded yet.</td></tr>';
                    return;
                }
                tbody.innerHTML = docs.map(d => `
                    <tr>
                        <td>${escapeHtml(d.filename)}</td>
                        <td>${d.file_type}</td>
                        <td>${formatFileSize(d.file_size)}</td>
                        <td>${d.chunk_count}</td>
                        <td><span class="badge badge-${d.status}">${d.status}</span></td>
                        <td>${formatDate(d.uploaded_at)}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="reindexDoc(${d.id})">Re-index</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteDoc(${d.id})">Delete</button>
                        </td>
                    </tr>
                `).join('');
            });
    }

    // ── Upload ──
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.style.borderColor = '#4fc3f7'; });
    dropzone.addEventListener('dragleave', () => { dropzone.style.borderColor = ''; });
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = '';
        if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) uploadFile(fileInput.files[0]);
    });

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        progressArea.style.display = 'block';
        uploadStatus.textContent = 'Uploading...';
        progressFill.style.width = '0%';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/documents/upload');
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const pct = Math.round((e.loaded / e.total) * 100);
                progressFill.style.width = pct + '%';
                uploadStatus.textContent = `Uploading... ${pct}%`;
            }
        });
        xhr.onload = () => {
            const data = JSON.parse(xhr.responseText);
            if (xhr.status >= 200 && xhr.status < 300) {
                uploadStatus.textContent = data.message + (data.warning ? ` (${data.warning})` : '');
            } else {
                uploadStatus.textContent = 'Error: ' + (data.error || 'Upload failed');
            }
            loadDocuments();
        };
        xhr.onerror = () => { uploadStatus.textContent = 'Network error'; };
        xhr.send(formData);
    }

    // ── Actions ──
    window.deleteDoc = function (id) {
        if (!confirm('Delete this document and all its data?')) return;
        fetch(`/documents/${id}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(() => loadDocuments());
    };

    window.reindexDoc = function (id) {
        fetch(`/documents/${id}/reindex`, { method: 'POST' })
            .then(r => r.json())
            .then(() => loadDocuments());
    };

    // ── Init ──
    loadDocuments();
})();
