"""System service — system info for the dashboard."""

import os
import platform


def get_system_info() -> dict:
    """Return basic system information."""
    try:
        load_1, load_5, load_15 = os.getloadavg()
    except (OSError, AttributeError):
        load_1 = load_5 = load_15 = 0.0

    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "load_1m": round(load_1, 2),
        "load_5m": round(load_5, 2),
        "load_15m": round(load_15, 2),
    }
