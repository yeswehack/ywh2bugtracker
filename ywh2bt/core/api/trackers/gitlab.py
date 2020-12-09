"""Models and functions used for data synchronisation between YesWeHack and GitLab trackers."""
from __future__ import annotations

from typing import Iterable, List, Optional, Tuple, cast

import requests
from gitlab import Gitlab, GitlabError  # type: ignore
from gitlab.v4.objects import Project, ProjectIssue, ProjectIssueNote  # type: ignore

from ywh2bt.core.api.formatter.markdown import ReportMessageMarkdownFormatter
from ywh2bt.core.api.models.report import Attachment, Log, Report
from ywh2bt.core.api.tracker import (
    TrackerClient,
    TrackerClientError,
    TrackerComment,
    TrackerComments,
    TrackerIssue,
)
from ywh2bt.core.configuration.trackers.gitlab import GitLabConfiguration


class GitLabTrackerClientError(TrackerClientError):
    """A GitLab tracker client error."""


class GitLabTrackerClient(TrackerClient[GitLabConfiguration]):
    """A GitLab tracker client."""

    _session: requests.Session
    _gitlab: Gitlab
    _message_formatter: ReportMessageMarkdownFormatter

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
        is_closed: bool,
    ) -> TrackerIssue:
        return TrackerIssue(
            tracker_url=cast(str, self.configuration.url),
            project=cast(str, self.configuration.project),
            issue_id=issue_id,
            issue_url=issue_url,
            is_closed=is_closed,
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
            is_closed=gitlab_issue.state == 'closed',
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
        description = self._message_formatter.format_report_description(
            report=report,
        )
        uploads = self._upload_attachments(
            gitlab_project=gitlab_project,
            attachments=report.attachments,
        )
        for attachment_url, uploaded_url in uploads:
            description = description.replace(
                attachment_url,
                uploaded_url,
            )
        gitlab_issue = self._create_issue(
            gitlab_project=gitlab_project,
            title=self._message_formatter.format_report_title(
                report=report,
            ),
            description=description,
        )
        return self._build_tracker_issue(
            issue_id=gitlab_issue.id,
            issue_url=gitlab_issue.web_url,
            is_closed=False,
        )

    def send_logs(
        self,
        tracker_issue: TrackerIssue,
        logs: Iterable[Log],
    ) -> TrackerComments:
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
        tracker_comments = TrackerComments(
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
                TrackerComment(
                    comment_id=gitlab_comment.id,
                ),
            )
        return tracker_comments

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

    def _upload_attachments(
        self,
        gitlab_project: Project,
        attachments: List[Attachment],
    ) -> List[Tuple[str, str]]:
        try:
            return [
                (
                    attachment.url,
                    gitlab_project.upload(attachment.original_name, attachment.data)['url'],
                )
                for attachment in attachments
            ]
        except GitlabError as e:
            raise GitLabTrackerClientError(
                f'Unable to upload attachments for project {self.configuration.project} to GitLab',
            ) from e

    def _create_issue(
        self,
        gitlab_project: Project,
        title: str,
        description: str,
    ) -> ProjectIssue:
        issue_data = {
            'title': title,
            'description': description,
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
        )
        uploads = self._upload_attachments(
            gitlab_project=gitlab_project,
            attachments=log.attachments,
        )
        for attachment_url, uploaded_url in uploads:
            comment_body = comment_body.replace(
                attachment_url,
                uploaded_url,
            )
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
