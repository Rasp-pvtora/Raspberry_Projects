require('dotenv').config();
const express = require('express');
const session = require('express-session');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const fs = require('fs');
const http = require('http');
const https = require('https');
const WebSocket = require('ws');

const authMiddleware = require('./src/middleware/auth');
const authRoutes = require('./src/routes/auth');
const systemRoutes = require('./src/routes/system');
const torRoutes = require('./src/routes/tor');
const apRoutes = require('./src/routes/access-point');
const gpioRoutes = require('./src/routes/gpio');
const filesRoutes = require('./src/routes/files');
const settingsRoutes = require('./src/routes/settings');
const systemService = require('./src/services/system-service');

const app = express();

// --- HTTPS / HTTP server selection ---
const HTTPS_ENABLED = (process.env.HTTPS_ENABLED || 'false') === 'true';
const HTTPS_CERT_PATH = process.env.HTTPS_CERT_PATH || path.join(__dirname, 'certs', 'cert.pem');
const HTTPS_KEY_PATH = process.env.HTTPS_KEY_PATH || path.join(__dirname, 'certs', 'key.pem');

let server;
if (HTTPS_ENABLED) {
  // Check if cert files exist; if not, generate self-signed
  if (!fs.existsSync(HTTPS_CERT_PATH) || !fs.existsSync(HTTPS_KEY_PATH)) {
    console.log('  HTTPS enabled but no certificates found. Generating self-signed certificate...');
    const selfsigned = require('selfsigned');
    const attrs = [{ name: 'commonName', value: 'TorSecurityNode' }];
    const pems = selfsigned.generate(attrs, {
      keySize: 2048,
      days: 365,
      algorithm: 'sha256'
    });
    const certDir = path.dirname(HTTPS_CERT_PATH);
    fs.mkdirSync(certDir, { recursive: true });
    fs.writeFileSync(HTTPS_CERT_PATH, pems.cert, 'utf8');
    fs.writeFileSync(HTTPS_KEY_PATH, pems.private, 'utf8');
    console.log(`  Certificates saved to ${certDir}/`);
  }
  const httpsOptions = {
    cert: fs.readFileSync(HTTPS_CERT_PATH, 'utf8'),
    key: fs.readFileSync(HTTPS_KEY_PATH, 'utf8')
  };
  server = https.createServer(httpsOptions, app);
  console.log('  HTTPS mode enabled');
} else {
  server = http.createServer(app);
}
const wss = new WebSocket.Server({ noServer: true });

// --- View engine ---
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// --- Security middleware ---
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"],
      fontSrc: ["'self'", "https://cdnjs.cloudflare.com"],
      imgSrc: ["'self'", "data:"],
      connectSrc: ["'self'", "ws:", "wss:"]
    }
  }
}));

// Rate-limit login attempts
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  message: 'Too many login attempts. Try again in 15 minutes.'
});

// --- Body parsers ---
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// --- Static files ---
app.use(express.static(path.join(__dirname, 'public')));

// --- Session ---
const sessionMiddleware = session({
  secret: process.env.SESSION_SECRET || 'change-this-secret',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: HTTPS_ENABLED,
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000,
    sameSite: 'lax'
  }
});
app.use(sessionMiddleware);

// --- Auth routes (public) ---
app.use('/auth', loginLimiter, authRoutes);

// --- Page routes (protected) ---
app.get('/login', (req, res) => {
  if (req.session && req.session.authenticated) return res.redirect('/');
  res.render('login', { error: null });
});

app.get('/', authMiddleware, (req, res) => res.render('dashboard', { page: 'dashboard' }));
app.get('/tor-website', authMiddleware, (req, res) => res.render('tor-website', { page: 'tor-website' }));
app.get('/system', authMiddleware, (req, res) => res.render('system', { page: 'system' }));
app.get('/access-point', authMiddleware, (req, res) => res.render('access-point', { page: 'access-point' }));
app.get('/gpio', authMiddleware, (req, res) => res.render('gpio', { page: 'gpio' }));
app.get('/file-browser', authMiddleware, (req, res) => res.render('file-browser', { page: 'file-browser' }));
app.get('/settings', authMiddleware, (req, res) => res.render('settings', { page: 'settings' }));

// --- API routes (protected) ---
app.use('/api/system', authMiddleware, systemRoutes);
app.use('/api/tor', authMiddleware, torRoutes);
app.use('/api/ap', authMiddleware, apRoutes);
app.use('/api/gpio', authMiddleware, gpioRoutes);
app.use('/api/files', authMiddleware, filesRoutes);
app.use('/api/settings', authMiddleware, settingsRoutes);

// --- WebSocket upgrade (session-authenticated) ---
server.on('upgrade', (request, socket, head) => {
  sessionMiddleware(request, {}, () => {
    if (!request.session || !request.session.authenticated) {
      socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
      socket.destroy();
      return;
    }
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request);
    });
  });
});

wss.on('connection', (ws) => {
  const interval = setInterval(async () => {
    try {
      const stats = await systemService.getQuickStats();
      ws.send(JSON.stringify({ type: 'system-stats', data: stats }));
    } catch (_) { /* client disconnected */ }
  }, 2000);

  ws.on('close', () => clearInterval(interval));
  ws.on('error', () => clearInterval(interval));
});

// --- 404 handler ---
app.use((req, res) => {
  res.status(404).render('login', { error: 'Page not found. Please log in.' });
});

// --- Start server ---
const PORT = parseInt(process.env.PORT, 10) || 3000;
const HOST = process.env.HOST || '0.0.0.0';

server.listen(PORT, HOST, () => {
  const scheme = HTTPS_ENABLED ? 'https' : 'http';
  console.log(`\n  Tor Security Node running at ${scheme}://${HOST}:${PORT}\n`);
});

module.exports = { app, server };
