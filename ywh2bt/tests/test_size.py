import unittest
from typing import Union

from ywh2bt.size import sizeof_fmt_si, sizeof_fmt_iec


class TestCli(unittest.TestCase):
    def _test_sizeof_fmt_si(self, expected: str, num: Union[int, float], precision: int) -> None:
        with self.subTest(f'sizeof_fmt_si({num}, precision={precision})'):
            self.assertEqual(expected, sizeof_fmt_si(num, precision=precision))

    def _test_sizeof_fmt_iec(self, expected: str, num: Union[int, float], precision: int) -> None:
        with self.subTest(f'sizeof_fmt_iec({num}, precision={precision})'):
            self.assertEqual(expected, sizeof_fmt_iec(num, precision=precision))

    def test_sizeof_fmt(self) -> None:
        values = {
            999: {
                0: ['999B', '999B'],
                1: ['999.0B', '999.0B'],
                2: ['999.00B', '999.00B'],
            },
            1000: {
                0: ['1kB', '1000B'],
                1: ['1.0kB', '1000.0B'],
                2: ['1.00kB', '1000.00B'],
            },
            1024: {
                0: ['1kB', '1KiB'],
                1: ['1.0kB', '1.0KiB'],
                2: ['1.02kB', '1.00KiB'],
            },
            2000000: {
                0: ['2MB', '2MiB'],
                1: ['2.0MB', '1.9MiB'],
                2: ['2.00MB', '1.91MiB'],
            },
            123456897101112: {
                0: ['123TB', '112TiB'],
                1: ['123.5TB', '112.3TiB'],
                2: ['123.46TB', '112.28TiB'],
            },
            9999999999999999999999999: {
                0: ['10YB', '8YiB'],
                1: ['10.0YB', '8.3YiB'],
                2: ['10.00YB', '8.27YiB'],
            },
        }
        for num, precisions in values.items():
            for precision, expected_values in precisions.items():
                self._test_sizeof_fmt_si(expected_values[0], num=num, precision=precision)
                self._test_sizeof_fmt_iec(expected_values[1], num=num, precision=precision)
