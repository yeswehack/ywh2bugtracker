# -*- encoding: utf-8 -*-
import os
import sys
import copy
import yaml
import pyotp
from ywh2bt.logging import logger
from pathlib import Path
from colorama import Fore, Style
from yeswehack.api import YesWeHack
from yeswehack.exceptions import (
    BadCredentials,
    ObjectNotFound,
    InvalidResponse,
    TOTPLoginEnabled,
)
from ywh2bt.utils import read_input
from abc import abstractmethod
from ywh2bt.utils import get_all_subclasses
from ywh2bt.exceptions import BugTrackerNotFound, MultipleBugTrackerMacth


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


class BugTrackerConfig(ConfigObject):

    bugtracker_type = "abstract"

    def __init__(
        self, name, keys, no_interactive=False, configure_mode=False, **config
    ):
        type_ = config.get("type", self.bugtracker_type)
        super().__init__(keys, "{} BugTracker".format(type_.title()), **config)
        self._name = name
        self._type = type_
        self._no_interactive = no_interactive
        self._configure_mode = configure_mode

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
        return self.config_secret()

    @property
    def url(self):
        return self._url

    @property
    def no_interactive(self):
        return self._no_interactive

    @property
    def project(self):
        return self._project

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

    def configure(self):
        self.config_url()
        self.config_project()
        self.config_params()
        if self.no_interactive:
            self.config_secret()
            self._set_bugtracker()
            self.test_project()

    def verify(self):
        self.test_project()

    @abstractmethod
    def config_url(self):
        pass

    @abstractmethod
    def config_secret(self):
        pass

    @abstractmethod
    def config_params(self):
        pass

    @abstractmethod
    def _set_bugtracker(self):
        pass

    def config_project(self):
        self._project = read_input(
            Fore.BLUE + "Project id/name: " + Style.RESET_ALL
        )

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
                self.configure()
            else:
                logger.error(
                    "{project} ko on {url}".format(
                        project=self.project, url=self.url
                    )
                )
                sys.exit(-210)


