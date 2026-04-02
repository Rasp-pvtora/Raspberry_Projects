"""Tests for bandwidth tracker."""

import pytest
from src.bandwidth_tracker import BandwidthTracker
from unittest.mock import MagicMock


class TestBandwidthTracker:
    def test_calculate_rates_empty(self):
        db = MagicMock()
        tracker = BandwidthTracker(db)
        rates = tracker._calculate_rates({})
        assert rates == {}

    def test_calculate_rates_no_previous(self):
        db = MagicMock()
        tracker = BandwidthTracker(db)
        tracker.previous = {}
        current = {'10.0.0.10': {'rx': 1000, 'tx': 500}}
        rates = tracker._calculate_rates(current)
        assert rates == {}  # No previous data to compare

    def test_calculate_rates_with_previous(self):
        db = MagicMock()
        tracker = BandwidthTracker(db, interval=5)
        tracker.previous = {'10.0.0.10': {'rx': 1000, 'tx': 500}}
        current = {'10.0.0.10': {'rx': 6000, 'tx': 2500}}
        rates = tracker._calculate_rates(current)

        assert '10.0.0.10' in rates
        # (6000-1000)*8/5/1000 = 8 kbps
        assert rates['10.0.0.10']['rx_kbps'] == 8.0
        # (2500-500)*8/5/1000 = 3.2 kbps
        assert rates['10.0.0.10']['tx_kbps'] == 3.2

    def test_start_stop(self):
        db = MagicMock()
        tracker = BandwidthTracker(db, interval=1)
        tracker.start()
        assert tracker.running
        tracker.stop()
        assert not tracker.running
