"""Models and functions used for data synchronisation between YesWeHack and trackers."""
from __future__ import annotations

from string import Template
from typing import Any, List, Optional, Tuple, cast

from ywh2bt.core.api.models.report import (
    CommentLog,
    DetailsUpdateLog,
    Log,
    Report,
    RewardLog,
    StatusUpdateLog,
    TrackerUpdateLog,
    TrackingStatusLog,
)
from ywh2bt.core.api.tracker import TrackerClient, TrackerClientError, TrackerComments, TrackerIssue, TrackerIssueState
from ywh2bt.core.api.yeswehack import YesWeHackApiClient, YesWeHackApiClientError
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.configuration.tracker import Trackers
from ywh2bt.core.configuration.yeswehack import (
    Program,
    Programs,
    SynchronizeOptions,
    YesWeHackConfiguration,
    YesWeHackConfigurations,
)
from ywh2bt.core.mixins.tracker_clients import TrackerClientsMixin
from ywh2bt.core.mixins.yeswehack_api_clients import YesWeHackApiClientsMixin
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


class Synchronizer(YesWeHackApiClientsMixin, TrackerClientsMixin):  # noqa: WPS214
    """A class used for data synchronisation between YesWeHack and trackers."""

    _configuration: RootConfiguration
    _listener: SynchronizerListener
    _message_formatter: _MessageFormatter

    def __init__(
        self,
        configuration: RootConfiguration,
        listener: Optional[SynchronizerListener] = None,
    ):
        """
        Initialize self.

        Args:
            configuration: a configuration
            listener: an observer that will receive synchronization events
        """
        YesWeHackApiClientsMixin.__init__(self)  # noqa: WPS609  # type: ignore
        TrackerClientsMixin.__init__(self)  # noqa: WPS609  # type: ignore
        self._configuration = configuration
        self._listener = listener or NoOpSynchronizerListener()
        self._message_formatter = _MessageFormatter()

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
        yeswehack_client = self.get_yeswehack_api_client(
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
        include_tracked = any(
            (
                synchronize_options.upload_private_comments,
                synchronize_options.upload_public_comments,
                synchronize_options.upload_details_updates,
                synchronize_options.upload_rewards,
                synchronize_options.upload_status_updates,
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
        for bugtracker_name in program.bugtrackers_name:
            self._send_report_to_tracker(
                configuration=configuration,
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
                yeswehack_client=yeswehack_client,
                bugtracker_name=bugtracker_name,
                synchronize_options=cast(SynchronizeOptions, program.synchronize_options),
                report=report,
            )

    def _send_report_to_tracker(  # noqa: WPS210
        self,
        configuration: RootConfiguration,
        yeswehack_name: str,
        yeswehack_configuration: YesWeHackConfiguration,
        yeswehack_client: YesWeHackApiClient,
        bugtracker_name: str,
        synchronize_options: SynchronizeOptions,
        report: Report,
    ) -> None:
        bugtracker_configuration = cast(Trackers, self._configuration.bugtrackers)[bugtracker_name]
        tracker_client = self.get_tracker_client(
            configuration=bugtracker_configuration,
        )
        self._send_event(
            event=SynchronizerStartSendReportEvent(
                configuration=configuration,
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
                program_slug=report.program.slug,
                tracker_name=bugtracker_name,
                report=report,
            ),
        )
        tracker_issue = self._get_tracker_issue_from_logs(
            bugtracker_name=bugtracker_name,
            tracker_client=tracker_client,
            report=report,
        )
        is_existing_issue = tracker_issue is not None
        if not is_existing_issue:
            tracker_issue, _ = self._synchronize_tracker_issue_and_get_logs(
                bugtracker_name=bugtracker_name,
                tracker_client=tracker_client,
                report=report,
            )
        if tracker_issue is None:
            raise SynchronizerError(
                f'Unable to create new issue or get existing issue for #{report.report_id} in {bugtracker_name}',
            )
        if report.tracking_status != 'T' or not is_existing_issue:
            self._update_tracking_status(
                yeswehack_client=yeswehack_client,
                bugtracker_name=bugtracker_name,
                tracker_client=tracker_client,
                report=report,
                tracker_issue=tracker_issue,
            )
        logs = report.logs
        if is_existing_issue:
            last_tracker_update_log = self._get_last_tracker_update_log(
                report=report,
                bugtracker_name=bugtracker_name,
            )
            if last_tracker_update_log:
                logs = report.get_logs_after(
                    log=last_tracker_update_log,
                )
        tracker_comments = self._send_synchronizable_logs(
            bugtracker_name=bugtracker_name,
            tracker_client=tracker_client,
            tracker_issue=tracker_issue,
            synchronize_options=synchronize_options,
            logs=logs,
            report=report,
        )
        if tracker_comments.added_comments:
            yeswehack_client.post_report_tracker_update(
                report=report,
                tracker_name=bugtracker_name,
                issue_id=tracker_issue.issue_id,
                issue_url=tracker_issue.issue_url,
                token=StateEncryptor.encrypt(
                    key=report.report_id,
                    state=TrackerIssueState(
                        closed=False,
                        bugtracker_name=bugtracker_name,
                    ),
                ),
                comment=self._message_formatter.format_synchronization_done_message(
                    tracker_type=tracker_client.tracker_type,
                    report=report,
                    tracker_comments=tracker_comments,
                ),
            )
        self._send_event(
            event=SynchronizerEndSendReportEvent(
                configuration=configuration,
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
                program_slug=report.program.slug,
                tracker_name=bugtracker_name,
                report=report,
                is_existing_issue=is_existing_issue,
                tracking_status_updated=report.tracking_status != 'T' or not is_existing_issue,
                result=tracker_comments,
            ),
        )

    def _get_last_tracker_update_log(
        self,
        bugtracker_name: str,
        report: Report,
    ) -> Optional[Log]:
        for log in reversed(report.logs):
            if isinstance(log, TrackerUpdateLog):
                state = StateDecryptor.decrypt(
                    encrypted_state=log.tracker_token or '',
                    key=report.report_id,
                    state_type=TrackerIssueState,
                )
                if state and state.bugtracker_name == bugtracker_name:
                    return log
        return None

    def _send_synchronizable_logs(
        self,
        bugtracker_name: str,
        tracker_client: TrackerClient[Any],
        tracker_issue: TrackerIssue,
        synchronize_options: SynchronizeOptions,
        logs: List[Log],
        report: Report,
    ) -> TrackerComments:
        synchronizable_logs = []
        for log in logs:
            synchronize = self._is_synchronizable_log(
                synchronize_options=synchronize_options,
                log=log,
            )
            if synchronize:
                synchronizable_logs.append(log)
        if not synchronizable_logs:
            return TrackerComments(
                tracker_issue=tracker_issue,
                added_comments=[],
            )
        return self._send_logs(
            bugtracker_name=bugtracker_name,
            tracker_client=tracker_client,
            tracker_issue=tracker_issue,
            logs=synchronizable_logs,
            report=report,
        )

    def _is_synchronizable_log(
        self,
        synchronize_options: SynchronizeOptions,
        log: Log,
    ) -> bool:
        return any((
            isinstance(log, CommentLog) and synchronize_options.upload_public_comments and not log.private,
            isinstance(log, CommentLog) and synchronize_options.upload_private_comments and log.private,
            isinstance(log, DetailsUpdateLog) and synchronize_options.upload_details_updates,
            isinstance(log, RewardLog) and synchronize_options.upload_rewards,
            isinstance(log, StatusUpdateLog) and synchronize_options.upload_status_updates,
        ))

    def _send_logs(
        self,
        bugtracker_name: str,
        tracker_client: TrackerClient[Any],
        tracker_issue: TrackerIssue,
        logs: List[Log],
        report: Report,
    ) -> TrackerComments:
        try:
            return tracker_client.send_logs(
                tracker_issue=tracker_issue,
                logs=logs,
            )
        except TrackerClientError as send_error:
            raise SynchronizerError(
                f'Unable to send logs for #{report.report_id} to {bugtracker_name}',
            ) from send_error

    def _update_tracking_status(
        self,
        yeswehack_client: YesWeHackApiClient,
        bugtracker_name: str,
        tracker_client: TrackerClient[Any],
        report: Report,
        tracker_issue: TrackerIssue,
    ) -> None:
        message = self._message_formatter.format_tracking_status_update_message(
            tracker_type=tracker_client.tracker_type,
            tracker_issue=tracker_issue,
        )
        try:
            yeswehack_client.put_report_tracking_status(
                report=report,
                status='T',
                tracker_name=bugtracker_name,
                issue_id=tracker_issue.issue_id,
                issue_url=tracker_issue.issue_url,
                comment=message,
            )
        except YesWeHackApiClientError as tracking_status_error:
            raise SynchronizerError(
                f'Unable to update tracking status for report #{report.report_id}',
            ) from tracking_status_error

    def _get_tracker_issue_from_logs(
        self,
        bugtracker_name: str,
        tracker_client: TrackerClient[Any],
        report: Report,
    ) -> Optional[TrackerIssue]:
        log = report.get_last_tracking_status_update_log(
            tracker_name=bugtracker_name,
        )
        if log and isinstance(log, TrackingStatusLog) and all((log.tracker_id, log.tracker_url)):
            return tracker_client.get_tracker_issue(
                issue_id=cast(str, log.tracker_id),
            )
        return None

    def _synchronize_tracker_issue_and_get_logs(
        self,
        bugtracker_name: str,
        tracker_client: TrackerClient[Any],
        report: Report,
    ) -> Tuple[Optional[TrackerIssue], List[Log]]:
        try:
            tracker_issue = tracker_client.send_report(
                report=report,
            )
        except TrackerClientError as send_error:
            raise SynchronizerError(
                f'Unable to send report #{report.report_id} to {bugtracker_name}',
            ) from send_error
        return (
            tracker_issue,
            report.get_comments(),
        )


class _MessageFormatter:
    _tracking_status_update_template: Template = Template(
        'Synchronized with bugtracker : ${tracker_url} on project : ${project}.'
        + '\n'
        + 'Tracked to [${tracker_type} #${issue_id}](${issue_url}).',
    )
    _synchronization_done_template: Template = Template(
        'Synchronized with bugtracker : ${tracker_url} on project : ${project}.'
        + '\n'
        + 'Tracked to [${tracker_type} #${issue_id}](${issue_url}).'
        + '\n'
        + 'Report comments added to issue: ${comment_count}',
    )

    def format_tracking_status_update_message(
        self,
        tracker_type: str,
        tracker_issue: TrackerIssue,
    ) -> str:
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
        tracker_comments: TrackerComments,
    ) -> str:
        tracker_issue = tracker_comments.tracker_issue
        return self._synchronization_done_template.substitute(
            tracker_type=tracker_type,
            tracker_url=tracker_issue.tracker_url,
            project=tracker_issue.project,
            issue_id=tracker_issue.issue_id,
            issue_url=tracker_issue.issue_url,
            comment_count=len(tracker_comments.added_comments),
        )

    def _string_state(
        self,
        is_existing_issue: bool,
        issue_state: TrackerIssueState,
        last_state: Optional[TrackerIssueState],
    ) -> str:
        if is_existing_issue:
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
