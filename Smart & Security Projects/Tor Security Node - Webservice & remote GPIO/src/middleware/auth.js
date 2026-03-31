/**
 * Session-based authentication middleware.
 * Redirects to /login for page requests, returns 401 for API requests.
 */
module.exports = function authMiddleware(req, res, next) {
  if (req.session && req.session.authenticated) {
    return next();
  }

  if (req.path.startsWith('/api/')) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  return res.redirect('/login');
};
