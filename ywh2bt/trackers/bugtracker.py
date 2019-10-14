# -*- encoding: utf-8 -*-
import io
import base64
import imghdr
import mimetypes
from abc import abstractmethod

class BugTracker:

    issue_name_template = "{report_local_id} : {report_title}"
    ywh_comment_marker = (
        "Imported to the bugtracker : {url} on project : {project_id}."
    )
    ywh_comment_template = "Tracked to [{type} #{issue_id}]({bug_url})"
    description_template = """
|  bug type  |    Description   |       Remediation         |
| ---------- | ---------------- | ------------------------- |
| {bug_type} | {bug_description}| [link]({remediation_link})|

|    scope    |  vulnerable part  |  CVSS |
| ----------- | ----------------- | ----- |
| {end_point} | {vulnerable_part} | {cvss} |

{description}
"""

    def file_to_base64(self, img: bytes, content_type=None) -> str:
        """Transforme input image to base64 string."""
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

    @abstractmethod
    def configure(bugtracker):
        pass

    @abstractmethod
    def get_project(self):
        pass

    # @abstractmethod
    # def get_issue(self, report):
    #     pass

    @abstractmethod
    def post_issue(self, report):
        pass

    @abstractmethod
    def get_url(self, issue):
        pass

    @abstractmethod
    def get_id(self, issue):
        pass
