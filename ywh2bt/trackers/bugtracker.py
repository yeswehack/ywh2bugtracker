# -*- encoding: utf-8 -*-
import io
import base64
import imghdr
import mimetypes
from abc import abstractmethod


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
|  bug type  |    Description   |       Remediation         |
| ---------- | ---------------- | ------------------------- |
| {bug_type__category__name} | {bug_type__description}| [link]({bug_type__link})|

|    scope    |  vulnerable part  |  CVSS |
| ----------- | ----------------- | ----- |
| {scope} | {vulnerable_part} | {cvss__score} |

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
