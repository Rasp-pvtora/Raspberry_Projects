"""Client monitor — discovers connected WiFi clients via iw and ARP."""

import subprocess
import re
import socket
import logging

logger = logging.getLogger(__name__)


class ClientMonitor:
    def __init__(self, interface='wlan0'):
        self.interface = interface

    def get_connected_clients(self):
        """Get list of connected WiFi clients with details."""
        clients = []
        stations = self._get_stations()
        arp = self._get_arp_table()

        for mac, info in stations.items():
            ip = arp.get(mac, {}).get('ip', 'unknown')
            hostname = self._resolve_hostname(ip) if ip != 'unknown' else ''
            clients.append({
                'mac': mac,
                'ip': ip,
                'hostname': hostname,
                'signal_dbm': info.get('signal', 0),
                'connected_time': info.get('connected_time', 0),
                'rx_bytes': info.get('rx_bytes', 0),
                'tx_bytes': info.get('tx_bytes', 0),
                'inactive_ms': info.get('inactive_ms', 0),
            })
        return clients

    def disconnect_client(self, mac_address):
        """Force disconnect a client by MAC address."""
        try:
            subprocess.run(
                ['hostapd_cli', '-i', self.interface, 'disassociate', mac_address],
                check=True, capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            logger.error("Failed to disconnect client %s", mac_address)
            return False

    def _get_stations(self):
        """Parse iw station dump output."""
        try:
            result = subprocess.run(
                ['iw', 'dev', self.interface, 'station', 'dump'],
                capture_output=True, text=True, timeout=10
            )
            return self._parse_iw_output(result.stdout)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            logger.error("Failed to get station list from iw")
            return {}

    def _parse_iw_output(self, output):
        stations = {}
        current_mac = None
        for line in output.splitlines():
            mac_match = re.match(r'Station\s+([0-9a-fA-F:]+)', line)
            if mac_match:
                current_mac = mac_match.group(1).upper()
                stations[current_mac] = {}
            elif current_mac:
                line_stripped = line.strip()
                if 'signal:' in line_stripped:
                    m = re.search(r'(-?\d+)', line_stripped)
                    if m:
                        stations[current_mac]['signal'] = int(m.group(1))
                elif 'rx bytes:' in line_stripped:
                    m = re.search(r'(\d+)', line_stripped)
                    if m:
                        stations[current_mac]['rx_bytes'] = int(m.group(1))
                elif 'tx bytes:' in line_stripped:
                    m = re.search(r'(\d+)', line_stripped)
                    if m:
                        stations[current_mac]['tx_bytes'] = int(m.group(1))
                elif 'connected time:' in line_stripped:
                    m = re.search(r'(\d+)', line_stripped)
                    if m:
                        stations[current_mac]['connected_time'] = int(m.group(1))
                elif 'inactive time:' in line_stripped:
                    m = re.search(r'(\d+)', line_stripped)
                    if m:
                        stations[current_mac]['inactive_ms'] = int(m.group(1))
        return stations

    def _get_arp_table(self):
        try:
            result = subprocess.run(
                ['arp', '-an'], capture_output=True, text=True, timeout=5
            )
            arp = {}
            for line in result.stdout.splitlines():
                match = re.search(
                    r'\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-fA-F:]+)', line
                )
                if match:
                    arp[match.group(2).upper()] = {'ip': match.group(1)}
            return arp
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return {}

    def _resolve_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror, OSError):
            return ''
