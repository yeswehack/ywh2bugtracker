"""Models and functions used for data synchronisation between YesWeHack and GitHub trackers."""
import os
import re
from copy import deepcopy
from datetime import (
    datetime,
    timezone,
)
from string import Template
from typing import (
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    cast,
)

import requests
from github import (
    Github,
    GithubException,
)
from github.Issue import Issue
from github.IssueComment import IssueComment
from github.Repository import Repository

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
)
from ywh2bt.core.api.trackers.github.attachment import GitHubAttachmentUploader
from ywh2bt.core.configuration.trackers.github import GitHubConfiguration

_RE_IMAGE = re.compile(pattern=r'!\[([^\]]+)]\(([^)]+)\)')
_RE_CONTENT_DISPOSITION_FILENAME = re.compile(pattern='filename="([^"]+)";?')
_TEXT_MAX_SIZE = 65536

AttachmentUploadResult = Tuple[Attachment, Optional[str], Optional[str]]


class GitHubTrackerClientError(TrackerClientError):
    """A GitHub tracker client error."""


class GitHubTrackerClient(TrackerClient[GitHubConfiguration]):
    """A GitHub tracker client."""

    _attachment_name_regex_template = Template(r'(?:!?\[)([^\[\]]*)(?:\])(?:\(${url}\))')
    _attachment_substitute_regex_template = Template(r'!?\[[^\[\]]*\]\(${url}\)')
    _github: Github
    _attachment_uploader: GitHubAttachmentUploader
    _message_formatter: ReportMessageMarkdownFormatter

    _default_timezone: timezone = timezone.utc

    def __init__(
        self,
        configuration: GitHubConfiguration,
    ):
        """
        Initialize self.

        Args:
            configuration: a GitHub configuration
        """
        super().__init__(
            configuration=configuration,
        )
        self._github = Github(
            base_url=cast(str, self.configuration.url),
            login_or_token=cast(str, self.configuration.token),
            verify=cast(bool, self.configuration.verify),
        )
        self._attachment_uploader = GitHubAttachmentUploader(
            configuration=self.configuration,
        )
        self._message_formatter = ReportMessageMarkdownFormatter()

    @property
    def tracker_type(self) -> str:
        """
        Get the type of the tracker client.

        Returns:
            the type of the  tracker client
        """
        return 'GitHub'

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
        self._ensure_auth()
        try:
            github_issue = self._get_github_issue(
                issue_id=issue_id,
            )
        except GitHubTrackerClientError:
            return None
        if github_issue is None:
            return None
        return self._build_tracker_issue(
            issue_id=issue_id,
            issue_url=github_issue.html_url,
            closed=github_issue.closed_at is not None,
        )

    def get_tracker_issue_comments(
        self,
        issue_id: str,
        exclude_comments: Optional[List[str]] = None,
    ) -> List[TrackerIssueComment]:
        """
        Get a list of comments on an issue.

        Args:
            issue_id: an issue id
            exclude_comments: an optional list of comment to exclude

        Returns:
            The list of comments
        """
        self._ensure_auth()
        try:
            github_issue = self._get_github_issue(
                issue_id=issue_id,
            )
        except GitHubTrackerClientError:
            return []
        if not github_issue:
            return []
        return self._extract_comments(
            github_issue=github_issue,
            exclude_comments=exclude_comments,
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
        repository = self._get_repository()
        title = self._message_formatter.format_report_title(
            report=report,
        )
        description = self._message_formatter.format_report_description(
            report=report,
        ) + self._get_attachments_list_description(
            attachments=report.attachments,
        )
        external_description = ''
        description_attachment = None
        if len(description) > _TEXT_MAX_SIZE:
            external_description = description
            description_attachment = self._build_external_description_attachment(
                name=f'report-{report.local_id.replace("#", "")}-description.md',
            )
            report_copy = deepcopy(report)
            report_copy.description_html = (
                '<p>This report description is too large to fit into a GitHub issue. '
                + f'See attachment <a href="{description_attachment.url}">{description_attachment.original_name}</a> '
                + 'for more details.</p>'
            )
            description = self._message_formatter.format_report_description(
                report=report_copy,
            ) + self._get_attachments_list_description(
                attachments=[
                    description_attachment,
                    *report.attachments,
                ],
            )
        issue = self._create_issue(
            github_repository=repository,
            title=title,
            body='This issue is being synchronized. Please check back in a moment.',
        )
        description, external_description = self._replace_attachments_references(
            uploads=self._upload_attachments(
                issue=issue,
                attachments=report.attachments,
            ),
            referencing_texts=[
                description,
                external_description,
            ],
        )
        if description_attachment:
            description_attachment.data_loader = lambda: bytes(external_description, 'utf-8')
            description = self._replace_attachments_references(
                uploads=self._upload_attachments(
                    issue=issue,
                    attachments=[
                        description_attachment,
                    ],
                ),
                referencing_texts=[
                    description,
                ],
            )[0]
        issue.edit(
            body=description,
        )
        return self._build_tracker_issue(
            issue_id=str(issue.id),
            issue_url=issue.html_url,
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
        logs: Iterable[Log],
    ) -> SendLogsResult:
        """
        Send logs to the tracker.

        Args:
            tracker_issue: information about the tracker issue
            logs: a list of comments

        Raises:
            GitHubTrackerClientError: if an error occurs

        Returns:
            information about the sent comments
        """
        self._ensure_auth()
        tracker_comments = SendLogsResult(
            tracker_issue=tracker_issue,
            added_comments=[],
        )
        github_issue = self._get_github_issue(
            issue_id=tracker_issue.issue_id,
        )
        if not github_issue:
            raise GitHubTrackerClientError(f'GitHub issue {tracker_issue.issue_id} not found')
        for log in logs:
            github_comment = self._add_comment(
                github_issue=github_issue,
                log=log,
            )
            tracker_comments.added_comments.append(
                TrackerIssueComment(
                    author=github_comment.user.name or github_comment.user.login,
                    created_at=self._ensure_timezone(
                        dt=github_comment.created_at,
                        tz=self._default_timezone,
                    ),
                    comment_id=str(github_comment.id),
                    body=github_comment.body,
                    attachments={},
                ),
            )
        return tracker_comments

    def _ensure_timezone(
        self,
        dt: datetime,
        tz: timezone,
    ) -> datetime:
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=tz)
        return dt

    def test(
        self,
    ) -> None:
        """
        Test the client.

        Raises:
            GitHubTrackerClientError: if the test failed
        """
        try:
            login = self._github.get_user().login
        except GithubException as e:
            raise GitHubTrackerClientError('Unable to log in with GitHub API client') from e
        if not login:
            raise GitHubTrackerClientError('Unable to log in with GitHub API client')

    def _extract_comments(
        self,
        github_issue: Issue,
        exclude_comments: Optional[List[str]] = None,
    ) -> List[TrackerIssueComment]:
        return [
            self._extract_comment(
                github_comment=github_comment,
            )
            for github_comment in github_issue.get_comments()
            if exclude_comments is None or str(github_comment.id) not in exclude_comments
        ]

    def _extract_comment(
        self,
        github_comment: IssueComment,
    ) -> TrackerIssueComment:
        github_body = github_comment.body
        inline_images = _RE_IMAGE.findall(github_body)
        comment_attachments: Dict[str, TrackerAttachment] = {}
        for _, inline_url in inline_images:
            attachment = self._download_attachment(
                url=inline_url,
            )
            if attachment:
                comment_attachments[inline_url] = attachment
        return TrackerIssueComment(
            created_at=self._ensure_timezone(
                dt=github_comment.created_at,
                tz=self._default_timezone,
            ),
            author=github_comment.user.name or github_comment.user.login,
            comment_id=str(github_comment.id),
            body=github_body,
            attachments=comment_attachments,
        )

    def _download_attachment(
        self,
        url: str,
    ) -> Optional[TrackerAttachment]:
        try:
            response = requests.get(url)
        except requests.RequestException:
            return None
        content_disposition = response.headers.get('Content-Disposition')
        filename = None
        if content_disposition:
            match = _RE_CONTENT_DISPOSITION_FILENAME.search(content_disposition)
            if match:
                filename = match.group(1)
        if not content_disposition or not filename:
            filename = os.path.basename(url)
        return TrackerAttachment(
            filename=filename,
            mime_type=response.headers.get('Content-Type', 'text/plain'),
            content=response.content,
        )

    def _get_repository(
        self,
    ) -> Repository:
        project = cast(str, self.configuration.project)
        if project[0] == '/':
            project = project[1:]
        try:
            return self._github.get_repo(
                project,
            )
        except (GithubException, requests.RequestException) as e:
            raise GitHubTrackerClientError(
                f'Unable to get GitHub repository {self.configuration.project}',
            ) from e

    def _create_issue(
        self,
        github_repository: Repository,
        title: str,
        body: str,
    ) -> Issue:
        try:
            return github_repository.create_issue(
                title=title,
                body=body,
            )
        except GithubException as e:
            raise GitHubTrackerClientError(
                f'Unable to create issue for project {self.configuration.project} to GitHub',
            ) from e

    def _add_comment(
        self,
        github_issue: Issue,
        log: Log,
    ) -> IssueComment:
        comment_body = self._message_formatter.format_log(
            log=log,
        ) + self._get_attachments_list_description(
            attachments=log.attachments,
        )
        external_body = ''
        body_attachment = None
        if len(comment_body) > _TEXT_MAX_SIZE:
            external_body = comment_body
            body_attachment = self._build_external_description_attachment(
                name=f'comment-{log.log_id}-description.md',
            )
            log_copy = deepcopy(log)
            log_copy.message_html = (
                '<p>This comment is too large to fit into a GitHub comment. '
                + f'See attachment <a href="{body_attachment.url}">{body_attachment.original_name}</a> '
                + 'for more details.</p>'
            )
            comment_body = self._message_formatter.format_log(
                log=log_copy,
            ) + self._get_attachments_list_description(
                attachments=[
                    body_attachment,
                    *log.attachments,
                ],
            )
        try:
            github_comment = github_issue.create_comment(
                body='This comment is being synchronized. Please check back in a moment.',
            )
        except GithubException as e:
            raise GitHubTrackerClientError(
                f'Unable to add GitHub comment for issue {github_issue} in project {self.configuration.project}',
            ) from e
        comment_body, external_body = self._replace_attachments_references(
            uploads=self._upload_attachments(
                issue=github_issue,
                attachments=log.attachments,
            ),
            referencing_texts=[
                comment_body,
                external_body,
            ],
        )
        if body_attachment:
            body_attachment.data_loader = lambda: bytes(external_body, 'utf-8')
            comment_body = self._replace_attachments_references(
                uploads=self._upload_attachments(
                    issue=github_issue,
                    attachments=[
                        body_attachment,
                    ],
                ),
                referencing_texts=[
                    comment_body,
                ],
            )[0]
        github_comment.edit(
            body=comment_body,
        )
        return github_comment

    def _get_github_issue(
        self,
        issue_id: str,
    ) -> Optional[Issue]:
        github_repository = self._get_repository()
        issue_id_int = int(issue_id)
        try:
            for issue in github_repository.get_issues(state='all'):
                if issue.id == issue_id_int:
                    return issue
        except GithubException as e:
            raise GitHubTrackerClientError(
                f'GitHub issue {issue_id} not found in project {self.configuration.project}',
            ) from e
        return None

    def _replace_attachments_references(
        self,
        uploads: List[AttachmentUploadResult],
        referencing_texts: List[str],
    ) -> List[str]:
        for attachment, upload_url, error_message in uploads:
            if upload_url:
                referencing_texts = [
                    text.replace(
                        attachment.url,
                        upload_url,
                    )
                    for text in referencing_texts
                ]
            elif error_message:
                referencing_texts = [
                    self._substitute_attachment_url(
                        body=text,
                        url=attachment.url,
                        substitution=error_message,
                    )
                    for text in referencing_texts
                ]
        return referencing_texts

    def _upload_attachments(
        self,
        issue: Issue,
        attachments: List[Attachment],
    ) -> List[AttachmentUploadResult]:
        uploads = []
        for attachment in attachments:
            url = None
            error_message = None
            if self.configuration.github_cdn_on:
                url = self._attachment_uploader.upload_attachment(
                    issue=issue,
                    attachment=attachment,
                )
                if not url:
                    error_message = f'(Attachment "{attachment.original_name}" not available due to upload error)'
            else:
                error_message = (
                    f'(Attachment "{attachment.original_name}" not available '
                    + 'due to export script’s configuration)'
                )
            uploads.append(
                (
                    attachment,
                    url,
                    error_message,
                ),
            )
        return uploads

    def _get_attachments_list_description(
        self,
        attachments: List[Attachment],
    ) -> str:
        attachments_lines = []
        if attachments:
            attachments_lines = [
                '',
                '**Attachments**:',
            ]
            for attachment in attachments:
                attachments_lines.append(
                    f'- [{attachment.original_name}]({attachment.url})',
                )
            attachments_lines.append('')
        return '\n'.join(attachments_lines)

    def _extract_attachment_name(
        self,
        referencing_texts: List[str],
        attachment: Attachment,
    ) -> str:
        attachment_name_regex = self._attachment_name_regex_template.substitute(
            url=re.escape(attachment.url),
        )
        for text in referencing_texts:
            matches = re.findall(
                attachment_name_regex,
                text,
            )
            if matches:
                return cast(str, matches[0])
        return attachment.original_name

    def _substitute_attachment_url(
        self,
        body: str,
        url: str,
        substitution: str,
    ) -> str:
        attachment_substitute_regex = self._attachment_substitute_regex_template.substitute(
            url=re.escape(url),
        )
        return re.sub(
            attachment_substitute_regex,
            substitution,
            body,
        )

    def _ensure_auth(
        self,
    ) -> None:
        try:
            user_id = self._github.get_user().id
        except GithubException as e:
            raise GitHubTrackerClientError('Unable to authenticate to GitHub') from e
        if not isinstance(user_id, int):
            raise GitHubTrackerClientError('Unable to authenticate to GitHub')
