const express = require('express');
const router = express.Router();
const systemService = require('../services/system-service');

// GET /api/system/stats — full system report
router.get('/stats', async (req, res) => {
  try {
    const report = await systemService.getFullReport();
    res.json(report);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/system/quick — quick stats (temp, memory, cpu)
router.get('/quick', async (req, res) => {
  try {
    const stats = await systemService.getQuickStats();
    res.json(stats);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/system/service — manage services (start/stop/restart)
router.post('/service', async (req, res) => {
  const { name, action } = req.body;
  try {
    await systemService.manageService(name, action);
    res.json({ success: true, message: `Service ${name} ${action}ed` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
