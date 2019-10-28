from .abstract import ConfigObject
from ywh2bt.logging import logger
from colorama import Fore, Style

from yeswehack.api import YesWeHack
from yeswehack.exceptions import (
    BadCredentials,
    ObjectNotFound,
    InvalidResponse,
    TOTPLoginEnabled,
)
from ywh2bt.utils import read_input
import sys

__all__ = ["YesWeHackConfig", "ProgramConfig"]


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
        for pgm_config in config:
            pgms.append(
                ProgramConfig(
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
        while not exit_config:
            self._programs.append(
                ProgramConfig(
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
        pgms = [pgm.to_dict() for pgm in self.programs]
        # for pgm in self.programs:
        #     pgms = {**pgms, **pgm.to_dict()}
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
        self, bugtrackers, no_interactive=False, configure_mode=False, **config
    ):  # name, bugtrackers={}):
        self.bugtrackers = []
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
    def name(self):
        return self._name

    def configure(self, bugtrackers):
        all_bt_names = [bt.name for bt in bugtrackers]
        self._name = read_input(Fore.BLUE + "Program name: " + Style.RESET_ALL)
        exit_config = False
        while not exit_config:
            bg_list = [
                "{}/ {}".format(i + 1, j)
                for i, j in enumerate(all_bt_names)
                if not j in [bt.name for bt in self.bugtrackers]
            ]
            if not bg_list:
                exit_config = True
                continue
            try:
                bt_idx = read_input(
                    Fore.BLUE
                    + "Select a bugtracker :{} \n\t{}\n".format(
                        Style.RESET_ALL, "\n\t".join(bg_list)
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
            "name": self.name,
            "bugtrackers_name": [
                bgtracker.name for bgtracker in self.bugtrackers
            ],
        }
