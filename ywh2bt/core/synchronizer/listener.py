"""Models and functions used for observing synchronisation between YesWeHack and trackers."""
from abc import ABC
from dataclasses import dataclass
from typing import (
    List,
    Optional,
    Tuple,
)

from ywh2bt.core.api.models.report import Report
from ywh2bt.core.api.tracker import TrackerIssue
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.configuration.yeswehack import YesWeHackConfiguration
from ywh2bt.core.listener import (
    Event,
    Listener,
)


@dataclass
class SynchronizerEvent(Event, ABC):
    """A base event sent by a Synchronizer."""


@dataclass
class SynchronizerStartEvent(SynchronizerEvent):
    """An event sent when a synchronization starts."""

    configuration: RootConfiguration


@dataclass
class SynchronizerEndEvent(SynchronizerEvent):
    """An event sent when a synchronization ends."""

    configuration: RootConfiguration


@dataclass
class SynchronizerStartFetchReportsEvent(SynchronizerEvent):
    """An event sent when fetching of reports starts."""

    configuration: RootConfiguration
    yeswehack_name: str
    yeswehack_configuration: YesWeHackConfiguration
    program_slug: str


@dataclass
class SynchronizerEndFetchReportsEvent(SynchronizerEvent):
    """An event sent when fetching of reports ends."""

    configuration: RootConfiguration
    yeswehack_name: str
    yeswehack_configuration: YesWeHackConfiguration
    program_slug: str
    reports: List[Report]


@dataclass
class SynchronizerStartSendReportEvent(SynchronizerEvent):
    """An event sent when a synchronization of a report starts."""

    configuration: RootConfiguration
    yeswehack_name: str
    yeswehack_configuration: YesWeHackConfiguration
    program_slug: str
    tracker_name: str
    report: Report


@dataclass
class SynchronizerEndSendReportEvent(SynchronizerEvent):
    """An event sent when a synchronization of a report ends."""

    configuration: RootConfiguration
    yeswehack_name: str
    yeswehack_configuration: YesWeHackConfiguration
    program_slug: str
    tracker_name: str
    report: Report
    is_created_issue: bool
    is_existing_issue: bool
    new_report_status: Optional[Tuple[str, str]]
    tracking_status_updated: bool
    tracker_issue: Optional[TrackerIssue]
    issue_added_comments: List[str]
    report_added_comments: List[str]


class SynchronizerListener(Listener[SynchronizerEvent], ABC):
    """A listener receiving events from a Synchronizer."""


class NoOpSynchronizerListener(SynchronizerListener):
    """A listener receiving events from a Synchronizer and doing nothing."""

    def on_event(
        self,
        event: SynchronizerEvent,
    ) -> None:
        """
        Receive an event and do nothing.

        Args:
            event: an event
        """
