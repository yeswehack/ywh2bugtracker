from typing import (
    Any,
    Union,
)


class Condition:
    operand_left: Any = ...
    operand_right: Any = ...
    operator_conditional: Any = ...
    operator_logical: str = ...
    registry: Any = ...

    def __init__(self, key: str, operator: str, value: Union[str, int, None]) -> None: ...

    def serialize(self, cond: Condition = ...) -> str: ...

    def serialize_registry(self) -> str: ...

    def __and__(self, next_cond: Condition) -> Condition: ...

    def __or__(self, next_cond: Condition) -> Condition: ...

    def __xor__(self, next_cond: Condition) -> Condition: ...
