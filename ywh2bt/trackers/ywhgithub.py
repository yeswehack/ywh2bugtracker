# -*- encoding: utf-8 -*-

import github
from .bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig
from bs4 import BeautifulSoup

__all__ = ["YWHGithub", "YWHGithubConfig"]

"""
Github Bugtracker System
"""

class YWHGithub(BugTracker):

    """
    Github Client Wrapper
    """

    ############################################################
    ####################### Constructor ########################
    ############################################################
    def __init__(self, project, token):

        self.project = project
        self.token = token
        self.bt = github.Github(self.token)
        try:
            self.bt.get_user().name
        except github.GithubException.BadCredentialsException:
            raise

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def get_project(self):
        """
        return github project object
        """
        try:
            repo = self.bt.get_repo(self.project)
        except github.GithubException.UnknownObjectException:
            raise
        return repo

    def post_issue(self, report):
        """
        post issue to github from report information

        :param yeswehack.api.Report report: Report from yeswehack
        """
        repo = self.bt.get_repo(self.project)
        title = self.report_as_title(report)
        body = self.report_as_description(report)
        for attachment in report.attachments:
            attachment.get_data()
        issue = repo.create_issue(title=title, body=body)
        return issue

    def get_url(self, issue):
        """
        Return issue url
        """
        return issue.html_url

    def get_id(self, issue):
        """
        Return issue id
        """
        return issue.number

    def report_as_description(self, report, template=None, additional_keys=[]):
        """
        Overwrite report_as_description BugTrackerConfig method.
        """
        report.description_html = self._img_to_a_balisis(report.description_html)
        return super().report_as_description(report, template=template, additional_keys=additional_keys)

    def _img_to_a_balisis(self, html):
        """
        Replace "img" balisis in html to "a" balisis.
        """
        soup = BeautifulSoup(html, features="lxml")
        n_html = str(soup)
        for img in soup.findAll("img"):
            alt = img.attrs.get('alt', '')
            src = img.attrs.get('src', '')
            a = f'<a href="{src}">{alt}</a>'
            n_html = n_html.replace(str(img), a)
        return n_html

class YWHGithubConfig(BugTrackerConfig):

    """
    BugTrackerConfig Class associated to github.

    :attr str bugtracker_type: bugtracker identifier
    :attr class client: Client class
    :attr list mandatory_keys: keys needed in configuration file part
    :attr list secret_keys: keys need interaction in interactive mode
    :attr dict optional_keys: keys with default values
    :attr dict _description: descriptor for each specified key
    """
    bugtracker_type = "github"
    client = YWHGithub

    mandatory_keys = ["project"]
    secret_keys = ["token"]
    optional_keys = dict(url="https://github/api/v3")
    _description = dict(project="path/to/project")

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def _set_bugtracker(self):
        self._get_bugtracker(self._project, self._token)
