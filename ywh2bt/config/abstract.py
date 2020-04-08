from abc import abstractmethod
from ywh2bt.logging import logger
from colorama import Fore, Style

from requests.exceptions import SSLError

import sys
import copy
from colorama import Fore, Style

from ywh2bt.utils import read_input
from abc import abstractmethod

__all__ = ["ConfigObject", "BugTrackerConfig"]


"""
Base Configuration classes.
"""


class ConfigObject(object):

    ############################################################
    ######################## Constructor #######################
    ############################################################
    """
    Base class for all configuration class.
    """

    def __init__(self, keys, type_name, **config):
        self.validate(keys, type_name, config)

    ############################################################
    ###################### Static method #######################
    ############################################################

    @staticmethod
    def validate(keys, type_name, config):
        """
        Validate mandatory keys send, and exit if error detected.

        :param list keys: list of key needed in config.
        :param str type_name: keyword identifier of class caller for logging error.
        :param dict config: config dictionary loaded from config yaml file.
        """
        errors = []
        for key in keys:
            if key not in config:
                errors.append(key)
        if errors:
            logger.critical(
                "{} not set in {} configuration part".format(
                    ", ".join(errors), type_name
                )
            )
            sys.exit(120)

    ############################################################
    ####################### Class method #######################
    ############################################################
    @classmethod
    def check_secret_keys(cls, no_interactive, secret_keys, config):
        """
        Validate secret keys in config and log warning if error detected.

        :param bool no_interactive: is it execute in no_interactive mode ?
        :param list secret_keys: keys needed in config if secret is active.
        :param dict config: config dictionary loaded from config yaml file.
        """
        secrect_in_config = []
        for s in secret_keys:
            if s in config:
                secrect_in_config.append(s)
        if secrect_in_config and not no_interactive:
            logger.warning(
                "'{}' secret parameter hardcoded in your configuration".format(
                    ", ".join(secrect_in_config)
                )
            )


