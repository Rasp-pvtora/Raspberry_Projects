"""Abstract base class for all hardware key adapters.

Every adapter (mock, PKCS#11, YubiKey, …) must implement this interface so
the rest of the codebase stays adapter-agnostic.
"""
from abc import ABC, abstractmethod


class IHardwareKey(ABC):
    """Interface for a hardware (or software-mock) key adapter."""

    @abstractmethod
    def identify(self) -> str:
        """Return a human-readable identifier for this adapter/token."""

    @abstractmethod
    def wrap_key(self, key: bytes) -> bytes:
        """Wrap (encrypt) a DEK using the adapter's KEK.

        Args:
            key: Raw bytes of the DEK to protect.

        Returns:
            Opaque wrapped-key blob (bytes).
        """

    @abstractmethod
    def unwrap_key(self, wrapped: bytes) -> bytes:
        """Unwrap (decrypt) a previously wrapped DEK.

        Args:
            wrapped: The opaque blob returned by `wrap_key`.

        Returns:
            Raw bytes of the original DEK.
        """
