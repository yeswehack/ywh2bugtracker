from functools import wraps
from unittest import TestCase
from unittest.mock import (
    ANY,
    MagicMock,
    patch,
)

from gitlab import (
    Gitlab,
    GitlabError,
)
from gitlab.v4.objects import (
    Project,
    ProjectIssue,
    ProjectIssueNote,
)
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
    TrackerComments,
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


def patch_gitlab(func):
    @wraps(func)
    @patch('gitlab.v4.objects.ProjectIssue', autospec=ProjectIssueSpec, spec_set=True)
    @patch('gitlab.v4.objects.ProjectIssueManager', autospec=True, spec_set=True)
    @patch('gitlab.v4.objects.Project', autospec=ProjectSpec, spec_set=True)
    @patch('gitlab.v4.objects.ProjectManager', autospec=True, spec_set=True)
    @patch('ywh2bt.core.api.trackers.gitlab.Gitlab', autospec=GitlabSpec, spec_set=True)
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
        issue_mock.web_url = 'http://tracker/issue/123'
        issue_mock.state = 'opened'
        issue_manager_mock.list.return_value = [issue_mock]

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
                project='my-project',
            ),
        )
        issue = client.get_tracker_issue(issue_id='123')
        self.assertIsInstance(issue, TrackerIssue)
        self.assertEqual('123', issue.issue_id)
        self.assertEqual('http://tracker/issue/123', issue.issue_url)
        self.assertEqual('my-project', issue.project)
        self.assertFalse(issue.is_closed)

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
        issue_mock.web_url = 'http://tracker/issue/456'
        issue_mock.state = 'opened'
        issue_manager_mock.list.return_value = [issue_mock]

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
                project='my-project',
            ),
        )
        issue = client.get_tracker_issue(issue_id='123')
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
        issue_mock.web_url = 'http://tracker/issue/456'
        issue_mock.state = 'opened'
        issue_manager_mock.create.return_value = issue_mock

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
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
            technical_information='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
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
        self.assertFalse(issue.is_closed)

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

        project_manager_mock.get.side_effect = GitlabError('Project not found')

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
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
            technical_information='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
            tracking_status='AFI',
            program=ReportProgram(
                title='My program',
                slug='my-program',
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

        issue_manager_mock.create.side_effect = GitlabError('Unable to create issue')

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
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
            technical_information='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
            tracking_status='AFI',
            program=ReportProgram(
                title='My program',
                slug='my-program',
            ),
        )
        with self.assertRaises(GitLabTrackerClientError):
            client.send_report(
                report=report,
            )

    @patch('gitlab.v4.objects.ProjectIssueNote', autospec=ProjectIssueNoteSpec, spec_set=True)
    @patch('gitlab.v4.objects.ProjectIssueNoteManager', autospec=True, spec_set=True)
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
        issue_mock.web_url = 'http://tracker/issue/456'
        issue_mock.state = 'opened'
        issue_manager_mock.list.return_value = [issue_mock]

        project_issue_note_manager_mock = project_issue_note_manager_mock_class(gl=ANY)
        issue_mock.notes = project_issue_note_manager_mock

        project_issue_note_mock = project_issue_note_mock_class(manager=ANY, attrs=ANY)
        project_issue_note_mock.id = 147
        project_issue_note_manager_mock.create.return_value = project_issue_note_mock

        client = GitLabTrackerClient(
            configuration=GitLabConfiguration(
                project='my-project',
            ),
        )
        tracker_issue = TrackerIssue(
            tracker_url='http://tracker/issue/456',
            project='my-project',
            issue_id='456',
            issue_url='http://tracker/issue/456',
            is_closed=False,
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
        tracker_comments = client.send_logs(
            tracker_issue=tracker_issue,
            logs=logs,
        )
        self.assertIsInstance(tracker_comments, TrackerComments)
        self.assertEqual(tracker_issue, tracker_comments.tracker_issue)
        self.assertEqual(1, len(tracker_comments.added_comments))
        self.assertEqual('147', tracker_comments.added_comments[0].comment_id)
