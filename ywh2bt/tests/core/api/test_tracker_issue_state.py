from unittest import TestCase

from ywh2bt.core.api.tracker import TrackerIssueState


class TestYesWeHackApiClient(TestCase):
    def test_state_no_args(self) -> None:
        state = TrackerIssueState()
        self.assertFalse(state.changed)
        self.assertFalse(state.closed)
        self.assertIsNone(state.bugtracker_name)
        self.assertIsNone(state.downloaded_comments)
        state.closed = True
        state.bugtracker_name = "my-tracker"
        state.add_downloaded_comment(comment_id="123")
        self.assertTrue(state.changed)
        self.assertTrue(state.closed)
        self.assertEqual("my-tracker", state.bugtracker_name)
        self.assertEqual(["123"], state.downloaded_comments)

    def test_state_args(self) -> None:
        state = TrackerIssueState(
            closed=True,
            bugtracker_name="my-tracker",
            downloaded_comments=["123"],
        )
        self.assertFalse(state.changed)
        self.assertTrue(state.closed)
        self.assertEqual("my-tracker", state.bugtracker_name)
        self.assertEqual(["123"], state.downloaded_comments)

    def test_state_equals(self) -> None:
        self.assertEqual(
            TrackerIssueState(
                closed=True,
                bugtracker_name="my-tracker",
                downloaded_comments=["123"],
            ),
            TrackerIssueState(
                closed=True,
                bugtracker_name="my-tracker",
                downloaded_comments=["123"],
            ),
        )

    def test_state_not_equals(self) -> None:
        self.assertNotEqual(
            TrackerIssueState(
                closed=True,
                bugtracker_name="your-tracker",
                downloaded_comments=["456"],
            ),
            TrackerIssueState(
                closed=True,
                bugtracker_name="my-tracker",
                downloaded_comments=["123"],
            ),
        )