class YesWeHackConfig(ConfigObject):

    default_url_api = "https://api.yeswehack.com"

    def __init__(
        self,
        name,
        bugtrackers,
        no_interactive=False,
        configure_mode=False,
        **config
    ):  # api_url, login, password, totp=False):
        assert bugtrackers is not None
        self._name = name
        self.configure_mode = configure_mode
        self.no_interactive = no_interactive
        self._programs = []
        self._password = ""
        self._totp_secret = ""
        if config or not configure_mode:
            self._totp = config.get("totp", False)
            keys = ["login", "programs"]
            if self.no_interactive:
                keys.append("password")
                if self._totp:
                    keys.append("totp_secret")
            super().__init__(keys, "YesWeHack", **config)
            self._login = config["login"]
            self._api_url = config.get("api_url", self.default_url_api)
            self._totp_secret = (
                config["totp_secrect"]
                if self.no_interactive and self._totp
                else ""
            )

            self._totp = config.get("totp", False)
            self._programs = self._config_programs(
                bugtrackers, config["programs"]
            )

            if not no_interactive and not configure_mode:
                self.get_interactive_info()
            else:
                self._password = (
                    config["password"] if self.no_interactive else ""
                )

            self._ywh = YesWeHack(
                username=self._login,
                password=self._password,
                api_url=self._api_url,
                lazy=False,
            )
        if configure_mode:
            self.configure(bugtrackers)

    def _config_programs(self, bugtrackers, config, configure_mode=False):
        pgms = []
        for index_name, pgm_config in config.items():
            pgms.append(
                ProgramConfig(
                    index_name,
                    bugtrackers,
                    no_interactive=self.no_interactive,
                    configure_mode=configure_mode,
                    **pgm_config
                )
            )
        return pgms

    @property
    def name(self):
        return self._name

    @property
    def totp_secret(self):
        return self._totp_secret

    @property
    def api_url(self):
        return self._api_url

    @property
    def programs(self):
        return self._programs

    @property
    def login(self):
        return self._login

    @property
    def password(self):
        return self._password

    @property
    def totp(self):
        return self._totp

    @property
    def ywh(self):
        return self._ywh

    def get_totp_code(self):
        def get_totp_code(self):
            totp_code = None
            if self._totp_secret:
                totp = pyotp.TOTP(self.totp_secret)
                totp_code = totp.now()
            return totp_code

    def configure(self, bugtrackers):
        self.config_user()
        exit_config = False
        counter = 1
        while not exit_config:
            self._programs.append(
                ProgramConfig(
                    "pgm_{}".format(counter),
                    bugtrackers,
                    no_interactive=self.no_interactive,
                    configure_mode=True,
                )
            )

            if read_input(
                Fore.BLUE
                + "Configure an other Program ? [y/N]"
                + Style.RESET_ALL
            ) in ["n", "N", ""]:
                exit_config = True
            else:
                counter += 1
        # ProgramConfig while

    def verify(self):
        self.test_login_config()
        self.test_program_config()

    def config_user(self):
        self._api_url = (
            read_input(
                "{}API url [{}{}{}]: {}".format(
                    Fore.BLUE,
                    Fore.GREEN,
                    self.default_url_api,
                    Fore.BLUE,
                    Style.RESET_ALL,
                )
            )
            or self.default_url_api
        )
        self._login = read_input(Fore.BLUE + "YesWeHack login: " + Fore.RESET)
        totp = read_input(
            Fore.BLUE + "Is TOTP Enabled : [y/N] " + Style.RESET_ALL
        )
        self._totp = True if totp in ["y", "Y"] else False

        if self.no_interactive:
            self.config_secret()

    def config_secret(self):
        self._password = read_input(
            Fore.BLUE
            + "Password for {} on {}: ".format(
                Fore.GREEN + self._login + Fore.BLUE,
                Fore.GREEN + self._api_url + Fore.BLUE,
            )
            + Style.RESET_ALL,
            secret=True,
        )
        if self.totp:
            self._totp_secret = read_input(
                Fore.BLUE + "Totp secret: " + Style.RESET_ALL, secret=True
            )
        self._ywh = YesWeHack(
            username=self.login, password=self.password, api_url=self.api_url
        )
        self.test_login_config()

    def test_login_config(self):
        if self.no_interactive:
            logger.info("Testing login")
        try:
            totp_code = self.get_totp_code()
            self.ywh.login(totp_code=totp_code)
            if self.no_interactive:
                logger.info(
                    "YesWeHack status: " + Fore.GREEN + "OK" + Style.RESET_ALL
                )
            else:
                logger.info(
                    "Login ok with {login} on {url}".format(
                        login=self.login, url=self.api_url
                    )
                )
        except TOTPLoginEnabled:
            if self.no_interactive:
                logger.info(Fore.RED + "KO (TOTP)" + Style.RESET_ALL)
                self._totp = True
                self.config_user()
        except BadCredentials:
            if self.no_interactive:
                logger.info(Fore.RED + "KO" + Style.RESET_ALL)
                self.config_user()
            else:
                logger.error(
                    "Login fail with {login} on {url} (BadCredentials)".format(
                        login=self.login, url=self.api_url
                    )
                )
                sys.exit(100)
        except InvalidResponse:
            if self.no_interactive:
                logger.info(Fore.RED + "KO" + Style.RESET_ALL)
                self.config_user()
            else:
                logger.error(
                    "Login fail with {login} on {url} (InvalidResponse)".format(
                        login=self.login, url=self.api_url
                    )
                )
                sys.exit(100)

    def get_interactive_info(self):
        logger.info(
            "Getting account info for "
            + Fore.GREEN
            + ", ".join([pgm.name for pgm in self.programs])
            + Style.RESET_ALL
            + " on "
            + Fore.GREEN
            + self.api_url
            + Style.RESET_ALL
            + " via "
            + Fore.GREEN
            + self.login
            + Style.RESET_ALL
        )
        self.config_secret()

    def test_program_config(self):
        totp_code = self.get_totp_code()
        self.ywh.login(totp_code=totp_code)
        if self.no_interactive:
            logger.info("Testing program")
        for program in self.programs:
            try:
                pgm = self.ywh.get_program(program)
                if self.no_interactive:
                    logger.info(
                        "{} status: ".format(self._project)
                        + Fore.GREEN
                        + "OK"
                        + Style.RESET_ALL
                    )
                else:
                    logger.info(
                        "Program {program} ok with {login} on  {url}".format(
                            program=pgm.name,
                            login=self.login,
                            url=self.api_url,
                        )
                    )
            except ObjectNotFound:
                if self.no_interactive:
                    logger.info(
                        "{} status: ".format(self._project)
                        + Fore.RED
                        + "KO"
                        + Style.RESET_ALL
                    )
                else:
                    logger.error(
                        "Program {program} fail with {login} on  {url}".format(
                            program=pgm.name,
                            login=self.login,
                            url=self.api_url,
                        )
                    )
                    sys.exit(110)
                self.config_program_info()

    def to_dict(self):
        pgms = {}
        for pgm in self.programs:
            pgms = {**pgms, **pgm.to_dict()}
        component = {
            "api_url": self.api_url,
            "login": self.login,
            "totp": self.totp,
            "programs": pgms,
        }
        if self.no_interactive:
            component["password"] = self.password
            if self.totp:
                component["totp_secret"] = self.totp_secret

        return {self.name: component}


