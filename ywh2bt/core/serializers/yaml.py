"""Models and functions used for Yaml data SerDe."""
from typing import Any, TextIO

from ruamel.yaml import YAML  # type: ignore

from ywh2bt.core.serde import SerDe, SerDeError


class YamlSerDe(SerDe):
    """A Yaml Serializer/deserializer."""

    def serialize_to_stream(
        self,
        data: Any,
        stream: TextIO,
    ) -> None:
        """
        Write serialized data as Yaml into a stream.

        Args:
            data: data
            stream: a stream

        Raises:
            SerDeError: if an error occurred during writing or serialization
        """
        yaml = YAML()
        try:
            yaml.dump(
                data=data,
                stream=stream,
            )
        except Exception as e:
            raise SerDeError('YAML dump error') from e

    def deserialize_from_stream(
        self,
        stream: TextIO,
    ) -> Any:
        """
        Read and deserialize Yaml data from a stream.

        Args:
            stream: a stream

        Returns:
            the deserialized data

        Raises:
            SerDeError: if an error occurred during reading or deserialization
        """
        yaml = YAML()
        try:
            return yaml.load(stream.read())
        except Exception as e:
            raise SerDeError('YAML load error') from e
