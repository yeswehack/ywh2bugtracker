"""Models used for the configuration of a GitHub tracker."""
from typing import Any, Dict, Optional, Text

from ywh2bt.core.configuration.attribute import Attribute, BoolAttributeType, StrAttributeType
from ywh2bt.core.configuration.error import AttributesError, MissingAttributeError
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.validator import not_blank_validator, url_validator


class GitHubConfiguration(TrackerConfiguration):
    """A class describing the configuration of a GitHub tracker."""

    url: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='API URL',
        description='Base URL of the GitHub API',
        default='https://api.github.com',
        validator=url_validator,
    )
    token: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='API token',
        description='User private token for the GitHub API',
        required=True,
        secret=True,
        validator=not_blank_validator,
    )
    project: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Project path',
        description='Path to the project on GitHub',
        required=True,
        validator=not_blank_validator,
    )
    verify: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Verify TLS',
        description="Verify server's TLS certificate",
        default=True,
    )
    github_cdn_on: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Use CDN',
        description='Enable or disable saving attachment file to GitHub CDN',
        default=False,
    )
    login: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Login',
        description='User login for the GitHub server. Required only if github_cdn_on is true',
        secret=False,
    )
    password: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Password',
        description='User password for the GitHub server. Required only if github_cdn_on is true',
        secret=True,
    )

    def __init__(
        self,
        url: Optional[Text] = None,
        token: Optional[Text] = None,
        project: Optional[Text] = None,
        verify: Optional[bool] = None,
        github_cdn_on: Optional[bool] = None,
        login: Optional[Text] = None,
        password: Optional[Text] = None,
        **kwargs: Any,
    ):
        """
        Initialize the configuration.

        Args:
            url: a GitHub API URL
            token: a GitHub API token
            project: a GitHub project name
            verify: a flag indicating whether to check SSL/TLS connection
            github_cdn_on: a flag indicating whether to save attachment file to GitHub CDN
            login: a GitLab user login ; used when github_cdn_on is true
            password: a GitLab user password ; used when github_cdn_on is true
            kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        self.url = url
        self.token = token
        self.project = project
        self.verify = verify
        self.github_cdn_on = github_cdn_on
        self.login = login
        self.password = password

    def validate(self) -> None:
        """
        Validate the container.

        # noqa: DAR401, DAR402

        Raises:
            AttributesError: if the container is not valid
        """
        super_error: Optional[AttributesError] = None
        try:
            super().validate()
        except AttributesError as e:
            super_error = e

        errors = {}
        if self.github_cdn_on:
            errors.update(
                self._ensure_login_password(),
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

    def _ensure_login_password(
        self,
    ) -> Dict[str, MissingAttributeError]:
        errors = {}
        if self.login is None:
            errors['login'] = MissingAttributeError(
                message="Expecting value for attribute 'login' when 'github_on_cdn' is True",
                context=self,
            )
        if self.password is None:
            errors['password'] = MissingAttributeError(
                message="Expecting value for attribute 'password' when 'github_on_cdn' is True",
                context=self,
            )
        return errors


TrackerConfiguration.register_subtype(
    subtype_name='github',
    subtype_class=GitHubConfiguration,
)
