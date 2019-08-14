# -*- encoding: utf-8 -*-
import os
import sys
import copy
import yaml
import pyotp
import getpass
import logging
from pathlib import Path
from colorama import Fore, Style
from yeswehack.api import YesWeHack
from yeswehack.exceptions import BadCredentials, ObjectNotFound, InvalidResponse, TOTPLoginEnabled

logger = logging.getLogger(__name__)


class GlobalConfig:

    configuration = None
    no_interactive = False

    def __init__(self, no_interactive=False):
        self.no_interactive = no_interactive
        self.load()

    def get_config_file(self):
        if os.name == "posix":
            config_dir = Path(os.environ.get("HOME") + "/")
        else:
            config_dir = Path(os.environ.get("APPDATA") + "ywh2bt/")
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
        config_file = Path(str(config_dir) + "/.ywh2bt.cfg")
        return config_file

    def load(self):
        config_file = self.get_config_file()
        if config_file.exists():
            with open(config_file, "r") as ymlfile:
                self.configuration = yaml.safe_load(ymlfile)
        return self.configuration

    def _update_configuration(self):
        count = 1
        for cfg_program in self.configuration["yeswehack"]:
            cfg_bt_name = self.configuration["yeswehack"][cfg_program]["bt"]
            print(
                str(count)
                + "/ "
                + Fore.GREEN
                + self.configuration["yeswehack"][cfg_program]["program"]
                + Style.RESET_ALL
                + " tracked on "
                + Fore.GREEN
                + self.configuration["bugtracker"][cfg_bt_name]["type"]
                + Style.RESET_ALL
                + " (id: "
                + Fore.GREEN
                + self.configuration["bugtracker"][cfg_bt_name]["project_id"]
                + Style.RESET_ALL
                + ")"
            )
            count += 1
        read_config_to_keep = input(
            Fore.BLUE + "which ones to keep (eg 1 2 3, empty to keep all programs, None to keep any): " + Style.RESET_ALL
        )

        config_to_keep = []
        if read_config_to_keep == "":
            config_to_keep = [config for config in range(1, count)]
        elif read_config_to_keep.lower() == "none":
            self.configuration = {"yeswehack": {}, "bugtracker": {}}
            return 
        else:
            read_config_to_keep = read_config_to_keep.split(" ")
        invalid_response = False
        for config in read_config_to_keep:
            try:
                if not 0 < int(config) <= count:
                    invalid_response = True
                    print("Value not in range")
                else:
                    config_to_keep.append(int(config))
            except:
                invalid_response = True

        if invalid_response:
            self._update_configuration()

        # Replace current config with the item we keep
        new_configuration = {"yeswehack": {}, "bugtracker": {}}
        count = 1
        counter = 1
        for ywh_cfg in self.configuration["yeswehack"]:
            if count in config_to_keep:
                new_configuration["yeswehack"]["yeswehack_" + str(counter)] = self.configuration[
                    "yeswehack"
                ][ywh_cfg]
                new_configuration["yeswehack"]["yeswehack_" + str(counter)]["bt"] = "bugtracker_" + str(
                    counter
                )
                counter += 1
            count += 1

        count = 1
        counter = 1
        for bt_cfg in self.configuration["bugtracker"]:
            if count in config_to_keep:
                new_configuration["bugtracker"]["bugtracker_" + str(counter)] = self.configuration[
                    "bugtracker"
                ][bt_cfg]
                counter += 1
            count += 1
        self.configuration = new_configuration

    def configure(self):
        print(Fore.BLUE + "Welcome in ywh2bt configuration tools")
        print(Style.RESET_ALL)
        yeswehack = []
        bugtracker = []
        exit_config = False
        if self.configuration is not None:
            self._update_configuration()
            # exif config if we only want to delete a pgm
            exit_configuration = input("Configure an other PGM [y/N] ")
            if exit_configuration not in ["y", "Y"]:
                exit_config = True
        else:
            self.configuration = {"yeswehack": {}, "bugtracker": {}}

        while not exit_config:
            config = Config(self.no_interactive)
            config.configure()
            yeswehack.append(copy.copy(config.yeswehack))
            bugtracker.append(copy.copy(config.bugtracker))
            exit_configuration = input("Configure an other PGM [y/N] ")
            if exit_configuration not in ["y", "Y"]:
                break
            # del config
        counter = len(self.configuration["yeswehack"]) + 1

        for bt_cfg in bugtracker:
            self.configuration["bugtracker"]["bugtracker_" + str(counter)] = bt_cfg
            counter += 1
        counter = len(self.configuration["yeswehack"]) + 1
        for ywh_cfg in yeswehack:
            self.configuration["yeswehack"]["yeswehack_" + str(counter)] = ywh_cfg
            self.configuration["yeswehack"]["yeswehack_" + str(counter)]["bt"] = "bugtracker_" + str(
                counter
            )
            counter += 1
        self.write()

    def write(self):
        yaml_configuration = yaml.dump(self.configuration)
        config_file = self.get_config_file()
        with open(config_file, "w") as f:
            f.write(yaml_configuration)


