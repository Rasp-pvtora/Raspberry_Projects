"""Network health monitoring routes."""

from flask import Blueprint, request, jsonify, render_template, current_app
from src.auth import require_auth

bp = Blueprint('health', __name__)


def _svc(name):
    return current_app.config['services'][name]


@bp.route('/health')
@require_auth
def health_page():
    return render_template('health.html')


@bp.route('/connection-log')
@require_auth
def connection_log_page():
    return render_template('connection_log.html')


@bp.route('/api/health', methods=['GET'])
@require_auth
def get_health():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_HEALTH_MONITOR'):
        return jsonify({'error': 'Health monitoring is disabled'}), 403

    db = _svc('db')
    latest = db.get_latest_health()
    if latest:
        return jsonify({
            'latency_ms': latest['latency_ms'],
            'packet_loss_pct': latest['packet_loss_pct'],
            'dns_resolve_ms': latest['dns_resolve_ms'],
            'internet_up': bool(latest['internet_up']),
            'checked_at': latest['checked_at'],
        })
    return jsonify({'latency_ms': -1, 'packet_loss_pct': 100, 'dns_resolve_ms': -1,
                    'internet_up': False})


@bp.route('/api/health/history', methods=['GET'])
@require_auth
def get_health_history():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_HEALTH_MONITOR'):
        return jsonify({'error': 'Health monitoring is disabled'}), 403

    hours = request.args.get('hours', 24, type=int)
    hours = min(hours, 720)

    db = _svc('db')
    history = db.get_health_history(hours=hours)
    return jsonify([
        {
            'latency_ms': h['latency_ms'],
            'packet_loss_pct': h['packet_loss_pct'],
            'dns_resolve_ms': h['dns_resolve_ms'],
            'internet_up': bool(h['internet_up']),
            'checked_at': h['checked_at'],
        }
        for h in history
    ])


@bp.route('/api/connections/log', methods=['GET'])
@require_auth
def get_connection_log():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_CONNECTION_LOG'):
        return jsonify({'error': 'Connection logging is disabled'}), 403

    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = min(limit, 500)

    db = _svc('db')
    logs = db.get_connection_log(limit=limit, offset=offset)
    return jsonify([dict(log) for log in logs])


@bp.route('/api/channels/scan', methods=['GET'])
@require_auth
def scan_channels():
    scanner = _svc('channel_scanner')
    try:
        aps = scanner.scan()
        usage = scanner.get_channel_usage()
        best_24 = scanner.get_best_channel('2.4')
        return jsonify({
            'nearby_aps': aps,
            'channel_usage': usage,
            'recommended_24ghz': best_24,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
