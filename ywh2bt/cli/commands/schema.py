"""Models and functions for CLI JSON schema dump."""
import argparse
import sys

from ywh2bt.cli.error import CliError
from ywh2bt.core.core import AVAILABLE_SCHEMA_DUMP_FORMATS, write_message
from ywh2bt.core.schema.error import SchemaError


def dump_schema(
    args: argparse.Namespace,
) -> None:
    """
    Dump a Schema of the structure of the configuration files.

    Args:
        args: command line arguments

    Raises:
        CliError: if an error occurred
    """
    dumper = AVAILABLE_SCHEMA_DUMP_FORMATS.get(args.output_format)
    if not dumper:
        raise CliError(f'Unsupported schema dump format {repr(args.output_format)}')
    try:
        schema = dumper()
    except SchemaError as schema_error:
        raise CliError('JSON Schema error') from schema_error
    write_message(
        message=schema,
        stream=sys.stdout,
    )
