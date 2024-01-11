import unittest
from typing import cast

from ywh2bt.core.configuration.yeswehack import (
    Bugtrackers,
    Program,
    Programs,
    YesWeHackConfiguration,
)


class TestYesWeHack(unittest.TestCase):
    def test_constructor(self) -> None:
        ywh = YesWeHackConfiguration(
            api_url="http://example.com",
            pat="60d8fac0-c0ee-496a-a153-298164615021",
            verify=True,
            programs=Programs(
                [
                    Program(
                        slug="1-pgm",
                        bugtrackers_name=Bugtrackers(
                            [
                                "bt1",
                                "bt2",
                            ],
                        ),
                    ),
                ],
            ),
        )

        self.assertEqual("http://example.com", ywh.api_url)
        self.assertEqual("60d8fac0-c0ee-496a-a153-298164615021", ywh.pat)
        self.assertEqual(first=True, second=ywh.verify)
        self.assertEqual("1-pgm", cast(Programs, ywh.programs)[0].slug)
        self.assertEqual(
            [
                "bt1",
                "bt2",
            ],
            cast(Programs, ywh.programs)[0].bugtrackers_name,
        )
