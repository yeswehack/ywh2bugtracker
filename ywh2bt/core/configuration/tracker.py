"""Models used to describe bugtrackers."""
from __future__ import annotations

import os
import pkgutil
import sys
from importlib import import_module
from typing import Any, Dict

from ywh2bt.core.configuration.attribute import AttributesContainer, AttributesContainerDict
from ywh2bt.core.configuration.subtypable import Subtypable, SubtypableMetaclass, SubtypeError


class TrackerConfiguration(AttributesContainer, Subtypable, metaclass=SubtypableMetaclass):
    """Base class for tracker."""

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the tracker.

        Args:
            kwargs: keyword arguments

        Raises:
            SubtypeError: if the tracker has not been registered
        """
        tracker_type = self.__class__.get_subtype_name(self.__class__)
        if tracker_type is None:
            message = (
                f'TrackerConfiguration {self.__class__} is not registered ; '
                + 'use TrackerConfiguration.register_subtype() to register.'
            )
            raise SubtypeError(
                message=message,
                context=self,
            )
        super().__init__(**kwargs)

    def export(self) -> Dict[str, Any]:
        """
        Export the tracker data, adding the registered tracker type as `type` entry.

        Returns:
            The data.
        """
        exported = {}
        tracker_type = self.__class__.get_subtype_name(self.__class__)
        if tracker_type:
            exported['type'] = tracker_type
        exported.update(super().export())
        return exported


# import all defined trackers
module_name = vars(sys.modules[__name__])['__package__']  # noqa: WPS421
dirname = os.path.dirname(__file__)
for (_module_finder, name, _is_pkg) in pkgutil.iter_modules([f'{dirname}/trackers']):
    import_module(f'{module_name}.trackers.{name}')


class Trackers(AttributesContainerDict[TrackerConfiguration]):
    """A list of trackers."""

    def __init__(
        self,
        **kwargs: Any,
    ):
        """
        Initialize the list of trackers.

        Args:
            kwargs: a list of trackers
        """
        super().__init__(
            values_type=TrackerConfiguration,
            items=kwargs,
        )
