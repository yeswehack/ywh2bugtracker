"""CLI arguments parsing and execution."""
import argparse
import sys

import urllib3  # type: ignore

from ywh2bt.cli.commands.convert import convert
from ywh2bt.cli.commands.schema import dump_schema
from ywh2bt.cli.commands.synchronize import synchronize
from ywh2bt.cli.commands.test import test
from ywh2bt.cli.commands.validate import validate
from ywh2bt.core.core import AVAILABLE_FORMATS, AVAILABLE_SCHEMA_DUMP_FORMATS
from ywh2bt.core.error import print_error, print_error_message
from ywh2bt.core.exceptions import CoreException
from ywh2bt.version import __VERSION__

urllib3.disable_warnings(
    category=urllib3.exceptions.InsecureRequestWarning,
)

DEFAULT_FORMATTER_CLASS = argparse.ArgumentDefaultsHelpFormatter
CONFIGURATION_FORMATS = list(AVAILABLE_FORMATS.keys())
SCHEMA_DUMP_FORMATS = list(AVAILABLE_SCHEMA_DUMP_FORMATS.keys())

SubParsersActionType = argparse._SubParsersAction  # noqa: WPS437


def run(
    *args: str,
) -> None:
    """
    Run the CLI.

    Args:
        args: command line arguments
    """
    if not args:
        args = tuple(sys.argv[1:])
    parsed = _parse_args(*args)
    try:
        parsed.func(parsed)
    except CoreException as e:
        print_error(
            error=e,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print_error_message(
            message='Interrupted by user.',
        )
        sys.exit(130)
    sys.exit(0)


def _parse_args(
    *args: str,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=DEFAULT_FORMATTER_CLASS,
    )
    parser.add_argument(
        '--version',
        '-V',
        action='version',
        version=f'%(prog)s {__VERSION__}',  # noqa: C812, WPS323
    )
    parser.set_defaults(func=lambda _: parser.print_help())

    commands = parser.add_subparsers(dest='command')

    _add_validate_command(
        parent_parser=commands,
    )
    _add_synchronize_command(
        parent_parser=commands,
    )
    _add_test_command(
        parent_parser=commands,
    )
    _add_convert_command(
        parent_parser=commands,
    )
    _add_schema_command(
        parent_parser=commands,
    )

    return parser.parse_args(
        args,
    )


def _add_validate_command(
    parent_parser: SubParsersActionType,
) -> None:
    validate_parser = parent_parser.add_parser(
        formatter_class=DEFAULT_FORMATTER_CLASS,
        name='validate',
        help='Validate configuration file (mandatory fields, data types, ...)',
    )
    _add_config_file_format(
        parser=validate_parser,
    )
    validate_parser.set_defaults(func=validate)


def _add_synchronize_command(
    parent_parser: SubParsersActionType,
) -> None:
    synchronize_parser = parent_parser.add_parser(
        formatter_class=DEFAULT_FORMATTER_CLASS,
        name='synchronize',
        aliases=('sync',),
        help='Execute synchronization',
    )
    _add_config_file_format(
        parser=synchronize_parser,
    )
    synchronize_parser.set_defaults(func=synchronize)


def _add_test_command(
    parent_parser: SubParsersActionType,
) -> None:
    test_parser = parent_parser.add_parser(
        formatter_class=DEFAULT_FORMATTER_CLASS,
        name='test',
        help='Test the connection to the trackers',
    )
    _add_config_file_format(
        parser=test_parser,
    )
    test_parser.set_defaults(func=test)


def _add_convert_command(
    parent_parser: SubParsersActionType,
) -> None:
    convert_parser = parent_parser.add_parser(
        formatter_class=DEFAULT_FORMATTER_CLASS,
        name='convert',
        help='Convert a configuration file from a format to another',
    )
    _add_config_file_format(
        parser=convert_parser,
        format_required=True,
    )
    convert_parser.add_argument(
        '--destination-file',
        '-d',
        dest='destination_file',
        help='path to converted file ; if "-", print to stdout',
        default='-',
        type=str,
    )
    convert_parser.add_argument(
        '--destination-format',
        '-df',
        dest='destination_format',
        help='format to converted file',
        required=True,
        type=str,
        default=argparse.SUPPRESS,
        choices=CONFIGURATION_FORMATS,
    )
    convert_parser.add_argument(
        '--override',
        dest='override',
        help='override destination file if it already exists',
        action='store_true',
    )
    convert_parser.set_defaults(func=convert)


def _add_schema_command(
    parent_parser: SubParsersActionType,
) -> None:
    schema_parser = parent_parser.add_parser(
        formatter_class=DEFAULT_FORMATTER_CLASS,
        name='schema',
        help='Dump a schema of the structure of the configuration files in JSON Schema, markdown or plaintext',
    )
    schema_parser.add_argument(
        '--format',
        '-f',
        dest='output_format',
        help='format',
        type=str,
        required=False,
        default=SCHEMA_DUMP_FORMATS[0],
        choices=SCHEMA_DUMP_FORMATS,
    )
    schema_parser.set_defaults(func=dump_schema)


def _add_config_file(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        '--config-file',
        '-c',
        dest='config_file',
        help='path to configuration file',
        required=True,
        type=str,
        default=argparse.SUPPRESS,
    )


def _add_config_format(
    parser: argparse.ArgumentParser,
    required: bool = False,
) -> None:
    parser.add_argument(
        '--config-format',
        '-f',
        dest='config_format',
        help='format of configuration file',
        type=str,
        required=required,
        default='yaml',
        choices=CONFIGURATION_FORMATS,
    )


def _add_config_file_format(
    parser: argparse.ArgumentParser,
    format_required: bool = False,
) -> None:
    _add_config_file(
        parser=parser,
    )
    _add_config_format(
        parser=parser,
        required=format_required,
    )


if __name__ == '__main__':
    run(
        *sys.argv[1:],
    )