class BugTrackerConfig(ConfigObject):

    """
    Loader of a bugtracker config.


    :attr str bugtracker_type: name identifier of the current bugtracker config class
    :attr dict _description: description of given keys.
    :attr list mandatory_keys: keys needed in configuration file.
    :attr list secret_keys: keys define as secret (asked in interactive mode).
    :attr dict optional_keys: keys with default value.
    """

    ############################################################
    ######################## Attributes ########################
    ############################################################
    bugtracker_type = "abstract"
    _description = dict()
    mandatory_keys = []
    secret_keys = []
    optional_keys = dict()
    conditional_keys = dict()
    ############################################################
    ######################## Constructor #######################
    ############################################################
    def __new__(
        cls, name, no_interactive=False, configure_mode=False, **config
    ):
        secrect_in_config = []
        cls.check_secret_keys(no_interactive, cls.secret_keys, config)
        cls._set_properties()
        inst = super().__new__(cls)
        return inst

    def __init__(
        self, name, no_interactive=False, configure_mode=False, **config
    ):
        self._bugtracker = None
        keys = []
        if config or not configure_mode:
            keys += self.mandatory_keys
            if no_interactive:
                keys += self.secret_keys
        type_ = config.get("type", self.bugtracker_type)
        if not "project" in [
            *self.mandatory_keys,
            *self.secret_keys,
            *self.optional_keys_list(),
        ]:
            logger.critical(
                "'project' key not present in mandatory_keys, secret_keys or optional_keys for {} class".format(
                    self.__class__
                )
            )
            sys.exit(210)
        super().__init__(keys, "{} BugTracker".format(type_.title()), **config)
        self._name = name
        self._type = type_
        self._no_interactive = no_interactive
        self._configure_mode = configure_mode

        if config or not configure_mode:
            self._configure_attributes(**config)

        if configure_mode:
            self.configure()

        if not no_interactive:
            self.get_interactive_info()

        if not self._bugtracker:
            self._set_bugtracker()

    ############################################################
    ##################### Instance methods #####################
    ############################################################

    def configure(self, test=True):
        """
        Main methods to configure the implement bugtracker config class.

        :param bool test: if True, test client connexion.
        """
        self.read_mandatory()
        self.read_optional()
        if self.no_interactive:
            self.read_secret()
        self.read_conditional(interactive=self.no_interactive, configure=True)
        self.user_config()
        if self.no_interactive:
            self._set_bugtracker()
            if test:
                self.test_project()

    def get_interactive_info(self):
        """
        Get secret info as interactive.
        """
        self.read_secret()
        self.read_conditional(interactive=True, configure=False)

    def read_mandatory(self):
        """
        Ask user to write values for each mandatories keys.
        """
        for key in self.mandatory_keys:
            desc = ""
            if key in self._description:
                desc += (
                    Fore.GREEN + f" - ({self._description[key]})" + Fore.RESET
                )
            setattr(
                self,
                "_" + key,
                read_input(
                    Fore.BLUE
                    + "{}{}: ".format(key.title(), desc)
                    + Style.RESET_ALL
                ),
            )

    def read_conditional(self, interactive=False, configure=False):
        """
        Ask user to write values for each conditional keys if condition is True.
        """
        for key, info in self.conditional_keys.items():
            desc = ""
            if key in self._description:
                desc += (
                    Fore.GREEN + f" - ({self._description[key]})" + Fore.RESET
                )
            default = info.get("default", None)
            secret = info.get("secret", False)
            condition = info["condition"]
            if condition(self):
                if secret and interactive:
                    setattr(
                        self,
                        "_" + key,
                        read_input(
                            Fore.GREEN
                            + self.type.title()
                            + Fore.BLUE
                            + " {}{}{}: ".format(
                                "{}".format(key.title())
                                + (
                                    " for {}".format(
                                        Fore.GREEN + self.login + Fore.BLUE
                                    )
                                    if hasattr(self, "login")
                                    else ""
                                )
                                + (
                                    " on {}".format(
                                        Fore.GREEN + self.url + Fore.BLUE
                                    )
                                    if hasattr(self, "url")
                                    else ""
                                ),
                                " [default='{}']"
                                if default is not None
                                else "",
                                desc,
                            )
                            + Style.RESET_ALL
                            or default,
                            secret=True,
                        ),
                    )
                elif not secret and default is not None and configure:
                    setattr(
                        self,
                        "_" + key,
                        read_input(
                            Fore.GREEN
                            + self.type.title()
                            + Fore.BLUE
                            + " {} [default='{}']{}: ".format(
                                key.title(), default, desc
                            )
                            + Style.RESET_ALL
                        )
                        or default,
                    )
                elif not secret and default is None and configure:
                    setattr(
                        self,
                        "_" + key,
                        read_input(
                            Fore.BLUE
                            + "{}{}: ".format(key.title(), desc)
                            + Style.RESET_ALL
                        ),
                    )

    def read_optional(self):
        """
        Ask user to write values for each optinals keys.
        """
        for key, default in self.optional_keys.items():
            desc = ""
            if key in self._description:
                desc += (
                    Fore.GREEN + f" - ({self._description[key]})" + Fore.RESET
                )
            setattr(
                self,
                "_" + key,
                read_input(
                    Fore.GREEN
                    + self.type.title()
                    + Fore.BLUE
                    + " {} [default='{}']{}: ".format(
                        key.title(), default, desc
                    )
                    + Style.RESET_ALL
                )
                or default,
            )

    def read_secret(self):
        """
        Ask user to write values for each secrets keys.
        """
        for key in self.secret_keys:
            desc = ""
            if key in self._description:
                desc += (
                    Fore.GREEN + f" - ({self._description[key]})" + Fore.RESET
                )
            setattr(
                self,
                "_" + key,
                read_input(
                    Fore.BLUE
                    + "{}{}: ".format(
                        "{}".format(key.title())
                        + (
                            " for {}".format(
                                Fore.GREEN + self.login + Fore.BLUE
                            )
                            if hasattr(self, "login")
                            else ""
                        )
                        + (
                            " on {}".format(Fore.GREEN + self.url + Fore.BLUE)
                            if hasattr(self, "url")
                            else ""
                        ),
                        desc,
                    )
                    + Style.RESET_ALL,
                    secret=True,
                ),
            )

    def test_project(self):
        """
        Test connexion to the project on the client
        """
        if self.no_interactive:
            logger.info(
                "Testing project: {}{}{}".format(
                    Fore.BLUE, self.project, Style.RESET_ALL
                )
            )
        try:
            self._bugtracker.get_project()
            if self.no_interactive:
                logger.info(
                    "{} status : {}OK{}".format(
                        self.project, Fore.GREEN, Style.RESET_ALL
                    )
                )
            else:
                logger.info(
                    "{project} ok on {url}".format(
                        project=self.project, url=self.url
                    )
                )
        except Exception as e:
            if self.no_interactive:
                logger.info(
                    "{} status : {}KO{}".format(
                        self.project, Fore.RED, Style.RESET_ALL
                    )
                )
                self.configure(test=False)
            else:
                logger.error(
                    "{project} ko on {url}".format(
                        project=self.project, url=self.url
                    )
                )
                sys.exit(-210)

    def to_dict(self):
        """
        Map object to dictionary
        """
        component = {"type": self.type}
        for attr in [*self.mandatory_keys, *self.optional_keys_list()]:
            component[attr] = self.__getattribute__(attr)

        for attr, info in self.conditional_keys.items():
            condition = info["condition"]
            secret = info.get("secret", False)
            default = info.get("default", None)
            if (secret and self.no_interactive) or not secret:
                component[attr] = self.__getattribute__(attr)

        if self.no_interactive:
            for attr in self.secret_keys:
                component[attr] = self.__getattribute__(attr)
        return {self.name: component}

    def user_config(self):
        """
        Methods to implement for special user interaction in configuration mode.
        """
        pass

    def verify(self):
        """
        Test project connexion
        """
        self.test_project()

    def _configure_attributes(self, **config):
        """
            Append protected attribute for each keys in mandatory keys and optional_keys, secret keys if no_interactive,
            in aggreement with config file.
            """
        for attr in self.mandatory_keys:
            setattr(self, "_" + attr, config[attr])
        for attr in self.secret_keys:
            setattr(
                self, "_" + attr, config[attr] if self._no_interactive else ""
            )
        for attr, default in self.optional_keys.items():
            setattr(self, "_" + attr, config.get(attr, default))
        for attr, info in self.conditional_keys.items():
            default = info.get("default", None)
            secret = info.get("secret", False)
            condition = info["condition"]
            if condition(self):
                if secret:
                    if default is not None:
                        setattr(
                            self,
                            "_" + attr,
                            config.get(attr, default)
                            if self._no_interactive
                            else "",
                        )
                    else:
                        setattr(
                            self,
                            "_" + attr,
                            config[attr] if self._no_interactive else "",
                        )
                elif (
                    default is not None
                ):  # secret == False, default is not None
                    setattr(self, "_" + attr, config.get(attr, default))
                else:  #  secret == False, default is None => mandatory
                    setattr(self, "_" + attr, config[attr])

    def _get_bugtracker(self, *args, **kwargs):
        """
        Configure bugtracker client and test if is reachable.
        Args and Kwargs are parameters for bugtracker client class.
        """
        try:
            self._bugtracker = self.client(*args, **kwargs)
            if self.no_interactive:
                logger.info(
                    "{} ({}) status: {}".format(
                        self.bugtracker_type,
                        self.name,
                        "{}OK{}".format(Fore.GREEN, Style.RESET_ALL),
                    )
                )
            else:
                logger.info(
                    "Login ok on {type} ({url})".format(
                        type=self.type, url=self.url
                    )
                )
        except SSLError as e:
                logger.error(
                    "Certificate verification failed. If you accept this risk, "\
                    + "you can update configuration with verifiy:false in {} section".format(self.name)
                )
                sys.exit(-200)
        except Exception as e:
            if self.no_interactive:
                logger.info(
                    "{} ({}) status: {}".format(
                        self.bugtracker_type,
                        self.name,
                        "{}KO{}".format(Fore.RED, Style.RESET_ALL),
                    )
                )
            else:
                logger.error(
                    "Login fail on {type} ({url}) with error {error}".format(
                        type=self.type, url=self.url, error=str(e)
                    )
                )
                raise e
                sys.exit(-200)
            self.configure()

    def set_yeswehack_domain(self, ywh_domain):
        self._bugtracker.set_yeswehack_domain(ywh_domain)

    ############################################################
    ####################### Class methods ######################
    ############################################################
    @classmethod
    def conditional_keys_list(cls):
        """
        Map conditional_keys Keys to list object.
        """
        return list(cls.conditional_keys.keys())

    @classmethod
    def optional_keys_list(cls):
        """
        Map optional_keys Keys to list object.
        """
        return list(cls.optional_keys.keys())

    @classmethod
    def _set_properties(cls):
        """
        Set get properties for each keys define in mandatory, optonial and secret keys.
        """

        def set_item(cls, attr):
            def func(self):
                return self.__getattribute__("_" + attr)

            setattr(cls, attr, property(copy.copy(func)))

        for attr in [
            *cls.mandatory_keys,
            *cls.secret_keys,
            *cls.optional_keys_list(),
            *cls.conditional_keys_list(),
        ]:
            set_item(cls, attr)

    ############################################################
    ##################### Abstract methods #####################
    ############################################################

    @abstractmethod
    def _set_bugtracker(self):
        """
        Method to setup bugtracker class.
        """
        pass

    ############################################################
    ######################## Properties ########################
    ############################################################
    @property
    def no_interactive(self):
        return self._no_interactive

    @property
    def bugtracker(self):
        return self._bugtracker

    @property
    def configure_mode(self):
        return self._configure_mode

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def bugtracker(self):
        return self._bugtracker
