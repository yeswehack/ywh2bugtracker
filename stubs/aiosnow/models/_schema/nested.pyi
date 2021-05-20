from typing import Any

import marshmallow


class Nested(marshmallow.fields.Nested):
    def __init__(self, parent_name: str, nested_cls: type, *args: Any, **kwargs: Any) -> None: ...
