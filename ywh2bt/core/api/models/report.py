"""Models for reports."""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
)

from typing_extensions import Protocol
from yeswehack.api import Report as YesWeHackRawApiReport

REPORT_PROPERTY_LABELS = MappingProxyType({
    'bug_type': 'Bug type',
    'scope': 'Scope',
    'end_point': 'Endpoint',
    'vulnerable_part': 'Vulnerable part',
    'part_name': 'Part name',
    'payload_sample': 'Payload',
    'application_finger_print': 'Application fingerprint',
})
REPORT_STATUS_TRANSLATIONS = MappingProxyType({
    'new': 'New',
    'under_review': 'Under Review',
    'reopen_under_review': 'Reopen Under Review',
    'more_info': 'Need More Info',
    'reopen_more_info': 'Reopen Need More Info',
    'accepted': 'Accepted',
    'ask_verif': 'Ask for fix verification',
    'wont_fix': "Won't fix",
    'informative': 'Informative',
    'resolved': 'Resolved',
    'rtfs': 'RTFS',
    'spam': 'Spam',
    'out_of_scope': 'Out Of Scope',
    'not_applicable': 'Not Applicable',
    'invalid': 'Invalid',
    'duplicate': 'Duplicate',
    'auto_close': 'Auto Close',
})


@dataclass
class Report:
    """A report."""

    raw_report: YesWeHackRawApiReport
    report_id: str
    title: str
    local_id: str
    bug_type: BugType
    scope: str
    cvss: Cvss
    end_point: str
    vulnerable_part: str
    part_name: str
    payload_sample: str
    technical_environment: str
    description_html: str
    attachments: List[Attachment]
    hunter: Author
    logs: List[Log]
    status: str
    tracking_status: str
    program: ReportProgram
    priority: Optional[Priority] = None

    def get_last_tracking_status_update_log(
        self,
        tracker_name: str,
    ) -> Optional[Log]:
        """
        Get the log for the last tracking status update of a tracker, if any.

        Args:
            tracker_name: a tracker name

        Returns:
            a log
        """
        tracking_status_logs = list(filter(
            _all_log_filter(
                partial(
                    _log_type_equals,
                    log_type='tracking-status',
                ),
                partial(
                    _log_tracker_name_equals,
                    tracker_name=tracker_name,
                ),
                _not_log_filter(
                    partial(
                        _log_tracker_id_equals,
                        tracker_id=None,
                    ),
                ),
            ),
            self.logs,
        ))
        if tracking_status_logs:
            return tracking_status_logs[-1]
        return None

    def get_logs_after(
        self,
        log: Log,
    ) -> List[Log]:
        """
        Get all the logs that occurred after the given log.

        Args:
            log: a log

        Returns:
            the logs that occurred after the given log
        """
        log_index = self.logs.index(log)
        return self.logs[log_index + 1:]

    def get_comments_after(
        self,
        log: Log,
    ) -> List[Log]:
        """
        Get all the comments that occurred after the given log.

        Args:
            log: a log

        Returns:
            the comments that occurred after the given log
        """
        return list(filter(
            _log_is_public_comment,
            self.get_logs_after(
                log=log,
            ),
        ))

    def get_comments(
        self,
    ) -> List[Log]:
        """
        Get all the comments.

        Returns:
            the comments
        """
        return list(filter(
            _log_is_public_comment,
            self.logs,
        ))


@dataclass
class Attachment:
    """An attachment."""

    attachment_id: int
    name: str
    original_name: str
    mime_type: str
    size: int
    url: str
    data_loader: Callable[[], bytes]

    @property
    def data(self) -> bytes:
        """
        Get the data from the attachment.

        Returns:
            the data
        """
        return self.data_loader()  # type: ignore


@dataclass
class Priority:
    """A priority."""

    name: str = ''


@dataclass
class ReportProgram:
    """Program details from a report."""

    title: str = ''
    slug: str = ''


@dataclass
class BugType:
    """A bug type."""

    name: str
    link: str
    remediation_link: str


@dataclass
class Cvss:
    """A CVSS."""

    criticity: str
    score: float
    vector: str


@dataclass
class Author:
    """An author."""

    username: str


@dataclass
class Log:
    """A log."""

    created_at: str
    log_id: int
    log_type: str
    private: bool
    author: Author
    message_html: str
    attachments: List[Attachment]


@dataclass
class CommentLog(Log):
    """A comment log."""


@dataclass
class CvssUpdateLog(Log):
    """A cvss-update log."""

    old_cvss: Cvss
    new_cvss: Cvss


@dataclass
class DetailsUpdateLog(Log):
    """A details-update log."""

    old_details: Optional[Dict[str, Any]]
    new_details: Optional[Dict[str, Any]]


@dataclass
class PriorityUpdateLog(Log):
    """A priority-update log."""

    new_priority: Optional[Priority]


@dataclass
class RewardLog(Log):
    """A reward log."""

    reward_type: str


@dataclass
class StatusUpdateLog(Log):
    """A status-update log."""

    old_status: Optional[Dict[str, Any]]
    new_status: Optional[Dict[str, Any]]


@dataclass
class TrackingStatusLog(Log):
    """A tracking-status log."""

    tracker_name: Optional[str]
    tracker_url: Optional[str]
    tracker_id: Optional[str]


@dataclass
class TrackerUpdateLog(Log):
    """A tracker-update log."""

    tracker_name: Optional[str]
    tracker_url: Optional[str]
    tracker_id: Optional[str]
    tracker_token: Optional[str]


@dataclass
class TrackerMessageLog(Log):
    """A tracker-message log."""

    tracker_name: Optional[str]
    tracker_url: Optional[str]
    tracker_id: Optional[str]


class _LogFilterProtocol(Protocol):

    def __call__(
        self,
        log: Log,
    ) -> bool:
        ...  # noqa: WPS428


def _apply_log_filter(
    log: Log,
    filter_fn: _LogFilterProtocol,
) -> bool:
    return filter_fn(
        log=log,
    )


def _all_log_filter(
    *filters: _LogFilterProtocol,
) -> _LogFilterProtocol:
    def fn(  # noqa: WPS430
        log: Log,
    ) -> bool:
        return all(
            map(
                partial(
                    _apply_log_filter,
                    log,
                ),
                filters,
            ),
        )

    return fn


def _not_log_filter(
    filter_fn: _LogFilterProtocol,
) -> _LogFilterProtocol:
    def fn(  # noqa: WPS430
        log: Log,
    ) -> bool:
        return not _apply_log_filter(
            log=log,
            filter_fn=filter_fn,
        )

    return fn


def _log_type_equals(
    log_type: str,
    log: Log,
) -> bool:
    return log.log_type == log_type


def _log_private_equals(
    private: bool,
    log: Log,
) -> bool:
    return log.private == private


def _log_tracker_name_equals(
    tracker_name: Optional[str],
    log: TrackingStatusLog,
) -> bool:
    return log.tracker_name == tracker_name


def _log_tracker_id_equals(
    tracker_id: Optional[str],
    log: TrackingStatusLog,
) -> bool:
    return log.tracker_id == tracker_id


_log_is_comment = partial(
    _log_type_equals,
    log_type='comment',
)
_log_is_public = partial(
    _log_private_equals,
    private=False,
)
_log_is_public_comment = _all_log_filter(
    _log_is_comment,
    _log_is_public,
)
