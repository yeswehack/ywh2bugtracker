# -*- encoding: utf-8 -*-
import io
import base64
import imghdr
import mimetypes
from abc import abstractmethod
import html2text

__all__ = ["BugTracker"]

"""
Define Abstract client class
"""

class BugTracker:

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
| {local_id} : {title} ||
| Bug Type | [{bug_type__name}]({bug_type__link}) &#8594; [Remediation]({bug_type__remediation_link}) |
| Scope | {scope} |
| Severity | {cvss__criticity}, score: {cvss__score:.1f}, vector: {cvss__vector}|
| Endpoint |{end_point}|
| Vulnerable part | {vulnerable_part} |
| Part Name | {part_name} |
| Payload | {payload_sample} |
| Technical Environment | {technical_information}|

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


    def report_as_title(self, report, template=None, additional_keys=[]):
        """
        Format template title with given information.

        :param yeswehack.api.Report report: Report representation
        :param str template: if not None, overwride default template.
        :param list additional_keys: keys corresponding to attribute of report object.

        to used subjobject, use '__' separator : cvss__score -> cvss.score
        """
        if template is None:
            template = self.issue_name_template
        return self.format_template(report, template, keys=additional_keys, fmt_keys={"local_id":report.local_id, "title": report.title})


    def report_as_descripton(self, report, template=None, additional_keys=[]):
        """
        Format template description with given information

        :param yeswehack.api.Report report: Report representation
        :param str template: if not None, overwride default template.
        :param list additional_keys: keys corresponding to attribute of report object.

        to used subjobject, use '__' separator : cvss__score -> cvss.score
        """
        if template is None:
            template = self.description_template
        keys = [
            "scope",
            "cvss__score",
            "cvss__criticity",
            "cvss__vector",
            "vulnerable_part",
            "bug_type__name",
            # "bug_type__description",
            "bug_type__link",
            "bug_type__remediation_link",
            "description_html",
            "end_point",
            "vulnerable_part",
            "part_name",
            "payload_sample",
            "technical_information",
            "local_id",
            "title"
        ]
        return self.format_template(report, template=template, keys=[*additional_keys,*keys])

    ############################################################
    ####################### Static methods #####################
    ############################################################
    @staticmethod
    def format_template(report, template, keys=[], fmt_keys={}):
        """
        Format given template with report information

        :param yeswehack.api.Report report: Report representation
        :param str template: template to use.
        :param list additional_keys: keys corresponding to attribute of report object.

        to used subjobject, use '__' separator : cvss__score -> cvss.score
        """

        for key in keys:
            obj = report
            for i in key.split('__'):
                obj = obj.__getattribute__(i)
            if 'html' in key:
                obj = html2text.html2text(obj)
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
