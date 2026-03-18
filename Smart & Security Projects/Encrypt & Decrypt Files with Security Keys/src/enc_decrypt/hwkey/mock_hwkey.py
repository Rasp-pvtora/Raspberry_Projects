"""Mock hardware key adapter for local testing.

This mock simulates wrapping/unwrapping of DEKs. It is NOT secure and is
only intended for development and unit tests on the laptop.
"""
import base64

from .base import IHardwareKey


class MockHardwareKey(IHardwareKey):
    """Simple mock that 'wraps' a key by base64-encoding it with a prefix.

    DO NOT USE THIS IN PRODUCTION.
    """

    def __init__(self, identifier: str = "mock-token"):
        self._identifier = identifier

    def identify(self) -> str:
        return self._identifier

    def wrap_key(self, key: bytes) -> bytes:
        return b"MOCKWRAP:" + base64.b64encode(key)

    def unwrap_key(self, wrapped: bytes) -> bytes:
        if not wrapped.startswith(b"MOCKWRAP:"):
            raise ValueError("invalid wrapped key format")
        return base64.b64decode(wrapped.split(b":", 1)[1])

