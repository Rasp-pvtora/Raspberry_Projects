"""CLI entrypoint for enc_decrypt.

Commands
--------
  encrypt     Encrypt a file and persist the wrapped DEK in the keystore.
  decrypt     Decrypt a file by retrieving its DEK from the keystore.
  provision   Initialise a named key slot in the keystore (mock or real adapter).
  list-keys   List all key-ids registered in the keystore.
  rotate      Re-wrap an existing DEK with a fresh key and update the keystore.

Usage examples (mock adapter, laptop development)
-------------------------------------------------
  python -m src.enc_decrypt.cli encrypt \\
      --input tests/original_document.txt \\
      --output tests/original_document.txt.enc \\
      --key-id my-key --use-mock

  python -m src.enc_decrypt.cli decrypt \\
      --input tests/original_document.txt.enc \\
      --output tests/decrypted_document.txt \\
      --key-id my-key --use-mock

  python -m src.enc_decrypt.cli list-keys

  python -m src.enc_decrypt.cli rotate --key-id my-key --use-mock
"""
import os
import base64
from pathlib import Path

import click

from . import crypto_core
from . import store as keystore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _b64(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")


def _unb64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def _get_adapter(use_mock: bool):
    """Return an adapter instance.  Extend here for real hardware adapters."""
    if use_mock:
        from .hwkey.mock_hwkey import MockHardwareKey
        return MockHardwareKey()
    raise click.ClickException(
        "No hardware adapter configured. "
        "Pass --use-mock for development or configure a real adapter."
    )


def _store_path_option(ctx, param, value):  # noqa: ARG001
    if value:
        return Path(value)
    return None


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """enc_decrypt — file encryption with hardware security key support."""


# ---------------------------------------------------------------------------
# encrypt
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--input",    "input_path",  required=True,  help="Path to the plaintext file to encrypt.")
@click.option("--output",   "output_path", required=True,  help="Destination path for the ciphertext file.")
@click.option("--key-id",   "key_id",      required=True,  help="Logical key identifier (stored in keystore).")
@click.option("--use-mock", is_flag=True,                  help="Use the software mock adapter (development only).")
@click.option("--store",    "store_path",  default=None,   callback=_store_path_option, is_eager=False,
              help="Path to keystore file (default: ~/.enc_decrypt/keystore.json).")
def encrypt(input_path, output_path, key_id, use_mock, store_path):
    """Encrypt INPUT and store the wrapped DEK under KEY_ID in the keystore."""
    if not os.path.exists(input_path):
        raise click.ClickException(f"Input file not found: {input_path}")

    adapter = _get_adapter(use_mock)

    dek = crypto_core.generate_data_key()
    try:
        metadata = crypto_core.encrypt_file(input_path, output_path, dek)
    except Exception as exc:
        raise click.ClickException(f"Encryption failed: {exc}") from exc

    wrapped = adapter.wrap_key(dek)

    try:
        keystore.store_key(
            key_id=key_id,
            wrapped_dek=wrapped,
            metadata=metadata,
            adapter_id=adapter.identify(),
            store_path=store_path,
        )
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"[OK] Encrypted  : {input_path}")
    click.echo(f"     Ciphertext : {output_path}")
    click.echo(f"     Key-ID     : {key_id}")
    click.echo(f"     Adapter    : {adapter.identify()}")


# ---------------------------------------------------------------------------
# decrypt
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--input",    "input_path",  required=True,  help="Path to the ciphertext file.")
@click.option("--output",   "output_path", required=True,  help="Destination path for the decrypted file.")
@click.option("--key-id",   "key_id",      required=True,  help="Logical key identifier used during encryption.")
@click.option("--use-mock", is_flag=True,                  help="Use the software mock adapter (development only).")
@click.option("--store",    "store_path",  default=None,   callback=_store_path_option, is_eager=False,
              help="Path to keystore file.")
