"""Bandwidth monitoring routes."""

from flask import Blueprint, request, jsonify, render_template, current_app
from src.auth import require_auth

bp = Blueprint('bandwidth', __name__)


def _svc(name):
    return current_app.config['services'][name]


@bp.route('/bandwidth')
@require_auth
def bandwidth_page():
    return render_template('bandwidth.html')


@bp.route('/api/bandwidth', methods=['GET'])
@require_auth
def get_bandwidth():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_BANDWIDTH_MONITOR'):
        return jsonify({'error': 'Bandwidth monitoring is disabled'}), 403

    tracker = _svc('bandwidth_tracker')
    rates = tracker.get_current_rates()

    total_rx = sum(r['rx_kbps'] for r in rates.values()) if rates else 0
    total_tx = sum(r['tx_kbps'] for r in rates.values()) if rates else 0

    return jsonify({
        'total': {'rx_kbps': round(total_rx, 2), 'tx_kbps': round(total_tx, 2)},
        'per_client': [
            {'ip': ip, 'rx_kbps': d['rx_kbps'], 'tx_kbps': d['tx_kbps']}
            for ip, d in rates.items()
        ],
    })


@bp.route('/api/bandwidth/history', methods=['GET'])
@require_auth
def get_bandwidth_history():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_BANDWIDTH_MONITOR'):
        return jsonify({'error': 'Bandwidth monitoring is disabled'}), 403

    hours = request.args.get('hours', 24, type=int)
    hours = min(hours, 720)  # Cap at 30 days

    db = _svc('db')
    history = db.get_bandwidth_history(hours=hours)

    labels = []
    total_rx = []
    total_tx = []
    for row in history:
        labels.append(row['recorded_at'])
        total_rx.append(row['rx_rate_kbps'] or 0)
        total_tx.append(row['tx_rate_kbps'] or 0)

    return jsonify({
        'labels': labels,
        'total_rx': total_rx,
        'total_tx': total_tx,
    })
