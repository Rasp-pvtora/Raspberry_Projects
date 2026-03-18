"""Unit tests for store.py (keystore)."""
import os
import pytest

from src.enc_decrypt import store as keystore
from src.enc_decrypt import crypto_core
from src.enc_decrypt.hwkey.mock_hwkey import MockHardwareKey


@pytest.fixture()
def adapter():
    return MockHardwareKey()


class TestKeystore:
    def test_store_and_load(self, keystore_path, adapter):
        dek = crypto_core.generate_data_key()
        wrapped = adapter.wrap_key(dek)
        metadata = {"alg": "AES-GCM", "nonce": "abc123=="}

        keystore.store_key("key1", wrapped, metadata, adapter.identify(), keystore_path)

        entry = keystore.load_key("key1", keystore_path)
        assert entry["key_id"] == "key1"
        assert entry["alg"] == "AES-GCM"
        assert entry["adapter"] == adapter.identify()

    def test_get_wrapped_dek_roundtrip(self, keystore_path, adapter):
        dek = crypto_core.generate_data_key()
        wrapped = adapter.wrap_key(dek)
        metadata = {"alg": "AES-GCM", "nonce": "nonce=="}

        keystore.store_key("key2", wrapped, metadata, adapter.identify(), keystore_path)

        retrieved_wrapped = keystore.get_wrapped_dek("key2", keystore_path)
        recovered_dek = adapter.unwrap_key(retrieved_wrapped)
        assert recovered_dek == dek

    def test_duplicate_key_raises(self, keystore_path, adapter):
        dek = crypto_core.generate_data_key()
        wrapped = adapter.wrap_key(dek)
        metadata = {"alg": "AES-GCM", "nonce": "n=="}

        keystore.store_key("dup-key", wrapped, metadata, adapter.identify(), keystore_path)
        with pytest.raises(KeyError, match="already exists"):
            keystore.store_key("dup-key", wrapped, metadata, adapter.identify(), keystore_path)

    def test_list_keys(self, keystore_path, adapter):
        for i in range(3):
            dek = crypto_core.generate_data_key()
            w = adapter.wrap_key(dek)
            keystore.store_key(f"key-{i}", w, {"alg": "AES-GCM", "nonce": ""}, adapter.identify(), keystore_path)

        keys = keystore.list_keys(keystore_path)
        assert sorted(keys) == ["key-0", "key-1", "key-2"]

    def test_missing_key_raises(self, keystore_path):
        with pytest.raises(KeyError, match="not found"):
            keystore.load_key("nonexistent", keystore_path)

    def test_rotate_key(self, keystore_path, adapter):
        dek = crypto_core.generate_data_key()
        wrapped = adapter.wrap_key(dek)
        keystore.store_key("rot-key", wrapped, {"alg": "AES-GCM", "nonce": ""}, adapter.identify(), keystore_path)

        new_dek = crypto_core.generate_data_key()
        new_wrapped = adapter.wrap_key(new_dek)
        keystore.rotate_key("rot-key", new_wrapped, {"alg": "AES-GCM", "nonce": ""}, adapter.identify(), keystore_path)

        entry = keystore.load_key("rot-key", keystore_path)
        assert "rotated" in entry
        recovered = adapter.unwrap_key(keystore.get_wrapped_dek("rot-key", keystore_path))
        assert recovered == new_dek

    def test_delete_key(self, keystore_path, adapter):
        dek = crypto_core.generate_data_key()
        w = adapter.wrap_key(dek)
        keystore.store_key("del-key", w, {"alg": "AES-GCM", "nonce": ""}, adapter.identify(), keystore_path)

        keystore.delete_key("del-key", keystore_path)
        assert "del-key" not in keystore.list_keys(keystore_path)

    def test_empty_store_returns_empty_list(self, keystore_path):
        keys = keystore.list_keys(keystore_path)
        assert keys == []
