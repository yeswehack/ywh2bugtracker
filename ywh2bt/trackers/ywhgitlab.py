# -*- encoding: utf-8 -*-

import gitlab

from colorama import Fore, Style

from .bugtracker import BugTracker
from ywh2bt.utils import read_input
from ywh2bt.config import BugTrackerConfig


__all__ = ["YWHGitlab", "YWHGitlabConfig"]


class YWHGitlab(BugTracker):

    token = None
    bt = None
    project = None
    URL = "http://gitlab.com"

    def __init__(self, url, project, token):
        self.url = url
        self.project = project
        self.token = token
        self.bt = gitlab.Gitlab(self.url, private_token=self.token)
        try:
            self.bt.auth()
        except gitlab.exceptions.GitlabAuthenticationError:
            raise

    def get_project(self):
        try:
            project = self.bt.projects.get(self.project)
        except gitlab.exceptions.GitlabAuthenticationError:
            return False
        except gitlab.exceptions.GitlabGetError:
            return False
        return project

    def post_issue(self, report):
        project = self.bt.projects.get(self.project)
        description = self.description_template
        for attachment in report.attachments:
            # Add attachment to gitlab issue if there is attachement in the original bug
            f = project.upload(attachment.original_name, attachment.data)
            description += "\n" + f["markdown"] + "\n"
        issue_data = {
            "title": self.issue_name_template.format(
                report_local_id=report.local_id, report_title=report.title
            ),
            "description": description.format(
                end_point=report.end_point,
                vulnerable_part=report.vulnerable_part,
                cvss=report.cvss.score,
                bug_type=report.bug_type.category.name,
                bug_description=report.bug_type.description,
                remediation_link=report.bug_type.link,
                description=report.description_html,
            ),
        }
        issue = project.issues.create(issue_data)
        return issue

    def get_url(self, issue):
        return issue.links.gitlab.url + issue.links.path

    def get_id(self, issue):
        return issue.id


class YWHGitlabConfig(BugTrackerConfig):
    bugtracker_type = "gitlab"
    client = YWHGitlab

    def __init__(
        self, name, no_interactive=False, configure_mode=False, **config
    ):
        self._bugtracker = None
        keys = []
        if config or not configure_mode:
            keys += ["url", "project"]
            if no_interactive:
                keys.append("token")
            super().__init__(
                name,
                keys,
                no_interactive=no_interactive,
                configure_mode=configure_mode,
                **config
            )
            self._url = config["url"]
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
        if not no_interactive:
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
                + " url [{0}]: ".format(YWHGitlab.URL)
                + Style.RESET_ALL
            )
            or YWHGitlab.URL
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

    def _set_bugtracker(self):
        self._get_bugtracker(self._url, self._project, self._token)

    def to_dict(self):
        component = {
            "url": self.url,
            "project": self.project,
            "type": self.type,
        }
        if self.no_interactive:
            component["token"] = self.token
        return {self.name: component}
