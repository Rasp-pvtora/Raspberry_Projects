"""Settings routes — feature toggles, AP config, captive portal."""

from flask import Blueprint, request, jsonify, render_template, current_app
from src.auth import require_auth

bp = Blueprint('settings', __name__)


def _svc(name):
    return current_app.config['services'][name]


@bp.route('/settings')
@require_auth
def settings_page():
    return render_template('settings.html')


@bp.route('/captive-portal')
@require_auth
def captive_portal_page():
    return render_template('captive_portal.html')


# ── Feature Toggles ──

@bp.route('/api/settings/features', methods=['GET'])
@require_auth
def get_features():
    ft = _svc('feature_toggles')
    return jsonify(ft.get_all())


@bp.route('/api/settings/features', methods=['PUT'])
@require_auth
def update_features():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    ft = _svc('feature_toggles')
    updated = ft.set_multiple(data, getattr(request, 'user_id', None))
    return jsonify({'updated': updated})


# ── Captive Portal ──

@bp.route('/api/captive-portal/authenticate', methods=['POST'])
def captive_portal_auth():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_CAPTIVE_PORTAL'):
        return jsonify({'error': 'Captive portal is disabled'}), 403

    data = request.get_json()
    portal = _svc('captive_portal')

    # Check optional password
    import os
    portal_pass = os.getenv('CAPTIVE_PORTAL_PASSWORD', '')
    if portal_pass and data.get('password') != portal_pass:
        return jsonify({'error': 'Invalid portal password'}), 401

    mac = data.get('mac', '')
    ip = request.remote_addr

    try:
        portal.authenticate_client(mac, ip)
        return jsonify({'authenticated': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── VPN Passthrough ──

@bp.route('/api/vpn/status', methods=['GET'])
@require_auth
def vpn_status():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_VPN_PASSTHROUGH'):
        return jsonify({'error': 'VPN passthrough is disabled'}), 403

    vpn = _svc('vpn_passthrough')
    return jsonify(vpn.status())


@bp.route('/api/vpn/toggle', methods=['POST'])
@require_auth
def vpn_toggle():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_VPN_PASSTHROUGH'):
        return jsonify({'error': 'VPN passthrough is disabled'}), 403

    data = request.get_json()
    vpn = _svc('vpn_passthrough')

    try:
        if data.get('enabled'):
            vpn.enable()
        else:
            vpn.disable()
        return jsonify(vpn.status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
