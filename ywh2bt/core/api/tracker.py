"""Models and functions used for data synchronisation between YesWeHack and trackers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

from ywh2bt.core.api.client import TestableApiClient
from ywh2bt.core.api.models.report import Log, Report
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.exceptions import CoreException
from ywh2bt.core.state.state import State


class TrackerClientError(CoreException):
    """A base tracker client error."""


@dataclass
class TrackerIssueState(State):
    """A state of an issue."""

    closed: bool = False
    bugtracker_name: Optional[str] = None

    def __eq__(
        self,
        other: Optional[object],
    ) -> bool:
        """
        Indicate if 2 states are the same.

        Args:
            other: a state

        Returns:
            True if the states are the same
        """
        return isinstance(other, TrackerIssueState) and all(
            (
                self.closed == other.closed,
                self.bugtracker_name == other.bugtracker_name,
            ),
        )


@dataclass
class TrackerIssue:
    """Information about a tracker issue."""

    tracker_url: str
    project: str
    issue_id: str
    issue_url: str
    is_closed: bool


@dataclass
class TrackerComment:
    """Information about a tracker comment on an issue."""

    comment_id: str


@dataclass
class TrackerComments:
    """A result of sending comments to a tracker."""

    tracker_issue: TrackerIssue
    added_comments: List[TrackerComment]


T = TypeVar('T', bound=TrackerConfiguration)


class TrackerClient(TestableApiClient, ABC, Generic[T]):
    """An abstract base tracker client."""

    configuration: T

    def __init__(
        self,
        configuration: T,
    ):
        """
        Initialize self.

        Args:
            configuration: a tracker configuration
        """
        self.configuration = configuration

    @property
    @abstractmethod
    def tracker_type(self) -> str:
        """Get the type of the tracker client."""

    @abstractmethod
    def get_tracker_issue(
        self,
        issue_id: str,
    ) -> Optional[TrackerIssue]:
        """
        Get a tracker issue.

        Args:
            issue_id: an issue id
        """

    @abstractmethod
    def send_report(
        self,
        report: Report,
    ) -> TrackerIssue:
        """
        Send a report to the tracker.

        Args:
            report: a report
        """

    @abstractmethod
    def send_logs(
        self,
        tracker_issue: TrackerIssue,
        logs: List[Log],
    ) -> TrackerComments:
        """
        Send logs to the tracker.

        Args:
            tracker_issue: information about the tracker issue
            logs: a list of comments
        """
