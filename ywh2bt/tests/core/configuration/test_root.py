import unittest

from ywh2bt.core.configuration.error import AttributesError
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.configuration.tracker import Trackers
from ywh2bt.core.configuration.trackers.github import GitHubConfiguration
from ywh2bt.core.configuration.trackers.gitlab import GitLabConfiguration
from ywh2bt.core.configuration.yeswehack import (
    Bugtrackers,
    Program,
    Programs,
    YesWeHackConfiguration,
    YesWeHackConfigurations,
)


class TestRoot(unittest.TestCase):
    def test_validate(self) -> None:
        root = RootConfiguration(
            bugtrackers=Trackers(
                my_gitlab=GitLabConfiguration(
                    token="gl-token",
                    project="my-project",
                ),
                my_github=GitHubConfiguration(
                    token="gh-token",
                    project="project",
                ),
            ),
            yeswehack=YesWeHackConfigurations(
                my_ywh=YesWeHackConfiguration(
                    api_url="http://example.com",
                    pat="e2d00087-a2fa-4fe2-ac1c-7abf1da2a036",
                    verify=True,
                    programs=Programs(
                        [
                            Program(
                                slug="1-pgm",
                                bugtrackers_name=Bugtrackers(
                                    [
                                        "my_gitlab",
                                    ],
                                ),
                            ),
                            Program(
                                slug="1-pgm",
                                bugtrackers_name=Bugtrackers(
                                    [
                                        "my_github",
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
                    token="gl-token",
                    project="my-project",
                ),
            ),
            yeswehack=YesWeHackConfigurations(
                my_ywh=YesWeHackConfiguration(
                    api_url="http://example.com",
                    pat="e2d00087-a2fa-4fe2-ac1c-7abf1da2a036",
                    verify=True,
                    programs=Programs(
                        [
                            Program(
                                slug="1-pgm",
                                bugtrackers_name=Bugtrackers(
                                    [
                                        "my_gitlab",
                                        "my_github",
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
                    api_url="http://example.com",
                    pat="e2d00087-a2fa-4fe2-ac1c-7abf1da2a036",
                    verify=True,
                    programs=Programs(
                        [
                            Program(
                                slug="1-pgm",
                                bugtrackers_name=Bugtrackers(
                                    [
                                        "my_gitlab",
                                        "my_github",
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
