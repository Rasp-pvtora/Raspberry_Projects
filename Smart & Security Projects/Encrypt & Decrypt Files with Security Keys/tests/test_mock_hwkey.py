"""Unit tests for MockHardwareKey adapter."""
import os
import pytest

from src.enc_decrypt.hwkey.mock_hwkey import MockHardwareKey
from src.enc_decrypt.hwkey.base import IHardwareKey


class TestMockHardwareKey:
    def test_implements_interface(self):
        assert issubclass(MockHardwareKey, IHardwareKey)

    def test_identify_returns_string(self):
        token = MockHardwareKey()
        assert isinstance(token.identify(), str)
        assert len(token.identify()) > 0

    def test_custom_identifier(self):
        token = MockHardwareKey(identifier="my-test-token")
        assert token.identify() == "my-test-token"

    def test_wrap_unwrap_roundtrip(self):
        token = MockHardwareKey()
        key = os.urandom(32)
        wrapped = token.wrap_key(key)
        assert wrapped != key
        recovered = token.unwrap_key(wrapped)
        assert recovered == key

    def test_wrap_produces_different_output_from_input(self):
        token = MockHardwareKey()
        key = os.urandom(32)
        wrapped = token.wrap_key(key)
        assert wrapped != key

    def test_unwrap_invalid_blob_raises(self):
        token = MockHardwareKey()
        with pytest.raises(ValueError, match="invalid wrapped key format"):
            token.unwrap_key(b"GARBAGE_DATA")

    def test_two_tokens_same_mock_can_cross_unwrap(self):
        """Mock tokens do not have per-instance secrets — wrapping is symmetric."""
        token_a = MockHardwareKey(identifier="a")
        token_b = MockHardwareKey(identifier="b")
        key = os.urandom(32)
        wrapped = token_a.wrap_key(key)
        # Both mock instances use the same trivial scheme
        recovered = token_b.unwrap_key(wrapped)
        assert recovered == key
