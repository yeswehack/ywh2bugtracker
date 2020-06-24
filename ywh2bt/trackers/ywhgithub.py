# -*- encoding: utf-8 -*-

import github
from .bugtracker import BugTracker
from github.GithubException import BadCredentialsException
from ywh2bt.config import BugTrackerConfig
from bs4 import BeautifulSoup
import requests
from requests_toolbelt import MultipartEncoder
from ywh2bt.logging import logger
from ywh2bt.utils import read_input
from colorama import Fore, Style
from copy import copy
import re

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
    def __init__(
        self, url, project, token, login="", password="", github_cdn_on=False, verify=True
    ):
        self.url = url
        self.project = project
        self.token = token
        self.password = password
        self.username = login
        self.github_cdn_on = github_cdn_on
        self.verify = verify
        self.session = None
        if self.url.endswith("/"):
            self.url = self.url[:-1]

        if self.url != "https://api.github.com":
            self.bt = github.Github(
                base_url=self.url, login_or_token=self.token, verify=self.verify
            )
            self.github_domain = (
                self.url.replace("https://", "")
                .replace("http://", "")
                .split("/")[0]
            )
        else:
            self.bt = github.Github(login_or_token=self.token, verify=self.verify)
            self.github_domain = "github.com"
        try:
            self.bt.get_user().name
        except BadCredentialsException:
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
        copy_report = copy(report)
        repo = self.bt.get_repo(self.project)
        title = self.report_as_title(report)
        body = self.report_as_description(report)
        issue = repo.create_issue(title=title, body=body)
        substitute_regex = r"!?\[[^\[\]]*\]\({text}\)"
        attach_name_regex = "(?:!?\[)([^\[\]]*)(?:\])(?:\({text}\))"
        for attachment in report.attachments:
            attach_name = re.findall(
                attach_name_regex.format(text=re.escape(attachment.url)), body
            )
            if attach_name:
                attach_name = attach_name[0]
            else:
                attach_name = attachment.name
            if self.github_cdn_on:
                attachment.get_data()
                url, status_code = self.post_attachment(
                    attachment, issue.number
                )
                if url:
                    body = body.replace(attachment.url, url)
                else:
                    body = re.sub(
                        substitute_regex.format(
                            text=re.escape(attachment.url)
                        ),
                        '(Attachment "{f_name}" not available due to upload error)'.format(
                            f_name=attach_name
                        ),
                        body,
                    )
            else:
                body = re.sub(
                    substitute_regex.format(text=re.escape(attachment.url)),
                    '(Attachment "{f_name}" not available due to export script’s configuration)'.format(
                        f_name=attach_name
                    ),
                    body,
                )
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

    def cdn_request(self, method, url, data=None, headers={}):
        try:
            if headers:
                requested = self.session.request(
                    method, url, data=data, headers=headers
                )
            else:
                requested = self.session.request(method, url, data=data)
        except Exception as e:
            logger.error(f"An exception occurred on {self.name} : {str(e)}")
            raise e
        return requested

    def login(self):
        """
        Login to github platform
        """
        status = None
        if self.session is None:
            self.session = requests.Session()
            self.session.verify = self.verify
            r = self.cdn_request("GET", f"https://{self.github_domain}/login")
            form = BeautifulSoup(r.text, features="lxml").find("form")
            keys = {}
            for key in [
                "authenticity_token",
                "commit",
                "timestamp_secret",
                "webauthn-support",
                "webauthn-iuvpaa-support",
                "required_field_59db",
                "utf8",
            ]:
                value = form.find("input", {"name": key})
                keys = {**keys, key: value["value"] if value else None}
            status = self.session.post(
                f"https://{self.github_domain}/session",
                data={
                    **keys,
                    "login": self.username,
                    "password": self.password,
                },
            ).status_code
        return status

    def logout(self):
        """
        Logout from github platform
        """
        status = None
        if self.session is not None:
            r = self.cdn_request("GET", f"https://{self.github_domain}/")
            hiddens = (
                BeautifulSoup(r.text, features="lxml")
                .find("form", {"action": "/logout"})
                .findAll("input", {"type": "hidden"})
            )
            data = {}
            for h in hiddens:
                data = {**data, h["name"]: h["value"]}
            status = self.cdn_request(
                "POST", f"https://{self.github_domain}/logout", data=data
            ).status_code
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
            msg = 'Github CDN ("https://{self.github_domain}") login error'
            logger.error(msg)
            raise Exception(msg)

        if self.session:
            repo_id = self.bt.get_repo(self.project).id

            r = self.cdn_request(
                "GET",
                "https://{}/{}/issues/{}".format(
                    self.github_domain, self.project, issue_id
                ),
            )

            file_attach = BeautifulSoup(r.text, features="lxml").find(
                "file-attachment"
            )

            if not file_attach:
                msg = f"Can't get information to upload data, status code: {r.status_code}"
                logger.error(msg)
                raise Exception(msg)
            authenticity_token = file_attach.get("data-upload-policy-authenticity-token", None)
            if authenticity_token is None:
                csrf_policy_input = file_attach.find('input', {'class': 'js-data-upload-policy-url-csrf'})
                if csrf_policy_input is not None:
                    authenticity_token = csrf_policy_input.get('value', None)
            if authenticity_token is None:
                msg = f'Unable to find authenticity token. Please report this error to the script maintainer.'
                logger.error(msg)
                raise Exception(msg)
            filename = attachment.original_name.split("/")[-1]
            content_type = attachment.mime_type
            fields = {
                "name": filename,
                "size": str(len(attachment.data)),
                "content_type": content_type,
                "authenticity_token": authenticity_token,
                "repository_id": "{}".format(repo_id),
            }
            data = MultipartEncoder(fields=fields)
            href = self.cdn_request(
                "POST",
                f"https://{self.github_domain}/upload/policies/assets",
                data=data,
                headers={
                    **self.session.headers,
                    "Content-Type": data.content_type,
                    "Content-Length": str(data.len),
                },
            )
            status_code = href.status_code
            if status_code == 201:  #  status_code 201
                info = href.json()
                if "asset" not in info:
                    msg = f"Can't upload data, response: {info}"
                    logger.error(msg)
                    raise Exception(msg)
                url = info["asset"]["href"]
                fields = {}
                for field, value in info["form"].items():
                    fields[field] = value
                fields["file"] = (filename, attachment.data, content_type)
                data = MultipartEncoder(fields=fields)
                href = self.cdn_request(
                    "POST",
                    info["upload_url"],
                    data=data,
                    headers={
                        **self.session.headers,
                        "Content-Type": data.content_type,
                        "Content-Length": str(data.len),
                    },
                )
                status_code = href.status_code

                data = MultipartEncoder(
                    fields={
                        "authenticity_token": info[
                            "asset_upload_authenticity_token"
                        ]
                    }
                )
                r = self.cdn_request(
                    "PUT",
                    f"https://{self.github_domain}" + info["asset_upload_url"],
                    data=data,
                    headers={
                        **self.session.headers,
                        "Content-Type": data.content_type,
                        "Content-Length": str(data.len),
                        "Referer": "https://{}/{}/issues/{}".format(
                            self.github_domain, self.project, issue_id
                        ),
                        "Accept": "application/json",
                    },
                )
                status_code = r.status_code
                try:
                    info = r.json()
                    url = info.get("href", "") or url
                except:
                    url = ""
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
    optional_keys = dict(url="https://api.github.com", github_cdn_on=False, verify=True)
    _description = dict(
        project="path/to/project",
        github_cdn_on="Enable or Disable saving attachment file to Github CDN",
    )

    conditional_keys = dict(
        password=dict(condition=lambda x: x._github_cdn_on, secret=True),
        login=dict(condition=lambda x: x._github_cdn_on, secret=False),
    )

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def _set_bugtracker(self):
        if self._github_cdn_on:
            self._get_bugtracker(
                self._url,
                self._project,
                self._token,
                login=self._login,
                password=self._password,
                github_cdn_on=self._github_cdn_on,
                verify=self._verify
            )
        else:
            self._get_bugtracker(self._url, self._project, self._token)

    def user_config(self):
        self._github_cdn_on = (
            True
            if self._github_cdn_on.lower().strip() in ["true", "y", "yes", "1"]
            else False
        )
