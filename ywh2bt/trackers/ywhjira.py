# -*- encoding: utf-8 -*-

import jira
import html2text
from colorama import Fore, Style
from .bugtracker import BugTracker
from ywh2bt.utils import read_input
from ywh2bt.config import BugTrackerConfig


class YWHJira(BugTracker):

    jira = None
    project = None
    description_template = """
||  bug type  ||    Description   ||       Remediation         ||
| {bug_type} | {bug_description}| {remediation_link}        |

||    scope    ||  vulnerable part  ||  CVSS ||
| {end_point} | {vulnerable_part} | {cvss} |

{description}
    """

    def __init__(self, url, login, password, project, issuetype="Task"):
        self.url = url
        self.login = login
        self.password = password
        self.project = project
        self.issuetype = issuetype
        try:
            self.jira = jira.JIRA(self.url, auth=(self.login, self.password))
        except jira.exceptions.JIRAError:
            raise

    def get_project(self):
        try:
            self.jira.project(self.project)
        except jira.exceptions.os:
            raise

    def post_issue(self, report):
        html = html2text.HTML2Text()
        html.ignore_links = True

        issue_data = {
            "project": {"key": self.project},
            "summary": self.issue_name_template.format(
                report_local_id=report.local_id, report_title=report.title
            ),
            "description": self.description_template.format(
                end_point=report.end_point,
                vulnerable_part=report.vulnerable_part,
                cvss=report.cvss.score,
                bug_type=report.bug_type.category.name,
                bug_description=report.bug_type.description,
                remediation_link=report.bug_type.link,
                description=html.handle(report.description_html),
            ),
            "issuetype": {"name": self.issuetype},
        }
        issue = self.jira.create_issue(**issue_data)
        for attachment in report.attachments:
            attachment.get_data()
            self.jira.add_attachment(
                issue=issue,
                filename=attachment.original_name,
                attachment=attachment.data,
            )
        return issue

    def get_url(self, issue):
        return issue.permalink()

    def get_id(self, issue):
        return issue.key


class YWHJiraConfig(BugTrackerConfig):
    bugtracker_type = "jira"
    client = YWHJira

    def __init__(
        self, name, no_interactive=False, configure_mode=False, **config
    ):
        self._bugtracker = None
        keys = []
        if config or not configure_mode:
            keys += ["url", "login", "project"]
            if no_interactive:
                keys.append("password")
            super().__init__(
                name,
                keys,
                no_interactive=no_interactive,
                configure_mode=configure_mode,
                **config
            )
            self._url = config["url"]
            self._login = config["login"]
            self._password = config["password"] if no_interactive else ""
            self._project = config["project"]  # project_id
            self._issuetype = config.get("issuetype", "Task")
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
    def login(self):
        return self._login

    @property
    def password(self):
        return self._password

    @property
    def issuetype(self):
        return self._issuetype

    def config_url(self):
        self._url = read_input(
            Fore.BLUE + self.type.title() + " url: " + Style.RESET_ALL
        )

    def config_params(self):
        self._login = read_input(Fore.BLUE + "Login: " + Style.RESET_ALL)
        self._issuetype = (
            read_input(
                Fore.BLUE + "Issue Type (default:  Task): " + Style.RESET_ALL
            )
            or "Task"
        )

    def config_secret(self):
        self._password = read_input(
            Fore.BLUE
            + "Password for "
            + Fore.GREEN
            + self.login
            + Fore.BLUE
            + " on "
            + Fore.GREEN
            + self.url
            + Fore.BLUE
            + ": "
            + Style.RESET_ALL,
            secret=True,
        )

    def _set_bugtracker(self):
        self._get_bugtracker(
            self._url,
            self._login,
            self._password,
            self._project,
            issuetype=self._issuetype,
        )

    def to_dict(self):
        component = {
            "url": self.url,
            "login": self.login,
            "project": self.project,
            "type": self.type,
            "issuetype": self.issuetype,
        }
        if self.no_interactive:
            component["password"] = self.password
        return {self.name: component}
