"""Tests for feature toggles."""

import pytest
from src.feature_toggles import FeatureToggles, FEATURE_KEYS


class TestFeatureToggles:
    def test_get_all_defaults(self, db):
        ft = FeatureToggles(db)
        toggles = ft.get_all()
        assert 'ENABLE_AUTO_SETUP' in toggles
        assert toggles['ENABLE_AUTO_SETUP'] is True
        assert toggles['ENABLE_MAC_FILTER'] is False

    def test_set_toggle(self, db):
        ft = FeatureToggles(db)
        ft.set_toggle('ENABLE_QOS', True)
        assert ft.is_enabled('ENABLE_QOS') is True

        ft.set_toggle('ENABLE_QOS', False)
        assert ft.is_enabled('ENABLE_QOS') is False

    def test_set_invalid_key(self, db):
        ft = FeatureToggles(db)
        with pytest.raises(ValueError):
            ft.set_toggle('INVALID_KEY', True)

    def test_set_multiple(self, db):
        ft = FeatureToggles(db)
        updated = ft.set_multiple({
            'ENABLE_QOS': True,
            'ENABLE_CAPTIVE_PORTAL': True,
            'INVALID': True,  # Should be ignored
        })
        assert 'ENABLE_QOS' in updated
        assert 'ENABLE_CAPTIVE_PORTAL' in updated
        assert 'INVALID' not in updated

    def test_all_feature_keys_exist(self, db):
        ft = FeatureToggles(db)
        toggles = ft.get_all()
        for key in FEATURE_KEYS:
            assert key in toggles


class TestFeatureTogglesAPI:
    def test_get_features(self, auth_client):
        resp = auth_client.get('/api/settings/features')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'ENABLE_AUTO_SETUP' in data

    def test_update_features(self, auth_client):
        resp = auth_client.put('/api/settings/features', json={
            'ENABLE_QOS': True,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'ENABLE_QOS' in data['updated']
