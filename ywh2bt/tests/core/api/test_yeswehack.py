from json import JSONDecodeError
from unittest import TestCase
from unittest.mock import (
    MagicMock,
    create_autospec,
    patch,
)

import requests
from yeswehack.api import Report as YesWeHackRawApiReport
from yeswehack.exceptions import APIError as YesWeHackRawAPiError

from ywh2bt.core.api.models.report import (
    Author,
    BugType,
    Cvss,
    Report,
    ReportProgram,
)
from ywh2bt.core.api.yeswehack import (
    YesWeHackApiClient,
    YesWeHackApiClientError,
)
from ywh2bt.core.configuration.yeswehack import YesWeHackConfiguration


class TestYesWeHackApiClient(TestCase):
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_get_program_reports_login_error(
        self,
        YesWeHackRawApiClientMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.side_effect = YesWeHackRawAPiError("Cannot login.")
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.get_program_reports(
                slug="my-program",
            )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_get_program_reports(
        self,
        YesWeHackRawApiClientMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        YesWeHackRawApiClientMock.return_value.get_reports.return_value = [
            YesWeHackRawApiReport(
                ywh_api=None,
                lazy=True,
                id=123,
            )
        ]
        YesWeHackRawApiClientMock.return_value.get_report.return_value = YesWeHackRawApiReport(
            ywh_api=None,
            lazy=True,
            id=123,
            title="A bug report",
        )
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        reports = client.get_program_reports(
            slug="my-program",
        )
        self.assertEqual(1, len(reports))
        self.assertEqual("A bug report", reports[0].title)

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_post_report_tracker_update_raise_error(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        YesWeHackRawApiReportMock.return_value.post_tracker_update.side_effect = YesWeHackRawAPiError()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.post_report_tracker_update(
                report=report,
                tracker_name="tracker",
                issue_id="foo",
                issue_url="https://tracker.example.com/issues/foo",
                token="abcde",
                comment="Tracker synchronized.",
            )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_post_report_tracker_update_json_decode_error(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        RequestsResponseMock = create_autospec(requests.models.Response)
        RequestsResponseMock.return_value.json.side_effect = JSONDecodeError(
            "Error",
            "{}",
            0,
        )
        YesWeHackRawApiReportMock.return_value.post_tracker_update.return_value = RequestsResponseMock()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.post_report_tracker_update(
                report=report,
                tracker_name="tracker",
                issue_id="foo",
                issue_url="https://tracker.example.com/issues/foo",
                token="abcde",
                comment="Tracker synchronized.",
            )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_post_report_tracker_update_json_not_dict_error(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        RequestsResponseMock = create_autospec(requests.models.Response)
        RequestsResponseMock.return_value.json.return_value = "I am an API response"
        YesWeHackRawApiReportMock.return_value.post_tracker_update.return_value = RequestsResponseMock()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.post_report_tracker_update(
                report=report,
                tracker_name="tracker",
                issue_id="foo",
                issue_url="https://tracker.example.com/issues/foo",
                token="abcde",
                comment="Tracker synchronized.",
            )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_post_report_tracker_update_response_error(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        RequestsResponseMock = create_autospec(requests.models.Response)
        RequestsResponseMock.return_value.json.return_value = {
            "errors": [
                "Some error",
            ],
        }
        YesWeHackRawApiReportMock.return_value.post_tracker_update.return_value = RequestsResponseMock()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.post_report_tracker_update(
                report=report,
                tracker_name="tracker",
                issue_id="foo",
                issue_url="https://tracker.example.com/issues/foo",
                token="abcde",
                comment="Tracker synchronized.",
            )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_post_report_tracker_update(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        RequestsResponseMock = create_autospec(requests.models.Response)
        RequestsResponseMock.return_value.json.return_value = {
            "status": "success",
        }
        YesWeHackRawApiReportMock.return_value.post_tracker_update.return_value = RequestsResponseMock()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        client.post_report_tracker_update(
            report=report,
            tracker_name="tracker",
            issue_id="foo",
            issue_url="https://tracker.example.com/issues/foo",
            token="abcde",
            comment="Tracker synchronized.",
        )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_put_report_tracking_status_raise_error(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        YesWeHackRawApiReportMock.return_value.put_tracking_status.side_effect = YesWeHackRawAPiError()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.put_report_tracking_status(
                report=report,
                tracker_name="tracker",
                issue_id="foo",
                issue_url="https://tracker.example.com/issues/foo",
                status="T",
                comment="Tracker synchronized.",
            )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_put_report_tracking_status_json_decode_error(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        RequestsResponseMock = create_autospec(requests.models.Response)
        RequestsResponseMock.return_value.json.side_effect = JSONDecodeError(
            "Error",
            "{}",
            0,
        )
        YesWeHackRawApiReportMock.return_value.put_tracking_status.return_value = RequestsResponseMock()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.put_report_tracking_status(
                report=report,
                tracker_name="tracker",
                issue_id="foo",
                issue_url="https://tracker.example.com/issues/foo",
                status="T",
                comment="Tracker synchronized.",
            )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_put_report_tracking_status_json_not_dict_error(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        RequestsResponseMock = create_autospec(requests.models.Response)
        RequestsResponseMock.return_value.json.return_value = "I am an API response"
        YesWeHackRawApiReportMock.return_value.put_tracking_status.return_value = RequestsResponseMock()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.put_report_tracking_status(
                report=report,
                tracker_name="tracker",
                issue_id="foo",
                issue_url="https://tracker.example.com/issues/foo",
                status="T",
                comment="Tracker synchronized.",
            )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_put_report_tracking_status_response_error(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        RequestsResponseMock = create_autospec(requests.models.Response)
        RequestsResponseMock.return_value.json.return_value = {
            "errors": [
                "Some error",
            ],
        }
        YesWeHackRawApiReportMock.return_value.put_tracking_status.return_value = RequestsResponseMock()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.put_report_tracking_status(
                report=report,
                tracker_name="tracker",
                issue_id="foo",
                issue_url="https://tracker.example.com/issues/foo",
                status="T",
                comment="Tracker synchronized.",
            )

    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiReport")
    @patch("ywh2bt.core.api.yeswehack.YesWeHackRawApiClient")
    def test_put_report_tracking_status(
        self,
        YesWeHackRawApiClientMock: MagicMock,
        YesWeHackRawApiReportMock: MagicMock,
    ) -> None:
        YesWeHackRawApiClientMock.return_value.login.return_value = True
        RequestsResponseMock = create_autospec(requests.models.Response)
        RequestsResponseMock.return_value.json.return_value = {
            "status": "success",
        }
        YesWeHackRawApiReportMock.return_value.put_tracking_status.return_value = RequestsResponseMock()
        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
        )
        raw_report = YesWeHackRawApiReportMock(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        report = Report(
            raw_report=raw_report,
            report_id="123",
            title="A bug report",
            local_id="YWH-123",
            bug_type=BugType(
                name="bug-type",
                link="http://bug.example.com/type",
                remediation_link="http://bug.example.com/type/remediation",
            ),
            scope="",
            cvss=Cvss(
                criticity="critical",
                score=9.0,
                vector="vector",
            ),
            end_point="/",
            vulnerable_part="post",
            part_name="param",
            payload_sample="abcde",
            technical_environment="",
            description_html="This is a bug",
            attachments=[],
            hunter=Author(
                username="a-hunter",
            ),
            logs=[],
            status="accepted",
            tracking_status="AFI",
            program=ReportProgram(
                title="My program",
                slug="my-program",
            ),
            ask_for_fix_verification_status="UNKNOWN",
        )
        client.put_report_tracking_status(
            report=report,
            tracker_name="tracker",
            issue_id="foo",
            issue_url="https://tracker.example.com/issues/foo",
            status="T",
            comment="Tracker synchronized.",
        )
