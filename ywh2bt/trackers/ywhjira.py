# -*- encoding: utf-8 -*-

import jira
import html2text
from .bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig


__all__ = ["YWHJira", "YWHJiraConfig"]


class YWHJira(BugTracker):
    """
    Jira Client Wrapper
    """

    description_template = """
||  bug type  ||    Description   ||       Remediation         ||
| {bug_type__category__name} | {bug_type__description}| {bug_type__link}        |

||    scope    ||  vulnerable part  ||  CVSS ||
| {scope} | {vulnerable_part} | {cvss__score} |

{description_html}
    """

    ############################################################
    ####################### Constructor ########################
    ############################################################
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

    ############################################################
    #################### Instance methods ######################
    ############################################################
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
            "summary": self.report_as_title(report),
            "description": self.report_as_descripton(report),
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

    """
    BugTrackerConfig Class associated to jira.

    :attr str bugtracker_type: bugtracker identifier
    :attr class client: Client class
    :attr list mandatory_keys: keys needed in configuration file part
    :attr list secret_keys: keys need interaction in interactive mode
    :attr dict optional_keys: keys with default values
    :attr dict _description: descriptor for each specified key
    """

    bugtracker_type = "jira"
    client = YWHJira

    mandatory_keys = ["url", "login", "project"]
    secret_keys = ["password"]
    optional_keys = dict(issuetype="Task")
    _description = dict(project="Jira slug")

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def _set_bugtracker(self):
        self._get_bugtracker(
            self._url,
            self._login,
            self._password,
            self._project,
            issuetype=self._issuetype,
        )
