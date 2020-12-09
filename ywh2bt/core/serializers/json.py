"""Models and functions used for Json data SerDe."""
import json
from typing import Any, TextIO

from ywh2bt.core.serde import SerDe, SerDeError


class JsonSerDe(SerDe):
    """A Json Serializer/deserializer."""

    def serialize_to_stream(
        self,
        data: Any,
        stream: TextIO,
    ) -> None:
        """
        Write serialized data as Json into a stream.

        Args:
            data: data
            stream: a stream

        Raises:
            SerDeError: if an error occurred during writing or serialization
        """
        try:
            stream.write(json.dumps(data, indent=2))
        except Exception as e:
            raise SerDeError('JSON dump error') from e

    def deserialize_from_stream(
        self,
        stream: TextIO,
    ) -> Any:
        """
        Read and deserialize Json data from a stream.

        Args:
            stream: a stream

        Returns:
            the deserialized data

        Raises:
            SerDeError: if an error occurred during reading or deserialization
        """
        try:
            return json.load(stream)
        except Exception as e:
            raise SerDeError('JSON load error') from e
