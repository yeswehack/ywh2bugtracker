# -*- encoding: utf-8 -*-

import jira
import html2text
import getpass
from colorama import Fore, Style
from lib.bugtracker import BugTracker


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

    def __init__(self, config):
        self.jira = jira.JIRA(config["url"], auth=(config["login"], config["password"]))
        try:
            self.jira = jira.JIRA(config["url"], auth=(config["login"], config["password"]))
        except jira.exceptions.JIRAError:
            raise
        if "project_id" in config.keys():
            self.project = config["project_id"]

    @staticmethod
    def configure(bugtracker):
        bugtracker["url"] = input(Fore.BLUE + bugtracker["type"].title() + " url: " + Style.RESET_ALL)
        bugtracker["login"] = input(Fore.BLUE + "Login: " + Style.RESET_ALL)

    @staticmethod
    def get_interactive_info(bt_cfg):
        password = getpass.getpass(prompt=Fore.BLUE
                + "Password for " 
                + Fore.GREEN
                + bt_cfg["login"]
                + Fore.BLUE
                + " on "
                + Fore.GREEN
                + bt_cfg["url"]
                + Fore.BLUE
                + ": "
                + Style.RESET_ALL)
        return {"password" : password}


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
            "issuetype": {"name": "Tâche"},
        }
        issue = self.jira.create_issue(issue_data)
        for attachment in report.attachments:
            attachment.get_data()
            self.jira.add_attachment(
                issue=issue, filename=attachment.original_name, attachment=attachment.data
            )
        return issue

    def get_url(self, issue):
        return issue.permalink()

    def get_id(self, issue):
        return issue.key
