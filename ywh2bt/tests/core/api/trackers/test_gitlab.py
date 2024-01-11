import datetime
from functools import wraps
from unittest import TestCase
from unittest.mock import (
    ANY,
    MagicMock,
    create_autospec,
    patch,
)

import requests
from gitlab import (
    Gitlab,
    GitlabError,
)
from gitlab.v4.objects import (
    Project,
    ProjectIssue,
    ProjectIssueNote,
)
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
from ywh2bt.core.api.trackers.gitlab import (
    GitLabTrackerClient,
    GitLabTrackerClientError,
)
from ywh2bt.core.configuration.trackers.gitlab import GitLabConfiguration


class GitlabSpec(Gitlab):
    projects = None


class ProjectSpec(Project):
    issues = None


class ProjectIssueSpec(ProjectIssue):
    id = None
    web_url = None
    state = None
    notes = None


class ProjectIssueNoteSpec(ProjectIssueNote):
    id = None
    noteable_iid = None
    created_at = None
    author = None
    body = None


def patch_gitlab(func):
    @patch("gitlab.v4.objects.ProjectIssue", autospec=ProjectIssueSpec, spec_set=True)
    @patch("gitlab.v4.objects.ProjectIssueManager", autospec=True, spec_set=True)
    @patch("gitlab.v4.objects.Project", autospec=ProjectSpec, spec_set=True)
    @patch("gitlab.v4.objects.ProjectManager", autospec=True, spec_set=True)
    @patch("ywh2bt.core.api.trackers.gitlab.Gitlab", autospec=GitlabSpec, spec_set=True)
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


