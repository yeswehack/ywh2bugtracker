"""Models and functions used for tracker clients factories."""
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Any,
    Dict,
    Optional,
    Type,
)

from ywh2bt.core.api.tracker import (
    TrackerClient,
    TrackerClientError,
)
from ywh2bt.core.api.trackers.github.tracker import GitHubTrackerClient
from ywh2bt.core.api.trackers.gitlab import GitLabTrackerClient
from ywh2bt.core.api.trackers.jira.tracker import JiraTrackerClient
from ywh2bt.core.api.trackers.servicenow.tracker import ServiceNowTrackerClient
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.trackers.github import GitHubConfiguration
from ywh2bt.core.configuration.trackers.gitlab import GitLabConfiguration
from ywh2bt.core.configuration.trackers.jira import JiraConfiguration
from ywh2bt.core.configuration.trackers.servicenow import ServiceNowConfiguration
from ywh2bt.core.exceptions import CoreException


class TrackerClientsAbstractFactory(ABC):
    """Abstract factory for TrackerClients."""

    @abstractmethod
    def get_tracker_client(
        self,
        configuration: TrackerConfiguration,
    ) -> TrackerClient[Any]:
        """
        Get the api client for the given configuration.

        Args:
            configuration: a configuration
        """


class TrackerClientsFactory(TrackerClientsAbstractFactory):
    """Concrete factory for TrackerClients."""

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
        tracker_client_class = TrackerClientClassesRegistry.get_tracker_client_class(
            configuration_class=configuration_class,
        )
        if not tracker_client_class:
            message = (
                f'{configuration_class} does not have an associated tracker client ; '
                + f'use {TrackerClientClassesRegistry.__name__}.register_tracker_client_class() to register.'
            )
            raise CoreException(message)
        try:
            client = tracker_client_class(
                configuration=configuration,
            )
        except TrackerClientError as e:
            raise CoreException(f'Unable to create {configuration_class} API client') from e
        return client


TrackerConfigurationType = Type[TrackerConfiguration]
TrackerClientType = Type[TrackerClient[Any]]
TrackerClientClassesType = Dict[
    TrackerConfigurationType,
    TrackerClientType,
]


class TrackerClientClassesRegistry:
    """Registry for associating TrackerConfiguration classes with TrackerClient classes."""

    _classes: TrackerClientClassesType = {}

    @classmethod
    def register_tracker_client_class(
        cls,
        configuration_class: TrackerConfigurationType,
        client_class: TrackerClientType,
    ) -> None:
        """
        Associate a TrackerConfiguration class with a TrackerClient client class.

        Args:
            configuration_class: a TrackerConfiguration class
            client_class: a TrackerClient client class
        """
        cls._classes[configuration_class] = client_class

    @classmethod
    def unregister_tracker_client_class(
        cls,
        configuration_class: TrackerConfigurationType,
    ) -> None:
        """
        Dissociate a TrackerConfiguration class from a TrackerClient client class.

        Args:
            configuration_class: a TrackerConfiguration class
        """
        if configuration_class in cls._classes:
            cls._classes.pop(configuration_class)

    @classmethod
    def get_tracker_client_class(
        cls,
        configuration_class: TrackerConfigurationType,
    ) -> Optional[TrackerClientType]:
        """
        Get the TrackerConfiguration class associated with a TrackerClient client class.

        Args:
            configuration_class: a TrackerConfiguration class

        Returns:
            the TrackerClient client class if one is associated with the TrackerConfiguration class ; else None
        """
        return cls._classes.get(configuration_class)


TrackerClientClassesRegistry.register_tracker_client_class(
    configuration_class=GitHubConfiguration,
    client_class=GitHubTrackerClient,
)
TrackerClientClassesRegistry.register_tracker_client_class(
    configuration_class=GitLabConfiguration,
    client_class=GitLabTrackerClient,
)
TrackerClientClassesRegistry.register_tracker_client_class(
    configuration_class=JiraConfiguration,
    client_class=JiraTrackerClient,
)
TrackerClientClassesRegistry.register_tracker_client_class(
    configuration_class=ServiceNowConfiguration,
    client_class=ServiceNowTrackerClient,
)
