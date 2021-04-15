"""Models used for the configuration of a ServiceNow tracker."""
from typing import (
    Any,
    Optional,
    Text,
)

from ywh2bt.core.configuration.attribute import (
    Attribute,
    BoolAttributeType,
    StrAttributeType,
)
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.validator import (
    host_validator,
    not_blank_validator,
)


class ServiceNowConfiguration(TrackerConfiguration):
    """A class describing the configuration of a ServiceNow tracker."""

    host: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Instance host',
        description='Host of the ServiceNow instance',
        required=True,
        validator=host_validator,
    )
    login: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Login',
        description='User login for the ServiceNow instance',
        required=True,
        secret=False,
        validator=not_blank_validator,
    )
    password: StrAttributeType = Attribute.create(
        value_type=str,
        short_description='Password',
        description='User password for the ServiceNow instance',
        required=True,
        secret=True,
        validator=not_blank_validator,
    )
    use_ssl: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Use SSL',
        description='Use SSL connection',
        default=True,
    )
    verify: BoolAttributeType = Attribute.create(
        value_type=bool,
        short_description='Verify SSL',
        description='Verify SSL certs',
        default=True,
    )

    def __init__(
        self,
        host: Optional[Text] = None,
        login: Optional[Text] = None,
        password: Optional[Text] = None,
        use_ssl: Optional[bool] = None,
        verify: Optional[bool] = None,
        **kwargs: Any,
    ):
        """
        Initialize the configuration.

        Args:
            host: a ServiceNow instance host
            login: a ServiceNow user login
            password: a ServiceNow user password
            use_ssl: a flag indicating whether to use SSL/TLS connection
            verify: a flag indicating whether to check SSL/TLS connection
            kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        self.host = host
        self.login = login
        self.password = password
        self.use_ssl = use_ssl
        self.verify = verify


TrackerConfiguration.register_subtype(
    subtype_name='servicenow',
    subtype_class=ServiceNowConfiguration,
)
