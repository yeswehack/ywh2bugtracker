#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import os
import yaml
import logging
import getpass
import pyotp
from pathlib import Path
from colorama import Fore, Style
from optparse import OptionParser
from yeswehack.api import YesWeHack
from yeswehack.exceptions import BadCredentials, ObjectNotFound, InvalidResponse, TOTPLoginEnabled
from lib.bugtracker import BugTracker
from lib import ywhgitlab, ywhgithub, ywhjira
from lib import config


def check_bug(comments):
    for comment in comments:
        if comment.message_html is not None and BugTracker.ywh_comment_marker in comment.message_html:
            return True
    return False


def main():
    parser = OptionParser(usage="usage: %prod [option]")
    parser.add_option(
        "-c", "--configure", action="store_true", dest="configure", help="Create config file"
    )
    parser.add_option(
        "-n",
        "--no-interactive",
        action="store_true",
        dest="no_interactive",
        default=False,
        help="non interactive mode but store credencials on disk. You need to activate it on configure to store credencials",
    )
    (options, args) = parser.parse_args()
    ywh_cfg = config.GlobalConfig(options.no_interactive)
    if options.configure:
        ywh_cfg.configure()
    else:
        cfg = ywh_cfg.load()
        if options.no_interactive:
            logging.basicConfig(
                format="%(asctime)s %(message)s", level=logging.INFO, datefmt="%m/%d/%Y %H:%M:%S"
            )

        run(cfg, options)

def run(cfg, options):
    for cfg_program in cfg["yeswehack"]:
        # Iterate on every referenced program
        logging.info("Get info for " + cfg_program)
        cfg_bt_name = cfg["yeswehack"][cfg_program]["bt"]
        pgm_export_config = config.Config(
            yeswehack=cfg["yeswehack"][cfg_program], bugtracker=cfg["bugtracker"][cfg_bt_name]
        )

        if not options.no_interactive:
            pgm_export_config.get_interactive_info()
        totp_code = pgm_export_config.get_totp_code()
        try:
            class_ = pgm_export_config.get_bt_class()
        except Exception as e:
            print("Can't load BugTracker class : " + str(e))
            sys.exit(220)
        try:
            bt = class_(cfg["bugtracker"][cfg_bt_name])
        except Exception as e:
            print("Configuration error on " + cfg_bt_name + " : " + str(e))
            sys.exit(220)

        try:
            ywh = YesWeHack(
                cfg["yeswehack"][cfg_program]["login"],
                cfg["yeswehack"][cfg_program]["password"],
                cfg["yeswehack"][cfg_program]["api_url"],
                lazy=False,
                totp_code=totp_code,
            )
        except Exception as e:
            sys.exit("Failed to login on YesWeHack for {program} : {error}".format(program=cfg_program, error=str(e)))
        #except KeyError as e:
        #    print("Configuration error on " + cfg_program + "\nMissing " + str(e) + " parameter")
        #    sys.exit(120)
        #except TOTPLoginEnabled as e:
        #    print("TOTP login enabled, can't login")
        #    sys.exit(100)
        # ywh.login(totp_code=totp_code)
        reports = ywh.get_reports(
            cfg["yeswehack"][cfg_program]["program"], filters={"status": "accepted"}
        )
        for report in reports:
            report = ywh.get_report(report["id"])
            report.get_comments()
            logging.info("Cheking " + report.title)
            if not check_bug(report.get_comments()):
                # Post issue and comment
                logging.info(report.title + " Marker not found, posting issue")
                issue_meta = {}
                issue = bt.post_issue(report)
                issue_meta["url"] = bt.get_url(issue)
                issue_meta["id"] = bt.get_id(issue)

                comment = (
                    BugTracker.ywh_comment_marker
                    + "\n"
                    + BugTracker.ywh_comment_template.format(
                        type=cfg["bugtracker"][cfg_bt_name]["type"],
                        issue_id=issue_meta["id"],
                        bug_url=issue_meta["url"],
                    )
                )
                logging.info(report.title + ": posting marker")
                report.post_comment(comment, True)
            else:
                logging.debug(report.title + ": marker found, report already imported")


if __name__ == "__main__":
    defaults = {
        "ywh_url_api": "http://api.ywh.docker.local",
        "supported_bugtracker": ["gitlab", "jira", "github"],
    }
    main()
