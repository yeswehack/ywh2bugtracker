import unittest.mock
from json import JSONDecodeError
from typing import Any, Dict, List, Optional, Type, Union, cast

from yeswehack.api import (
    Log as YesWeHackRawApiLog, Report as YesWeHackRawApiReport, YesWeHack, YesWeHack as YesWeHackRawApiClient
)
from yeswehack.exceptions import APIError as YesWeHackRawAPiError

from ywh2bt.core.api.models.report import Author, BugType, Cvss, Report, ReportProgram
from ywh2bt.core.api.yeswehack import YesWeHackApiClient, YesWeHackApiClientError
from ywh2bt.core.configuration.yeswehack import YesWeHackConfiguration


class AbstractRawApiClient(YesWeHack):
    def __init__(self, **kwargs: Any) -> None:
        pass

    def login(
        self,
        totp_code: Optional[str] = None,
    ) -> bool:
        raise NotImplemented()

    def get_reports(
        self,
        program: str,
        filters: Optional[Dict[str, Any]] = None,
        lazy: bool = False,
    ) -> List[YesWeHackRawApiReport]:
        raise NotImplemented()

    def get_report(
        self,
        report: Union[str, int],
        lazy: bool = False,
    ) -> YesWeHackRawApiReport:
        raise NotImplemented()

    def post_comment(
        self,
        report_id: Union[str, int],
        comment: str,
        private: bool = False,
    ) -> YesWeHackRawApiLog:
        raise NotImplemented()


