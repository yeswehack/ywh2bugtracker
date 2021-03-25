"""Models and functions used in markdown conversions."""
import re
from typing import Dict

from ywh2bt.core.api.models.report import Attachment

_RE_IMAGE = re.compile(pattern=r'\!\[([^\]]+)]\(([^)]+)\)')


def markdown_to_ywh(
    message: str,
    attachments: Dict[str, Attachment],
) -> str:
    """
    Convert standard markdown to YWH markdown.

    Args:
        message: a markdown message
        attachments: a list of attachments

    Returns:
        a YWH markdown
    """
    images = _RE_IMAGE.findall(message)
    for key, value in images:
        attachment = attachments.get(value)
        if not attachment:
            continue
        message = message.replace(
            f'![{key}]({value})',
            f'{{YWH-C{attachment.attachment_id}}}',
        )
    return message
