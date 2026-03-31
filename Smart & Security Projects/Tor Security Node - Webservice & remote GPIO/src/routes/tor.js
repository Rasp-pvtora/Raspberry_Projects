const express = require('express');
const router = express.Router();
const torService = require('../services/tor-service');

// GET /api/tor/status
router.get('/status', (req, res) => {
  try {
    const status = torService.getTorStatus();
    res.json(status);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/tor/start
router.post('/start', async (req, res) => {
  try {
    const result = await torService.startTor();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/tor/stop
router.post('/stop', async (req, res) => {
  try {
    const result = await torService.stopTor();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/tor/restart
router.post('/restart', async (req, res) => {
  try {
    const result = await torService.restartTor();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/tor/configure — write hidden service config to torrc
router.post('/configure', async (req, res) => {
  try {
    const result = await torService.configureHiddenService();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/tor/website/files — list website files
router.get('/website/files', (req, res) => {
  try {
    const files = torService.getWebsiteFiles();
    res.json(files);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/tor/website/file?path=... — read a website file
router.get('/website/file', (req, res) => {
  try {
    const filePath = req.query.path;
    if (!filePath) return res.status(400).json({ error: 'path parameter required' });
    const content = torService.readWebsiteFile(filePath);
    res.json({ path: filePath, content });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/tor/website/file — write a website file
router.put('/website/file', (req, res) => {
  try {
    const { path: filePath, content } = req.body;
    if (!filePath || content === undefined) {
      return res.status(400).json({ error: 'path and content are required' });
    }
    torService.writeWebsiteFile(filePath, content);
    res.json({ success: true, path: filePath });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
