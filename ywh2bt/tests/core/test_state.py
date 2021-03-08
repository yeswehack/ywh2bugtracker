import unittest
from dataclasses import (
    asdict,
    dataclass,
)
from typing import (
    Any,
    Dict,
)

from ywh2bt.core.state.decrypt import StateDecryptor
from ywh2bt.core.state.encrypt import StateEncryptor
from ywh2bt.core.state.state import State


class TestState(unittest.TestCase):

    def test_encrypt(self) -> None:
        @dataclass
        class MyState(State):
            foo: str
            bar: int
            baz: Dict[str, str]
            qux: bool

            def as_dict(self) -> Dict[str, Any]:
                return asdict(self)

        state = MyState(
            foo='state-foo',
            bar=1_011,
            baz={
                'key1': 'val1',
                'key2': 'val2',
            },
            qux=False,
        )
        key = '42069'
        encrypted = StateEncryptor.encrypt(
            state=state,
            key=key,
        )
        decrypted_state = StateDecryptor.decrypt(
            encrypted_state=encrypted,
            key=key,
            state_type=MyState,
        )
        self.assertEqual(state, decrypted_state)

    def test_decrypt_in_message(self) -> None:
        @dataclass
        class MyState(State):
            foo: str
            bar: int
            baz: Dict[str, str]
            qux: bool

            def as_dict(self) -> Dict[str, Any]:
                return asdict(self)

        state = MyState(
            foo='state-foo',
            bar=1_011,
            baz={
                'key1': 'val1',
                'key2': 'val2',
            },
            qux=False,
        )
        key = '42069'
        encrypted = StateEncryptor.encrypt(
            state=state,
            key=key,
        )
        decrypted_state = StateDecryptor.decrypt(
            encrypted_state=f'The state is encrypted and put somewhere in the message. {encrypted}. Here it was.',
            key=key,
            state_type=MyState,
        )
        self.assertEqual(state, decrypted_state)
