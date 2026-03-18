"""Basic import smoke tests — ensure all modules load without errors."""
import importlib


def test_import_cli():
    mod = importlib.import_module("src.enc_decrypt.cli")
    assert hasattr(mod, "cli")


def test_import_crypto_core():
    mod = importlib.import_module("src.enc_decrypt.crypto_core")
    assert hasattr(mod, "generate_data_key")
    assert hasattr(mod, "encrypt_file")
    assert hasattr(mod, "decrypt_file")


def test_import_mock_hwkey():
    mod = importlib.import_module("src.enc_decrypt.hwkey.mock_hwkey")
    assert hasattr(mod, "MockHardwareKey")


def test_import_hwkey_base():
    mod = importlib.import_module("src.enc_decrypt.hwkey.base")
    assert hasattr(mod, "IHardwareKey")


def test_import_store():
    mod = importlib.import_module("src.enc_decrypt.store")
    assert hasattr(mod, "store_key")
    assert hasattr(mod, "load_key")
    assert hasattr(mod, "list_keys")
    assert hasattr(mod, "rotate_key")
    assert hasattr(mod, "delete_key")
