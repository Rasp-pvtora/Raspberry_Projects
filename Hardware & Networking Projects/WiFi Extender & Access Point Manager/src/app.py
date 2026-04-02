"""Flask application — main entry point with SocketIO integration."""

import os
import sys
import logging

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG', 'false').lower() == 'true' else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

# ── Flask app ──
app = Flask(
    __name__,
    template_folder='templates',
    static_folder='../static',
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)

# ── Shared services ──
from src.models import Database
from src.ap_manager import APManager
from src.client_monitor import ClientMonitor
from src.bandwidth_tracker import BandwidthTracker
from src.mac_filter import MACFilter
from src.qos_manager import QoSManager
from src.captive_portal import CaptivePortal
from src.wifi_scheduler import WiFiScheduler
from src.channel_scanner import ChannelScanner
from src.dns_manager import DNSManager
from src.vpn_passthrough import VPNPassthrough
from src.health_monitor import HealthMonitor
from src.notification_service import NotificationService
from src.feature_toggles import FeatureToggles

db = Database()
ap_manager = APManager()
client_monitor = ClientMonitor(os.getenv('AP_INTERFACE', 'wlan0'))
mac_filter = MACFilter(db, os.getenv('AP_INTERFACE', 'wlan0'))
qos_manager = QoSManager(os.getenv('AP_INTERFACE', 'wlan0'))
captive_portal = CaptivePortal(os.getenv('AP_INTERFACE', 'wlan0'))
channel_scanner = ChannelScanner(os.getenv('AP_INTERFACE', 'wlan0'))
dns_manager = DNSManager(os.getenv('AP_INTERFACE', 'wlan0'))
vpn_passthrough = VPNPassthrough(os.getenv('AP_INTERFACE', 'wlan0'))
notification_service = NotificationService()
feature_toggles = FeatureToggles(db)
wifi_scheduler = WiFiScheduler(ap_manager, db)


def ws_emit(event, data):
    """Helper to emit WebSocket events."""
    socketio.emit(event, data)


bandwidth_tracker = BandwidthTracker(
    db, ws_callback=ws_emit,
    interval=int(os.getenv('BANDWIDTH_INTERVAL', '5'))
)
health_monitor = HealthMonitor(
    db, ws_callback=ws_emit,
    check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL_SEC', '30')),
    ping_target=os.getenv('HEALTH_PING_TARGET', '1.1.1.1'),
)

# Store services on app for access in routes
app.config['services'] = {
    'db': db,
    'ap_manager': ap_manager,
    'client_monitor': client_monitor,
    'bandwidth_tracker': bandwidth_tracker,
    'mac_filter': mac_filter,
    'qos_manager': qos_manager,
    'captive_portal': captive_portal,
    'wifi_scheduler': wifi_scheduler,
    'channel_scanner': channel_scanner,
    'dns_manager': dns_manager,
    'vpn_passthrough': vpn_passthrough,
    'health_monitor': health_monitor,
    'notification_service': notification_service,
    'feature_toggles': feature_toggles,
}

# ── Register blueprints ──
from src.routes.auth_routes import bp as auth_bp
from src.routes.ap_routes import bp as ap_bp
from src.routes.client_routes import bp as client_bp
from src.routes.bandwidth_routes import bp as bandwidth_bp
from src.routes.mac_filter_routes import bp as mac_filter_bp
from src.routes.qos_routes import bp as qos_bp
from src.routes.schedule_routes import bp as schedule_bp
from src.routes.dns_routes import bp as dns_bp
from src.routes.health_routes import bp as health_bp
from src.routes.settings_routes import bp as settings_bp

app.register_blueprint(auth_bp)
app.register_blueprint(ap_bp)
app.register_blueprint(client_bp)
app.register_blueprint(bandwidth_bp)
app.register_blueprint(mac_filter_bp)
app.register_blueprint(qos_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(dns_bp)
app.register_blueprint(health_bp)
app.register_blueprint(settings_bp)


# ── WebSocket events ──
@socketio.on('connect')
def handle_connect():
    logger.debug("WebSocket client connected")


@socketio.on('disconnect')
def handle_disconnect():
    logger.debug("WebSocket client disconnected")


@socketio.on('toggle_feature')
def handle_toggle_feature(data):
    feature = data.get('feature')
    enabled = data.get('enabled', False)
    try:
        feature_toggles.set_toggle(feature, enabled)
        socketio.emit('feature_toggled', {'feature': feature, 'enabled': enabled})
    except ValueError as e:
        socketio.emit('error', {'message': str(e)})


# ── Start background services ──
def start_services():
    toggles = feature_toggles.get_all()

    if toggles.get('ENABLE_BANDWIDTH_MONITOR', True):
        bandwidth_tracker.start()
    if toggles.get('ENABLE_HEALTH_MONITOR', True):
        health_monitor.start()
    if toggles.get('ENABLE_WIFI_SCHEDULE', False):
        wifi_scheduler.start()

    logger.info("Background services started")


# ── Main ──
if __name__ == '__main__':
    start_services()
    socketio.run(
        app,
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', '5000')),
        debug=os.getenv('DEBUG', 'false').lower() == 'true',
        allow_unsafe_werkzeug=True,
    )
