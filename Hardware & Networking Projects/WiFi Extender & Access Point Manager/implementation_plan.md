# 🗺️ Implementation Plan — WiFi Extender & Access Point Manager

---

## Phase 1: Project Setup & Authentication (Day 1)

### Step 1.1 — Initialize project
```bash
mkdir -p src/routes src/templates static/css static/js data config deploy docs tests
python3 -m venv venv && source venv/bin/activate
```

### Step 1.2 — Core dependencies (`requirements.txt`)
```text
Flask==3.1.*
Flask-SocketIO==5.3.*
flask-limiter==3.5.*
flask-cors==4.0.*
PyJWT==2.9.*
bcrypt==4.2.*
python-dotenv==1.0.*
Jinja2==3.1.*
APScheduler==3.10.*
psutil==6.0.*
python-telegram-bot==21.*
slack-sdk==3.33.*
gunicorn==22.*
```

### Step 1.3 — Flask app skeleton (`src/app.py`)
```python
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='../static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
socketio = SocketIO(app, cors_allowed_origins="*")

from routes import auth_routes, ap_routes, client_routes, bandwidth_routes
from routes import mac_filter_routes, qos_routes, schedule_routes
from routes import dns_routes, health_routes, settings_routes
app.register_blueprint(auth_routes.bp)
app.register_blueprint(ap_routes.bp)
app.register_blueprint(client_routes.bp)
app.register_blueprint(bandwidth_routes.bp)
app.register_blueprint(mac_filter_routes.bp)
app.register_blueprint(qos_routes.bp)
app.register_blueprint(schedule_routes.bp)
app.register_blueprint(dns_routes.bp)
app.register_blueprint(health_routes.bp)
app.register_blueprint(settings_routes.bp)

if __name__ == '__main__':
    socketio.run(app, host=os.getenv('HOST', '0.0.0.0'),
                 port=int(os.getenv('PORT', 5000)))
```

### Step 1.4 — Authentication module (`src/auth.py`)
```python
import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify

SECRET = os.getenv('SECRET_KEY')
SESSION_HOURS = int(os.getenv('AUTH_SESSION_HOURS', 24))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_token(user_id: int) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token') or \
                request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        try:
            payload = jwt.decode(token, SECRET, algorithms=['HS256'])
            request.user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated
```

---

## Phase 2: hostapd + dnsmasq Auto-Setup (Day 1–2)

### Step 2.1 — AP manager (`src/ap_manager.py`)
```python
import subprocess
import os
from jinja2 import Template

class APManager:
    def __init__(self):
        self.hostapd_conf = '/etc/hostapd/hostapd.conf'
        self.dnsmasq_conf = '/etc/dnsmasq.conf'
        self.interface = os.getenv('AP_INTERFACE', 'wlan0')
        self.eth_interface = os.getenv('ETH_INTERFACE', 'eth0')

    def generate_hostapd_config(self):
        with open('config/hostapd.conf.template', 'r') as f:
            template = Template(f.read())
        config = template.render(
            AP_INTERFACE=self.interface,
            AP_SSID=os.getenv('AP_SSID', 'RaspberryPi-AP'),
            AP_PASSWORD=os.getenv('AP_PASSWORD', 'ChangeMe123!'),
            AP_CHANNEL=os.getenv('AP_CHANNEL', '6'),
            AP_HW_MODE=os.getenv('AP_HW_MODE', 'g'),
            AP_WPA=os.getenv('AP_WPA', '2'),
            AP_HIDDEN=os.getenv('AP_HIDDEN', '0'),
            AP_COUNTRY_CODE=os.getenv('AP_COUNTRY_CODE', 'US')
        )
        with open(self.hostapd_conf, 'w') as f:
            f.write(config)

    def generate_dnsmasq_config(self):
        with open('config/dnsmasq.conf.template', 'r') as f:
            template = Template(f.read())
        config = template.render(
            AP_INTERFACE=self.interface,
            DHCP_RANGE_START=os.getenv('DHCP_RANGE_START', '10.0.0.10'),
            DHCP_RANGE_END=os.getenv('DHCP_RANGE_END', '10.0.0.200'),
            DHCP_LEASE_TIME=os.getenv('DHCP_LEASE_TIME', '12h'),
            DNS_PRIMARY=os.getenv('DNS_PRIMARY', '1.1.1.1'),
            DNS_SECONDARY=os.getenv('DNS_SECONDARY', '8.8.8.8')
        )
        with open(self.dnsmasq_conf, 'w') as f:
            f.write(config)

    def setup_nat(self):
        """Enable IP forwarding and NAT masquerade"""
        cmds = [
            'sysctl -w net.ipv4.ip_forward=1',
            f'iptables -t nat -A POSTROUTING -o {self.eth_interface} -j MASQUERADE',
            f'iptables -A FORWARD -i {self.interface} -o {self.eth_interface} -j ACCEPT',
            f'iptables -A FORWARD -i {self.eth_interface} -o {self.interface} '
            '-m state --state RELATED,ESTABLISHED -j ACCEPT'
        ]
        for cmd in cmds:
            subprocess.run(cmd.split(), check=True)

    def start(self):
        subprocess.run(['systemctl', 'start', 'hostapd'], check=True)
        subprocess.run(['systemctl', 'start', 'dnsmasq'], check=True)

    def stop(self):
        subprocess.run(['systemctl', 'stop', 'hostapd'], check=True)
        subprocess.run(['systemctl', 'stop', 'dnsmasq'], check=True)

    def restart(self):
        self.stop()
        self.generate_hostapd_config()
        self.generate_dnsmasq_config()
        self.start()

    def status(self):
        result = subprocess.run(['systemctl', 'is-active', 'hostapd'],
                                capture_output=True, text=True)
        return result.stdout.strip() == 'active'
```

