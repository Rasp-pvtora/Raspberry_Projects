"""Tests for database operations."""

import os
import tempfile

# Use temp DB for tests
_tmp = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_PATH"] = _tmp

from src.services.db import init_db, log_recognition, get_recognition_history, \
    update_learning_progress, get_learning_progress, get_setting, set_setting, DB_PATH


class TestDatabase:
    @classmethod
    def setup_class(cls):
        init_db()

    def test_recognition_log(self):
        log_recognition("A", 0.95, "asl")
        log_recognition("B", 0.88, "asl", sentence="A B")
        history = get_recognition_history(10)
        assert len(history) >= 2
        assert history[0]["sign_label"] in ("A", "B")

    def test_learning_progress(self):
        update_learning_progress("A", "asl", True)
        update_learning_progress("A", "asl", False)
        progress = get_learning_progress("asl")
        found = [p for p in progress if p["sign_label"] == "A"]
        assert len(found) == 1
        assert found[0]["attempts"] == 2
        assert found[0]["correct"] == 1

    def test_settings(self):
        set_setting("test_key", "test_value")
        assert get_setting("test_key") == "test_value"
        set_setting("test_key", "updated")
        assert get_setting("test_key") == "updated"

    def test_get_missing_setting(self):
        assert get_setting("nonexistent") is None
        assert get_setting("nonexistent", "default") == "default"
