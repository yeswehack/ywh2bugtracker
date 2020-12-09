"""Models and functions used for encryption."""
from ywh2bt.core.crypt.error import CryptError
from ywh2bt.core.crypt.key import Key


class Encryptor:
    """A simple encryptor."""

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

    def encrypt(
        self,
        message_bytes: bytes,
    ) -> bytes:
        """
        Encrypt a message.

        Args:
            message_bytes: a message

        Raises:
            CryptError: if an error occurred

        Returns:
            The encrypted message.
        """
        if not isinstance(message_bytes, bytes):
            raise CryptError(f'Message should be {bytes}. {type(message_bytes)} given.')
        key_generator = self._key.generator()
        message_size = len(message_bytes)
        return bytes([
            message_bytes[i] ^ next(key_generator)
            for i in range(message_size)
        ])
