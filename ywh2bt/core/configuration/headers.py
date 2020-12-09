"""Models used for HTTP headers."""

from ywh2bt.core.configuration.attribute import ExportableDict


class Headers(ExportableDict[str, str, str, str]):
    """A class describing a list of HTTP headers."""