class Config:

    no_interactive = False

    bugtracker = {}
    yeswehack = {}

    defaults = {
        "ywh_url_api": "http://api.ywh.docker.local",
        "supported_bugtracker": ["gitlab", "jira", "github"],
    }

    def __init__(self, no_interactive=False, yeswehack=None, bugtracker=None):
        if no_interactive is not None:
            self.no_interactive = no_interactive
        if yeswehack is not None:
            self.yeswehack = yeswehack
        if bugtracker is not None:
            self.bugtracker = bugtracker

    def get_totp_code(self):
        totp_code = None
        if "totp_secret" in self.yeswehack:
            totp = pyotp.TOTP(self.yeswehack["totp_secret"])
            totp_code = totp.now()
        return totp_code

    def get_bt_class(self):
        module_name = "lib.ywh" + self.bugtracker["type"]
        try:
            class_ = getattr(sys.modules[module_name], "YWH" + self.bugtracker["type"].title())
        except Exception as e:
            raise e
        return class_

    def get_interactive_info(self):
        print(
            Fore.BLUE
            + "Getting account info for "
            + Fore.GREEN
            + self.yeswehack["program"]
            + Fore.BLUE
            + " on "
            + Fore.GREEN
            + self.yeswehack["api_url"]
            + Fore.BLUE
            + " via "
            + Fore.GREEN
            + self.yeswehack["login"]
            + Style.RESET_ALL
        )
        self.ywh_config_secret()
        print(self.bugtracker)
        class_ = self.get_bt_class()
        self.bugtracker_config_secret(class_)

    def configure(self):
        self.ywh_config_user()
        self.ywh_config_program_info()
        self.bugtracker_config_user()
        self.bugtracker_config_project()

    def verify(self):
        self.ywh_test_login_config()
        self.ywh_test_program_config()
        self.bugtracker_test_login()
        self.bugtracker_test_project()

    def ywh_config_user(self):
        self.yeswehack["login"] = input(Fore.BLUE + "YesWeHack login: " + Style.RESET_ALL)
        self.yeswehack["api_url"] = input("API url [{0}]: ".format(self.defaults["ywh_url_api"]))
        self.yeswehack["api_url"] = self.yeswehack["api_url"] or self.defaults["ywh_url_api"]
        self.yeswehack["totp"] = input(Fore.BLUE + "Is TOTP Enabled : [y/N] " + Style.RESET_ALL)
        if self.yeswehack["totp"] in ["y", "Y"]:
            self.yeswehack["totp"] = True
        else:
            self.yeswehack["totp"] = False
        if self.no_interactive:
            self.ywh_config_secret()
            # self.yeswehack["password"] = getpass.getpass(
            #    prompt=Fore.BLUE + "Password: " + Style.RESET_ALL
            # )
            # if "totp" in self.yeswehack and self.yeswehack["totp"]:
            #    self.yeswehack["totp_secret"] = getpass.getpass(
            #        prompt=Fore.BLUE + "Totp secret: " + Style.RESET_ALL
            #    )

            # self.ywh_test_login_config()
        # return self.yeswehack

    def ywh_config_secret(self):
        self.yeswehack["password"] = getpass.getpass(prompt=Fore.BLUE + "Password: " + Style.RESET_ALL)
        if "totp" in self.yeswehack and self.yeswehack["totp"]:
            self.yeswehack["totp_secret"] = getpass.getpass(
                prompt=Fore.BLUE + "Totp secret: " + Style.RESET_ALL
            )

        self.ywh_test_login_config()

    def ywh_test_login_config(self):
        if self.no_interactive:
            print("Testing login: ", end="", flush=True)
        try:
            ywh = YesWeHack(
                self.yeswehack["login"], self.yeswehack["password"], self.yeswehack["api_url"]
            )
            totp_code = self.get_totp_code()
            ywh.login(totp_code=totp_code)
            if self.no_interactive:
                print(Fore.GREEN + "OK")
                print(Style.RESET_ALL)
            else:
                logging.info(
                    "Login ok with {login} on {url}".format(
                        login=self.yeswehack["login"], url=self.yeswehack["api_url"]
                    )
                )
        except TOTPLoginEnabled:
            if self.no_interactive:
                print(Fore.RED + "KO (TOTP)")
                print(Style.RESET_ALL)
                self.yeswehack["totp"] = True
                self.ywh_config_user()
        except BadCredentials:
            if self.no_interactive:
                print(Fore.RED + "KO")
                print(Style.RESET_ALL)
                self.ywh_config_user()
            else:
                logging.error(
                    "Login fail with {login} on {url} (BadCredentials)".format(
                        login=self.yeswehack["login"], url=self.yeswehack["api_url"]
                    )
                )
                sys.exit(100)
        except InvalidResponse:
            if self.no_interactive:
                print(Fore.RED + "KO")
                print(Style.RESET_ALL)
                self.ywh_config_user()
            else:
                logging.error(
                    "Login fail with {login} on {url} (InvalidResponse)".format(
                        login=self.yeswehack["login"], url=self.yeswehack["api_url"]
                    )
                )
                sys.exit(100)
        # return self.yeswehack

    def ywh_config_program_info(self):
        self.yeswehack["program"] = input(Fore.BLUE + "Program: " + Style.RESET_ALL).lower()
        if self.no_interactive:
            self.ywh_test_program_config()
        # return self.yeswehack

    def ywh_test_program_config(self):
        ywh = YesWeHack(self.yeswehack["login"], self.yeswehack["password"], self.yeswehack["api_url"])
        totp_code = self.get_totp_code()
        ywh.login(totp_code=totp_code)
        if self.no_interactive:
            print("Testing program : ", end="", flush=True)

        try:
            pgm = ywh.get_program(self.yeswehack["program"])
            if self.no_interactive:
                print(Fore.GREEN + "OK")
                print(Style.RESET_ALL)
            else:
                logging.info(
                    "Program {program} ok with {login} on  {url}".format(
                        program=self.yeswehack["program"],
                        login=self.yeswehack["login"],
                        url=self.yeswehack["api_url"],
                    )
                )
        except ObjectNotFound:
            if self.no_interactive:
                print(Fore.RED + "KO")
                print(Style.RESET_ALL)
            else:
                logging.error(
                    "Program {program} fail with {login} on  {url}".format(
                        program=self.yeswehack["program"],
                        login=self.yeswehack["login"],
                        url=self.yeswehack["api_url"],
                    )
                )
                sys.exit(110)
            self.ywh_config_program_info()
        # return self.yeswehack

    def bugtracker_config_user(self):
        print(Fore.BLUE + "Supported engine are: " + Fore.YELLOW, end="")
        for bt_type in self.defaults["supported_bugtracker"]:
            print(bt_type.title() + ", ", end="")
        print(Style.RESET_ALL)
        while True:
            self.bugtracker["type"] = input(Fore.BLUE + "Type: " + Style.RESET_ALL).lower()
            if not self.bugtracker["type"] in self.defaults["supported_bugtracker"]:
                print(Fore.RED + "Unsuported type")
            else:
                break
        class_ = self.get_bt_class()
        class_.configure(self.bugtracker)
        if self.no_interactive:
            self.bugtracker_config_secret(class_)
        return self.bugtracker

    def bugtracker_config_secret(self, bt_class):
        self.bugtracker.update(bt_class.get_interactive_info(self.bugtracker))
        self.bugtracker_test_login()

    def bugtracker_test_login(self):
        class_ = self.get_bt_class()
        if self.no_interactive:
            print(
                "Testing login on "
                + Fore.BLUE
                + self.bugtracker["type"].title()
                + ": "
                + Style.RESET_ALL,
                end="",
                flush=True,
            )
        try:
            bt = class_(self.bugtracker)
            if self.no_interactive:
                print(Fore.GREEN + "OK")
                print(Style.RESET_ALL)
            else:
                logging.info(
                    "Login ok on {type} ({url})".format(
                        type=self.bugtracker["type"], url=self.bugtracker["url"]
                    )
                )
        except:
            if self.no_interactive:
                print(Fore.RED + "KO")
                print(Style.RESET_ALL)
            else:
                logging.info(
                    "Login fail on {type} ({url})".format(
                        type=self.bugtracker["type"], url=self.bugtracker["url"]
                    )
                )
                sys.exit(-200)

            self.bugtracker_config_user()
        # return self.bugtracker

    def bugtracker_config_project(self):
        self.bugtracker["project_id"] = input(Fore.BLUE + "Project id: " + Style.RESET_ALL)
        if self.no_interactive:
            self.bugtracker_test_project()
        # return self.bugtracker

    def bugtracker_test_project(self):
        class_ = self.get_bt_class()
        bt = class_(self.bugtracker)
        if self.no_interactive:
            print("Testing project: " + Style.RESET_ALL, end="", flush=True)
        try:
            bt.get_project()
            if self.no_interactive:
                print(Fore.GREEN + "OK")
                print(Style.RESET_ALL)
            else:
                logging.info(
                    "{project} ok on {url}".format(
                        project=self.bugtracker["project_id"], url=self.bugtracker["url"]
                    )
                )
        except:
            if self.no_interactive:
                print(Fore.RED + "KO")
                print(Style.RESET_ALL)
                self.bugtracker_config_project()
            else:
                logging.error(
                    "{project} ko on {url}".format(
                        project=self.bugtracker["project_id"], url=self.bugtracker["url"]
                    )
                )
                sys.exit(-210)
