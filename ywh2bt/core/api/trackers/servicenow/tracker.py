"""Models and functions used for data synchronisation between YesWeHack and ServiceNow trackers."""
import asyncio
import datetime
import re
from abc import ABC
from dataclasses import dataclass
from typing import (
    Any,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

from aiosnow import (
    Client,
    select,
)
from aiosnow.exceptions import AiosnowException
from aiosnow.models.table.declared import (
    IncidentModel,
    JournalModel,
)

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
from ywh2bt.core.api.trackers.servicenow.formatter import ServiceNowReportMessageFormatter
from ywh2bt.core.api.trackers.servicenow.model import (
    InMemoryAttachmentModel,
    Record,
    UserModel,
)
from ywh2bt.core.configuration.trackers.servicenow import ServiceNowConfiguration

_RE_INLINE_ATTACHMENT = re.compile(pattern=r'(!?\[([^\]]+)]\(([^)]+)\))')

_MODEL_NOT_EQUALS_LIMIT = 100


class ServiceNowTrackerClientError(TrackerClientError):
    """A ServiceNow tracker client error."""


class ServiceNowAsyncTrackerClient:
    """A ServiceNow async tracker client."""

    _configuration: ServiceNowConfiguration
    _servicenow_client: Client
    _message_formatter: ServiceNowReportMessageFormatter

    _incident_attachment_prefix: str = 'incident_'
    _comment_attachment_prefix: str = 'comment_'

    def __init__(
        self,
        configuration: ServiceNowConfiguration,
    ):
        """
        Initialize self.

        Args:
            configuration: a ServiceNow configuration
        """
        self._configuration = configuration
        self._servicenow_client = Client(
            address=cast(str, self._configuration.host),
            basic_auth=(
                cast(str, self._configuration.login),
                cast(str, self._configuration.password),
            ),
            use_ssl=cast(bool, self._configuration.use_ssl),
            verify_ssl=cast(bool, self._configuration.verify),
        )
        self._message_formatter = ServiceNowReportMessageFormatter()

    def _build_tracker_issue(
        self,
        issue_id: str,
        issue_url: str,
        closed: bool,
    ) -> TrackerIssue:
        return TrackerIssue(
            tracker_url=f'https://{cast(str, self._configuration.host)}',
            project=cast(str, self._configuration.host),
            issue_id=issue_id,
            issue_url=issue_url,
            closed=closed,
        )

    def _build_incident_url(
        self,
        sys_id: str,
    ) -> str:
        host = cast(str, self._configuration.host)
        return f'https://{host}/nav_to.do?uri=%2Fincident.do%3Fsys_id%3D{sys_id}'  # noqa: WPS323

    async def get_tracker_issue(
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
        incident_data = await self._get_servicenow_incident(
            incident_id=issue_id,
        )
        if incident_data is None:
            return None
        issue_url = self._build_incident_url(
            sys_id=incident_data['sys_id'],
        )
        return self._build_tracker_issue(
            issue_id=issue_id,
            issue_url=issue_url,
            closed=incident_data['state'].value.lower() == 'closed',
        )

    async def _get_servicenow_incident(
        self,
        incident_id: str,
    ) -> Optional[Record]:
        async with IncidentModel(
            self._servicenow_client,
            table_name='incident',
        ) as incident_model:
            try:
                incident_response = await incident_model.get_one(IncidentModel.sys_id == incident_id)
            except AiosnowException:
                return None
        return _as_dict(incident_response.data)

    async def get_tracker_issue_comments(
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
        incident_data = await self._get_servicenow_incident(
            incident_id=issue_id,
        )
        if incident_data is None:
            return []
        incident_sys_id = cast(str, incident_data['sys_id'])
        wrapped_items: List[RecordWrapper] = []
        wrapped_items += map(
            CommentRecordWrapper, await self._get_incident_journal_comments(
                incident_sys_id=incident_sys_id,
                exclude_comments=exclude_comments,
            ),
        )
        wrapped_items += map(
            AttachmentRecordWrapper, await self._get_incident_attachments(
                incident_sys_id=incident_sys_id,
                exclude_comments=exclude_comments,
            ),
        )
        wrapped_items = sorted(wrapped_items, key=_sort_key_wrapped_sys_created_on)
        comments = []
        for wrapped_item in wrapped_items:
            if isinstance(wrapped_item, CommentRecordWrapper):
                comments.append(
                    self._extract_comment(
                        comment_data=wrapped_item.data,
                    ),
                )
            elif isinstance(wrapped_item, AttachmentRecordWrapper):
                comments.append(
                    await self._extract_attachment(
                        attachment_data=wrapped_item.data,
                    ),
                )
        return comments

    def _exclude_from_list(
        self,
        records: List[Record],
        record_property: str,
        exclude: Set[str],
    ) -> List[Record]:
        return list(
            filter(
                lambda record: record[record_property] not in exclude,
                records,
            ),
        )

    async def _get_incident_journal_comments(
        self,
        incident_sys_id: str,
        exclude_comments: Optional[List[str]] = None,
    ) -> List[Record]:
        journal_condition = JournalModel.element_id.equals(incident_sys_id)
        journal_condition &= JournalModel.element.equals('comments')
        # limited pre-filter on query because API url might be too long
        for exclude_comment in (exclude_comments or [])[:_MODEL_NOT_EQUALS_LIMIT]:
            journal_condition &= JournalModel.sys_id.not_equals(exclude_comment)
        journal_query = select(journal_condition).order_asc(JournalModel.sys_created_on)
        async with JournalModel(
            self._servicenow_client,
            table_name='sys_journal_field',
        ) as journal_model:
            try:
                records = list(cast(Iterable[Record], await journal_model.get(journal_query)))
            except AiosnowException as journal_exception:
                raise ServiceNowTrackerClientError(
                    f'Unable to get journal comments for incident {incident_sys_id}',
                ) from journal_exception
        return self._exclude_from_list(
            records=records,
            record_property='sys_id',
            exclude=set(exclude_comments or []),
        )

    async def _get_incident_attachments(
        self,
        incident_sys_id: str,
        exclude_comments: Optional[List[str]] = None,
    ) -> List[Record]:
        attachment_condition = InMemoryAttachmentModel.table_name.equals('incident')
        attachment_condition &= InMemoryAttachmentModel.table_sys_id.equals(incident_sys_id)
        # limited pre-filter on query because API url might be too long
        for exclude_comment in (exclude_comments or [])[:_MODEL_NOT_EQUALS_LIMIT]:
            attachment_condition &= JournalModel.sys_id.not_equals(exclude_comment)
        attachment_query = select(attachment_condition).order_asc(InMemoryAttachmentModel.sys_created_on)
        async with InMemoryAttachmentModel(
            self._servicenow_client,
            table_name='incident',
        ) as attachment_model:
            try:
                records = list(cast(Iterable[Record], await attachment_model.get(attachment_query)))
            except AiosnowException as attachment_exception:
                raise ServiceNowTrackerClientError(
                    f'Unable to get attachments for incident {incident_sys_id}',
                ) from attachment_exception
        return self._exclude_from_list(
            records=records,
            record_property='sys_id',
            exclude=set(exclude_comments or []),
        )

    def _extract_comment(
        self,
        comment_data: Record,
    ) -> TrackerIssueComment:
        return TrackerIssueComment(
            created_at=comment_data['sys_created_on'],
            author=comment_data['sys_created_by'],
            comment_id=comment_data['sys_id'],
            body=comment_data['value'],
            attachments={},
        )

    async def _extract_attachment(
        self,
        attachment_data: Record,
    ) -> TrackerIssueComment:
        async with InMemoryAttachmentModel(
            self._servicenow_client,
            table_name='incident',
        ) as attachment_model:
            try:
                attachment_content = await attachment_model.download(
                    InMemoryAttachmentModel.sys_id == cast(str, attachment_data['sys_id']),
                )
            except AiosnowException as attachment_exception:
                raise ServiceNowTrackerClientError(
                    f'Unable to download attachment for incident {attachment_data["sys_id"]}',
                ) from attachment_exception
        file_name = cast(str, attachment_data['file_name'])
        return TrackerIssueComment(
            created_at=attachment_data['sys_created_on'],
            author=attachment_data['sys_created_by'],
            comment_id=attachment_data['sys_id'],
            body=f'Attachment:\n![{file_name}]({file_name})',
            attachments={
                file_name: TrackerAttachment(
                    filename=file_name,
                    mime_type=cast(str, attachment_data['content_type']),
                    content=attachment_content,
                ),
            },
        )

    async def send_report(
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
        short_description = self._message_formatter.format_report_title(
            report=report,
        )
        description = self._replace_inline_attachments(
            attachments=report.attachments,
            content=self._message_formatter.format_report_description(
                report=report,
            ),
            file_name_prefix=self._incident_attachment_prefix,
        )
        incident_data = await self._create_incident(
            short_description=short_description,
            description=description,
        )
        sys_id = incident_data['sys_id']
        await self._upload_attachments(
            attachments=report.attachments,
            file_name_prefix=self._incident_attachment_prefix,
            table_name='incident',
            record_sys_id=sys_id,
        )
        issue_url = self._build_incident_url(
            sys_id=sys_id,
        )
        return self._build_tracker_issue(
            issue_id=sys_id,
            issue_url=issue_url,
            closed=False,
        )

    async def _create_incident(
        self,
        short_description: str,
        description: str,
    ) -> Record:
        async with IncidentModel(
            self._servicenow_client,
            table_name='incident',
        ) as incident_model:
            try:
                incident_response = await incident_model.create(
                    {
                        'description': description,
                        'short_description': short_description,
                    },
                )
            except AiosnowException as incident_create_exception:
                raise ServiceNowTrackerClientError('Unable to create incident') from incident_create_exception
        return _as_dict(incident_response.data)

    async def _upload_attachments(
        self,
        attachments: List[Attachment],
        file_name_prefix: str,
        table_name: str,
        record_sys_id: str,
    ) -> List[Tuple[str, str]]:
        uploaded_attachments = []
        host = cast(str, self._configuration.host)
        try:
            async with InMemoryAttachmentModel(
                self._servicenow_client,
                table_name=table_name,
            ) as attachment_model:
                for attachment in attachments:
                    attachment_response = await attachment_model.upload(
                        table_name=table_name,
                        record_sys_id=record_sys_id,
                        file_name=f'{file_name_prefix}{attachment.original_name}',
                        content_type=attachment.mime_type,
                        content=attachment.data,
                    )
                    sys_id = _as_dict(attachment_response.data)['sys_id']
                    view_url = f'https://{host}/sys_attachment.do?view=false&sys_id={sys_id}'
                    uploaded_attachments.append(
                        (
                            attachment.url,
                            view_url,
                        ),
                    )
        except AiosnowException as attachment_upload_exception:
            raise ServiceNowTrackerClientError(
                f'Unable to upload attachments to {table_name}',
            ) from attachment_upload_exception
        return uploaded_attachments

    async def send_logs(
        self,
        tracker_issue: TrackerIssue,
        logs: List[Log],
    ) -> SendLogsResult:
        """
        Send logs to the tracker.

        Args:
            tracker_issue: information about the tracker issue
            logs: a list of comments

        Raises:
            ServiceNowTrackerClientError: if an error occurs

        Returns:
            information about the sent comments
        """
        data = _as_optional_dict(
            await self._get_servicenow_incident(
                incident_id=tracker_issue.issue_id,
            ),
        )
        if data is None:
            raise ServiceNowTrackerClientError(
                f'ServiceNow incident {tracker_issue.issue_id} not found',
            )
        incident_data = data
        tracker_comments = SendLogsResult(
            tracker_issue=tracker_issue,
            added_comments=[],
        )
        if incident_data['state'].value.lower() == 'closed':
            return tracker_comments
        incident_id = cast(str, incident_data['sys_id'])
        for log in logs:
            comment = self._message_formatter.format_log(
                log=log,
            )
            comment = self._replace_inline_attachments(
                attachments=log.attachments,
                content=comment,
                file_name_prefix=self._comment_attachment_prefix,
            )
            async with IncidentModel(
                self._servicenow_client,
                table_name='incident',
            ) as incident_model:
                try:
                    await incident_model.update(
                        IncidentModel.sys_id == incident_id,
                        {
                            'comments': comment,
                        },
                    )
                except AiosnowException as incident_update_exception:
                    raise ServiceNowTrackerClientError(
                        f'Unable to add comment to incident number {incident_data["number"]}',
                    ) from incident_update_exception
            comment_data = await self._get_incident_comment_id(
                incident_id=incident_id,
                comment=comment,
            )
            await self._upload_attachments(
                attachments=log.attachments,
                file_name_prefix=self._comment_attachment_prefix,
                table_name='incident',
                record_sys_id=incident_data['sys_id'],
            )
            tracker_comments.added_comments.append(
                TrackerIssueComment(
                    created_at=comment_data['sys_created_on'],
                    author=comment_data['sys_created_by'],
                    comment_id=comment_data['sys_id'],
                    body=comment,
                    attachments={},
                ),
            )
        return tracker_comments

    def _replace_inline_attachments(
        self,
        attachments: List[Attachment],
        content: str,
        file_name_prefix: str,
    ) -> str:
        attachment_urls = {attachment.url for attachment in attachments}
        inline_attachments = _RE_INLINE_ATTACHMENT.findall(content)
        for match, attachment_name, url in inline_attachments:
            if url in attachment_urls:
                content = content.replace(match, f'[See attachment "{file_name_prefix}{attachment_name}"]')
        return content

    async def _get_incident_comment_id(
        self,
        incident_id: str,
        comment: str,
    ) -> Record:
        async with JournalModel(
            self._servicenow_client,
            table_name='sys_journal_field',
        ) as journal_model:
            condition = JournalModel.element_id.equals(incident_id)
            condition &= JournalModel.element.equals('comments')
            condition &= JournalModel.value.equals(
                self._escape_query_term_separator(
                    term=comment,
                ),
            )
            try:
                journal_response = await journal_model.get_one(condition)
            except AiosnowException as journal_comment_exception:
                raise ServiceNowTrackerClientError(
                    f'Unable to get comment from incident {incident_id}',
                ) from journal_comment_exception
            return _as_dict(journal_response.data)

    async def test(
        self,
    ) -> None:
        """
        Test the client.

        Raises:
            ServiceNowTrackerClientError: if the test failed
        """
        # The query itself does not really matter, we only want to be sure that we can perform a query.
        # If the credentials are not valid, the query will fail.
        async with UserModel(
            self._servicenow_client,
            table_name='sys_user',
        ) as user_model:
            try:
                await user_model.get_one(UserModel.user_name == self._configuration.login)
            except AiosnowException as user_exception:
                raise ServiceNowTrackerClientError('User not found') from user_exception

    def _escape_query_term_separator(
        self,
        term: str,
    ) -> str:
        return term.replace('^', '^^')


class ServiceNowTrackerClient(TrackerClient[ServiceNowConfiguration]):
    """A ServiceNow tracker client wrapping an async client."""

    _async_client: ServiceNowAsyncTrackerClient

    def __init__(
        self,
        configuration: ServiceNowConfiguration,
    ):
        """
        Initialize self.

        Args:
            configuration: a ServiceNow configuration
        """
        super().__init__(
            configuration=configuration,
        )
        self._async_client = ServiceNowAsyncTrackerClient(
            configuration=configuration,
        )

    @property
    def tracker_type(
        self,
    ) -> str:
        """
        Get the type of the tracker client.

        Returns:
            the type of the tracker client
        """
        return 'ServiceNow'

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
        return asyncio.run(
            self._async_client.get_tracker_issue(
                issue_id=issue_id,
            ),
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
        return asyncio.run(
            self._async_client.get_tracker_issue_comments(
                issue_id=issue_id,
                exclude_comments=exclude_comments,
            ),
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
        return asyncio.run(
            self._async_client.send_report(
                report=report,
            ),
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
            logs: a list of comments

        Returns:
            information about the sent comments
        """
        return asyncio.run(
            self._async_client.send_logs(
                tracker_issue=tracker_issue,
                logs=logs,
            ),
        )

    def test(
        self,
    ) -> None:
        """Test the client."""
        asyncio.run(self._async_client.test())


@dataclass
class RecordWrapper(ABC):
    """A wrapper for records."""

    data: Record


@dataclass
class CommentRecordWrapper(RecordWrapper):
    """A wrapper for comment records."""


@dataclass
class AttachmentRecordWrapper(RecordWrapper):
    """A wrapper for attachment records."""


def _sort_key_wrapped_sys_created_on(
    wrapped: RecordWrapper,
) -> datetime.datetime:
    return cast(datetime.datetime, wrapped.data['sys_created_on'])


ResponseDataType = Union[List[Any], Record, bytes]


def _as_optional_dict(data: Optional[ResponseDataType]) -> Optional[Record]:
    if data is not None and not isinstance(data, dict):
        raise ServiceNowTrackerClientError(f'Expecting dict, got {type(data)}')
    return data


def _as_dict(data: Optional[ResponseDataType]) -> Record:
    if not isinstance(data, dict):
        raise ServiceNowTrackerClientError(f'Expecting non-empty dict, got {type(data)}')
    return data
