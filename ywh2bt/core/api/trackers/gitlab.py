"""Models and functions used for data synchronisation between YesWeHack and GitLab trackers."""
from __future__ import annotations

import os
import re
from copy import deepcopy
from datetime import datetime
from typing import (
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    cast,
)

import requests
from gitlab import (  # type: ignore
    Gitlab,
    GitlabError,
)
from gitlab.v4.objects import (  # type: ignore
    Project,
    ProjectIssue,
    ProjectIssueNote,
)

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
from ywh2bt.core.configuration.trackers.gitlab import GitLabConfiguration

_RE_IMAGE = re.compile(pattern=r'!\[([^\]]+)]\(([^)]+)\)')
_RE_CONTENT_DISPOSITION_FILENAME = re.compile(pattern='filename="([^"]+)";?')
_TEXT_MAX_SIZE = 1000000


class GitLabTrackerClientError(TrackerClientError):
    """A GitLab tracker client error."""


class GitLabTrackerClient(TrackerClient[GitLabConfiguration]):
    """A GitLab tracker client."""

    _session: requests.Session
    _gitlab: Gitlab
    _message_formatter: ReportMessageMarkdownFormatter
    _default_author_name: str

    def __init__(
        self,
        configuration: GitLabConfiguration,
    ):
        """
        Initialize self.

        Args:
            configuration: a GitLab configuration
        """
        super().__init__(
            configuration=configuration,
        )
        self._default_author_name = 'Anonymous'
        self._session = requests.Session()
        self._session.verify = configuration.verify
        self._gitlab = Gitlab(
            url=configuration.url,
            private_token=configuration.token,
            session=self._session,
        )
        self._message_formatter = ReportMessageMarkdownFormatter()

    @property
    def tracker_type(self) -> str:
        """
        Get the type of the tracker client.

        Returns:
            the type of the  tracker client
        """
        return 'GitLab'

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
            gitlab_issue = self._get_gitlab_issue(
                issue_id=issue_id,
            )
        except GitLabTrackerClientError:
            return None
        if gitlab_issue is None:
            return None
        return self._build_tracker_issue(
            issue_id=issue_id,
            issue_url=gitlab_issue.web_url,
            closed=gitlab_issue.state == 'closed',
        )

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
            gitlab_issue = self._get_gitlab_issue(
                issue_id=issue_id,
            )
        except GitLabTrackerClientError:
            return []
        if not gitlab_issue:
            return []
        return self._extract_comments(
            gitlab_issue=gitlab_issue,
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
        gitlab_project = self._get_gitlab_project()
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
                '<p>This report description is too large to fit into a GitLab issue. '
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
        description, external_description = self._replace_attachments_references(
            uploads=self._upload_attachments(
                gitlab_project=gitlab_project,
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
                    gitlab_project=gitlab_project,
                    attachments=[
                        description_attachment,
                    ],
                ),
                referencing_texts=[
                    description,
                ],
            )[0]
        gitlab_issue = self._create_issue(
            gitlab_project=gitlab_project,
            title=title,
            description=description,
            confidential=self.configuration.confidential or False,
        )
        return self._build_tracker_issue(
            issue_id=str(gitlab_issue.id),
            issue_url=gitlab_issue.web_url,
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

    def _extract_comments(
        self,
        gitlab_issue: ProjectIssue,
        exclude_comments: Optional[List[str]] = None,
    ) -> List[TrackerIssueComment]:
        return [
            self._extract_comment(
                gitlab_note=gitlab_note,
            )
            for gitlab_note in reversed(gitlab_issue.notes.list())
            if exclude_comments is None or str(gitlab_note.id) not in exclude_comments
        ]

    def _extract_comment(
        self,
        gitlab_note: ProjectIssueNote,
    ) -> TrackerIssueComment:
        gitlab_body = gitlab_note.body
        inline_images = _RE_IMAGE.findall(gitlab_body)
        comment_attachments: Dict[str, TrackerAttachment] = {}
        for _, inline_path in inline_images:
            attachment = self._download_attachment(
                path=inline_path,
            )
            if attachment:
                comment_attachments[inline_path] = attachment
        return TrackerIssueComment(
            created_at=self._parse_date(
                date=gitlab_note.created_at,
            ),
            author=gitlab_note.author.get('name', self._default_author_name),
            comment_id=str(gitlab_note.id),
            body=gitlab_body,
            attachments=comment_attachments,
        )

    def _download_attachment(
        self,
        path: str,
    ) -> Optional[TrackerAttachment]:
        url = f'{self.configuration.url}/{self.configuration.project}/{path}'
        try:
            response = requests.get(url)
        except requests.RequestException:
            return None
        if not response.ok:
            return None
        content_disposition = response.headers.get('Content-Disposition')
        filename = None
        if content_disposition:
            match = _RE_CONTENT_DISPOSITION_FILENAME.search(content_disposition)
            if match:
                filename = match.group(1)
        if not content_disposition or not filename:
            filename = os.path.basename(path)
        return TrackerAttachment(
            filename=filename,
            mime_type=response.headers.get('Content-Type', 'text/plain'),
            content=response.content,
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
            GitLabTrackerClientError: if an error occurs

        Returns:
            information about the sent comments
        """
        self._ensure_auth()
        tracker_comments = SendLogsResult(
            tracker_issue=tracker_issue,
            added_comments=[],
        )
        gitlab_project = self._get_gitlab_project()
        gitlab_issue = self._get_gitlab_issue(
            issue_id=tracker_issue.issue_id,
        )
        if not gitlab_issue:
            raise GitLabTrackerClientError(
                f'GitLab issue {tracker_issue.issue_id} not found in project {self.configuration.project}',
            )
        for log in logs:
            gitlab_comment = self._add_comment(
                gitlab_project=gitlab_project,
                gitlab_issue=gitlab_issue,
                log=log,
            )
            tracker_comments.added_comments.append(
                TrackerIssueComment(
                    created_at=self._parse_date(
                        date=gitlab_comment.created_at,
                    ),
                    author=gitlab_comment.author.get('name', self._default_author_name),
                    comment_id=str(gitlab_comment.id),
                    body=gitlab_comment.body,
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
        """
        Test the client.

        Raises:
            GitLabTrackerClientError: if the test failed
        """
        try:
            self._gitlab.auth()
        except GitlabError as e:
            raise GitLabTrackerClientError('Unable to log in with GitLab API client') from e

    def _get_gitlab_project(
        self,
    ) -> Project:
        try:
            return self._gitlab.projects.get(
                self.configuration.project,
            )
        except GitlabError as e:
            raise GitLabTrackerClientError(
                f'Unable to get GitLab project {self.configuration.project}',
            ) from e

    def _get_gitlab_issue(
        self,
        issue_id: str,
    ) -> Optional[ProjectIssue]:
        gitlab_project = self._get_gitlab_project()
        try:
            gitlab_issues = gitlab_project.issues.list(all=False, as_list=False)
        except GitlabError as e:
            raise GitLabTrackerClientError(
                f'Unable to get GitLab issues for project {self.configuration.project}',
            ) from e
        issue_id_int = int(issue_id)
        for gitlab_issue in gitlab_issues:
            if gitlab_issue.id == issue_id_int:
                return gitlab_issue
        return None

    def _replace_attachments_references(
        self,
        uploads: List[Tuple[Attachment, str]],
        referencing_texts: List[str],
    ) -> List[str]:
        for attachment, upload_url in uploads:
            referencing_texts = [
                text.replace(
                    attachment.url,
                    f'{self.configuration.url}/{self.configuration.project}{upload_url}',
                )
                for text in referencing_texts
            ]
        return referencing_texts

    def _upload_attachments(
        self,
        gitlab_project: Project,
        attachments: List[Attachment],
    ) -> List[Tuple[Attachment, str]]:
        try:
            return [
                (
                    attachment,
                    gitlab_project.upload(attachment.original_name, attachment.data)['url'],
                )
                for attachment in attachments
            ]
        except GitlabError as e:
            raise GitLabTrackerClientError(
                f'Unable to upload attachments for project {self.configuration.project} to GitLab',
            ) from e

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

    def _create_issue(
        self,
        gitlab_project: Project,
        title: str,
        description: str,
        confidential: bool,
    ) -> ProjectIssue:
        issue_data = {
            'title': title,
            'description': description,
            'confidential': confidential,
        }
        try:
            return gitlab_project.issues.create(issue_data)
        except GitlabError as e:
            raise GitLabTrackerClientError(
                f'Unable to create issue for project {self.configuration.project} to GitLab',
            ) from e

    def _add_comment(
        self,
        gitlab_project: Project,
        gitlab_issue: ProjectIssue,
        log: Log,
    ) -> ProjectIssueNote:
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
                '<p>This comment is too large to fit into a GitLab comment. '
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
        comment_body, external_body = self._replace_attachments_references(
            uploads=self._upload_attachments(
                gitlab_project=gitlab_project,
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
                    gitlab_project=gitlab_project,
                    attachments=[
                        body_attachment,
                    ],
                ),
                referencing_texts=[
                    comment_body,
                ],
            )[0]
        try:
            return gitlab_issue.notes.create({
                'body': comment_body,
            })
        except GitlabError as e:
            raise GitLabTrackerClientError(
                f'Unable to add GitLab comment for issue {gitlab_issue} in project {self.configuration.project}',
            ) from e

    def _ensure_auth(
        self,
    ) -> None:
        try:
            self._gitlab.auth()
        except GitlabError as e:
            raise GitLabTrackerClientError('Unable to authenticate to GitLab') from e
