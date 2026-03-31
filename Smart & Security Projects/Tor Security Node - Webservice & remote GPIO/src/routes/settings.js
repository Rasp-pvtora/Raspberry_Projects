const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');

const ENV_PATH = path.resolve(__dirname, '../../.env');

/**
 * Parse the .env file into an object.
 */
function readEnv() {
  try {
    const content = fs.readFileSync(ENV_PATH, 'utf8');
    const vars = {};
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIndex = trimmed.indexOf('=');
      if (eqIndex === -1) continue;
      const key = trimmed.substring(0, eqIndex).trim();
      const value = trimmed.substring(eqIndex + 1).trim();
      vars[key] = value;
    }
    return vars;
  } catch (_) {
    return {};
  }
}

/**
 * Write an object back to .env preserving comments and structure.
 */
function writeEnv(updates) {
  let content;
  try {
    content = fs.readFileSync(ENV_PATH, 'utf8');
  } catch (_) {
    content = '';
  }

  const lines = content.split('\n');
  const updatedKeys = new Set();

  const newLines = lines.map((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return line;
    const eqIndex = trimmed.indexOf('=');
    if (eqIndex === -1) return line;
    const key = trimmed.substring(0, eqIndex).trim();
    if (key in updates) {
      updatedKeys.add(key);
      return `${key}=${updates[key]}`;
    }
    return line;
  });

  // Append new keys that weren't in the original file
  for (const [key, value] of Object.entries(updates)) {
    if (!updatedKeys.has(key)) {
      newLines.push(`${key}=${value}`);
    }
  }

  fs.writeFileSync(ENV_PATH, newLines.join('\n'), 'utf8');

  // Update process.env so changes take effect immediately
  for (const [key, value] of Object.entries(updates)) {
    process.env[key] = value;
  }
}

// GET /api/settings — get current settings (mask password)
router.get('/', (req, res) => {
  try {
    const vars = readEnv();
    // Mask the password for display
    if (vars.ADMIN_PASSWORD) {
      vars.ADMIN_PASSWORD = '********';
    }
    if (vars.SESSION_SECRET) {
      vars.SESSION_SECRET = '********';
    }
    res.json(vars);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/settings — update settings
router.put('/', (req, res) => {
  try {
    const updates = req.body;
    if (!updates || typeof updates !== 'object') {
      return res.status(400).json({ error: 'Request body must be an object of key-value pairs' });
    }

    // Prevent empty password updates (masked value)
    if (updates.ADMIN_PASSWORD === '********') {
      delete updates.ADMIN_PASSWORD;
    }
    if (updates.SESSION_SECRET === '********') {
      delete updates.SESSION_SECRET;
    }

    // Validate critical fields
    if (updates.PORT) {
      const port = parseInt(updates.PORT, 10);
      if (isNaN(port) || port < 1 || port > 65535) {
        return res.status(400).json({ error: 'PORT must be between 1 and 65535' });
      }
    }

    writeEnv(updates);
    res.json({ success: true, message: 'Settings updated. Some changes require a restart.' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/settings/password — change admin password
router.put('/password', (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body;
    if (!currentPassword || !newPassword) {
      return res.status(400).json({ error: 'currentPassword and newPassword are required' });
    }

    const envVars = readEnv();
    if (currentPassword !== (envVars.ADMIN_PASSWORD || process.env.ADMIN_PASSWORD)) {
      return res.status(403).json({ error: 'Current password is incorrect' });
    }

    if (newPassword.length < 6) {
      return res.status(400).json({ error: 'New password must be at least 6 characters' });
    }

    writeEnv({ ADMIN_PASSWORD: newPassword });
    res.json({ success: true, message: 'Password updated successfully' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
