from aiosnow.query.condition import Condition as Condition

from .base import BaseQueryable as BaseQueryable


class BooleanQueryable(BaseQueryable):
    def is_true(self) -> Condition: ...

    def is_falsy(self) -> Condition: ...
