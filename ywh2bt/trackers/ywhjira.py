# -*- encoding: utf-8 -*-

import jira
import html2text
from .bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig
from ywh2bt.utils import html2jira, unescape_text
from bs4 import BeautifulSoup
from pprint import pprint
from copy import copy
from string import Formatter

__all__ = ["YWHJira", "YWHJiraConfig"]


class YWHJira(BugTracker):
    """
    Jira Client Wrapper
    """

    description_template = """
    || Title || {local_id} : {title} ||
    | Priority | {priority__name} |
    | Bug Type | [{bug_type__name}]({bug_type__link}) => [Remediation]({bug_type__remediation_link}) |
    | Scope | {scope} |
    | Severity | {cvss__criticity}, score {cvss__score:.1f}, vector {cvss__vector}|
    | Endpoint |{end_point}|
    | Vulnerable part | {vulnerable_part} |
    | Part Name | {part_name} |
    | Payload | {payload_sample} |
    | Technical Environment | {technical_information}|

    {description_html}
    """

    tag_format = "yeswehack_code_section_{idx}"
    ############################################################
    ####################### Constructor ########################
    ############################################################
    def __init__(self, url, login, password, project, issuetype="Task", verify=True):
        self.url = url
        self.login = login
        self.password = password
        self.project = project
        self.issuetype = issuetype
        self.verify = verify
        try:
            self.jira = jira.JIRA(
                    self.url, basic_auth=(self.login, self.password), options={'verify': self.verify}
            )
        except jira.exceptions.JIRAError:
            raise

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def get_project(self):
        try:
            self.jira.project(self.project)
        except jira.exceptions.os:
            raise

    def post_issue(self, report):
        copy_report = copy(report)
        html = html2text.HTML2Text()
        html.ignore_links = True
        desc, tags = self.report_as_description(copy_report)
        issue_data = {
            "project": {"key": self.project},
            "summary": self.report_as_title(copy_report),
            "description": desc,
            "issuetype": {"name": self.issuetype},
        }
        try:
            issue = self.jira.create_issue(**issue_data)
        except:  #  if jira need direct issuetype name
            issue_data["issuetype"] = self.issuetype
            issue = self.jira.create_issue(**issue_data)
        for attachment in report.attachments:
            attachment.get_data()
            attach = self.jira.add_attachment(
                issue=issue,
                filename=attachment.original_name,
                attachment=attachment.data,
            )
            replacer = (
                "/".join(attach.content.split("/")[:-1])
                + "/"
                + attach.filename.replace(" ", "%20")
            ).replace("\n", "")
            copy_report.description_html = copy_report.description_html.replace(
                attachment.url, replacer
            )
        desc, _ = self.report_as_description(copy_report, tags=tags)
        issue.update(description=desc.replace("!!", "! !"))
        return issue

    def get_url(self, issue):
        return issue.permalink()

    def get_id(self, issue):
        return issue.key

    def report_as_description(
        self, report, template=None, additional_keys=[], tags=[]
    ):
        report.description_html = self.replace_external_link(report)
        report.description_html = self._img_to_jira_tag(
            report.description_html
        )

        report.description_html, tmp_tags = self._code_to_jira_tag(
            report.description_html
        )
        if not tags:
            tags = tmp_tags
        description = super().report_as_description(
            report,
            template=template,
            additional_keys=additional_keys,
            html_parser=html2jira,
        )

        for (_, f_name, _, _) in Formatter().parse(description):
            if f_name in tags:
                description = description.replace(
                    "{%s}" % f_name, tags[f_name]
                )
        return description, tags

    def _code_to_jira_tag(self, html):
        soup = BeautifulSoup(html, features="lxml")
        n_html = str(soup)
        code_format = "{{code{title}}}\n{content}\n{{code}}"
        tags = {}
        for idx, code in enumerate(soup.findAll("code")):
            tag = self.tag_format.format(idx=str(idx))
            title = code.attrs.get("class", "")
            if type(title) == list:
                title = title[0] if len(title) > 0 else ""
            title = title.replace("language-", "")
            if title.lower() in ["burp", "http", "shell", "graphql"]:
                title = ""
            tags[tag] = code_format.format(
                title=":{title}".format(title=title) if title else "",
                content="".join([str(i) for i in code.contents]),
            )
            n_html = n_html.replace(str(code), "{%(tag)s}" % ({"tag": tag}))
        return unescape_text(n_html), tags

    def _img_to_jira_tag(self, html):
        """
        Replace "img" balisis in html to "a" balisis.
        """
        soup = BeautifulSoup(html, features="lxml")
        n_html = str(soup)
        for img in soup.findAll("img"):
            alt = img.attrs.get("alt", "")
            src = img.attrs.get("src", "")
            a = f"!{alt}|{src}!"
            n_html = n_html.replace(str(img), a)
        return unescape_text(n_html)


class YWHJiraConfig(BugTrackerConfig):

    """
    BugTrackerConfig Class associated to jira.

    :attr str bugtracker_type: bugtracker identifier
    :attr class client: Client class
    :attr list mandatory_keys: keys needed in configuration file part
    :attr list secret_keys: keys need interaction in interactive mode
    :attr dict optional_keys: keys with default values
    :attr dict _description: descriptor for each specified key
    """

    bugtracker_type = "jira"
    client = YWHJira

    mandatory_keys = ["url", "login", "project"]
    secret_keys = ["password"]
    optional_keys = dict(issuetype="Task", verify=True)
    _description = dict(project="Jira slug")

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def _set_bugtracker(self):
        self._get_bugtracker(
            self._url,
            self._login,
            self._password,
            self._project,
            issuetype=self._issuetype,
            verify=self._verify,
        )
