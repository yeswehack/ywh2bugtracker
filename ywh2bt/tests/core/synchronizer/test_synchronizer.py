from __future__ import annotations

import datetime
from io import StringIO
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)
from unittest import TestCase
from unittest.mock import (
    MagicMock,
    create_autospec,
)

from yeswehack.api import (
    Report as YesWeHackRawApiReport,
    YesWeHack as YesWeHackRawApi,
)

from ywh2bt.core.api.models.report import (
    Attachment,
    Author,
    BugType,
    CommentLog,
    Cvss,
    Log,
    Report,
    ReportProgram,
    TrackerUpdateLog,
    TrackingStatusLog,
)
from ywh2bt.core.api.tracker import (
    SendLogsResult,
    TrackerClient,
    TrackerIssue,
    TrackerIssueComment,
    TrackerIssueState,
)
from ywh2bt.core.api.yeswehack import YesWeHackApiClient
from ywh2bt.core.configuration.error import AttributesError
from ywh2bt.core.configuration.headers import Headers
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.configuration.tracker import (
    TrackerConfiguration,
    Trackers,
)
from ywh2bt.core.configuration.yeswehack import (
    Bugtrackers,
    FeedbackOptions,
    Program,
    Programs,
    SynchronizeOptions,
    YesWeHackConfiguration,
    YesWeHackConfigurations,
)
from ywh2bt.core.error import print_error
from ywh2bt.core.state.encrypt import StateEncryptor
from ywh2bt.core.synchronizer.listener import (
    SynchronizerEvent,
    SynchronizerListener,
)
from ywh2bt.core.synchronizer.synchronizer import (
    AbstractSynchronizerMessageFormatter,
    DownloadCommentsResult,
    ReportSynchronizer,
    SynchronizeReportResult,
)


