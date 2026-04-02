"""Dashboard routes — main dashboard, kiosk mode."""

import os

from flask import Blueprint, render_template

from src.routes.auth import login_required
from src.services.system_service import get_system_info

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html", system=get_system_info())


@dashboard_bp.route("/kiosk")
def kiosk():
    kiosk_enabled = os.getenv("KIOSK_MODE", "false").lower() == "true"
    timeout = int(os.getenv("KIOSK_TIMEOUT_SEC", "60"))
    return render_template("kiosk.html", kiosk_enabled=kiosk_enabled, timeout=timeout)
