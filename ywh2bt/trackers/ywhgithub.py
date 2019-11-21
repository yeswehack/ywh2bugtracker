# -*- encoding: utf-8 -*-

import github
from .bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig
from bs4 import BeautifulSoup
import requests
from requests_toolbelt import MultipartEncoder
import magic
from ywh2bt.utils import read_input
from colorama import Fore, Style

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
    def __init__(self, project, token, login="", password="", github_cdn_on=False):

        self.project = project
        self.token = token
        self.password = password
        self.username = login
        self.github_cdn_on = github_cdn_on
        self.session = None

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
        issue = repo.create_issue(title=title, body=body)
        for attachment in report.attachments:
            attachment.get_data()
            url, status_code = self.post_attachment(attachment, issue.number)
            if url:
                body = body.replace(attachment.url, url)
        issue.edit(body=body)
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

    def login(self):
        """
        Login to github platform
        """
        status = None
        if self.session is None:
            self.session = requests.Session()
            r = self.session.get('https://github.com/login')
            form = BeautifulSoup(r.text, features="lxml").find('form')
            keys = {}
            for key in [
                "authenticity_token",
                "commit",
                "timestamp_secret",
                "webauthn-support",
                "webauthn-iuvpaa-support",
                "required_field_59db",
                "utf8"
            ]:
                value = form.find('input', {"name": key})
                keys = {
                    **keys,
                    key: value['value'] if value else None
                }
            status = self.session.post(
                'https://github.com/session',
                data={
                    **keys,
                    'login' : self.username,
                    "password" : self.password
                }
            ).status_code
        return status

    def logout(self):
        """
        Logout from github platform
        """
        status = None
        if self.session is not None:
            r = self.session.get('https://github.com/')
            hiddens = (
                BeautifulSoup(r.text, features="lxml")
                .find('form', {"action": "/logout"})
                .findAll('input', {"type" : "hidden"})
            )
            data = {}
            for h in hiddens:
                data = {
                    **data,
                    h['name']: h['value']
                }
            status = self.session.post('https://github.com/logout', data=data).status_code
            self.session = None
        return status

    def post_attachment(self, attachment, issue_id):
        """
        Post attachment to issue on github CDN

        :param yeswehack.api.Attachment attachment: Attachment file representation.
        :param int issue_id: issue_id on project.
        """
        url = ""
        status_code = self.login()
        href = None
        if status_code != 200:
            return url, status_code

        if self.session:
            repo_id = self.bt.get_repo(self.project).id

            r = self.session.request(
                'GET',
                "https://github.com/{}/issues/{}".format(self.project, issue_id)
            )
            file_attach = BeautifulSoup(r.text, features="lxml").find('file-attachment')
            filename = attachment.original_name.split('/')[-1]
            content_type = magic.from_buffer(attachment.data, mime=True)
            fields={
                "name": filename,
                "size": str(len(attachment.data)),
                "content_type": content_type,
                "authenticity_token": (
                    file_attach['data-upload-policy-authenticity-token']
                ),
                "repository_id" : "{}".format(repo_id)
            }
            data = MultipartEncoder(fields=fields)
            href = self.session.request(
                'POST',
                'https://github.com/upload/policies/assets',
                data=data,
                headers={
                    **self.session.headers,
                    "Content-Type" : data.content_type,
                    "Content-Length": str(data.len),
                }
            )
            status_code = href.status_code
            if status_code == 201:# status_code 201
                info = href.json()
                url = info['asset']["href"]
                fields = {}
                for field,value in info['form'].items():
                    fields[field] = value
                fields['file']  = (filename, attachment.data, content_type)
                data = MultipartEncoder(fields=fields)
                href = self.session.request(
                    'POST',
                    info['upload_url'],
                    data=data,
                    headers={
                        **self.session.headers,
                        "Content-Type" : data.content_type,
                        "Content-Length": str(data.len),
                    }
                )
                status_code = href.status_code
            self.logout()
            return url, status_code


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
    optional_keys = dict(url="https://github.com/api/v3", github_cdn_on=False)
    _description = dict(project="path/to/project", github_cdn_on="Enable or Disable saving attachment file to Github CDN")

    conditional_keys = dict(password=dict(condition=lambda x: x._github_cdn_on, secret=True), login=dict(condition=lambda x: x._github_cdn_on, secret=False))


    ############################################################
    #################### Instance methods ######################
    ############################################################
    def _set_bugtracker(self):
        if self._github_cdn_on:
            self._get_bugtracker(self._project, self._token, login=self._login, password=self._password, github_cdn_on=self._github_cdn_on)
        else:
            self._get_bugtracker(self._project, self._token)

    def user_config(self):
        self._github_cdn_on = True if self._github_cdn_on.lower().strip() in ["true", "y", "yes", "1"] else False
