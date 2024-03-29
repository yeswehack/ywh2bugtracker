from aiosnow.query.condition import Condition as Condition

from .base import BaseQueryable as BaseQueryable


class IntegerQueryable(BaseQueryable):
    def equals(self, value: int) -> Condition: ...

    def not_equals(self, value: int) -> Condition: ...

    def less_than(self, value: int) -> Condition: ...

    def greater_than(self, value: int) -> Condition: ...

    def less_or_equals(self, value: int) -> Condition: ...

    def greater_or_equals(self, value: int) -> Condition: ...

    def between(self, value1: int, value2: int) -> Condition: ...
