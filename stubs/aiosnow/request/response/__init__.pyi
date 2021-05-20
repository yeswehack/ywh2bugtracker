from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Union,
)

from aiohttp import ClientResponse

from .schemas import ContentSchema as ContentSchema


class Response(ClientResponse):
    data: Optional[Union[List[Any], Dict[str, Any], bytes]] = ...

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def __getitem__(self, name: Any) -> Any: ...

    def __iter__(self) -> Iterable[Any]: ...

    def __len__(self) -> int: ...

    async def load_document(self) -> None: ...
