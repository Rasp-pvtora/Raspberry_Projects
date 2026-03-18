"""CLI integration tests using Click's test runner.

These tests exercise the full encrypt/decrypt/provision/list-keys/rotate
pipeline using the mock adapter and a temporary keystore.

The `original_document.txt` fixture is used as a real-world test file.
"""
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.enc_decrypt.cli import cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def ks(tmp_path):
    """Return a temporary keystore path string for --store option."""
    return str(tmp_path / "keystore.json")


class TestEncryptDecryptCLI:
    def test_encrypt_and_decrypt_original_document(self, runner, tmp_path, ks):
        """End-to-end: encrypt original_document.txt, decrypt, compare bytes."""
        src = Path(__file__).parent / "original_document.txt"
        enc = str(tmp_path / "original_document.txt.enc")
        dec = str(tmp_path / "original_document.txt.dec")

        result = runner.invoke(cli, [
            "encrypt",
            "--input", str(src),
            "--output", enc,
            "--key-id", "doc-key",
            "--use-mock",
            "--store", ks,
        ])
        assert result.exit_code == 0, result.output
        assert "[OK]" in result.output

        result = runner.invoke(cli, [
            "decrypt",
            "--input", enc,
            "--output", dec,
            "--key-id", "doc-key",
            "--use-mock",
            "--store", ks,
        ])
        assert result.exit_code == 0, result.output
        assert "[OK]" in result.output
        assert Path(dec).read_bytes() == src.read_bytes()

    def test_encrypt_custom_file(self, runner, tmp_path, ks, plaintext_file):
        enc = str(tmp_path / "custom.enc")
        dec = str(tmp_path / "custom.dec")

        result = runner.invoke(cli, [
            "encrypt",
            "--input", str(plaintext_file),
            "--output", enc,
            "--key-id", "custom-key",
            "--use-mock",
            "--store", ks,
        ])
        assert result.exit_code == 0, result.output

        result = runner.invoke(cli, [
            "decrypt",
            "--input", enc,
            "--output", dec,
            "--key-id", "custom-key",
            "--use-mock",
            "--store", ks,
        ])
        assert result.exit_code == 0, result.output
        assert Path(dec).read_bytes() == plaintext_file.read_bytes()

    def test_encrypt_missing_input(self, runner, tmp_path, ks):
        result = runner.invoke(cli, [
            "encrypt",
            "--input", "/nonexistent/file.txt",
            "--output", str(tmp_path / "out.enc"),
            "--key-id", "k",
            "--use-mock",
            "--store", ks,
        ])
        assert result.exit_code != 0

    def test_encrypt_duplicate_key_id_errors(self, runner, tmp_path, ks, plaintext_file):
        enc1 = str(tmp_path / "enc1.bin")
        enc2 = str(tmp_path / "enc2.bin")

        runner.invoke(cli, ["encrypt", "--input", str(plaintext_file), "--output", enc1,
                             "--key-id", "dupe", "--use-mock", "--store", ks])

        result = runner.invoke(cli, ["encrypt", "--input", str(plaintext_file), "--output", enc2,
                                     "--key-id", "dupe", "--use-mock", "--store", ks])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_decrypt_wrong_key_id_errors(self, runner, tmp_path, ks, plaintext_file):
        enc = str(tmp_path / "enc.bin")
        runner.invoke(cli, ["encrypt", "--input", str(plaintext_file), "--output", enc,
                             "--key-id", "real-key", "--use-mock", "--store", ks])

        result = runner.invoke(cli, [
            "decrypt",
            "--input", enc,
            "--output", str(tmp_path / "dec.txt"),
            "--key-id", "wrong-key",
            "--use-mock",
            "--store", ks,
        ])
        assert result.exit_code != 0


class TestProvisionListRotateCLI:
    def test_provision(self, runner, ks):
        result = runner.invoke(cli, ["provision", "--key-id", "slot1", "--use-mock", "--store", ks])
        assert result.exit_code == 0, result.output
        assert "Provisioned" in result.output

    def test_list_keys_empty(self, runner, ks):
        result = runner.invoke(cli, ["list-keys", "--store", ks])
        assert result.exit_code == 0
        assert "empty" in result.output.lower()

    def test_list_keys_after_provision(self, runner, ks):
        runner.invoke(cli, ["provision", "--key-id", "key-a", "--use-mock", "--store", ks])
        runner.invoke(cli, ["provision", "--key-id", "key-b", "--use-mock", "--store", ks])
        result = runner.invoke(cli, ["list-keys", "--store", ks])
        assert "key-a" in result.output
        assert "key-b" in result.output

    def test_rotate(self, runner, ks):
        runner.invoke(cli, ["provision", "--key-id", "rotate-me", "--use-mock", "--store", ks])
        result = runner.invoke(cli, ["rotate", "--key-id", "rotate-me", "--use-mock", "--store", ks])
        assert result.exit_code == 0, result.output
        assert "Rotated" in result.output

    def test_rotate_nonexistent_key_errors(self, runner, ks):
        result = runner.invoke(cli, ["rotate", "--key-id", "ghost-key", "--use-mock", "--store", ks])
        assert result.exit_code != 0

    def test_no_adapter_without_use_mock(self, runner, ks):
        result = runner.invoke(cli, ["provision", "--key-id", "k", "--store", ks])
        assert result.exit_code != 0
        assert "adapter" in result.output.lower() or "mock" in result.output.lower()
