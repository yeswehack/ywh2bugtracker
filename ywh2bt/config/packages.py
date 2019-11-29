from .abstract import ConfigObject
from ywh2bt.logging import logger
import importlib
import os
import sys
from ywh2bt.utils import read_input
from colorama import Fore, Style

__all__ = ["ExtraPackageConfig"]

"""
Module to load and configure External BugTracker packages to append.
"""


class ExtraPackageConfig(ConfigObject):
    """
    Load / Configure External packages to append.
    """

    ############################################################
    ###################### Constructor #########################
    ############################################################
    def __init__(self, configure_mode=False, **config):
        self._configure_mode = configure_mode
        self._package_name = ""
        keys = []
        self._modules = []
        self._path = ""
        if config or not configure_mode:
            keys += ["path", "modules"]
            self._path = config["path"]
            self._modules = [module for module in config["modules"]]
            if "package" in config:
                self._package_name = config["package"]

        super().__init__(keys, "Packages", **config)
        if configure_mode:
            self.configure()
        self.bugtracker_class_appender()

    ############################################################
    #################### Instance Methods ######################
    ############################################################
    def bugtracker_class_appender(self):
        """
        Verify if package exist and append it to sys.path.
        Import BugTrackerConfig module definition
        """
        if not os.path.isdir(self.format_path()):
            raise FileNotFoundError(
                "package path does'nt exist: {}".format(
                    os.path.abspath(self.path)
                )
            )

        sys.path.append(self.path)

        for bugtracker_module in self.modules:
            module_path = ""
            if self.package_name:
                module_path += self.package_name + "."
            module_path += bugtracker_module
            importlib.import_module(module_path)

    def configure(self):
        """
        Configure packages interactively.
        """
        exit_config = False
        self._package_name = read_input(
            Fore.BLUE
            + "Package Name (empty for module path): "
            + Style.RESET_ALL
        )
        while True:
            self._path = read_input(
                Fore.BLUE
                + "Absolute path to package directory: "
                + Style.RESET_ALL
            )
            if not os.path.isdir(self.format_path()):
                logger.error(
                    "package path does'nt exist: {}".format(self.path)
                )
                continue
            break

        while not exit_config:
            self._modules.append(
                read_input(Fore.BLUE + "Module name: " + Style.RESET_ALL)
            )
            while True:
                exit_configuration = read_input(
                    Fore.BLUE + "Add module ? [y/N]: " + Style.RESET_ALL
                )
                if exit_configuration in ["n", "N", ""]:
                    exit_config = True
                    break
                elif exit_configuration in ["y", "Y"]:
                    break
        self.info()

    def format_path(self):
        """
        Normalize given path.
        """
        return os.path.realpath(os.path.expanduser(self._path))

    def info(self):
        """
        Log information for the package.
        """
        logger.info("package name : {}".format(self.package_name))
        logger.info("path : {}".format(self.path))

        logger.info(
            "Modules : {}".format(
                "\n\t".join(
                    [
                        "{}/ {}".format(idx + 1, module)
                        for idx, module in enumerate(self.modules)
                    ]
                )
            )
        )

    def to_dict(self):
        """
        Map object to dictionary.
        """
        return {
            "package": self.package_name,
            "path": self.path,
            "modules": self.modules,
        }

    ############################################################
    ####################### Properties #########################
    ############################################################
    @property
    def package_name(self):
        return self._package_name

    @property
    def configure_mode(self):
        return self._configure_mode

    @property
    def path(self):
        return self._path

    @property
    def modules(self):
        return self._modules
