from typing import (
    Any,
    Union,
)

from aiosnow.client import Client as Client
from aiosnow.models.attachment.file import FileHandler as FileHandler
from aiosnow.query import (
    Condition as Condition,
    Selector as Selector,
)
from aiosnow.request import Response as Response

from .._base.table import BaseTableModel as BaseTableModel


class TableModel(BaseTableModel):
    def __init__(self, client: Client, attachment: bool = ..., **kwargs: Any) -> None: ...

    async def upload_file(self, selection: Union[Selector, Condition, str], path: str) -> Response: ...

    async def download_file(self, selection: Union[Selector, Condition, str], dst_dir: str = ...) -> FileHandler: ...

    async def get_attachments(self, selection: Union[Selector, Condition, str] = ..., **kwargs: Any) -> Response: ...

    async def get_attachment(self, selection: Union[Selector, Condition, str] = ..., **kwargs: Any) -> Response: ...
