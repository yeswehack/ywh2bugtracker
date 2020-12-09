"""Models and functions related to tabs (tab-widget, ...)."""
from typing import Any, Optional

from ywh2bt.core.configuration.yeswehack import Program


def object_to_tab_title(
    obj: Any,
) -> Optional[str]:
    """
    Extract from the given object a string to be used a tab title.

    Args:
        obj: an object

    Returns:
        The title if it could have been extracted; otherwise None
    """
    if isinstance(obj, Program):
        return obj.slug
    return None