class ProgramConfig(ConfigObject):
    def __init__(
        self,
        index_name,
        bugtrackers,
        no_interactive=False,
        configure_mode=False,
        **config
    ):  # name, bugtrackers={}):
        self.bugtrackers = []
        self._index_name = index_name
        if config or not configure_mode:
            super().__init__(["name", "bugtrackers_name"], "Program", **config)
            self._name = config["name"]
            self._validate_and_set_bugtrackers(
                config["bugtrackers_name"], bugtrackers
            )

        if configure_mode:
            self.configure(bugtrackers)

    def _validate_and_set_bugtrackers(self, program_bt_names, bugtrackers):
        all_bt_names = [bt.name for bt in bugtrackers]
        warnings = []
        for bt in program_bt_names:
            if bt not in all_bt_names:
                warnings.append(bt)
            else:
                self.bugtrackers.append(bugtrackers[all_bt_names.index(bt)])
        if not self.bugtrackers:
            logger.critical(
                "Bugtrackers type set in progams config part for {} does'nt exist in bugtrackers global configuration part".format(
                    self.name
                )
            )
            sys.exit(120)
        if warnings:
            logger.warning(
                "{} doesn't exists in bugtrackers global configuration part".format(
                    ", ".join(warnings)
                )
            )

    @property
    def index_name(self):
        return self._index_name

    @property
    def name(self):
        return self._name

    def configure(self, bugtrackers):
        all_bt_names = [bt.name for bt in bugtrackers]
        self._name = read_input(Fore.BLUE + "Program name: " + Style.RESET_ALL)
        exit_config = False
        while not exit_config:
            try:
                bt_idx = read_input(
                    Fore.BLUE
                    + "Select a bugtracker :{} \n\t{}\n".format(
                        Style.RESET_ALL,
                        "\n\t".join(
                            [
                                "{}/ {}".format(i + 1, j)
                                for i, j in enumerate(all_bt_names)
                                if not j
                                in [bt.name for bt in self.bugtrackers]
                            ]
                        ),
                    )
                )
                self.bugtrackers.append(bugtrackers[int(bt_idx) - 1])
                if read_input(
                    Fore.BLUE
                    + "Add an other bugtracker ? [y/N]"
                    + Style.RESET_ALL
                ) in ["n", "N", ""]:
                    exit_config = True
            except Exception as e:
                logger.error("Invalide response")

    def to_dict(self):
        return {
            self.index_name: {
                "name": self.name,
                "bugtrackers_name": [
                    bgtracker.name for bgtracker in self.bugtrackers
                ],
            }
        }


