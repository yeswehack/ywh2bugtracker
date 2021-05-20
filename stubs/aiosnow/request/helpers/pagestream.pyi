from typing import (
    Any,
    AsyncGenerator,
)

from aiosnow.request import GetRequest as GetRequest


class Pagestream(GetRequest):
    exhausted: bool = ...

    def __init__(self, *args: Any, page_size: int = ..., **kwargs: Any) -> None: ...

    async def get_next(self, **kwargs: Any) -> AsyncGenerator[Any, Any]: ...
