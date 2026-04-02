"""Client management routes."""

import re
from flask import Blueprint, request, jsonify, render_template, current_app
from src.auth import require_auth

bp = Blueprint('clients', __name__)

MAC_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')


def _svc(name):
    return current_app.config['services'][name]


@bp.route('/clients')
@require_auth
def clients_page():
    return render_template('clients.html')


@bp.route('/api/clients', methods=['GET'])
@require_auth
def list_clients():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_CLIENT_LIST'):
        return jsonify({'error': 'Client list feature is disabled'}), 403

    client_monitor = _svc('client_monitor')
    db = _svc('db')
    clients = client_monitor.get_connected_clients()

    # Upsert clients to database
    for c in clients:
        db.upsert_client(c['mac'], c['hostname'], c['ip'])

    return jsonify(clients)


@bp.route('/api/clients/<mac>', methods=['GET'])
@require_auth
def get_client(mac):
    mac = mac.upper()
    if not MAC_PATTERN.match(mac):
        return jsonify({'error': 'Invalid MAC address'}), 400

    db = _svc('db')
    client = db.get_client_by_mac(mac)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    return jsonify(dict(client))


@bp.route('/api/clients/<mac>/disconnect', methods=['POST'])
@require_auth
def disconnect_client(mac):
    mac = mac.upper()
    if not MAC_PATTERN.match(mac):
        return jsonify({'error': 'Invalid MAC address'}), 400

    client_monitor = _svc('client_monitor')
    success = client_monitor.disconnect_client(mac)
    if success:
        return jsonify({'disconnected': True, 'mac': mac})
    return jsonify({'error': 'Failed to disconnect client'}), 500
