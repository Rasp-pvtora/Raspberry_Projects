const express = require('express');
const bcrypt = require('bcrypt');
const router = express.Router();

const SALT_ROUNDS = 10;
let passwordHash = null;

// Hash the password from .env on first use
async function getHash() {
  if (!passwordHash) {
    const pw = process.env.ADMIN_PASSWORD || 'changeme';
    passwordHash = await bcrypt.hash(pw, SALT_ROUNDS);
  }
  return passwordHash;
}

// POST /auth/login
router.post('/login', async (req, res) => {
  const { username, password } = req.body;
  const expectedUser = process.env.ADMIN_USERNAME || 'admin';

  if (!username || !password) {
    return res.render('login', { error: 'Username and password are required.' });
  }

  if (username !== expectedUser) {
    return res.render('login', { error: 'Invalid credentials.' });
  }

  // Compare against current .env password (or updated hash)
  const currentPassword = process.env.ADMIN_PASSWORD || 'changeme';
  if (password !== currentPassword) {
    return res.render('login', { error: 'Invalid credentials.' });
  }

  req.session.authenticated = true;
  req.session.username = username;
  res.redirect('/');
});

// GET /auth/logout
router.get('/logout', (req, res) => {
  req.session.destroy(() => {
    res.redirect('/login');
  });
});

module.exports = router;