### Step 2.2 — Initial AP setup script (`setup_ap.py`)
```python
#!/usr/bin/env python3
"""One-time AP setup: configure interfaces, hostapd, dnsmasq, NAT"""
import subprocess
import os
from dotenv import load_dotenv
from src.ap_manager import APManager

load_dotenv()

def setup():
    interface = os.getenv('AP_INTERFACE', 'wlan0')
    gateway = os.getenv('AP_GATEWAY', '10.0.0.1')

    # Set static IP on WiFi interface
    subprocess.run([
        'ip', 'addr', 'add', f'{gateway}/24', 'dev', interface
    ], check=False)
    subprocess.run(['ip', 'link', 'set', interface, 'up'], check=True)

    # Generate configs and start
    ap = APManager()
    ap.generate_hostapd_config()
    ap.generate_dnsmasq_config()
    ap.setup_nat()
    ap.start()
    print(f"AP started on {interface} — SSID: {os.getenv('AP_SSID')}")

if __name__ == '__main__':
    setup()
```

---

## Phase 3: Client Monitor & Bandwidth (Day 2–4)

### Step 3.1 — Client monitor (`src/client_monitor.py`)
```python
import subprocess
import re
import socket

class ClientMonitor:
    def __init__(self, interface='wlan0'):
        self.interface = interface

    def get_connected_clients(self):
        """Parse hostapd station list and ARP table"""
        clients = []
        # Get stations from iw
        result = subprocess.run(
            ['iw', 'dev', self.interface, 'station', 'dump'],
            capture_output=True, text=True
        )
        stations = self._parse_iw_output(result.stdout)

        # Enrich with ARP table for IP/hostname
        arp = self._get_arp_table()
        for mac, info in stations.items():
            ip = arp.get(mac, {}).get('ip', 'unknown')
            hostname = self._resolve_hostname(ip)
            clients.append({
                'mac': mac,
                'ip': ip,
                'hostname': hostname,
                'signal_dbm': info.get('signal', 0),
                'connected_time': info.get('connected_time', 0),
                'rx_bytes': info.get('rx_bytes', 0),
                'tx_bytes': info.get('tx_bytes', 0)
            })
        return clients

    def _parse_iw_output(self, output):
        stations = {}
        current_mac = None
        for line in output.splitlines():
            mac_match = re.match(r'Station\s+([0-9a-f:]+)', line, re.I)
            if mac_match:
                current_mac = mac_match.group(1).upper()
                stations[current_mac] = {}
            elif current_mac:
                if 'signal:' in line:
                    stations[current_mac]['signal'] = int(
                        re.search(r'(-?\d+)', line).group(1))
                elif 'rx bytes:' in line:
                    stations[current_mac]['rx_bytes'] = int(
                        re.search(r'(\d+)', line).group(1))
                elif 'tx bytes:' in line:
                    stations[current_mac]['tx_bytes'] = int(
                        re.search(r'(\d+)', line).group(1))
        return stations

    def _get_arp_table(self):
        result = subprocess.run(['arp', '-an'], capture_output=True, text=True)
        arp = {}
        for line in result.stdout.splitlines():
            match = re.search(
                r'\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-f:]+)', line, re.I)
            if match:
                arp[match.group(2).upper()] = {'ip': match.group(1)}
        return arp

    def _resolve_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror):
            return ''
```

