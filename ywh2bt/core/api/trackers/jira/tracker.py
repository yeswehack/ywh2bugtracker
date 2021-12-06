"""Models and functions used for data synchronisation between YesWeHack and Jira trackers."""
import re
from copy import deepcopy
from datetime import datetime
from string import Template
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    cast,
)
from urllib.parse import quote

from jira import (  # type: ignore
    Comment as JIRAComment,
    Issue as JIRAIssue,
    JIRA,
    JIRAError,
)
from jira.utils import CaseInsensitiveDict  # type: ignore

from ywh2bt.core.api.formatter.markdown import ReportMessageMarkdownFormatter
from ywh2bt.core.api.models.report import (
    Attachment,
    Log,
    Report,
)
from ywh2bt.core.api.tracker import (
    SendLogsResult,
    TrackerAttachment,
    TrackerClient,
    TrackerClientError,
    TrackerIssue,
    TrackerIssueComment,
    TrackerIssueComments,
)
from ywh2bt.core.api.trackers.jira.formatter import JiraReportMessageFormatter
from ywh2bt.core.configuration.trackers.jira import JiraConfiguration
from ywh2bt.core.converter.jira2markdown import jira2markdown

_RE_IMAGE = re.compile(pattern=r'!([^!|]+)(?:\|[^!]*)?!')
_TEXT_MAX_SIZE = 32767


# hot patching shenanigans
def _case_insensitive_dict_init_hot_patch(
    obj: CaseInsensitiveDict,
    *args: Any,
    **kw: Any,
) -> None:
    super(CaseInsensitiveDict, obj).__init__(*args, *kw)  # noqa: WPS608, WPS613
    obj_copy = super(CaseInsensitiveDict, obj).copy()  # noqa: WPS608, WPS613
    obj.itemlist = {}
    for key, value in obj_copy.items():
        if key != key.lower():
            obj[key.lower()] = value
            obj.pop(key, None)


CaseInsensitiveDict.__init__ = _case_insensitive_dict_init_hot_patch  # noqa: WPS609


class JiraTrackerClientError(TrackerClientError):
    """A Jira tracker client error."""


