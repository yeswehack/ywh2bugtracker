import unittest

from ywh2bt.core.configuration.error import AttributesError
from ywh2bt.core.configuration.headers import Headers
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.configuration.tracker import Trackers
from ywh2bt.core.configuration.trackers.github import GitHubConfiguration
from ywh2bt.core.configuration.trackers.gitlab import GitLabConfiguration
from ywh2bt.core.configuration.yeswehack import (
    Bugtrackers, OAuthSettings, Program, Programs, YesWeHackConfiguration,
    YesWeHackConfigurations
)


class TestRoot(unittest.TestCase):

    def test_validate(self) -> None:
        root = RootConfiguration(
            bugtrackers=Trackers(
                my_gitlab=GitLabConfiguration(
                    token='gl-token',
                    project='my-project',
                ),
                my_github=GitHubConfiguration(
                    token='gh-token',
                    project='project',
                ),
            ),
            yeswehack=YesWeHackConfigurations(
                my_ywh=YesWeHackConfiguration(
                    api_url='http://example.com',
                    login='michel@example.com',
                    password='my-password',
                    oauth_args=OAuthSettings(
                        client_id='client-id',
                        client_secret='client-secret',
                        redirect_uri='http://example.com/oauth/redirect',
                    ),
                    apps_headers=Headers(
                        {
                            'X-YesWeHack-Apps': '123',
                        },
                    ),
                    verify=True,
                    programs=Programs(
                        [
                            Program(
                                slug='1-pgm',
                                bugtrackers_name=Bugtrackers(
                                    [
                                        'my_gitlab',
                                    ],
                                ),
                            ),
                            Program(
                                slug='1-pgm',
                                bugtrackers_name=Bugtrackers(
                                    [
                                        'my_github',
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ),
        )
        root.validate()

    def test_validate_unknown_tracker(self) -> None:
        root = RootConfiguration(
            bugtrackers=Trackers(
                my_gitlab=GitLabConfiguration(
                    token='gl-token',
                    project='my-project',
                ),
            ),
            yeswehack=YesWeHackConfigurations(
                my_ywh=YesWeHackConfiguration(
                    api_url='http://example.com',
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
                                        'my_gitlab',
                                        'my_github',
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ),
        )
        with self.assertRaises(AttributesError):
            root.validate()

    def test_validate_no_trackers(self) -> None:
        root = RootConfiguration(
            bugtrackers=Trackers(),
            yeswehack=YesWeHackConfigurations(
                my_ywh=YesWeHackConfiguration(
                    api_url='http://example.com',
                    login='michel@example.com',
                    password='my-password',
                    oauth_args=OAuthSettings(
                        client_id='client-id',
                        client_secret='client-secret',
                        redirect_uri='http://example.com/oauth/redirect',
                    ),
                    apps_headers=Headers(
                        {
                            'X-YesWeHack-Apps': '123',
                        },
                    ),
                    verify=True,
                    programs=Programs(
                        [
                            Program(
                                slug='1-pgm',
                                bugtrackers_name=Bugtrackers(
                                    [
                                        'my_gitlab',
                                        'my_github',
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ),
        )
        with self.assertRaises(AttributesError):
            root.validate()
