"""Authentication routes — login, logout, session management."""

import os
import time
import functools
from collections import defaultdict

import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth_bp = Blueprint("auth", __name__)

# ---------------------------------------------------------------------------
# Rate limiting (in-memory per IP)
# ---------------------------------------------------------------------------
_login_attempts: dict[str, list] = defaultdict(list)
_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW = 15 * 60  # 15 minutes


def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < _RATE_LIMIT_WINDOW]
    return len(_login_attempts[ip]) >= _RATE_LIMIT_MAX


def _record_attempt(ip: str) -> None:
    _login_attempts[ip].append(time.time())


# ---------------------------------------------------------------------------
# Auth decorator
# ---------------------------------------------------------------------------
def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------
def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# Lazy-init: hash on first login check so we don't hash at import time.
_cached_hash: str | None = None


def _get_admin_hash() -> str:
    global _cached_hash
    if _cached_hash is None:
        _cached_hash = _hash_password(os.getenv("ADMIN_PASSWORD", "changeme"))
    return _cached_hash


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    ip = request.remote_addr or "unknown"
    if _is_rate_limited(ip):
        flash("Too many login attempts. Try again later.", "error")
        return render_template("login.html"), 429

    username = request.form.get("username", "")
    password = request.form.get("password", "")
    admin_user = os.getenv("ADMIN_USERNAME", "admin")

    if username == admin_user and _check_password(password, _get_admin_hash()):
        session.permanent = True
        session["logged_in"] = True
        session["username"] = username
        return redirect(url_for("dashboard.dashboard_page"))

    _record_attempt(ip)
    flash("Invalid credentials.", "error")
    return render_template("login.html"), 401


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
