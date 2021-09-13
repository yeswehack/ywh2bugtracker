"""Models used for the configuration of YesWeHack."""
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    cast,
)

from ywh2bt.core.configuration.attribute import (
    Attribute,
    AttributesContainer,
    AttributesContainerDict,
    AttributesContainerList,
    BoolAttributeType,
    ExportableList,
    StrAttributeType,
)
from ywh2bt.core.configuration.validator import (
    length_one_validator,
    not_blank_validator,
    not_empty_validator,
    url_validator,
)


class Bugtrackers(ExportableList[str, str]):
    """A list of bugtrackers."""


BugtrackersNameAttributeType = Union[
    Optional[Bugtrackers],
    Attribute[Bugtrackers],
]
BugtrackersNameInitType = Union[
    Optional[Bugtrackers],
    Optional[List[str]],
]


class SynchronizeOptions(AttributesContainer):
    """Synchronization option."""

    upload_private_comments: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Upload private comments',
        description='Upload the report private comments into the bug tracker',
        default=False,
    )
    upload_public_comments: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Upload public comments',
        description='Upload the report public comments into the bug tracker',
        default=False,
    )
    upload_cvss_updates: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Upload CVSS updates',
        description='Upload the report CVSS updates into the bug tracker',
        default=False,
    )
    upload_details_updates: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Upload details updates',
        description='Upload the report details updates into the bug tracker',
        default=False,
    )
    upload_priority_updates: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Upload priority updates',
        description='Upload the report priority updates into the bug tracker',
        default=False,
    )
    upload_rewards: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Upload rewards',
        description='Upload the report rewards into the bug tracker',
        default=False,
    )
    upload_status_updates: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Upload status updates',
        description='Upload the report status updates into the bug tracker',
        default=False,
    )
    recreate_missing_issues: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Recreate missing issues',
        description=(
            'Recreate issues that were created by a previous synchronization '
            + 'but are not found into the bug tracker anymore'
        ),
        default=True,
    )

    def __init__(
        self,
        upload_private_comments: Optional[bool] = None,
        upload_public_comments: Optional[bool] = None,
        upload_details_updates: Optional[bool] = None,
        upload_cvss_updates: Optional[bool] = None,
        upload_priority_updates: Optional[bool] = None,
        upload_rewards: Optional[bool] = None,
        upload_status_updates: Optional[bool] = None,
        recreate_missing_issues: Optional[bool] = None,
        **kwargs: Any,
    ):
        """
        Initialize self.

        Args:
            upload_private_comments: a flag indicating whether to upload private comments to the bug tracker
            upload_public_comments: a flag indicating whether to upload public comments to the bug tracker
            upload_cvss_updates: a flag indicating whether to upload CVSS updates to the bug tracker
            upload_details_updates: a flag indicating whether to upload details updates to the bug tracker
            upload_priority_updates: a flag indicating whether to upload priority updates into the bug tracker
            upload_rewards: a flag indicating whether to upload rewards to the bug tracker
            upload_status_updates: a flag indicating whether to upload status updates to the bug tracker
            recreate_missing_issues: a flag indicating whether to recreate missing issues
            kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        self.upload_private_comments = upload_private_comments
        self.upload_public_comments = upload_public_comments
        self.upload_cvss_updates = upload_cvss_updates
        self.upload_details_updates = upload_details_updates
        self.upload_priority_updates = upload_priority_updates
        self.upload_rewards = upload_rewards
        self.upload_status_updates = upload_status_updates
        self.recreate_missing_issues = recreate_missing_issues


SynchronizeOptionsAttributeType = Union[
    Dict[str, bool],
    SynchronizeOptions,
    Attribute[SynchronizeOptions],
]
SynchronizeOptionsInitType = Union[
    Optional[SynchronizeOptions],
    Optional[Dict[str, bool]],
]


class FeedbackOptions(AttributesContainer):
    """Feedback option."""

    download_tracker_comments: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Download bug trackers comments',
        description='Download comments from the bug tracker and put them into the report',
        default=False,
    )
    issue_closed_to_report_afv: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Issue closed to report AFV',
        description='Set the report status to "Ask for Fix Verification" when the tracker issue is closed',
        default=False,
    )

    def __init__(
        self,
        download_tracker_comments: Optional[bool] = None,
        issue_closed_to_report_afv: Optional[bool] = None,
        **kwargs: Any,
    ):
        """
        Initialize self.

        Args:
            download_tracker_comments:
            a flag indicating whether to download comments from the bug tracker and put them into the report
            issue_closed_to_report_afv:
            a flag indicating whether to set report status to "Ask for Fix Verification" when tracker issue is closed
            kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        self.download_tracker_comments = download_tracker_comments
        self.issue_closed_to_report_afv = issue_closed_to_report_afv


