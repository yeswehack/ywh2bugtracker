from typing import Any


class Selector:
    sysparms: str = ...

    def __init__(self, sysparms: str) -> None: ...

    def order_desc(self, value: Any) -> Selector: ...

    def order_asc(self, value: Any) -> Selector: ...
