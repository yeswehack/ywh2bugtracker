from abc import abstractmethod
from ywh2bt.logging import logger
from colorama import Fore, Style

import sys
import copy
from colorama import Fore, Style

from ywh2bt.utils import read_input
from abc import abstractmethod

__all__ = ["ConfigObject", "BugTrackerConfig"]


class ConfigObject(object):
    def __init__(self, keys, type_name, **config):
        self.validate(keys, type_name, config)

    @staticmethod
    def validate(keys, type_name, config):
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

    @classmethod
    def check_secret_keys(cls, no_interactive, secret_keys, config):
        secrect_in_config = []
        for s in secret_keys:
            if s in config:
                secrect_in_config.append(s)
        if secrect_in_config and not no_interactive:
            logger.warning("{} secrets key-s in configuration but non interactive is not actif ".format(", ".join(secrect_in_config)))
class BugTrackerConfig(ConfigObject):

    bugtracker_type = "abstract"
    _description = dict()
    mandatory_keys = []
    secret_keys = []
    optional_keys = dict()


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
        if not 'project' in [*self.mandatory_keys, *self.secret_keys, *self.optional_keys_list()]:
            logger.critical("'project' key not present in mandatory_keys, secret_keys or optional_keys for {} class".format(self.__class__))
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

    @classmethod
    def optional_keys_list(cls):
        return list(cls.optional_keys.keys())

    @classmethod
    def _set_properties(cls):
        def set_item(cls, attr):
            def func(self):
                return self.__getattribute__("_" + attr)

            setattr(cls, attr, property(copy.copy(func)))

        for attr in [
            *cls.mandatory_keys,
            *cls.secret_keys,
            *cls.optional_keys_list(),
        ]:
            set_item(cls, attr)

    def _configure_attributes(self, **config):
        for attr in self.mandatory_keys:
            setattr(self, "_" + attr, config[attr])
        for attr in self.secret_keys:
            setattr(
                self, "_" + attr, config[attr] if self._no_interactive else ""
            )
        for attr, default in self.optional_keys.items():
            setattr(self, "_" + attr, config.get(attr, default))

    def _get_bugtracker(self, *args, **kwargs):
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

    def get_interactive_info(self):
        self.read_secret()

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

    def configure(self, test=True):
        self.read_mandatory()
        self.read_optional()
        if self.no_interactive:
            self.read_secret()
            self._set_bugtracker()
            if test:
                self.test_project()

    def verify(self):
        self.test_project()


    @abstractmethod
    def _set_bugtracker(self):
        pass

    def read_mandatory(self):
        for key in self.mandatory_keys:
            desc = ""
            if key in self._description:
                desc += Fore.GREEN + f" - ({self._desc[key]})" + Fore.RESET
            setattr(self, '_' + key, read_input(Fore.BLUE + "{}{}: ".format(key.title(), desc) + Style.RESET_ALL))

    def read_optional(self):
        for key, default in self.optional_keys.items():
            desc = ""
            if key in self._description:
                desc += Fore.GREEN + f" - ({self._desc[key]})" + Fore.RESET
            setattr(self, '_' + key, read_input(Fore.GREEN + self.type.title() + Fore.BLUE + " {} [default='{}']{}: ".format(key.title(), default, desc) + Style.RESET_ALL) or default)

    def read_secret(self):
        for key in self.secret_keys:
            desc = ""
            if key in self._description:
                desc += Fore.GREEN + f" - ({self._desc[key]})" + Fore.RESET
            setattr(self, '_' + key, read_input(Fore.BLUE + "{}{}: ".format("{}".format(key.title()) +
            (" for {}".format(Fore.GREEN + self.login + Fore.BLUE) if hasattr(self, 'login') else "") +
            (" on {}".format(Fore. GREEN + self.url + Fore.BLUE) if hasattr(self, 'url') else "" ), desc) + Style.RESET_ALL, secret=True))

    def test_project(self):
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
        component = {"type": self.type}
        for attr in [*self.mandatory_keys, *self.optional_keys_list()]:
            component[attr] = self.__getattribute__(attr)

        if self.no_interactive:
            for attr in self.secret_keys:
                component[attr] = self.__getattribute__(attr)
        return {self.name: component}
