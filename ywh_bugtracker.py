#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from ywh2bt.ywh2bt import main

"""
Entry script
"""
if __name__ == "__main__":

    defaults = {
        "ywh_url_api": "http://api.ywh.docker.local",
        "supported_bugtracker": ["gitlab", "jira", "github"],
    }
    main()
