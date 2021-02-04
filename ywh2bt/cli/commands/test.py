"""Models and functions for CLI test."""
import argparse

from ywh2bt.cli.error import CliError
from ywh2bt.cli.listener import CliTesterListener
from ywh2bt.core.configuration.error import BaseAttributeError
from ywh2bt.core.core import load_configuration
from ywh2bt.core.factories.tracker_clients import TrackerClientsFactory
from ywh2bt.core.factories.yeswehack_api_clients import YesWeHackApiClientsFactory
from ywh2bt.core.tester.error import TesterError
from ywh2bt.core.tester.tester import Tester


def test(
    args: argparse.Namespace,
) -> None:
    """
    Test YWH and trackers clients.

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
    tester = Tester(
        configuration=configuration,
        yes_we_hack_api_clients_factory=YesWeHackApiClientsFactory(),
        tracker_clients_factory=TrackerClientsFactory(),
        listener=CliTesterListener(),
    )
    try:
        tester.test()
    except TesterError as testing_error:
        raise CliError('Testing error') from testing_error
