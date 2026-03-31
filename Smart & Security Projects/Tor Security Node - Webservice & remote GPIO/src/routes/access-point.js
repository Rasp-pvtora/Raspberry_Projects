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

// --- Travel Mode (WiFi-to-WiFi) ---

// GET /api/ap/usb-scan — Scan for USB WiFi adapters
router.get('/usb-scan', (req, res) => {
  try {
    const result = apService.scanUsbWifiAdapters();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/ap/wifi-networks?iface=wlan1 — Scan WiFi networks on an interface
router.get('/wifi-networks', async (req, res) => {
  try {
    const iface = req.query.iface || undefined;
    const networks = await apService.getWifiNetworks(iface);
    res.json(networks);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/ap/travel-start — Start travel mode { usbInterface, ssid, password }
router.post('/travel-start', async (req, res) => {
  try {
    const { usbInterface, ssid, password } = req.body;
    if (!usbInterface || !ssid) {
      return res.status(400).json({ error: 'usbInterface and ssid are required' });
    }
    const result = await apService.startTravelMode(usbInterface, ssid, password);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/ap/travel-stop — Stop travel mode { usbInterface }
router.post('/travel-stop', async (req, res) => {
  try {
    const { usbInterface } = req.body || {};
    const result = await apService.stopTravelMode(usbInterface);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/ap/travel-status — Get travel mode status
router.get('/travel-status', (req, res) => {
  try {
    const status = apService.getTravelModeStatus();
    res.json(status);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
