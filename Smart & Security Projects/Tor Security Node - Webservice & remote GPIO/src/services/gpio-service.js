const fs = require('fs');
const path = require('path');

const GPIO_ENABLED = (process.env.GPIO_ENABLED || 'true') === 'true';
const GPIO_PRESET_FILE = process.env.GPIO_PRESET_FILE || path.join(__dirname, '../../gpio-presets/rpi4b.json');

let Gpio;
try {
  if (GPIO_ENABLED) {
    Gpio = require('onoff').Gpio;
  }
} catch (_) {
  Gpio = null;
}

// Track active GPIO pin objects
const activePins = {};

// Load pin layout from preset file
let PRESET = null;
let PIN_LAYOUT = {};

function loadPreset() {
  try {
    const presetPath = path.resolve(GPIO_PRESET_FILE);
    const raw = fs.readFileSync(presetPath, 'utf8');
    PRESET = JSON.parse(raw);
    PIN_LAYOUT = {};
    for (const [pin, info] of Object.entries(PRESET.pinLayout)) {
      PIN_LAYOUT[pin] = { gpio: info.gpio, name: info.name, type: info.type };
    }
    return PRESET;
  } catch (err) {
    console.error(`Failed to load GPIO preset from ${GPIO_PRESET_FILE}: ${err.message}`);
    // Fallback to hardcoded Pi 4 layout
    PIN_LAYOUT = getFallbackLayout();
    PRESET = { name: 'Fallback (Pi 4 B)', model: 'rpi4b', description: 'Hardcoded fallback layout', pinLayout: PIN_LAYOUT, defaultConfigurations: [] };
    return PRESET;
  }
}

function getFallbackLayout() {
  return {
  1:  { gpio: null, name: '3.3V',  type: 'power' },
  2:  { gpio: null, name: '5V',    type: 'power' },
  3:  { gpio: 2,    name: 'GPIO2 (SDA1)',  type: 'gpio' },
  4:  { gpio: null, name: '5V',    type: 'power' },
  5:  { gpio: 3,    name: 'GPIO3 (SCL1)',  type: 'gpio' },
  6:  { gpio: null, name: 'GND',   type: 'ground' },
  7:  { gpio: 4,    name: 'GPIO4',  type: 'gpio' },
  8:  { gpio: 14,   name: 'GPIO14 (TXD)', type: 'gpio' },
  9:  { gpio: null, name: 'GND',   type: 'ground' },
  10: { gpio: 15,   name: 'GPIO15 (RXD)', type: 'gpio' },
  11: { gpio: 17,   name: 'GPIO17', type: 'gpio' },
  12: { gpio: 18,   name: 'GPIO18 (PWM0)', type: 'gpio' },
  13: { gpio: 27,   name: 'GPIO27', type: 'gpio' },
  14: { gpio: null, name: 'GND',   type: 'ground' },
  15: { gpio: 22,   name: 'GPIO22', type: 'gpio' },
  16: { gpio: 23,   name: 'GPIO23', type: 'gpio' },
  17: { gpio: null, name: '3.3V',  type: 'power' },
  18: { gpio: 24,   name: 'GPIO24', type: 'gpio' },
  19: { gpio: 10,   name: 'GPIO10 (MOSI)', type: 'gpio' },
  20: { gpio: null, name: 'GND',   type: 'ground' },
  21: { gpio: 9,    name: 'GPIO9 (MISO)', type: 'gpio' },
  22: { gpio: 25,   name: 'GPIO25', type: 'gpio' },
  23: { gpio: 11,   name: 'GPIO11 (SCLK)', type: 'gpio' },
  24: { gpio: 8,    name: 'GPIO8 (CE0)',  type: 'gpio' },
  25: { gpio: null, name: 'GND',   type: 'ground' },
  26: { gpio: 7,    name: 'GPIO7 (CE1)',  type: 'gpio' },
  27: { gpio: 0,    name: 'GPIO0 (ID_SD)', type: 'gpio' },
  28: { gpio: 1,    name: 'GPIO1 (ID_SC)', type: 'gpio' },
  29: { gpio: 5,    name: 'GPIO5',  type: 'gpio' },
  30: { gpio: null, name: 'GND',   type: 'ground' },
  31: { gpio: 6,    name: 'GPIO6',  type: 'gpio' },
  32: { gpio: 12,   name: 'GPIO12 (PWM0)', type: 'gpio' },
  33: { gpio: 13,   name: 'GPIO13 (PWM1)', type: 'gpio' },
  34: { gpio: null, name: 'GND',   type: 'ground' },
  35: { gpio: 19,   name: 'GPIO19 (MISO)', type: 'gpio' },
  36: { gpio: 16,   name: 'GPIO16', type: 'gpio' },
  37: { gpio: 26,   name: 'GPIO26', type: 'gpio' },
  38: { gpio: 20,   name: 'GPIO20 (MOSI)', type: 'gpio' },
  39: { gpio: null, name: 'GND',   type: 'ground' },
  40: { gpio: 21,   name: 'GPIO21 (SCLK)', type: 'gpio' }
  };
}

// Load preset on startup
loadPreset();

/**
 * Check if GPIO is available on this system.
 */
function isAvailable() {
  return GPIO_ENABLED && Gpio !== null;
}

/**
 * Get the full pin layout with current states.
 */
