"""Models and functions used for formatting reports data into markdown."""

from html import escape as html_escape
from string import Template

from ywh2bt.core.api.formatter.formatter import ReportMessageFormatter
from ywh2bt.core.html import ywh_html_to_markdown


REPORT_TITLE_TEMPLATE = "${local_id} : ${title}"
REPORT_DESCRIPTION_TEMPLATE = """
| Title | ${local_id} : ${title} |
|-------|---------------------|
| Priority | ${priority_name} |
| ${bug_type_label} | [${bug_type_name}](${bug_type_link}) &#8594; [Remediation](${bug_type_remediation_link}) |
| ${scope_label} | ${scope} |
| Severity | ${cvss_criticity}, score: ${cvss_score}, vector: ${cvss_vector} |
| ${end_point_label} | ${end_point} |
| ${vulnerable_part_label} | ${vulnerable_part} |
| ${part_name_label} | ${part_name} |
| ${payload_sample_label} | ${payload_sample} |
| Technical Environment | ${technical_environment} |

${description}
"""
CLOSE_LOG_TEMPLATE = """
**Report closed**:

${old_status} -> ${new_status}

**Comment**:

${comment}
"""
COMMENT_BODY_TEMPLATE = """
**Date**: ${date}

${body}
"""
COMMENT_LOG_TEMPLATE = """
**Comment**:

${comment}
"""
CVSS_UPDATE_LOG_TEMPLATE = """
**CVSS updated**:

| Detail | Old value | New value |
|--------|-----------|-----------|
| **Severity** | ${old_cvss_criticity} | ${new_cvss_criticity} |
| **Score** | ${old_cvss_score} | ${new_cvss_score} |
"""
STATUS_UPDATE_LOG_TEMPLATE = """
**Status updated**:

${old_status} -> ${new_status}

**Comment**:

${comment}
"""
FIX_VERIFIED_LOG_TEMPLATE = """
**Fix verification**:

${verified}

**Comment**:

${comment}
"""
DETAILS_UPDATE_LOG_TEMPLATE = """
**Details updated**:

| Detail | Old value | New value |
|--------|-----------|-----------|
${details_lines}
"""
DETAILS_UPDATE_LOG_LINE_TEMPLATE = """| **${updated_property}** | ${old_value} | ${new_value} |
"""
PRIORITY_UPDATE_LOG_TEMPLATE = """
**Priority updated**:

${new_priority}
"""
REWARD_LOG_TEMPLATE = """
**Comment from reward**:

${comment}
"""
TRANSFER_LOG_TEMPLATE = """
**Report transferred**:

${old_program} -> ${program}
"""
ASK_FOR_FIX_VERIFICATION_STATUS_LOG_TEMPLATE = """
**Fix verification**:

${new_ask_for_fix_verification_status}

**Comment**:

${comment}
"""


def _html_transformer(
    value: str,
) -> str:
    return html_escape(value)


class ReportMessageMarkdownFormatter(ReportMessageFormatter):
    """A report formatter to markdown."""

    def __init__(self) -> None:
        """Initialize self."""
        super().__init__(
            report_title_template=Template(REPORT_TITLE_TEMPLATE),
            report_description_template=Template(REPORT_DESCRIPTION_TEMPLATE),
            close_log_template=Template(CLOSE_LOG_TEMPLATE),
            comment_body_template=Template(COMMENT_BODY_TEMPLATE),
            comment_log_template=Template(COMMENT_LOG_TEMPLATE),
            cvss_update_log_template=Template(CVSS_UPDATE_LOG_TEMPLATE),
            status_update_log_template=Template(STATUS_UPDATE_LOG_TEMPLATE),
            fix_verified_log_template=Template(FIX_VERIFIED_LOG_TEMPLATE),
            details_update_log_template=Template(DETAILS_UPDATE_LOG_TEMPLATE),
            details_update_log_line_template=Template(DETAILS_UPDATE_LOG_LINE_TEMPLATE),
            priority_update_log_template=Template(PRIORITY_UPDATE_LOG_TEMPLATE),
            reward_log_template=Template(REWARD_LOG_TEMPLATE),
            transfer_log_template=Template(TRANSFER_LOG_TEMPLATE),
            ask_for_fix_verification_status_log_template=Template(ASK_FOR_FIX_VERIFICATION_STATUS_LOG_TEMPLATE),
            value_transformer=_html_transformer,
        )

    def transform_report_description_html(
        self,
        description_html: str,
    ) -> str:
        """
        Transform the report description.

        Args:
            description_html: a report description in HTML

        Returns:
            a transformed description
        """
        return ywh_html_to_markdown(
            html=description_html,
        )

    def transform_html(
        self,
        html: str,
    ) -> str:
        """
        Transform from HTML.

        Args:
            html: HTML

        Returns:
            HTML transformed to markdown
        """
        return ywh_html_to_markdown(
            html=html,
        )
