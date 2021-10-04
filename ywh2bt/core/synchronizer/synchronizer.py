"""Models and functions used for data synchronisation between YesWeHack and trackers."""
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from string import Template
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    cast,
)

from ywh2bt.core.api.models.report import (
    Attachment,
    CloseLog,
    CommentLog,
    CvssUpdateLog,
    DetailsUpdateLog,
    Log,
    PriorityUpdateLog,
    REPORT_STATUS_TRANSLATIONS,
    Report,
    RewardLog,
    StatusUpdateLog,
    TrackerUpdateLog,
    TrackingStatusLog,
)
from ywh2bt.core.api.tracker import (
    SendLogsResult,
    TrackerClient,
    TrackerClientError,
    TrackerIssue,
    TrackerIssueComment,
    TrackerIssueComments,
    TrackerIssueState,
)
from ywh2bt.core.api.yeswehack import (
    YesWeHackApiClient,
    YesWeHackApiClientError,
)
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.configuration.tracker import Trackers
from ywh2bt.core.configuration.yeswehack import (
    FeedbackOptions,
    Program,
    Programs,
    SynchronizeOptions,
    YesWeHackConfiguration,
    YesWeHackConfigurations,
)
from ywh2bt.core.factories.tracker_clients import (
    TrackerClientsAbstractFactory,
)
from ywh2bt.core.factories.yeswehack_api_clients import (
    YesWeHackApiClientsAbstractFactory,
)
from ywh2bt.core.markdown import markdown_to_ywh
from ywh2bt.core.state.decrypt import StateDecryptor
from ywh2bt.core.state.encrypt import StateEncryptor
from ywh2bt.core.synchronizer.error import SynchronizerError
from ywh2bt.core.synchronizer.listener import (
    NoOpSynchronizerListener,
    SynchronizerEndEvent,
    SynchronizerEndFetchReportsEvent,
    SynchronizerEndSendReportEvent,
    SynchronizerEvent,
    SynchronizerListener,
    SynchronizerStartEvent,
    SynchronizerStartFetchReportsEvent,
    SynchronizerStartSendReportEvent,
)


