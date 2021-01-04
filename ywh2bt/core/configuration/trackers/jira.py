"""Models used for the configuration of a Jira tracker."""
from typing import Any, Optional, Text

from ywh2bt.core.configuration.attribute import Attribute, BoolAttributeType, StrAttributeType
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.validator import not_blank_validator, url_validator


class JiraConfiguration(TrackerConfiguration):
    """A class describing the configuration of a Jira tracker."""

    url: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='API URL',
        description='Base URL of the Jira server',
        required=True,
        validator=url_validator,
    )
    login: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Login',
        description='User login for the Jira server',
        required=True,
        secret=False,
        validator=not_blank_validator,
    )
    password: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Password',
        description='User password or API token for the Jira server',
        required=True,
        secret=True,
        validator=not_blank_validator,
    )
    project: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Project slug',
        description='Jira slug',
        required=True,
        validator=not_blank_validator,
    )
    verify: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Verify SSL',
        description='Verify SSL certs',
        default=True,
    )
    issuetype: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Issue type',
        description='Issue type (sensitive to account language)',
        default='Task',
    )
    issue_closed_status: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Issue closed status',
        description='Issue closed status (sensitive to account language)',
        default='Closed',
    )

    def __init__(
        self,
        url: Optional[Text] = None,
        login: Optional[Text] = None,
        password: Optional[Text] = None,
        project: Optional[Text] = None,
        verify: Optional[bool] = None,
        issuetype: Optional[Text] = None,
        issue_closed_status: Optional[Text] = None,
        **kwargs: Any,
    ):
        """
        Initialize the configuration.

        Args:
            url: a Jira API URL
            login: a Jira API user login
            password: a Jira API user password
            project: a Jira project name
            verify: a flag indicating whether to check SSL/TLS connection
            issuetype: a Jira issue type
            issue_closed_status: a Jira name when the issue is closed
            kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        self.url = url
        self.login = login
        self.password = password
        self.project = project
        self.verify = verify
        self.issuetype = issuetype
        self.issue_closed_status = issue_closed_status


TrackerConfiguration.register_subtype(
    subtype_name='jira',
    subtype_class=JiraConfiguration,
)
