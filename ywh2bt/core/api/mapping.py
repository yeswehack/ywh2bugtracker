"""Models and functions used for YesWeHack data mapping."""
from dataclasses import dataclass
from typing import Any, Dict, List, Union

from yeswehack.api import (  # noqa: N811
    Attachment as YesWeHackRawApiAttachment,
    Author as YesWeHackRawApiAuthor,
    BugType as YesWeHackRawApiBugType,
    CVSS as YesWeHackRawApiCvss,
    Log as YesWeHackRawApiLog,
    Priority as YesWeHackRawApiPriority,
    Report as YesWeHackRawApiReport,
)

from ywh2bt.core.api.models.report import (  # noqa: WPS235
    Attachment,
    Author,
    BugType,
    CommentLog,
    Cvss,
    CvssUpdateLog,
    DetailsUpdateLog,
    Log,
    Priority,
    PriorityUpdateLog,
    Report,
    ReportProgram,
    RewardLog,
    StatusUpdateLog,
    TrackerMessageLog,
    TrackerUpdateLog,
    TrackingStatusLog,
)
from ywh2bt.core.html import cleanup_ywh_redirects_from_html, cleanup_ywh_redirects_from_text


@dataclass
class MappingContext:
    """A mapping context."""

    yeswehack_domain: str


def map_raw_report(
    context: MappingContext,
    raw_report: YesWeHackRawApiReport,
) -> Report:
    """
    Map a raw API report to a local report.

    Args:
        context: a mapping context
        raw_report: a raw report

    Returns:
        a local report
    """
    attachments = _map_raw_attachments(
        context=context,
        raw_attachments=raw_report.attachments,
    )
    bug_type = _map_raw_bug_type(
        context=context,
        raw_bug_type=raw_report.bug_type,
    )
    cvss = _map_raw_cvss(
        context=context,
        raw_cvss=raw_report.cvss,
    )
    priority = _map_raw_priority(
        context=context,
        raw_priority=raw_report.priority,
    ) if raw_report.priority else None
    hunter = _map_raw_author(
        context=context,
        raw_author=raw_report.hunter,
    )
    status = _map_raw_status(
        context=context,
        raw_status=raw_report.status,
    )
    logs = map_raw_logs(
        context=context,
        raw_logs=raw_report.logs or [],
    )
    return Report(
        raw_report=raw_report,
        report_id=str(raw_report.id),
        title=raw_report.title,
        local_id=raw_report.local_id,
        bug_type=bug_type,
        scope=raw_report.scope,
        cvss=cvss,
        end_point=raw_report.end_point,
        vulnerable_part=raw_report.vulnerable_part,
        part_name=raw_report.part_name,
        payload_sample=raw_report.payload_sample,
        technical_environment=raw_report.technical_environment,
        description_html=cleanup_ywh_redirects_from_html(
            ywh_domain=context.yeswehack_domain,
            html=raw_report.description_html,
        ),
        attachments=attachments,
        hunter=hunter,
        status=status,
        tracking_status=raw_report.tracking_status,
        logs=logs,
        priority=priority,
        program=_map_raw_report_program(
            context=context,
            raw_program=raw_report.program or {},
        ),
    )


def _map_raw_bug_type(
    context: MappingContext,
    raw_bug_type: YesWeHackRawApiBugType,
) -> BugType:
    return BugType(
        name=raw_bug_type.name,
        link=raw_bug_type.link,
        remediation_link=raw_bug_type.remediation_link,
    )


def _map_raw_priority(
    context: MappingContext,
    raw_priority: YesWeHackRawApiPriority,
) -> Priority:
    return Priority(
        name=raw_priority.name,
    )


def _map_raw_report_program(
    context: MappingContext,
    raw_program: Dict[Any, Any],
) -> ReportProgram:
    return ReportProgram(
        title=raw_program.get('title', ''),
        slug=raw_program.get('slug', ''),
    )


def _map_raw_cvss(
    context: MappingContext,
    raw_cvss: YesWeHackRawApiCvss,
) -> Cvss:
    return Cvss(
        criticity=raw_cvss.criticity,
        score=raw_cvss.score,
        vector=raw_cvss.vector,
    )


def _map_raw_attachments(
    context: MappingContext,
    raw_attachments: List[YesWeHackRawApiAttachment],
) -> List[Attachment]:
    return [
        map_raw_attachment(
            context=context,
            raw_attachment=raw_attachment,
        )
        for raw_attachment in raw_attachments
    ]


def map_raw_attachment(
    context: MappingContext,
    raw_attachment: YesWeHackRawApiAttachment,
) -> Attachment:
    """
    Map a raw API attachment to a local attachment.

    Args:
        context: a mapping context
        raw_attachment: a raw attachment

    Returns:
        a local attachment
    """
    return Attachment(
        attachment_id=raw_attachment.id,
        name=raw_attachment.name,
        original_name=raw_attachment.original_name,
        mime_type=raw_attachment.mime_type,
        size=raw_attachment.size,
        url=raw_attachment.url,
        data_loader=lambda: raw_attachment.data,
    )


def _map_raw_author(
    context: MappingContext,
    raw_author: Union[YesWeHackRawApiAuthor, Dict[str, Any]],
) -> Author:
    default_username = 'Anonymous'
    if isinstance(raw_author, YesWeHackRawApiAuthor):
        username = raw_author.username or default_username
    else:
        username = raw_author.get('username', default_username)
    return Author(
        username=username,
    )


