# -*- encoding: utf-8 -*-

import github
from colorama import Fore, Style
from .bugtracker import BugTracker
from ywh2bt.utils import read_input


class YWHGithub(BugTracker):

    token = None
    bt = None
    project = None
    URL = "https://github/api/v3"

    def __init__(self, config):
        self.bt = github.Github(config["token"])
        try:
            self.bt.get_user().name
        except github.GithubException.BadCredentialsException:
            raise
        if "project_id" in config.keys():
            self.project = config["project_id"]

    @staticmethod
    def configure(bugtracker):
        bugtracker["url"] = (
            read_input(
                Fore.BLUE
                + bugtracker["type"].title()
                + " url (default : '{}'):".format(YWHGithub.URL)
                + Style.RESET_ALL
            )
            or YWHGithub.URL
        )
        bugtracker["token"] = read_input(
            Fore.BLUE + "Token: " + Style.RESET_ALL, secret=True
        )
        return bugtracker

    def get_project(self):
        try:
            repo = self.bt.get_repo(self.project)
        except github.GithubException.UnknownObjectException:
            raise
        return repo

    def post_issue(self, report):
        repo = self.bt.get_repo(self.project)
        description = self.description_template
        title = self.issue_name_template.format(
            report_local_id=report.local_id, report_title=report.title
        )
        body = description.format(
            end_point=report.end_point,
            vulnerable_part=report.vulnerable_part,
            cvss=report.cvss.score,
            bug_type=report.bug_type.category.name,
            bug_description=report.bug_type.description,
            remediation_link=report.bug_type.link,
            description=report.description_html,
        )
        issue = repo.create_issue(title=title, body=body)
        return issue

    def get_url(self, issue):
        return issue.html_url

    def get_id(self, issue):
        return issue.number
