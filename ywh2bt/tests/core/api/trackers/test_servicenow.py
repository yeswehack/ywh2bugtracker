import datetime
import sys
from collections import namedtuple
from functools import wraps
from unittest import (
    TestCase,
    skipIf,
)
from unittest.mock import (
    ANY,
    MagicMock,
    create_autospec,
    patch,
)

from aiosnow.exceptions import AiosnowException
from aiosnow.models._schema.fields.mapped import IntegerMapping
from aiosnow.request import Response
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
from ywh2bt.core.api.trackers.servicenow.tracker import (
    ServiceNowTrackerClient,
    ServiceNowTrackerClientError,
)
from ywh2bt.core.configuration.trackers.servicenow import ServiceNowConfiguration


class ResponseSpec(Response):
    data = None


def skip_before_py38(func):
    @skipIf(sys.version_info[0:2] < (3, 8), 'No AsyncMock for before Python 3.8')
    @wraps(func)
    def skipped(
        *args,
        **kwargs,
    ):
        return func(
            *args,
            **kwargs,
        )

    return skipped


def patch_servicenow(func):
    @patch('aiohttp.ClientSession', autospec=True, spec_set=True)
    @patch('ywh2bt.core.api.trackers.servicenow.tracker.IncidentModel', autospec=True, spec_set=True)
    @patch('ywh2bt.core.api.trackers.servicenow.tracker.Client', autospec=True, spec_set=True)
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


