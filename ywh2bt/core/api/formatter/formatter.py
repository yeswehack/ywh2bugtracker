"""Models and functions used for formatting reports data."""

from abc import ABC, abstractmethod
from string import Template
from types import MappingProxyType
from typing import Optional

from singledispatchmethod import singledispatchmethod
from typing_extensions import Protocol

from ywh2bt.core.api.models.report import CommentLog, DetailsUpdateLog, Log, Report, RewardLog, StatusUpdateLog

PROPERTY_LABELS = MappingProxyType({
    'bug_type': 'Bug type',
    'scope': 'Scope',
    'end_point': 'Endpoint',
    'vulnerable_part': 'Vulnerable part',
    'part_name': 'Part name',
    'payload_sample': 'Payload',
    'application_finger_print': 'Application fingerprint',
})

STATUS_TRANSLATIONS = MappingProxyType({
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


class _ValueTransformer(Protocol):
    def __call__(
        self,
        value: str,
    ) -> str:
        ...  # noqa: WPS428


def _identity_transformer(
    value: str,
) -> str:
    return value


class ReportMessageFormatter(ABC):
    """A base report formatter."""

    _report_title_template: Template
    _report_description_template: Template
    _comment_body_template: Template
    _comment_log_template: Template
    _status_update_log_template: Template
    _details_update_log_template: Template
    _details_update_log_line_template: Template
    _reward_log_template: Template
    _value_transformer: _ValueTransformer

    def __init__(
        self,
        report_title_template: Template,
        report_description_template: Template,
        comment_body_template: Template,
        comment_log_template: Template,
        status_update_log_template: Template,
        details_update_log_template: Template,
        details_update_log_line_template: Template,
        reward_log_template: Template,
        value_transformer: Optional[_ValueTransformer] = None,
    ):
        """
        Initialize self.

        Args:
            report_title_template: a template for a report title
            report_description_template: a template for a report description
            comment_body_template: a template for an issue comment
            comment_log_template: a template for a template for a CommentLog
            status_update_log_template: a template for a StatusUpdateLog
            details_update_log_template: a template for a DetailsUpdateLog
            details_update_log_line_template: a template for entries of a DetailsUpdateLog
            reward_log_template: a template for a RewardLog
            value_transformer: a transformer for values
        """
        self._report_title_template = report_title_template
        self._report_description_template = report_description_template
        self._comment_body_template = comment_body_template
        self._comment_log_template = comment_log_template
        self._status_update_log_template = status_update_log_template
        self._details_update_log_template = details_update_log_template
        self._details_update_log_line_template = details_update_log_line_template
        self._reward_log_template = reward_log_template
        self._value_transformer = value_transformer or _identity_transformer

    def _transform_value(
        self,
        value: str,
    ) -> str:
        return self._value_transformer(
            value=value,
        )

    def format_report_title(
        self,
        report: Report,
    ) -> str:
        """
        Get a formatted title for a report.

        Args:
            report: a report

        Returns:
            a formatted title
        """
        return self._report_title_template.substitute(
            local_id=report.local_id,
            title=self._transform_value(
                value=report.title or '',
            ),
        )

    def format_report_description(
        self,
        report: Report,
    ) -> str:
        """
        Get a formatted description for a report.

        Args:
            report: a report

        Returns:
            a formatted description
        """
        return self._report_description_template.substitute(
            local_id=report.local_id,
            title=self._transform_value(
                value=report.title,
            ),
            priority_name=report.priority.name if report.priority else '',
            bug_type_label=self._get_property_label('bug_type'),
            bug_type_name=report.bug_type.name,
            bug_type_link=report.bug_type.link,
            bug_type_remediation_link=report.bug_type.remediation_link or '/',
            scope_label=self._get_property_label('scope'),
            scope=self._transform_value(
                value=report.scope,
            ),
            cvss_criticity=report.cvss.criticity,
            cvss_score=report.cvss.score,
            cvss_vector=report.cvss.vector,
            end_point_label=self._get_property_label('end_point'),
            end_point=self._transform_value(
                value=report.end_point,
            ),
            vulnerable_part_label=self._get_property_label('vulnerable_part'),
            vulnerable_part=self._transform_value(
                value=report.vulnerable_part,
            ),
            part_name_label=self._get_property_label('part_name'),
            part_name=self._transform_value(
                value=report.part_name,
            ),
            payload_sample_label=self._get_property_label('payload_sample'),
            payload_sample=self._transform_value(
                value=report.payload_sample or '',
            ),
            technical_information=self._transform_value(
                value=report.technical_information or '',
            ),
            description=self.transform_report_description_html(
                description_html=report.description_html,
            ),
        )

    def _get_property_label(
        self,
        property_name: str,
    ) -> str:
        return PROPERTY_LABELS.get(property_name, property_name)

    @abstractmethod
    def transform_report_description_html(
        self,
        description_html: str,
    ) -> str:
        """
        Transform the report description.

        Args:
            description_html: a report description in HTML
        """

    def format_log(
        self,
        log: Log,
    ) -> str:
        """
        Get a formatted comment for a log.

        Args:
            log: a log

        Returns:
            a formatted log
        """
        return self._comment_body_template.substitute(
            author=log.author.username,
            date=log.created_at,
            body=self._transform_log(
                log,
            ),
        )

    @abstractmethod
    def transform_html(
        self,
        html: str,
    ) -> str:
        """
        Transform html.

        Args:
            html: some HTML
        """

    @singledispatchmethod
    def _transform_log(
        self,
        log: Log,
    ) -> str:
        return self.transform_html(
            html=log.message_html,
        )

    @_transform_log.register
    def _transform_comment_log(
        self,
        log: CommentLog,
    ) -> str:
        return self._comment_log_template.substitute(
            comment=self.transform_html(
                html=log.message_html,
            ),
        )

    @_transform_log.register
    def _transform_status_update_log(
        self,
        log: StatusUpdateLog,
    ) -> str:
        return self._status_update_log_template.substitute(
            old_status=self._translate_status(
                status=(log.old_status or {}).get('workflow_state') or '',
            ),
            new_status=self._translate_status(
                status=(log.new_status or {}).get('workflow_state') or '',
            ),
            comment=self.transform_html(
                html=log.message_html,
            ),
        )

    def _translate_status(
        self,
        status: str,
    ) -> str:
        return STATUS_TRANSLATIONS.get(status, '')

    @_transform_log.register
    def _transform_details_update_log(
        self,
        log: DetailsUpdateLog,
    ) -> str:
        details_lines = []
        for updated_property, new_value in (log.new_details or {}).items():
            old_value = (log.old_details or {}).get(updated_property, '')
            details_lines.append(
                self._details_update_log_line_template.substitute(
                    updated_property=self._get_property_label(
                        property_name=updated_property,
                    ),
                    old_value=self._transform_value(
                        value=old_value or '',
                    ),
                    new_value=self._transform_value(
                        value=new_value or '',
                    ),
                ),
            )
        return self._details_update_log_template.substitute(
            details_lines=''.join(details_lines),
        )

    @_transform_log.register
    def _format_reward_log(
        self,
        log: RewardLog,
    ) -> str:
        return self._reward_log_template.substitute(
            comment=self.transform_html(
                html=log.message_html,
            ),
        )
