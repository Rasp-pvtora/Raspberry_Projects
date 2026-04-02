"""Tests for QoS manager."""

import pytest
from unittest.mock import patch, MagicMock
from src.qos_manager import QoSManager


class TestQoSManager:
    @patch('subprocess.run')
    def test_init_qdisc(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        qos = QoSManager()
        qos.init_qdisc()
        assert qos.initialized
        assert mock_run.call_count == 3  # del + add + class

    @patch('subprocess.run')
    def test_set_client_limit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        qos = QoSManager()
        qos.initialized = True
        class_id = qos.set_client_limit('10.0.0.15', 5000, 2000)
        assert class_id >= 10
        assert mock_run.call_count == 2  # class + filter

    @patch('subprocess.run')
    def test_reset_all(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        qos = QoSManager()
        qos.initialized = True
        qos.reset_all()
        assert not qos.initialized
