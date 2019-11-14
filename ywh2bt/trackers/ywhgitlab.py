# -*- encoding: utf-8 -*-

import gitlab
from .bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig


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
    def __init__(self, url, project, token):
        self.url = url
        self.project = project
        self.token = token
        self.bt = gitlab.Gitlab(self.url, private_token=self.token)
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
        project = self.bt.projects.get(self.project)
        description = self.report_as_descripton(report)
        for attachment in report.attachments:
            # Add attachment to gitlab issue if there is attachement in the original bug
            f = project.upload(attachment.original_name, attachment.data)
            description += "\n" + f["markdown"] + "\n"
        issue_data = {
            "title": self.report_as_title(report),
            "description": description
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
    optional_keys = dict(url="http://gitlab.com")
    _description = dict(project="path/to/project")

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def _set_bugtracker(self):
        self._get_bugtracker(self._url, self._project, self._token)
