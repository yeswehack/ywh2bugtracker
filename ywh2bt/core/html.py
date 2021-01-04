"""Models and functions used for manipulating html data."""
import re
from typing import Iterator
from urllib.parse import parse_qs, unquote, urlencode, urlsplit, urlunsplit

import html2text
from bs4 import BeautifulSoup  # type: ignore


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
    redirect_base_re = re.escape(f'https://{ywh_domain}/redirect?url=')

    pattern = re.compile(f'"({redirect_base_re})([^ "]*)"')
    redirect_urls = pattern.findall(html)
    for base_url, redirect_url in redirect_urls:
        html = _cleanup_ywh_redirect_from_text(
            text=html,
            base_url=base_url,
            redirect_url=redirect_url,
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
    redirect_base_re = re.escape(f'https://{ywh_domain}/redirect?url=')

    pattern = re.compile(fr'({redirect_base_re})(\S*)')
    redirect_urls = pattern.findall(text)
    for base_url, redirect_url in redirect_urls:
        text = _cleanup_ywh_redirect_from_text(
            text=text,
            base_url=base_url,
            redirect_url=redirect_url,
        )
    return text


def _cleanup_ywh_redirect_from_text(
    text: str,
    base_url: str,
    redirect_url: str,
) -> str:
    parse_result = urlsplit(unquote(unquote(redirect_url)))
    params = parse_qs(parse_result.query)
    clean_params = {
        name: value
        for name, value in params.items()
        if name not in {'expires', 'token'}
    }
    clean_url = urlunsplit(
        (
            parse_result.scheme,
            parse_result.netloc,
            parse_result.path,
            urlencode(clean_params, doseq=True),
            parse_result.fragment,
        ),
    )
    return text.replace(
        f'{base_url}{redirect_url}',
        clean_url,
    )
