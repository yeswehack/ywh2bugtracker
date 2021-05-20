from typing import (
    Any,
    Dict,
    List,
)

from .base import BaseRequest as BaseRequest


class GetRequest(BaseRequest):
    nested_fields: Any = ...
    query: Any = ...

    def __init__(self, *args: Any, nested_fields: Dict[str, Any] = ..., limit: int = ..., offset: int = ...,
                 query: str = ..., cache_secs: int = ..., **kwargs: Any) -> None: ...

    @property
    def offset(self) -> int: ...

    @property
    def limit(self) -> int: ...

    async def get_cached(self, url: str, fields: List[Any] = ...) -> Dict[str, Any]: ...

    async def send(self, *args: Any, **kwargs: Any) -> Any: ...

    @property
    def params(self) -> Dict[str, Any]: ...
