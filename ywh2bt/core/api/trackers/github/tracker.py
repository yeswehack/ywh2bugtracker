"""Models and functions used for data synchronisation between YesWeHack and GitHub trackers."""
import os
import re
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
        body = self._message_formatter.format_report_description(
            report=report,
        )
        issue = self._create_issue(
            github_repository=repository,
            title=title,
            body=body,
        )
        self._upload_issue_attachments(
            issue=issue,
            attachments=report.attachments,
        )
        return self._build_tracker_issue(
            issue_id=str(issue.id),
            issue_url=issue.html_url,
            closed=False,
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
            self._upload_comment_attachments(
                issue=github_issue,
                comment=github_comment,
                attachments=log.attachments,
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
        )
        try:
            return github_issue.create_comment(
                body=comment_body,
            )
        except GithubException as e:
            raise GitHubTrackerClientError(
                f'Unable to add GitHub comment for issue {github_issue} in project {self.configuration.project}',
            ) from e

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

    def _upload_issue_attachments(
        self,
        issue: Issue,
        attachments: List[Attachment],
    ) -> None:
        body = self._upload_attachments(
            issue=issue,
            body=issue.body,
            attachments=attachments,
        )
        issue.edit(
            body=body,
        )

    def _upload_comment_attachments(
        self,
        issue: Issue,
        comment: IssueComment,
        attachments: List[Attachment],
    ) -> None:
        body = self._upload_attachments(
            issue=issue,
            body=comment.body,
            attachments=attachments,
        )
        comment.edit(
            body=body,
        )

    def _upload_attachments(
        self,
        issue: Issue,
        body: str,
        attachments: List[Attachment],
    ) -> str:
        for attachment in attachments:
            attachment_name = self._extract_attachment_name(
                body=body,
                attachment=attachment,
            )
            if self.configuration.github_cdn_on:
                url = self._attachment_uploader.upload_attachment(
                    issue=issue,
                    attachment=attachment,
                )
                if url:
                    body = body.replace(
                        attachment.url,
                        url,
                    )
                else:
                    substitution = f'(Attachment "{attachment_name}" not available due to upload error)'
                    body = self._substitute_attachment(
                        body=body,
                        attachment=attachment,
                        substitution=substitution,
                    )
            else:
                substitution = f'(Attachment "{attachment_name}" not available due to export script’s configuration)'
                body = self._substitute_attachment(
                    body=body,
                    attachment=attachment,
                    substitution=substitution,
                )
        return body

    def _extract_attachment_name(
        self,
        body: str,
        attachment: Attachment,
    ) -> str:
        attachment_name_regex = self._attachment_name_regex_template.substitute(
            url=re.escape(attachment.url),
        )
        matches = re.findall(
            attachment_name_regex,
            body,
        )
        if matches:
            return cast(str, matches[0])
        return attachment.original_name

    def _substitute_attachment(
        self,
        body: str,
        attachment: Attachment,
        substitution: str,
    ) -> str:
        attachment_substitute_regex = self._attachment_substitute_regex_template.substitute(
            url=re.escape(attachment.url),
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
