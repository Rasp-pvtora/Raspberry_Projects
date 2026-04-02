/* ─── main.js — Shared utilities ─────────────────────────────── */

/**
 * Format file size in bytes to a human-readable string.
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Format an ISO timestamp to a locale string.
 */
function formatDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString();
}

/**
 * Escape HTML characters for safe rendering.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
