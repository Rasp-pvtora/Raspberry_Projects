"""Tests for AP manager."""

import pytest
from unittest.mock import patch, MagicMock
from src.ap_manager import APManager


class TestAPManager:
    def test_status_parsing(self):
        ap = APManager()
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout='active\n', returncode=0)
            status = ap.status()
            assert status['ssid']
            assert 'running' in status

    @patch('subprocess.run')
    def test_start(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        ap = APManager()
        ap.start()
        assert mock_run.call_count == 2  # hostapd + dnsmasq

    @patch('subprocess.run')
    def test_stop(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        ap = APManager()
        ap.stop()
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_setup_nat(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        ap = APManager()
        ap.setup_nat()
        assert mock_run.call_count == 4  # 4 commands

    def test_update_config(self, tmp_path):
        env_file = tmp_path / '.env'
        env_file.write_text('AP_SSID=OldSSID\nAP_CHANNEL=6\n')

        ap = APManager()
        ap._base_dir = str(tmp_path)
        ap.update_config(ssid='NewSSID', channel=11)

        content = env_file.read_text()
        assert 'AP_SSID=NewSSID' in content
        assert 'AP_CHANNEL=11' in content
