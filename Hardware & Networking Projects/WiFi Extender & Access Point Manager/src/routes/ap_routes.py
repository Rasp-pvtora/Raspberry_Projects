"""Access Point control routes."""

from flask import Blueprint, request, jsonify, render_template, current_app
from src.auth import require_auth

bp = Blueprint('ap', __name__)


def _svc(name):
    return current_app.config['services'][name]


@bp.route('/')
@require_auth
def dashboard():
    return render_template('dashboard.html')


@bp.route('/api/ap/status', methods=['GET'])
@require_auth
def ap_status():
    ap = _svc('ap_manager')
    client_monitor = _svc('client_monitor')
    status = ap.status()
    clients = client_monitor.get_connected_clients()
    status['clients_count'] = len(clients)
    return jsonify(status)


@bp.route('/api/ap/restart', methods=['POST'])
@require_auth
def ap_restart():
    ap = _svc('ap_manager')
    try:
        ap.restart()
        return jsonify({'status': 'restarting', 'eta_sec': 10})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/ap/config', methods=['PUT'])
@require_auth
def ap_update_config():
    ap = _svc('ap_manager')
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    ap.update_config(
        ssid=data.get('ssid'),
        password=data.get('password'),
        channel=data.get('channel'),
        hidden=data.get('hidden'),
    )
    return jsonify({'updated': True, 'restart_required': True})
