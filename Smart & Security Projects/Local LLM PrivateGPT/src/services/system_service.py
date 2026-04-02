"""System info — CPU temperature, RAM usage, disk usage."""

import os
import platform
import shutil


def get_system_info() -> dict:
    """Return a dict of system metrics."""
    info: dict = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_temp": _get_cpu_temp(),
        "ram": _get_ram(),
        "disk": _get_disk(),
    }
    return info


def _get_cpu_temp() -> str:
    """Read CPU temperature on Raspberry Pi (Linux)."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_milli = int(f.read().strip())
        return f"{temp_milli / 1000:.1f} °C"
    except Exception:
        return "N/A"


def _get_ram() -> dict:
    """Return RAM usage as a dict."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "total_mb": round(mem.total / 1024 / 1024),
            "used_mb": round(mem.used / 1024 / 1024),
            "percent": mem.percent,
        }
    except ImportError:
        return {"total_mb": 0, "used_mb": 0, "percent": 0}


def _get_disk() -> dict:
    """Return disk usage for the data directory."""
    data_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    try:
        usage = shutil.disk_usage(os.path.dirname(data_dir))
        return {
            "total_gb": round(usage.total / 1024 / 1024 / 1024, 1),
            "used_gb": round(usage.used / 1024 / 1024 / 1024, 1),
            "free_gb": round(usage.free / 1024 / 1024 / 1024, 1),
            "percent": round(usage.used / usage.total * 100, 1),
        }
    except Exception:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}
