#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import os
import yaml
import logging
import getpass
from pathlib import Path
from colorama import Fore, Style, init, deinit
from optparse import OptionParser
from yeswehack.api import YesWeHack
from yeswehack.exceptions import (
    BadCredentials,
    ObjectNotFound,
    InvalidResponse,
    TOTPLoginEnabled,
)
from ywh2bt.trackers.bugtracker import BugTracker
from ywh2bt import config
from ywh2bt.trackers import ywhgitlab, ywhgithub, ywhjira, ywhtfs, ywhazuredevops


def check_bug(comments, comment):
    return any(
        report_comment.message_html is not None
        and comment in report_comment.message_html
        for report_comment in comments
    )


def main():
    init()
    parser = OptionParser(usage="usage: %prod [option]")
    parser.add_option(
        "-c",
        "--configure",
        action="store_true",
        dest="configure",
        help="Create config file",
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
        deinit()
    else:
        cfg = ywh_cfg.load()
        logging.basicConfig(
            format="%(asctime)s %(message)s",
            level=logging.INFO,
            datefmt="%m/%d/%Y %H:%M:%S",
        )
        if cfg:
            # if options.no_interactive:
            run(cfg, options)
            deinit()
        else:
            deinit()
            sys.exit('No configuration detected or "-c" option missing')


def run(cfg, options):

    for cfg_program in cfg["yeswehack"]:
        # Iterate on every referenced program
        logging.info("Get info for " + cfg_program)
        cfg_bt_name = cfg["yeswehack"][cfg_program]["bt"]
        pgm_export_config = config.Config(
            yeswehack=cfg["yeswehack"][cfg_program],
            bugtracker=cfg["bugtracker"][cfg_bt_name],
        )
        if not options.no_interactive:
            pgm_export_config.get_interactive_info()
        totp_code = pgm_export_config.get_totp_code()
        try:
            class_ = pgm_export_config.get_bt_class()
        except Exception as e:
            print("Can't load BugTracker class : " + str(e))
            deinit()
            sys.exit(220)
        try:
            bt = class_(cfg["bugtracker"][cfg_bt_name])
        except Exception as e:
            print("Configuration error on " + cfg_bt_name + " : " + str(e))
            deinit()
            sys.exit(220)

        try:
            ywh = YesWeHack(
                username=cfg["yeswehack"][cfg_program]["login"],
                password=cfg["yeswehack"][cfg_program]["password"],
                api_url=cfg["yeswehack"][cfg_program]["api_url"],
                lazy=False,
                totp_code=totp_code,
            )
        except Exception as e:
            deinit()
            sys.exit(
                "Failed to login on YesWeHack for {program} : {error}".format(
                    program=cfg_program, error=str(e)
                )
            )

        reports = ywh.get_reports(
            cfg["yeswehack"][cfg_program]["program"],
            filters={"status": "accepted"},
        )
        for report in reports:
            report.get_comments()
            logging.info("Cheking " + report.title)

            comments = report.get_comments()
            marker = BugTracker.ywh_comment_marker.format(
                url=cfg["bugtracker"][cfg_bt_name]["url"],
                project_id=cfg["bugtracker"][cfg_bt_name]["project_id"],
            )

            if not check_bug(comments, marker):

                # Post issue and comment
                logging.info(report.title + " Marker not found, posting issue")

                issue = bt.post_issue(report)
                issue_meta = {"url": bt.get_url(issue), "id": bt.get_id(issue)}

                comment = (
                    marker
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
                logging.debug(
                    report.title + ": marker found, report already imported"
                )
