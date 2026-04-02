"""Captive portal — redirect unauthenticated clients to a landing page."""

import subprocess
import logging

logger = logging.getLogger(__name__)


class CaptivePortal:
    def __init__(self, interface='wlan0', portal_port=5000):
        self.interface = interface
        self.portal_port = portal_port
        self.authenticated_macs = set()
        self.enabled = False

    def enable(self):
        """Redirect all HTTP traffic to the captive portal."""
        try:
            # Redirect HTTP to portal
            subprocess.run([
                'iptables', '-t', 'nat', '-A', 'PREROUTING',
                '-i', self.interface, '-p', 'tcp', '--dport', '80',
                '-j', 'REDIRECT', '--to-port', str(self.portal_port)
            ], check=True, capture_output=True)

            # Redirect HTTPS to portal
            subprocess.run([
                'iptables', '-t', 'nat', '-A', 'PREROUTING',
                '-i', self.interface, '-p', 'tcp', '--dport', '443',
                '-j', 'REDIRECT', '--to-port', str(self.portal_port)
            ], check=True, capture_output=True)

            # Block all forward traffic by default (captive wall)
            subprocess.run([
                'iptables', '-I', 'FORWARD', '-i', self.interface,
                '-j', 'DROP'
            ], check=True, capture_output=True)

            # Allow DNS through so captive portal detection works
            subprocess.run([
                'iptables', '-I', 'FORWARD', '-i', self.interface,
                '-p', 'udp', '--dport', '53', '-j', 'ACCEPT'
            ], check=True, capture_output=True)

            self.enabled = True
            logger.info("Captive portal enabled on %s", self.interface)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to enable captive portal: %s", e)
            raise

    def authenticate_client(self, mac, ip):
        """Allow an authenticated client through the portal."""
        self.authenticated_macs.add(mac.upper())
        try:
            subprocess.run([
                'iptables', '-I', 'FORWARD', '-i', self.interface,
                '-s', ip, '-j', 'ACCEPT'
            ], check=True, capture_output=True)
            # Also allow return traffic
            subprocess.run([
                'iptables', '-I', 'FORWARD', '-o', self.interface,
                '-d', ip, '-j', 'ACCEPT'
            ], check=True, capture_output=True)
            logger.info("Client authenticated through portal: %s (%s)", mac, ip)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to authenticate client %s: %s", mac, e)
            raise

    def is_authenticated(self, mac):
        return mac.upper() in self.authenticated_macs

    def disable(self):
        """Remove captive portal iptables rules."""
        subprocess.run([
            'iptables', '-t', 'nat', '-D', 'PREROUTING',
            '-i', self.interface, '-p', 'tcp', '--dport', '80',
            '-j', 'REDIRECT', '--to-port', str(self.portal_port)
        ], check=False, capture_output=True)
        subprocess.run([
            'iptables', '-t', 'nat', '-D', 'PREROUTING',
            '-i', self.interface, '-p', 'tcp', '--dport', '443',
            '-j', 'REDIRECT', '--to-port', str(self.portal_port)
        ], check=False, capture_output=True)
        subprocess.run([
            'iptables', '-D', 'FORWARD', '-i', self.interface, '-j', 'DROP'
        ], check=False, capture_output=True)
        subprocess.run([
            'iptables', '-D', 'FORWARD', '-i', self.interface,
            '-p', 'udp', '--dport', '53', '-j', 'ACCEPT'
        ], check=False, capture_output=True)
        self.enabled = False
        self.authenticated_macs.clear()
        logger.info("Captive portal disabled")
