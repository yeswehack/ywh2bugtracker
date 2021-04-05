"""Models used for the configuration of a GitLab tracker."""
from typing import Any, Optional, Text

from ywh2bt.core.configuration.attribute import Attribute, BoolAttributeType, StrAttributeType
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.validator import not_blank_validator, url_validator


class GitLabConfiguration(TrackerConfiguration):
    """A class describing the configuration of a GitLab tracker."""

    url: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='API URL',
        description='Base URL of the GitLab server',
        default='https://gitlab.com',
        validator=url_validator,
    )
    token: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='API token',
        description='User private token for the GitLab API',
        required=True,
        secret=True,
        validator=not_blank_validator,
    )
    project: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Project path',
        description='Path to the project on GitLab',
        required=True,
        validator=not_blank_validator,
    )
    verify: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Verify TLS',
        description="Verify server's TLS certificate",
        default=True,
    )
    confidential: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Confidential issues',
        description='Mark created issues as confidential',
        default=False,
    )

    def __init__(
        self,
        url: Optional[Text] = None,
        token: Optional[Text] = None,
        project: Optional[Text] = None,
        verify: Optional[bool] = None,
        confidential: Optional[bool] = None,
        **kwargs: Any,
    ):
        """
        Initialize the configuration.

        Args:
            url: a GitLab API URL
            token: a GitLab API token
            project: a GitLab project name
            verify: a flag indicating whether to check SSL/TLS connection
            confidential: a flag indicating whether to mark created issues as confidential
            kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        self.url = url
        self.token = token
        self.project = project
        self.verify = verify
        self.confidential = confidential


TrackerConfiguration.register_subtype(
    subtype_name='gitlab',
    subtype_class=GitLabConfiguration,
)
