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

"""
YesWeHack Config module
"""


class YesWeHackConfig(ConfigObject):

    """
    Build/Configure YesWeHack Configuration.

    :attr str default_url_api: default URL Api for this application.
    :attr list know_header: headers known to exchange with api.
    """

    default_url_api = "https://apps.yeswehack.com"
    known_headers = ["X-YesWeHack-Apps"]

    ############################################################
    ###################### Constructor #########################
    ############################################################
    def __init__(
        self,
        name,
        bugtrackers,
        no_interactive=False,
        configure_mode=False,
        **config,
    ):
        assert bugtrackers is not None
        self._name = name
        self.configure_mode = configure_mode
        self.no_interactive = no_interactive
        self._programs = []
        self._oauth_args = {}
        self._apps_headers = {}
        self._password = ""
        self._totp_secret = ""

        self.check_secret_keys(
            no_interactive, ["totp_secret", "password"], config
        )

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
            self._oauth_mode = "oauth_args" in config
            self._oauth_args = config.get("oauth_args", {})
            self._apps_headers = config.get("apps_headers", {})
            self._verify = config.get("verify", True)
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
                oauth_mode=self._oauth_mode,
                oauth_args=self._oauth_args,
                apps_headers=self.apps_headers,
                verify=self._verify,
                headers={"Access-Control-Allow-Originx": "*"},
                lazy=False,
            )
        if configure_mode:
            self.configure(bugtrackers)

    ############################################################
    ################### Instance Methods #######################
    ############################################################

    def configure(self, bugtrackers):
        """
        Configure programs interactively.
        """
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

    def config_oauth(self):
        """
        Configure oauth public information interactively.
        """
        self._oauth_args["client_id"] = read_input(
            Fore.BLUE + "Client id: " + Style.RESET_ALL
        )
        self._oauth_args["redirect_uri"] = read_input(
            Fore.BLUE + "Redirect URI: " + Style.RESET_ALL
        )

    def config_secret(self):
        """
        Configure secret information interactively.
        """
        self._password = read_input(
            Fore.BLUE
            + "Password for {} on {}: ".format(
                Fore.GREEN + self._login + Fore.BLUE,
                Fore.GREEN + self._api_url + Fore.BLUE,
            )
            + Style.RESET_ALL,
            secret=True,
        )
        if self.oauth_mode:
            self._oauth_args["client_secret"] = read_input(
                Fore.BLUE + "Client Secret: " + Style.RESET_ALL, secret=True
            )
        if self.totp:
            self._totp_secret = read_input(
                Fore.BLUE + "Totp secret: " + Style.RESET_ALL, secret=True
            )
        self._config_header()

        self._ywh = YesWeHack(
            username=self._login,
            password=self._password,
            api_url=self._api_url,
            oauth_mode=self._oauth_mode,
            oauth_args=self._oauth_args,
            apps_headers=self.apps_headers,
        )
        self.test_login_config()

    def config_user(self):
        """
        Configure user login information interactively.
        """
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

        while True:
            inpt = read_input(
                Fore.BLUE + "OAuth2 Authentication ? [y/N]: " + Fore.RESET
            )
            if inpt in ["y", "Y"]:
                self._oauth_mode = True
                self.config_oauth()
                break
            elif inpt in ["", "n", "N"]:
                self._oauth_mode = False
                break

        if self.no_interactive:
            self.config_secret()

    def get_interactive_info(self):
        """
        Configure secret information interactively.
        """
        logger.info(
            "Getting account info for "
            + Fore.GREEN
            + ", ".join([pgm.slug for pgm in self.programs])
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

    def get_totp_code(self):
        """
        Get TOTP code
        """
        totp_code = None
        if self._totp_secret:
            totp = pyotp.TOTP(self.totp_secret)
            totp_code = totp.now()
        return totp_code

    def test_login_config(self):
        """
        Test login configuration information.
        """
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

    def test_program_config(self):
        """
        Test programs configuration information.
        """
        totp_code = self.get_totp_code()
        self.ywh.login(totp_code=totp_code)
        managed_programs = set(self.ywh.managed_programs())
        pgms_names = [pgm.name for pgm in self.programs]
        diffs = set(pgms_names).difference(managed_programs)
        if diffs:
            logger.error(
                "Program-s {} are not manageable for {} yeswehack user".format(
                    "".join(diffs), self.login
                )
            )
            sys.exit(110)
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
        """
        Map object to dictionary
        """
        pgms = [pgm.to_dict() for pgm in self.programs]

        component = {
            "api_url": self.api_url,
            "login": self.login,
            "totp": self.totp,
            "programs": pgms,
        }

        if self.oauth_mode:
            component["oauth_args"] = self.oauth_args
        if self.apps_headers:
            component["apps_headers"] = self.apps_headers
        if self.no_interactive:
            component["password"] = self.password
            if self.totp:
                component["totp_secret"] = self.totp_secret

        return {self.name: component}

    def verify(self):
        """
        Verify connexion information
        """
        self.test_login_config()
        self.test_program_config()

    def _config_programs(self, bugtrackers, config, configure_mode=False):
        """
        Configure existing programs.
        """
        pgms = []
        for pgm_config in config:
            pgms.append(
                ProgramConfig(
                    bugtrackers,
                    no_interactive=self.no_interactive,
                    configure_mode=configure_mode,
                    **pgm_config,
                )
            )
        return pgms

    def _config_header(self):
        """
        Config headers interactively
        """
        logger.info("Yeswehack Apps Headers configuration")
        for know_header in self.known_headers:
            header = read_input(
                Fore.BLUE
                + "Value for {}: ".format(Fore.GREEN + know_header + Fore.BLUE)
                + Fore.RESET,
                secret=True,
            )
            if header:
                self.apps_headers[know_header] = header
        inpt = ""
        exit_config = False
        while not exit_config:
            while True:
                inpt = read_input(
                    Fore.BLUE
                    + "Append an other Application Header ? [y/N]: "
                    + Fore.RESET
                )
                if inpt in ["y", "Y"]:
                    apps_header_name = read_input(
                        Fore.BLUE + "Header Name: " + Fore.RESET
                    )
                    apps_header_value = read_input(
                        Fore.BLUE + "Header Value: " + Fore.RESET
                    )
                    self.apps_headers[apps_header_name] = apps_header_value
                    break
                if inpt in ["", "n", "N"]:
                    exit_config = True
                    break

    ############################################################
    ####################### Properties #########################
    ############################################################

    @property
    def apps_headers(self):
        return self._apps_headers

    @property
    def oauth_args(self):
        return self._oauth_args

    @property
    def oauth_mode(self):
        return self._oauth_mode

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


class ProgramConfig(ConfigObject):

    """
    Load or configure Program configuration.
    """

    ############################################################
    ###################### Constructor #########################
    ############################################################

    def __init__(
        self, bugtrackers, no_interactive=False, configure_mode=False, **config
    ):  # name, bugtrackers={}):
        self.bugtrackers = []
        if config or not configure_mode:
            super().__init__(["slug", "bugtrackers_name"], "Program", **config)
            self._slug = config["slug"]
            self._validate_and_set_bugtrackers(
                config["bugtrackers_name"], bugtrackers
            )

        if configure_mode:
            self.configure(bugtrackers)

    ############################################################
    ################### Instance Methods #######################
    ############################################################

    def configure(self, bugtrackers):
        """
        Configure and link to bugtrackers interactively.
        """
        all_bt_names = [bt.name for bt in bugtrackers]
        self._slug = read_input(Fore.BLUE + "Program slug: " + Style.RESET_ALL)
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
        """
        Map object to dictionary.
        """
        return {
            "slug": self.slug,
            "bugtrackers_name": [
                bgtracker.name for bgtracker in self.bugtrackers
            ],
        }

    def _delete_bugtrackers(self, config_to_keep, bugtrackers):
        """
        Delete Linked bugtrackers
        """
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
                    bugtrackers[i - 1]
                    for i in range(1, len(bugtrackers) + 1)
                    if i not in config_to_keep
                ]
                break
        for del_bg in delete_bugtrackers:
            try:
                bugtrackers.remove(del_bg)
            except:
                logger.warning(
                    "You can't delete unexisting BugTracker ({})".format(
                        del_bg.name
                    )
                )

    def _validate_and_set_bugtrackers(self, program_bt_names, bugtrackers):
        """
        Configure and link to bugtrackers from configuration file.
        """
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
                    self.slug
                )
            )
            sys.exit(120)
        if warnings:
            logger.warning(
                "{} doesn't exists in bugtrackers global configuration part".format(
                    ", ".join(warnings)
                )
            )

    ############################################################
    ####################### Properties #########################
    ############################################################
    @property
    def slug(self):
        return self._slug
