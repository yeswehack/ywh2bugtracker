from abc import ABC
from typing import (
    Any,
    Optional,
    Union,
)

import marshmallow

from .integer import Integer as Integer
from .string import String as String


class Mapping(ABC):
    key: Optional[Union[str, int]] = ...
    value: Optional[str] = ...


class StringMapping(Mapping):
    key: Any = ...
    value: Any = ...

    def __init__(self, key: str, value: str) -> None: ...


class IntegerMapping(Mapping):
    key: Any = ...
    value: Any = ...

    def __init__(self, key: int, value: str) -> None: ...


class MappedField(marshmallow.fields.Tuple):
    should_dump_text: Any = ...

    def __init__(self, *args: Any, dump_text: bool = ..., **kwargs: Any) -> None: ...


class IntegerMap(MappedField, Integer):

    def _serialize(self, value, attr, obj, **kwargs) -> Optional[str, int]:  # type: ignore
        ...

    def _deserialize(self, value, attr, data, **kwargs) -> Integer:  # type: ignore
        ...


class StringMap(MappedField, String):

    def _serialize(self, value, attr, obj, **kwargs) -> Optional[str]:  # type: ignore
        ...

    def _deserialize(self, value, attr, data, **kwargs) -> String:  # type: ignore
        ...
