# -*- encoding: utf-8 -*-

import gitlab
import getpass

from colorama import Fore, Style

from lib.bugtracker import BugTracker


class YWHGitlab(BugTracker):

    token = None
    bt = None
    project = None
    URL = "http://git.ywh.docker.local"
    # URL = "https://gitlab.com"

    def __init__(self, config):
        self.URL = config["url"]
        self.bt = gitlab.Gitlab(self.URL, private_token=config["token"])
        try:
            self.bt.auth()
        except gitlab.exceptions.GitlabAuthenticationError:
            raise
        if "project_id" in config.keys():
            self.project = config["project_id"]

    @staticmethod
    def configure(bugtracker):
        bugtracker["url"] = input(
            Fore.BLUE
            + bugtracker["type"].title()
            + " url [{0}]: ".format(YWHGitlab.URL)
            + Style.RESET_ALL
        )
        bugtracker["url"] = bugtracker["url"] or YWHGitlab.URL

    @staticmethod
    def get_interactive_info(bt_cfg):
        token = getpass.getpass(
            prompt=Fore.BLUE
            + "Token for "
            #+ Fore.GREEN
            #+ bt_cfg["login"]
            #+ Fore.BLUE
            #+ " on "
            + Fore.GREEN
            + bt_cfg["url"]
            + Fore.BLUE
            + ": "
            + Style.RESET_ALL
        )
        return {"token": token}

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
