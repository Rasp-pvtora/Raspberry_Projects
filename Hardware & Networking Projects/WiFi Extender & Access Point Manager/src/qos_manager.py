"""QoS traffic shaping — per-client bandwidth limits using tc."""

import subprocess
import logging

logger = logging.getLogger(__name__)


class QoSManager:
    def __init__(self, interface='wlan0'):
        self.interface = interface
        self.initialized = False
        self._next_class_id = 10

    def init_qdisc(self):
        """Initialize HTB qdisc on interface."""
        # Remove existing qdisc first
        subprocess.run(
            ['tc', 'qdisc', 'del', 'dev', self.interface, 'root'],
            check=False, capture_output=True
        )
        # Add HTB root qdisc
        subprocess.run([
            'tc', 'qdisc', 'add', 'dev', self.interface,
            'root', 'handle', '1:', 'htb', 'default', '99'
        ], check=True, capture_output=True)
        # Default class — full bandwidth
        subprocess.run([
            'tc', 'class', 'add', 'dev', self.interface,
            'parent', '1:', 'classid', '1:99',
            'htb', 'rate', '100mbit', 'ceil', '100mbit'
        ], check=True, capture_output=True)
        self.initialized = True
        logger.info("QoS HTB qdisc initialized on %s", self.interface)

    def set_client_limit(self, client_ip, down_kbps, up_kbps, class_id=None):
        """Apply bandwidth limit for a specific client."""
        if not self.initialized:
            self.init_qdisc()

        if class_id is None:
            class_id = self._next_class_id
            self._next_class_id += 1

        try:
            # Download limit (traffic TO client)
            subprocess.run([
                'tc', 'class', 'add', 'dev', self.interface,
                'parent', '1:', 'classid', f'1:{class_id}',
                'htb', 'rate', f'{down_kbps}kbit', 'ceil', f'{down_kbps}kbit'
            ], check=True, capture_output=True)

            # Filter to match client IP
            subprocess.run([
                'tc', 'filter', 'add', 'dev', self.interface,
                'parent', '1:0', 'protocol', 'ip', 'u32',
                'match', 'ip', 'dst', f'{client_ip}/32',
                'flowid', f'1:{class_id}'
            ], check=True, capture_output=True)

            logger.info("QoS limit set for %s: down=%dkbps, up=%dkbps",
                        client_ip, down_kbps, up_kbps)
            return class_id
        except subprocess.CalledProcessError as e:
            logger.error("Failed to set QoS limit for %s: %s", client_ip, e)
            raise

    def remove_client_limit(self, class_id):
        """Remove bandwidth limit for a client."""
        subprocess.run([
            'tc', 'class', 'del', 'dev', self.interface,
            'classid', f'1:{class_id}'
        ], check=False, capture_output=True)
        logger.info("QoS limit removed for class %d", class_id)

    def reset_all(self):
        """Remove all QoS rules."""
        subprocess.run([
            'tc', 'qdisc', 'del', 'dev', self.interface, 'root'
        ], check=False, capture_output=True)
        self.initialized = False
        self._next_class_id = 10
        logger.info("All QoS rules cleared on %s", self.interface)

    def get_status(self):
        """Get current tc qdisc status."""
        try:
            result = subprocess.run(
                ['tc', '-s', 'qdisc', 'show', 'dev', self.interface],
                capture_output=True, text=True, timeout=5
            )
            return {'initialized': self.initialized, 'details': result.stdout}
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return {'initialized': False, 'details': ''}
