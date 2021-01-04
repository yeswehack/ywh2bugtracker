"""Models and functions used in file dialogs."""
from string import Template
from typing import Dict, Optional, Set

from ywh2bt.core.core import AvailableFormat


class FileFormatDialogFilters:
    """A class that holds data for manipulating file dialogs filters."""

    _filters: Dict[str, str]

    def __init__(
        self,
        formats: Dict[str, AvailableFormat],
    ):
        """
        Initialize self.

        Args:
            formats: a dict of available core formats
        """
        filter_template = Template('${name} files (${patterns})')
        filters = {}
        for name, available_format in formats.items():
            patterns = self._get_extensions_patterns(
                extensions=available_format.extensions,
            )
            filters[name] = filter_template.substitute(
                name=name.upper(),
                patterns=patterns,
            )
        self._filters = filters

    @classmethod
    def _get_extensions_patterns(
        cls,
        extensions: Set[str],
    ) -> str:
        template = Template('*.${extension}')
        patterns = []
        for extension in extensions:
            patterns.append(
                template.substitute(
                    extension=extension,
                ),
            )
        return ' '.join(patterns)

    def get_filters_string_for(
        self,
        format_name: str,
    ) -> Optional[str]:
        """
        Get the filters for a format.

        Args:
            format_name: a format name

        Returns:
            The filters
        """
        return self._filters.get(format_name)

    def get_filters_string(
        self,
        separator: str = ';;',
    ) -> str:
        """
        Get the filters.

        Args:
            separator: a string to be used as a separators between the filters

        Returns:
            The filters
        """
        return separator.join(self._filters.values())

    def get_format_name(
        self,
        filter_string: str,
    ) -> Optional[str]:
        """
        Get the name of format given a filter.

        Args:
            filter_string: a filter string

        Returns:
            The format name or None if the format does not exist
        """
        for format_name, existing_filter_string in self._filters.items():
            if filter_string == existing_filter_string:
                return format_name
        return None
