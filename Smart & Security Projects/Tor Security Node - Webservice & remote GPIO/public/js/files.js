/**
 * File Browser page — navigate Pi filesystem.
 */
let currentPath = '';

async function navigateTo(dir) {
  currentPath = dir || '';
  try {
    const data = await api(`/api/files/list?path=${encodeURIComponent(currentPath)}`);

    // Breadcrumb
    const bc = document.getElementById('file-breadcrumb');
    let bcHtml = `<a href="#" onclick="navigateTo('')"><i class="fas fa-home"></i> Root</a>`;
    if (data.current && data.current !== '/') {
      const parts = data.current.split('/');
      let acc = '';
      for (const part of parts) {
        acc += (acc ? '/' : '') + part;
        bcHtml += ` <span class="sep">/</span> <a href="#" onclick="navigateTo('${acc}')">${part}</a>`;
      }
    }
    bc.innerHTML = bcHtml;

    // File table
    const tbody = document.querySelector('#file-table tbody');
    if (data.items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="3">Empty directory</td></tr>';
      return;
    }

    // Add parent directory link
    let rows = '';
    if (currentPath) {
      const parent = currentPath.split('/').slice(0, -1).join('/');
      rows += `<tr onclick="navigateTo('${parent}')" style="cursor:pointer">
        <td><i class="fas fa-level-up-alt" style="color:var(--accent)"></i> ..</td><td></td><td></td></tr>`;
    }

    rows += data.items.map(item => {
      if (item.isDirectory) {
        return `<tr onclick="navigateTo('${item.path}')" style="cursor:pointer">
          <td><i class="fas fa-folder" style="color:#f1fa8c"></i> ${item.name}</td>
          <td>--</td>
          <td>${new Date(item.modified).toLocaleString()}</td></tr>`;
      }
      return `<tr onclick="previewFile('${item.path}')" style="cursor:pointer">
        <td><i class="fas fa-file" style="color:var(--text-secondary)"></i> ${item.name}</td>
        <td>${fileSize(item.size)}</td>
        <td>${new Date(item.modified).toLocaleString()}</td></tr>`;
    }).join('');

    tbody.innerHTML = rows;
  } catch (e) {
    document.querySelector('#file-table tbody').innerHTML =
      `<tr><td colspan="3" style="color:var(--danger)">${e.message}</td></tr>`;
  }
}

async function previewFile(path) {
  const card = document.getElementById('file-preview-card');
  const content = document.getElementById('file-preview-content');
  const name = document.getElementById('preview-filename');
  try {
    const data = await api(`/api/files/read?path=${encodeURIComponent(path)}`);
    name.textContent = data.name;
    content.textContent = data.content;
    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth' });
  } catch (e) {
    name.textContent = 'Error';
    content.textContent = e.message;
    card.style.display = 'block';
  }
}

// Init
navigateTo('');
