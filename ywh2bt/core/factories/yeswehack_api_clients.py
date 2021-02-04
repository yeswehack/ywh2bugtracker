"""Models and functions used for YesWeHack api clients factories."""
from abc import (
    ABC,
    abstractmethod,
)
from typing import Dict

from ywh2bt.core.api.yeswehack import (
    YesWeHackApiClient,
    YesWeHackApiClientError,
)
from ywh2bt.core.configuration.yeswehack import YesWeHackConfiguration
from ywh2bt.core.exceptions import CoreException


class YesWeHackApiClientsAbstractFactory(ABC):
    """Abstract factory for YesWeHackApiClients."""

    @abstractmethod
    def get_yeswehack_api_client(
        self,
        configuration: YesWeHackConfiguration,
    ) -> YesWeHackApiClient:
        """
        Get the api client for the given configuration.

        Args:
            configuration: a configuration
        """


class YesWeHackApiClientsFactory(YesWeHackApiClientsAbstractFactory):
    """Concrete factory for YesWeHackApiClients."""

    _yeswehack_api_clients: Dict[YesWeHackConfiguration, YesWeHackApiClient]

    def __init__(
        self,
    ) -> None:
        """Initialize self."""
        self._yeswehack_api_clients = {}

    def get_yeswehack_api_client(
        self,
        configuration: YesWeHackConfiguration,
    ) -> YesWeHackApiClient:
        """
        Get the api client for the given configuration.

        Args:
            configuration: a configuration

        Raises:
            CoreException: if the client could not be created

        Returns:
            The client
        """
        if configuration not in self._yeswehack_api_clients:
            try:
                client = YesWeHackApiClient(
                    configuration=configuration,
                )
            except YesWeHackApiClientError as e:
                raise CoreException('Unable to create YesWeHack API client') from e
            self._yeswehack_api_clients[configuration] = client
        return self._yeswehack_api_clients[configuration]