def _map_raw_status(
    context: MappingContext,
    raw_status: Dict[str, Any],
) -> str:
    return raw_status.get('workflow_state', '')


def map_raw_logs(
    context: MappingContext,
    raw_logs: List[YesWeHackRawApiLog],
) -> List[Log]:
    """
    Map a list of raw API logs to a list of local logs.

    Args:
        context: a mapping context
        raw_logs: a list of raw logs

    Returns:
        a list of local logs
    """
    return [
        map_raw_log(
            context=context,
            raw_log=raw_log,
        )
        for raw_log in raw_logs
    ]


def map_raw_log(  # noqa: WPS210,WPS212,WPS231
    context: MappingContext,
    raw_log: YesWeHackRawApiLog,
) -> Log:
    """
    Map a raw API log to a local log.

    Args:
        context: a mapping context
        raw_log: a raw log

    Returns:
        a local log
    """
    created_at = raw_log.created_at
    log_id = raw_log.id
    log_type = raw_log.type
    private = raw_log.private
    author = _map_raw_author(
        context=context,
        raw_author=raw_log.author,
    ) if raw_log.author else Author(
        username='Anonymous',
    )
    message_html = cleanup_ywh_redirects_from_html(
        ywh_domain=context.yeswehack_domain,
        html=raw_log.message_html or '',
    )
    attachments = _map_raw_attachments(
        context=context,
        raw_attachments=raw_log.attachments,
    )
    if raw_log.type == 'comment':
        return CommentLog(
            created_at=created_at,
            log_id=log_id,
            log_type=log_type,
            private=private,
            author=author,
            message_html=message_html,
            attachments=attachments,
        )
    if raw_log.type == 'cvss-update':
        return CvssUpdateLog(
            created_at=created_at,
            log_id=log_id,
            log_type=log_type,
            private=private,
            author=author,
            message_html=message_html,
            attachments=attachments,
            old_cvss=_map_raw_cvss(
                context=context,
                raw_cvss=raw_log.old_cvss,
            ),
            new_cvss=_map_raw_cvss(
                context=context,
                raw_cvss=raw_log.new_cvss,
            ),
        )
    if raw_log.type == 'details-update':
        return DetailsUpdateLog(
            created_at=created_at,
            log_id=log_id,
            log_type=log_type,
            private=private,
            author=author,
            message_html=message_html,
            attachments=attachments,
            old_details=raw_log.old_details,
            new_details=raw_log.new_details,
        )
    if raw_log.type == 'priority-update':
        return PriorityUpdateLog(
            created_at=created_at,
            log_id=log_id,
            log_type=log_type,
            private=private,
            author=author,
            message_html=message_html,
            attachments=attachments,
            new_priority=_map_raw_priority(
                context=context,
                raw_priority=raw_log.priority,
            ) if raw_log.priority else None,
        )
    if raw_log.type == 'reward':
        return RewardLog(
            created_at=created_at,
            log_id=log_id,
            log_type=log_type,
            private=private,
            author=author,
            message_html=message_html,
            attachments=attachments,
            reward_type=raw_log.reward_type,
        )
    if raw_log.type == 'status-update':
        return StatusUpdateLog(
            created_at=created_at,
            log_id=log_id,
            log_type=log_type,
            private=private,
            author=author,
            message_html=message_html,
            attachments=attachments,
            old_status=raw_log.old_status,
            new_status=raw_log.status,
        )
    if raw_log.type == 'tracking-status':
        return TrackingStatusLog(
            created_at=created_at,
            log_id=log_id,
            log_type=log_type,
            private=private,
            author=author,
            message_html=message_html,
            attachments=attachments,
            tracker_name=raw_log.tracker_name,
            tracker_url=cleanup_ywh_redirects_from_text(
                ywh_domain=context.yeswehack_domain,
                text=raw_log.tracker_url,
            ) if raw_log.tracker_url else None,
            tracker_id=raw_log.tracker_id,
        )
    if raw_log.type == 'tracker-update':
        return TrackerUpdateLog(
            created_at=created_at,
            log_id=log_id,
            log_type=log_type,
            private=private,
            author=author,
            message_html=message_html,
            attachments=attachments,
            tracker_name=raw_log.tracker_name,
            tracker_url=cleanup_ywh_redirects_from_text(
                ywh_domain=context.yeswehack_domain,
                text=raw_log.tracker_url,
            ) if raw_log.tracker_url else None,
            tracker_id=raw_log.tracker_id,
            tracker_token=raw_log.tracker_token,
        )
    if raw_log.type == 'tracker-message':
        return TrackerMessageLog(
            created_at=created_at,
            log_id=log_id,
            log_type=log_type,
            private=private,
            author=author,
            message_html=message_html,
            attachments=attachments,
            tracker_name=raw_log.tracker_name,
            tracker_url=cleanup_ywh_redirects_from_text(
                ywh_domain=context.yeswehack_domain,
                text=raw_log.tracker_url,
            ) if raw_log.tracker_url else None,
            tracker_id=raw_log.tracker_id,
        )
    return Log(
        created_at=created_at,
        log_id=log_id,
        log_type=log_type,
        private=private,
        author=author,
        message_html=message_html,
        attachments=attachments,
    )
