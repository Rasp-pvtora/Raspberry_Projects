#!/usr/bin/env python3
"""Initialize the SQLite database with all required tables."""

import sqlite3
import os
import sys

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'data/wifi_extender.db')

SCHEMA = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

-- Clients table
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_address TEXT NOT NULL UNIQUE,
    hostname TEXT,
    friendly_name TEXT,
    ip_address TEXT,
    interface TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_blocked BOOLEAN DEFAULT 0
);

-- Connection log
CREATE TABLE IF NOT EXISTS connection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    ip_address TEXT,
    signal_dbm INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- Bandwidth readings
CREATE TABLE IF NOT EXISTS bandwidth_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    rx_bytes INTEGER NOT NULL,
    tx_bytes INTEGER NOT NULL,
    rx_rate_kbps REAL,
    tx_rate_kbps REAL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- MAC filter
CREATE TABLE IF NOT EXISTS mac_filter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_address TEXT NOT NULL UNIQUE,
    list_type TEXT NOT NULL,
    description TEXT,
    added_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (added_by) REFERENCES users(id)
);

-- QoS rules
CREATE TABLE IF NOT EXISTS qos_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    mac_address TEXT NOT NULL,
    down_limit_kbps INTEGER,
    up_limit_kbps INTEGER,
    priority INTEGER DEFAULT 5,
    enabled BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- WiFi schedule
CREATE TABLE IF NOT EXISTS wifi_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_of_week TEXT NOT NULL,
    on_time TEXT NOT NULL,
    off_time TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1
);

-- Health checks
CREATE TABLE IF NOT EXISTS health_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latency_ms REAL,
    packet_loss_pct REAL,
    dns_resolve_ms REAL,
    internet_up BOOLEAN,
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Feature toggles
CREATE TABLE IF NOT EXISTS feature_toggles (
    feature_key TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_connection_log_timestamp ON connection_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_bandwidth_recorded ON bandwidth_readings(recorded_at);
CREATE INDEX IF NOT EXISTS idx_health_checked ON health_checks(checked_at);
CREATE INDEX IF NOT EXISTS idx_clients_mac ON clients(mac_address);
"""

DEFAULT_FEATURES = [
    ('ENABLE_AUTO_SETUP', True),
    ('ENABLE_SSID_MANAGER', True),
    ('ENABLE_CLIENT_LIST', True),
    ('ENABLE_BANDWIDTH_MONITOR', True),
    ('ENABLE_MAC_FILTER', False),
    ('ENABLE_CAPTIVE_PORTAL', False),
    ('ENABLE_QOS', False),
    ('ENABLE_WIFI_SCHEDULE', False),
    ('ENABLE_AUTO_CHANNEL', True),
    ('ENABLE_DNS_CONFIG', True),
    ('ENABLE_DUAL_BAND', False),
    ('ENABLE_VPN_PASSTHROUGH', False),
    ('ENABLE_NOTIFICATIONS', False),
    ('ENABLE_CONNECTION_LOG', True),
    ('ENABLE_HEALTH_MONITOR', True),
]

DEFAULT_SCHEDULE = [
    ('mon', '07:00', '23:00'),
    ('tue', '07:00', '23:00'),
    ('wed', '07:00', '23:00'),
    ('thu', '07:00', '23:00'),
    ('fri', '07:00', '23:00'),
    ('sat', '07:00', '23:00'),
    ('sun', '07:00', '23:00'),
]


def init_database():
    """Create database tables and seed default data."""
    os.makedirs(os.path.dirname(DB_PATH) or '.', exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)

    # Seed default feature toggles
    for key, enabled in DEFAULT_FEATURES:
        env_val = os.getenv(key, str(enabled)).lower()
        is_enabled = 1 if env_val == 'true' else 0
        conn.execute(
            "INSERT OR IGNORE INTO feature_toggles (feature_key, enabled) VALUES (?, ?)",
            (key, is_enabled)
        )

    # Seed default WiFi schedule
    existing = conn.execute("SELECT COUNT(*) FROM wifi_schedule").fetchone()[0]
    if existing == 0:
        for day, on_time, off_time in DEFAULT_SCHEDULE:
            conn.execute(
                "INSERT INTO wifi_schedule (day_of_week, on_time, off_time) VALUES (?, ?, ?)",
                (day, on_time, off_time)
            )

    # Create default admin user if no users exist
    existing_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing_users == 0:
        import bcrypt
        password_hash = bcrypt.hashpw(b'changeme', bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ('admin', password_hash, 'admin')
        )
        print("Default admin user created — username: admin, password: changeme")
        print("WARNING: Change the default password on first login!")

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


if __name__ == '__main__':
    init_database()
