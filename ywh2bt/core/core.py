"""Models and functions used for loading/writing configuration files."""
from dataclasses import dataclass
from typing import Dict, OrderedDict, Set, TextIO, Type

from ywh2bt.core.configuration.error import BaseAttributeError
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.exceptions import CoreException
from ywh2bt.core.loader import RootConfigurationLoader
from ywh2bt.core.schema.json import root_configuration_as_json_schema
from ywh2bt.core.schema.markdown import root_configuration_as_markdown
from ywh2bt.core.schema.protocol import SchemaDumpProtocol
from ywh2bt.core.schema.text import root_configuration_as_text
from ywh2bt.core.serde import SerDe
from ywh2bt.core.serializers.json import JsonSerDe
from ywh2bt.core.serializers.yaml import YamlSerDe


@dataclass
class AvailableFormat:
    """A class describing a core format and its supported file name extensions."""

    ser_de: Type[SerDe]
    extensions: Set[str]


AVAILABLE_FORMATS: Dict[str, AvailableFormat] = OrderedDict[str, AvailableFormat]({
    'yaml': AvailableFormat(
        ser_de=YamlSerDe,
        extensions={
            'yaml',
            'yml',
        },
    ),
    'json': AvailableFormat(
        ser_de=JsonSerDe,
        extensions={
            'json',
        },
    ),
})

AVAILABLE_SCHEMA_DUMP_FORMATS: Dict[str, SchemaDumpProtocol] = OrderedDict[str, SchemaDumpProtocol]({
    'text': root_configuration_as_text,
    'markdown': root_configuration_as_markdown,
    'json': root_configuration_as_json_schema,
})


def get_root_configuration_loader(
    file_format: str,
) -> RootConfigurationLoader:
    """
    Get a configuration loader for the given format.

    Args:
        file_format: a file format

    Returns:
        a configuration loader
    """
    serde = get_serde(
        file_format=file_format,
    )
    return RootConfigurationLoader(
        serde=serde,
    )


def get_serde(
    file_format: str,
) -> SerDe:
    """
    Get a serde for the given format.

    Args:
        file_format: a file format

    Returns:
        a serde

    Raises:
        CoreException: is the format is not supported
    """
    available_format = AVAILABLE_FORMATS.get(file_format)
    if available_format:
        return available_format.ser_de()
    raise CoreException(f'Unsupported file format {file_format}.')


def load_configuration(
    config_format: str,
    config_file: str,
) -> RootConfiguration:
    """
    Load a configuration file.

    Args:
        config_format: a file format
        config_file: a file

    Returns:
        a configuration

    Raises:
        CoreException: if the configuration couldn't be loaded
    """
    loader = get_root_configuration_loader(
        file_format=config_format,
    )
    try:
        with open(config_file, 'r') as f:
            return loader.load(
                stream=f,
            )
    except FileNotFoundError as e:
        raise CoreException('Configuration file not found') from e
    except BaseAttributeError as e:
        raise CoreException('Configuration invalid') from e


def write_message(
    stream: TextIO,
    message: str,
    end: str = '\n',
) -> None:
    """
    Write a message on the stream.

    Args:
        stream: a stream
        message: a message
        end: a string appended after the message, default a newline
    """
    stream.write(message)
    if end:
        stream.write(end)
    stream.flush()
