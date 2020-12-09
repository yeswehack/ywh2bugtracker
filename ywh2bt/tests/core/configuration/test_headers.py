import unittest

from ywh2bt.core.configuration.headers import Headers


class TestHeaders(unittest.TestCase):

    def test_export(self) -> None:
        headers = Headers(
            foo='bar',
        )
        headers['baz'] = 'qux'
        exported = headers.export()
        self.assertEqual(
            dict(
                foo='bar',
                baz='qux',
            ),
            exported,
        )
