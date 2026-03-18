"""Unit tests for crypto_core: encrypt/decrypt roundtrip, bad inputs."""
import os
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag

from src.enc_decrypt import crypto_core


class TestGenerateDataKey:
    def test_length(self):
        key = crypto_core.generate_data_key()
        assert len(key) == 32

    def test_randomness(self):
        keys = {crypto_core.generate_data_key() for _ in range(10)}
        assert len(keys) == 10, "Keys should be unique (random)"


class TestEncryptDecryptRoundtrip:
    def test_small_file(self, tmp_path, plaintext_file):
        out_enc = tmp_path / "enc.bin"
        out_dec = tmp_path / "dec.txt"

        dek = crypto_core.generate_data_key()
        metadata = crypto_core.encrypt_file(str(plaintext_file), str(out_enc), dek)

        assert out_enc.exists()
        assert metadata["alg"] == "AES-GCM"
        assert "nonce" in metadata

        crypto_core.decrypt_file(str(out_enc), str(out_dec), dek, metadata)

        assert out_dec.read_bytes() == plaintext_file.read_bytes()

    def test_original_document(self, tmp_path, original_document):
        """Encrypt and decrypt tests/original_document.txt."""
        out_enc = tmp_path / "original_document.txt.enc"
        out_dec = tmp_path / "original_document.txt.dec"

        dek = crypto_core.generate_data_key()
        metadata = crypto_core.encrypt_file(str(original_document), str(out_enc), dek)
        crypto_core.decrypt_file(str(out_enc), str(out_dec), dek, metadata)

        original_bytes = original_document.read_bytes()
        decrypted_bytes = out_dec.read_bytes()
        assert decrypted_bytes == original_bytes

    def test_empty_file(self, tmp_path):
        empty = tmp_path / "empty.txt"
        empty.write_bytes(b"")
        out_enc = tmp_path / "empty.enc"
        out_dec = tmp_path / "empty.dec"

        dek = crypto_core.generate_data_key()
        metadata = crypto_core.encrypt_file(str(empty), str(out_enc), dek)
        crypto_core.decrypt_file(str(out_enc), str(out_dec), dek, metadata)

        assert out_dec.read_bytes() == b""

    def test_binary_file(self, tmp_path):
        src = tmp_path / "bin_data.bin"
        src.write_bytes(os.urandom(4096))
        out_enc = tmp_path / "bin_data.enc"
        out_dec = tmp_path / "bin_data.dec"

        dek = crypto_core.generate_data_key()
        metadata = crypto_core.encrypt_file(str(src), str(out_enc), dek)
        crypto_core.decrypt_file(str(out_enc), str(out_dec), dek, metadata)

        assert out_dec.read_bytes() == src.read_bytes()

    def test_wrong_dek_raises(self, tmp_path, plaintext_file):
        out_enc = tmp_path / "enc.bin"
        out_dec = tmp_path / "dec.txt"

        dek = crypto_core.generate_data_key()
        metadata = crypto_core.encrypt_file(str(plaintext_file), str(out_enc), dek)

        wrong_dek = crypto_core.generate_data_key()
        with pytest.raises(Exception):
            crypto_core.decrypt_file(str(out_enc), str(out_dec), wrong_dek, metadata)

    def test_tampered_ciphertext_raises(self, tmp_path, plaintext_file):
        out_enc = tmp_path / "enc.bin"
        out_dec = tmp_path / "dec.txt"

        dek = crypto_core.generate_data_key()
        metadata = crypto_core.encrypt_file(str(plaintext_file), str(out_enc), dek)

        # Flip a byte in the ciphertext to simulate tampering
        raw = bytearray(out_enc.read_bytes())
        raw[0] ^= 0xFF
        out_enc.write_bytes(bytes(raw))

        with pytest.raises(Exception):
            crypto_core.decrypt_file(str(out_enc), str(out_dec), dek, metadata)

    def test_unsupported_algorithm_raises(self, tmp_path, plaintext_file):
        out_enc = tmp_path / "enc.bin"
        out_dec = tmp_path / "dec.txt"

        dek = crypto_core.generate_data_key()
        metadata = crypto_core.encrypt_file(str(plaintext_file), str(out_enc), dek)
        metadata["alg"] = "UNSUPPORTED"

        with pytest.raises(ValueError, match="unsupported algorithm"):
            crypto_core.decrypt_file(str(out_enc), str(out_dec), dek, metadata)
