"""Models and classes related to exportable objects."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')


class Exportable(Generic[T], ABC):
    """A class representing an object that can be exported."""

    @abstractmethod
    def export(self) -> T:
        """Export the object."""
