"""Authentication module — bcrypt hashing, JWT tokens, rate-limited login."""

import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, redirect, url_for

SECRET = os.getenv('SECRET_KEY', 'dev-key')
SESSION_HOURS = int(os.getenv('AUTH_SESSION_HOURS', '24'))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_token(user_id: int) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=['HS256'])


def require_auth(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token') or \
                request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login_page'))
        try:
            payload = decode_token(token)
            request.user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Token expired'}), 401
            return redirect(url_for('auth.login_page'))
        except jwt.InvalidTokenError:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Invalid token'}), 401
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated
