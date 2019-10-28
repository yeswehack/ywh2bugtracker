# -*- encoding: utf-8 -*-

import jira
import html2text
from .bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig


__all__ = ["YWHJira", "YWHJiraConfig"]


class YWHJira(BugTracker):

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

    mandatory_keys = ["url", "login", "project"]
    secret_keys = ["password"]
    optional_keys = dict(issuetype="Task")

    def _set_bugtracker(self):
        self._get_bugtracker(
            self._url,
            self._login,
            self._password,
            self._project,
            issuetype=self._issuetype,
        )
