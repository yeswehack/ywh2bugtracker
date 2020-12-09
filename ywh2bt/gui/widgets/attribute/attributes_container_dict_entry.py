"""Models and functions used for attributes container dict GUI."""
from dataclasses import dataclass

from ywh2bt.core.configuration.attribute import AttributesContainer


@dataclass
class AttributesContainerDictEntry:
    """A class describing an entry of an AttributesContainerDict instance."""

    key: str
    value: AttributesContainer
