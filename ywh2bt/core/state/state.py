"""Models and functions used for representing states."""

from abc import ABC
from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class State(ABC):
    """A state."""

    def as_dict(self) -> Dict[str, Any]:
        """
        Get the fields a a new dict.

        Returns:
            a dict containing the fields values.
        """
        return asdict(self)
