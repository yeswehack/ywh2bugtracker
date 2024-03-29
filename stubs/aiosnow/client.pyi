from typing import (
    Any,
    Tuple,
    Type,
    Union,
)

from aiohttp import ClientSession
from aiosnow.request import Response as Response


class Client:
    config: Any = ...
    session_cls: Any = ...
    response_cls: Any = ...
    base_url: Any = ...
    pool_size: Any = ...

    def __init__(self, address: Union[str, bytes], basic_auth: Tuple[str, str] = ..., use_ssl: bool = ...,
                 verify_ssl: bool = ..., pool_size: int = ..., response_cls: Type[Response] = ...,
                 session_cls: Type[ClientSession] = ...) -> None: ...

    def get_session(self) -> Any: ...
