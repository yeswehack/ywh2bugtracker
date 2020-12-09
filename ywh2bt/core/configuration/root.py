"""Models used for the root configuration."""
from typing import Any, Dict, Optional, Union, cast

from ywh2bt.core.configuration.attribute import Attribute, AttributesContainer
from ywh2bt.core.configuration.error import AttributesError
from ywh2bt.core.configuration.tracker import TrackerConfiguration, Trackers
from ywh2bt.core.configuration.validator import not_empty_validator
from ywh2bt.core.configuration.yeswehack import Programs, YesWeHackConfigurations

BugtrackersAttributeType = Union[
    Dict[str, TrackerConfiguration],
    Optional[Trackers],
    Attribute[Trackers],
]
BugtrackersInitType = Union[
    Optional[Trackers],
    Optional[Dict[str, TrackerConfiguration]],
    Optional[Dict[str, Any]],
]
YesWeHackAttributeType = Union[
    Dict[str, Any],
    Optional[YesWeHackConfigurations],
    Attribute[YesWeHackConfigurations],
]
YesWeHackInitType = Union[
    Optional[YesWeHackConfigurations],
    Optional[Dict[str, Any]],
]


class RootConfiguration(AttributesContainer):
    """A root configuration."""

    bugtrackers: BugtrackersAttributeType = Attribute.create(
        value_type=Trackers,
        short_description='Trackers',
        description='Trackers to be synchronized with YesWeHack',
        required=True,
        validator=not_empty_validator,
    )
    yeswehack: YesWeHackAttributeType = Attribute.create(
        value_type=YesWeHackConfigurations,
        short_description='YesWeHack',
        required=True,
        validator=not_empty_validator,
    )

    def __init__(
        self,
        bugtrackers: BugtrackersInitType = None,
        yeswehack: YesWeHackInitType = None,
        **kwargs: Any,
    ):
        """
        Initialize the configuration.

        Args:
            bugtrackers: a configuration for the bugtrackers
            yeswehack: a configuration for YesWeHack
            kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        self.bugtrackers = bugtrackers
        self.yeswehack = yeswehack

    def validate(self) -> None:
        """
        Validate the configuration.

        Raises:
            AttributesError: if the configuration is invalid

        # noqa: DAR401
        # noqa: DAR402
        """
        super_error: Optional[AttributesError] = None
        try:
            super().validate()
        except AttributesError as e:
            super_error = e

        errors = {}
        if self.yeswehack:
            errors.update(
                self._ensure_declared_trackers(
                    trackers=cast(Trackers, self.bugtrackers or {}),
                    yeswehack=cast(YesWeHackConfigurations, self.yeswehack or {}),
                ),
            )

        if errors:
            if not super_error:
                super_error = AttributesError(
                    message='Validation error',
                    errors={},
                    context=self,
                )
            super_error.errors.update(errors)

        if super_error:
            raise super_error

    def _ensure_declared_trackers(
        self,
        trackers: Trackers,
        yeswehack: YesWeHackConfigurations,
    ) -> Dict[str, AttributesError]:
        errors = {}
        for yeswehack_name, yeswehack_config in yeswehack.items():
            config_errors = self._ensure_bugtrackers_name(
                trackers=trackers,
                programs=cast(Programs, yeswehack_config.programs or {}),
            )
            for key, error in config_errors.items():
                errors[f'yeswehack.{yeswehack_name}.{key}'] = error
        return errors

    def _ensure_bugtrackers_name(
        self,
        trackers: Trackers,
        programs: Programs,
    ) -> Dict[str, AttributesError]:
        errors = {}
        for i, program in enumerate(programs):
            if not program.bugtrackers_name:
                continue
            for j, bugtracker_name in enumerate(program.bugtrackers_name):
                if bugtracker_name not in trackers:
                    errors[f'programs[{i}].bugtrackers_name[{j}]'] = AttributesError(
                        message=f'Bugtracker not {repr(bugtracker_name)} declared in bugtrackers',
                        errors={},
                        context=self,
                    )
        return errors
