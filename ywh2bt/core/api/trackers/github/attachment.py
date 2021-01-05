"""Models and functions used for GitHub attachments upload."""
from json.decoder import JSONDecodeError
from typing import Any, Dict, Optional, cast
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup, Tag  # type: ignore
from github.Issue import Issue
from requests_toolbelt import MultipartEncoder  # type: ignore

from ywh2bt.core.api.models.report import Attachment
from ywh2bt.core.configuration.trackers.github import GitHubConfiguration


class GitHubAttachmentUploader:
    """An attachment uploader."""

    _configuration: GitHubConfiguration
    _github_domain: str

    _login_form_field_names = (
        'authenticity_token',
        'commit',
        'timestamp_secret',
        'webauthn-support',
        'webauthn-iuvpaa-support',
        'required_field_59db',
        'utf8',
    )

    def __init__(
        self,
        configuration: GitHubConfiguration,
    ):
        """
        Initialize self.

        Args:
            configuration: a GitHub configuration
        """
        self._configuration = configuration
        domain = 'github.com'
        if configuration.url != 'https://api.github.com':
            domain = urlsplit(cast(str, configuration.url)).netloc
        self._github_domain = domain

    def upload_attachment(
        self,
        issue: Issue,
        attachment: Attachment,
    ) -> Optional[str]:
        """
        Upload an attachment to an issue.

        Args:
            issue: an issue
            attachment: an attachment

        Returns:
            the url or the uploaded attachment
        """
        session = self._login()
        if not session:
            return None

        upload_policies_assets_authenticity_token = self._get_upload_policies_assets_authenticity_token(
            session=session,
            issue=issue,
        )
        if not upload_policies_assets_authenticity_token:
            return None

        policies_assets_response_data = self._upload_policies_assets(
            session=session,
            issue=issue,
            attachment=attachment,
            authenticity_token=upload_policies_assets_authenticity_token,
        )
        if not policies_assets_response_data:
            return None

        upload_response = self._upload(
            session=session,
            attachment=attachment,
            url=policies_assets_response_data['upload_url'],
            form=policies_assets_response_data['form'],
        )
        if not upload_response:
            return None

        url = self._upload_asset(
            session=session,
            issue=issue,
            url=policies_assets_response_data['asset_upload_url'],
            authenticity_token=policies_assets_response_data['asset_upload_authenticity_token'],
        )

        return cast(
            str,
            url or policies_assets_response_data['asset']['href'],
        )

    def _get_upload_policies_assets_authenticity_token(
        self,
        session: requests.Session,
        issue: Issue,
    ) -> Optional[str]:
        issue_response = self._github_request(
            session=session,
            method='GET',
            path=f'/{issue.repository.full_name}/issues/{issue.number}',
        )
        if not issue_response:
            return None

        return self._extract_upload_policies_asset_authenticity_token(
            html=issue_response.text,
        )

    def _extract_upload_policies_asset_authenticity_token(
        self,
        html: str,
    ) -> Optional[str]:
        file_attachment_tag = BeautifulSoup(
            html,
            features='lxml',
        ).find(
            'file-attachment',
        )

        if not file_attachment_tag:
            return None

        authenticity_token = file_attachment_tag.get('data-upload-policy-authenticity-token', None)
        if authenticity_token is None:
            csrf_policy_input = file_attachment_tag.find(
                'input', {
                    'class': 'js-data-upload-policy-url-csrf',
                },
            )
            if csrf_policy_input is not None:
                authenticity_token = csrf_policy_input.get('value', None)

        return cast(str, authenticity_token)

    def _upload_policies_assets(
        self,
        session: requests.Session,
        issue: Issue,
        attachment: Attachment,
        authenticity_token: str,
    ) -> Optional[Dict[str, Any]]:
        data = MultipartEncoder(
            fields={
                'name': attachment.original_name.split('/')[-1],
                'size': str(len(attachment.data)),
                'content_type': attachment.mime_type,
                'authenticity_token': authenticity_token,
                'repository_id': str(issue.repository.id),
            },
        )
        response = self._github_request(
            session=session,
            method='POST',
            path='/upload/policies/assets',
            data=data,
            headers={
                'Content-Type': data.content_type,
                'Content-Length': str(data.len),
            },
        )
        if not response or response.status_code != 201:
            return None
        response_data = response.json()
        if 'asset' not in response_data:
            return None
        return cast(Dict[str, Any], response_data)

    def _upload(
        self,
        session: requests.Session,
        attachment: Attachment,
        url: str,
        form: Dict[str, Any],
    ) -> bool:
        upload_data = MultipartEncoder(
            fields={
                **form,
                'file': (attachment.original_name.split('/')[-1], attachment.data, attachment.mime_type),
            },
        )
        upload_response = _url_request(
            session=session,
            method='POST',
            url=url,
            data=upload_data,
            headers={
                'Content-Type': upload_data.content_type,
                'Content-Length': str(upload_data.len),
            },
        )
        if not upload_response:  # noqa: WPS531
            return False
        return True

    def _upload_asset(
        self,
        session: requests.Session,
        issue: Issue,
        url: str,
        authenticity_token: str,
    ) -> Optional[str]:
        asset_upload_data = MultipartEncoder(
            fields={
                'authenticity_token': authenticity_token,
            },
        )
        repository_url = f'https://{self._github_domain}/{issue.repository.full_name}'
        asset_upload_response = self._github_request(
            session=session,
            method='PUT',
            path=url,
            data=asset_upload_data,
            headers={
                'Content-Type': asset_upload_data.content_type,
                'Content-Length': str(asset_upload_data.len),
                'Referer': f'{repository_url}/issues/{issue.number}',
                'Accept': 'application/json',
            },
        )
        if not asset_upload_response:
            return None
        try:
            asset_upload_response_data = asset_upload_response.json()
        except JSONDecodeError:
            return None
        return cast(Optional[str], asset_upload_response_data.get('href', None))

    def _login(self) -> Optional[requests.Session]:
        session = requests.Session()
        session.verify = self._configuration.verify
        login_page = self._github_request(
            session=session,
            method='GET',
            path='/login',
        )
        if not login_page:
            return None
        form = BeautifulSoup(login_page.text, features='lxml').find('form')
        fields = self._extract_login_fields(
            form=form,
        )
        session_response = self._github_request(
            session=session,
            method='POST',
            path='/session',
            data={
                **fields,
                'login': self._configuration.login,
                'password': self._configuration.password,
            },
        )
        if session_response and session_response.status_code == 200:
            return session
        return None

    def _extract_login_fields(
        self,
        form: Tag,
    ) -> Dict[str, Any]:
        fields: Dict[str, Any] = {}
        for field_name in self._login_form_field_names:
            value = form.find(
                'input', {
                    'name': field_name,
                },
            )
            if value:
                fields[field_name] = value['value']
        return fields

    def _github_request(
        self,
        session: requests.Session,
        method: str,
        path: str,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> Optional[requests.Response]:
        return _url_request(
            session=session,
            method=method,
            url=f'https://{self._github_domain}{path}',
            data=data,
            headers=headers,
        )


def _url_request(
    session: requests.Session,
    method: str,
    url: str,
    data: Optional[Any] = None,
    headers: Optional[Dict[str, Any]] = None,
) -> Optional[requests.Response]:
    try:
        return session.request(
            method=method,
            url=url,
            data=data,
            headers=headers,
        )
    except requests.RequestException:
        return None