class GlobalConfig(ConfigObject):
    def __init__(
        self, configure_mode=False, no_interactive=False, filename=None
    ):
        self.default_supported_bugtrackers = [
            tr.bugtracker_type for tr in get_all_subclasses(BugTrackerConfig)
        ] or []
        self.no_interactive = no_interactive
        self.configure_mode = configure_mode
        self.filename = (
            Path(filename) if filename else self.get_default_config_file()
        )
        config = self._load(self.filename)
        self.bugtrackers = []
        self.yeswehack = []
        if config or not configure_mode:
            super().__init__(["yeswehack", "bugtrackers"], "global", **config)
            self.bugtrackers = self._config_bugtrackers(
                config["bugtrackers"], configure_mode=False
            )
            self.yeswehack = self._config_ywh(config["yeswehack"])  #
        if configure_mode:
            self.configure()

    def _config_bugtrackers(self, bgtrackers, configure_mode=False):
        bts = []
        for bt_name, bt_config in bgtrackers.items():
            if "type" in bt_config:
                class_ = self.get_bugtracker_class(bt_config["type"])
                bts.append(
                    class_(
                        bt_name,
                        configure_mode=configure_mode,
                        no_interactive=self.no_interactive,
                        **bt_config
                    )
                )
            else:
                logger.critical(
                    "type not set in {} configuration part".format(bt_name)
                )
                sys.exit(120)
        return bts

    def _config_ywh(self, ywh, configure_mode=False):
        bts = []
        for ywh_name, ywh_config in ywh.items():
            bts.append(
                YesWeHackConfig(
                    ywh_name,
                    self.bugtrackers,
                    configure_mode=configure_mode,
                    no_interactive=self.no_interactive,
                    **ywh_config
                )
            )
        return bts

    def get_default_config_file(self):
        if os.name == "posix":
            config_dir = Path(os.environ.get("HOME") + "/")
        else:
            config_dir = Path(os.environ.get("APPDATA") + "/ywh2bt/")
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
        config_file = Path(str(config_dir) + "/.ywh2bt.cfg")
        return config_file

    def _load(self, filename):
        if not filename.exists() and not self.configure_mode:
            logger.critical("File {} not exist".format(filename))
            sys.exit(130)
        configuration = {}
        if filename.exists():
            with open(filename, "r") as ymlfile:
                configuration = yaml.safe_load(ymlfile)
        return configuration

    def configure(self):
        logger.info("Welcome in ywh2bt configuration tools")

        if self.no_interactive:
            logger.warning(
                "You have choose non interactive mode ! All information you will write will be stored clearly visible."
            )
        exit_config = False
        if self.yeswehack or self.bugtrackers:
            logger.info(
                "Existing configuration {} loaded".format(self.filename)
            )
        while not exit_config:
            configure_new_elem = read_input(
                Fore.BLUE + "Configure new element ? [y/N]: " + Style.RESET_ALL
            )
            if configure_new_elem in ["y", "Y"]:
                self.configure_new_bugtrackers()
                self.configure_new_yeswehack()
            elif configure_new_elem in ["n", "N", ""]:
                exit_config = True
        self._update_configuration()
        self.write()

    @staticmethod
    def get_bugtracker_class(tracker_type):
        tracker_config = get_all_subclasses(
            BugTrackerConfig, cls_attr_filter={"bugtracker_type": tracker_type}
        )
        if len(tracker_config) != 1:
            if len(tracker_config) == 0:
                raise BugTrackerNotFound(
                    "Bug tracker not found from type `{}`".format(tracker_type)
                )
            else:
                raise MultipleBugTrackerMacth(
                    "Multiple Bug tracker have the same `bugtracker_type` class attribute (bugtracker_type : {}, classes : {}). Please change refered BugTracker in config file.".format(
                        tracker_type,
                        ", ".join(
                            [tr.bugtracker_type for tr in tracker_config]
                        ),
                        tracker_config,
                    )
                )
        return tracker_config[0]

    def configure_new_yeswehack(self):
        exit_config = False
        count = len(self.yeswehack) + 1
        while not exit_config:
            exit_configuration = read_input(
                Fore.BLUE
                + "Add YesWeHack configuration element ? [y/N]: "
                + Style.RESET_ALL
            )
            if exit_configuration in ["n", "N", ""]:
                exit_config = True
            elif exit_configuration in ["y", "Y"]:
                self.yeswehack.append(
                    YesWeHackConfig(
                        "yeswehack_{}".format(count),
                        self.bugtrackers,
                        no_interactive=self.no_interactive,
                        configure_mode=True,
                    )
                )
                count += 1

    def configure_new_bugtrackers(self):
        counter = len(self.bugtrackers) + 1
        exit_config = False
        while not exit_config:
            exit_configuration = read_input(
                Fore.BLUE + "Add new BugTracker ? [y/N]: " + Style.RESET_ALL
            )
            if exit_configuration in ["n", "N", ""]:
                exit_config = True
            elif exit_configuration in ["y", "Y"]:
                logger.info(
                    "Supported engine are: "
                    + Fore.YELLOW
                    + ", ".join(
                        [
                            bt_type.title()
                            for bt_type in self.default_supported_bugtrackers
                        ]
                    )
                    + Style.RESET_ALL
                )
                while True:
                    tracker_type = read_input(
                        Fore.BLUE + "Type: " + Style.RESET_ALL
                    ).lower()
                    if not tracker_type in self.default_supported_bugtrackers:
                        logger.error("Unsuported type")
                    else:
                        break
                self.bugtrackers.append(
                    self.get_bugtracker_class(tracker_type)(
                        "bugtracker_{}".format(counter),
                        no_interactive=self.no_interactive,
                        configure_mode=True,
                    )
                )
                counter += 1

    def _update_configuration(self):

        for cfg_ywh in self.yeswehack:
            for cfg_program in cfg_ywh.programs:
                cfg_bt = cfg_program.bugtrackers
                for count, bt in enumerate(cfg_bt):
                    logger.info(
                        str(count + 1)
                        + "/ "
                        + Fore.GREEN
                        + cfg_program.name
                        + Style.RESET_ALL
                        + " tracked on "
                        + Fore.GREEN
                        + bt.name
                        + Style.RESET_ALL
                        + " (id: "
                        + Fore.GREEN
                        + bt.project
                        + Style.RESET_ALL
                        + ")"
                    )
                read_config_to_keep = read_input(
                    Fore.BLUE
                    + "which ones to keep (eg 1 2 3, empty to keep all programs, None to keep any): "
                    + Style.RESET_ALL
                )

                config_to_keep = []
                if read_config_to_keep == "":
                    config_to_keep = [
                        config for config in range(1, len(cfg_bt) + 1)
                    ]
                elif read_config_to_keep.lower() == "none":
                    self.yeswehack = []
                    self.bugtrackers = []
                    return
                else:
                    read_config_to_keep = read_config_to_keep.split(" ")
                invalid_response = False
                for config in read_config_to_keep:
                    try:
                        if not 0 < int(config) <= len(cfg_bt):
                            invalid_response = True
                            logger.error("Value not in range")
                        else:
                            config_to_keep.append(int(config))
                    except:
                        invalid_response = True

                if invalid_response:
                    self._update_configuration()
                # Replace current config with the item we keep
                if len(config_to_keep) < len(cfg_program.bugtrackers):
                    delete_bugtrackers = []

                    while True:
                        user_input = read_input(
                            Fore.BLUE
                            + "You Want to delete other bugtrackers ? "
                            + Fore.YELLOW
                            + "(if not, they are just unset for this program, otherwise, this operation could break you're configuration file)"
                            + Fore.BLUE
                            + " [y/N] :"
                            + Style.RESET_ALL
                        )
                        if user_input in ["n", "N", ""]:
                            break
                        elif user_input in ["y", "Y"]:
                            delete_bugtrackers = [
                                cfg_program.bugtrackers[i - 1]
                                for i in range(
                                    1, len(cfg_program.bugtrackers) + 1
                                )
                                if i not in config_to_keep
                            ]
                            break
                    for del_bg in delete_bugtrackers:
                        try:
                            self.bugtrackers.remove(del_bg)
                        except:
                            logger.warning(
                                "You can't delete unexisting BugTracker ({})".format(
                                    del_bg.name
                                )
                            )
                cfg_program.bugtrackers = [
                    cfg_program.bugtrackers[i - 1] for i in config_to_keep
                ]
                for i in config_to_keep:
                    Fore.BLUE + "Which ones to add for this program ('1,2,3') -  empty to pass: " + Style.RESET_ALL
                exit_config = False
                bts = [
                    bt
                    for bt in self.bugtrackers
                    if bt not in cfg_program.bugtrackers
                ]
                while not exit_config and bts:
                    for count, bt in enumerate(bts):
                        logger.info("{}/ {}".format(count + 1, bt.name))
                    bt_idx = read_input(
                        Fore.BLUE
                        + "Which ones to add for this program ('1,2,3') -  empty to pass: "
                        + Style.RESET_ALL
                    )
                    if bt_idx:
                        try:
                            bt_idx = [int(i) for i in bt_idx.split(",")]
                            [
                                cfg_program.bugtrackers.append(bts[i - 1])
                                for i in bt_idx
                            ]
                        except Exception as e:
                            logger.error("Invalid Response")
                            continue
                    exit_config = True

    def to_dict(self):
        bts = {}
        for bugtracker in self.bugtrackers:
            bts = {**bts, **bugtracker.to_dict()}
        ywhs = {}
        for ywh in self.yeswehack:
            ywhs = {**ywhs, **ywh.to_dict()}
        return {"yeswehack": ywhs, "bugtrackers": bts}

    def write(self):
        yaml_configuration = yaml.dump(self.to_dict())
        with open(self.filename, "w") as f:
            f.write(yaml_configuration)
