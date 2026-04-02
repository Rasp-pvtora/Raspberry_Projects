"""Feature toggles — synchronized between .env file and SQLite database."""

import os
import logging

logger = logging.getLogger(__name__)

FEATURE_KEYS = [
    'ENABLE_AUTO_SETUP',
    'ENABLE_SSID_MANAGER',
    'ENABLE_CLIENT_LIST',
    'ENABLE_BANDWIDTH_MONITOR',
    'ENABLE_MAC_FILTER',
    'ENABLE_CAPTIVE_PORTAL',
    'ENABLE_QOS',
    'ENABLE_WIFI_SCHEDULE',
    'ENABLE_AUTO_CHANNEL',
    'ENABLE_DNS_CONFIG',
    'ENABLE_DUAL_BAND',
    'ENABLE_VPN_PASSTHROUGH',
    'ENABLE_NOTIFICATIONS',
    'ENABLE_CONNECTION_LOG',
    'ENABLE_HEALTH_MONITOR',
]


class FeatureToggles:
    def __init__(self, db):
        self.db = db
        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._env_path = os.path.join(self._base_dir, '.env')

    def get_all(self):
        """Get all feature toggle states from database."""
        toggles = self.db.get_feature_toggles()
        # Fill in any missing keys from environment
        for key in FEATURE_KEYS:
            if key not in toggles:
                toggles[key] = os.getenv(key, 'false').lower() == 'true'
        return toggles

    def is_enabled(self, feature_key):
        """Check if a specific feature is enabled."""
        toggles = self.db.get_feature_toggles()
        if feature_key in toggles:
            return toggles[feature_key]
        return os.getenv(feature_key, 'false').lower() == 'true'

    def set_toggle(self, feature_key, enabled, updated_by=None):
        """Set a feature toggle and sync to both DB and .env."""
        if feature_key not in FEATURE_KEYS:
            raise ValueError(f"Unknown feature key: {feature_key}")

        # Update database
        self.db.set_feature_toggle(feature_key, enabled, updated_by)

        # Update os.environ
        os.environ[feature_key] = 'true' if enabled else 'false'

        # Update .env file
        self._update_env(feature_key, enabled)

        logger.info("Feature toggle %s set to %s", feature_key, enabled)

    def set_multiple(self, updates, updated_by=None):
        """Set multiple feature toggles at once."""
        updated = []
        for feature_key, enabled in updates.items():
            if feature_key in FEATURE_KEYS:
                self.set_toggle(feature_key, enabled, updated_by)
                updated.append(feature_key)
        return updated

    def _update_env(self, key, enabled):
        """Update a single key in the .env file."""
        value = 'true' if enabled else 'false'
        if not os.path.exists(self._env_path):
            return

        with open(self._env_path, 'r') as f:
            lines = f.readlines()

        found = False
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and '=' in stripped:
                line_key = stripped.split('=', 1)[0]
                if line_key == key:
                    new_lines.append(f"{key}={value}\n")
                    found = True
                    continue
            new_lines.append(line)

        if not found:
            new_lines.append(f"{key}={value}\n")

        with open(self._env_path, 'w') as f:
            f.writelines(new_lines)