class TestGitLabTrackerClient(TestCase):
    @patch_gitlab
    def test_get_tracker_issue(
        self,
        gitlab_mock_class: MagicMock,
        project_manager_mock_class: MagicMock,
        project_mock_class: MagicMock,
        project_issues_manager_mock_class: MagicMock,
        project_issue_mock_class: MagicMock,
    ) -> None:
        issue_manager_mock = project_issues_manager_mock_class(gl=ANY)
        project_manager_mock = project_manager_mock_class(gl=ANY)
        gitlab_mock_class.return_value.projects = project_manager_mock

        project_mock = project_mock_class(manager=ANY, attrs=ANY)
        project_mock.issues = issue_manager_mock

        project_manager_mock.get.return_value = project_mock

        issue_mock = project_issue_mock_class(manager=ANY, attrs=ANY)
        issue_mock.id = 123
        issue_mock.web_url = "http://tracker/issue/123"
        issue_mock.state = "opened"
        issue_manager_mock.list.return_value = [issue_mock]

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
                project="my-project",
            ),
        )
        issue = client.get_tracker_issue(issue_id="123")
        self.assertIsInstance(issue, TrackerIssue)
        self.assertEqual("123", issue.issue_id)
        self.assertEqual("http://tracker/issue/123", issue.issue_url)
        self.assertEqual("my-project", issue.project)
        self.assertFalse(issue.closed)

    @patch_gitlab
    def test_get_tracker_issue_not_found(
        self,
        gitlab_mock_class: MagicMock,
        project_manager_mock_class: MagicMock,
        project_mock_class: MagicMock,
        project_issues_manager_mock_class: MagicMock,
        project_issue_mock_class: MagicMock,
    ) -> None:
        issue_manager_mock = project_issues_manager_mock_class(gl=ANY)
        project_manager_mock = project_manager_mock_class(gl=ANY)
        gitlab_mock_class.return_value.projects = project_manager_mock

        project_mock = project_mock_class(manager=ANY, attrs=ANY)
        project_mock.issues = issue_manager_mock

        project_manager_mock.get.return_value = project_mock

        issue_mock = project_issue_mock_class(manager=ANY, attrs=ANY)
        issue_mock.id = 456
        issue_mock.web_url = "http://tracker/issue/456"
        issue_mock.state = "opened"
        issue_manager_mock.list.return_value = [issue_mock]

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
                project="my-project",
            ),
        )
        issue = client.get_tracker_issue(issue_id="123")
        self.assertIsNone(issue)

    @patch_gitlab
    def test_send_report(
        self,
        gitlab_mock_class: MagicMock,
        project_manager_mock_class: MagicMock,
        project_mock_class: MagicMock,
        project_issues_manager_mock_class: MagicMock,
        project_issue_mock_class: MagicMock,
    ) -> None:
        issue_manager_mock = project_issues_manager_mock_class(gl=ANY)
        project_manager_mock = project_manager_mock_class(gl=ANY)
        gitlab_mock_class.return_value.projects = project_manager_mock

        project_mock = project_mock_class(manager=ANY, attrs=ANY)
        project_mock.issues = issue_manager_mock

        project_manager_mock.get.return_value = project_mock

        issue_mock = project_issue_mock_class(manager=ANY, attrs=ANY)
        issue_mock.id = 456
        issue_mock.web_url = "http://tracker/issue/456"
        issue_mock.state = "opened"
        issue_manager_mock.create.return_value = issue_mock

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
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

    @patch_gitlab
    def test_send_report_error_project_not_found(
        self,
        gitlab_mock_class: MagicMock,
        project_manager_mock_class: MagicMock,
        project_mock_class: MagicMock,
        project_issues_manager_mock_class: MagicMock,
        project_issue_mock_class: MagicMock,
    ) -> None:
        project_manager_mock = project_manager_mock_class(gl=ANY)
        gitlab_mock_class.return_value.projects = project_manager_mock

        project_manager_mock.get.side_effect = GitlabError("Project not found")

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
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
        with self.assertRaises(GitLabTrackerClientError):
            client.send_report(
                report=report,
            )

    @patch_gitlab
    def test_send_report_issue_create_error(
        self,
        gitlab_mock_class: MagicMock,
        project_manager_mock_class: MagicMock,
        project_mock_class: MagicMock,
        project_issues_manager_mock_class: MagicMock,
        project_issue_mock_class: MagicMock,
    ) -> None:
        issue_manager_mock = project_issues_manager_mock_class(gl=ANY)
        project_manager_mock = project_manager_mock_class(gl=ANY)
        gitlab_mock_class.return_value.projects = project_manager_mock

        project_mock = project_mock_class(manager=ANY, attrs=ANY)
        project_mock.issues = issue_manager_mock

        project_manager_mock.get.return_value = project_mock

        issue_manager_mock.create.side_effect = GitlabError("Unable to create issue")

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
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
        with self.assertRaises(GitLabTrackerClientError):
            client.send_report(
                report=report,
            )

    @patch("gitlab.v4.objects.ProjectIssueNote", autospec=ProjectIssueNoteSpec, spec_set=True)
    @patch("gitlab.v4.objects.ProjectIssueNoteManager", autospec=True, spec_set=True)
    @patch_gitlab
    def test_send_logs(
        self,
        gitlab_mock_class: MagicMock,
        project_manager_mock_class: MagicMock,
        project_mock_class: MagicMock,
        project_issues_manager_mock_class: MagicMock,
        project_issue_mock_class: MagicMock,
        project_issue_note_manager_mock_class: MagicMock,
        project_issue_note_mock_class: MagicMock,
    ) -> None:
        issue_manager_mock = project_issues_manager_mock_class(gl=ANY)
        project_manager_mock = project_manager_mock_class(gl=ANY)
        gitlab_mock_class.return_value.projects = project_manager_mock

        project_mock = project_mock_class(manager=ANY, attrs=ANY)
        project_mock.issues = issue_manager_mock

        project_manager_mock.get.return_value = project_mock

        issue_mock = project_issue_mock_class(manager=ANY, attrs=ANY)
        issue_mock.id = 456
        issue_mock.web_url = "http://tracker/issue/456"
        issue_mock.state = "opened"
        issue_manager_mock.list.return_value = [issue_mock]

        project_issue_note_manager_mock = project_issue_note_manager_mock_class(gl=ANY)
        issue_mock.notes = project_issue_note_manager_mock

        project_issue_note_mock = project_issue_note_mock_class(manager=ANY, attrs=ANY)
        project_issue_note_mock.id = 147
        project_issue_note_mock.created_at = "2020-11-02T15:17:23.420Z"
        project_issue_note_mock.author = {
            "name": "user1",
        }
        project_issue_note_mock.body = "This is a comment"
        project_issue_note_manager_mock.create.return_value = project_issue_note_mock

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
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

    @patch("ywh2bt.core.api.trackers.gitlab.requests")
    @patch("gitlab.v4.objects.ProjectIssueNote", autospec=ProjectIssueNoteSpec, spec_set=True)
    @patch("gitlab.v4.objects.ProjectIssueNote", autospec=ProjectIssueNoteSpec, spec_set=True)
    @patch("gitlab.v4.objects.ProjectIssueNoteManager", autospec=True, spec_set=True)
    @patch_gitlab
    def test_get_tracker_issue_comments(
        self,
        gitlab_mock_class: MagicMock,
        project_manager_mock_class: MagicMock,
        project_mock_class: MagicMock,
        project_issues_manager_mock_class: MagicMock,
        project_issue_mock_class: MagicMock,
        project_issue_note_manager_mock_class: MagicMock,
        project_issue_note_mock_class1: MagicMock,
        project_issue_note_mock_class2: MagicMock,
        requests_mock: MagicMock,
    ) -> None:
        issue_manager_mock = project_issues_manager_mock_class(gl=ANY)
        project_manager_mock = project_manager_mock_class(gl=ANY)
        gitlab_mock_class.return_value.projects = project_manager_mock

        project_mock = project_mock_class(manager=ANY, attrs=ANY)
        project_mock.issues = issue_manager_mock

        project_manager_mock.get.return_value = project_mock

        issue_mock = project_issue_mock_class(manager=ANY, attrs=ANY)
        issue_mock.id = 456
        issue_mock.web_url = "http://tracker/issue/456"
        issue_mock.state = "opened"
        issue_manager_mock.list.return_value = [issue_mock]

        project_issue_note_manager_mock = project_issue_note_manager_mock_class(gl=ANY)
        issue_mock.notes = project_issue_note_manager_mock

        project_issue_note_mock1 = project_issue_note_mock_class1(manager=ANY, attrs=ANY)
        project_issue_note_mock1.id = 147
        project_issue_note_mock1.noteable_iid = 42069
        project_issue_note_mock1.created_at = "2020-11-02T15:17:23.420Z"
        project_issue_note_mock1.author = {
            "name": "user1",
        }
        project_issue_note_mock1.body = "This is a comment with an attachment ![img](uploads/image.png)"

        project_issue_note_mock2 = project_issue_note_mock_class2(manager=ANY, attrs=ANY)
        project_issue_note_mock2.id = 148
        project_issue_note_mock2.noteable_iid = 258
        project_issue_note_mock2.created_at = "2020-12-25T05:31:42.951627Z"
        project_issue_note_mock2.author = {
            "name": "user2",
        }
        project_issue_note_mock2.body = "Another comment with an attachment ![my image](uploads/hacker.png)"
        project_issue_note_manager_mock.list.return_value = [
            project_issue_note_mock2,
            project_issue_note_mock1,
        ]

        def requests_get_mock(url):
            if url == "https://gitlab.com/my-project/uploads/image.png":
                response_spec = create_autospec(requests.Response)
                response = response_spec()
                response.ok = True
                response.headers = {
                    "Content-Disposition": 'filename="original-image.png"',
                    "Content-Type": "image/png",
                }
                response.content = bytes("fake png", encoding="utf-8")
                return response
            if url == "https://gitlab.com/my-project/uploads/hacker.png":
                response_spec = create_autospec(requests.Response)
                response = response_spec()
                response.ok = True
                response.headers = {
                    "Content-Disposition": 'filename="original-hacker.png"',
                    "Content-Type": "image/png",
                }
                response.content = bytes("another fake png", encoding="utf-8")
                return response
            raise requests.RequestException(f"Unhandled request to {url}")

        requests_mock.get = requests_get_mock

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
                project="my-project",
            ),
        )
        tracker_issue_comments = client.get_tracker_issue_comments(issue_id="456")
        self.assertEqual(2, len(tracker_issue_comments))
        tracker_issue_comment1 = tracker_issue_comments[0]
        self.assertEqual("user1", tracker_issue_comment1.author)
        self.assertEqual("147", tracker_issue_comment1.comment_id)
        created_at1 = datetime.datetime(
            year=2020,
            month=11,
            day=2,
            hour=15,
            minute=17,
            second=23,
            microsecond=420000,
            tzinfo=datetime.timezone.utc,
        )
        self.assertEqual(created_at1, tracker_issue_comment1.created_at)
        self.assertIn("This is a comment", tracker_issue_comment1.body)
        self.assertEqual(1, len(tracker_issue_comment1.attachments))
        self.assertIn("uploads/image.png", tracker_issue_comment1.attachments)
        attachment1 = tracker_issue_comment1.attachments["uploads/image.png"]
        self.assertEqual(bytes("fake png", encoding="utf-8"), attachment1.content)
        self.assertEqual("original-image.png", attachment1.filename)
        self.assertEqual("image/png", attachment1.mime_type)
        tracker_issue_comment2 = tracker_issue_comments[1]
        self.assertEqual("user2", tracker_issue_comment2.author)
        self.assertEqual("148", tracker_issue_comment2.comment_id)
        created_at2 = datetime.datetime(
            year=2020,
            month=12,
            day=25,
            hour=5,
            minute=31,
            second=42,
            microsecond=951627,
            tzinfo=datetime.timezone.utc,
        )
        self.assertEqual(created_at2, tracker_issue_comment2.created_at)
        self.assertIn("Another comment", tracker_issue_comment2.body)
        self.assertEqual(1, len(tracker_issue_comment2.attachments))
        self.assertIn("uploads/hacker.png", tracker_issue_comment2.attachments)
        attachment2 = tracker_issue_comment2.attachments["uploads/hacker.png"]
        self.assertEqual(bytes("another fake png", encoding="utf-8"), attachment2.content)
        self.assertEqual("original-hacker.png", attachment2.filename)
        self.assertEqual("image/png", attachment2.mime_type)
