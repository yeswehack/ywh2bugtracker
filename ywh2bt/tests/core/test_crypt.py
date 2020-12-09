import unittest
from secrets import token_bytes

from ywh2bt.core.crypt.decrypt import Decryptor
from ywh2bt.core.crypt.encrypt import Encryptor
from ywh2bt.core.crypt.key import Key


class TestCrypt(unittest.TestCase):

    def test_en_de(self) -> None:
        original_message = '''
        Did you ever hear the tragedy of Darth Plagueis The Wise?
        I thought not.
        It’s not a story the Jedi would tell you.
        It’s a Sith legend.
        Darth Plagueis was a Dark Lord of the Sith, so powerful
        and so wise he could use the Force to influence the midichlorians to create life…
        He had such a knowledge of the dark side that he could even keep the ones he cared about from dying.
        The dark side of the Force is a pathway to many abilities some consider to be unnatural.
        He became so powerful…
        The only thing he was afraid of was losing his power, which eventually, of course, he did.
        Unfortunately, he taught his apprentice everything he knew, then his apprentice killed him in his sleep.
        Ironic.
        He could save others from death, but not himself.
        '''
        key = Key(key_bytes=token_bytes(128))
        encoding = 'utf-8'
        encrypted_bytes = Encryptor(key=key).encrypt(str.encode(original_message, encoding))
        decrypted_bytes = Decryptor(key=key).decrypt(encrypted_bytes)
        decrypted_message = decrypted_bytes.decode(encoding)
        self.assertEqual(decrypted_message, original_message)
