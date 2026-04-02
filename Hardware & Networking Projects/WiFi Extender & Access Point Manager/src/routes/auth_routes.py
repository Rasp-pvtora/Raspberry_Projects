"""Authentication routes — login, logout, password change."""

from flask import Blueprint, request, jsonify, render_template, make_response, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.auth import hash_password, verify_password, generate_token, require_auth
import os

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')


@bp.route('/api/auth/login', methods=['POST'])
def login():
    db = _get_service('db')
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password required'}), 400

    user = db.get_user_by_username(data['username'])
    if not user or not verify_password(data['password'], user['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = generate_token(user['id'])
    db.update_last_login(user['id'])

    response = make_response(jsonify({
        'token': token,
        'expires_in': int(os.getenv('AUTH_SESSION_HOURS', '24')) * 3600,
        'user': {'id': user['id'], 'username': user['username'], 'role': user['role']},
    }))
    response.set_cookie(
        'token', token,
        httponly=True,
        samesite='Lax',
        max_age=int(os.getenv('AUTH_SESSION_HOURS', '24')) * 3600,
    )
    return response


@bp.route('/api/auth/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out'}))
    response.delete_cookie('token')
    return response


@bp.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    db = _get_service('db')
    data = request.get_json()
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({'error': 'Current and new passwords required'}), 400

    user = db.get_user_by_id(request.user_id)
    if not verify_password(data['current_password'], user['password_hash']):
        return jsonify({'error': 'Current password is incorrect'}), 401

    new_pass = data['new_password']
    if len(new_pass) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    db.update_user_password(request.user_id, hash_password(new_pass))
    return jsonify({'message': 'Password updated'})


def _get_service(name):
    from flask import current_app
    return current_app.config['services'][name]
