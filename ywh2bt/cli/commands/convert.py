"""Models and functions for CLI conversion."""
import argparse
import sys
from pathlib import Path
from typing import TextIO

from ywh2bt.cli.error import CliError
from ywh2bt.core.configuration.error import BaseAttributeError
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.core import get_root_configuration_loader, load_configuration
from ywh2bt.core.loader import LoaderError, RootConfigurationLoader


def convert(
    args: argparse.Namespace,
) -> None:
    """
    Convert a configuration file.

    Args:
        args: command line arguments

    Raises:
        CliError: if an error occurred
    """
    configuration = load_configuration(
        config_format=args.config_format,
        config_file=args.config_file,
    )
    try:
        configuration.validate()
    except BaseAttributeError as e:
        raise CliError('Invalid configuration') from e
    destination_loader = get_root_configuration_loader(
        file_format=args.destination_format,
    )
    if args.destination_file == '-':
        _convert_to_stream(
            loader=destination_loader,
            configuration=configuration,
            stream=sys.stdout,
        )
        return

    file_path = Path(args.destination_file)
    if file_path.exists() and not args.override:
        raise CliError(f'Unable to open destination file {file_path} (already exist)')
    _convert_to_file(
        loader=destination_loader,
        configuration=configuration,
        file_path=file_path,
    )


def _convert_to_stream(
    loader: RootConfigurationLoader,
    configuration: RootConfiguration,
    stream: TextIO,
) -> None:
    try:
        loader.save(
            data=configuration,
            stream=stream,
        )
    except LoaderError as loader_error:
        raise CliError('Unable to convert configuration (stdout)') from loader_error


def _convert_to_file(
    loader: RootConfigurationLoader,
    configuration: RootConfiguration,
    file_path: Path,
) -> None:
    try:
        with open(file_path, 'w') as f:
            _convert_to_stream(
                loader=loader,
                configuration=configuration,
                stream=f,
            )
    except OSError as open_error:
        raise CliError(f'Unable to open destination file {file_path}') from open_error
