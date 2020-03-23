# -*- encoding: utf-8 -*-

import gitlab
import requests
from .bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig
from copy import copy

__all__ = ["YWHGitlab", "YWHGitlabConfig"]


"""
GiLab Bugtracker System
"""


class YWHGitlab(BugTracker):

    """
    Gitlab Client Wrapper
    """

    ############################################################
    ####################### Constructor ########################
    ############################################################
    def __init__(self, url, project, token, verify=True):
        self.url = url
        self.project = project
        self.token = token
        self.session = requests.Session()
        self.session.verify = verify
        self.bt = gitlab.Gitlab(self.url, private_token=self.token, session=self.session)
        try:
            self.bt.auth()
        except gitlab.exceptions.GitlabAuthenticationError:
            raise

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def get_project(self):
        try:
            project = self.bt.projects.get(self.project)
        except gitlab.exceptions.GitlabAuthenticationError:
            return False
        except gitlab.exceptions.GitlabGetError:
            return False
        return project

    def post_issue(self, report):
        copy_report = copy(report)
        project = self.bt.projects.get(self.project)
        for attachment in report.attachments:
            # Add attachment to gitlab issue if there is attachement in the original bug
            f = project.upload(attachment.original_name, attachment.data)
            copy_report.description_html = copy_report.description_html.replace(
                attachment.url, f["url"]
            )

        description = self.report_as_description(copy_report)
        issue_data = {
            "title": self.report_as_title(copy_report),
            "description": description,
        }
        issue = project.issues.create(issue_data)
        return issue

    def get_url(self, issue):
        return issue.web_url

    def get_id(self, issue):
        return issue.id


class YWHGitlabConfig(BugTrackerConfig):

    """
    BugTrackerConfig Class associated to gitlab

    :attr str bugtracker_type: bugtracker identifier
    :attr class client: Client class
    :attr list mandatory_keys: keys needed in configuration file part
    :attr list secret_keys: keys need interaction in interactive mode
    :attr dict optional_keys: keys with default values
    :attr dict _description: descriptor for each specified key
    """

    bugtracker_type = "gitlab"
    client = YWHGitlab

    mandatory_keys = ["project"]
    secret_keys = ["token"]
    optional_keys = dict(url="http://gitlab.com", verify=True)
    _description = dict(project="path/to/project")

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def _set_bugtracker(self):
        self._get_bugtracker(self._url, self._project, self._token, verify=self._verify)
