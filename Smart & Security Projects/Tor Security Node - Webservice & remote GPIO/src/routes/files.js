const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');

const FILE_BROWSER_ROOT = path.resolve(process.env.FILE_BROWSER_ROOT || '/home/pi');

/**
 * Validate and resolve a requested path, preventing path traversal.
 */
function safePath(requestedPath) {
  const resolved = path.resolve(FILE_BROWSER_ROOT, requestedPath || '');
  if (!resolved.startsWith(FILE_BROWSER_ROOT)) {
    throw new Error('Path traversal denied');
  }
  return resolved;
}

// GET /api/files/list?path=...
router.get('/list', (req, res) => {
  try {
    const dirPath = safePath(req.query.path || '');
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    const items = [];

    for (const entry of entries) {
      // Skip hidden files starting with '.'
      if (entry.name.startsWith('.')) continue;

      const fullPath = path.join(dirPath, entry.name);
      const relativePath = path.relative(FILE_BROWSER_ROOT, fullPath);

      try {
        const stat = fs.statSync(fullPath);
        items.push({
          name: entry.name,
          path: relativePath.split(path.sep).join('/'),
          isDirectory: entry.isDirectory(),
          size: entry.isDirectory() ? null : stat.size,
          modified: stat.mtime.toISOString()
        });
      } catch (_) {
        // Skip files we can't stat (permission denied, etc.)
      }
    }

    // Sort: directories first, then alphabetically
    items.sort((a, b) => {
      if (a.isDirectory && !b.isDirectory) return -1;
      if (!a.isDirectory && b.isDirectory) return 1;
      return a.name.localeCompare(b.name);
    });

    const relativeCurrent = path.relative(FILE_BROWSER_ROOT, dirPath).split(path.sep).join('/');

    res.json({
      current: relativeCurrent || '/',
      root: FILE_BROWSER_ROOT,
      items
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/files/read?path=...
router.get('/read', (req, res) => {
  try {
    const filePath = safePath(req.query.path || '');
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      return res.status(400).json({ error: 'Cannot read a directory' });
    }

    // Limit file reading to 1MB for safety
    if (stat.size > 1024 * 1024) {
      return res.status(400).json({ error: 'File too large to read (max 1 MB)' });
    }

    const content = fs.readFileSync(filePath, 'utf8');
    const relativePath = path.relative(FILE_BROWSER_ROOT, filePath).split(path.sep).join('/');

    res.json({
      path: relativePath,
      name: path.basename(filePath),
      size: stat.size,
      content
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
