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
from yeswehack.api import (
    Report as YesWeHackRawApiReport,
)

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
from ywh2bt.core.api.trackers.github.tracker import GitHubTrackerClient
from ywh2bt.core.configuration.trackers.github import GitHubConfiguration


def patch_github(func):
    @patch('github.Issue.Issue', autospec=True, spec_set=True)
    @patch('github.Repository.Repository', autospec=True, spec_set=True)
    @patch('github.NamedUser.NamedUser', autospec=True, spec_set=True)
    @patch('ywh2bt.core.api.trackers.github.tracker.Github', autospec=True, spec_set=True)
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


class TestGitHubTrackerClient(TestCase):

    @patch_github
    def test_get_tracker_issue(
        self,
        github_mock_class: MagicMock,
        named_user_mock_class: MagicMock,
        repository_mock_class: MagicMock,
        issue_mock_class: MagicMock,
    ) -> None:
        issue_mock = issue_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        issue_mock.id = 123
        issue_mock.html_url = 'http://tracker/issue/123'
        issue_mock.closed_at = None

        repository_mock = repository_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        repository_mock.get_issues.return_value = [issue_mock]

        user_mock = named_user_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        user_mock.id = 1

        github_mock_class.return_value.get_repo.return_value = repository_mock
        github_mock_class.return_value.get_user.return_value = user_mock

        client = GitHubTrackerClient(
            configuration=GitHubConfiguration(
                project='my-project',
            ),
        )
        issue = client.get_tracker_issue(issue_id='123')
        self.assertIsInstance(issue, TrackerIssue)
        self.assertEqual('123', issue.issue_id)
        self.assertEqual('http://tracker/issue/123', issue.issue_url)
        self.assertEqual('my-project', issue.project)
        self.assertFalse(issue.closed)

    @patch_github
    def test_get_tracker_issue_not_found(
        self,
        github_mock_class: MagicMock,
        named_user_mock_class: MagicMock,
        repository_mock_class: MagicMock,
        issue_mock_class: MagicMock,
    ) -> None:
        issue_mock = issue_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        issue_mock.id = 123
        issue_mock.html_url = 'http://tracker/issue/123'
        issue_mock.closed_at = None

        repository_mock = repository_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        repository_mock.get_issues.return_value = [issue_mock]

        user_mock = named_user_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        user_mock.id = 1

        github_mock_class.return_value.get_repo.return_value = repository_mock
        github_mock_class.return_value.get_user.return_value = user_mock

        client = GitHubTrackerClient(
            configuration=GitHubConfiguration(
                project='my-project',
            ),
        )
        issue = client.get_tracker_issue(issue_id='456')
        self.assertIsNone(issue)

    @patch_github
    def test_send_report(
        self,
        github_mock_class: MagicMock,
        named_user_mock_class: MagicMock,
        repository_mock_class: MagicMock,
        issue_mock_class: MagicMock,
    ) -> None:
        issue_mock = issue_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        issue_mock.id = 456
        issue_mock.html_url = 'http://tracker/issue/456'
        issue_mock.closed_at = None

        repository_mock = repository_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        repository_mock.create_issue.return_value = issue_mock

        user_mock = named_user_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        user_mock.id = 1

        github_mock_class.return_value.get_repo.return_value = repository_mock
        github_mock_class.return_value.get_user.return_value = user_mock

        client = GitHubTrackerClient(
            configuration=GitHubConfiguration(
                project='my-project',
            ),
        )
        raw_report = YesWeHackRawApiReport(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id='123',
            title='A bug report',
            local_id='YWH-123',
            bug_type=BugType(
                name='bug-type',
                link='http://bug.example.com/type',
                remediation_link='http://bug.example.com/type/remediation',
            ),
            scope='',
            cvss=Cvss(
                criticity='critical',
                score=9.0,
                vector='vector',
            ),
            end_point='/',
            vulnerable_part='post',
            part_name='param',
            payload_sample='abcde',
            technical_environment='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
            status='accepted',
            tracking_status='AFI',
            program=ReportProgram(
                title='My program',
                slug='my-program',
            ),
        )
        issue = client.send_report(
            report=report,
        )
        self.assertIsInstance(issue, TrackerIssue)
        self.assertEqual('456', issue.issue_id)
        self.assertEqual('http://tracker/issue/456', issue.issue_url)
        self.assertEqual('my-project', issue.project)
        self.assertFalse(issue.closed)

    @patch('github.IssueComment.IssueComment', autospec=True, spec_set=True)
    @patch_github
    def test_send_logs(
        self,
        github_mock_class: MagicMock,
        named_user_mock_class: MagicMock,
        repository_mock_class: MagicMock,
        issue_mock_class: MagicMock,
        issue_comment_mock_class: MagicMock,
    ) -> None:
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

        user_mock = named_user_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        user_mock.id = 1
        user_mock.name = 'user1'

        issue_comment_mock = issue_comment_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        issue_comment_mock.id = 147
        issue_comment_mock.user = user_mock
        issue_comment_mock.created_at = created_at
        issue_comment_mock.body = 'This is a comment'

        issue_mock = issue_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        issue_mock.id = 456
        issue_mock.html_url = 'http://tracker/issue/456'
        issue_mock.closed_at = None
        issue_mock.create_comment.return_value = issue_comment_mock

        repository_mock = repository_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        repository_mock.get_issues.return_value = [issue_mock]

        github_mock_class.return_value.get_repo.return_value = repository_mock
        github_mock_class.return_value.get_user.return_value = user_mock

        client = GitHubTrackerClient(
            configuration=GitHubConfiguration(
                project='my-project',
            ),
        )
        tracker_issue = TrackerIssue(
            tracker_url='http://tracker/issue/456',
            project='my-project',
            issue_id='456',
            issue_url='http://tracker/issue/456',
            closed=False,
        )
        logs = [
            Log(
                created_at='2021-01-28 16:00:54.140843',
                log_id=987,
                log_type='comment',
                private=False,
                author=Author(
                    username='Anonymous',
                ),
                message_html='This is a comment',
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
        self.assertEqual('147', tracker_issue_comment.comment_id)
        self.assertEqual('user1', tracker_issue_comment.author)
        self.assertEqual(created_at, tracker_issue_comment.created_at)

    @patch('ywh2bt.core.api.trackers.github.tracker.requests')
    @patch('github.IssueComment.IssueComment', autospec=True, spec_set=True)
    @patch_github
    def test_get_tracker_issue_comments(
        self,
        github_mock_class: MagicMock,
        named_user_mock_class: MagicMock,
        repository_mock_class: MagicMock,
        issue_mock_class: MagicMock,
        issue_comment_mock_class: MagicMock,
        requests_mock: MagicMock,
    ) -> None:
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

        user_mock = named_user_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        user_mock.id = 1
        user_mock.name = 'user1'

        issue_comment_mock = issue_comment_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        issue_comment_mock.id = 42069
        issue_comment_mock.user = user_mock
        issue_comment_mock.created_at = created_at
        issue_comment_mock.body = 'This is a comment with an attachment ![img](https://github.com/my-project/uploads/image.png)'

        issue_mock = issue_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        issue_mock.id = 456
        issue_mock.html_url = 'http://tracker/issue/456'
        issue_mock.closed_at = None
        issue_mock.get_comments.return_value = [issue_comment_mock]

        repository_mock = repository_mock_class(requester=ANY, headers=ANY, attributes=ANY, completed=ANY)
        repository_mock.get_issues.return_value = [issue_mock]

        github_mock_class.return_value.get_repo.return_value = repository_mock
        github_mock_class.return_value.get_user.return_value = user_mock

        def requests_get_mock(url):
            if url == 'https://github.com/my-project/uploads/image.png':
                response_spec = create_autospec(requests.Response)
                response = response_spec()
                response.ok = True
                response.headers = {
                    'Content-Disposition': 'filename="original-image.png"',
                    'Content-Type': 'image/png',
                }
                response.content = bytes('fake png', encoding='utf-8')
                return response
            raise requests.RequestException(f'Unhandled request to {url}')

        requests_mock.get = requests_get_mock

        client = GitHubTrackerClient(
            configuration=GitHubConfiguration(
                project='my-project',
            ),
        )
        tracker_issue_comments = client.get_tracker_issue_comments(issue_id='456')
        self.assertEqual(1, len(tracker_issue_comments))
        tracker_issue_comment = tracker_issue_comments[0]
        self.assertEqual('user1', tracker_issue_comment.author)
        self.assertEqual('42069', tracker_issue_comment.comment_id)
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
        self.assertIn('This is a comment', tracker_issue_comment.body)
        self.assertEqual(1, len(tracker_issue_comment.attachments))
        self.assertIn('https://github.com/my-project/uploads/image.png', tracker_issue_comment.attachments)
        attachment = tracker_issue_comment.attachments['https://github.com/my-project/uploads/image.png']
        self.assertEqual(bytes('fake png', encoding='utf-8'), attachment.content)
        self.assertEqual('original-image.png', attachment.filename)
        self.assertEqual('image/png', attachment.mime_type)
