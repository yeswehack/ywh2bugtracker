# -*- encoding: utf-8 -*-

import github
from colorama import Fore, Style
from .bugtracker import BugTracker
from ywh2bt.utils import read_input
from ywh2bt.config import BugTrackerConfig


__all__ = ["YWHGithub", "YWHGithubConfig"]


class YWHGithub(BugTracker):

    token = None
    bt = None
    project = None
    URL = "https://github/api/v3"

    def __init__(self, project, token):

        self.project = project
        self.token = token
        self.bt = github.Github(self.token)
        try:
            self.bt.get_user().name
        except github.GithubException.BadCredentialsException:
            raise

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


class YWHGithubConfig(BugTrackerConfig):
    bugtracker_type = "github"
    client = YWHGithub

    def __init__(
        self, name, no_interactive=False, configure_mode=False, **config
    ):
        keys = []
        self._bugtracker = None

        if config or not configure_mode:
            keys += ["project"]
            if no_interactive:
                keys.append("token")
            super().__init__(
                name, keys, no_interactive=no_interactive, **config
            )
            self._url = config.get("url", "https://github/api/v3")
            self._token = config["token"] if no_interactive else ""
            self._project = config["project"]
        else:
            super().__init__(
                name,
                keys,
                no_interactive=no_interactive,
                configure_mode=configure_mode,
            )
        if configure_mode:
            self.configure()

        if not no_interactive and not configure_mode:
            self.get_interactive_info()

        if not self._bugtracker:
            self._set_bugtracker()

    @property
    def token(self):
        return self._token

    def config_url(self):
        self._url = (
            read_input(
                Fore.BLUE
                + self.type.title()
                + " url (default : '{}'): ".format(YWHGithub.URL)
                + Style.RESET_ALL
            )
            or YWHGithub.URL
        )

    def config_params(self):
        pass

    def config_secret(self):
        self._token = read_input(
            Fore.BLUE
            + "Token for "
            + Fore.GREEN
            + self.url
            + Fore.BLUE
            + ": "
            + Style.RESET_ALL,
            secret=True,
        )

    def to_dict(self):
        component = {
            "url": self.url,
            "project": self.project,
            "type": self.type,
        }
        if self.no_interactive:
            component["token"] = self.token
        return {self.name: component}

    def _set_bugtracker(self):
        self._get_bugtracker(self._project, self._token)
