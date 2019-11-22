from ywh2bt.utils import get_all_subclasses
from ywh2bt.exceptions import BugTrackerNotFound, MultipleBugTrackerMacth
from .abstract import ConfigObject, BugTrackerConfig
from .yeswehack import YesWeHackConfig
from .packages import ExtraPackageConfig
import os
from pathlib import Path
import sys
import yaml
from ywh2bt.utils import read_input
from ywh2bt.logging import logger
from colorama import Fore, Style

__all__ = ["GlobalConfig"]

"""
Module to load configuration file globaly
"""


class GlobalConfig(ConfigObject):

    """
    Configuration file representation

    :attr list mandatory_keys: keys needed in config_file
    :attr str name: ConfigObject identifier
    """

    mandatory_keys = ["yeswehack", "bugtrackers"]
    name = "global"

    ############################################################
    ####################### Constructor ########################
    ############################################################
    def __init__(
        self, configure_mode=False, no_interactive=False, filename=None
    ):
        self.default_supported_bugtrackers = []
        self.no_interactive = no_interactive
        self.configure_mode = configure_mode
        self.filename = (
            Path(filename) if filename else self.get_default_config_file()
        )
        config = self._load(self.filename)
        self.bugtrackers = []
        self.yeswehack = []
        self.packages = []
        if config or not configure_mode:
            self._build(config)
        if configure_mode:
            self.configure()

    ############################################################
    ################### Instance methods #######################
    ############################################################

    def configure(self):
        """
        Load or setup configuration, depends of attribute and existence configuration keys.
        """
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
                try:
                    self.configure_new_packages()
                    self.configure_new_bugtrackers()
                    self.configure_new_yeswehack()
                except Exception as e:
                    logger.error(str(e))
            elif configure_new_elem in ["n", "N", ""]:
                exit_config = True
        self._update_configuration()
        self.write()

    def configure_new_bugtrackers(self):
        """
        Add new bugtrackers with user interaction
        """
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

    def configure_new_packages(self):
        """
        Add new packages with user interaction
        """
        exit_config = False
        while not exit_config:
            exit_configuration = read_input(
                Fore.BLUE
                + "Add Package configuration element ? [y/N]: "
                + Style.RESET_ALL
            )
            if exit_configuration in ["n", "N", ""]:
                exit_config = True
            elif exit_configuration in ["y", "Y"]:
                self.packages.append(ExtraPackageConfig(configure_mode=True))
        self.default_supported_bugtrackers = [
            tr.bugtracker_type for tr in get_all_subclasses(BugTrackerConfig)
        ] or []

    def configure_new_yeswehack(self):
        """
        Add new YesWeHack with user interaction
        """
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

    def get_default_config_file(self):
        """
        Return default configuration file.
        """
        if os.name == "posix":
            config_dir = Path(os.environ.get("HOME") + "/")
        else:
            config_dir = Path(os.environ.get("APPDATA") + "/ywh2bt/")
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
        config_file = Path(str(config_dir) + "/.ywh2bt.cfg")
        return config_file

    def to_dict(self):
        """
        Map object to dictionary
        """
        bts = {}
        for bugtracker in self.bugtrackers:
            bts = {**bts, **bugtracker.to_dict()}
        ywhs = {}
        for ywh in self.yeswehack:
            ywhs = {**ywhs, **ywh.to_dict()}
        component = {"yeswehack": ywhs, "bugtrackers": bts}
        if self.packages:
            pkgs = [pkg.to_dict() for pkg in self.packages]
            component["packages"] = pkgs
        return component

    def write(self):
        """
        Write GlobalConfig to configuration file.
        """
        yaml_configuration = yaml.dump(self.to_dict())
        with open(self.filename, "w") as f:
            f.write(yaml_configuration)

    def _build(self, config):
        """
        Build object from config dictionary information.

        :param dict config: configuration.
        """
        super().__init__(self.mandatory_keys, self.name, **config)
        self.bugtrackers = self._config_bugtrackers(
            config["bugtrackers"], configure_mode=False
        )
        self.yeswehack = self._config_ywh(config["yeswehack"])
        if "packages" in config:
            self.packages = self._config_packages(config["packages"])
        self.default_supported_bugtrackers = [
            tr.bugtracker_type for tr in get_all_subclasses(BugTrackerConfig)
        ] or []

    def _add_bugtrackers_to_pgm(self, cfg_program):
        """
        Link an existing bugtracker to the given program
        """
        exit_config = False

        bts = [
            bt for bt in self.bugtrackers if bt not in cfg_program.bugtrackers
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

    def _config_to_keep(self, cfg_program):
        """
        Select bugtrackers to keep in program configuration
        """
        cfg_bt = cfg_program.bugtrackers
        for count, bt in enumerate(cfg_bt):
            logger.info(
                str(count + 1)
                + "/ "
                + Fore.GREEN
                + cfg_program.slug
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
            config_to_keep = [config for config in range(1, len(cfg_bt) + 1)]
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
        return config_to_keep

    def _config_bugtrackers(self, bgtrackers, configure_mode=False):
        """
        Build BugTrackerConfig-s Object from config information.

        :param dict bgtrackers: Bugtrackers definitions.
        :param bool configure_mode: True if configuration mode is actif.
        """
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

    def _config_packages(self, packages):
        """
        Build ExtraPackageConfig-s Object from config information.

        :param list packages: packages definitions.
        """
        pkgs = []
        for params in packages:
            pkgs.append(ExtraPackageConfig(configure_mode=False, **params))
        return pkgs

    def _config_ywh(self, ywh, configure_mode=False):
        """
        Build YesWeHackConfig-s Object from config information.

        :param dict ywh: yeswehack definitions.
        """
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

    def _load(self, filename):
        """
        Load yaml file with name  `filename`.

        :param str filename: name of file to load.
        """
        if not filename.exists() and not self.configure_mode:
            logger.critical("File {} not exist".format(filename))
            sys.exit(130)
        configuration = {}
        if filename.exists():
            with open(filename, "r") as ymlfile:
                configuration = yaml.safe_load(ymlfile)
        return configuration

    def _update_package(self):
        """
        In configure mode only, used to change configured package.
        """
        for package in self.packages:
            exit_config = False
            package.info()
            while not exit_config:
                del_modules = read_input(
                    Fore.BLUE
                    + "Which modules to delete ? ('1,2,3') - empty to pass :"
                    + Style.RESET_ALL
                )
                if del_modules:
                    try:
                        err = ""
                        del_idx = []
                        for i in del_modules.split(","):
                            idx = int(i) - 1
                            if i not in range(len(package._modules)):
                                err = "Index out of range"
                                break
                            if i in del_idx:
                                continue
                            del_idx.append(idx)
                        if not err:
                            exit_config = True
                        else:
                            logger.error(err)
                            continue
                    except:
                        logger.error("Invalid Input")
                        continue
                exit_config = True

            for i in sorted(del_modules, reverse=True):
                del package.modules[i]

    def _update_configuration(self):
        """
        In configure mode only, used to change configured object.
        """
        self._update_package()

        for cfg_ywh in self.yeswehack:
            for cfg_program in cfg_ywh.programs:
                config_to_keep = self._config_to_keep(cfg_program)

                # Replace current config with the item we keep
                if len(config_to_keep) < len(cfg_program.bugtrackers):
                    cfg_program._delete_bugtrackers(
                        config_to_keep, self.bugtrackers
                    )
                cfg_program.bugtrackers = [
                    cfg_program.bugtrackers[i - 1] for i in config_to_keep
                ]
                self._add_bugtrackers_to_pgm(cfg_program)

    ############################################################
    #################### Static methods ########################
    ############################################################
    @staticmethod
    def get_bugtracker_class(tracker_type):
        """
        Return bugtracker class from tracker type.

        :param str tracker_type: type identifier of the BugTrackerConfig subclass.
        """
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
