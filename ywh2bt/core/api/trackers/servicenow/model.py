"""Models and functions used for data synchronisation between YesWeHack and ServiceNow trackers."""
from typing import (
    Any,
    Dict,
    Union,
)

from aiosnow import (
    Client,
    Selector,
    TableModel,
)
from aiosnow.models import BaseTableModel
from aiosnow.models._schema import fields  # noqa: WPS436
from aiosnow.models.attachment.schema import AttachmentModelSchema
from aiosnow.query import Condition
from aiosnow.request import (
    Response,
    methods,
)

Record = Dict[str, Any]


class UserModelSchema:
    """User API Schema."""

    sys_id = fields.String(is_primary=True)
    user_name = fields.String()


class UserModel(TableModel, UserModelSchema):
    """User API Model."""


class InMemoryAttachmentModel(BaseTableModel, AttachmentModelSchema):
    """Attachment API Model."""

    _client: Client

    async def create(self, payload: Record) -> Response:
        """
        Create a new record.

        Args:
            payload: New record payload

        Raises:
            AttributeError: always because this method is not supported on this object
        """
        raise AttributeError(
            "Attachment doesn't support create(), use upload() instead",
        )

    async def update(self, selection: Union[Condition, str], payload: Record) -> Response:
        """
        Update matching record.

        Args:
            selection: Condition or ID of object to update
            payload: Update payload

        Raises:
            AttributeError: always because this method is not supported on this object
        """
        raise AttributeError(
            "Attachment doesn't support update()",
        )

    @property
    def _api_url(self) -> str:
        return f'{self._client.base_url}/api/now/attachment'

    async def download(
        self,
        selection: Union[Selector, Condition, str],
    ) -> bytes:
        """
        Download file.

        Args:
            selection: Attachment selection

        Returns:
            The content of the attachment
        """
        meta = await self.get_one(selection)
        data = await self.request(
            methods.GET,
            url=meta['download_link'],
            resolve=False,
            decode=False,
        )
        return await data.read()

    async def upload(
        self,
        table_name: str,
        record_sys_id: str,
        file_name: str,
        content_type: str,
        content: bytes,
    ) -> Response:
        """
        Upload a file.

        Args:
            table_name: Table name, e.g. incident
            record_sys_id: Sys id of the record to attach to
            file_name: Source file name
            content_type: Content type
            content: Content

        Returns:
            ClientResponse
        """
        return await self.request(
            methods.POST,
            url=f'{self._api_url}/file',
            params={
                'table_name': table_name,
                'table_sys_id': record_sys_id,
                'file_name': file_name,
            },
            headers={
                'Content-type': content_type,
            },
            payload=content,
        )
