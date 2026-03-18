"""Core cryptographic primitives for the project.

This module implements a minimal software-only AEAD file encrypt/decrypt
implementation using AES-GCM. It is intended for laptop testing; a hardware
adapter is used to wrap/unwrap DEKs in other layers.
"""

import os
import base64
import json
from typing import Dict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_data_key() -> bytes:
	"""Generate a 256-bit data encryption key (DEK)."""
	return os.urandom(32)


def _b64(x: bytes) -> str:
	return base64.b64encode(x).decode("ascii")


def _unb64(s: str) -> bytes:
	return base64.b64decode(s.encode("ascii"))


def encrypt_file(input_path: str, output_path: str, dek: bytes) -> Dict:
	"""Encrypt a file using AES-GCM and return metadata.

	The ciphertext is written to `output_path`. Returned metadata contains
	base64-encoded nonce, algorithm and version. The DEK itself is not stored
	here; callers should wrap it with a hardware adapter or otherwise protect it.
	"""
	aesgcm = AESGCM(dek)
	nonce = os.urandom(12)

	with open(input_path, "rb") as f:
		plaintext = f.read()

	ciphertext = aesgcm.encrypt(nonce, plaintext, None)

	with open(output_path, "wb") as f:
		f.write(ciphertext)

	metadata = {
		"version": 1,
		"alg": "AES-GCM",
		"nonce": _b64(nonce),
		"length": len(ciphertext),
	}
	return metadata


def decrypt_file(input_path: str, output_path: str, dek: bytes, metadata: Dict) -> None:
	"""Decrypt a file previously encrypted by `encrypt_file`.

	`metadata` must contain the `nonce` (base64) and algorithm info.
	"""
	if metadata.get("alg") != "AES-GCM":
		raise ValueError("unsupported algorithm")

	nonce = _unb64(metadata["nonce"])
	aesgcm = AESGCM(dek)

	with open(input_path, "rb") as f:
		ciphertext = f.read()

	plaintext = aesgcm.decrypt(nonce, ciphertext, None)

	with open(output_path, "wb") as f:
		f.write(plaintext)

