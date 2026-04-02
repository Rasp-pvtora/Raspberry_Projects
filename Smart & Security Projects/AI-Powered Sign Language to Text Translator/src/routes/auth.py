"""Authentication routes — login, logout, session management."""

import os
import time
from functools import wraps

import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth_bp = Blueprint("auth", __name__)

# Rate limiting storage: {ip: [timestamps]}
_login_attempts: dict[str, list[float]] = {}
RATE_LIMIT = 10
RATE_WINDOW = 900  # 15 minutes


def _check_rate_limit(ip: str) -> bool:
    """Return True if the IP is rate-limited."""
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < RATE_WINDOW]
    _login_attempts[ip] = attempts
    return len(attempts) >= RATE_LIMIT


def _record_attempt(ip: str):
    _login_attempts.setdefault(ip, []).append(time.time())


def login_required(f):
    """Decorator — redirect to login if not authenticated. Kiosk mode bypasses."""
    @wraps(f)
    def decorated(*args, **kwargs):
        kiosk = os.getenv("KIOSK_MODE", "false").lower() == "true"
        if kiosk or session.get("logged_in"):
            return f(*args, **kwargs)
        return redirect(url_for("auth.login"))
    return decorated


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    ip = request.remote_addr
    if _check_rate_limit(ip):
        flash("Too many login attempts. Please try again later.", "error")
        return render_template("login.html"), 429

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "changeme")

    # Compare with bcrypt if stored hash, otherwise plain (first-run default)
    valid = False
    if admin_pass.startswith("$2b$"):
        valid = username == admin_user and bcrypt.checkpw(
            password.encode("utf-8"), admin_pass.encode("utf-8")
        )
    else:
        valid = username == admin_user and password == admin_pass

    if valid:
        session["logged_in"] = True
        session["username"] = username
        session.permanent = True
        return redirect(url_for("dashboard.dashboard_page"))

    _record_attempt(ip)
    flash("Invalid credentials.", "error")
    return render_template("login.html"), 401


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
