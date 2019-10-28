# -*- encoding: utf-8 -*-

import gitlab
from .bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig


__all__ = ["YWHGitlab", "YWHGitlabConfig"]


class YWHGitlab(BugTracker):
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

    mandatory_keys = ["project"]
    secret_keys = ["token"]
    optional_keys = dict(url="http://gitlab.com")

    def _set_bugtracker(self):
        self._get_bugtracker(self._url, self._project, self._token)
