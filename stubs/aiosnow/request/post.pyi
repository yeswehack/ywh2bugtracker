from typing import Any

from .base import BaseRequest as BaseRequest


class PostRequest(BaseRequest):
    payload: Any = ...

    def __init__(self, *args: Any, payload: str, **kwargs: Any) -> None: ...

    async def send(self, *args: Any, **kwargs: Any) -> Any: ...