class Synchronizer:
    """A class used for data synchronisation between YesWeHack and trackers."""

    _configuration: RootConfiguration
    _yes_we_hack_api_clients_factory: YesWeHackApiClientsAbstractFactory
    _tracker_clients_factory: TrackerClientsAbstractFactory
    _listener: SynchronizerListener
    _message_formatter: AbstractSynchronizerMessageFormatter

    def __init__(
        self,
        configuration: RootConfiguration,
        yes_we_hack_api_clients_factory: YesWeHackApiClientsAbstractFactory,
        tracker_clients_factory: TrackerClientsAbstractFactory,
        listener: Optional[SynchronizerListener] = None,
        message_formatter: Optional[AbstractSynchronizerMessageFormatter] = None,
    ):
        """
        Initialize self.

        Args:
            configuration: a configuration
            yes_we_hack_api_clients_factory: a YesWeHackApiClients factory
            tracker_clients_factory: a TrackerClients factory
            listener: an observer that will receive synchronization events
            message_formatter: a message formatter
        """
        self._configuration = configuration
        self._yes_we_hack_api_clients_factory = yes_we_hack_api_clients_factory
        self._tracker_clients_factory = tracker_clients_factory
        self._listener = listener or NoOpSynchronizerListener()
        self._message_formatter = message_formatter or SynchronizerMessageFormatter()

    def synchronize(
        self,
    ) -> None:
        """Synchronize YesWeHack and the trackers."""
        self._send_event(
            event=SynchronizerStartEvent(
                configuration=self._configuration,
            ),
        )
        yeswehack_configurations = cast(YesWeHackConfigurations, self._configuration.yeswehack)
        for yeswehack_name, yeswehack_configuration in yeswehack_configurations.items():
            self._send_programs_from_yeswehack_configuration(
                configuration=self._configuration,
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
            )
        self._send_event(
            event=SynchronizerEndEvent(
                configuration=self._configuration,
            ),
        )

    def _send_event(
        self,
        event: SynchronizerEvent,
    ) -> None:
        self._listener.on_event(
            event=event,
        )

    def _send_programs_from_yeswehack_configuration(
        self,
        configuration: RootConfiguration,
        yeswehack_name: str,
        yeswehack_configuration: YesWeHackConfiguration,
    ) -> None:
        yeswehack_client = self._yes_we_hack_api_clients_factory.get_yeswehack_api_client(
            configuration=yeswehack_configuration,
        )
        programs = cast(Programs, yeswehack_configuration.programs)
        for program in programs:
            if program.slug is None:
                continue
            self._send_event(
                event=SynchronizerStartFetchReportsEvent(
                    configuration=configuration,
                    yeswehack_name=yeswehack_name,
                    yeswehack_configuration=yeswehack_configuration,
                    program_slug=program.slug,
                ),
            )
            reports = self._get_afi_reports(
                yeswehack_client=yeswehack_client,
                program=program,
            )
            self._send_event(
                event=SynchronizerEndFetchReportsEvent(
                    configuration=configuration,
                    yeswehack_name=yeswehack_name,
                    yeswehack_configuration=yeswehack_configuration,
                    program_slug=program.slug,
                    reports=reports,
                ),
            )
            self._send_reports_to_trackers(
                configuration=configuration,
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
                yeswehack_client=yeswehack_client,
                program=program,
                reports=reports,
            )

    def _get_afi_reports(
        self,
        yeswehack_client: YesWeHackApiClient,
        program: Program,
    ) -> List[Report]:
        program_slug = cast(str, program.slug)
        filters = {
            'filter[trackingStatus][0]': 'AFI',
        }
        synchronize_options = cast(SynchronizeOptions, program.synchronize_options)
        feedback_options = cast(FeedbackOptions, program.feedback_options)
        include_tracked = any(
            (
                synchronize_options.upload_private_comments,
                synchronize_options.upload_public_comments,
                synchronize_options.upload_cvss_updates,
                synchronize_options.upload_details_updates,
                synchronize_options.upload_priority_updates,
                synchronize_options.upload_rewards,
                synchronize_options.upload_status_updates,
                feedback_options.download_tracker_comments,
                feedback_options.issue_closed_to_report_afv,
            ),
        )
        if include_tracked:
            filters['filter[trackingStatus][1]'] = 'T'
        try:
            return yeswehack_client.get_program_reports(
                slug=program_slug,
                filters=filters,
            )
        except YesWeHackApiClientError as e:
            raise SynchronizerError(
                f'Unable to get AFI/T reports for program {program_slug}',
            ) from e

    def _send_reports_to_trackers(
        self,
        configuration: RootConfiguration,
        yeswehack_name: str,
        yeswehack_configuration: YesWeHackConfiguration,
        yeswehack_client: YesWeHackApiClient,
        program: Program,
        reports: List[Report],
    ) -> None:
        for report in reports:
            self._send_report_to_trackers(
                configuration=configuration,
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
                yeswehack_client=yeswehack_client,
                program=program,
                report=report,
            )

    def _send_report_to_trackers(
        self,
        configuration: RootConfiguration,
        yeswehack_name: str,
        yeswehack_configuration: YesWeHackConfiguration,
        yeswehack_client: YesWeHackApiClient,
        program: Program,
        report: Report,
    ) -> None:
        if not program.bugtrackers_name:
            return
        for tracker_name in program.bugtrackers_name:
            self._send_report_to_tracker(
                configuration=configuration,
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
                yeswehack_client=yeswehack_client,
                tracker_name=tracker_name,
                synchronize_options=cast(SynchronizeOptions, program.synchronize_options),
                feedback_options=cast(FeedbackOptions, program.feedback_options),
                report=report,
            )

    def _send_report_to_tracker(
        self,
        configuration: RootConfiguration,
        yeswehack_name: str,
        yeswehack_configuration: YesWeHackConfiguration,
        yeswehack_client: YesWeHackApiClient,
        tracker_name: str,
        synchronize_options: SynchronizeOptions,
        feedback_options: FeedbackOptions,
        report: Report,
    ) -> None:
        tracker_configuration = cast(Trackers, configuration.bugtrackers)[tracker_name]
        tracker_client = self._tracker_clients_factory.get_tracker_client(
            configuration=tracker_configuration,
        )
        self._send_event(
            event=SynchronizerStartSendReportEvent(
                configuration=configuration,
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
                program_slug=report.program.slug,
                tracker_name=tracker_name,
                report=report,
            ),
        )
        report_synchronizer = ReportSynchronizer(
            report=report,
            yeswehack_client=yeswehack_client,
            tracker_name=tracker_name,
            tracker_client=tracker_client,
            synchronize_options=synchronize_options,
            feedback_options=feedback_options,
            message_formatter=self._message_formatter,
        )
        synchronize_report_result = report_synchronizer.synchronize_report()
        is_created_issue = synchronize_report_result.is_created_issue
        self._send_event(
            event=SynchronizerEndSendReportEvent(
                configuration=configuration,
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
                program_slug=report.program.slug,
                tracker_name=tracker_name,
                report=report,
                is_created_issue=is_created_issue,
                is_existing_issue=synchronize_report_result.is_existing_issue,
                new_report_status=synchronize_report_result.new_report_status,
                tracking_status_updated=report.tracking_status != 'T' or not is_created_issue,
                tracker_issue=synchronize_report_result.send_logs_result.tracker_issue,
                issue_added_comments=[
                    comment.comment_id
                    for comment in synchronize_report_result.send_logs_result.added_comments or []
                ],
                report_added_comments=synchronize_report_result.download_comments_result.downloaded_comments or [],
            ),
        )


