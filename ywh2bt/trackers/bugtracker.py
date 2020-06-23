# -*- encoding: utf-8 -*-
import io
import base64
import imghdr
import mimetypes
from abc import abstractmethod
import html2text
import urllib.parse as uparse
import re
from bs4 import BeautifulSoup

__all__ = ["BugTracker"]

"""
Define Abstract client class
"""


def html_handler(html):
    """
    Process html to markdown
    """
    html_parser = html2text.HTML2Text()
    html_parser.body_width = 0
    html_parser.mark_code = True
    langs = []
    soup = BeautifulSoup(html, "lxml")
    for pre in soup.findAll("pre"):
        for code in pre:
            langs.append(
                code.attrs.get("class", [""])[0].replace("language-", "")
            )
    n_html = html_parser.handle(html)
    idx = 0
    for i in range(len(langs)):
        idx = n_html[idx:].index("[code]") + 6 + idx
        n_html = n_html[:idx] + langs[i] + n_html[idx:]
    h = n_html.replace("[code]", "```").replace("[/code]", "```")
    return h


class BugTracker(object):

    """
    Abstract client Wrapper class for all BugTrackers Client.

    :attr str issue_name_template: template for the title part.
    :attr str ywh_comment_marker: template for comment marker part.
    :attr str ywh_comment_marker: template for comment part.
    :attr str description_template: template for description part.
    """

    issue_name_template = "{local_id} : {title}"
    ywh_comment_marker = (
        "Imported to the bugtracker : {url} on project : {project_id}."
    )
    ywh_comment_template = "Tracked to [{type} #{issue_id}]({bug_url})"

    description_template = """
| Title | {local_id} : {title}|
|-------|---------------------|
| Priority | {priority__name} |
| Bug Type | [{bug_type__name}]({bug_type__link}) &#8594; [Remediation]({bug_type__remediation_link}) |
| Scope | {scope} |
| Severity | {cvss__criticity}, score: {cvss__score:.1f}, vector: {cvss__vector} |
| Endpoint | {end_point} |
| Vulnerable part | {vulnerable_part} |
| Part Name | {part_name} |
| Payload | {payload_sample} |
| Technical Environment | {technical_information} |

{description_html}
    """

    ############################################################
    #################### Instance methods ######################
    ############################################################
    def file_to_base64(self, img, content_type):
        """
        Transforme input image to base64 string.

        :param bytes img: img to change to base64?
        :param content_type: content_type header
        """
        f = io.BytesIO(img)
        mime = imghdr.what(f)
        if mime is None and (
            not content_type
            or "image/" not in content_type
            or "svg" in content_type
        ):
            raise ValueError("Image type not supported")
        mime = mimetypes.types_map["." + mime] if mime else content_type
        image = (
            "data:"
            + mime
            + ";base64,"
            + str(base64.b64encode(img).decode("utf-8"))
        )
        return image

    def replace_external_link(self, report):
        description = report.description_html
        base_string = "https://{ywhdomain}/redirect?url=".format(
            ywhdomain=self._ywh_domain
        )

        pattern = re.compile(
            '"{base_string}([^ "]*)"'.format(
                base_string=base_string.replace("/", "\/")
                .replace("?", "\?")
                .replace(".", "\.")
            )
        )
        redirect_urls = pattern.findall(report.description_html)
        for url in redirect_urls:
            base_url, params = uparse.splitquery(uparse.unquote(uparse.unquote(url)))
            new_params = "&".join(
                [
                    p
                    for p in params.split("&")
                    if not p.startswith("expires")
                    and not p.startswith("token")
                ]
            ) if params else ''
            description = description.replace(
                "{base_string}{url}".format(base_string=base_string, url=url),
                "{base_url}{params}".format(
                    base_url=base_url
                    + ("/" if not base_url.endswith("/") else ""),
                    params=("?" + new_params) if new_params else "",
                ),
            )
        return description

    def report_as_title(
        self,
        report,
        template=None,
        additional_keys=[],
        html_parser=html2text.html2text,
    ):
        """
        Format template title with given information.

        :param yeswehack.api.Report report: Report representation
        :param str template: if not None, overwride default template.
        :param list additional_keys: keys corresponding to attribute of report object.

        to used subjobject, use '__' separator : cvss__score -> cvss.score
        """
        if template is None:
            template = self.issue_name_template
        return self.format_template(
            report,
            template,
            keys=additional_keys,
            fmt_keys={"local_id": report.local_id, "title": report.title},
            html_parser=html_parser,
        )

    def report_as_description(
        self,
        report,
        template=None,
        additional_keys=[],
        html_parser=html_handler,
    ):
        """
        Format template description with given information

        :param yeswehack.api.Report report: Report representation
        :param str template: if not None, overwride default template.
        :param list additional_keys: keys corresponding to attribute of report object.

        to used subjobject, use '__' separator : cvss__score -> cvss.score
        """
        report.description_html = self.replace_external_link(report)
        if template is None:
            template = self.description_template
        keys = [
            "scope",
            "cvss__score",
            "priority__name",
            "cvss__criticity",
            "cvss__vector",
            "vulnerable_part",
            "bug_type__name",
            "bug_type__link",
            "bug_type__remediation_link",
            "description_html",
            "end_point",
            "vulnerable_part",
            "part_name",
            "payload_sample",
            "technical_information",
            "local_id",
            "title",
        ]
        return self.format_template(
            report,
            template=template,
            keys=[*additional_keys, *keys],
            html_parser=html_parser,
        )

    def set_yeswehack_domain(self, ywh_domain):
        self._ywh_domain = ywh_domain

    ############################################################
    ####################### Static methods #####################
    ############################################################
    @staticmethod
    def format_template(
        report, template, keys=[], fmt_keys={}, html_parser=html_handler
    ):
        """
        Format given template with report information

        :param yeswehack.api.Report report: Report representation
        :param str template: template to use.
        :param list additional_keys: keys corresponding to attribute of report object.

        to used subjobject, use '__' separator : cvss__score -> cvss.score
        """

        for key in keys:
            obj = report
            for i in key.split("__"):
                if obj:
                    obj = getattr(obj, i, None)
                else:
                    break
            if "html" in key:
                obj = html_parser(obj)
            fmt_keys[key] = obj
        return template.format(**fmt_keys)

    ############################################################
    ###################### Abstract methods ####################
    ############################################################
    @abstractmethod
    def configure(bugtracker):
        pass

    @abstractmethod
    def get_project(self):
        pass

    @abstractmethod
    def post_issue(self, report):
        pass

    @abstractmethod
    def get_url(self, issue):
        pass

    @abstractmethod
    def get_id(self, issue):
        pass
