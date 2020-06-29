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
__VERSION__ = "0.5.3"

"""
Entry point for script and setup
"""


def main():
    """
    Parse args from commande line, setup GlobalConfig and run corresponding process.
    """
    init()

    description = (
        "ywh2bt is a simple YesWeHack tools for Bounty Program manager."
        + "it's build to exchange report log from the platform to your issue manager."
    )

    parser = OptionParser(
        usage="",
        version="%prog {}".format(__VERSION__),
        description=description,
    )
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
        help="non interactive mode. Store credencials on disk. You need to activate it on configure to store credencials",
    )

    parser.set_usage(
        "usage: %prog [-f|--filename] FILENAME [-n|--no-interactive] [-c|--configure]\n\n{}".format(
            parser.format_help()
        )
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
    """
    Process YesWeHack Report Log loading and insert them in bugtrackers systems.
    """
    for cfg_ywh in cfg.yeswehack:
        # Iterate on every referenced program
        logger.info("Get info for " + cfg_ywh.name)
        ywh_domain = ".".join(
            cfg_ywh.api_url.replace("https://", "")
            .replace("http://", "")
            .split(".")[1:]
        )
        ywh_domain = ywh_domain.split("/")[0]
        for cfg_pgm in cfg_ywh.programs:

            reports = cfg_ywh.ywh.get_reports(
                cfg_pgm.slug,
                filters={"filter[trackingStatus][]": "AFI"},
                lazy=True,
            )
            for report in reports:
                report = cfg_ywh.ywh.get_report(report.id)
                logger.info("Checking " + report.title)
                comments = report.get_comments(lazy=True)
                for cfg_bt in cfg_pgm.bugtrackers:
                    try:
                        cfg_bt.set_yeswehack_domain(ywh_domain)
                        issue = cfg_bt.bugtracker.post_issue(report)
                        issue_meta = {
                            "url": cfg_bt.bugtracker.get_url(issue),
                            "id": cfg_bt.bugtracker.get_id(issue),
                        }

                        logger.info(report.title + " posted to " + cfg_bt.name)

                        marker = BugTracker.ywh_comment_marker.format(
                            url=cfg_bt.url, project_id=cfg_bt.project
                        )

                        comment = (
                            marker
                            + "\n"
                            + BugTracker.ywh_comment_template.format(
                                type=cfg_bt.type,
                                issue_id=issue_meta["id"],
                                bug_url=issue_meta["url"],
                            )
                        )
                        resp = report.put_tracking_status(
                            "T",
                            cfg_bt.name,
                            issue_meta["url"],
                            tracker_id=issue_meta["id"],
                            message=comment,
                        )

                        try:
                            resp_json = resp.json()
                        except:
                            logger.error("Response from YesWeHack not JSON")
                        else:
                            if "errors" in resp_json:
                                logger.error(
                                    "Status Update Error : {}".format(
                                        resp_json.get(
                                            "error_description", resp.text
                                        )
                                    )
                                )
                            else:
                                logger.info("Status updated.")
                    except Exception as e:
                        logger.error(
                            "An error occurred on {}, continuing with the next bugtracker".format(
                                cfg_bt.name
                            )
                        )