class TestReportSynchronizer(TestCase):

    def setUp(self) -> None:
        TrackerConfiguration.register_subtype(
            subtype_name='my',
            subtype_class=MyTrackerTrackerConfiguration,
        )

    def validate_configuration(
        self,
        configuration: RootConfiguration,
    ) -> None:
        try:
            configuration.validate()
        except AttributesError as e:
            error_stream = StringIO()
            print_error(
                error=e,
                stream=error_stream,
            )
            self.fail(error_stream.getvalue())

    def test_new_afi_no_logs(
        self,
    ) -> None:
        report = self._build_report(
            report_id=123,
            tracking_status='AFI',
        )
        ywh_api_client_mock = create_autospec(YesWeHackApiClient, spec_set=True)
        tracker_client_mock = create_autospec(TrackerClient, spec_set=True)
        tracker_client_mock.tracker_type = 'MyTracker'
        tracker_client_mock.send_report.return_value = TrackerIssue(
            tracker_url='http://tracker/issue/1',
            project='my-project',
            issue_id='1',
            issue_url='http://tracker/issue/1',
            closed=False,
        )
        Given(
            case=self,
            report=report,
            yeswehack_client=ywh_api_client_mock,
            tracker_name='my-tracker',
            tracker_client=tracker_client_mock,
            synchronize_options=SynchronizeOptions(
                upload_private_comments=True,
                upload_public_comments=True,
                upload_details_updates=True,
                upload_rewards=True,
                upload_status_updates=True,
            ),
            feedback_options=FeedbackOptions(),
            message_formatter=SimpleMessageFormatter(
                tracking_status_update_format='issue url: {tracker_issue.issue_url}',
                synchronization_done_format='issue url: {send_logs_result.tracker_issue.issue_url}',
                download_comment_format='comment: {comment}',
                status_update_comment_format='comment: {comment}',
            ),
        ).when_synchronize_report(
        ).then_assert_no_error(
        ).then_assert_has_result(
        ).then_assert_is_not_existing_issue(
        ).then_assert_tracker_client_send_report_called_once_with(
            report=report,
        ).then_assert_tracker_client_send_logs_not_called(
        ).then_assert_yeswehack_client_put_report_tracking_status_called_once_with(
            report=report,
            status='T',
            tracker_name='my-tracker',
            issue_id='1',
            issue_url='http://tracker/issue/1',
            comment='issue url: http://tracker/issue/1',
        )

    def test_new_afi_all_new_logs(
        self,
    ) -> None:
        comment_log1 = CommentLog(
            created_at='2021-01-01T00:00:00+00:00',
            log_id=1,
            log_type='comment',
            private=True,
            author=Author(
                username='user1',
            ),
            message_html='This is a comment',
            attachments=[],
        )
        report = self._build_report(
            report_id=123,
            tracking_status='AFI',
            logs=[
                comment_log1,
            ],
        )
        ywh_api_client_mock = create_autospec(YesWeHackApiClient, spec_set=True)
        tracker_client_mock = create_autospec(TrackerClient, spec_set=True)
        tracker_client_mock.tracker_type = 'MyTracker'
        issue = TrackerIssue(
            tracker_url='http://tracker/issue/1',
            project='my-project',
            issue_id='1',
            issue_url='http://tracker/issue/1',
            closed=False,
        )
        tracker_client_mock.send_report.return_value = issue
        tracker_client_mock.send_logs.return_value = SendLogsResult(
            tracker_issue=issue,
            added_comments=[
                TrackerIssueComment(
                    created_at=datetime.datetime(
                        year=2020,
                        month=1,
                        day=1,
                        hour=15,
                        minute=17,
                        second=23,
                        microsecond=420000,
                        tzinfo=datetime.timezone.utc,
                    ),
                    author='tracker-user',
                    comment_id='456',
                    body='',
                    attachments={},
                ),
            ],
        )
        Given(
            case=self,
            report=report,
            yeswehack_client=ywh_api_client_mock,
            tracker_name='my-tracker',
            tracker_client=tracker_client_mock,
            synchronize_options=SynchronizeOptions(
                upload_private_comments=True,
                upload_public_comments=True,
                upload_details_updates=True,
                upload_rewards=True,
                upload_status_updates=True,
            ),
            feedback_options=FeedbackOptions(),
            message_formatter=SimpleMessageFormatter(
                tracking_status_update_format='issue url: {tracker_issue.issue_url}',
                synchronization_done_format='issue url: {send_logs_result.tracker_issue.issue_url}',
                download_comment_format='comment: {comment}',
                status_update_comment_format='comment: {comment}',
            ),
        ).when_synchronize_report(
        ).then_assert_no_error(
        ).then_assert_has_result(
        ).then_assert_is_not_existing_issue(
        ).then_assert_tracker_client_send_report_called_once_with(
            report=report,
        ).then_assert_tracker_client_send_logs_called_once_with(
            tracker_issue=issue,
            logs=[
                comment_log1,
            ],
        ).then_assert_yeswehack_client_put_report_tracking_status_called_once_with(
            report=report,
            status='T',
            tracker_name='my-tracker',
            issue_id='1',
            issue_url='http://tracker/issue/1',
            comment='issue url: http://tracker/issue/1',
        )

    def test_partially_synced(
        self,
    ) -> None:
        comment_log1 = CommentLog(
            created_at='2021-01-01T00:00:00+00:00',
            log_id=1,
            log_type='comment',
            private=True,
            author=Author(
                username='user1',
            ),
            message_html='This is a comment',
            attachments=[],
        )
        tracking_status = TrackingStatusLog(
            created_at='2021-01-01T00:30:00+00:00',
            log_id=1,
            log_type='tracking-status',
            private=True,
            author=Author(
                username='user1',
            ),
            message_html='Tracked',
            attachments=[],
            tracker_name='my-tracker',
            tracker_url='http://tracker/issue/1',
            tracker_id='1',
        )
        tracker_update_log1 = TrackerUpdateLog(
            created_at='2021-01-01T01:00:00+00:00',
            log_id=2,
            log_type='tracker-update',
            private=True,
            author=Author(
                username='user1',
            ),
            message_html='This is a a tracker update',
            attachments=[],
            tracker_name='my-tracker',
            tracker_id='1',
            tracker_url='http://tracker/issue/1',
            tracker_token=StateEncryptor.encrypt(
                key='123',
                state=TrackerIssueState(
                    closed=False,
                    bugtracker_name='my-tracker',
                ),
            ),
        )
        comment_log2 = CommentLog(
            created_at='2021-01-01T02:00:00+00:00',
            log_id=3,
            log_type='comment',
            private=True,
            author=Author(
                username='user1',
            ),
            message_html='This is another comment',
            attachments=[],
        )
        report = self._build_report(
            report_id=123,
            tracking_status='T',
            logs=[
                comment_log1,
                tracking_status,
                tracker_update_log1,
                comment_log2,
            ],
        )
        ywh_api_client_mock = create_autospec(YesWeHackApiClient, spec_set=True)
        tracker_client_mock = create_autospec(TrackerClient, spec_set=True)
        tracker_client_mock.tracker_type = 'MyTracker'
        issue = TrackerIssue(
            tracker_url='http://tracker/issue/1',
            project='my-project',
            issue_id='1',
            issue_url='http://tracker/issue/1',
            closed=False,
        )
        tracker_client_mock.get_tracker_issue.return_value = issue
        tracker_client_mock.send_logs.return_value = SendLogsResult(
            tracker_issue=issue,
            added_comments=[
                TrackerIssueComment(
                    created_at=datetime.datetime(
                        year=2020,
                        month=1,
                        day=1,
                        hour=15,
                        minute=17,
                        second=23,
                        microsecond=420000,
                        tzinfo=datetime.timezone.utc,
                    ),
                    author='tracker-user',
                    comment_id='456',
                    body='',
                    attachments={},
                ),
            ],
        )
        Given(
            case=self,
            report=report,
            yeswehack_client=ywh_api_client_mock,
            tracker_name='my-tracker',
            tracker_client=tracker_client_mock,
            synchronize_options=SynchronizeOptions(
                upload_private_comments=True,
                upload_public_comments=True,
                upload_details_updates=True,
                upload_rewards=True,
                upload_status_updates=True,
            ),
            feedback_options=FeedbackOptions(),
            message_formatter=SimpleMessageFormatter(
                tracking_status_update_format='issue url: {tracker_issue.issue_url}',
                synchronization_done_format='issue url: {send_logs_result.tracker_issue.issue_url}',
                download_comment_format='comment: {comment}',
                status_update_comment_format='comment: {comment}',
            ),
        ).when_synchronize_report(
        ).then_assert_no_error(
        ).then_assert_has_result(
        ).then_assert_is_existing_issue(
        ).then_assert_tracker_client_send_report_not_called(
        ).then_assert_tracker_client_send_logs_called_once_with(
            tracker_issue=issue,
            logs=[
                comment_log2,
            ],
        ).then_assert_yeswehack_client_post_report_tracker_update_called_once_with(
            report=report,
            tracker_name='my-tracker',
            issue_id='1',
            issue_url='http://tracker/issue/1',
            comment='issue url: http://tracker/issue/1',
            token=StateEncryptor.encrypt(
                key='123',
                state=TrackerIssueState(
                    closed=False,
                    bugtracker_name='my-tracker',
                    downloaded_comments=['456']
                ),
            ),
        )

    def test_already_tracked(
        self,
    ) -> None:
        report = self._build_report(
            report_id=123,
            tracking_status='T',
            logs=[
                TrackingStatusLog(
                    created_at='2021-01-01T00:00:00+00:00',
                    log_id=1,
                    log_type='tracking-status',
                    private=True,
                    author=Author(
                        username='user1',
                    ),
                    message_html='Tracked',
                    attachments=[],
                    tracker_name='my-tracker',
                    tracker_url='http://tracker/issue/1',
                    tracker_id='1',
                ),
            ],
        )
        ywh_api_client_mock = create_autospec(YesWeHackApiClient, spec_set=True)
        tracker_client_mock = create_autospec(TrackerClient, spec_set=True)
        tracker_client_mock.tracker_type = 'MyTracker'
        tracker_client_mock.get_tracker_issue.return_value = TrackerIssue(
            tracker_url='http://tracker/issue/1',
            project='my-project',
            issue_id='1',
            issue_url='http://tracker/issue/1',
            closed=False,
        )
        Given(
            case=self,
            report=report,
            yeswehack_client=ywh_api_client_mock,
            tracker_name='my-tracker',
            tracker_client=tracker_client_mock,
            synchronize_options=SynchronizeOptions(
                upload_private_comments=True,
                upload_public_comments=True,
                upload_details_updates=True,
                upload_rewards=True,
                upload_status_updates=True,
            ),
            feedback_options=FeedbackOptions(),
            message_formatter=SimpleMessageFormatter(
                tracking_status_update_format='issue url: {tracker_issue.issue_url}',
                synchronization_done_format='issue url: {send_logs_result.tracker_issue.issue_url}',
                download_comment_format='comment: {comment}',
                status_update_comment_format='comment: {comment}',
            ),
        ).when_synchronize_report(
        ).then_assert_no_error(
        ).then_assert_has_result(
        ).then_assert_is_existing_issue(
        ).then_assert_tracker_client_send_report_not_called(
        ).then_assert_tracker_client_send_logs_not_called(
        ).then_assert_yeswehack_client_put_report_tracking_status_not_called()

    def test_already_tracked_not_found(
        self,
    ) -> None:
        report = self._build_report(
            report_id=123,
            tracking_status='T',
            logs=[
                TrackingStatusLog(
                    created_at='2021-01-01',
                    log_id=1,
                    log_type='tracking-status',
                    private=True,
                    author=Author(
                        username='user1',
                    ),
                    message_html='Tracked',
                    attachments=[],
                    tracker_name='my-tracker',
                    tracker_url='http://tracker/issue/1',
                    tracker_id='1',
                ),
            ],
        )
        ywh_api_client_mock = create_autospec(YesWeHackApiClient, spec_set=True)
        ywh_api_client_mock.put_report_tracking_status.return_value = None
        tracker_client_mock = create_autospec(TrackerClient, spec_set=True)
        tracker_client_mock.tracker_type = 'MyTracker'
        tracker_client_mock.get_tracker_issue.return_value = None
        tracker_client_mock.send_report.return_value = TrackerIssue(
            tracker_url='http://tracker/issue/2',
            project='my-project',
            issue_id='2',
            issue_url='http://tracker/issue/2',
            closed=False,
        )
        Given(
            case=self,
            report=report,
            yeswehack_client=ywh_api_client_mock,
            tracker_name='my-tracker',
            tracker_client=tracker_client_mock,
            synchronize_options=SynchronizeOptions(
                upload_private_comments=True,
                upload_public_comments=True,
                upload_details_updates=True,
                upload_rewards=True,
                upload_status_updates=True,
            ),
            feedback_options=FeedbackOptions(),
            message_formatter=SimpleMessageFormatter(
                tracking_status_update_format='issue url: {tracker_issue.issue_url}',
                synchronization_done_format='issue url: {send_logs_result.tracker_issue.issue_url}',
                download_comment_format='comment: {comment}',
                status_update_comment_format='comment: {comment}',
            ),
        ).when_synchronize_report(
        ).then_assert_no_error(
        ).then_assert_has_result(
        ).then_assert_is_not_existing_issue(
        ).then_assert_tracker_client_send_report_called_once_with(
            report=report,
        ).then_assert_tracker_client_send_logs_not_called(
        ).then_assert_yeswehack_client_put_report_tracking_status_called_once_with(
            report=report,
            status='T',
            tracker_name='my-tracker',
            issue_id='2',
            issue_url='http://tracker/issue/2',
            comment='issue url: http://tracker/issue/2',
        )

    def _build_report(
        self,
        report_id: int,
        tracking_status: str = 'AFI',
        attachments: Optional[List[Attachment]] = None,
        logs: Optional[List[Log]] = None,
    ) -> Report:
        raw_report = YesWeHackRawApiReport(
            ywh_api=create_autospec(YesWeHackRawApi),
            lazy=True,
            id=report_id,
        )
        return Report(
            raw_report=raw_report,
            report_id=str(report_id),
            title='A bug report',
            local_id=f'YWH-{report_id}',
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
            attachments=attachments or [],
            hunter=Author(
                username='a-hunter',
            ),
            logs=logs or [],
            status='accepted',
            tracking_status=tracking_status,
            program=ReportProgram(
                title='Program 1',
                slug='program1',
            ),
        )

    def _build_configuration(
        self,
        tracker_key: str = 'tracker',
    ) -> RootConfiguration:
        return RootConfiguration(
            yeswehack=YesWeHackConfigurations(
                ywh_test=YesWeHackConfiguration(
                    apps_headers=Headers(
                        **{
                            'X-YesWeHack-Apps': 'qwerty',
                        },
                    ),
                    login='api-consumer',
                    password='password',
                    programs=Programs(
                        items=[
                            Program(
                                slug='program1',
                                bugtrackers_name=Bugtrackers(
                                    [
                                        tracker_key,
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ),
            bugtrackers=Trackers(
                **{
                    tracker_key: MyTrackerTrackerConfiguration(),
                },
            ),
        )


class MyTrackerTrackerConfiguration(TrackerConfiguration):
    pass


class HistorizingSynchronizerListener(SynchronizerListener):
    events: List[SynchronizerEvent]

    def __init__(self) -> None:
        super().__init__()
        self.events = []

    def on_event(
        self,
        event: SynchronizerEvent,
    ) -> None:
        self.events.append(event)


class SimpleMessageFormatter(AbstractSynchronizerMessageFormatter):
    tracking_status_update_format: str
    synchronization_done_format: str
    download_comment_format: str
    status_update_comment_format: str

    def __init__(
        self,
        tracking_status_update_format: str,
        synchronization_done_format: str,
        download_comment_format: str,
        status_update_comment_format: str,
    ) -> None:
        self.tracking_status_update_format = tracking_status_update_format
        self.synchronization_done_format = synchronization_done_format
        self.download_comment_format = download_comment_format
        self.status_update_comment_format = status_update_comment_format

    def format_tracking_status_update_message(
        self,
        tracker_type: str,
        tracker_issue: TrackerIssue,
    ) -> str:
        return self.tracking_status_update_format.format(
            tracker_type=tracker_type,
            tracker_issue=tracker_issue,
        )

    def format_synchronization_done_message(
        self,
        report: Report,
        tracker_type: str,
        send_logs_result: SendLogsResult,
        download_comments_result: DownloadCommentsResult,
        new_report_status: Optional[Tuple[str, str]],
    ) -> str:
        return self.synchronization_done_format.format(
            report=report,
            tracker_type=tracker_type,
            send_logs_result=send_logs_result,
            download_comments_result=download_comments_result,
        )

    def format_download_comment(
        self,
        comment: TrackerIssueComment,
        attachments: Dict[str, Attachment],
    ) -> str:
        return self.download_comment_format.format(
            author=comment.author,
            comment=comment.body,
        )

    def format_status_update_comment(
        self,
        comment: str,
    ) -> str:
        return self.status_update_comment_format.format(
            comment=comment,
        )


class Given:
    case: TestCase
    report: Report
    yeswehack_client: YesWeHackApiClient
    tracker_name: str
    tracker_client: TrackerClient[Any]
    synchronize_options: SynchronizeOptions
    feedback_options: FeedbackOptions
    message_formatter: Optional[AbstractSynchronizerMessageFormatter]

    def __init__(
        self,
        case: TestCase,
        report: Report,
        yeswehack_client: YesWeHackApiClient,
        tracker_name: str,
        tracker_client: TrackerClient[Any],
        synchronize_options: SynchronizeOptions,
        feedback_options: FeedbackOptions,
        message_formatter: Optional[AbstractSynchronizerMessageFormatter] = None,
    ) -> None:
        self.case = case
        self.report = report
        self.yeswehack_client = yeswehack_client
        self.tracker_name = tracker_name
        self.tracker_client = tracker_client
        self.synchronize_options = synchronize_options
        self.feedback_options = feedback_options
        self.message_formatter = message_formatter

    def when_synchronize_report(
        self,
    ) -> Assert:
        listener = HistorizingSynchronizerListener()
        synchronizer = ReportSynchronizer(
            report=self.report,
            yeswehack_client=self.yeswehack_client,
            tracker_name=self.tracker_name,
            tracker_client=self.tracker_client,
            synchronize_options=self.synchronize_options,
            feedback_options=self.feedback_options,
            message_formatter=self.message_formatter,
        )
        result = None
        error = None
        try:
            result = synchronizer.synchronize_report()
        except Exception as e:
            error = e
        return Assert(
            case=self.case,
            yeswehack_client=self.yeswehack_client,
            tracker_client=self.tracker_client,
            events=listener.events,
            result=result,
            error=error,
        )


class Assert:
    case: TestCase
    yeswehack_client: Union[MagicMock, YesWeHackApiClient]
    tracker_client: Union[MagicMock, TrackerClient[Any]]
    events: List[SynchronizerEvent]
    result: Optional[SynchronizeReportResult]
    error: Optional[Exception]

    def __init__(
        self,
        case: TestCase,
        yeswehack_client: Union[YesWeHackApiClient, MagicMock],
        tracker_client: Union[TrackerClient[Any], MagicMock],
        events: List[SynchronizerEvent],
        result: Optional[SynchronizeReportResult],
        error: Optional[Exception],
    ) -> None:
        self.case = case
        self.yeswehack_client = yeswehack_client
        self.tracker_client = tracker_client
        self.events = events
        self.result = result
        self.error = error

    def _serialize_error(
        self,
        error: Optional[Exception],
    ) -> Optional[str]:
        if not error:
            return None
        error_stream = StringIO()
        print_error(
            error=error,
            stream=error_stream,
        )
        return error_stream.getvalue()

    def then_assert_has_result(self) -> Assert:
        self.case.assertIsNotNone(self.result)
        return self

    def then_assert_has_no_result(self) -> Assert:
        self.case.assertIsNone(self.result)
        return self

    def then_assert_is_existing_issue_is(
        self,
        is_existing_issue: bool,
    ) -> Assert:
        self.case.assertIs(is_existing_issue, cast(SynchronizeReportResult, self.result).is_existing_issue)
        return self

    def then_assert_is_existing_issue(self) -> Assert:
        return self.then_assert_is_existing_issue_is(is_existing_issue=True)

    def then_assert_is_not_existing_issue(self) -> Assert:
        return self.then_assert_is_existing_issue_is(is_existing_issue=False)

    def then_assert_no_error(self) -> Assert:
        self.case.assertIsNone(self.error, msg=self._serialize_error(error=self.error))
        return self

    def then_assert_tracker_client_send_report_not_called(self) -> Assert:
        cast(MagicMock, self.tracker_client.send_report).assert_not_called()
        return self

    def then_assert_tracker_client_send_report_called_once_with(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Assert:
        cast(MagicMock, self.tracker_client.send_report).assert_called_once_with(*args, **kwargs)
        return self

    def then_assert_tracker_client_send_logs_not_called(self) -> Assert:
        cast(MagicMock, self.tracker_client.send_logs).assert_not_called()
        return self

    def then_assert_tracker_client_send_logs_called_once_with(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Assert:
        cast(MagicMock, self.tracker_client.send_logs).assert_called_once_with(*args, **kwargs)
        return self

    def then_assert_yeswehack_client_put_report_tracking_status_not_called(self) -> Assert:
        cast(MagicMock, self.yeswehack_client.put_report_tracking_status).assert_not_called()
        return self

    def then_assert_yeswehack_client_put_report_tracking_status_called_once_with(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Assert:
        cast(MagicMock, self.yeswehack_client.put_report_tracking_status).assert_called_once_with(*args, **kwargs)
        return self

    def then_assert_yeswehack_client_post_report_tracker_update_not_called(self) -> Assert:
        cast(MagicMock, self.yeswehack_client.post_report_tracker_update).assert_not_called()
        return self

    def then_assert_yeswehack_client_post_report_tracker_update_called_once_with(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Assert:
        cast(MagicMock, self.yeswehack_client.post_report_tracker_update).assert_called_once_with(*args, **kwargs)
        return self
