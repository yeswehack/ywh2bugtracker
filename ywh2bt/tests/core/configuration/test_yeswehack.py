import unittest
from typing import cast

from ywh2bt.core.configuration.headers import Headers
from ywh2bt.core.configuration.yeswehack import Bugtrackers, OAuthSettings, Program, Programs, YesWeHackConfiguration


class TestYesWeHack(unittest.TestCase):

    def test_constructor(self) -> None:
        ywh = YesWeHackConfiguration(
            api_url='http://example.com',
            apps_headers=Headers(
                foo='bar',
            ),
            login='michel@example.com',
            password='my-password',
            oauth_args=OAuthSettings(
                client_id='client-id',
                client_secret='client-secret',
                redirect_uri='http://example.com/oauth/redirect',
            ),
            verify=True,
            programs=Programs(
                [
                    Program(
                        slug='1-pgm',
                        bugtrackers_name=Bugtrackers(
                            [
                                'bt1',
                                'bt2',
                            ],
                        ),
                    ),
                ],
            ),
        )

        self.assertEqual('http://example.com', ywh.api_url)
        self.assertEqual(
            dict(
                foo='bar',
            ),
            ywh.apps_headers,
        )
        self.assertEqual('michel@example.com', ywh.login)
        self.assertEqual('my-password', ywh.password)
        self.assertEqual('client-id', cast(OAuthSettings, ywh.oauth_args).client_id)
        self.assertEqual('client-secret', cast(OAuthSettings, ywh.oauth_args).client_secret)
        self.assertEqual('http://example.com/oauth/redirect', cast(OAuthSettings, ywh.oauth_args).redirect_uri)
        self.assertEqual(first=True, second=ywh.verify)
        self.assertEqual('1-pgm', cast(Programs, ywh.programs)[0].slug)
        self.assertEqual(
            [
                'bt1',
                'bt2',
            ],
            cast(Programs, ywh.programs)[0].bugtrackers_name,
        )