class TestYesWeHackApiClient(unittest.TestCase):

    def test_get_program_reports_login_error(self) -> None:
        class RawApiClient(AbstractRawApiClient):
            def login(self, totp_code: Optional[str] = None) -> bool:
                raise YesWeHackRawAPiError('Cannot login.')

            def get_reports(self, **kwargs: Any) -> List[YesWeHackRawApiReport]:
                return []

        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
            raw_client_class=cast(Type[YesWeHackRawApiClient], RawApiClient),
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.get_program_reports(
                slug='my-program',
            )

    def test_get_program_reports(self) -> None:
        class RawApiClient(AbstractRawApiClient):
            def login(self, totp_code: Optional[str] = None) -> bool:
                return True

            def get_reports(self, **kwargs: Any) -> List[YesWeHackRawApiReport]:
                return [
                    YesWeHackRawApiReport(
                        ywh_api=None,
                        lazy=True,
                        id=123,
                    )
                ]

            def get_report(
                self,
                report: Union[str, int],
                lazy: bool = False,
            ) -> YesWeHackRawApiReport:
                return YesWeHackRawApiReport(
                    ywh_api=None,
                    lazy=True,
                    id=123,
                    title='A bug report',
                )

        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
            raw_client_class=cast(Type[YesWeHackRawApiClient], RawApiClient),
        )
        reports = client.get_program_reports(
            slug='my-program',
        )
        self.assertEqual(1, len(reports))
        self.assertEqual('A bug report', reports[0].title)

    def test_post_report_tracker_update_error(self) -> None:
        class RawApiClient(AbstractRawApiClient):
            def login(self, totp_code: Optional[str] = None) -> bool:
                return True

        def raw_post_tracker_update(**kwargs: Any) -> None:
            raise YesWeHackRawAPiError()

        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
            raw_client_class=cast(Type[YesWeHackRawApiClient], RawApiClient),
        )
        raw_report = YesWeHackRawApiReport(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        object.__setattr__(raw_report, 'post_tracker_update', raw_post_tracker_update)
        report = Report(
            raw_report=raw_report,
            report_id='123',
            title='A bug report',
            local_id='YWH-123',
            bug_type=BugType(
                name='bug-type',
                link='http://bug.example.com/type',
                remediation_link='http://bug.example.com/type/remediation',
            ),
            scope='',
            cvss=Cvss(
                criticity='critical',
                score=9.0,
                vector='vector',
            ),
            end_point='/',
            vulnerable_part='post',
            part_name='param',
            payload_sample='abcde',
            technical_information='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
            tracking_status='AFI',
            program=ReportProgram(
                title='My program',
                slug='my-program',
            ),
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.post_report_tracker_update(
                report=report,
                tracker_name='tracker',
                issue_id='foo',
                issue_url='https://tracker.example.com/issues/foo',
                token='abcde',
                comment='Tracker synchronized.',
            )

    def test_put_report_tracking_status_raise_error(self) -> None:
        class RawApiClient(AbstractRawApiClient):
            def login(self, totp_code: Optional[str] = None) -> bool:
                return True

        def raw_put_tracking_status(**kwargs: Any) -> None:
            raise YesWeHackRawAPiError()

        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
            raw_client_class=cast(Type[YesWeHackRawApiClient], RawApiClient),
        )
        raw_report = YesWeHackRawApiReport(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        object.__setattr__(raw_report, 'put_tracking_status', raw_put_tracking_status)
        report = Report(
            raw_report=raw_report,
            report_id='123',
            title='A bug report',
            local_id='YWH-123',
            bug_type=BugType(
                name='bug-type',
                link='http://bug.example.com/type',
                remediation_link='http://bug.example.com/type/remediation',
            ),
            scope='',
            cvss=Cvss(
                criticity='critical',
                score=9.0,
                vector='vector',
            ),
            end_point='/',
            vulnerable_part='post',
            part_name='param',
            payload_sample='abcde',
            technical_information='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
            tracking_status='AFI',
            program=ReportProgram(
                title='My program',
                slug='my-program',
            ),
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.put_report_tracking_status(
                report=report,
                tracker_name='tracker',
                issue_id='foo',
                issue_url='https://tracker.example.com/issues/foo',
                status='T',
                comment='Tracker synchronized.',
            )

    def test_put_report_tracking_status_json_decode_error(self) -> None:
        class RawApiClient(AbstractRawApiClient):
            def login(self, totp_code: Optional[str] = None) -> bool:
                return True

        class Response:
            def json(self) -> None:
                raise JSONDecodeError(
                    'Error',
                    '{}',
                    0,
                )

        def raw_put_tracking_status(**kwargs: Any) -> Response:
            return Response()

        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
            raw_client_class=cast(Type[YesWeHackRawApiClient], RawApiClient),
        )
        raw_report = YesWeHackRawApiReport(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        object.__setattr__(raw_report, 'put_tracking_status', raw_put_tracking_status)
        report = Report(
            raw_report=raw_report,
            report_id='123',
            title='A bug report',
            local_id='YWH-123',
            bug_type=BugType(
                name='bug-type',
                link='http://bug.example.com/type',
                remediation_link='http://bug.example.com/type/remediation',
            ),
            scope='',
            cvss=Cvss(
                criticity='critical',
                score=9.0,
                vector='vector',
            ),
            end_point='/',
            vulnerable_part='post',
            part_name='param',
            payload_sample='abcde',
            technical_information='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
            tracking_status='AFI',
            program=ReportProgram(
                title='My program',
                slug='my-program',
            ),
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.put_report_tracking_status(
                report=report,
                tracker_name='tracker',
                issue_id='foo',
                issue_url='https://tracker.example.com/issues/foo',
                status='T',
                comment='Tracker synchronized.',
            )

    def test_put_report_tracking_status_json_not_dict_error(self) -> None:
        class RawApiClient(AbstractRawApiClient):
            def login(self, totp_code: Optional[str] = None) -> bool:
                return True

        class Response:
            def json(self) -> str:
                return 'I am an API response'

        def raw_put_tracking_status(**kwargs: Any) -> Response:
            return Response()

        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
            raw_client_class=cast(Type[YesWeHackRawApiClient], RawApiClient),
        )
        raw_report = YesWeHackRawApiReport(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        object.__setattr__(raw_report, 'put_tracking_status', raw_put_tracking_status)
        report = Report(
            raw_report=raw_report,
            report_id='123',
            title='A bug report',
            local_id='YWH-123',
            bug_type=BugType(
                name='bug-type',
                link='http://bug.example.com/type',
                remediation_link='http://bug.example.com/type/remediation',
            ),
            scope='',
            cvss=Cvss(
                criticity='critical',
                score=9.0,
                vector='vector',
            ),
            end_point='/',
            vulnerable_part='post',
            part_name='param',
            payload_sample='abcde',
            technical_information='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
            tracking_status='AFI',
            program=ReportProgram(
                title='My program',
                slug='my-program',
            ),
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.put_report_tracking_status(
                report=report,
                tracker_name='tracker',
                issue_id='foo',
                issue_url='https://tracker.example.com/issues/foo',
                status='T',
                comment='Tracker synchronized.',
            )

    def test_put_report_tracking_status_response_error(self) -> None:
        class RawApiClient(AbstractRawApiClient):
            def login(self, totp_code: Optional[str] = None) -> bool:
                return True

        class Response:
            def json(self) -> Dict[str, Any]:
                return {
                    'errors': [
                        'Some error',
                    ],
                }

        def raw_put_tracking_status(**kwargs: Any) -> Response:
            return Response()

        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
            raw_client_class=cast(Type[YesWeHackRawApiClient], RawApiClient),
        )
        raw_report = YesWeHackRawApiReport(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        object.__setattr__(raw_report, 'put_tracking_status', raw_put_tracking_status)
        report = Report(
            raw_report=raw_report,
            report_id='123',
            title='A bug report',
            local_id='YWH-123',
            bug_type=BugType(
                name='bug-type',
                link='http://bug.example.com/type',
                remediation_link='http://bug.example.com/type/remediation',
            ),
            scope='',
            cvss=Cvss(
                criticity='critical',
                score=9.0,
                vector='vector',
            ),
            end_point='/',
            vulnerable_part='post',
            part_name='param',
            payload_sample='abcde',
            technical_information='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
            tracking_status='AFI',
            program=ReportProgram(
                title='My program',
                slug='my-program',
            ),
        )
        with self.assertRaises(YesWeHackApiClientError):
            client.put_report_tracking_status(
                report=report,
                tracker_name='tracker',
                issue_id='foo',
                issue_url='https://tracker.example.com/issues/foo',
                status='T',
                comment='Tracker synchronized.',
            )

    def test_put_report_tracking_status(self) -> None:
        class RawApiClient(AbstractRawApiClient):
            def login(self, totp_code: Optional[str] = None) -> bool:
                return True

        class Response:
            def json(self) -> Dict[str, Any]:
                return {
                    'status': 'success',
                }

        def raw_put_tracking_status(**kwargs: Any) -> Response:
            return Response()

        client = YesWeHackApiClient(
            configuration=YesWeHackConfiguration(),
            raw_client_class=cast(Type[YesWeHackRawApiClient], RawApiClient),
        )
        raw_report = YesWeHackRawApiReport(
            ywh_api=None,
            lazy=True,
            id=123,
        )
        object.__setattr__(raw_report, 'put_tracking_status', raw_put_tracking_status)
        report = Report(
            raw_report=raw_report,
            report_id='123',
            title='A bug report',
            local_id='YWH-123',
            bug_type=BugType(
                name='bug-type',
                link='http://bug.example.com/type',
                remediation_link='http://bug.example.com/type/remediation',
            ),
            scope='',
            cvss=Cvss(
                criticity='critical',
                score=9.0,
                vector='vector',
            ),
            end_point='/',
            vulnerable_part='post',
            part_name='param',
            payload_sample='abcde',
            technical_information='',
            description_html='This is a bug',
            attachments=[],
            hunter=Author(
                username='a-hunter',
            ),
            logs=[],
            tracking_status='AFI',
            program=ReportProgram(
                title='My program',
                slug='my-program',
            ),
        )
        client.put_report_tracking_status(
            report=report,
            tracker_name='tracker',
            issue_id='foo',
            issue_url='https://tracker.example.com/issues/foo',
            status='T',
            comment='Tracker synchronized.',
        )
