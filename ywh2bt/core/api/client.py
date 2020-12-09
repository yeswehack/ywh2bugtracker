"""Models and functions used for base api clients."""
from abc import ABC, abstractmethod


class TestableApiClient(ABC):
    """An API client that can be tested."""

    @abstractmethod
    def test(
        self,
    ) -> None:
        """Test the client."""
