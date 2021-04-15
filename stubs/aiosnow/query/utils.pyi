from typing import Union

from .condition import Condition as Condition
from .selector import Selector as Selector


def select(value: Union[Selector, Condition, str] = ...) -> Selector: ...
