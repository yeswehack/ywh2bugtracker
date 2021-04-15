import abc
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Any,
    Dict,
    Tuple,
)

from aiohttp import ClientSession as ClientSession

from .response import Response as Response


class BaseRequest(ABC, metaclass=abc.ABCMeta):
    session: ClientSession
    log: Any = ...
    api_url: Any = ...
    fields: Any = ...
    url_segments: Any = ...

    def __init__(self, api_url: str, session: ClientSession, fields: Dict[str, Any] = ...,
                 headers: Dict[str, Any] = ..., params: Dict[str, Any] = ..., resolve: bool = ...) -> None: ...

    @property
    def params(self) -> Dict[str, Any]: ...

    @property
    def url(self) -> str: ...

    @abstractmethod
    async def send(self, *args: Any, **kwargs: Any) -> Tuple[Response, Dict[str, Any]]: ...
