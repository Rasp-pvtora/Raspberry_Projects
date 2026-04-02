"""DNS configuration routes."""

import re
from flask import Blueprint, request, jsonify, render_template, current_app
from src.auth import require_auth

bp = Blueprint('dns', __name__)

IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')


def _svc(name):
    return current_app.config['services'][name]


@bp.route('/dns')
@require_auth
def dns_page():
    return render_template('dns.html')


@bp.route('/api/dns', methods=['GET'])
@require_auth
def get_dns():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_DNS_CONFIG'):
        return jsonify({'error': 'DNS configuration is disabled'}), 403

    dns = _svc('dns_manager')
    return jsonify(dns.get_config())


@bp.route('/api/dns', methods=['PUT'])
@require_auth
def update_dns():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_DNS_CONFIG'):
        return jsonify({'error': 'DNS configuration is disabled'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    primary = data.get('primary')
    secondary = data.get('secondary')

    if primary and not IP_PATTERN.match(primary):
        return jsonify({'error': 'Invalid primary DNS IP'}), 400
    if secondary and not IP_PATTERN.match(secondary):
        return jsonify({'error': 'Invalid secondary DNS IP'}), 400

    dns = _svc('dns_manager')
    try:
        dns.update_dns(primary=primary, secondary=secondary)
        return jsonify({'updated': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
