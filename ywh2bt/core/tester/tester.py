"""Models and functions used for testing of YesWeHack and tracker clients."""
from typing import (
    Optional,
    cast,
)

from ywh2bt.core.api.tracker import TrackerClientError
from ywh2bt.core.api.yeswehack import YesWeHackApiClientError
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.configuration.tracker import (
    TrackerConfiguration,
    Trackers,
)
from ywh2bt.core.configuration.yeswehack import (
    YesWeHackConfiguration,
    YesWeHackConfigurations,
)
from ywh2bt.core.factories.tracker_clients import (
    TrackerClientsAbstractFactory,
)
from ywh2bt.core.factories.yeswehack_api_clients import (
    YesWeHackApiClientsAbstractFactory,
)
from ywh2bt.core.tester.error import TesterError
from ywh2bt.core.tester.listener import (
    NoOpTesterListener,
    TesterEndEvent,
    TesterEndTrackerEvent,
    TesterEndYesWeHackEvent,
    TesterListener,
    TesterStartEvent,
    TesterStartTrackerEvent,
    TesterStartYesWeHackEvent,
)


class Tester:
    """A class used for testing of YesWeHack and tracker clients."""

    _configuration: RootConfiguration
    _yes_we_hack_api_clients_factory: YesWeHackApiClientsAbstractFactory
    _tracker_clients_factory: TrackerClientsAbstractFactory
    _listener: TesterListener

    def __init__(
        self,
        configuration: RootConfiguration,
        yes_we_hack_api_clients_factory: YesWeHackApiClientsAbstractFactory,
        tracker_clients_factory: TrackerClientsAbstractFactory,
        listener: Optional[TesterListener] = None,
    ):
        """
        Initialize self.

        Args:
            configuration: a configuration
            yes_we_hack_api_clients_factory: a YesWeHackApiClients factory
            tracker_clients_factory: a TrackerClients factory
            listener: an observer that will receive test events
        """
        self._configuration = configuration
        self._yes_we_hack_api_clients_factory = yes_we_hack_api_clients_factory
        self._tracker_clients_factory = tracker_clients_factory
        self._listener = listener or NoOpTesterListener()

    def test(
        self,
    ) -> None:
        """Test YesWeHack and tracker clients."""
        self._listener.on_event(
            event=TesterStartEvent(
                configuration=self._configuration,
            ),
        )
        self._test_yeswehack()
        self._test_bugtrackers()
        self._listener.on_event(
            event=TesterEndEvent(
                configuration=self._configuration,
            ),
        )

    def _test_yeswehack(
        self,
    ) -> None:
        yeswehack_configurations = cast(YesWeHackConfigurations, self._configuration.yeswehack)
        for yeswehack_name, yeswehack_configuration in yeswehack_configurations.items():
            self._test_yeswehack_configuration(
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
            )

    def _test_yeswehack_configuration(
        self,
        yeswehack_name: str,
        yeswehack_configuration: YesWeHackConfiguration,
    ) -> None:
        self._listener.on_event(
            event=TesterStartYesWeHackEvent(
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
            ),
        )
        yeswehack_client = self._yes_we_hack_api_clients_factory.get_yeswehack_api_client(
            configuration=yeswehack_configuration,
        )
        try:
            yeswehack_client.test()
        except YesWeHackApiClientError as e:
            raise TesterError(f'Test for yeswehack {yeswehack_name} has failed') from e
        self._listener.on_event(
            event=TesterEndYesWeHackEvent(
                yeswehack_name=yeswehack_name,
                yeswehack_configuration=yeswehack_configuration,
            ),
        )

    def _test_bugtrackers(
        self,
    ) -> None:
        bugtracker_configurations = cast(Trackers, self._configuration.bugtrackers)
        for bugtracker_name, bugtracker_configuration in bugtracker_configurations.items():
            self._test_bugtracker(
                bugtracker_name=bugtracker_name,
                bugtracker_configuration=bugtracker_configuration,
            )

    def _test_bugtracker(
        self,
        bugtracker_name: str,
        bugtracker_configuration: TrackerConfiguration,
    ) -> None:
        self._listener.on_event(
            event=TesterStartTrackerEvent(
                tracker_name=bugtracker_name,
                tracker_configuration=bugtracker_configuration,
            ),
        )
        tracker_client = self._tracker_clients_factory.get_tracker_client(
            configuration=bugtracker_configuration,
        )
        try:
            tracker_client.test()
        except TrackerClientError as e:
            raise TesterError(f'Test for bugtracker {bugtracker_name} has failed') from e
        self._listener.on_event(
            event=TesterEndTrackerEvent(
                tracker_name=bugtracker_name,
                tracker_configuration=bugtracker_configuration,
            ),
        )
