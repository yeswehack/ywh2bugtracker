"""Models for errors."""
from typing import Any, Dict

from ywh2bt.core.exceptions import CoreException


class BaseAttributeError(CoreException):
    """A class representing a base attribute error."""

    message: str
    context: Any

    def __init__(
        self,
        message: str,
        context: Any,
    ):
        """
        Initialize the error.

        Args:
            message: a message
            context: a context in which the error occurred
        """
        super().__init__(message)
        self.message = message
        self.context = context

    def __repr__(self) -> str:
        """
        Is called by the `repr()` built-in function to compute the "official" string representation.

        Returns:
            The string representation
        """
        message_repr = repr(self.message)
        context_repr = repr(self.context)
        return f'{self.__class__.__name__}({message_repr}, context={context_repr})'


class MissingAttributeError(BaseAttributeError):
    """A class representing a missing attribute error."""


class InvalidAttributeError(BaseAttributeError):
    """A class representing an invalid attribute error."""


class UnsupportedAttributeError(BaseAttributeError):
    """A class representing an extra attribute error."""

    extra: Dict[str, Any]


class AttributesError(BaseAttributeError):
    """A class representing a list of attribute errors."""

    message: str
    errors: Dict[str, BaseAttributeError]

    def __init__(
        self,
        message: str,
        errors: Dict[str, BaseAttributeError],
        context: Any,
    ):
        """
        Initialize the error.

        Args:
            message: a message
            errors: a list of errors
            context: a context in which the error occurred
        """
        super().__init__(
            message=message,
            context=context,
        )
        self.message = message
        self.errors = errors

    def __repr__(self) -> str:
        """
        Is called by the `repr()` built-in function to compute the "official" string representation.

        Returns:
            The string representation
        """
        message_repr = repr(self.message)
        errors_repr = repr(self.errors)
        return f'{self.__class__.__name__}({message_repr}, errors={errors_repr})'

    def __str__(self) -> str:
        """
        Get the string value.

        Is called by `str(object)` and the built-in functions `format()` and `print()`
        to compute the "informal" or nicely printable string representation.

        Returns:
            The string value
        """
        return f'{self.message}'
