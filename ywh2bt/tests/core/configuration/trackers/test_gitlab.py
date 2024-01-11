import unittest

from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.trackers.gitlab import GitLabConfiguration


class TestGitLab(unittest.TestCase):
    def test_registered(self) -> None:
        tracker = TrackerConfiguration(type="gitlab")
        self.assertIsInstance(tracker, GitLabConfiguration)

    def test_constructor(self) -> None:
        gitlab = GitLabConfiguration(
            url="http://example.com",
            token="my-token",
            project="my-project",
            verify=False,
        )
        self.assertEqual("http://example.com", gitlab.url)
        self.assertEqual("my-token", gitlab.token)
        self.assertEqual("my-project", gitlab.project)
        self.assertEqual(False, gitlab.verify)
