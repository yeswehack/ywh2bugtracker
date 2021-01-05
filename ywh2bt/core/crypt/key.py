"""Models and functions used for cryptographic keys."""
from __future__ import annotations

from typing import Generator

from ywh2bt.core.crypt.error import CryptError


class Key:
    """A simple crypt key."""

    _key_bytes: bytes

    def __init__(
        self,
        key_bytes: bytes,
    ):
        """
        Initialize self.

        Args:
            key_bytes: key in bytes

        Raises:
            CryptError: if an error occurred
        """
        if not isinstance(key_bytes, bytes):
            raise CryptError(f'Key should be {bytes}. {type(key_bytes)} given.')
        self._key_bytes = key_bytes

    def generator(
        self,
    ) -> Generator[int, None, None]:
        """
        Get a generator that yields each byte of the key.

        Yields:
            each byte of the key
        """
        idx = 0
        key_size = len(self._key_bytes)
        while True:  # noqa: WPS457
            yield self._key_bytes[idx % key_size]
            idx += 1

    def __str__(
        self,
    ) -> str:
        """
        Get a string representation of the key.

        Returns:
            The string representation of the key.
        """
        return f'Key(size={len(self._key_bytes)})'

    @classmethod
    def from_str(
        cls,
        key: str,
    ) -> Key:
        """
        Build a key from a string.

        Args:
            key: a key in a string format.

        Returns:
            The key.
        """
        return Key(str.encode(key))
