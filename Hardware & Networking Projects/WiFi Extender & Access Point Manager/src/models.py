"""Database models and helper for SQLite access."""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv('DB_PATH', 'data/wifi_extender.db')


def get_db_path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), DB_PATH)


@contextmanager
def get_db():
    """Context manager for database connections."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class Database:
    """Database operations wrapper."""

    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ── Users ──

    def get_user_by_username(self, username):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

    def get_user_by_id(self, user_id):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()

    def create_user(self, username, password_hash, role='admin'):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()

    def update_user_password(self, user_id, password_hash):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user_id)
            )
            conn.commit()

    def update_last_login(self, user_id):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()

    # ── Clients ──

    def upsert_client(self, mac_address, hostname='', ip_address='', interface='wlan0'):
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM clients WHERE mac_address = ?", (mac_address,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE clients SET hostname = ?, ip_address = ?, interface = ?, "
                    "last_seen = CURRENT_TIMESTAMP WHERE mac_address = ?",
                    (hostname, ip_address, interface, mac_address)
                )
                conn.commit()
                return existing['id']
            else:
                cursor = conn.execute(
                    "INSERT INTO clients (mac_address, hostname, ip_address, interface) "
                    "VALUES (?, ?, ?, ?)",
                    (mac_address, hostname, ip_address, interface)
                )
                conn.commit()
                return cursor.lastrowid

    def get_all_clients(self):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM clients ORDER BY last_seen DESC").fetchall()

    def get_client_by_mac(self, mac_address):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM clients WHERE mac_address = ?", (mac_address,)
            ).fetchone()

    def block_client(self, mac_address, blocked=True):
        with self._connect() as conn:
            conn.execute(
                "UPDATE clients SET is_blocked = ? WHERE mac_address = ?",
                (1 if blocked else 0, mac_address)
            )
            conn.commit()

    # ── Connection Log ──

    def log_connection(self, client_id, event_type, ip_address='', signal_dbm=0):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO connection_log (client_id, event_type, ip_address, signal_dbm) "
                "VALUES (?, ?, ?, ?)",
                (client_id, event_type, ip_address, signal_dbm)
            )
            conn.commit()

    def get_connection_log(self, limit=100, offset=0):
        with self._connect() as conn:
            return conn.execute(
                "SELECT cl.*, c.mac_address, c.hostname FROM connection_log cl "
                "JOIN clients c ON cl.client_id = c.id "
                "ORDER BY cl.timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()

    # ── Bandwidth ──

    def store_bandwidth(self, client_id, rx_bytes, tx_bytes, rx_rate_kbps=0, tx_rate_kbps=0):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO bandwidth_readings (client_id, rx_bytes, tx_bytes, "
                "rx_rate_kbps, tx_rate_kbps) VALUES (?, ?, ?, ?, ?)",
                (client_id, rx_bytes, tx_bytes, rx_rate_kbps, tx_rate_kbps)
            )
            conn.commit()

    def get_bandwidth_history(self, hours=24, client_id=None):
        with self._connect() as conn:
            if client_id:
                return conn.execute(
                    "SELECT * FROM bandwidth_readings "
                    "WHERE client_id = ? AND recorded_at >= datetime('now', ?) "
                    "ORDER BY recorded_at",
                    (client_id, f'-{hours} hours')
                ).fetchall()
            return conn.execute(
                "SELECT * FROM bandwidth_readings "
                "WHERE recorded_at >= datetime('now', ?) ORDER BY recorded_at",
                (f'-{hours} hours',)
            ).fetchall()

    # ── MAC Filter ──

    def get_mac_filter_entries(self, list_type=None):
        with self._connect() as conn:
            if list_type:
                return conn.execute(
                    "SELECT * FROM mac_filter WHERE list_type = ? ORDER BY created_at DESC",
                    (list_type,)
                ).fetchall()
            return conn.execute(
                "SELECT * FROM mac_filter ORDER BY created_at DESC"
            ).fetchall()

    def add_mac_filter(self, mac_address, list_type, description='', added_by=None):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO mac_filter "
                "(mac_address, list_type, description, added_by) VALUES (?, ?, ?, ?)",
                (mac_address, list_type, description, added_by)
            )
            conn.commit()

    def remove_mac_filter(self, mac_address):
        with self._connect() as conn:
            conn.execute("DELETE FROM mac_filter WHERE mac_address = ?", (mac_address,))
            conn.commit()

    # ── QoS Rules ──

    def get_qos_rules(self):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM qos_rules WHERE enabled = 1 ORDER BY priority"
            ).fetchall()

    def set_qos_rule(self, client_id, mac_address, down_limit_kbps, up_limit_kbps, priority=5):
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM qos_rules WHERE mac_address = ?", (mac_address,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE qos_rules SET down_limit_kbps = ?, up_limit_kbps = ?, "
                    "priority = ? WHERE mac_address = ?",
                    (down_limit_kbps, up_limit_kbps, priority, mac_address)
                )
            else:
                conn.execute(
                    "INSERT INTO qos_rules (client_id, mac_address, down_limit_kbps, "
                    "up_limit_kbps, priority) VALUES (?, ?, ?, ?, ?)",
                    (client_id, mac_address, down_limit_kbps, up_limit_kbps, priority)
                )
            conn.commit()

    def delete_qos_rule(self, mac_address):
        with self._connect() as conn:
            conn.execute("DELETE FROM qos_rules WHERE mac_address = ?", (mac_address,))
            conn.commit()

    # ── WiFi Schedule ──

    def get_wifi_schedules(self):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM wifi_schedule ORDER BY id").fetchall()

    def set_wifi_schedule(self, schedules):
        with self._connect() as conn:
            conn.execute("DELETE FROM wifi_schedule")
            for sched in schedules:
                conn.execute(
                    "INSERT INTO wifi_schedule (day_of_week, on_time, off_time, enabled) "
                    "VALUES (?, ?, ?, ?)",
                    (sched['day'], sched['on_time'], sched['off_time'],
                     1 if sched.get('enabled', True) else 0)
                )
            conn.commit()

    # ── Health Checks ──

    def store_health_check(self, latency_ms, packet_loss_pct, dns_resolve_ms, internet_up):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO health_checks (latency_ms, packet_loss_pct, dns_resolve_ms, "
                "internet_up) VALUES (?, ?, ?, ?)",
                (latency_ms, packet_loss_pct, dns_resolve_ms, 1 if internet_up else 0)
            )
            conn.commit()

    def get_health_history(self, hours=24):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM health_checks WHERE checked_at >= datetime('now', ?) "
                "ORDER BY checked_at",
                (f'-{hours} hours',)
            ).fetchall()

    def get_latest_health(self):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM health_checks ORDER BY checked_at DESC LIMIT 1"
            ).fetchone()

    # ── Feature Toggles ──

    def get_feature_toggles(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM feature_toggles").fetchall()
            return {row['feature_key']: bool(row['enabled']) for row in rows}

    def set_feature_toggle(self, feature_key, enabled, updated_by=None):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO feature_toggles (feature_key, enabled, updated_by) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(feature_key) DO UPDATE SET enabled = ?, "
                "updated_at = CURRENT_TIMESTAMP, updated_by = ?",
                (feature_key, 1 if enabled else 0, updated_by,
                 1 if enabled else 0, updated_by)
            )
            conn.commit()
