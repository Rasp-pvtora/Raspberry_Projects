"""Tests for MAC filter."""

import pytest
from src.mac_filter import MACFilter


class TestMACValidation:
    def test_valid_mac(self):
        assert MACFilter.validate_mac('AA:BB:CC:DD:EE:FF')
        assert MACFilter.validate_mac('aa:bb:cc:dd:ee:ff')
        assert MACFilter.validate_mac('00:11:22:33:44:55')

    def test_invalid_mac(self):
        assert not MACFilter.validate_mac('')
        assert not MACFilter.validate_mac('not-a-mac')
        assert not MACFilter.validate_mac('AA:BB:CC:DD:EE')  # Too short
        assert not MACFilter.validate_mac('AA:BB:CC:DD:EE:FF:00')  # Too long
        assert not MACFilter.validate_mac('GG:HH:II:JJ:KK:LL')  # Invalid hex


class TestMACFilterDB:
    def test_add_and_get_entries(self, db):
        mf = MACFilter(db)
        db.add_mac_filter('AA:BB:CC:DD:EE:FF', 'whitelist', 'Test device')
        entries = db.get_mac_filter_entries('whitelist')
        assert len(entries) == 1
        assert entries[0]['mac_address'] == 'AA:BB:CC:DD:EE:FF'

    def test_remove_entry(self, db):
        db.add_mac_filter('AA:BB:CC:DD:EE:FF', 'whitelist', 'Test')
        db.remove_mac_filter('AA:BB:CC:DD:EE:FF')
        entries = db.get_mac_filter_entries('whitelist')
        assert len(entries) == 0


class TestMACFilterAPI:
    def test_get_filter_when_enabled(self, auth_client, db):
        db.set_feature_toggle('ENABLE_MAC_FILTER', True)
        resp = auth_client.get('/api/mac-filter')
        assert resp.status_code == 200

    def test_get_filter_when_disabled(self, auth_client, db):
        db.set_feature_toggle('ENABLE_MAC_FILTER', False)
        resp = auth_client.get('/api/mac-filter')
        assert resp.status_code == 403

    def test_add_invalid_mac(self, auth_client, db):
        db.set_feature_toggle('ENABLE_MAC_FILTER', True)
        resp = auth_client.post('/api/mac-filter', json={'mac': 'invalid'})
        assert resp.status_code == 400