### Step 3.2 — Bandwidth tracker (`src/bandwidth_tracker.py`)
```python
import subprocess
import time
import threading

class BandwidthTracker:
    def __init__(self, db, ws_callback, interval=5):
        self.db = db
        self.ws = ws_callback
        self.interval = interval
        self.previous = {}
        self.running = False

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._track_loop, daemon=True)
        thread.start()

    def stop(self):
        self.running = False

    def _track_loop(self):
        while self.running:
            current = self._read_counters()
            rates = self._calculate_rates(current)
            if rates:
                self.db.store_bandwidth(rates)
                self.ws('bandwidth_update', rates)
            self.previous = current
            time.sleep(self.interval)

    def _read_counters(self):
        """Read iptables byte counters per client"""
        result = subprocess.run(
            ['iptables', '-L', 'FORWARD', '-v', '-n', '-x'],
            capture_output=True, text=True
        )
        # Parse per-IP byte counters
        counters = {}
        for line in result.stdout.splitlines():
            # Parse source/dest IP and byte counts
            pass  # Implementation depends on iptables chain structure
        return counters

    def _calculate_rates(self, current):
        rates = {}
        for mac, data in current.items():
            if mac in self.previous:
                elapsed = self.interval
                rates[mac] = {
                    'rx_kbps': (data['rx'] - self.previous[mac]['rx']) * 8 / elapsed / 1000,
                    'tx_kbps': (data['tx'] - self.previous[mac]['tx']) * 8 / elapsed / 1000
                }
        return rates
```

---

## Phase 4: QoS Traffic Shaping (Day 5)

### Step 4.1 — QoS manager (`src/qos_manager.py`)
```python
import subprocess

class QoSManager:
    def __init__(self, interface='wlan0'):
        self.interface = interface
        self.initialized = False

    def init_qdisc(self):
        """Initialize HTB qdisc on interface"""
        subprocess.run([
            'tc', 'qdisc', 'add', 'dev', self.interface,
            'root', 'handle', '1:', 'htb', 'default', '99'
        ], check=False)
        # Default class — full bandwidth
        subprocess.run([
            'tc', 'class', 'add', 'dev', self.interface,
            'parent', '1:', 'classid', '1:99',
            'htb', 'rate', '100mbit', 'ceil', '100mbit'
        ], check=False)
        self.initialized = True

    def set_client_limit(self, client_ip, down_kbps, up_kbps, class_id):
        """Apply bandwidth limit for specific client"""
        # Download limit (traffic TO client)
        subprocess.run([
            'tc', 'class', 'add', 'dev', self.interface,
            'parent', '1:', 'classid', f'1:{class_id}',
            'htb', 'rate', f'{down_kbps}kbit', 'ceil', f'{down_kbps}kbit'
        ], check=True)
        # Filter to match client IP
        subprocess.run([
            'tc', 'filter', 'add', 'dev', self.interface,
            'parent', '1:0', 'protocol', 'ip', 'u32',
            'match', 'ip', 'dst', f'{client_ip}/32',
            'flowid', f'1:{class_id}'
        ], check=True)

    def remove_client_limit(self, class_id):
        subprocess.run([
            'tc', 'class', 'del', 'dev', self.interface,
            'classid', f'1:{class_id}'
        ], check=False)

    def reset_all(self):
        subprocess.run([
            'tc', 'qdisc', 'del', 'dev', self.interface, 'root'
        ], check=False)
        self.initialized = False
```

---

## Phase 5: Captive Portal (Day 5–6)

