"""Health monitor — internet connectivity, latency, DNS resolution checks."""

import subprocess
import re
import time
import threading
import logging

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(self, db, ws_callback=None, check_interval=30, ping_target='1.1.1.1'):
        self.db = db
        self.ws = ws_callback
        self.interval = check_interval
        self.ping_target = ping_target
        self.running = False
        self._thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        logger.info("Health monitor started (interval=%ds, target=%s)",
                     self.interval, self.ping_target)

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=self.interval + 5)

    def _check_loop(self):
        while self.running:
            try:
                health = self.run_checks()
                self.db.store_health_check(
                    latency_ms=health['latency_ms'],
                    packet_loss_pct=health['packet_loss_pct'],
                    dns_resolve_ms=health['dns_resolve_ms'],
                    internet_up=health['internet_up'],
                )
                if self.ws:
                    self.ws('health_update', health)
            except Exception:
                logger.exception("Health check error")
            time.sleep(self.interval)

    def run_checks(self):
        """Run all health checks and return results."""
        latency = self._ping(self.ping_target)
        packet_loss = self._packet_loss(self.ping_target)
        dns_ms = self._dns_check()
        internet_up = latency >= 0 and packet_loss < 100

        return {
            'latency_ms': round(latency, 1),
            'packet_loss_pct': round(packet_loss, 1),
            'dns_resolve_ms': round(dns_ms, 1),
            'internet_up': internet_up,
        }

    def _ping(self, target, count=3):
        """Measure average latency with ping."""
        try:
            result = subprocess.run(
                ['ping', '-c', str(count), '-W', '2', target],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                return -1.0
            match = re.search(r'avg.*?=.*?/([\d.]+)/', result.stdout)
            if match:
                return float(match.group(1))
            # Try alternative format
            match = re.search(r'(\d+\.?\d*)\s*ms', result.stdout)
            return float(match.group(1)) if match else -1.0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return -1.0

    def _packet_loss(self, target, count=10):
        """Measure packet loss percentage."""
        try:
            result = subprocess.run(
                ['ping', '-c', str(count), '-W', '2', target],
                capture_output=True, text=True, timeout=30
            )
            match = re.search(r'(\d+)%\s*packet loss', result.stdout)
            return float(match.group(1)) if match else 100.0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return 100.0

    def _dns_check(self, domain='google.com'):
        """Measure DNS resolution time."""
        start = time.time()
        try:
            import dns.resolver
            dns.resolver.resolve(domain, 'A')
            return (time.time() - start) * 1000
        except ImportError:
            # Fallback: use nslookup
            try:
                subprocess.run(
                    ['nslookup', domain],
                    capture_output=True, timeout=5
                )
                return (time.time() - start) * 1000
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                return -1.0
        except Exception:
            return -1.0
