"""Models and functions used for representing states."""

from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Any,
    Dict,
)


class State(ABC):
    """A state."""

    @abstractmethod
    def as_dict(self) -> Dict[str, Any]:
        """Get the fields as a new dict."""
