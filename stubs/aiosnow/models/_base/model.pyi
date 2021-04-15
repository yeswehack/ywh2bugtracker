from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Type,
    TypeVar,
)

from aiosnow.client import Client as Client
from aiosnow.request import Response as Response

from .._schema import ModelSchema as ModelSchema

req_cls_map: Any


class BaseModelMeta(type):
    def __new__(mcs: Any, name: str, bases: Tuple[Type[Any], ...], attrs: Dict[str, Any]) -> Any: ...

T = TypeVar('T', bound='BaseModel')

class BaseModel(metaclass=BaseModelMeta):
    schema_cls: Type[ModelSchema]
    schema: ModelSchema
    fields: Any = ...

    def __init__(self, client: Client) -> None: ...

    async def request(self, method: str, *args: Any, **kwargs: Any) -> Response: ...

    async def __aenter__(self: T) -> T: ...

    async def __aexit__(self, *_: List[Any]) -> None: ...
