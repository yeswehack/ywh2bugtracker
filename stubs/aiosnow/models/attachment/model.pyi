from typing import (
    Any,
    Dict,
    Union,
)

from aiosnow.query import (
    Condition as Condition,
    Selector as Selector,
)
from aiosnow.request import Response as Response

from .file import FileHandler as FileHandler
from .schema import AttachmentModelSchema as AttachmentModelSchema
from .._base import BaseTableModel as BaseTableModel


class AttachmentModel(BaseTableModel, AttachmentModelSchema):
    io_pool_exc: Any = ...
    loop: Any = ...

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    async def create(self, payload: Dict[str, Any]) -> Response: ...

    async def update(self, selection: Union[Condition, str], payload: Dict[str, Any]) -> Response: ...

    async def download(self, selection: Union[Selector, Condition, str], dst_dir: str = ...) -> FileHandler: ...

    async def upload(self, table_name: str, record_sys_id: str, file_name: str, dir_name: str) -> Response: ...
