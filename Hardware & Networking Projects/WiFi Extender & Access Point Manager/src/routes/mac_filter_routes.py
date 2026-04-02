"""MAC filter routes."""

import re
from flask import Blueprint, request, jsonify, render_template, current_app
from src.auth import require_auth

bp = Blueprint('mac_filter', __name__)

MAC_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')


def _svc(name):
    return current_app.config['services'][name]


@bp.route('/mac-filter')
@require_auth
def mac_filter_page():
    return render_template('mac_filter.html')


@bp.route('/api/mac-filter', methods=['GET'])
@require_auth
def get_mac_filter():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_MAC_FILTER'):
        return jsonify({'error': 'MAC filtering is disabled'}), 403

    mf = _svc('mac_filter')
    return jsonify({
        'mode': mf.get_mode(),
        'entries': mf.get_entries(),
    })


@bp.route('/api/mac-filter', methods=['POST'])
@require_auth
def add_mac_filter():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_MAC_FILTER'):
        return jsonify({'error': 'MAC filtering is disabled'}), 403

    data = request.get_json()
    if not data or 'mac' not in data:
        return jsonify({'error': 'MAC address required'}), 400

    mac = data['mac'].upper()
    if not MAC_PATTERN.match(mac):
        return jsonify({'error': 'Invalid MAC address format'}), 400

    mf = _svc('mac_filter')
    try:
        mf.add_entry(mac, data.get('description', ''), getattr(request, 'user_id', None))
        return jsonify({'added': True, 'mac': mac}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/api/mac-filter/<mac>', methods=['DELETE'])
@require_auth
def remove_mac_filter(mac):
    mac = mac.upper()
    if not MAC_PATTERN.match(mac):
        return jsonify({'error': 'Invalid MAC address'}), 400

    mf = _svc('mac_filter')
    mf.remove_entry(mac)
    return jsonify({'removed': True})


@bp.route('/api/mac-filter/mode', methods=['PUT'])
@require_auth
def set_filter_mode():
    data = request.get_json()
    if not data or 'mode' not in data:
        return jsonify({'error': 'Mode required'}), 400

    mf = _svc('mac_filter')
    try:
        mode = mf.set_mode(data['mode'])
        entries = mf.get_entries(mode)
        return jsonify({'mode': mode, 'active_entries': len(entries)})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
