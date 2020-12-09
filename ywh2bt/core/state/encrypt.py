"""Models and functions used for states encryption."""
import base64
import json
from typing import Any, Dict, Tuple

from ywh2bt.core.crypt.encrypt import Encryptor
from ywh2bt.core.crypt.error import CryptError
from ywh2bt.core.crypt.key import Key
from ywh2bt.core.state.error import StateError
from ywh2bt.core.state.state import State


class StateEncryptor:
    """A simple state encryptor."""

    @classmethod
    def encrypt(
        cls,
        state: State,
        key: str,
    ) -> str:
        """
        Encrypt a state with a key.

        Args:
            state: a state
            key: a cryptographic key

        Raises:
            StateError: if the state could not be encrypted

        Returns:
            The encrypted state.
        """
        encryptor = Encryptor(
            key=Key.from_str(
                key=key,
            ),
        )
        try:
            encrypted_data = encryptor.encrypt(
                message_bytes=cls._as_bytes(
                    state=state,
                ),
            )
        except CryptError as e:
            raise StateError(f'Unable to encrypt state {state}') from e
        encrypted_base64 = base64.b64encode(
            encrypted_data,
        )
        encrypted = encrypted_base64.decode('utf-8')
        return f'[YWH2BT:S:{encrypted}]'

    @classmethod
    def _as_bytes(
        cls,
        state: State,
    ) -> bytes:
        json_string = cls._as_json_string(
            state=state,
        )
        return json_string.encode('utf-8')

    @classmethod
    def _as_json_string(
        cls,
        state: State,
    ) -> str:
        try:
            return json.dumps(
                cls._as_meta(
                    state=state,
                ),
            )
        except (TypeError, ValueError) as e:
            raise StateError(f'Unable to serialize state {state}') from e

    @classmethod
    def _as_meta(
        cls,
        state: State,
    ) -> Tuple[str, Dict[str, Any]]:
        return (
            state.__class__.__name__,
            state.as_dict(),
        )
