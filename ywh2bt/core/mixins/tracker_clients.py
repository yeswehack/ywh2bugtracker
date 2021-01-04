"""Models and functions used for tracker clients mixins."""
from typing import Any, Dict

from ywh2bt.core.api.tracker import TrackerClient, TrackerClientError
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.exceptions import CoreException
from ywh2bt.core.mapping import TRACKER_CLIENT_CLASSES


class TrackerClientsMixin:
    """Mixin for TrackerClients."""

    _tracker_clients: Dict[TrackerConfiguration, TrackerClient[Any]]

    def __init__(
        self,
    ) -> None:
        """Initialize self."""
        self._tracker_clients = {}

    def get_tracker_client(
        self,
        configuration: TrackerConfiguration,
    ) -> TrackerClient[Any]:
        """
        Get the api client for the given configuration.

        Args:
            configuration: a configuration

        Returns:
            The client
        """
        if configuration not in self._tracker_clients:
            self._tracker_clients[configuration] = self._build_tracker_client(
                configuration=configuration,
            )
        return self._tracker_clients[configuration]

    def _build_tracker_client(
        self,
        configuration: TrackerConfiguration,
    ) -> TrackerClient[Any]:
        configuration_class = configuration.__class__
        if configuration_class not in TRACKER_CLIENT_CLASSES:
            raise CoreException(f'{configuration_class} does not have an associated tracker client')
        tracker_client_class = TRACKER_CLIENT_CLASSES[configuration_class]
        try:
            client = tracker_client_class(
                configuration=configuration,
            )
        except TrackerClientError as e:
            raise CoreException(f'Unable to create {configuration_class} API client') from e
        return client
