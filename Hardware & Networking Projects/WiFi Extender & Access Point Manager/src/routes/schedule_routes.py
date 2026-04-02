"""WiFi schedule routes."""

from flask import Blueprint, request, jsonify, render_template, current_app
from src.auth import require_auth

bp = Blueprint('schedule', __name__)

VALID_DAYS = {'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}


def _svc(name):
    return current_app.config['services'][name]


@bp.route('/schedule')
@require_auth
def schedule_page():
    return render_template('schedule.html')


@bp.route('/api/schedule', methods=['GET'])
@require_auth
def get_schedule():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_WIFI_SCHEDULE'):
        return jsonify({'error': 'WiFi schedule is disabled'}), 403

    db = _svc('db')
    schedules = db.get_wifi_schedules()
    return jsonify([
        {
            'day': s['day_of_week'],
            'on_time': s['on_time'],
            'off_time': s['off_time'],
            'enabled': bool(s['enabled']),
        }
        for s in schedules
    ])


@bp.route('/api/schedule', methods=['PUT'])
@require_auth
def update_schedule():
    ft = _svc('feature_toggles')
    if not ft.is_enabled('ENABLE_WIFI_SCHEDULE'):
        return jsonify({'error': 'WiFi schedule is disabled'}), 403

    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({'error': 'Schedule list required'}), 400

    for entry in data:
        if entry.get('day') not in VALID_DAYS:
            return jsonify({'error': f"Invalid day: {entry.get('day')}"}), 400

    db = _svc('db')
    db.set_wifi_schedule(data)

    # Reload scheduler
    scheduler = _svc('wifi_scheduler')
    scheduler.load_schedule()

    return jsonify({'updated': True, 'count': len(data)})


@bp.route('/api/schedule/override', methods=['POST'])
@require_auth
def schedule_override():
    data = request.get_json()
    action = data.get('action') if data else None
    scheduler = _svc('wifi_scheduler')

    if action == 'force_on':
        scheduler.force_on()
        return jsonify({'status': 'forced_on'})
    elif action == 'force_off':
        scheduler.force_off()
        return jsonify({'status': 'forced_off'})
    elif action == 'clear':
        scheduler.clear_override()
        return jsonify({'status': 'override_cleared'})
    return jsonify({'error': 'Invalid action'}), 400
