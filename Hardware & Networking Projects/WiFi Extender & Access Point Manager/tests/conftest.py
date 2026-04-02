"""Shared test fixtures."""

import os
import sys
import pytest
import tempfile

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['AUTH_SESSION_HOURS'] = '24'
os.environ['DB_PATH'] = ':memory:'


@pytest.fixture
def db():
    """Create an in-memory test database."""
    import sqlite3
    from init_db import SCHEMA, DEFAULT_FEATURES, DEFAULT_SCHEDULE

    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)

    for key, enabled in DEFAULT_FEATURES:
        conn.execute(
            "INSERT INTO feature_toggles (feature_key, enabled) VALUES (?, ?)",
            (key, 1 if enabled else 0)
        )

    for day, on_time, off_time in DEFAULT_SCHEDULE:
        conn.execute(
            "INSERT INTO wifi_schedule (day_of_week, on_time, off_time) VALUES (?, ?, ?)",
            (day, on_time, off_time)
        )

    import bcrypt
    pw = bcrypt.hashpw(b'testpass', bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ('admin', pw, 'admin')
    )
    conn.commit()
    conn.close()

    # Create Database instance using temp file
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp_path = tmp.name
    tmp.close()

    conn = sqlite3.connect(tmp_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)

    for key, enabled in DEFAULT_FEATURES:
        conn.execute(
            "INSERT INTO feature_toggles (feature_key, enabled) VALUES (?, ?)",
            (key, 1 if enabled else 0)
        )
    for day, on_time, off_time in DEFAULT_SCHEDULE:
        conn.execute(
            "INSERT INTO wifi_schedule (day_of_week, on_time, off_time) VALUES (?, ?, ?)",
            (day, on_time, off_time)
        )
    pw = bcrypt.hashpw(b'testpass', bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ('admin', pw, 'admin')
    )
    conn.commit()
    conn.close()

    from src.models import Database
    database = Database(db_path=tmp_path)

    yield database

    os.unlink(tmp_path)


@pytest.fixture
def app(db):
    """Create Flask test app."""
    from src.app import app as flask_app, socketio

    flask_app.config['TESTING'] = True
    flask_app.config['services']['db'] = db

    # Create feature toggles with test db
    from src.feature_toggles import FeatureToggles
    ft = FeatureToggles(db)
    flask_app.config['services']['feature_toggles'] = ft

    yield flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_token(db):
    """Generate a valid JWT for testing."""
    from src.auth import generate_token
    return generate_token(1)


@pytest.fixture
def auth_client(client, auth_token):
    """Test client with authentication cookie."""
    client.set_cookie('token', auth_token)
    return client
