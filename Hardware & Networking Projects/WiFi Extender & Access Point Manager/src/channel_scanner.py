"""Channel scanner — scans WiFi channels and selects the least congested one."""

import subprocess
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class ChannelScanner:
    # Valid channels per band
    CHANNELS_24GHZ = list(range(1, 14))
    CHANNELS_5GHZ = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112,
                     116, 120, 124, 128, 132, 136, 140, 149, 153, 157, 161, 165]

    def __init__(self, interface='wlan0'):
        self.interface = interface

    def scan(self):
        """Scan for nearby APs and return channel usage info."""
        try:
            result = subprocess.run(
                ['iw', 'dev', self.interface, 'scan'],
                capture_output=True, text=True, timeout=30
            )
            return self._parse_scan(result.stdout)
        except subprocess.TimeoutExpired:
            logger.error("WiFi scan timed out")
            return []
        except subprocess.CalledProcessError as e:
            logger.error("WiFi scan failed: %s", e)
            return []

    def _parse_scan(self, output):
        """Parse iw scan output into list of nearby APs."""
        aps = []
        current = {}
        for line in output.splitlines():
            line = line.strip()
            if line.startswith('BSS '):
                if current:
                    aps.append(current)
                mac_match = re.match(r'BSS\s+([0-9a-fA-F:]+)', line)
                current = {'bssid': mac_match.group(1) if mac_match else ''}
            elif 'SSID:' in line:
                current['ssid'] = line.split('SSID:', 1)[1].strip()
            elif 'freq:' in line:
                m = re.search(r'(\d+)', line)
                if m:
                    current['frequency'] = int(m.group(1))
            elif 'signal:' in line:
                m = re.search(r'(-?\d+\.?\d*)', line)
                if m:
                    current['signal_dbm'] = float(m.group(1))
            elif 'DS Parameter set: channel' in line:
                m = re.search(r'channel\s+(\d+)', line)
                if m:
                    current['channel'] = int(m.group(1))
        if current:
            aps.append(current)
        return aps

    def get_channel_usage(self):
        """Get channel usage counts from scan data."""
        aps = self.scan()
        channel_counts = Counter()
        for ap in aps:
            if 'channel' in ap:
                channel_counts[ap['channel']] += 1
        return dict(channel_counts)

    def get_best_channel(self, band='2.4'):
        """Find the least congested channel."""
        usage = self.get_channel_usage()
        channels = self.CHANNELS_24GHZ if band == '2.4' else self.CHANNELS_5GHZ

        # Score each channel (lower is better)
        scores = {}
        for ch in channels:
            # Direct usage count
            score = usage.get(ch, 0) * 3
            # Adjacent channel interference (2.4 GHz only)
            if band == '2.4':
                for offset in [-2, -1, 1, 2]:
                    adj = ch + offset
                    score += usage.get(adj, 0)
            scores[ch] = score

        best = min(scores, key=scores.get)
        logger.info("Best %s GHz channel: %d (score: %d)", band, best, scores[best])
        return best

    @staticmethod
    def freq_to_channel(freq):
        """Convert frequency (MHz) to channel number."""
        if 2412 <= freq <= 2472:
            return (freq - 2407) // 5
        elif freq == 2484:
            return 14
        elif 5180 <= freq <= 5825:
            return (freq - 5000) // 5
        return 0
