"""Notification service — sends alerts via Telegram, Slack, and email."""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL', '')
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_pass = os.getenv('SMTP_PASS', '')
        self.smtp_to = os.getenv('SMTP_TO', '')

    def notify(self, title, message, channels=None):
        """Send notification to all configured channels."""
        if channels is None:
            channels = ['telegram', 'slack', 'email']

        results = {}
        for channel in channels:
            try:
                if channel == 'telegram' and self.telegram_token:
                    self._send_telegram(title, message)
                    results['telegram'] = True
                elif channel == 'slack' and self.slack_webhook:
                    self._send_slack(title, message)
                    results['slack'] = True
                elif channel == 'email' and self.smtp_user:
                    self._send_email(title, message)
                    results['email'] = True
            except Exception:
                logger.exception("Failed to send %s notification", channel)
                results[channel] = False
        return results

    def _send_telegram(self, title, message):
        """Send Telegram notification."""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': f"*{title}*\n{message}",
                'parse_mode': 'Markdown',
            }
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Telegram notification sent: %s", title)
        except ImportError:
            # Fallback: use urllib
            import urllib.request
            import json
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = json.dumps({
                'chat_id': self.telegram_chat_id,
                'text': f"*{title}*\n{message}",
                'parse_mode': 'Markdown',
            }).encode('utf-8')
            req = urllib.request.Request(
                url, data=data,
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=10)
            logger.info("Telegram notification sent: %s", title)

    def _send_slack(self, title, message):
        """Send Slack webhook notification."""
        try:
            import requests
            payload = {
                'text': f"*{title}*\n{message}",
            }
            resp = requests.post(self.slack_webhook, json=payload, timeout=10)
            resp.raise_for_status()
        except ImportError:
            import urllib.request
            import json
            data = json.dumps({'text': f"*{title}*\n{message}"}).encode('utf-8')
            req = urllib.request.Request(
                self.slack_webhook, data=data,
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=10)
        logger.info("Slack notification sent: %s", title)

    def _send_email(self, title, message):
        """Send email notification via SMTP."""
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = self.smtp_to
        msg['Subject'] = f"[WiFi AP Manager] {title}"
        msg.attach(MIMEText(message, 'plain'))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
        logger.info("Email notification sent: %s", title)

    # ── Predefined alert types ──

    def alert_new_client(self, hostname, mac, ip):
        self.notify(
            "New Client Connected",
            f"Device: {hostname or 'Unknown'}\nMAC: {mac}\nIP: {ip}"
        )

    def alert_client_disconnected(self, hostname, mac):
        self.notify(
            "Client Disconnected",
            f"Device: {hostname or 'Unknown'}\nMAC: {mac}"
        )

    def alert_health_down(self, latency_ms, packet_loss_pct):
        self.notify(
            "Internet Health Alert",
            f"Latency: {latency_ms}ms\nPacket Loss: {packet_loss_pct}%"
        )

    def alert_bandwidth_cap(self, mac, rx_kbps, tx_kbps):
        self.notify(
            "Bandwidth Cap Exceeded",
            f"MAC: {mac}\nDownload: {rx_kbps} kbps\nUpload: {tx_kbps} kbps"
        )
