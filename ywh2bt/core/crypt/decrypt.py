"""Models and functions used for decryption."""
from ywh2bt.core.crypt.error import CryptError
from ywh2bt.core.crypt.key import Key


class Decryptor:
    """A simple decryptor."""

    _key: Key

    def __init__(
        self,
        key: Key,
    ):
        """
        Initialize self.

        Args:
            key: a cryptographic key

        Raises:
            CryptError: if an error occurred
        """
        if not isinstance(key, Key):
            raise CryptError(f'Key should be {Key}. {type(key)} given.')
        self._key = key

    def decrypt(
        self,
        encrypted_bytes: bytes,
    ) -> bytes:
        """
        Decrypt a message.

        Args:
            encrypted_bytes: an encrypted message

        Raises:
            CryptError: if an error occurred

        Returns:
            The decrypted message.
        """
        if not isinstance(encrypted_bytes, bytes):
            raise CryptError(f'Encrypted should be {bytes}. {type(encrypted_bytes)} given.')
        key_generator = self._key.generator()
        encrypted_size = len(encrypted_bytes)
        return bytes([
            next(key_generator) ^ encrypted_bytes[i]
            for i in range(encrypted_size)
        ])
