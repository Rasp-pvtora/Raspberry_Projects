"""Tests for authentication module."""

import pytest
from src.auth import hash_password, verify_password, generate_token, decode_token


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = 'SecureP@ss123'
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password('correct')
        assert not verify_password('wrong', hashed)

    def test_hash_is_unique(self):
        p1 = hash_password('same_password')
        p2 = hash_password('same_password')
        assert p1 != p2  # Different salts


class TestJWT:
    def test_generate_and_decode(self):
        token = generate_token(42)
        payload = decode_token(token)
        assert payload['user_id'] == 42

    def test_expired_token(self):
        import jwt
        from datetime import datetime, timedelta, timezone
        import os

        payload = {
            'user_id': 1,
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, os.getenv('SECRET_KEY', 'test-secret-key'), algorithm='HS256')
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(token)

    def test_invalid_token(self):
        import jwt
        with pytest.raises(jwt.InvalidTokenError):
            decode_token('not-a-valid-token')


class TestLoginAPI:
    def test_login_success(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'testpass',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'token' in data
        assert data['user']['username'] == 'admin'

    def test_login_wrong_password(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'wrong',
        })
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post('/api/auth/login', json={'username': 'admin'})
        assert resp.status_code == 400

    def test_login_nonexistent_user(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'nobody',
            'password': 'pass',
        })
        assert resp.status_code == 401

    def test_logout(self, auth_client):
        resp = auth_client.post('/api/auth/logout')
        assert resp.status_code == 200

    def test_change_password(self, auth_client):
        resp = auth_client.post('/api/auth/change-password', json={
            'current_password': 'testpass',
            'new_password': 'newsecure123',
        })
        assert resp.status_code == 200

    def test_change_password_wrong_current(self, auth_client):
        resp = auth_client.post('/api/auth/change-password', json={
            'current_password': 'wrong',
            'new_password': 'newsecure123',
        })
        assert resp.status_code == 401

    def test_change_password_too_short(self, auth_client):
        resp = auth_client.post('/api/auth/change-password', json={
            'current_password': 'testpass',
            'new_password': 'short',
        })
        assert resp.status_code == 400
