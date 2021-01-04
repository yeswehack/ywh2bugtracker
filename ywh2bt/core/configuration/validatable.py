"""Models and classes related to validatable objects."""
from abc import ABC, abstractmethod

from ywh2bt.core.exceptions import CoreException


class Validatable(ABC):
    """A class representing an object that can be validated."""

    @abstractmethod
    def validate(self) -> None:
        """Validate the object."""

    def is_valid(self) -> bool:
        """
        Check if the object is valid.

        Returns:
            a boolean indicating if the object is valid
        """
        try:
            self.validate()
        except CoreException:
            return False
        return True
