"""Models and functions used for manipulating html data."""
import re
from copy import deepcopy
from html import (
    escape as html_escape,
    unescape as html_unescape,
)
from typing import (
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    cast,
)
from urllib.parse import (
    parse_qs,
    unquote,
    urlsplit,
)

import html2text
from bs4 import BeautifulSoup  # type: ignore

from ywh2bt.core.api.models.report import Attachment


def ywh_html_to_markdown(
    html: str,
) -> str:
    """
    Convert html emanating from YWH to markdown.

    Args:
        html: an html

    Returns:
        a markdown
    """
    markdown = html_to_markdown(html)
    offset = 0
    languages = _extract_language_codes(
        html=html,
    )
    for language in languages:
        offset = markdown[offset:].index('[code]') + 6 + offset
        markdown = markdown[:offset] + language + markdown[offset:]
    return markdown.replace(
        '[code]',
        '```',
    ).replace(
        '[/code]',
        '```',
    )


def _extract_language_codes(
    html: str,
) -> Iterator[str]:
    soup = BeautifulSoup(html, 'lxml')
    for pre in soup.findAll('pre'):
        for code in pre:
            class_attribute = code.attrs.get('class', [''])[0]
            yield class_attribute.replace('language-', '')


def html_to_markdown(
    html: str,
) -> str:
    """
    Convert html to markdown.

    Args:
        html: an html

    Returns:
        a markdown
    """
    html_parser = html2text.HTML2Text()
    html_parser.body_width = 0
    html_parser.mark_code = True
    return html_parser.handle(html)


def cleanup_ywh_redirects_from_html(
    ywh_domain: str,
    html: str,
) -> str:
    """
    Replace YesWeHack redirects with real URLs.

    Args:
        ywh_domain: a base domain of the YWH redirects
        html: an html

    Returns:
        the cleaned html
    """
    redirect_base_re = re.escape(f'{ywh_domain}/redirect?url=')

    pattern = re.compile(f'"(https?://{redirect_base_re}[^ "]*)"')
    redirect_urls = pattern.findall(html)
    for redirect_url in redirect_urls:
        real_url = _extract_real_url_from_redirect(
            redirect_url=html_unescape(redirect_url),
        )
        html = html.replace(
            redirect_url,
            html_escape(real_url or ''),
        )
    return html


def cleanup_ywh_redirects_from_text(
    ywh_domain: str,
    text: str,
) -> str:
    """
    Replace YesWeHack redirects with real URLs.

    Args:
        ywh_domain: a base domain of the YWH redirects
        text: an plain text

    Returns:
        the cleaned text
    """
    redirect_base_re = re.escape(f'{ywh_domain}/redirect?url=')

    pattern = re.compile(fr'(https?://{redirect_base_re}\S*)\b')
    redirect_urls = pattern.findall(text)
    for redirect_url in redirect_urls:
        real_url = _extract_real_url_from_redirect(
            redirect_url=redirect_url,
        )
        text = text.replace(
            redirect_url,
            real_url or '',
        )
    return text


def _extract_real_url_from_redirect(
    redirect_url: str,
) -> Optional[str]:
    parse_result = urlsplit(unquote(redirect_url))
    params = parse_qs(parse_result.query)
    if 'url' in params:
        return cast(List[str], params.get('url'))[0]
    return None


def cleanup_attachments_and_urls_from_html(
    html: str,
    attachments: List[Attachment],
) -> Tuple[str, List[Attachment]]:
    """
    Remove query parameters from attachments urls and from references in the HTML.

    Args:
        html: an html
        attachments: a list of attachments

    Returns:
        the cleaned html
    """
    clean_attachments = []
    clean_attachments_urls = []
    attachments_domains: Set[str] = set()
    for attachment in attachments:
        parsed_url = urlsplit(attachment.url)
        attachments_domains.add(parsed_url.netloc)
        clean_attachment = deepcopy(attachment)
        clean_attachment.url = f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}'
        clean_attachments.append(clean_attachment)
        clean_attachments_urls.append(clean_attachment.url)
    domains_base_re = '|'.join([
        re.escape(domain)
        for domain in attachments_domains
    ])
    pattern = re.compile(f'"(https?://(?:{domains_base_re})[^ "]*)"')
    html_urls = pattern.findall(html)
    for html_url in html_urls:
        parsed_html_url = urlsplit(html_url)
        clean_html_url = f'{parsed_html_url.scheme}://{parsed_html_url.netloc}{parsed_html_url.path}'
        if clean_html_url in clean_attachments_urls:
            html = html.replace(
                html_url,
                clean_html_url,
            )
    return html, clean_attachments
