"""QoS traffic shaping routes."""

import re
from flask import Blueprint, request, jsonify, render_template, current_app
from src.auth import require_auth

bp = Blueprint('qos', __name__)

MAC_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')


def _svc(name):
    return current_app.config['services'][name]


@bp.route('/qos')
@require_auth
def qos_page():
    return render_template('qos.html')


@bp.route('/api/qos/rules', methods=['GET'])
@require_auth
def get_qos_rules():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_QOS'):
        return jsonify({'error': 'QoS is disabled'}), 403

    db = _svc('db')
    rules = db.get_qos_rules()
    return jsonify([dict(r) for r in rules])


@bp.route('/api/qos/rules/<mac>', methods=['PUT'])
@require_auth
def set_qos_rule(mac):
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_QOS'):
        return jsonify({'error': 'QoS is disabled'}), 403

    mac = mac.upper()
    if not MAC_PATTERN.match(mac):
        return jsonify({'error': 'Invalid MAC address'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    down_kbps = data.get('down_limit_kbps', 10000)
    up_kbps = data.get('up_limit_kbps', 5000)
    priority = data.get('priority', 5)

    if not (1 <= priority <= 10):
        return jsonify({'error': 'Priority must be 1-10'}), 400

    db = _svc('db')
    qos = _svc('qos_manager')

    client = db.get_client_by_mac(mac)
    client_id = client['id'] if client else None

    db.set_qos_rule(client_id, mac, down_kbps, up_kbps, priority)

    # Apply tc rule if client is connected and has IP
    if client and client['ip_address']:
        try:
            qos.set_client_limit(client['ip_address'], down_kbps, up_kbps)
        except Exception as e:
            return jsonify({'error': f'Rule saved but tc failed: {e}'}), 500

    return jsonify({'applied': True})


@bp.route('/api/qos/rules/<mac>', methods=['DELETE'])
@require_auth
def delete_qos_rule(mac):
    mac = mac.upper()
    if not MAC_PATTERN.match(mac):
        return jsonify({'error': 'Invalid MAC address'}), 400

    db = _svc('db')
    db.delete_qos_rule(mac)
    return jsonify({'deleted': True})
