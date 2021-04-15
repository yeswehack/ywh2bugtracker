"""Functions and models used in validators."""
import re
from collections.abc import Sized
from typing import (
    Any,
    Dict,
    TypeVar,
)

from typing_extensions import Protocol


class ValidatorError(Exception):
    """A class representing a validator error."""


T = TypeVar('T', contravariant=True)


class ValidatorProtocol(Protocol[T]):
    """Protocol for validators."""

    def __call__(
        self,
        value: T,
    ) -> None:
        """
        Validate the given value.

        Args:
            value: the value to be validated
        """
        ...  # noqa: WPS428


url_validator_regex = re.compile(
    '^(?:http|ftp)s?://' +  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' +  # domain...
    'localhost|' +  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' +  # ...or ip
    r'(?::\d+)?' +  # optional port
    r'(?:/?|[/?]\S+)$',
    re.IGNORECASE,
)

host_validator_regex = re.compile(
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' +  # domain...
    'localhost|' +  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' +  # ...or ip
    r'(?::\d+)?$', +  # optional port
    re.IGNORECASE,
)


def url_validator(
    value: str,
) -> None:
    """
    Validate an URL.

    Args:
        value: the URL to be validated

    Raises:
        ValidatorError: if the URL is invalid
    """
    matches = re.match(
        pattern=url_validator_regex,
        string=value,
    )
    if not matches:
        raise ValidatorError(f'{repr(value)} is not a valid url')


def host_validator(
    value: str,
) -> None:
    """
    Validate a Host.

    Args:
        value: the Host to be validated

    Raises:
        ValidatorError: if the Host is invalid
    """
    matches = re.match(
        pattern=host_validator_regex,
        string=value,
    )
    if not matches:
        raise ValidatorError(f'{repr(value)} is not a valid host')


def not_empty_validator(
    value: Any,
) -> None:
    """
    Validate the emptiness.

    Args:
        value: the value to be validated

    Raises:
        ValidatorError: if the value is empty
    """
    if value is not False and not value:
        raise ValidatorError(f'{repr(value)} is empty')


def length_one_validator(
    value: Any,
) -> None:
    """
    Validate that the value has a length of 1.

    Args:
        value: the value to be validated

    Raises:
        ValidatorError: if the value does not have a length of one
    """
    if not isinstance(value, Sized):
        raise ValidatorError(f'{repr(value)} does not have a length')
    length = len(value)
    if length != 1:
        raise ValidatorError(f'{repr(value)} does not have a length of one (length={length})')


def not_blank_validator(
    value: str,
) -> None:
    """
    Validate that the value is not a blank string (only whitespaces).

    Args:
        value: the value to be validated

    Raises:
        ValidatorError: if the value is blank
    """
    if not value.strip():
        raise ValidatorError(f'{repr(value)} is blank')


def dict_has_non_blank_key_validator(
    key: str,
) -> ValidatorProtocol[Dict[Any, Any]]:
    """
    Create a validator that validate that the key exists in the dict and its value is not blank.

    Args:
        key: a key to be validated

    Returns:
        a validator
    """

    def validator(  # noqa: WPS430
        value: Dict[Any, Any],
    ) -> None:
        key_value = value.get(key, '')
        if not isinstance(key_value, str) or not key_value.strip():
            raise ValidatorError(f'{repr(value)} must contain non-blank string key {repr(key)}')

    return validator
