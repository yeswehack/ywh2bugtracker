import datetime
import inspect
from functools import wraps
from unittest import TestCase
from unittest.mock import (
    ANY,
    MagicMock,
    patch,
)

from jira.resources import (
    Attachment,
    Comment,
    Issue,
)
from jira.resources import PropertyHolder as NativePropertyHolder
from yeswehack.api import Report as YesWeHackRawApiReport

from ywh2bt.core.api.models.report import (
    Author,
    BugType,
    Cvss,
    Log,
    Report,
    ReportProgram,
)
from ywh2bt.core.api.tracker import (
    SendLogsResult,
    TrackerIssue,
)
from ywh2bt.core.api.trackers.jira.tracker import JiraTrackerClient
from ywh2bt.core.configuration.trackers.jira import JiraConfiguration


class IssueSpec(Issue):
    key = None
    fields = None


class CommentSpec(Comment):
    id = None
    created = None
    author = None
    body = None


class AttachmentSpec(Attachment):
    filename = None
    mimeType = None


class PropertyHolder(NativePropertyHolder):
    def __init__(self) -> None:
        signature = inspect.signature(super().__init__)
        if "raw" in signature.parameters:
            super().__init__(raw=None)
        else:
            super().__init__()


def patch_jira(func):
    @patch("jira.resources.Issue", autospec=IssueSpec, spec_set=True)
    @patch("ywh2bt.core.api.trackers.jira.tracker.JIRA", autospec=True, spec_set=True)
    @wraps(func)
    def patched(
        *args,
        **kwargs,
    ):
        return func(
            *args,
            **kwargs,
        )

    return patched