class ReportSynchronizer:
    """A class used for data synchronisation between a YesWeHack report and a tracker issue."""

    _report: Report
    _yeswehack_client: YesWeHackApiClient
    _tracker_name: str
    _tracker_client: TrackerClient[Any]
    _synchronize_options: SynchronizeOptions
    _feedback_options: FeedbackOptions
    _message_formatter: AbstractSynchronizerMessageFormatter

    def __init__(
        self,
        report: Report,
        yeswehack_client: YesWeHackApiClient,
        tracker_name: str,
        tracker_client: TrackerClient[Any],
        synchronize_options: SynchronizeOptions,
        feedback_options: FeedbackOptions,
        message_formatter: Optional[AbstractSynchronizerMessageFormatter] = None,
    ) -> None:
        """
        Initialize self.

        Args:
            report: a report to be synchronized
            yeswehack_client: a YesWeHackApiClient
            tracker_name: a tracker name
            tracker_client: a TrackerClient
            synchronize_options: synchronization options
            feedback_options: feedback options
            message_formatter: an optional message formatter
        """
        self._report = report
        self._yeswehack_client = yeswehack_client
        self._tracker_name = tracker_name
        self._tracker_client = tracker_client
        self._synchronize_options = synchronize_options
        self._feedback_options = feedback_options
        self._message_formatter = message_formatter or SynchronizerMessageFormatter()

    def synchronize_report(
        self,
    ) -> SynchronizeReportResult:
        """
        Synchronize a YesWeHack report and a tracker issue.

        Raises:
            SynchronizerError: if a synchronization error occur

        Returns:
            the result of the synchronization
        """
        log = self._report.get_last_tracking_status_update_log(
            tracker_name=self._tracker_name,
        )
        is_created_issue = False
        tracker_issue = None
        if log and isinstance(log, TrackingStatusLog):
            is_created_issue = True
            tracker_issue = self._get_tracker_issue_from_logs(
                log=log,
            )
        if tracker_issue is None:
            if not self._synchronize_options.recreate_missing_issues:
                return SynchronizeReportResult(
                    is_created_issue=is_created_issue,
                    is_existing_issue=False,
                    new_report_status=None,
                    send_logs_result=SendLogsResult(
                        tracker_issue=None,
                        added_comments=[],
                    ),
                    download_comments_result=DownloadCommentsResult(
                        downloaded_comments=[],
                    ),
                )
            is_created_issue = False
            tracker_issue = self._create_tracker_issue()
        if not isinstance(tracker_issue, TrackerIssue):
            raise SynchronizerError(
                f'Unable to create new or get existing issue for #{self._report.report_id} in {self._tracker_name}',
            )
        if self._report.tracking_status != 'T' or not is_created_issue:
            self._update_tracking_status(
                tracker_issue=tracker_issue,
            )
        tracker_issue_state = TrackerIssueState(
            closed=False,
            bugtracker_name=self._tracker_name,
        )
        logs = self._report.logs
        if is_created_issue:
            log_state = self._get_last_tracker_update_log()
            if log_state:
                last_tracker_update_log, tracker_issue_state = log_state
                if last_tracker_update_log:
                    logs = self._report.get_logs_after(
                        log=last_tracker_update_log,
                    )
        send_logs_result = self._send_synchronizable_logs(
            tracker_issue=tracker_issue,
            logs=logs,
        )
        for added_comment in send_logs_result.added_comments:
            tracker_issue_state.add_downloaded_comment(added_comment.comment_id)
        download_comments_result = self._download_comments(
            tracker_issue=tracker_issue,
            exclude_comments=tracker_issue_state.downloaded_comments,
        )
        for downloaded_comment in download_comments_result.downloaded_comments:
            tracker_issue_state.add_downloaded_comment(downloaded_comment)
        new_report_status = self._update_report_status(
            tracker_issue=tracker_issue,
            tracker_issue_state=tracker_issue_state,
        )
        issue_status = self._get_issue_status_change(
            tracker_issue=tracker_issue,
            tracker_issue_state=tracker_issue_state,
        )
        tracker_issue_state.closed = tracker_issue.closed
        self._post_report_tracker_update(
            tracker_issue=tracker_issue,
            tracker_issue_state=tracker_issue_state,
            send_logs_result=send_logs_result,
            download_comments_result=download_comments_result,
            new_report_status=new_report_status,
            issue_status=issue_status,
        )
        return SynchronizeReportResult(
            is_created_issue=is_created_issue,
            is_existing_issue=True,
            new_report_status=new_report_status,
            send_logs_result=send_logs_result,
            download_comments_result=download_comments_result,
        )

    def _get_issue_status_change(
        self,
        tracker_issue: TrackerIssue,
        tracker_issue_state: TrackerIssueState,
    ) -> str:
        if tracker_issue.closed:
            return 'Unchanged (closed)' if tracker_issue_state.closed else 'Opened -> Closed'
        return 'Closed -> Opened' if tracker_issue_state.closed else 'Unchanged (opened)'

    def _get_tracker_issue_from_logs(
        self,
        log: TrackingStatusLog,
    ) -> Optional[TrackerIssue]:
        if all((log.tracker_id, log.tracker_url)):
            return self._tracker_client.get_tracker_issue(
                issue_id=cast(str, log.tracker_id),
            )
        return None

    def _create_tracker_issue(
        self,
    ) -> TrackerIssue:
        try:
            tracker_issue = self._tracker_client.send_report(
                report=self._report,
            )
        except TrackerClientError as send_error:
            raise SynchronizerError(
                f'Unable to send report #{self._report.report_id} to {self._tracker_name}',
            ) from send_error
        return tracker_issue

    def _update_tracking_status(
        self,
        tracker_issue: TrackerIssue,
    ) -> None:
        message = self._message_formatter.format_tracking_status_update_message(
            tracker_type=self._tracker_client.tracker_type,
            tracker_issue=tracker_issue,
        )
        try:
            self._yeswehack_client.put_report_tracking_status(
                report=self._report,
                status='T',
                tracker_name=self._tracker_name,
                issue_id=tracker_issue.issue_id,
                issue_url=tracker_issue.issue_url,
                comment=message,
            )
        except YesWeHackApiClientError as tracking_status_error:
            raise SynchronizerError(
                f'Unable to update tracking status for report #{self._report.report_id}',
            ) from tracking_status_error

    def _get_last_tracker_update_log(
        self,
    ) -> Optional[Tuple[Log, TrackerIssueState]]:
        for log in reversed(self._report.logs):
            if isinstance(log, TrackerUpdateLog):
                state = StateDecryptor.decrypt(
                    encrypted_state=log.tracker_token or '',
                    key=self._report.report_id,
                    state_type=TrackerIssueState,
                )
                if state and state.bugtracker_name == self._tracker_name:
                    return log, state
        return None

    def _send_synchronizable_logs(
        self,
        tracker_issue: TrackerIssue,
        logs: List[Log],
    ) -> SendLogsResult:
        synchronizable_logs = []
        for log in logs:
            synchronize = self._is_synchronizable_log(
                log=log,
            )
            if synchronize:
                synchronizable_logs.append(log)
        if not synchronizable_logs:
            return SendLogsResult(
                tracker_issue=tracker_issue,
                added_comments=[],
            )
        return self._send_logs(
            tracker_issue=tracker_issue,
            logs=synchronizable_logs,
        )

    def _is_synchronizable_log(
        self,
        log: Log,
    ) -> bool:
        synchronize_options = self._synchronize_options
        return any((
            isinstance(log, CloseLog) and synchronize_options.upload_status_updates,
            isinstance(log, CommentLog) and synchronize_options.upload_public_comments and not log.private,
            isinstance(log, CommentLog) and synchronize_options.upload_private_comments and log.private,
            isinstance(log, CvssUpdateLog) and synchronize_options.upload_cvss_updates,
            isinstance(log, DetailsUpdateLog) and synchronize_options.upload_details_updates,
            isinstance(log, PriorityUpdateLog) and synchronize_options.upload_priority_updates,
            isinstance(log, RewardLog) and synchronize_options.upload_rewards,
            isinstance(log, StatusUpdateLog) and synchronize_options.upload_status_updates,
        ))

    def _send_logs(
        self,
        tracker_issue: TrackerIssue,
        logs: List[Log],
    ) -> SendLogsResult:
        try:
            return self._tracker_client.send_logs(
                tracker_issue=tracker_issue,
                logs=logs,
            )
        except TrackerClientError as send_error:
            raise SynchronizerError(
                f'Unable to send logs for #{self._report.report_id} to {self._tracker_name}',
            ) from send_error

    def _download_comments(
        self,
        tracker_issue: TrackerIssue,
        exclude_comments: Optional[List[str]] = None,
    ) -> DownloadCommentsResult:
        if not self._feedback_options.download_tracker_comments:
            return DownloadCommentsResult(
                downloaded_comments=[],
            )
        downloaded_comments = []
        comments = self._get_tracker_issue_comments(
            tracker_issue=tracker_issue,
            exclude_comments=exclude_comments,
        )
        for comment in comments:
            if comment.comment_id in (exclude_comments or []):
                continue
            self._download_comment(
                tracker_issue=tracker_issue,
                tracker_comment=comment,
            )
            downloaded_comments.append(comment.comment_id)
        return DownloadCommentsResult(
            downloaded_comments=downloaded_comments,
        )

    def _get_tracker_issue_comments(
        self,
        tracker_issue: TrackerIssue,
        exclude_comments: Optional[List[str]] = None,
    ) -> TrackerIssueComments:
        try:
            return self._tracker_client.get_tracker_issue_comments(
                issue_id=tracker_issue.issue_id,
                exclude_comments=exclude_comments,
            )
        except TrackerClientError as issue_comments_error:
            raise SynchronizerError(
                f'Unable to get issue comments for #{tracker_issue.issue_id}',
            ) from issue_comments_error

    def _download_comment(
        self,
        tracker_issue: TrackerIssue,
        tracker_comment: TrackerIssueComment,
    ) -> None:
        attachments = {}
        for attachment_key, attachment in tracker_comment.attachments.items():
            try:
                uploaded_attachment = self._yeswehack_client.post_report_attachment(
                    report=self._report,
                    filename=attachment.filename,
                    file_content=attachment.content,
                    file_type=attachment.mime_type,
                )
            except YesWeHackApiClientError as upload_attachment_error:
                raise SynchronizerError(
                    f'Unable to upload attachment {attachment.filename} for report #{self._report.report_id}',
                ) from upload_attachment_error
            attachments[attachment_key] = uploaded_attachment
        try:
            self._yeswehack_client.post_report_tracker_message(
                report=self._report,
                tracker_name=self._tracker_name,
                issue_id=tracker_issue.issue_id,
                issue_url=tracker_issue.issue_url,
                comment=self._message_formatter.format_download_comment(
                    comment=tracker_comment,
                    attachments=attachments,
                ),
                attachments=[uploaded_attachment.name for attachment_key, uploaded_attachment in attachments.items()],
            )
        except YesWeHackApiClientError as tracker_message_error:
            raise SynchronizerError(
                f'Unable to download comment {tracker_comment.comment_id} for report #{self._report.report_id}',
            ) from tracker_message_error

    def _post_report_tracker_update(
        self,
        tracker_issue: TrackerIssue,
        tracker_issue_state: TrackerIssueState,
        send_logs_result: SendLogsResult,
        download_comments_result: DownloadCommentsResult,
        new_report_status: Optional[Tuple[str, str]],
        issue_status: str,
    ) -> None:
        post_update = any(
            (
                send_logs_result.added_comments,
                download_comments_result.downloaded_comments,
                tracker_issue_state.changed,
            ),
        )
        if post_update:
            try:
                self._yeswehack_client.post_report_tracker_update(
                    report=self._report,
                    tracker_name=self._tracker_name,
                    issue_id=tracker_issue.issue_id,
                    issue_url=tracker_issue.issue_url,
                    token=StateEncryptor.encrypt(
                        key=self._report.report_id,
                        state=tracker_issue_state,
                    ),
                    comment=self._message_formatter.format_synchronization_done_message(
                        tracker_type=self._tracker_client.tracker_type,
                        report=self._report,
                        send_logs_result=send_logs_result,
                        download_comments_result=download_comments_result,
                        new_report_status=new_report_status,
                        issue_status=issue_status,
                    ),
                )
            except YesWeHackApiClientError as tracker_update_error:
                raise SynchronizerError(
                    f'Unable to post tracker update for report #{self._report.report_id}',
                ) from tracker_update_error

    def _update_report_status(
        self,
        tracker_issue: TrackerIssue,
        tracker_issue_state: TrackerIssueState,
    ) -> Optional[Tuple[str, str]]:
        if not self._feedback_options.issue_closed_to_report_afv:
            return None
        condition = tracker_issue.closed and not tracker_issue_state.closed
        ask_verif_status = 'ask_verif'
        if condition and self._report.status != ask_verif_status:
            status_updated = self._put_report_status(
                status=ask_verif_status,
                comment='\n'.join(
                    (
                        'Hello,',
                        'A fix has been deployed for this vulnerability.',
                        'Could you please verify that you cannot reproduce the bug nor bypass the fix?',
                        'Thanks for your help,',
                        'Regards,',
                    ),
                ),
            )
            return (self._report.status, ask_verif_status) if status_updated else None
        return None

    def _put_report_status(
        self,
        status: str,
        comment: str,
    ) -> bool:
        try:
            self._yeswehack_client.put_status(
                report=self._report,
                status=status,
                comment=self._message_formatter.format_status_update_comment(
                    comment=comment,
                ),
            )
        except YesWeHackApiClientError:
            return False
        return True


