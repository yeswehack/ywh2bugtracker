"""Models and functions used for data loading/saving."""
from abc import ABC, abstractmethod
from typing import Any, Generic, TextIO, TypeVar

from ywh2bt.core.configuration.error import BaseAttributeError
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.exceptions import CoreException
from ywh2bt.core.serde import SerDe, SerDeError

LoadType = TypeVar('LoadType')
DumpType = TypeVar('DumpType')


class LoaderError(CoreException):
    """A loading/saving error."""


class _BaseLoader(ABC, Generic[LoadType, DumpType]):
    @abstractmethod
    def load(
        self,
        stream: TextIO,
    ) -> LoadType:
        """
        Load data from a stream.

        Args:
            stream: a stream
        """

    @abstractmethod
    def save(
        self,
        data: DumpType,
        stream: TextIO,
    ) -> None:
        """
        Save data in a stream.

        Args:
            data: data to be saved
            stream: a stream
        """


class DataLoader(_BaseLoader[Any, Any]):
    """Generic data loader."""

    _serde: SerDe

    def __init__(
        self,
        serde: SerDe,
    ) -> None:
        """
        Initialize self.

        Args:
            serde: serializer/deserializer used when loading/saving
        """
        self._serde = serde

    def load(
        self,
        stream: TextIO,
    ) -> Any:
        """
        Load data from a stream.

        Args:
            stream: a stream

        Returns:
            the loaded data

        Raises:
            LoaderError: if the data couldn't be deserialized
        """
        try:
            data = self._serde.deserialize_from_stream(
                stream=stream,
            )
        except SerDeError as e:
            raise LoaderError('Unable to deserialize data') from e
        return data

    def save(
        self,
        data: Any,
        stream: TextIO,
    ) -> None:
        """
        Save data in a stream.

        Args:
            data: data to be saved
            stream: a stream

        Raises:
            LoaderError: if the data couldn't be serialized
        """
        try:
            self._serde.serialize_to_stream(
                data=data,
                stream=stream,
            )
        except SerDeError as e:
            raise LoaderError('Unable to serialize data') from e


class RootConfigurationLoader(_BaseLoader[RootConfiguration, RootConfiguration]):
    """Root configuration data loader."""

    _loader: DataLoader

    def __init__(
        self,
        serde: SerDe,
    ) -> None:
        """
        Initialize self.

        Args:
            serde: serializer/deserializer used when loading/saving
        """
        self._loader = DataLoader(
            serde=serde,
        )

    def load(
        self,
        stream: TextIO,
    ) -> RootConfiguration:
        """
        Load configuration from a stream.

        Args:
            stream: a stream

        Returns:
            the loaded configuration

        Raises:
            LoaderError: if the configuration couldn't be loaded
        """
        data = self._loader.load(
            stream=stream,
        )
        if not isinstance(data, dict):
            data_type = type(data)
            raise LoaderError(f'Expecting {dict} for root configuration ; got {data_type}')
        try:
            return RootConfiguration(**data)
        except BaseAttributeError as e:
            raise LoaderError('Unable to load root configuration') from e

    def save(
        self,
        data: RootConfiguration,
        stream: TextIO,
    ) -> None:
        """
        Save configuration in a stream.

        Args:
            data: data to be saved
            stream: a stream
        """
        self._loader.save(
            data=data.export(),
            stream=stream,
        )