class TestJiraTrackerClient(TestCase):
    @patch_jira
    def test_get_tracker_issue(
        self,
        jira_mock_class: MagicMock,
        issue_mock_class: MagicMock,
    ) -> None:
        issue_mock = issue_mock_class(options=ANY, session=ANY)
        issue_mock.key = "123"
        issue_mock.permalink.return_value = "http://tracker/issue/123"
        issue_mock.fields = PropertyHolder()
        issue_mock.fields.status = None

        jira_mock_class.return_value.issue.return_value = issue_mock

        client = JiraTrackerClient(
            configuration=JiraConfiguration(
                project="my-project",
            ),
        )
        issue = client.get_tracker_issue(issue_id="123")
        self.assertIsInstance(issue, TrackerIssue)
        self.assertEqual("123", issue.issue_id)
        self.assertEqual("http://tracker/issue/123", issue.issue_url)
        self.assertEqual("my-project", issue.project)
        self.assertFalse(issue.closed)

    @patch_jira
    def test_send_report(
        self,
        jira_mock_class: MagicMock,
        issue_mock_class: MagicMock,
    ) -> None:
        issue_mock = issue_mock_class(options=ANY, session=ANY)
        issue_mock.key = "456"
        issue_mock.permalink.return_value = "http://tracker/issue/456"

        jira_mock_class.return_value.create_issue.return_value = issue_mock

        client = JiraTrackerClient(
            configuration=JiraConfiguration(
                project="my-project",
            ),
        )
        raw_report = YesWeHackRawApiReport(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
        )
        issue = client.send_report(
            report=report,
        )
        self.assertIsInstance(issue, TrackerIssue)
        self.assertEqual("456", issue.issue_id)
        self.assertEqual("http://tracker/issue/456", issue.issue_url)
        self.assertEqual("my-project", issue.project)
        self.assertFalse(issue.closed)

    @patch("jira.resources.Comment", autospec=CommentSpec, spec_set=True)
    @patch_jira
    def test_send_logs(
        self,
        jira_mock_class: MagicMock,
        issue_mock_class: MagicMock,
        comment_mock_class: MagicMock,
    ) -> None:
        issue_comment_mock = comment_mock_class(options=ANY, session=ANY)
        issue_comment_mock.id = "147"
        issue_comment_mock.created = "2020-11-02T15:17:23.420Z"
        issue_comment_mock.body = "This is a comment"
        issue_comment_mock.author = PropertyHolder()
        issue_comment_mock.author.displayName = "user1"

        issue_mock = issue_mock_class(options=ANY, session=ANY)
        issue_mock.key = "456"
        issue_mock.permalink.return_value = "http://tracker/issue/456"
        issue_mock.fields = PropertyHolder()
        issue_mock.fields.status = None

        jira_mock_class.return_value.issue.return_value = issue_mock
        jira_mock_class.return_value.add_comment.return_value = issue_comment_mock

        client = JiraTrackerClient(
            configuration=JiraConfiguration(
                project="my-project",
            ),
        )
        tracker_issue = TrackerIssue(
            tracker_url="http://tracker/issue/456",
            project="my-project",
            issue_id="456",
            issue_url="http://tracker/issue/456",
            closed=False,
        )
        logs = [
            Log(
                created_at="2021-01-28 16:00:54.140843",
                log_id=987,
                log_type="comment",
                private=False,
                author=Author(
                    username="Anonymous",
                ),
                message_html="This is a comment",
                attachments=[],
            ),
        ]
        send_logs_result = client.send_logs(
            tracker_issue=tracker_issue,
            logs=logs,
        )
        self.assertIsInstance(send_logs_result, SendLogsResult)
        self.assertEqual(tracker_issue, send_logs_result.tracker_issue)
        self.assertEqual(1, len(send_logs_result.added_comments))
        tracker_issue_comment = send_logs_result.added_comments[0]
        self.assertEqual("147", tracker_issue_comment.comment_id)
        self.assertEqual("user1", tracker_issue_comment.author)
        created_at = datetime.datetime(
            year=2020,
            month=11,
            day=2,
            hour=15,
            minute=17,
            second=23,
            microsecond=420000,
            tzinfo=datetime.timezone.utc,
        )
        self.assertEqual(created_at, tracker_issue_comment.created_at)

    @patch("jira.resources.Attachment", autospec=AttachmentSpec, spec_set=True)
    @patch("jira.resources.Comment", autospec=CommentSpec, spec_set=True)
    @patch_jira
    def test_get_tracker_issue_comments(
        self,
        jira_mock_class: MagicMock,
        issue_mock_class: MagicMock,
        comment_mock_class: MagicMock,
        attachment_mock_class: MagicMock,
    ) -> None:
        issue_comment_mock = comment_mock_class(options=ANY, session=ANY)
        issue_comment_mock.id = 42069
        issue_comment_mock.created = "2020-11-02T15:17:23.420Z"
        issue_comment_mock.body = "This is a comment with an attachment !my-project/uploads/image.png!"
        issue_comment_mock.author = PropertyHolder()
        issue_comment_mock.author.displayName = "user1"

        attachment_mock = attachment_mock_class(options=ANY, session=ANY)
        attachment_mock.filename = "my-project/uploads/image.png"
        attachment_mock.mimeType = "image/png"
        attachment_mock.get.return_value = bytes("fake png", encoding="utf-8")

        issue_mock = issue_mock_class(options=ANY, session=ANY)
        issue_mock.key = "456"
        issue_mock.permalink.return_value = "http://tracker/issue/456"
        issue_mock.fields = PropertyHolder()
        issue_mock.fields.status = None
        issue_mock.fields.comment = PropertyHolder()
        issue_mock.fields.comment.comments = [issue_comment_mock]
        issue_mock.fields.attachment = [attachment_mock]

        jira_mock_class.return_value.issue.return_value = issue_mock

        client = JiraTrackerClient(
            configuration=JiraConfiguration(
                project="my-project",
            ),
        )
        tracker_issue_comments = client.get_tracker_issue_comments(issue_id="456")
        self.assertEqual(1, len(tracker_issue_comments))
        tracker_issue_comment = tracker_issue_comments[0]
        self.assertEqual("user1", tracker_issue_comment.author)
        self.assertEqual("42069", tracker_issue_comment.comment_id)
        created_at = datetime.datetime(
            year=2020,
            month=11,
            day=2,
            hour=15,
            minute=17,
            second=23,
            microsecond=420000,
            tzinfo=datetime.timezone.utc,
        )
        self.assertEqual(created_at, tracker_issue_comment.created_at)
        self.assertIn("This is a comment", tracker_issue_comment.body)
        self.assertEqual(1, len(tracker_issue_comment.attachments))
        self.assertIn("my-project/uploads/image.png", tracker_issue_comment.attachments)
        attachment = tracker_issue_comment.attachments["my-project/uploads/image.png"]
        self.assertEqual(bytes("fake png", encoding="utf-8"), attachment.content)
        self.assertEqual("my-project/uploads/image.png", attachment.filename)
        self.assertEqual("image/png", attachment.mime_type)