class AbstractSynchronizerMessageFormatter(ABC):
    """Abstract message formatter for a synchronizer."""

    @abstractmethod
    def format_tracking_status_update_message(
        self,
        tracker_type: str,
        tracker_issue: TrackerIssue,
    ) -> str:
        """
        Format a tracking status update message.

        Args:
            tracker_type: a tracker type
            tracker_issue: a tracker issue
        """

    @abstractmethod
    def format_synchronization_done_message(
        self,
        report: Report,
        tracker_type: str,
        send_logs_result: SendLogsResult,
        download_comments_result: DownloadCommentsResult,
        new_report_status: Optional[Tuple[str, str]],
        issue_status: str,
    ) -> str:
        """
        Format a synchronization done message.

        Args:
            report: a report
            tracker_type: a tracker type
            send_logs_result: a result of the synchronization of the report logs with the issue
            download_comments_result: a result of the synchronization of the issue comments with the report
            new_report_status: new status of the report, if changed
            issue_status: status of the issue
        """

    @abstractmethod
    def format_download_comment(
        self,
        comment: TrackerIssueComment,
        attachments: Dict[str, Attachment],
    ) -> str:
        """
        Format a downloaded comment.

        Args:
            comment: a comment
            attachments: a dict of attachments
        """

    @abstractmethod
    def format_status_update_comment(
        self,
        comment: str,
    ) -> str:
        """
        Format a report status update comment.

        Args:
            comment: a comment
        """


