"""Models and functions related to GUI synchronizer thread."""
from datetime import datetime
from typing import cast

from PySide2.QtCore import QObject, QThread, Signal, SignalInstance
from singledispatchmethod import singledispatchmethod

from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.error import error_to_string
from ywh2bt.core.exceptions import CoreException
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
from ywh2bt.core.synchronizer.synchronizer import Synchronizer
from ywh2bt.gui.widgets.logs_widget import LogEntry, LogType
from ywh2bt.gui.widgets.root_configuration_entry import RootConfigurationEntry
from ywh2bt.gui.widgets.typing import as_signal_instance


class SynchronizerThread(QThread):
    """A thread for synchronization."""

    synchronization_started: Signal = Signal()
    synchronization_ended: Signal = Signal()

    _entry: RootConfigurationEntry
    _log_entry_available_signal: SignalInstance
    _synchronizer: Synchronizer

    def __init__(
        self,
        parent: QObject,
        entry: RootConfigurationEntry,
        log_entry_available_signal: SignalInstance,
    ):
        """
        Initialize self.

        Args:
            parent: a parent widget
            entry: a root configuration entry
            log_entry_available_signal: a signal that receive events from the thread
        """
        super().__init__(
            parent,
        )
        self._entry = entry
        self._log_entry_available_signal = log_entry_available_signal
        observer = _SynchronizerListener(
            entry=entry,
            log_entry_available_signal=log_entry_available_signal,
        )
        self._synchronizer = Synchronizer(
            configuration=cast(RootConfiguration, entry.configuration),
            listener=observer,
        )

    def run(
        self,
    ) -> None:
        """Run the thread."""
        as_signal_instance(self.synchronization_started).emit()
        try:
            self._synchronizer.synchronize()
        except CoreException as e:
            self._log_entry_available_signal.emit(
                LogEntry(
                    date_time=datetime.now(),
                    context=f'{self._entry.name}',
                    message=error_to_string(
                        error=e,
                    ),
                    log_type=LogType.error,
                ),
            )
        as_signal_instance(self.synchronization_ended).emit()


class _SynchronizerListener(SynchronizerListener):
    _entry: RootConfigurationEntry
    _log_entry_available_signal: SignalInstance

    def __init__(
        self,
        entry: RootConfigurationEntry,
        log_entry_available_signal: SignalInstance,
    ):
        self._entry = entry
        self._log_entry_available_signal = log_entry_available_signal

    def _log_message(
        self,
        message: str,
        log_type: LogType = LogType.standard,
    ) -> None:
        self._log_entry_available_signal.emit(
            LogEntry(
                date_time=datetime.now(),
                context=f'{self._entry.name}',
                message=message,
                log_type=log_type,
            ),
        )

    def on_event(
        self,
        event: SynchronizerEvent,
    ) -> None:
        self._on_event(event)

    @singledispatchmethod
    def _on_event(
        self,
        event: SynchronizerEvent,
    ) -> None:
        self._log_message(
            message=f'Unhandled event {event}',
        )

    @_on_event.register
    def _on_start(
        self,
        event: SynchronizerStartEvent,
    ) -> None:
        self._log_message(
            message='Starting synchronization...',
        )

    @_on_event.register
    def _on_end(
        self,
        event: SynchronizerEndEvent,
    ) -> None:
        self._log_message(
            log_type=LogType.success,
            message='Synchronization done.',
        )

    @_on_event.register
    def _on_start_fetch_reports(
        self,
        event: SynchronizerStartFetchReportsEvent,
    ) -> None:
        yeswehack_name = event.yeswehack_name
        program_slug = event.program_slug
        self._log_message(
            message=f'Processing YesWeHack "{yeswehack_name}"...',
        )
        self._log_message(
            message=f'Fetching reports for program "{program_slug}"...',
        )

    @_on_event.register
    def _on_end_fetch_reports(
        self,
        event: SynchronizerEndFetchReportsEvent,
    ) -> None:
        reports_count = len(event.reports)
        self._log_message(
            log_type=LogType.success,
            message=f'{reports_count} report(s) fetched.',
        )

    @_on_event.register
    def _on_start_send_report(
        self,
        event: SynchronizerStartSendReportEvent,
    ) -> None:
        report = event.report
        report_details = f'#{report.report_id} ({report.title})'
        self._log_message(
            message=f'Processing report {report_details} with "{event.tracker_name}"...',
        )

    @_on_event.register
    def _on_end_send_report(
        self,
        event: SynchronizerEndSendReportEvent,
    ) -> None:
        result = event.result
        if event.is_existing_issue:
            if result.added_comments:
                issue_action = 'updated'
            else:
                issue_action = 'untouched'
        else:
            issue_action = 'added'
        report_details = f'#{event.report.report_id} ({event.report.title})'
        comments_details = f'{len(result.added_comments)} comment(s) added'
        tracking_status_action = 'updated' if event.tracking_status_updated else 'unchanged'
        message = ' | '.join(
            (
                f'{result.tracker_issue.issue_url} ({issue_action} ; {comments_details})',
                f'tracking status {tracking_status_action}',
            ),
        )
        self._log_message(
            log_type=LogType.success,
            message=f'Processed report {report_details} with "{event.tracker_name}": {message}.',
        )
