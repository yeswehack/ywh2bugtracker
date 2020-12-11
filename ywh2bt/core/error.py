"""Error related models and functions."""
import sys
import traceback
from io import StringIO
from typing import List, Optional, TextIO

from ywh2bt.core.configuration.error import (
    AttributesError,
    BaseAttributeError,
    InvalidAttributeError,
    MissingAttributeError,
    UnsupportedAttributeError,
)
from ywh2bt.core.configuration.subtypable import SubtypeError
from ywh2bt.core.core import write_message


def print_error_message(
    message: str,
    stream: Optional[TextIO] = None,
    end: str = '\n',
) -> None:
    """
    Print a message on STDERR.

    Args:
        message: a message
        stream: a stream to write the message to
        end: a string appended after the message, default a newline
    """
    if not stream:
        stream = sys.stderr
    write_message(
        stream=stream,
        message=message,
        end=end,
    )


def print_error(
    error: Exception,
    stream: Optional[TextIO] = None,
) -> None:
    """
    Print an error on STDERR.

    Args:
        error: an error
        stream: a stream to write the error to
    """
    if not stream:
        stream = sys.stderr
    print_error_message(
        stream=stream,
        message=_format_error(
            error=error,
        ),
    )


def error_to_string(
    error: Exception,
) -> str:
    """
    Get the full string representation of an error.

    Args:
        error: an error

    Returns:
        The string representation
    """
    error_stream = StringIO()
    print_error(
        stream=error_stream,
        error=error,
    )
    return error_stream.getvalue()


def _format_error(
    error: Exception,
) -> str:
    return '\n'.join(
        _get_formatted_error_items(
            error=error,
        ),
    )


def _get_formatted_error_items(
    error: Exception,
) -> List[str]:
    info = _extract_file_info(
        error=error,
    )
    class_name = error.__class__.__name__
    items = [f'{class_name}: {error} ({info})']
    if isinstance(error, BaseAttributeError):
        items.extend(_get_formatted_attribute_error_items(
            error=error,
        ))
    cause = getattr(error, '__cause__')  # noqa: B009
    if cause:
        cause_items = _get_formatted_error_items(
            error=cause,
        )
        items.extend(f'  {item}' for item in cause_items)
    return items


def _extract_file_info(
    error: Exception,
) -> str:
    if not hasattr(error, '__traceback__'):  # noqa: B009, WPS421
        return '?:?'
    tb = getattr(error, '__traceback__')  # noqa: B009
    stack_summary: traceback.StackSummary = traceback.extract_tb(tb)
    if stack_summary:
        frame_summary: traceback.FrameSummary = stack_summary[0]
        return f'{frame_summary.filename}:{frame_summary.lineno}'
    return '?:?'


def _get_formatted_attribute_error_items(
    error: BaseAttributeError,
) -> List[str]:
    if isinstance(error, AttributesError):
        return _get_formatted_attributes_error_items(
            error=error,
        )
    elif isinstance(error, (InvalidAttributeError, MissingAttributeError, SubtypeError, UnsupportedAttributeError)):
        return []
    return [
        f'Nonformatted error {error.__class__.__name__}: {error}',
    ]


def _get_formatted_attributes_error_items(
    error: AttributesError,
) -> List[str]:
    items = []
    for error_key, error_item in error.errors.items():
        formatted_item = _get_formatted_attribute_error_items(
            error=error_item,
        )
        items.append(f'  - {error_key}: {error_item}')
        items.extend(f'    {item}' for item in formatted_item)
    return items