FeedbackOptionsAttributeType = Union[
    Dict[str, bool],
    FeedbackOptions,
    Attribute[FeedbackOptions],
]
FeedbackOptionsInitType = Union[
    Optional[FeedbackOptions],
    Optional[Dict[str, bool]],
]


class Program(AttributesContainer):
    """A program and its associated bugtrackers."""

    slug: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Program slug',
        description='Program slug',
        required=True,
        validator=not_blank_validator,
    )
    synchronize_options: SynchronizeOptionsAttributeType = Attribute.create(
        value_type=SynchronizeOptions,
        short_description='Synchronization options',
        required=True,
    )
    feedback_options: FeedbackOptionsAttributeType = Attribute.create(
        value_type=FeedbackOptions,
        short_description='Feedback options',
        required=True,
    )
    bugtrackers_name: BugtrackersNameAttributeType = Attribute.create(
        value_type=Bugtrackers,
        short_description='Bug trackers',
        description='Bug trackers names',
        required=True,
        validator=length_one_validator,
    )

    def __init__(
        self,
        slug: Optional[str] = None,
        synchronize_options: SynchronizeOptionsInitType = None,
        feedback_options: FeedbackOptionsInitType = None,
        bugtrackers_name: BugtrackersNameInitType = None,
        **kwargs: Any,
    ):
        """
        Initialize the program.

        Args:
            slug: a program slug
            synchronize_options: synchronization options
            feedback_options: feedback options
            bugtrackers_name: a list of bugtrackers
            kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        self.slug = slug
        if not synchronize_options:
            synchronize_options = SynchronizeOptions()
        self.synchronize_options = synchronize_options
        if not feedback_options:
            feedback_options = FeedbackOptions()
        self.feedback_options = feedback_options
        if bugtrackers_name:
            if isinstance(bugtrackers_name, List):
                self.bugtrackers_name = Bugtrackers(bugtrackers_name)
            else:
                self.bugtrackers_name = cast(Bugtrackers, bugtrackers_name)


class Programs(AttributesContainerList[Program]):
    """A list of programs."""

    def __init__(
        self,
        items: Optional[List[Any]] = None,
    ) -> None:
        """
        Initialize the list of programs.

        Args:
            items: a list of programs
        """
        super().__init__(
            values_type=Program,
            items=items,
        )


ProgramsAttributeType = Union[
    List[Union[Program, Dict[str, Any]]],
    Optional[Programs],
    Attribute[Programs],
]
ProgramsInitType = Union[
    Optional[Programs],
    Optional[List[Union[Program, Dict[str, Any]]]],
]


class YesWeHackConfiguration(AttributesContainer):
    """A configuration for YesWeHack."""

    api_url: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='API URL',
        description='Base URL of the YWH API',
        default='https://api.yeswehack.com',
        validator=url_validator,
    )
    pat: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Personal Access Token',
        description='Personal Access Token',
        required=True,
        secret=True,
        validator=not_blank_validator,
    )
    verify: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Verify TLS',
        description="Verify server's TLS certificate",
        default=True,
    )
    programs: ProgramsAttributeType = Attribute.create(
        value_type=Programs,
        short_description='Programs',
        description='Programs',
        required=True,
        validator=not_empty_validator,
    )

    def __init__(
        self,
        api_url: Optional[str] = None,
        pat: Optional[str] = None,
        verify: Optional[bool] = None,
        programs: ProgramsInitType = None,
        **kwargs: Any,
    ):
        """
        Initialize the configuration.

        Args:
            api_url: a YesWeHack API URL
            pat: a Personal Access Token
            verify: a flag indicating whether to check SSL/TLS connection
            programs: a list of Programs
            kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        self.api_url = api_url
        self.pat = pat
        self.verify = verify
        self.programs = programs


class YesWeHackConfigurations(AttributesContainerDict[YesWeHackConfiguration]):
    """A list of YesWeHack configurations."""

    def __init__(
        self,
        **kwargs: Any,
    ):
        """
        Initialize the list of configurations.

        Args:
            kwargs: a list of configurations
        """
        super().__init__(
            values_type=YesWeHackConfiguration,
            items=kwargs,
        )
