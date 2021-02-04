"""Models and functions for CLI synchronization."""
import argparse

from ywh2bt.cli.error import CliError
from ywh2bt.cli.listener import CliSynchronizerListener
from ywh2bt.core.configuration.error import BaseAttributeError
from ywh2bt.core.core import load_configuration
from ywh2bt.core.factories.tracker_clients import TrackerClientsFactory
from ywh2bt.core.factories.yeswehack_api_clients import YesWeHackApiClientsFactory
from ywh2bt.core.synchronizer.error import SynchronizerError
from ywh2bt.core.synchronizer.synchronizer import Synchronizer


def synchronize(
    args: argparse.Namespace,
) -> None:
    """
    Synchronize data between YWH and trackers.

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
    except BaseAttributeError as validation_error:
        raise CliError('Invalid configuration') from validation_error
    synchronizer = Synchronizer(
        configuration=configuration,
        yes_we_hack_api_clients_factory=YesWeHackApiClientsFactory(),
        tracker_clients_factory=TrackerClientsFactory(),
        listener=CliSynchronizerListener(),
    )
    try:
        synchronizer.synchronize()
    except SynchronizerError as synchronization_error:
        raise CliError('Synchronization error') from synchronization_error
