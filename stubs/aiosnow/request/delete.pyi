from typing import Any

from .base import BaseRequest as BaseRequest


class DeleteRequest(BaseRequest):
    object_id: Any = ...

    def __init__(self, *args: Any, object_id: str, **kwargs: Any) -> None: ...

    async def send(self, *args: Any, **kwargs: Any) -> Any: ...