class TestServiceNowTrackerClient(TestCase):

    @skip_before_py38
    @patch_servicenow
    def test_get_tracker_issue(
        self,
        client_mock_class: MagicMock,
        incident_model_mock_class: MagicMock,
        session_mock_class: MagicMock,
    ) -> None:
        response = create_autospec(ResponseSpec, spec_set=True)
        response.data = {
            'sys_id': '456',
            'state': namedtuple('State', 'value')('opened'),
        }
        client = client_mock_class(
            address=ANY,
        )
        client.get_session.return_value = session_mock_class()
        incident_model = incident_model_mock_class(
            client=client,
        )
        incident_model.__aenter__.return_value = incident_model
        incident_model.get_one.return_value = response

        tracker_client = ServiceNowTrackerClient(
            configuration=ServiceNowConfiguration(
                host='my-instance.servicenow.local',
            ),
        )
        issue = tracker_client.get_tracker_issue(issue_id='123')
        self.assertIsInstance(issue, TrackerIssue)
        self.assertEqual('123', issue.issue_id)
        self.assertEqual(
            'https://my-instance.servicenow.local/nav_to.do?uri=%2Fincident.do%3Fsys_id%3D456',
            issue.issue_url,
        )
        self.assertEqual('my-instance.servicenow.local', issue.project)
        self.assertFalse(issue.closed)

    @skip_before_py38
    @patch_servicenow
    def test_get_tracker_issue_not_found(
        self,
        client_mock_class: MagicMock,
        incident_model_mock_class: MagicMock,
        session_mock_class: MagicMock,
    ) -> None:
        client = client_mock_class(
            address=ANY,
        )
        client.get_session.return_value = session_mock_class()
        incident_model = incident_model_mock_class(
            client=client,
        )
        incident_model.__aenter__.return_value = incident_model
        incident_model.get_one.side_effect = AiosnowException

        tracker_client = ServiceNowTrackerClient(
            configuration=ServiceNowConfiguration(
                host='my-instance.servicenow.local',
            ),
        )
        issue = tracker_client.get_tracker_issue(issue_id='123')
        self.assertIsNone(issue)

    @skip_before_py38
    @patch_servicenow
    def test_send_report(
        self,
        client_mock_class: MagicMock,
        incident_model_mock_class: MagicMock,
        session_mock_class: MagicMock,
    ) -> None:
        response = create_autospec(ResponseSpec, spec_set=True)
        response.data = {
            'sys_id': '456',
            'number': 'INC0123',
        }
        client = client_mock_class(
            address=ANY,
        )
        client.get_session.return_value = session_mock_class()
        incident_model = incident_model_mock_class(
            client=client,
        )
        incident_model.__aenter__.return_value = incident_model
        incident_model.create.return_value = response
        tracker_client = ServiceNowTrackerClient(
            configuration=ServiceNowConfiguration(
                host='my-instance.servicenow.local',
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
        issue = tracker_client.send_report(
            report=report,
        )
        self.assertIsInstance(issue, TrackerIssue)
        self.assertEqual('456', issue.issue_id)
        self.assertEqual(
            'https://my-instance.servicenow.local/nav_to.do?uri=%2Fincident.do%3Fsys_id%3D456',
            issue.issue_url,
        )
        self.assertEqual('my-instance.servicenow.local', issue.project)
        self.assertFalse(issue.closed)

    @skip_before_py38
    @patch_servicenow
    def test_send_report_issue_create_error(
        self,
        client_mock_class: MagicMock,
        incident_model_mock_class: MagicMock,
        session_mock_class: MagicMock,
    ) -> None:
        response = create_autospec(ResponseSpec, spec_set=True)
        response.data = {
            'sys_id': '456',
            'number': 'INC0123',
        }
        client = client_mock_class(
            address=ANY,
        )
        client.get_session.return_value = session_mock_class()
        incident_model = incident_model_mock_class(
            client=client,
        )
        incident_model.__aenter__.return_value = incident_model
        incident_model.create.side_effect = AiosnowException
        tracker_client = ServiceNowTrackerClient(
            configuration=ServiceNowConfiguration(
                host='my-instance.servicenow.local',
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
        with self.assertRaises(ServiceNowTrackerClientError):
            tracker_client.send_report(
                report=report,
            )

    @skip_before_py38
    @patch('ywh2bt.core.api.trackers.servicenow.tracker.JournalModel', autospec=True, spec_set=True)
    @patch_servicenow
    def test_send_logs(
        self,
        client_mock_class: MagicMock,
        incident_model_mock_class: MagicMock,
        session_mock_class: MagicMock,
        journal_model_mock_class: MagicMock,
    ) -> None:
        incident_response = create_autospec(ResponseSpec, spec_set=True)
        incident_response.data = {
            'sys_id': '456',
            'number': 'INC0123',
            'state': IntegerMapping(
                key=1,
                value='New',
            ),
        }
        journal_response = create_autospec(ResponseSpec, spec_set=True)
        journal_response.data = {
            'sys_id': '147',
            'sys_created_on': datetime.datetime(
                year=2020,
                month=11,
                day=2,
                hour=15,
                minute=17,
                second=23,
                microsecond=420000,
                tzinfo=datetime.timezone.utc,
            ),
            'sys_created_by': 'user1',
            'goo': 'ga'
        }
        client = client_mock_class(
            address=ANY,
        )
        client.get_session.return_value = session_mock_class()
        incident_model = incident_model_mock_class(
            client=client,
        )
        incident_model.__aenter__.return_value = incident_model
        incident_model.get_one.return_value = incident_response
        journal_model = journal_model_mock_class(
            client=client,
        )
        journal_model.__aenter__.return_value = journal_model
        journal_model.get_one.return_value = journal_response
        tracker_client = ServiceNowTrackerClient(
            configuration=ServiceNowConfiguration(
                host='my-instance.servicenow.local',
            ),
        )
        tracker_issue = TrackerIssue(
            tracker_url='https://my-instance.servicenow.local/nav_to.do?uri=%2Fincident.do%3Fsys_id%3D456',
            project='my-project',
            issue_id='456',
            issue_url='https://my-instance.servicenow.local/nav_to.do?uri=%2Fincident.do%3Fsys_id%3D456',
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
        send_logs_result = tracker_client.send_logs(
            tracker_issue=tracker_issue,
            logs=logs,
        )
        self.assertIsInstance(send_logs_result, SendLogsResult)
        self.assertEqual(tracker_issue, send_logs_result.tracker_issue)
        self.assertEqual(1, len(send_logs_result.added_comments))
        tracker_issue_comment = send_logs_result.added_comments[0]
        self.assertEqual('147', tracker_issue_comment.comment_id)
        self.assertEqual('user1', tracker_issue_comment.author)
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

    @skip_before_py38
    @patch('ywh2bt.core.api.trackers.servicenow.tracker.select')
    @patch('ywh2bt.core.api.trackers.servicenow.tracker.InMemoryAttachmentModel', autospec=True, spec_set=True)
    @patch('ywh2bt.core.api.trackers.servicenow.tracker.JournalModel', autospec=True, spec_set=True)
    @patch_servicenow
    def test_get_tracker_issue_comments(
        self,
        client_mock_class: MagicMock,
        incident_model_mock_class: MagicMock,
        session_mock_class: MagicMock,
        journal_model_mock_class: MagicMock,
        attachment_model_mock_class: MagicMock,
        select_mock: MagicMock,
    ) -> None:
        incident_response = create_autospec(ResponseSpec, spec_set=True)
        incident_response.data = {
            'sys_id': '456',
            'number': 'INC0123',
        }
        journal_response = [
            {
                'sys_id': '147',
                'sys_created_on': datetime.datetime(
                    year=2020,
                    month=11,
                    day=2,
                    hour=15,
                    minute=17,
                    second=23,
                    microsecond=420000,
                    tzinfo=datetime.timezone.utc,
                ),
                'sys_created_by': 'user1',
                'value': 'This is a comment!',
            },
            {
                'sys_id': '148',
                'sys_created_on': datetime.datetime(
                    year=2020,
                    month=12,
                    day=25,
                    hour=5,
                    minute=31,
                    second=42,
                    microsecond=951627,
                    tzinfo=datetime.timezone.utc,
                ),
                'sys_created_by': 'user2',
                'value': 'Another comment!',
            },
        ]
        client = client_mock_class(
            address=ANY,
        )
        client.get_session.return_value = session_mock_class()
        incident_model = incident_model_mock_class(
            client=client,
        )
        incident_model.__aenter__.return_value = incident_model
        incident_model.get_one.return_value = incident_response
        journal_model = journal_model_mock_class(
            client=client,
        )
        journal_model.__aenter__.return_value = journal_model
        journal_model.get.return_value = journal_response
        attachment_model = attachment_model_mock_class(
            client=client,
        )
        attachment_model.__aenter__.return_value = attachment_model
        attachment_model.get.return_value = []
        tracker_client = ServiceNowTrackerClient(
            configuration=ServiceNowConfiguration(
                host='my-instance.servicenow.local',
            ),
        )
        tracker_issue_comments = tracker_client.get_tracker_issue_comments(issue_id='456')
        self.assertEqual(2, len(tracker_issue_comments))
        tracker_issue_comment1 = tracker_issue_comments[0]
        self.assertEqual('user1', tracker_issue_comment1.author)
        self.assertEqual('147', tracker_issue_comment1.comment_id)
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
        self.assertIn('This is a comment', tracker_issue_comment1.body)
        self.assertEqual(0, len(tracker_issue_comment1.attachments))
        tracker_issue_comment2 = tracker_issue_comments[1]
        self.assertEqual('user2', tracker_issue_comment2.author)
        self.assertEqual('148', tracker_issue_comment2.comment_id)
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
        self.assertIn('Another comment', tracker_issue_comment2.body)
        self.assertEqual(0, len(tracker_issue_comment2.attachments))
