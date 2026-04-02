"""Bandwidth tracker — monitors per-client and total bandwidth using iptables counters."""

import subprocess
import re
import time
import threading
import logging

logger = logging.getLogger(__name__)


class BandwidthTracker:
    def __init__(self, db, ws_callback=None, interval=5):
        self.db = db
        self.ws = ws_callback
        self.interval = interval
        self.previous = {}
        self.running = False
        self._thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._track_loop, daemon=True)
        self._thread.start()
        logger.info("Bandwidth tracker started (interval=%ds)", self.interval)

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=self.interval + 2)

    def _track_loop(self):
        while self.running:
            try:
                current = self._read_counters()
                rates = self._calculate_rates(current)
                if rates:
                    self._store_and_broadcast(rates)
                self.previous = current
            except Exception:
                logger.exception("Bandwidth tracking error")
            time.sleep(self.interval)

    def _read_counters(self):
        """Read iptables byte counters per IP from FORWARD chain."""
        counters = {}
        try:
            result = subprocess.run(
                ['iptables', '-L', 'FORWARD', '-v', '-n', '-x'],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 9:
                    try:
                        bytes_count = int(parts[1])
                        src_ip = parts[7]
                        dst_ip = parts[8]
                        # Track by destination IP (download) and source IP (upload)
                        if re.match(r'10\.0\.0\.\d+', dst_ip):
                            counters.setdefault(dst_ip, {'rx': 0, 'tx': 0})
                            counters[dst_ip]['rx'] += bytes_count
                        if re.match(r'10\.0\.0\.\d+', src_ip):
                            counters.setdefault(src_ip, {'rx': 0, 'tx': 0})
                            counters[src_ip]['tx'] += bytes_count
                    except (ValueError, IndexError):
                        continue
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            logger.error("Failed to read iptables counters")
        return counters

    def _calculate_rates(self, current):
        rates = {}
        for ip, data in current.items():
            if ip in self.previous:
                rx_diff = max(0, data['rx'] - self.previous[ip]['rx'])
                tx_diff = max(0, data['tx'] - self.previous[ip]['tx'])
                rates[ip] = {
                    'rx_bytes': data['rx'],
                    'tx_bytes': data['tx'],
                    'rx_kbps': round(rx_diff * 8 / self.interval / 1000, 2),
                    'tx_kbps': round(tx_diff * 8 / self.interval / 1000, 2),
                }
        return rates

    def _store_and_broadcast(self, rates):
        total_rx_kbps = 0
        total_tx_kbps = 0
        client_rates = []

        for ip, data in rates.items():
            total_rx_kbps += data['rx_kbps']
            total_tx_kbps += data['tx_kbps']
            client_rates.append({
                'ip': ip,
                'rx_kbps': data['rx_kbps'],
                'tx_kbps': data['tx_kbps'],
                'rx_bytes': data['rx_bytes'],
                'tx_bytes': data['tx_bytes'],
            })

        # Store total bandwidth
        self.db.store_bandwidth(
            client_id=None,
            rx_bytes=sum(d['rx_bytes'] for d in rates.values()),
            tx_bytes=sum(d['tx_bytes'] for d in rates.values()),
            rx_rate_kbps=round(total_rx_kbps, 2),
            tx_rate_kbps=round(total_tx_kbps, 2),
        )

        if self.ws:
            self.ws('bandwidth_update', {
                'total_rx_kbps': round(total_rx_kbps, 2),
                'total_tx_kbps': round(total_tx_kbps, 2),
                'clients': client_rates,
            })

    def get_current_rates(self):
        """Get one-off bandwidth reading."""
        current = self._read_counters()
        return self._calculate_rates(current) if self.previous else {}
