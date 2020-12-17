"""Models and functions used for root configuration GUI."""
from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from typing import Optional

from PySide2.QtCore import QByteArray, QFileInfo

from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.core import get_root_configuration_loader
from ywh2bt.core.exceptions import CoreException
from ywh2bt.core.loader import LoaderError
from ywh2bt.gui.hashing import file_checksum


@dataclass
class RootConfigurationEntryFile:
    """A class describing an exiting configuration file."""

    info: QFileInfo
    file_format: str
    checksum: QByteArray


class RootConfigurationEntry:
    """A class describing an editable configuration."""

    _name: str
    _configuration: Optional[RootConfiguration]
    _raw: str
    _original_raw: str
    _raw_format: str
    _file: Optional[RootConfigurationEntryFile]

    def __init__(
        self,
        name: str,
        raw: str,
        original_raw: str,
        raw_format: str,
        file: Optional[RootConfigurationEntryFile] = None,
    ):
        """
        Initialize self.

        Args:
            name: a configuration name
            raw: raw content of the configuration
            original_raw: original raw content of the configuration
            raw_format: a format (json, yaml, ...)
            file: associated file information
        """
        self._name = name
        self._raw = raw
        self._original_raw = original_raw
        self._raw_format = raw_format
        self._file = file
        self._configuration = self._configuration_from_raw(
            raw=self._raw,
            raw_format=self._raw_format,
        )

    def _update_configuration(
        self,
    ) -> None:
        self._configuration = None
        self._configuration = self._configuration_from_raw(
            raw=self._raw,
            raw_format=self._raw_format,
        )

    def _update_raw(
        self,
    ) -> None:
        self._raw = self._raw_from_configuration()

    @property
    def name(
        self,
    ) -> str:
        """
        Get the name.

        Returns:
            name
        """
        return self._name

    @name.setter
    def name(
        self,
        name: str,
    ) -> None:
        """
        Set the name.

        Args:
            name: a name
        """
        self._name = name

    @property
    def configuration(
        self,
    ) -> Optional[RootConfiguration]:
        """
        Get the configuration.

        Returns:
            configuration
        """
        return self._configuration

    @configuration.setter
    def configuration(
        self,
        configuration: Optional[RootConfiguration],
    ) -> None:
        """
        Set the configuration.

        Args:
            configuration: a configuration
        """
        self._configuration = configuration
        self._update_raw()

    @property
    def original_configuration(
        self,
    ) -> Optional[RootConfiguration]:
        """
        Get the original configuration.

        Returns:
            original configuration
        """
        return self._configuration_from_raw(
            raw=self._original_raw,
            raw_format=self._raw_format,
        )

    @property
    def raw(
        self,
    ) -> str:
        """
        Get the raw content.

        Returns:
            raw content
        """
        return self._raw

    @raw.setter
    def raw(
        self,
        raw: str,
    ) -> None:
        """
        Set the raw content.

        Args:
            raw: content
        """
        self._raw = raw
        self._update_configuration()

    @property
    def raw_format(
        self,
    ) -> str:
        """
        Get the raw format.

        Returns:
            raw format
        """
        return self._raw_format

    @raw_format.setter
    def raw_format(
        self,
        raw_format: str,
    ) -> None:
        """
        Set the raw format.

        Args:
            raw_format: a format
        """
        self._raw_format = raw_format

    @property
    def original_raw(
        self,
    ) -> str:
        """
        Get the original raw content.

        Returns:
            original raw content
        """
        return self._original_raw

    @original_raw.setter
    def original_raw(
        self,
        original_raw: str,
    ) -> None:
        """
        Set the original raw content.

        Args:
            original_raw: content
        """
        self._original_raw = original_raw

    @property
    def file(
        self,
    ) -> Optional[RootConfigurationEntryFile]:
        """
        Get the file information.

        Returns:
            file information
        """
        return self._file

    @file.setter
    def file(
        self,
        file: Optional[RootConfigurationEntryFile],
    ) -> None:
        """
        Set the file information.

        Args:
            file: file information
        """
        self._file = file

    def has_changed(self) -> bool:
        """
        Check if the raw content has changed.

        Returns:
            True if the file has changed, otherwise False.
        """
        return self._raw != self._original_raw

    def is_empty(self) -> bool:
        """
        Check if the configuration is empty.

        Returns:
            True if the configuration is empty, otherwise False.
        """
        return self._raw == ''

    @classmethod
    def from_file(
        cls,
        file_info: QFileInfo,
        file_format: str,
    ) -> RootConfigurationEntry:
        """
        Create a RootConfigurationEntry from a file.

        Args:
            file_info: a file
            file_format: a file format

        Raises:
            CoreException: if the file couldn't be opened

        Returns:
            a RootConfigurationEntry
        """
        file_path = file_info.filePath()
        try:
            with open(file_path, 'r') as f:
                raw = f.read()
        except IOError as e:
            raise CoreException(f'Unable to open file:\n{file_path}') from e

        return RootConfigurationEntry(
            name=file_info.fileName(),
            raw=raw,
            original_raw=raw,
            raw_format=file_format,
            file=RootConfigurationEntryFile(
                info=file_info,
                file_format=file_format,
                checksum=file_checksum(file_info.filePath()),
            ),
        )

    @classmethod
    def _configuration_from_raw(
        cls,
        raw: str,
        raw_format: str,
    ) -> Optional[RootConfiguration]:
        if not raw:
            return RootConfiguration()
        loader = get_root_configuration_loader(
            file_format=raw_format,
        )
        raw_stream = StringIO(raw)
        try:
            return loader.load(
                stream=raw_stream,
            )
        except LoaderError as e:
            raise CoreException('Invalid raw configuration') from e

    def _raw_from_configuration(
        self,
    ) -> str:
        if not self._configuration:
            return ''
        loader = get_root_configuration_loader(
            file_format=self._raw_format,
        )
        raw_stream = StringIO()
        try:
            loader.save(
                stream=raw_stream,
                data=self._configuration,
            )
        except LoaderError:
            return ''
        return raw_stream.getvalue()
