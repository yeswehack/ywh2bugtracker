"""Models and functions used for data serialization/deserialization."""
from abc import ABC, abstractmethod
from typing import Any, TextIO

from ywh2bt.core.exceptions import CoreException


class SerDe(ABC):
    """Base abstract serializer/deserializer."""

    @abstractmethod
    def serialize_to_stream(
        self,
        data: Any,
        stream: TextIO,
    ) -> None:
        """
        Write serialized data into a stream.

        Args:
            data: data
            stream: a stream
        """

    @abstractmethod
    def deserialize_from_stream(
        self,
        stream: TextIO,
    ) -> Any:
        """
        Read and deserialize data from a stream.

        Args:
            stream: a stream
        """


class SerDeError(CoreException):
    """A serialization error."""
