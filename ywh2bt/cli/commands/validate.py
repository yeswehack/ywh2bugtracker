"""Models and functions for CLI validation."""
import argparse

from ywh2bt.cli.error import CliError
from ywh2bt.core.configuration.error import BaseAttributeError
from ywh2bt.core.core import load_configuration


def validate(
    args: argparse.Namespace,
) -> None:
    """
    Validate a configuration file.

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
