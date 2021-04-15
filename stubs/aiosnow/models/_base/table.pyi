from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Union,
)

from aiosnow.client import Client as Client
from aiosnow.query import (
    Condition as Condition,
    Selector as Selector,
)
from aiosnow.request import Response as Response

from .._base.model import BaseModel as BaseModel


class BaseTableModel(BaseModel):
    def __init__(self, client: Client, table_name: str = ..., return_only: List[str] = ...) -> None: ...

    async def stream(
        self, selection: Union[Selector, Condition, str] = ..., **kwargs: Any,
    ) -> AsyncGenerator[Any, Any]: ...

    async def get(self, selection: Union[Selector, Condition, str] = ..., **kwargs: Any) -> Response: ...

    async def get_one(self, selection: Union[Selector, Condition, str] = ..., **kwargs: Any) -> Response: ...

    async def get_object_id(self, value: Union[Selector, Condition, str]) -> str: ...

    async def update(self, selection: Union[Condition, str], payload: Dict[str, Any]) -> Response: ...

    async def create(self, payload: Dict[str, Any]) -> Response: ...

    async def delete(self, selection: Union[Condition, str]) -> Response: ...
