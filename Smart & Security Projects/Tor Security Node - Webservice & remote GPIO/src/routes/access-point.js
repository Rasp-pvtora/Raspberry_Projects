const express = require('express');
const router = express.Router();
const apService = require('../services/ap-service');

// GET /api/ap/status
router.get('/status', (req, res) => {
  try {
    const status = apService.getAPStatus();
    res.json(status);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/ap/start
router.post('/start', async (req, res) => {
  try {
    const result = await apService.startAP();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/ap/stop
router.post('/stop', async (req, res) => {
  try {
    const result = await apService.stopAP();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