function getPinLayout() {
  const layout = {};
  for (const [pin, info] of Object.entries(PIN_LAYOUT)) {
    const state = { ...info, physical: parseInt(pin, 10) };
    if (info.type === 'gpio' && info.gpio !== null) {
      const active = activePins[info.gpio];
      if (active) {
        state.direction = active.direction;
        state.value = active.pin ? active.pin.readSync() : 0;
        state.active = true;
      } else {
        state.direction = null;
        state.value = null;
        state.active = false;
      }
    }
    layout[pin] = state;
  }
  return layout;
}

/**
 * Configure a GPIO pin as input or output.
 */
function configurePin(gpioNum, direction) {
  if (!isAvailable()) throw new Error('GPIO not available on this system');
  if (!['in', 'out'].includes(direction)) throw new Error('Direction must be "in" or "out"');

  // Validate the GPIO number exists in our layout
  const valid = Object.values(PIN_LAYOUT).some(p => p.gpio === gpioNum && p.type === 'gpio');
  if (!valid) throw new Error(`GPIO ${gpioNum} is not a valid GPIO pin`);

  // Clean up existing pin if already configured
  if (activePins[gpioNum] && activePins[gpioNum].pin) {
    activePins[gpioNum].pin.unexport();
  }

  try {
    const pin = new Gpio(gpioNum, direction);
    activePins[gpioNum] = { pin, direction };
    return { gpio: gpioNum, direction, value: pin.readSync() };
  } catch (err) {
    // If hardware GPIO fails, use mock mode
    activePins[gpioNum] = { pin: null, direction, mockValue: 0 };
    return { gpio: gpioNum, direction, value: 0, mock: true };
  }
}

/**
 * Read the value of a configured GPIO pin.
 */
function readPin(gpioNum) {
  const active = activePins[gpioNum];
  if (!active) throw new Error(`GPIO ${gpioNum} is not configured. Configure it first.`);

  if (active.pin) {
    return { gpio: gpioNum, value: active.pin.readSync() };
  }
  return { gpio: gpioNum, value: active.mockValue || 0, mock: true };
}

/**
 * Write a value to a configured output GPIO pin.
 */
function writePin(gpioNum, value) {
  const active = activePins[gpioNum];
  if (!active) throw new Error(`GPIO ${gpioNum} is not configured. Configure it first.`);
  if (active.direction !== 'out') throw new Error(`GPIO ${gpioNum} is configured as input, not output`);

  const val = value ? 1 : 0;
  if (active.pin) {
    active.pin.writeSync(val);
  } else {
    active.mockValue = val;
  }
  return { gpio: gpioNum, value: val, mock: !active.pin };
}

/**
 * Release a configured GPIO pin.
 */
function releasePin(gpioNum) {
  const active = activePins[gpioNum];
  if (!active) return { gpio: gpioNum, released: false };

  if (active.pin) {
    active.pin.unexport();
  }
  delete activePins[gpioNum];
  return { gpio: gpioNum, released: true };
}

/**
 * Release all configured pins.
 */
function releaseAll() {
  for (const gpioNum of Object.keys(activePins)) {
    if (activePins[gpioNum].pin) {
      activePins[gpioNum].pin.unexport();
    }
    delete activePins[gpioNum];
  }
}

/**
 * Get list of currently configured pins.
 */
function getActivePins() {
  const result = [];
  for (const [gpioNum, info] of Object.entries(activePins)) {
    const value = info.pin ? info.pin.readSync() : (info.mockValue || 0);
    result.push({
      gpio: parseInt(gpioNum, 10),
      direction: info.direction,
      value,
      mock: !info.pin
    });
  }
  return result;
}

// Clean up all pins on process exit
process.on('SIGINT', () => { releaseAll(); process.exit(); });
process.on('SIGTERM', () => { releaseAll(); process.exit(); });

/**
 * Get currently loaded preset info.
 */
function getPresetInfo() {
  return {
    name: PRESET ? PRESET.name : 'Unknown',
    model: PRESET ? PRESET.model : 'unknown',
    description: PRESET ? PRESET.description : '',
    file: GPIO_PRESET_FILE,
    defaultConfigurations: PRESET ? (PRESET.defaultConfigurations || []) : []
  };
}

/**
 * List all available preset files in the gpio-presets directory.
 */
function listPresets() {
  const presetsDir = path.join(__dirname, '../../gpio-presets');
  try {
    const files = fs.readdirSync(presetsDir).filter(f => f.endsWith('.json'));
    return files.map(f => {
      try {
        const raw = fs.readFileSync(path.join(presetsDir, f), 'utf8');
        const preset = JSON.parse(raw);
        return { file: f, name: preset.name, model: preset.model, description: preset.description };
      } catch (_) {
        return { file: f, name: f, model: '', description: 'Parse error' };
      }
    });
  } catch (_) {
    return [];
  }
}

/**
 * Apply default pin configurations from the preset.
 */
function applyPresetDefaults() {
  if (!PRESET || !PRESET.defaultConfigurations) return [];
  const results = [];
  for (const config of PRESET.defaultConfigurations) {
    try {
      const result = configurePin(config.gpio, config.direction);
      results.push({ ...result, label: config.label || '' });
    } catch (err) {
      results.push({ gpio: config.gpio, error: err.message });
    }
  }
  return results;
}

module.exports = {
  isAvailable,
  getPinLayout,
  configurePin,
  readPin,
  writePin,
  releasePin,
  releaseAll,
  getActivePins,
  getPresetInfo,
  listPresets,
  loadPreset,
  applyPresetDefaults,
  PIN_LAYOUT
};
