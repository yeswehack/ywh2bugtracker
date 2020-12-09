import unittest

from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.trackers.github import GitHubConfiguration


class TestGitHub(unittest.TestCase):

    def test_registered(self) -> None:
        tracker = TrackerConfiguration(type='github')
        self.assertIsInstance(tracker, GitHubConfiguration)

    def test_constructor(self) -> None:
        github = GitHubConfiguration(
            url='http://example.com',
            token='my-token',
            project='my-project',
            verify=False,
            github_cdn_on=True,
        )
        self.assertEqual('http://example.com', github.url)
        self.assertEqual('my-token', github.token)
        self.assertEqual('my-project', github.project)
        self.assertEqual(False, github.verify)
        self.assertEqual(True, github.github_cdn_on)
