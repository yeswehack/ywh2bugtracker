"""Models and functions related to GUI tester thread."""
from datetime import datetime
from typing import cast

from PySide2.QtCore import (
    QObject,
    QThread,
    Signal,
    SignalInstance,
)
from singledispatchmethod import singledispatchmethod

from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.error import error_to_string
from ywh2bt.core.exceptions import CoreException
from ywh2bt.core.factories.tracker_clients import TrackerClientsFactory
from ywh2bt.core.factories.yeswehack_api_clients import YesWeHackApiClientsFactory
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
from ywh2bt.core.tester.tester import Tester
from ywh2bt.gui.widgets.logs_widget import (
    LogEntry,
    LogType,
)
from ywh2bt.gui.widgets.root_configuration_entry import RootConfigurationEntry
from ywh2bt.gui.widgets.typing import as_signal_instance


class TesterThread(QThread):
    """A thread for testing configuration."""

    test_started: Signal = Signal()
    test_ended: Signal = Signal()

    _entry: RootConfigurationEntry
    _log_entry_available_signal: SignalInstance
    _tester: Tester

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
        observer = _TesterListener(
            entry=entry,
            log_entry_available_signal=log_entry_available_signal,
        )
        self._tester = Tester(
            configuration=cast(RootConfiguration, entry.configuration),
            yes_we_hack_api_clients_factory=YesWeHackApiClientsFactory(),
            tracker_clients_factory=TrackerClientsFactory(),
            listener=observer,
        )

    def run(
        self,
    ) -> None:
        """Run the thread."""
        as_signal_instance(self.test_started).emit()
        try:
            self._tester.test()
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
        as_signal_instance(self.test_ended).emit()


class _TesterListener(TesterListener):
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
        event: TesterEvent,
    ) -> None:
        self._on_event(event)

    @singledispatchmethod
    def _on_event(
        self,
        event: TesterEvent,
    ) -> None:
        self._log_message(
            message=f'Unhandled event {event}',
        )

    @_on_event.register
    def _on_start(
        self,
        event: TesterStartEvent,
    ) -> None:
        self._log_message(
            message='Starting test',
        )

    @_on_event.register
    def _on_end(
        self,
        event: TesterEndEvent,
    ) -> None:
        self._log_message(
            log_type=LogType.success,
            message='Test done',
        )

    @_on_event.register
    def _on_start_test_yeswehack(
        self,
        event: TesterStartYesWeHackEvent,
    ) -> None:
        self._log_message(
            message=f'Testing YesWeHack {event.yeswehack_name}',
        )

    @_on_event.register
    def _on_end_test_yeswehack(
        self,
        event: TesterEndYesWeHackEvent,
    ) -> None:
        self._log_message(
            log_type=LogType.success,
            message=f'YesWeHack {event.yeswehack_name}: OK',
        )

    @_on_event.register
    def _on_start_test_tracker(
        self,
        event: TesterStartTrackerEvent,
    ) -> None:
        self._log_message(
            message=f'Testing tracker {event.tracker_name}',
        )

    @_on_event.register
    def _on_end_test_tracker(
        self,
        event: TesterEndTrackerEvent,
    ) -> None:
        self._log_message(
            log_type=LogType.success,
            message=f'Tracker {event.tracker_name}: OK',
        )