class JiraTrackerClient(TrackerClient[JiraConfiguration]):
    """A Jira tracker client."""

    _jira: Optional[JIRA]
    _message_formatter: JiraReportMessageFormatter

    _attachments_list_description_item_jira_template = Template('- [${name}|${url}]')
    _attachments_list_description_item_markdown_template = Template('- [${name}](${url})')

    def __init__(
        self,
        configuration: JiraConfiguration,
    ):
        """
        Initialize self.

        Args:
            configuration: a Jira configuration
        """
        super().__init__(
            configuration=configuration,
        )
        self._jira = None
        self._message_formatter = JiraReportMessageFormatter()

    @property
    def tracker_type(self) -> str:
        """
        Get the type of the tracker client.

        Returns:
            the type of the  tracker client
        """
        return 'Jira'

    def _build_tracker_issue(
        self,
        issue_id: str,
        issue_url: str,
        closed: bool,
    ) -> TrackerIssue:
        return TrackerIssue(
            tracker_url=cast(str, self.configuration.url),
            project=cast(str, self.configuration.project),
            issue_id=issue_id,
            issue_url=issue_url,
            closed=closed,
        )

    def get_tracker_issue(
        self,
        issue_id: str,
    ) -> Optional[TrackerIssue]:
        """
        Get a tracker issue.

        Args:
            issue_id: an issue id

        Returns:
            The issue if it exists, else None
        """
        try:
            jira_issue = self._get_issue(
                issue_id=issue_id,
            )
        except JiraTrackerClientError:
            return None
        return self._build_tracker_issue(
            issue_id=issue_id,
            issue_url=jira_issue.permalink(),
            closed=self._issue_is_closed(
                jira_issue=jira_issue,
            ),
        )

    def _issue_is_closed(
        self,
        jira_issue: JIRAIssue,
    ) -> bool:
        fields = jira_issue.fields
        return fields.status is not None and fields.status.name == self.configuration.issue_closed_status

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

        Returns:
            The list of comments
        """
        try:
            jira_issue = self._get_issue(
                issue_id=issue_id,
            )
        except JiraTrackerClientError:
            return []
        return self._extract_comments(
            jira_issue=jira_issue,
            exclude_comments=exclude_comments,
        )

    def _extract_comments(
        self,
        jira_issue: JIRAIssue,
        exclude_comments: Optional[List[str]] = None,
    ) -> List[TrackerIssueComment]:
        return [
            self._extract_comment(
                jira_issue=jira_issue,
                jira_comment=jira_comment,
            )
            for jira_comment in jira_issue.fields.comment.comments
            if exclude_comments is None or str(jira_comment.id) not in exclude_comments
        ]

    def _extract_comment(
        self,
        jira_issue: JIRAIssue,
        jira_comment: JIRAComment,
    ) -> TrackerIssueComment:
        jira_body = jira_comment.body
        inline_images = _RE_IMAGE.findall(jira_body)
        comment_attachments: Dict[str, TrackerAttachment] = {}
        for jira_attachment in jira_issue.fields.attachment:
            if jira_attachment.filename in inline_images:
                comment_attachments[jira_attachment.filename] = TrackerAttachment(
                    filename=jira_attachment.filename,
                    mime_type=jira_attachment.mimeType,
                    content=jira_attachment.get(),
                )
        return TrackerIssueComment(
            created_at=self._parse_date(
                date=jira_comment.created,
            ),
            author=jira_comment.author.displayName,
            comment_id=str(jira_comment.id),
            body=jira2markdown(
                src=jira_body,
            ),
            attachments=comment_attachments,
        )

    def send_report(
        self,
        report: Report,
    ) -> TrackerIssue:
        """
        Send a report to the tracker.

        Args:
            report: a report

        Returns:
            information about the sent report
        """
        self._ensure_auth()
        title = self._message_formatter.format_report_title(
            report=report,
        )
        description = self._message_formatter.format_report_description(
            report=report,
        ) + self._get_attachments_list_description(
            title='*Attachments*:',
            item_template=self._attachments_list_description_item_jira_template,
            attachments=report.attachments,
        )
        markdown_description = ''
        description_attachment = None
        if len(description) > _TEXT_MAX_SIZE:
            description_attachment = self._build_external_description_attachment(
                name=f'report-{report.local_id.replace("#", "")}-description.md',
            )
            markdown_description = ReportMessageMarkdownFormatter().format_report_description(
                report=report,
            ) + self._get_attachments_list_description(
                title='**Attachments**:',
                item_template=self._attachments_list_description_item_markdown_template,
                attachments=report.attachments,
            )
            report_copy = deepcopy(report)
            report_copy.description_html = (
                '<p>This report description is too large to fit into a JIRA issue. '
                + f'See attachment <a href="{description_attachment.url}">{description_attachment.original_name}</a> '
                + 'for more details.</p>'
            )
            description = self._message_formatter.format_report_description(
                report=report_copy,
            ) + self._get_attachments_list_description(
                title='*Attachments*:',
                item_template=self._attachments_list_description_item_jira_template,
                attachments=[
                    description_attachment,
                    *report.attachments,
                ],
            )
        jira_issue = self._create_issue(
            title=title,
            description='This issue is being synchronized. Please check back in a moment.',
        )
        description, markdown_description = self._replace_attachments_references(
            uploads=self._upload_attachments(
                issue=jira_issue,
                attachments=report.attachments,
            ),
            referencing_texts=[
                description,
                markdown_description,
            ],
        )
        if description_attachment:
            description_attachment.data_loader = lambda: bytes(markdown_description, 'utf-8')
            description = self._replace_attachments_references(
                uploads=self._upload_attachments(
                    issue=jira_issue,
                    attachments=[
                        description_attachment,
                    ],
                ),
                referencing_texts=[
                    description,
                ],
            )[0]
        jira_issue.update(
            description=description,
        )
        return self._build_tracker_issue(
            issue_id=jira_issue.key,
            issue_url=jira_issue.permalink(),
            closed=False,
        )

    def _build_external_description_attachment(
        self,
        name: str,
    ) -> Attachment:
        return Attachment(
            attachment_id=0,
            name=name,
            original_name=name,
            mime_type='text/markdown',
            size=0,
            url=f'http://tracker/external/{name}',
            data_loader=lambda: bytes('', 'utf-8'),
        )

    def send_logs(
        self,
        tracker_issue: TrackerIssue,
        logs: List[Log],
    ) -> SendLogsResult:
        """
        Send logs to the tracker.

        Args:
            tracker_issue: information about the tracker issue
            logs: a list of logs

        Returns:
            information about the sent logs
        """
        jira_issue = self._get_issue(
            issue_id=tracker_issue.issue_id,
        )
        tracker_comments = SendLogsResult(
            tracker_issue=tracker_issue,
            added_comments=[],
        )
        for log in logs:
            jira_comment = self._add_comment(
                issue=jira_issue,
                log=log,
            )
            tracker_comments.added_comments.append(
                TrackerIssueComment(
                    created_at=self._parse_date(
                        date=jira_comment.created,
                    ),
                    author=jira_comment.author.displayName,
                    comment_id=str(jira_comment.id),
                    body=jira2markdown(
                        src=jira_comment.body,
                    ),
                    attachments={},
                ),
            )
        return tracker_comments

    def _parse_date(
        self,
        date: str,
    ) -> datetime:
        return datetime.strptime(
            date,
            '%Y-%m-%dT%H:%M:%S.%f%z',
        )

    def test(
        self,
    ) -> None:
        """Test the client."""
        self._ensure_auth()

    def _get_issue(
        self,
        issue_id: str,
    ) -> JIRAIssue:
        try:
            return self._get_client().issue(
                id=issue_id,
            )
        except JIRAError as e:
            raise JiraTrackerClientError(
                f'Unable to get JIRA issue {issue_id} in project {self.configuration.project}',
            ) from e

    def _create_issue(
        self,
        title: str,
        description: str,
    ) -> JIRAIssue:
        fields = {
            'project': {
                'key': self.configuration.project,
            },
            'summary': title,
            'description': description,
            'issuetype': {
                'name': self.configuration.issuetype,
            },
        }
        try:
            return self._get_client().create_issue(
                fields=fields,
            )
        except JIRAError as e:
            raise JiraTrackerClientError(
                f'Unable to create JIRA issue for project {self.configuration.project}',
            ) from e

    def _add_comment(
        self,
        issue: JIRAIssue,
        log: Log,
    ) -> JIRAComment:
        comment_body = self._message_formatter.format_log(
            log=log,
        ) + self._get_attachments_list_description(
            title='*Attachments*:',
            item_template=self._attachments_list_description_item_jira_template,
            attachments=log.attachments,
        )
        markdown_description = ''
        body_attachment = None
        if len(comment_body) > _TEXT_MAX_SIZE:
            body_attachment = self._build_external_description_attachment(
                name=f'comment-{log.log_id}-description.md',
            )
            markdown_description = ReportMessageMarkdownFormatter().format_log(
                log=log,
            ) + self._get_attachments_list_description(
                title='**Attachments**:',
                item_template=self._attachments_list_description_item_markdown_template,
                attachments=log.attachments,
            )
            log_copy = deepcopy(log)
            log_copy.message_html = (
                '<p>This comment is too large to fit into a JIRA comment. '
                + f'See attachment <a href="{body_attachment.url}">{body_attachment.original_name}</a> '
                + 'for more details.</p>'
            )
            comment_body = self._message_formatter.format_log(
                log=log_copy,
            ) + self._get_attachments_list_description(
                title='*Attachments*:',
                item_template=self._attachments_list_description_item_jira_template,
                attachments=[
                    body_attachment,
                    *log.attachments,
                ],
            )
        comment_body, markdown_description = self._replace_attachments_references(
            uploads=self._upload_attachments(
                issue=issue,
                attachments=log.attachments,
            ),
            referencing_texts=[
                comment_body,
                markdown_description,
            ],
        )
        if body_attachment:
            body_attachment.data_loader = lambda: bytes(markdown_description, 'utf-8')
            comment_body = self._replace_attachments_references(
                uploads=self._upload_attachments(
                    issue=issue,
                    attachments=[
                        body_attachment,
                    ],
                ),
                referencing_texts=[
                    comment_body,
                ],
            )[0]
        try:
            return self._get_client().add_comment(
                issue=str(issue),
                body=comment_body,
            )
        except JIRAError as e:
            raise JiraTrackerClientError(
                f'Unable to add JIRA comment for issue {issue} in project {self.configuration.project}',
            ) from e

    def _upload_attachments_and_substitute_references(
        self,
        issue: JIRAIssue,
        attachments: List[Attachment],
        referencing_texts: List[str],
    ) -> List[str]:
        uploads = self._upload_attachments(
            issue=issue,
            attachments=attachments,
        )
        for attachment, upload_url in uploads:
            referencing_texts = [
                text.replace(
                    attachment.url,
                    upload_url,
                )
                for text in referencing_texts
            ]
        return referencing_texts

    def _replace_attachments_references(
        self,
        uploads: List[Tuple[Attachment, str]],
        referencing_texts: List[str],
    ) -> List[str]:
        for attachment, upload_url in uploads:
            referencing_texts = [
                text.replace(
                    attachment.url,
                    upload_url,
                )
                for text in referencing_texts
            ]
        return referencing_texts

    def _upload_attachments(
        self,
        issue: JIRAIssue,
        attachments: List[Attachment],
    ) -> List[Tuple[Attachment, str]]:
        uploads = []
        for attachment in attachments:
            try:
                issue_attachment = self._get_client().add_attachment(
                    issue=issue.key,
                    filename=attachment.original_name,
                    attachment=attachment.data,
                )
            except JIRAError as e:
                raise JiraTrackerClientError(
                    f'Unable to upload attachments for project {self.configuration.project} to JIRA',
                ) from e
            issue_attachment_url = quote(
                issue_attachment.content,
                safe=':/?&=',
            )
            uploads.append(
                (
                    attachment,
                    issue_attachment_url,
                ),
            )
        return uploads

    def _get_attachments_list_description(
        self,
        title: str,
        item_template: Template,
        attachments: List[Attachment],
    ) -> str:
        attachments_lines = []
        if attachments:
            attachments_lines = [
                '',
                title,
            ]
            for attachment in attachments:
                attachments_lines.append(
                    item_template.substitute(
                        name=attachment.original_name,
                        url=attachment.url,
                    ),
                )
            attachments_lines.append('')
        return '\n'.join(attachments_lines)

    def _get_client(
        self,
    ) -> JIRA:
        if not self._jira:
            self._jira = self._build_client()
        return self._jira

    def _build_client(
        self,
    ) -> JIRA:
        configuration = self.configuration
        try:
            return JIRA(
                server=configuration.url,
                basic_auth=(
                    configuration.login,
                    configuration.password,
                ),
                options={
                    'verify': configuration.verify,
                },
            )
        except JIRAError as e:
            raise JiraTrackerClientError('Unable to connect to JIRA') from e

    def _ensure_auth(
        self,
    ) -> None:
        try:
            self._get_client().myself()
        except JIRAError as e:
            raise JiraTrackerClientError('Unable to authenticate to JIRA') from e
