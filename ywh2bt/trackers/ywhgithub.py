# -*- encoding: utf-8 -*-

import github
from .bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig


__all__ = ["YWHGithub", "YWHGithubConfig"]


class YWHGithub(BugTracker):
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

    mandatory_keys = ["project"]
    secret_keys = ["token"]
    optional_keys = dict(url="https://github/api/v3")
    _description = dict(project="path/to/project")

    def _set_bugtracker(self):
        self._get_bugtracker(self._project, self._token)
