from dataclasses import dataclass
from typing import (
    Any,
    List,
)


@dataclass
class BusinessUnit:

    programs: List[Any]
    name: str
    slug: str
