"""Models and functions used for YesWeHack platform data access."""
from json import JSONDecodeError
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlsplit

import requests
from yeswehack.api import (
    Report as YesWeHackRawApiReport,
    YesWeHack as YesWeHackRawApiClient,
)
from yeswehack.exceptions import APIError as YesWeHackRawAPiError

from ywh2bt.core.api.client import TestableApiClient
from ywh2bt.core.api.mapping import MappingContext, map_raw_report
from ywh2bt.core.api.models.report import Report
from ywh2bt.core.configuration.headers import Headers
from ywh2bt.core.configuration.yeswehack import OAuthSettings, YesWeHackConfiguration
from ywh2bt.core.exceptions import CoreException


class YesWeHackApiClientError(CoreException):
    """A YesWeHack API client error."""


class YesWeHackApiClient(TestableApiClient):
    """A YesWeHack API client."""

    _configuration: YesWeHackConfiguration
    _raw_client: YesWeHackRawApiClient
    _yeswehack_domain: str
    _logged_in: bool

    def __init__(
        self,
        configuration: YesWeHackConfiguration,
    ):
        """
        Initialize self.

        Args:
            configuration: a YesWeHack configuration
        """
        self._configuration = configuration
        self._raw_client = self._build_raw_client()
        self._logged_in = False
        self._yeswehack_domain = self._extract_yeswehack_domain(
            url=cast(str, self._configuration.api_url),
        )

    def test(
        self,
    ) -> None:
        """Test the client."""
        self._ensure_login()

    def _build_raw_client(
        self,
    ) -> YesWeHackRawApiClient:
        configuration = self._configuration
        oauth_settings = cast(Optional[OAuthSettings], configuration.oauth_args)
        oauth_mode = True if oauth_settings is not None and oauth_settings.export() else False  # noqa: WPS502
        has_headers = configuration.apps_headers is not None
        try:
            client = YesWeHackRawApiClient(
                username=configuration.login,
                password=configuration.password,
                api_url=self._normalize_api_url(
                    api_url=cast(str, configuration.api_url),
                ),
                oauth_mode=oauth_mode,
                oauth_args=oauth_settings.export() if oauth_mode and oauth_settings else {},
                apps_headers=cast(Headers, configuration.apps_headers).export() if has_headers else {},
                verify=configuration.verify,
                lazy=True,
            )
        except (YesWeHackRawAPiError, requests.RequestException) as e:
            raise YesWeHackApiClientError('Unable to initialize YesWeHack API client') from e
        return client

    def _normalize_api_url(
        self,
        api_url: str,
    ) -> str:
        return api_url[:-1] if api_url[-1] == '/' else api_url

    def _extract_yeswehack_domain(
        self,
        url: str,
    ) -> str:
        result = urlsplit(url)
        # only keep 'xxx.yyy.zzz' from 'www.xxx.yyy.zzz'
        _, domain = result.netloc.split('.', 1)
        return domain

    def _ensure_login(
        self,
    ) -> None:
        if not self._logged_in:
            try:
                success = self._raw_client.login()
            except (YesWeHackRawAPiError, requests.RequestException) as e:
                raise YesWeHackApiClientError('Unable to log in with YesWeHack API client') from e
            self._logged_in = success

    def get_program_reports(
        self,
        slug: str,
        filters: Optional[Dict[str, Any]],
    ) -> List[Report]:
        """
        Get reports for the program.

        Args:
            slug: a program slug
            filters: a report filter

        Returns:
            the list of reports

        Raises:
            YesWeHackApiClientError: if an error occurred when getting the reports
        """
        self._ensure_login()
        try:
            raw_reports = self._raw_client.get_reports(
                program=slug,
                filters=filters or {},
                lazy=True,
            )
        except (YesWeHackRawAPiError, YesWeHackApiClientError, requests.RequestException) as e:
            raise YesWeHackApiClientError(f'Unable to get reports for program {slug}') from e
        return self._get_detailed_reports(
            raw_reports=raw_reports,
        )

    def _get_detailed_reports(
        self,
        raw_reports: List[YesWeHackRawApiReport],
    ) -> List[Report]:
        return [
            self._get_detailed_report(
                report_id=raw_report.id,
            )
            for raw_report in raw_reports
        ]

    def _get_detailed_report(
        self,
        report_id: int,
    ) -> Report:
        try:
            raw_report = self._raw_client.get_report(
                report=report_id,
            )
        except (YesWeHackRawAPiError, requests.RequestException, TypeError) as e:
            raise YesWeHackApiClientError(f'Unable to get report #{report_id} details') from e
        return self._map_raw_report(
            raw_report=raw_report,
        )

    def _get_mapping_context(
        self,
    ) -> MappingContext:
        return MappingContext(
            yeswehack_domain=self._yeswehack_domain,
        )

    def _map_raw_report(
        self,
        raw_report: YesWeHackRawApiReport,
    ) -> Report:
        try:
            return map_raw_report(
                context=self._get_mapping_context(),
                raw_report=raw_report,
            )
        except TypeError as e:
            raise YesWeHackApiClientError(f'Unable to map report #{raw_report.id}') from e

    def put_report_tracking_status(
        self,
        report: Report,
        status: str,
        tracker_name: str,
        issue_id: str,
        issue_url: str,
        comment: str,
    ) -> None:
        """
        Update a report tracking status with information about a tracked issue.

        Args:
            report: a report
            status: a status (T, AFI, ...)
            tracker_name: a tracker name
            issue_id: an id of an issue from a tracker
            issue_url: an URL of an issue from a tracker
            comment: a comment

        Raises:
            YesWeHackApiClientError: if an error occurred when updating the status
        """
        self._ensure_login()
        try:
            response: requests.Response = report.raw_report.put_tracking_status(
                tracking_status=status,
                tracker_name=tracker_name,
                tracker_id=issue_id,
                tracker_url=issue_url,
                message=comment,
            )
        except (YesWeHackRawAPiError, requests.RequestException) as api_error:
            raise YesWeHackApiClientError(f'Unable to update report #{report.report_id} tracking status') from api_error
        try:
            data = response.json()
        except JSONDecodeError as decode_error:
            raise YesWeHackApiClientError(
                f'Unable to parse response after updating report #{report.report_id} tracking status',
            ) from decode_error
        if not isinstance(data, dict):
            raise YesWeHackApiClientError(
                (
                    f'Expecting {dict} from response to report #{report.report_id} tracking status update ; '
                    + f'got {type(data)}',
                ),
            )
        if 'errors' in data:
            comment = data['message'] if 'message' in data else '[no error message]'
            raise YesWeHackApiClientError(
                f'Unable to update report #{report.report_id} tracking status: {comment}',
            )

    def post_report_tracker_update(
        self,
        report: Report,
        tracker_name: str,
        issue_id: str,
        issue_url: str,
        token: str,
        comment: str,
    ) -> None:
        """
        Send a report tracker update with information about a tracked issue.

        Args:
            report: a report
            tracker_name: a tracker name
            issue_id: an id of an issue from a tracker
            issue_url: an URL of an issue from a tracker
            token: a token containing the state of the issue
            comment: a comment

        Raises:
            YesWeHackApiClientError: if an error occurred when sending the update
        """
        self._ensure_login()
        try:
            report.raw_report.post_tracker_update(
                tracker_name=tracker_name,
                tracker_id=issue_id,
                tracker_url=issue_url,
                token=token,
                message=comment,
            )
        except (YesWeHackRawAPiError, requests.RequestException) as api_error:
            raise YesWeHackApiClientError(f'Unable to send report #{report.report_id} tracker update') from api_error
