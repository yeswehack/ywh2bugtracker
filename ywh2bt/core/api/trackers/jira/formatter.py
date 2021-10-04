"""Models and functions used for formatting reports data."""
from string import Template
from typing import Dict, Tuple, cast

from bs4 import BeautifulSoup, Tag  # type: ignore

from ywh2bt.core.api.formatter.formatter import ReportMessageFormatter
from ywh2bt.core.converter.html2jira import html2jira

REPORT_TITLE_TEMPLATE = '${local_id} : ${title}'
REPORT_DESCRIPTION_TEMPLATE = """
|| Title || ${local_id} : ${title} ||
| Priority | ${priority_name} |
| ${bug_type_label} | [${bug_type_name}|${bug_type_link}] => [Remediation|${bug_type_remediation_link}] |
| ${scope_label} | ${scope} |
| Severity | ${cvss_criticity}, score: ${cvss_score}, vector: {noformat}${cvss_vector}{noformat} |
| ${end_point_label} | ${end_point} |
| ${vulnerable_part_label} | ${vulnerable_part} |
| ${part_name_label} | ${part_name} |
| ${payload_sample_label} | ${payload_sample} |
| Technical Environment | ${technical_environment} |

${description}
"""
CLOSE_LOG_TEMPLATE = """
*Report closed*:

${old_status} -> ${new_status}

*Comment*:

${comment}
"""
COMMENT_BODY_TEMPLATE = """
*Date*: ${date}

${body}
"""
COMMENT_LOG_TEMPLATE = """
*Comment*:

${comment}
"""
CVSS_UPDATE_LOG_TEMPLATE = """
*CVSS updated*:

|| Detail || Old value || New value ||
| *Severity* | ${old_cvss_criticity} | ${new_cvss_criticity} |
| *Score* | ${old_cvss_score} | ${new_cvss_score} |
"""
STATUS_UPDATE_LOG_TEMPLATE = """
*Status updated*:

${old_status} -> ${new_status}

*Comment*:

${comment}
"""
DETAILS_UPDATE_LOG_TEMPLATE = """
*Details updated*:

|| Detail || Old value || New value ||
${details_lines}
"""
DETAILS_UPDATE_LOG_LINE_TEMPLATE = """| *${updated_property}* | ${old_value} | ${new_value} |
"""
PRIORITY_UPDATE_LOG_TEMPLATE = """
*Priority updated*:

${new_priority}
"""
REWARD_LOG_TEMPLATE = """
*Comment from reward*:

${comment}
"""


class JiraReportMessageFormatter(ReportMessageFormatter):
    """A report formatter to JIRA."""

    _code_block_template = Template('{code${language}}\n${content}\n{code}')

    _code_block_languages = [
        'actionscript',
        'ada',
        'applescript',
        'bash',
        'c',
        'c#',
        'c++',
        'cpp',
        'css',
        'erlang',
        'go',
        'groovy',
        'haskell',
        'html',
        'java',
        'javascript',
        'js',
        'json',
        'lua',
        'none',
        'nyan',
        'objc',
        'perl',
        'php',
        'python',
        'r',
        'rainbow',
        'ruby',
        'scala',
        'sh',
        'sql',
        'swift',
        'visualbasic',
        'xml',
        'yaml',
    ]

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
            details_update_log_template=Template(DETAILS_UPDATE_LOG_TEMPLATE),
            details_update_log_line_template=Template(DETAILS_UPDATE_LOG_LINE_TEMPLATE),
            priority_update_log_template=Template(PRIORITY_UPDATE_LOG_TEMPLATE),
            reward_log_template=Template(REWARD_LOG_TEMPLATE),
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
        return self._html2jira(
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
            HTML transformed to JIRA
        """
        return self._html2jira(
            html=html,
        )

    def _html2jira(
        self,
        html: str,
    ) -> str:
        body_html = self._img_tags_to_jira_tags(
            html=html,
        )
        body_html, code_blocks = self._extract_code_blocks(
            html=body_html,
        )
        body_jira = html2jira(
            html=body_html,
        )
        for block_id, code_block in code_blocks.items():
            body_jira = body_jira.replace(
                block_id,
                code_block,
            )
        return body_jira

    def _img_tags_to_jira_tags(
        self,
        html: str,
    ) -> str:
        soup = BeautifulSoup(
            html,
            features='lxml',
        )
        clean_html = str(soup)
        for img in soup.findAll('img'):
            alt = img.attrs.get('alt', '')
            src = img.attrs.get('src', '')
            a = f'!{alt}|{src}!'
            clean_html = clean_html.replace(str(img), a)
        return clean_html

    def _extract_code_blocks(
        self,
        html: str,
    ) -> Tuple[str, Dict[str, str]]:
        return self._extract_code_blocks_from_soup(
            soup=BeautifulSoup(
                html,
                features='lxml',
            ),
        )

    def _extract_code_blocks_from_soup(
        self,
        soup: BeautifulSoup,
    ) -> Tuple[str, Dict[str, str]]:
        clean_html = str(soup)
        code_blocks = {}
        for idx, code_tag in enumerate(soup.findAll('code')):
            block_id = f'{{yeswehack_code_section_{idx}}}'
            language = self._extract_code_block_language(
                code_tag=code_tag,
            )
            code_blocks[block_id] = self._code_block_template.substitute(
                language=f':{language}' if language else '',
                content=''.join(map(str, code_tag.contents)),
            )
            clean_html = clean_html.replace(str(code_tag), block_id)
        return clean_html, code_blocks

    def _extract_code_block_language(
        self,
        code_tag: Tag,
    ) -> str:
        title = code_tag.attrs.get('class', '')
        if isinstance(title, list):
            title = title[0] if title else ''
        language = cast(str, title.lower().replace('language-', ''))
        return language if language in self._code_block_languages else ''