class SynchronizerMessageFormatter(AbstractSynchronizerMessageFormatter):
    """Message formatter for a synchronizer."""

    _tracking_status_update_template: Template = Template(
        'Synchronized with bugtracker: ${tracker_url} on project : ${project}.'
        + '\n'
        + 'Tracked to [${tracker_type} #${issue_id}](${issue_url}).',
    )
    _synchronization_done_template: Template = Template(
        'Synchronized with bugtracker: ${tracker_url} on project : ${project}.'
        + '\n'
        + 'Tracked to [${tracker_type} #${issue_id}](${issue_url}).'
        + '\n'
        + 'Report comments added to issue: ${issue_added_comment_count}'
        + '\n'
        + 'Issue comments added to report: ${report_added_comment_count}'
        + '\n'
        + 'Report status: ${report_status}'
        + '\n'
        + 'Issue status: ${issue_status}',
    )
    _download_comment_template: Template = Template(
        'Comment from bugtracker:'
        + '\n'
        + 'Date: ${date}'
        + '\n'
        + 'Author: ${author}'
        + '\n\n'
        + '${comment}',
    )
    _status_update_comment_template: Template = Template(
        '${comment}',
    )

    def format_tracking_status_update_message(
        self,
        tracker_type: str,
        tracker_issue: TrackerIssue,
    ) -> str:
        """
        Format a tracking status update message.

        Args:
            tracker_type: a tracker type
            tracker_issue: a tracker issue

        Returns:
            a formatted message
        """
        return self._tracking_status_update_template.substitute(
            tracker_type=tracker_type,
            tracker_url=tracker_issue.tracker_url,
            project=tracker_issue.project,
            issue_id=tracker_issue.issue_id,
            issue_url=tracker_issue.issue_url,
        )

    def format_synchronization_done_message(
        self,
        report: Report,
        tracker_type: str,
        send_logs_result: SendLogsResult,
        download_comments_result: DownloadCommentsResult,
        new_report_status: Optional[Tuple[str, str]],
        issue_status: str,
    ) -> str:
        """
        Format a synchronization done message.

        Args:
            report: a report
            tracker_type: a tracker type
            send_logs_result: a result of the synchronization of the report logs with the issue
            download_comments_result: a result of the synchronization of the issue comments with the report
            new_report_status: new status of the report, if changed
            issue_status: status of the issue

        Returns:
            a formatted message
        """
        tracker_issue = send_logs_result.tracker_issue
        report_status = 'Unchanged'
        if new_report_status:
            unknown_status_translation = 'Unknown'
            old_status, new_status = new_report_status
            old_status_translation = REPORT_STATUS_TRANSLATIONS.get(old_status, unknown_status_translation)
            new_status_translation = REPORT_STATUS_TRANSLATIONS.get(new_status, unknown_status_translation)
            report_status = f'{old_status_translation} -> {new_status_translation}'
        return self._synchronization_done_template.substitute(
            tracker_type=tracker_type,
            tracker_url=tracker_issue.tracker_url if tracker_issue else '',
            project=tracker_issue.project if tracker_issue else '',
            issue_id=tracker_issue.issue_id if tracker_issue else '',
            issue_url=tracker_issue.issue_url if tracker_issue else '',
            issue_added_comment_count=len(send_logs_result.added_comments),
            report_added_comment_count=len(download_comments_result.downloaded_comments),
            report_status=report_status,
            issue_status=issue_status,
        )

    def format_download_comment(
        self,
        comment: TrackerIssueComment,
        attachments: Dict[str, Attachment],
    ) -> str:
        """
        Format a downloaded comment.

        Args:
            comment: a comment
            attachments: a dict of attachments

        Returns:
            a formatted comment
        """
        return self._download_comment_template.substitute(
            date=comment.created_at,
            author=comment.author,
            comment=markdown_to_ywh(
                message=comment.body,
                attachments=attachments,
            ),
        )

    def format_status_update_comment(
        self,
        comment: str,
    ) -> str:
        """
        Format a report status update comment.

        Args:
            comment: a comment

        Returns:
            a formatted comment for a status update
        """
        return self._status_update_comment_template.substitute(
            comment=comment,
        )

    def _string_state(
        self,
        is_created_issue: bool,
        issue_state: TrackerIssueState,
        last_state: Optional[TrackerIssueState],
    ) -> str:
        if is_created_issue:
            return self._string_state_for_update(
                issue_state=issue_state,
                last_state=last_state,
            )
        return 'created'

    def _string_state_for_update(
        self,
        issue_state: TrackerIssueState,
        last_state: Optional[TrackerIssueState],
    ) -> str:
        string_state = []
        if issue_state != last_state:
            if last_state:
                string_state.append('closed' if last_state.closed else 'opened')
            else:
                string_state.append('???')
            string_state.append(' -> ')
            string_state.append('closed' if issue_state.closed else 'opened')
        return ''.join(string_state)


@dataclass
class DownloadCommentsResult:
    """A result of downloading comments from a tracker."""

    downloaded_comments: List[str]


@dataclass
class SynchronizeReportResult:
    """A result of synchronizing a report with a tracker."""

    is_created_issue: bool
    is_existing_issue: bool
    new_report_status: Optional[Tuple[str, str]]
    send_logs_result: SendLogsResult
    download_comments_result: DownloadCommentsResult
