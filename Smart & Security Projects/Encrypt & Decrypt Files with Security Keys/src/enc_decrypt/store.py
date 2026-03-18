"""Keystore: persists wrapped DEKs and metadata on disk.

File format: a JSON object where each entry is keyed by a user-chosen
key-id.  The file is written with restrictive permissions (owner read-only)
on POSIX systems; on Windows the same access restriction is applied where
the API allows.

Schema per entry:
  {
    "key_id": "<str>",
    "wrapped_dek": "<base64>",
    "alg": "AES-GCM",
    "nonce": "<base64>",
    "created": "<ISO-8601>",
    "adapter": "<adapter identifier>"
  }
"""

import json
import os
import stat
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


# Default keystore lives inside the project tree so it stays alongside the
# encrypted files. The keystore/ folder is in .gitignore — never committed.
_DEFAULT_STORE = Path(__file__).resolve().parents[2] / "keystore" / "keystore.json"


def _b64(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")


def _unb64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def _secure_write(path: Path, data: str) -> None:
    """Write `data` to `path` and restrict permissions to owner-only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")
    try:
        # POSIX: chmod 600
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except (AttributeError, NotImplementedError):
        # On Windows Path.chmod is a no-op; use icacls via subprocess only if
        # available — skip silently otherwise so the app still works.
        try:
            import subprocess
            subprocess.run(  # noqa: S603
                ["icacls", str(path), "/inheritance:r",
                 "/grant:r", f"{os.getlogin()}:(R,W)"],
                capture_output=True,
                check=False,
            )
        except Exception:
            pass


def _load(store_path: Path) -> Dict:
    if not store_path.exists():
        return {}
    try:
        raw = store_path.read_text(encoding="utf-8")
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(store_path: Path, data: Dict) -> None:
    _secure_write(store_path, json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def store_key(
    key_id: str,
    wrapped_dek: bytes,
    metadata: Dict,
    adapter_id: str = "mock-token",
    store_path: Optional[Path] = None,
) -> None:
    """Persist a wrapped DEK and its metadata under `key_id`.

    Raises:
        KeyError: if `key_id` already exists in the store (use update_key to
                  overwrite deliberately).
    """
    path = store_path or _DEFAULT_STORE
    store = _load(path)

    if key_id in store:
        raise KeyError(f"Key '{key_id}' already exists; use rotate_key to replace it.")

    entry = {
        "key_id": key_id,
        "wrapped_dek": _b64(wrapped_dek),
        "alg": metadata.get("alg", "AES-GCM"),
        "nonce": metadata.get("nonce", ""),
        "created": datetime.now(tz=timezone.utc).isoformat(),
        "adapter": adapter_id,
    }
    store[key_id] = entry
    _save(path, store)


def load_key(key_id: str, store_path: Optional[Path] = None) -> Dict:
    """Return the store entry for `key_id`.

    Raises:
        KeyError: if the key is not found.
    """
    path = store_path or _DEFAULT_STORE
    store = _load(path)
    if key_id not in store:
        raise KeyError(f"Key '{key_id}' not found in keystore.")
    return dict(store[key_id])


def get_wrapped_dek(key_id: str, store_path: Optional[Path] = None) -> bytes:
    """Return the raw wrapped-DEK bytes for `key_id`."""
    entry = load_key(key_id, store_path)
    return _unb64(entry["wrapped_dek"])


def list_keys(store_path: Optional[Path] = None) -> list:
    """Return a list of all key-id strings in the store."""
    path = store_path or _DEFAULT_STORE
    return list(_load(path).keys())


def rotate_key(
    key_id: str,
    new_wrapped_dek: bytes,
    metadata: Dict,
    adapter_id: str = "mock-token",
    store_path: Optional[Path] = None,
) -> None:
    """Replace the wrapped DEK for an existing key entry."""
    path = store_path or _DEFAULT_STORE
    store = _load(path)
    if key_id not in store:
        raise KeyError(f"Key '{key_id}' not found; cannot rotate.")

    entry = store[key_id]
    entry["wrapped_dek"] = _b64(new_wrapped_dek)
    entry["alg"] = metadata.get("alg", entry.get("alg", "AES-GCM"))
    entry["nonce"] = metadata.get("nonce", entry.get("nonce", ""))
    entry["adapter"] = adapter_id
    entry["rotated"] = datetime.now(tz=timezone.utc).isoformat()
    store[key_id] = entry
    _save(path, store)


def delete_key(key_id: str, store_path: Optional[Path] = None) -> None:
    """Remove a key entry from the keystore."""
    path = store_path or _DEFAULT_STORE
    store = _load(path)
    if key_id not in store:
        raise KeyError(f"Key '{key_id}' not found.")
    del store[key_id]
    _save(path, store)
