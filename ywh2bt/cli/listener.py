"""Models and functions used for observing synchronisation between YesWeHack and trackers from the CLI."""
import sys
from datetime import datetime

from singledispatchmethod import singledispatchmethod

from ywh2bt.core.api.models.report import REPORT_STATUS_TRANSLATIONS
from ywh2bt.core.core import write_message
from ywh2bt.core.synchronizer.listener import (
    SynchronizerEndEvent,
    SynchronizerEndFetchReportsEvent,
    SynchronizerEndSendReportEvent,
    SynchronizerEvent,
    SynchronizerListener,
    SynchronizerStartEvent,
    SynchronizerStartFetchReportsEvent,
    SynchronizerStartSendReportEvent,
)
from ywh2bt.core.tester.listener import (
    TesterEndEvent,
    TesterEndTrackerEvent,
    TesterEndYesWeHackEvent,
    TesterEvent,
    TesterListener,
    TesterStartEvent,
    TesterStartTrackerEvent,
    TesterStartYesWeHackEvent,
)


def _print(
    message: str,
    end: str = '\n',
) -> None:
    write_message(
        stream=sys.stdout,
        message=message,
        end=end,
    )


def _print_timestamped(
    message: str,
    end: str = '\n',
) -> None:
    now = datetime.now()
    formatted_now = now.strftime('%Y-%m-%d %H:%M:%S.%f')  # noqa: WPS323
    _print(
        message=f'[{formatted_now}] {message}',
        end=end,
    )


class CliSynchronizerListener(SynchronizerListener):
    """A listener that print details about the event on the standard output stream."""

    def on_event(
        self,
        event: SynchronizerEvent,
    ) -> None:
        """
        Receive an event.

        Args:
            event: an event
        """
        self._on_event(event)

    @singledispatchmethod
    def _on_event(
        self,
        event: SynchronizerEvent,
    ) -> None:
        listener_name = self.__class__.__name__
        event_name = event.__class__.__name__
        _print(
            message=f'{listener_name}: Unhandled event {event_name}',
        )

    @_on_event.register
    def _on_start(
        self,
        event: SynchronizerStartEvent,
    ) -> None:
        _print_timestamped(
            message='Starting synchronization:',
        )

    @_on_event.register
    def _on_end(
        self,
        event: SynchronizerEndEvent,
    ) -> None:
        _print_timestamped(
            message='Synchronization done.',
        )

    @_on_event.register
    def _on_start_fetch_reports(
        self,
        event: SynchronizerStartFetchReportsEvent,
    ) -> None:
        yeswehack_name = event.yeswehack_name
        program_slug = event.program_slug
        _print_timestamped(
            message=f'  Processing YesWeHack "{yeswehack_name}": ',
        )
        _print_timestamped(
            message=f'    Fetching reports for program "{program_slug}": ',
            end='',
        )

    @_on_event.register
    def _on_end_fetch_reports(
        self,
        event: SynchronizerEndFetchReportsEvent,
    ) -> None:
        reports_count = len(event.reports)
        _print(
            message=f'{reports_count} report(s)',
        )

    @_on_event.register
    def _on_start_send_report(
        self,
        event: SynchronizerStartSendReportEvent,
    ) -> None:
        tracker_name = event.tracker_name
        report = event.report
        title_max_len = 32
        title = report.title[:title_max_len] + (report.title[title_max_len:] and '...')
        report_details = f'#{report.report_id} ({title})'
        _print_timestamped(
            message=f'    Processing report {report_details} with "{tracker_name}": ',
            end='',
        )

    @_on_event.register
    def _on_end_send_report(
        self,
        event: SynchronizerEndSendReportEvent,
    ) -> None:
        tracker_issue = event.tracker_issue
        issue_added_comment_count = len(event.issue_added_comments)
        if not tracker_issue or not event.is_existing_issue:
            issue_details = [
                'does not exist anymore',
            ]
        else:
            issue_details = [
                tracker_issue.issue_url,
            ]
            if event.is_created_issue:
                if issue_added_comment_count:
                    issue_details.append('updated')
            else:
                issue_details.append('added')
            if issue_added_comment_count:
                issue_details.append(f'{issue_added_comment_count} comment(s) added')
        report_added_comment_count = len(event.report_added_comments)
        report_details = []
        if report_added_comment_count:
            report_details.append(f'{report_added_comment_count} comment(s) added')
        report_details.append(f'tracking status {"updated" if event.tracking_status_updated else "unchanged"}')
        if event.new_report_status:
            old_status, new_status = event.new_report_status
            old_status_translation = REPORT_STATUS_TRANSLATIONS.get(old_status, 'Unknown')
            new_status_translation = REPORT_STATUS_TRANSLATIONS.get(new_status, 'Unknown')
            report_details.append(f'status "{old_status_translation}" -> "{new_status_translation}"')
        _print(
            message=' | '.join(
                (
                    f'issue => {" ; ".join(issue_details)}',
                    f'report => {" ; ".join(report_details)}',
                ),
            ),
        )


class CliTesterListener(TesterListener):
    """A listener that print details about the event on the standard output stream."""

    def on_event(
        self,
        event: TesterEvent,
    ) -> None:
        """
        Receive an event.

        Args:
            event: an event
        """
        self._on_event(event)

    @singledispatchmethod
    def _on_event(
        self,
        event: TesterEvent,
    ) -> None:
        listener_name = self.__class__.__name__
        event_name = event.__class__.__name__
        _print(
            message=f'{listener_name}: Unhandled event {event_name}',
        )

    @_on_event.register
    def _on_start(
        self,
        event: TesterStartEvent,
    ) -> None:
        _print_timestamped(
            message='Starting test:',
        )

    @_on_event.register
    def _on_end(
        self,
        event: TesterEndEvent,
    ) -> None:
        _print_timestamped(
            message='Test done.',
        )

    @_on_event.register
    def _on_start_test_yeswehack(
        self,
        event: TesterStartYesWeHackEvent,
    ) -> None:
        yeswehack_name = event.yeswehack_name
        _print_timestamped(
            message=f'  YesWeHack {yeswehack_name}: ',
            end='',
        )

    @_on_event.register
    def _on_end_test_yeswehack(
        self,
        event: TesterEndYesWeHackEvent,
    ) -> None:
        _print(
            message='OK',
        )

    @_on_event.register
    def _on_start_test_tracker(
        self,
        event: TesterStartTrackerEvent,
    ) -> None:
        tracker_name = event.tracker_name
        _print_timestamped(
            message=f'  Tracker {tracker_name}: ',
            end='',
        )

    @_on_event.register
    def _on_end_test_tracker(
        self,
        event: TesterEndTrackerEvent,
    ) -> None:
        _print(
            message='OK',
        )
