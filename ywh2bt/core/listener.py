"""Models and functions used for listening to events."""
from abc import ABC
from dataclasses import dataclass
from typing import Generic, TypeVar


@dataclass
class Event(ABC):
    """A base event."""


E = TypeVar('E', bound=Event, contravariant=True)


class Listener(Generic[E], ABC):
    """A generic listener receiving events."""

    def on_event(
        self,
        event: E,
    ) -> None:
        """
        Receive an event.

        Args:
            event: an event
        """
