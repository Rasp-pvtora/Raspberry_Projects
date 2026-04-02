"""Optional alert channels (webhook)."""

import os
import requests


class AlertService:
    """Send alerts via webhook when configured."""

    def __init__(self):
        self.enabled = os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true"
        self.webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")

    def send(self, title: str, message: str) -> bool:
        if not self.enabled or not self.webhook_url:
            return False
        try:
            resp = requests.post(
                self.webhook_url,
                json={"title": title, "message": message},
                timeout=10,
            )
            return resp.ok
        except Exception:
            return False
