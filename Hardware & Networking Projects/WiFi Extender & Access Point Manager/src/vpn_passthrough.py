"""VPN passthrough — routes AP traffic through WireGuard or OpenVPN tunnel."""

import subprocess
import os
import logging

logger = logging.getLogger(__name__)


class VPNPassthrough:
    def __init__(self, interface='wlan0', eth_interface='eth0'):
        self.interface = interface
        self.eth_interface = eth_interface
        self.vpn_type = os.getenv('VPN_TYPE', 'wireguard')
        self.vpn_config = os.getenv('VPN_CONFIG_PATH', '/etc/wireguard/wg0.conf')
        self.active = False

    def enable(self):
        """Enable VPN passthrough — route all AP traffic through VPN."""
        if self.vpn_type == 'wireguard':
            self._start_wireguard()
        elif self.vpn_type == 'openvpn':
            self._start_openvpn()
        else:
            raise ValueError(f"Unsupported VPN type: {self.vpn_type}")

        # Route AP traffic through VPN interface
        vpn_iface = 'wg0' if self.vpn_type == 'wireguard' else 'tun0'
        try:
            # Update NAT to masquerade through VPN interface
            subprocess.run([
                'iptables', '-t', 'nat', '-A', 'POSTROUTING',
                '-o', vpn_iface, '-j', 'MASQUERADE'
            ], check=True, capture_output=True)

            subprocess.run([
                'iptables', '-A', 'FORWARD', '-i', self.interface,
                '-o', vpn_iface, '-j', 'ACCEPT'
            ], check=True, capture_output=True)

            subprocess.run([
                'iptables', '-A', 'FORWARD', '-i', vpn_iface,
                '-o', self.interface, '-m', 'state',
                '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'
            ], check=True, capture_output=True)

            self.active = True
            logger.info("VPN passthrough enabled via %s (%s)", vpn_iface, self.vpn_type)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to configure VPN routing: %s", e)
            raise

    def disable(self):
        """Disable VPN passthrough."""
        vpn_iface = 'wg0' if self.vpn_type == 'wireguard' else 'tun0'

        # Remove VPN iptables rules
        subprocess.run([
            'iptables', '-t', 'nat', '-D', 'POSTROUTING',
            '-o', vpn_iface, '-j', 'MASQUERADE'
        ], check=False, capture_output=True)
        subprocess.run([
            'iptables', '-D', 'FORWARD', '-i', self.interface,
            '-o', vpn_iface, '-j', 'ACCEPT'
        ], check=False, capture_output=True)
        subprocess.run([
            'iptables', '-D', 'FORWARD', '-i', vpn_iface,
            '-o', self.interface, '-m', 'state',
            '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'
        ], check=False, capture_output=True)

        if self.vpn_type == 'wireguard':
            self._stop_wireguard()
        else:
            self._stop_openvpn()

        self.active = False
        logger.info("VPN passthrough disabled")

    def status(self):
        """Get VPN connection status."""
        vpn_iface = 'wg0' if self.vpn_type == 'wireguard' else 'tun0'
        try:
            result = subprocess.run(
                ['ip', 'link', 'show', vpn_iface],
                capture_output=True, text=True, timeout=5
            )
            iface_up = 'state UP' in result.stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            iface_up = False

        return {
            'active': self.active,
            'type': self.vpn_type,
            'interface': vpn_iface,
            'interface_up': iface_up,
        }

    def _start_wireguard(self):
        try:
            subprocess.run(
                ['wg-quick', 'up', 'wg0'],
                check=True, capture_output=True, timeout=15
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to start WireGuard: %s", e)
            raise

    def _stop_wireguard(self):
        subprocess.run(
            ['wg-quick', 'down', 'wg0'],
            check=False, capture_output=True, timeout=15
        )

    def _start_openvpn(self):
        try:
            subprocess.run(
                ['systemctl', 'start', 'openvpn@client'],
                check=True, capture_output=True, timeout=30
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to start OpenVPN: %s", e)
            raise

    def _stop_openvpn(self):
        subprocess.run(
            ['systemctl', 'stop', 'openvpn@client'],
            check=False, capture_output=True, timeout=15
        )
