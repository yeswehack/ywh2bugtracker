import unittest

from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.trackers.jira import JiraConfiguration


class TestJira(unittest.TestCase):
    def test_registered(self) -> None:
        tracker = TrackerConfiguration(type="jira")
        self.assertIsInstance(tracker, JiraConfiguration)

    def test_constructor(self) -> None:
        jira = JiraConfiguration(
            url="http://example.com",
            login="my-login",
            password="my-password",
            project="my-project",
            verify=False,
            issuetype="Task",
        )
        self.assertEqual("http://example.com", jira.url)
        self.assertEqual("my-login", jira.login)
        self.assertEqual("my-password", jira.password)
        self.assertEqual("my-project", jira.project)
        self.assertEqual(False, jira.verify)
        self.assertEqual("Task", jira.issuetype)