def decrypt(input_path, output_path, key_id, use_mock, store_path):
    """Decrypt INPUT using the DEK stored under KEY_ID in the keystore."""
    if not os.path.exists(input_path):
        raise click.ClickException(f"Input file not found: {input_path}")

    adapter = _get_adapter(use_mock)

    try:
        entry = keystore.load_key(key_id, store_path)
        wrapped = keystore.get_wrapped_dek(key_id, store_path)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        dek = adapter.unwrap_key(wrapped)
    except Exception as exc:
        raise click.ClickException(f"Key unwrap failed: {exc}") from exc

    try:
        crypto_core.decrypt_file(input_path, output_path, dek, entry)
    except Exception as exc:
        raise click.ClickException(f"Decryption failed: {exc}") from exc

    click.echo(f"[OK] Decrypted  : {input_path}")
    click.echo(f"     Plaintext  : {output_path}")
    click.echo(f"     Key-ID     : {key_id}")


# ---------------------------------------------------------------------------
# provision
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--key-id",   "key_id",     required=True, help="Name for this key slot.")
@click.option("--use-mock", is_flag=True,                help="Use the software mock adapter.")
@click.option("--store",    "store_path", default=None,  callback=_store_path_option, is_eager=False,
              help="Path to keystore file.")
def provision(key_id, use_mock, store_path):
    """Create a new key slot in the keystore for KEY_ID."""
    adapter = _get_adapter(use_mock)

    placeholder_dek = crypto_core.generate_data_key()
    wrapped = adapter.wrap_key(placeholder_dek)
    metadata = {"alg": "AES-GCM", "nonce": "", "provisioned": True}

    try:
        keystore.store_key(
            key_id=key_id,
            wrapped_dek=wrapped,
            metadata=metadata,
            adapter_id=adapter.identify(),
            store_path=store_path,
        )
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"[OK] Provisioned key slot '{key_id}' with adapter '{adapter.identify()}'.")


# ---------------------------------------------------------------------------
# list-keys
# ---------------------------------------------------------------------------

@cli.command("list-keys")
@click.option("--store", "store_path", default=None, callback=_store_path_option, is_eager=False,
              help="Path to keystore file.")
def list_keys(store_path):
    """List all key-ids registered in the keystore."""
    keys = keystore.list_keys(store_path)
    if not keys:
        click.echo("Keystore is empty.")
        return
    click.echo(f"{'KEY-ID':<30}  {'CREATED':<30}  ADAPTER")
    click.echo("-" * 80)
    for kid in keys:
        try:
            entry = keystore.load_key(kid, store_path)
            created = entry.get("created", "unknown")
            adapter_id = entry.get("adapter", "unknown")
            click.echo(f"{kid:<30}  {created:<30}  {adapter_id}")
        except KeyError:
            click.echo(f"{kid:<30}  (error reading entry)")


# ---------------------------------------------------------------------------
# rotate
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--key-id",   "key_id",     required=True, help="Key slot to rotate.")
@click.option("--use-mock", is_flag=True,                help="Use the software mock adapter.")
@click.option("--store",    "store_path", default=None,  callback=_store_path_option, is_eager=False,
              help="Path to keystore file.")
def rotate(key_id, use_mock, store_path):
    """Re-wrap the DEK for KEY_ID with a freshly generated key.

    WARNING: files encrypted with the old DEK cannot be decrypted after
    rotation unless they are re-encrypted first.
    """
    adapter = _get_adapter(use_mock)

    try:
        wrapped_old = keystore.get_wrapped_dek(key_id, store_path)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        adapter.unwrap_key(wrapped_old)
    except Exception as exc:
        raise click.ClickException(f"Cannot unwrap current key: {exc}") from exc

    new_dek = crypto_core.generate_data_key()
    new_wrapped = adapter.wrap_key(new_dek)
    keystore.rotate_key(
        key_id=key_id,
        new_wrapped_dek=new_wrapped,
        metadata={"alg": "AES-GCM", "nonce": ""},
        adapter_id=adapter.identify(),
        store_path=store_path,
    )

    click.echo(f"[OK] Rotated key slot '{key_id}'.")
    click.echo("     WARNING: files encrypted with the old DEK must be re-encrypted.")


if __name__ == "__main__":
    cli()
