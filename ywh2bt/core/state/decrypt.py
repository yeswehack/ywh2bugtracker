"""Models and functions used for states decryption."""
import base64
import json
import re
from typing import Optional, Type, TypeVar

from ywh2bt.core.crypt.decrypt import Decryptor
from ywh2bt.core.crypt.error import CryptError
from ywh2bt.core.crypt.key import Key
from ywh2bt.core.state.error import StateError
from ywh2bt.core.state.state import State

StateType = TypeVar('StateType', bound=State, covariant=True)


class StateDecryptor:
    """A simple state decryptor."""

    _encrypted_re = re.compile(
        r'\[YWH2BT:S:(.+)]',
    )

    @classmethod
    def decrypt(
        cls,
        encrypted_state: str,
        key: str,
        state_type: Type[StateType],
    ) -> Optional[StateType]:
        """
        Decrypt a state with a key.

        Args:
            encrypted_state: an encrypted state
            key: a cryptographic key
            state_type: a type of the decrypted state

        Raises:
            StateError: if the state could not be decrypted

        Returns:
            The decrypted state.
        """
        encrypted_base64 = cls._extract_encrypted(
            encrypted_state=encrypted_state,
        )
        if not encrypted_base64:
            return None
        encrypted = base64.b64decode(encrypted_base64)
        decryptor = Decryptor(
            key=Key.from_str(
                key=key,
            ),
        )
        try:
            decrypted_data = decryptor.decrypt(encrypted)
        except CryptError as decrypt_error:
            raise StateError(f'Unable to decrypt state {encrypted_state}') from decrypt_error
        try:
            class_name, data = json.loads(decrypted_data)
        except (json.JSONDecodeError, TypeError) as json_error:
            raise StateError(f'Unable to deserialize state {encrypted_state}') from json_error
        if class_name != state_type.__name__:
            raise StateError(f'Invalid state type {class_name}')
        if not isinstance(data, dict):
            raise StateError('Invalid state data')
        return state_type(**data)  # type: ignore

    @classmethod
    def _extract_encrypted(
        cls,
        encrypted_state: str,
    ) -> Optional[str]:
        match = cls._encrypted_re.search(encrypted_state)
        if match:
            return match.group(1)
        return None
