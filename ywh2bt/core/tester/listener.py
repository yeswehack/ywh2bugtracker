"""Models and functions used for observing test of YesWeHack and tracker clients."""
from abc import ABC
from dataclasses import dataclass

from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.yeswehack import YesWeHackConfiguration
from ywh2bt.core.listener import Event, Listener


@dataclass
class TesterEvent(Event, ABC):
    """A base event sent by a Tester."""


@dataclass
class TesterStartEvent(TesterEvent):
    """An event sent when a test starts."""

    configuration: RootConfiguration


@dataclass
class TesterEndEvent(TesterEvent):
    """An event sent when a test ends."""

    configuration: RootConfiguration


@dataclass
class TesterStartYesWeHackEvent(TesterEvent):
    """An event sent when a test of a YesWeJackConfiguration starts."""

    yeswehack_name: str
    yeswehack_configuration: YesWeHackConfiguration


@dataclass
class TesterEndYesWeHackEvent(TesterEvent):
    """An event sent when a test of a YesWeJackConfiguration ends."""

    yeswehack_name: str
    yeswehack_configuration: YesWeHackConfiguration


@dataclass
class TesterStartTrackerEvent(TesterEvent):
    """An event sent when a test of a Tracker starts."""

    tracker_name: str
    tracker_configuration: TrackerConfiguration


@dataclass
class TesterEndTrackerEvent(TesterEvent):
    """An event sent when a test of a Tracker ends."""

    tracker_name: str
    tracker_configuration: TrackerConfiguration


class TesterListener(Listener[TesterEvent], ABC):
    """A listener receiving events from a Tester."""


class NoOpTesterListener(TesterListener):
    """A listener receiving events from a Tester and doing nothing."""

    def on_event(
        self,
        event: TesterEvent,
    ) -> None:
        """
        Receive an event and do nothing.

        Args:
            event: an event
        """
