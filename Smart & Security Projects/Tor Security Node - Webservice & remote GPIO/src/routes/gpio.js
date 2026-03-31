const express = require('express');
const router = express.Router();
const gpioService = require('../services/gpio-service');

// GET /api/gpio/status — check if GPIO is available
router.get('/status', (req, res) => {
  res.json({
    available: gpioService.isAvailable(),
    activePins: gpioService.getActivePins()
  });
});

// GET /api/gpio/layout — get full 40-pin layout with states
router.get('/layout', (req, res) => {
  try {
    const layout = gpioService.getPinLayout();
    res.json(layout);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/gpio/configure — configure a pin { gpio, direction }
router.post('/configure', (req, res) => {
  try {
    const { gpio, direction } = req.body;
    if (gpio === undefined || !direction) {
      return res.status(400).json({ error: 'gpio and direction are required' });
    }
    const result = gpioService.configurePin(parseInt(gpio, 10), direction);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/gpio/read/:gpio — read a pin value
router.get('/read/:gpio', (req, res) => {
  try {
    const gpio = parseInt(req.params.gpio, 10);
    const result = gpioService.readPin(gpio);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/gpio/write — write a pin value { gpio, value }
router.post('/write', (req, res) => {
  try {
    const { gpio, value } = req.body;
    if (gpio === undefined || value === undefined) {
      return res.status(400).json({ error: 'gpio and value are required' });
    }
    const result = gpioService.writePin(parseInt(gpio, 10), parseInt(value, 10));
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/gpio/release — release a pin { gpio }
router.post('/release', (req, res) => {
  try {
    const { gpio } = req.body;
    if (gpio === undefined) return res.status(400).json({ error: 'gpio is required' });
    const result = gpioService.releasePin(parseInt(gpio, 10));
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
