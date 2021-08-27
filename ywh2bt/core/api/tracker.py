"""Models and functions used for data synchronisation between YesWeHack and trackers."""
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
)

from ywh2bt.core.api.client import TestableApiClient
from ywh2bt.core.api.models.report import (
    Log,
    Report,
)
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.exceptions import CoreException
from ywh2bt.core.state.state import State


class TrackerClientError(CoreException):
    """A base tracker client error."""


class TrackerIssueState(State):
    """A state of an issue."""

    _changed: bool = False

    _closed: bool = False
    _bugtracker_name: Optional[str] = None
    _downloaded_comments: Optional[List[str]] = None

    def __init__(
        self,
        closed: bool = False,
        bugtracker_name: Optional[str] = None,
        downloaded_comments: Optional[List[str]] = None,
    ):
        """
        Initialize self.

        Args:
            closed: a flag indicating the closed status of the tracker issue to which this state belongs
            bugtracker_name: a bug tracker name of the tracker issue to which this state belongs
            downloaded_comments:
            a list of comment ids that have been downloaded (from the bug tracker to yeswehack platform)
        """
        self._closed = closed
        self._bugtracker_name = bugtracker_name
        self._downloaded_comments = downloaded_comments

    def as_dict(self) -> Dict[str, Any]:
        """
        Get the fields as a new dict.

        Returns:
            the fields as a new dict
        """
        return {
            'closed': self._closed,
            'bugtracker_name': self._bugtracker_name,
            'downloaded_comments': list(set(self._downloaded_comments)) if self._downloaded_comments else None,
        }

    @property
    def changed(self) -> bool:
        """
        Indicate if the underlying values of the state have changed.

        Returns:
            True if the underlying values of the state have changed
        """
        return self._changed

    @property
    def closed(self) -> bool:
        """
        Indicate the closed status of the tracker issue to which this state belongs.

        Returns:
            True if the tracker issue is closed
        """
        return self._closed

    @closed.setter
    def closed(
        self,
        closed: bool,
    ) -> None:
        """
        Set the closed status of the tracker issue to which this state belongs.

        Args:
            closed: True if the tracker issue is closed
        """
        if self._closed == closed:
            return
        self._changed = True
        self._closed = closed

    @property
    def bugtracker_name(self) -> Optional[str]:
        """
        Get the bug tracker name of the tracker issue to which this state belongs.

        Returns:
            the bug tracker name
        """
        return self._bugtracker_name

    @bugtracker_name.setter
    def bugtracker_name(
        self,
        bugtracker_name: str,
    ) -> None:
        """
        Set the bug tracker name of the tracker issue to which this state belongs.

        Args:
            bugtracker_name: the bug tracker name
        """
        if self._bugtracker_name == bugtracker_name:
            return
        self._changed = True
        self._bugtracker_name = bugtracker_name

    @property
    def downloaded_comments(self) -> Optional[List[str]]:
        """
        Get the list of comment ids that have been downloaded (from the bug tracker to yeswehack platform).

        Returns:
            the list of comment ids
        """
        return self._downloaded_comments

    @downloaded_comments.setter
    def downloaded_comments(
        self,
        downloaded_comments: Optional[List[str]],
    ) -> None:
        """
        Set the list of comment ids that have been downloaded (from the bug tracker to yeswehack platform).

        Args:
            downloaded_comments: the list of comment ids
        """
        if self._downloaded_comments == downloaded_comments:
            return
        self._changed = True
        self._downloaded_comments = downloaded_comments

    def add_downloaded_comment(
        self,
        comment_id: str,
    ) -> None:
        """
        Add a downloaded comment to the state.

        Args:
            comment_id: a comment id
        """
        if not self.downloaded_comments:
            self.downloaded_comments = []
        self.downloaded_comments.append(comment_id)

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
                self._closed == other.closed,
                self._bugtracker_name == other.bugtracker_name,
                self._downloaded_comments == other.downloaded_comments,
            ),
        )


@dataclass
class TrackerIssue:
    """Information about a tracker issue."""

    tracker_url: str
    project: str
    issue_id: str
    issue_url: str
    closed: bool


@dataclass
class TrackerIssueComment:
    """Information about a tracker comment on an issue."""

    attachments: Dict[str, TrackerAttachment]
    author: str
    comment_id: str
    created_at: datetime
    body: str


TrackerIssueComments = List[TrackerIssueComment]


@dataclass
class TrackerAttachment:
    """Attachment on a tracker issue or comment."""

    filename: str
    mime_type: str
    content: bytes


@dataclass
class SendLogsResult:
    """A result of sending logs to a tracker."""

    tracker_issue: Optional[TrackerIssue]
    added_comments: TrackerIssueComments


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
    def get_tracker_issue_comments(
        self,
        issue_id: str,
        exclude_comments: Optional[List[str]] = None,
    ) -> TrackerIssueComments:
        """
        Get a list of comments on an issue.

        Args:
            issue_id: an issue id
            exclude_comments: an optional list of comment to exclude
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
    ) -> SendLogsResult:
        """
        Send logs to the tracker.

        Args:
            tracker_issue: information about the tracker issue
            logs: a list of comments
        """