### Step 5.1 — Captive portal redirect (`src/captive_portal.py`)
```python
import subprocess

class CaptivePortal:
    def __init__(self, interface='wlan0', portal_port=5000):
        self.interface = interface
        self.portal_port = portal_port
        self.authenticated_macs = set()

    def enable(self):
        """Redirect all HTTP to captive portal"""
        subprocess.run([
            'iptables', '-t', 'nat', '-A', 'PREROUTING',
            '-i', self.interface, '-p', 'tcp', '--dport', '80',
            '-j', 'REDIRECT', '--to-port', str(self.portal_port)
        ], check=True)
        # Block internet for unauthenticated clients
        subprocess.run([
            'iptables', '-I', 'FORWARD', '-i', self.interface,
            '-j', 'DROP'
        ], check=True)

    def authenticate_client(self, mac, ip):
        """Allow client through the portal"""
        self.authenticated_macs.add(mac)
        subprocess.run([
            'iptables', '-I', 'FORWARD', '-i', self.interface,
            '-s', ip, '-j', 'ACCEPT'
        ], check=True)

    def disable(self):
        """Remove captive portal iptables rules"""
        subprocess.run([
            'iptables', '-t', 'nat', '-D', 'PREROUTING',
            '-i', self.interface, '-p', 'tcp', '--dport', '80',
            '-j', 'REDIRECT', '--to-port', str(self.portal_port)
        ], check=False)
```

---

## Phase 6: WiFi Schedule & Health Monitor (Day 6–8)

### Step 6.1 — WiFi scheduler (`src/wifi_scheduler.py`)
```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

class WiFiScheduler:
    def __init__(self, ap_manager, db):
        self.ap = ap_manager
        self.db = db
        self.scheduler = BackgroundScheduler()

    def load_schedule(self):
        schedules = self.db.get_wifi_schedules()
        for sched in schedules:
            if not sched['enabled']:
                continue
            # Schedule WiFi ON
            self.scheduler.add_job(
                self.ap.start,
                'cron',
                day_of_week=sched['day_of_week'],
                hour=int(sched['on_time'].split(':')[0]),
                minute=int(sched['on_time'].split(':')[1]),
                id=f"wifi_on_{sched['day_of_week']}"
            )
            # Schedule WiFi OFF
            self.scheduler.add_job(
                self.ap.stop,
                'cron',
                day_of_week=sched['day_of_week'],
                hour=int(sched['off_time'].split(':')[0]),
                minute=int(sched['off_time'].split(':')[1]),
                id=f"wifi_off_{sched['day_of_week']}"
            )

    def start(self):
        self.load_schedule()
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()
```

### Step 6.2 — Health monitor (`src/health_monitor.py`)
```python
import subprocess
import time
import threading
import dns.resolver

class HealthMonitor:
    def __init__(self, db, ws_callback, check_interval=30):
        self.db = db
        self.ws = ws_callback
        self.interval = check_interval
        self.running = False

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._check_loop, daemon=True)
        thread.start()

    def _check_loop(self):
        while self.running:
            health = self._run_checks()
            self.db.store_health_check(health)
            self.ws('health_update', health)
            time.sleep(self.interval)

    def _run_checks(self):
        return {
            'latency_ms': self._ping(),
            'packet_loss_pct': self._packet_loss(),
            'dns_resolve_ms': self._dns_check(),
            'internet_up': True  # Based on combined checks
        }

    def _ping(self, target='1.1.1.1', count=3):
        result = subprocess.run(
            ['ping', '-c', str(count), '-W', '2', target],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return -1
        # Parse average latency
        import re
        match = re.search(r'avg.*?=.*?/([\d.]+)/', result.stdout)
        return float(match.group(1)) if match else -1

    def _packet_loss(self, target='1.1.1.1', count=10):
        result = subprocess.run(
            ['ping', '-c', str(count), '-W', '2', target],
            capture_output=True, text=True
        )
        import re
        match = re.search(r'(\d+)% packet loss', result.stdout)
        return float(match.group(1)) if match else 100.0

    def _dns_check(self, domain='google.com'):
        start = time.time()
        try:
            dns.resolver.resolve(domain, 'A')
            return round((time.time() - start) * 1000, 1)
        except Exception:
            return -1
```

---

## Phases 7–10: Remaining Phases

Phases 7–10 follow the same implementation pattern:
- **Phase 7** (VPN Passthrough): WireGuard/OpenVPN tunnel setup + iptables routing
- **Phase 8** (Dual-Band): Second hostapd instance on wlan1 (5GHz)
- **Phase 9** (Feature Toggles): Bidirectional `.env` ↔ SQLite sync with WebSocket
- **Phase 10** (Deployment): systemd service, auto-start, TLS certs, iptables persistence

Each phase follows the same pattern: module implementation → API routes → dashboard UI → WebSocket integration → testing.
