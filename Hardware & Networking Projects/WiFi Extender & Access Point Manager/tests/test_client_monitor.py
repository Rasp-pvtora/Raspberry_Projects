"""Tests for client monitor."""

import pytest
from src.client_monitor import ClientMonitor


class TestClientMonitor:
    def test_parse_iw_output(self):
        monitor = ClientMonitor()
        output = """Station aa:bb:cc:dd:ee:ff (on wlan0)
\tinactive time:\t120 ms
\trx bytes:\t123456
\ttx bytes:\t654321
\tsignal:\t\t-42 dBm
\tconnected time:\t3600 seconds
Station 11:22:33:44:55:66 (on wlan0)
\tinactive time:\t50 ms
\trx bytes:\t99999
\ttx bytes:\t11111
\tsignal:\t\t-65 dBm
\tconnected time:\t1200 seconds"""

        stations = monitor._parse_iw_output(output)
        assert len(stations) == 2

        assert 'AA:BB:CC:DD:EE:FF' in stations
        s1 = stations['AA:BB:CC:DD:EE:FF']
        assert s1['signal'] == -42
        assert s1['rx_bytes'] == 123456
        assert s1['tx_bytes'] == 654321
        assert s1['connected_time'] == 3600

        assert '11:22:33:44:55:66'.upper() in stations
        s2 = stations['11:22:33:44:55:66'.upper()]
        assert s2['signal'] == -65

    def test_parse_empty_output(self):
        monitor = ClientMonitor()
        stations = monitor._parse_iw_output('')
        assert stations == {}

    def test_parse_malformed_output(self):
        monitor = ClientMonitor()
        stations = monitor._parse_iw_output('random garbage\nmore garbage')
        assert stations == {}
