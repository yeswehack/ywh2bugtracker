#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import os
import yaml
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
from ywh2bt.logging import logger

__all__ = ["main"]

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
        default=False,
    )
    parser.add_option(
        "-f", "--filename", action="store", dest="filename", default=""
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
    ywh_cfg = config.GlobalConfig(
        no_interactive=options.no_interactive,
        filename=options.filename,
        configure_mode=options.configure,
    )

    if not options.configure:
        run(ywh_cfg, options)
    deinit()


def run(cfg, options):

    for cfg_ywh in cfg.yeswehack:
        # Iterate on every referenced program
        logger.info("Get info for " + cfg_ywh.name)
        for cfg_pgm in cfg_ywh.programs:

            reports = cfg_ywh.ywh.get_reports(
                cfg_pgm.name,
                filters={"filter[status][]": "accepted"},  #  tracking_status
                lazy=True,
            )

            for report in reports:
                logger.info("Checking " + report.title)
                comments = report.get_comments(lazy=True)

                for cfg_bt in cfg_pgm.bugtrackers:

                    marker = BugTracker.ywh_comment_marker.format(
                        url=cfg_bt.url, project_id=cfg_bt.project
                    )

                    if not check_bug(comments, marker):
                        # Post issue and comment
                        logger.info(
                            report.title + " Marker not found, posting issue"
                        )

                        issue = cfg_bt.bugtracker.post_issue(report)
                        issue_meta = {
                            "url": cfg_bt.bugtracker.get_url(issue),
                            "id": cfg_bt.bugtracker.get_id(issue),
                        }

                        comment = (
                            marker
                            + "\n"
                            + BugTracker.ywh_comment_template.format(
                                type=cfg_bt.type,
                                issue_id=issue_meta["id"],
                                bug_url=issue_meta["url"],
                            )
                        )

                        logger.info(report.title + ": posting marker")

                        report.post_comment(comment, True)
                    else:
                        logger.info(
                            report.title
                            + ": marker found, report already imported"
                        )
