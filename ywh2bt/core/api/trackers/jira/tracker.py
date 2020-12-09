"""Models and functions used for data synchronisation between YesWeHack and Jira trackers."""
from typing import Any, List, Optional, Tuple, cast
from urllib.parse import quote

from jira import Comment as JIRAComment, Issue as JIRAIssue, JIRA, JIRAError  # type: ignore
from jira.utils import CaseInsensitiveDict  # type: ignore

from ywh2bt.core.api.models.report import Attachment, Log, Report
from ywh2bt.core.api.tracker import TrackerClient, TrackerClientError, TrackerComment, TrackerComments, TrackerIssue
from ywh2bt.core.api.trackers.jira.formatter import JiraReportMessageFormatter
from ywh2bt.core.configuration.trackers.jira import JiraConfiguration


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
            jira_issue = self._get_issue(
                issue_id=issue_id,
            )
        except JiraTrackerClientError:
            return None
        return self._build_tracker_issue(
            issue_id=issue_id,
            issue_url=jira_issue.permalink(),
            is_closed=all((
                jira_issue.fields.status is not None,
                jira_issue.fields.status.name == self.configuration.issue_closed_status,
            )),
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
        )
        jira_issue = self._create_issue(
            title=title,
            description=description,
        )
        uploads = self._upload_attachments(
            issue=jira_issue,
            attachments=report.attachments,
        )
        for attachment_url, uploaded_url in uploads:
            description = description.replace(
                attachment_url,
                uploaded_url,
            )
        jira_issue.update(
            description=description,
        )
        return self._build_tracker_issue(
            issue_id=jira_issue.key,
            issue_url=jira_issue.permalink(),
            is_closed=False,
        )

    def send_logs(
        self,
        tracker_issue: TrackerIssue,
        logs: List[Log],
    ) -> TrackerComments:
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
        tracker_comments = TrackerComments(
            tracker_issue=tracker_issue,
            added_comments=[],
        )
        for log in logs:
            jira_comment = self._add_comment(
                issue=jira_issue,
                log=log,
            )
            tracker_comments.added_comments.append(
                TrackerComment(
                    comment_id=jira_comment.id,
                ),
            )
        return tracker_comments

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
        )
        uploads = self._upload_attachments(
            issue=issue,
            attachments=log.attachments,
        )
        for attachment_url, uploaded_url in uploads:
            comment_body = comment_body.replace(
                attachment_url,
                uploaded_url,
            )
        try:
            return self._get_client().add_comment(
                issue=str(issue),
                body=comment_body,
            )
        except JIRAError as e:
            raise JiraTrackerClientError(
                f'Unable to add JIRA comment for issue {issue} in project {self.configuration.project}',
            ) from e

    def _upload_attachments(
        self,
        issue: JIRAIssue,
        attachments: List[Attachment],
    ) -> List[Tuple[str, str]]:
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
                    attachment.url,
                    issue_attachment_url,
                ),
            )
        return uploads

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
