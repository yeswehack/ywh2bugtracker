import unittest
from typing import (
    Optional,
    cast,
)

from ywh2bt.core.configuration.attribute import Attribute
from ywh2bt.core.configuration.subtypable import SubtypeError
from ywh2bt.core.configuration.tracker import (
    TrackerConfiguration,
    Trackers,
)


class TestTracker(unittest.TestCase):
    def test_register_tracker(self) -> None:
        class MyTracker(TrackerConfiguration):
            prop1 = Attribute.create(
                value_type=str,
                required=True,
            )

        TrackerConfiguration.register_subtype("my-tracker", MyTracker)

        t1 = MyTracker()
        t1.prop1 = "foo"
        self.assertEqual(
            t1.export(),
            dict(
                type="my-tracker",
                prop1="foo",
            ),
        )

    def test_unregistered_tracker(self) -> None:
        class MyUnregisteredTracker(TrackerConfiguration):
            prop = Attribute.create(
                value_type=str,
                required=True,
            )

        with self.assertRaises(expected_exception=SubtypeError):
            MyUnregisteredTracker()


class TestTrackers(unittest.TestCase):
    def test_trackers_loose_cast(self) -> None:
        class ATracker(TrackerConfiguration):
            name = Attribute.create(
                value_type=str,
            )

            def __init__(
                self,
                name: Optional[str],
            ):
                super().__init__()
                self.name = name

        TrackerConfiguration.register_subtype("a-tracker", ATracker)

        class CTracker(TrackerConfiguration):
            description = Attribute.create(
                value_type=str,
            )

            def __init__(
                self,
                description: Optional[str],
            ):
                super().__init__()
                self.description = description

        TrackerConfiguration.register_subtype("c-tracker", CTracker)

        trackers = Trackers(
            a=dict(
                type="a-tracker",
                name="my tracker",
            ),
            c=dict(
                type="c-tracker",
                description="this a tracker of type c",
            ),
        )
        self.assertIsInstance(trackers["a"], ATracker)
        self.assertEqual("my tracker", cast(ATracker, trackers["a"]).name)
        self.assertIsInstance(trackers["c"], CTracker)
        self.assertEqual("this a tracker of type c", cast(CTracker, trackers["c"]).description)
