from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
    Type,
)

import marshmallow


class ModelSchemaMeta(marshmallow.schema.SchemaMeta):
    def __new__(mcs: Any, name: str, bases: Tuple[Type[Any], ...], attrs: Dict[str, Any]) -> Any: ...


class ModelSchema(marshmallow.Schema, metaclass=ModelSchemaMeta):
    fields: Dict[str, Any]
    nested_fields: Dict[str, Any]

    def load_content(self, *args: Any, **kwargs: Any) -> Dict[str, Any]: ...

    def loads(self, *args: Any, **kwargs: Any) -> Dict[str, Any]: ...

    def dumps(self, obj: Any, *args: Any, many: Optional[bool] = ..., **kwargs: Any) -> str: ...
