"""MAC address filtering — whitelist/blacklist management for hostapd."""

import os
import re
import subprocess
import logging

logger = logging.getLogger(__name__)

MAC_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')


class MACFilter:
    def __init__(self, db, interface='wlan0'):
        self.db = db
        self.interface = interface
        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.whitelist_file = os.path.join(
            self._base_dir, os.getenv('MAC_WHITELIST_FILE', 'config/mac_whitelist.txt')
        )
        self.blacklist_file = os.path.join(
            self._base_dir, os.getenv('MAC_BLACKLIST_FILE', 'config/mac_blacklist.txt')
        )

    @staticmethod
    def validate_mac(mac):
        return bool(MAC_PATTERN.match(mac))

    def get_mode(self):
        return os.getenv('MAC_FILTER_MODE', 'whitelist')

    def set_mode(self, mode):
        if mode not in ('whitelist', 'blacklist'):
            raise ValueError("Mode must be 'whitelist' or 'blacklist'")
        os.environ['MAC_FILTER_MODE'] = mode
        self._apply_filter()
        return mode

    def get_entries(self, list_type=None):
        rows = self.db.get_mac_filter_entries(list_type)
        return [dict(row) for row in rows]

    def add_entry(self, mac_address, description='', added_by=None):
        mac_address = mac_address.upper()
        if not self.validate_mac(mac_address):
            raise ValueError(f"Invalid MAC address: {mac_address}")
        mode = self.get_mode()
        self.db.add_mac_filter(mac_address, mode, description, added_by)
        self._write_filter_file()
        self._apply_filter()

    def remove_entry(self, mac_address):
        mac_address = mac_address.upper()
        self.db.remove_mac_filter(mac_address)
        self._write_filter_file()
        self._apply_filter()

    def _write_filter_file(self):
        """Write MAC addresses to the appropriate filter file."""
        mode = self.get_mode()
        file_path = self.whitelist_file if mode == 'whitelist' else self.blacklist_file
        entries = self.db.get_mac_filter_entries(mode)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            for entry in entries:
                f.write(f"{entry['mac_address']}\n")

    def _apply_filter(self):
        """Apply MAC filter rules via hostapd configuration."""
        mode = self.get_mode()
        if mode == 'whitelist':
            acl_file = self.whitelist_file
            macaddr_acl = '1'  # accept unless in deny list
        else:
            acl_file = self.blacklist_file
            macaddr_acl = '0'  # accept unless in deny list

        try:
            # Reload hostapd to apply MAC filter changes
            subprocess.run(
                ['hostapd_cli', '-i', self.interface, 'reload'],
                check=False, capture_output=True, timeout=10
            )
            logger.info("MAC filter applied: mode=%s", mode)
        except subprocess.TimeoutExpired:
            logger.error("Timeout applying MAC filter")
