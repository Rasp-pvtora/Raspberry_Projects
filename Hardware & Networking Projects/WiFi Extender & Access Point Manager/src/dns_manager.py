"""DNS manager — manages dnsmasq DNS configuration."""

import os
import subprocess
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)


class DNSManager:
    def __init__(self, interface='wlan0'):
        self.interface = interface
        self.dnsmasq_conf = '/etc/dnsmasq.conf'
        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def get_config(self):
        """Get current DNS configuration."""
        return {
            'primary': os.getenv('DNS_PRIMARY', '1.1.1.1'),
            'secondary': os.getenv('DNS_SECONDARY', '8.8.8.8'),
            'interface': self.interface,
        }

    def update_dns(self, primary=None, secondary=None):
        """Update upstream DNS servers and regenerate dnsmasq config."""
        env_path = os.path.join(self._base_dir, '.env')
        updates = {}
        if primary:
            updates['DNS_PRIMARY'] = primary
            os.environ['DNS_PRIMARY'] = primary
        if secondary:
            updates['DNS_SECONDARY'] = secondary
            os.environ['DNS_SECONDARY'] = secondary

        if updates:
            self._update_env(env_path, updates)
            self._regenerate_dnsmasq()
            self._restart_dnsmasq()

    def _regenerate_dnsmasq(self):
        """Regenerate dnsmasq.conf from template."""
        template_path = os.path.join(self._base_dir, 'config', 'dnsmasq.conf.template')
        with open(template_path, 'r') as f:
            template = Template(f.read())
        config = template.render(
            AP_INTERFACE=self.interface,
            DHCP_RANGE_START=os.getenv('DHCP_RANGE_START', '10.0.0.10'),
            DHCP_RANGE_END=os.getenv('DHCP_RANGE_END', '10.0.0.200'),
            DHCP_LEASE_TIME=os.getenv('DHCP_LEASE_TIME', '12h'),
            DNS_PRIMARY=os.getenv('DNS_PRIMARY', '1.1.1.1'),
            DNS_SECONDARY=os.getenv('DNS_SECONDARY', '8.8.8.8'),
        )
        with open(self.dnsmasq_conf, 'w') as f:
            f.write(config)
        logger.info("dnsmasq config regenerated")

    def _restart_dnsmasq(self):
        try:
            subprocess.run(
                ['systemctl', 'restart', 'dnsmasq'],
                check=True, capture_output=True, timeout=15
            )
            logger.info("dnsmasq restarted")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error("Failed to restart dnsmasq: %s", e)
            raise

    @staticmethod
    def _update_env(env_path, updates):
        if not os.path.exists(env_path):
            return
        with open(env_path, 'r') as f:
            lines = f.readlines()
        new_lines = []
        updated = set()
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and '=' in stripped:
                key = stripped.split('=', 1)[0]
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}\n")
                    updated.add(key)
                    continue
            new_lines.append(line)
        for key, val in updates.items():
            if key not in updated:
                new_lines.append(f"{key}={val}\n")
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
