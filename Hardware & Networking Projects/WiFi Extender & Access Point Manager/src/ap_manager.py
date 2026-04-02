"""Access Point manager — hostapd + dnsmasq configuration and control."""

import subprocess
import os
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)


class APManager:
    def __init__(self):
        self.hostapd_conf = '/etc/hostapd/hostapd.conf'
        self.dnsmasq_conf = '/etc/dnsmasq.conf'
        self.interface = os.getenv('AP_INTERFACE', 'wlan0')
        self.eth_interface = os.getenv('ETH_INTERFACE', 'eth0')
        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def generate_hostapd_config(self):
        template_path = os.path.join(self._base_dir, 'config', 'hostapd.conf.template')
        with open(template_path, 'r') as f:
            template = Template(f.read())
        config = template.render(
            AP_INTERFACE=self.interface,
            AP_SSID=os.getenv('AP_SSID', 'RaspberryPi-AP'),
            AP_PASSWORD=os.getenv('AP_PASSWORD', 'ChangeMe123!'),
            AP_CHANNEL=os.getenv('AP_CHANNEL', '6'),
            AP_HW_MODE=os.getenv('AP_HW_MODE', 'g'),
            AP_WPA=os.getenv('AP_WPA', '2'),
            AP_HIDDEN=os.getenv('AP_HIDDEN', '0'),
            AP_COUNTRY_CODE=os.getenv('AP_COUNTRY_CODE', 'US'),
        )
        with open(self.hostapd_conf, 'w') as f:
            f.write(config)
        logger.info("hostapd config written to %s", self.hostapd_conf)

    def generate_dnsmasq_config(self):
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
        logger.info("dnsmasq config written to %s", self.dnsmasq_conf)

    def setup_nat(self):
        """Enable IP forwarding and NAT masquerade."""
        cmds = [
            ['sysctl', '-w', 'net.ipv4.ip_forward=1'],
            ['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o',
             self.eth_interface, '-j', 'MASQUERADE'],
            ['iptables', '-A', 'FORWARD', '-i', self.interface, '-o',
             self.eth_interface, '-j', 'ACCEPT'],
            ['iptables', '-A', 'FORWARD', '-i', self.eth_interface, '-o',
             self.interface, '-m', 'state', '--state', 'RELATED,ESTABLISHED',
             '-j', 'ACCEPT'],
        ]
        for cmd in cmds:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error("NAT setup command failed: %s — %s", ' '.join(cmd), e.stderr)
                raise

    def start(self):
        subprocess.run(['systemctl', 'start', 'hostapd'], check=True, capture_output=True)
        subprocess.run(['systemctl', 'start', 'dnsmasq'], check=True, capture_output=True)
        logger.info("AP started on %s", self.interface)

    def stop(self):
        subprocess.run(['systemctl', 'stop', 'hostapd'], check=False, capture_output=True)
        subprocess.run(['systemctl', 'stop', 'dnsmasq'], check=False, capture_output=True)
        logger.info("AP stopped")

    def restart(self):
        self.stop()
        self.generate_hostapd_config()
        self.generate_dnsmasq_config()
        self.start()

    def status(self):
        """Return AP status dict."""
        hostapd_active = self._is_service_active('hostapd')
        dnsmasq_active = self._is_service_active('dnsmasq')
        return {
            'running': hostapd_active and dnsmasq_active,
            'hostapd': 'active' if hostapd_active else 'inactive',
            'dnsmasq': 'active' if dnsmasq_active else 'inactive',
            'ssid': os.getenv('AP_SSID', 'RaspberryPi-AP'),
            'channel': int(os.getenv('AP_CHANNEL', '6')),
            'interface': self.interface,
            'hw_mode': os.getenv('AP_HW_MODE', 'g'),
        }

    def _is_service_active(self, service_name):
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True, text=True
        )
        return result.stdout.strip() == 'active'

    def update_config(self, ssid=None, password=None, channel=None, hidden=None):
        """Update AP configuration by modifying environment and regenerating configs."""
        env_path = os.path.join(self._base_dir, '.env')
        updates = {}
        if ssid is not None:
            updates['AP_SSID'] = ssid
        if password is not None:
            updates['AP_PASSWORD'] = password
        if channel is not None:
            updates['AP_CHANNEL'] = str(channel)
        if hidden is not None:
            updates['AP_HIDDEN'] = '1' if hidden else '0'

        if updates:
            self._update_env_file(env_path, updates)
            # Also update os.environ so config is immediately available
            for key, val in updates.items():
                os.environ[key] = val

    @staticmethod
    def _update_env_file(env_path, updates):
        """Update specific keys in .env file."""
        if not os.path.exists(env_path):
            return
        with open(env_path, 'r') as f:
            lines = f.readlines()
        new_lines = []
        updated_keys = set()
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and '=' in stripped:
                key = stripped.split('=', 1)[0]
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                    continue
            new_lines.append(line)
        # Append any keys that weren't found
        for key, val in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={val}\n")
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
