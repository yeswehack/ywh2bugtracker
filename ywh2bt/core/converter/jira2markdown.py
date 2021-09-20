"""Models and functions used for format conversion from jira to markdown."""

import re
from typing import (
    Dict,
    List,
    Match,
)

from typing_extensions import Protocol

MatchStr = Match[str]

# inspired by https://github.com/metysj/jira2md.forked


class _ReplacementProtocol(Protocol):

    def __call__(
        self,
        src: str,
    ) -> str:
        ...  # noqa: WPS428


_RE_BLOCKQUOTE = re.compile(pattern=r'^bq\.\s+', flags=re.MULTILINE)
_RE_BOLD = re.compile(pattern=r'(^|\s|_)\*(\S.*)(\S)\*', flags=re.MULTILINE)
_RE_CODE = re.compile(
    pattern=r'\{code(:([a-z]+))?([:|]?(title|borderStyle|borderColor|borderWidth|bgColor|titleBGColor)=.+?)*\}',
)
_RE_CITATION = re.compile(pattern=r'(^|\s)\?\?((?:[^?])+)\?\?')
_RE_COLOR = re.compile(pattern=r'\{color:([^}]+)\}(.*)\{color\}', flags=re.MULTILINE | re.DOTALL)
_RE_HEADER = re.compile(pattern=r'^h([0-6])\.(.*)', flags=re.MULTILINE)
_RE_INSERT = re.compile(pattern=r'(^|\s)\+([^+]*)(\S)\+')
_RE_IMAGE = re.compile(pattern=r'!([^!|]+)(\|[^!]*)?!')
_RE_ITALIC = re.compile(pattern=r'(^|\s|\*)_(\S.*)(\S)_')
_RE_LIST = re.compile(pattern=r'^[ \t]*(\*+)\s+', flags=re.MULTILINE)
_RE_MONOSPACE = re.compile(pattern=r'(^|\s){{([^}]+)}}($|\s)')
_RE_NAMED_LINK = re.compile(pattern=r'\[(.+?)\|((www\.|(https?|ftp|ssh):\/\/)[^\s/$.?#].[^\s]*)\]')
_RE_NUMBERED_LIST = re.compile(pattern=r'^[ \t]*(#+)\s+', flags=re.MULTILINE)
_RE_PANEL = re.compile(pattern=r'\{panel:title=([^}]*)\}\n?(.*?)\n?\{panel\}', flags=re.MULTILINE | re.DOTALL)
_RE_QUOTE = re.compile(pattern=r'\{quote\}(.*)\{quote\}', flags=re.MULTILINE | re.DOTALL)
_RE_SIMPLE_LINK = re.compile(pattern=r'\[((www\.|(https?|ftp|ssh):\/\/)[^\s/$.?#].[^\s]*)\]')
_RE_STRIKETHROUGH = re.compile(pattern=r'(^|\s)-(\S+.*?\S)-($|\s)')
_RE_SUBSCRIPT = re.compile(pattern=r'(^|\s)~([^~]*)(\S)~')
_RE_SUPERSCRIPT = re.compile(pattern=r'(^|\s)\^([^^]*)(\S)\^')
_RE_TABLE_CELL = re.compile(pattern=r'\|[^|]+')
_RE_TABLE_HEADER = re.compile(pattern=r'^[ \t]*((?:\|\|.*?)+\|\|)[ \t]*$', flags=re.MULTILINE)
_RE_TABLE_NO_HEADER = re.compile(pattern=r'^[ \t]*((?:\|{1}[^\|\n]+)+\|)[ \t]*$', flags=re.MULTILINE)


def _replace_blockquote(
    src: str,
) -> str:
    return _RE_BLOCKQUOTE.sub('> ', src)


def _replace_bold(
    src: str,
) -> str:
    return _RE_BOLD.sub(r'\1**\2\3**', src)


def _replace_citation(
    src: str,
) -> str:
    return _RE_CITATION.sub(r'\1*&mdash; \2*', src)


def _replace_color(
    src: str,
) -> str:
    return _RE_COLOR.sub(r'<span style="color:\1" class="text-color-\1">\2</span>', src)


def _replace_header_sub(
    match: MatchStr,
) -> str:
    prefix = '#' * int(match.group(1))
    title = match.group(2)
    return f'{prefix}{title}'


def _replace_header(
    src: str,
) -> str:
    return _RE_HEADER.sub(_replace_header_sub, src)


def _replace_insert(
    src: str,
) -> str:
    return _RE_INSERT.sub(r'\1<ins>\2\3</ins>', src)


def _replace_image(
    src: str,
) -> str:
    return _RE_IMAGE.sub(r'![\1](\1)', src)


def _replace_italic(
    src: str,
) -> str:
    return _RE_ITALIC.sub(r'\1*\2\3*', src)


def _replace_list_sub(
    match: MatchStr,
) -> str:
    prefix = '  ' * (len(match.group(1)) - 1)
    return f'{prefix}* '


def _replace_list(
    src: str,
) -> str:
    return _RE_LIST.sub(_replace_list_sub, src)


def _replace_monospace(
    src: str,
) -> str:
    return _RE_MONOSPACE.sub(r'\1`\2`\3', src)


def _replace_named_link(
    src: str,
) -> str:
    return _RE_NAMED_LINK.sub(r'[\1](\2)', src)


def _replace_noformat(
    src: str,
) -> str:
    return src.replace('{noformat}', '```')


def _replace_numbered_list_sub(
    match: MatchStr,
) -> str:
    prefix = '  ' * (len(match.group(1)) - 1)
    return f'{prefix}1. '


def _replace_numbered_list(
    src: str,
) -> str:
    return _RE_NUMBERED_LIST.sub(_replace_numbered_list_sub, src)


def _replace_panel(
    src: str,
) -> str:
    return _RE_PANEL.sub(r'\n| \1 |\n| --- |\n| \2 |', src)


def _replace_quote_sub(
    match: MatchStr,
) -> str:
    lines = match.group(1).strip().split('\n')
    joined_lines = '\n> '.join(lines).strip()
    return f'> {joined_lines}\n'


def _replace_quote(
    src: str,
) -> str:
    return _RE_QUOTE.sub(_replace_quote_sub, src)


def _replace_simple_link(
    src: str,
) -> str:
    return _RE_SIMPLE_LINK.sub(r'<\1>', src)


def _replace_strikethrough(
    src: str,
) -> str:
    return _RE_STRIKETHROUGH.sub(r'\1~~\2~~\3', src)


def _replace_subscript(
    src: str,
) -> str:
    return _RE_SUBSCRIPT.sub(r'\1<sub>\2\3</sub>', src)


def _replace_superscript(
    src: str,
) -> str:
    return _RE_SUPERSCRIPT.sub(r'\1<sup>\2\3</sup>', src)


def _replace_table_no_header_sub(
    match: MatchStr,
) -> str:
    lookup_offset = match.start(1) - 1
    breaks_count = 0
    while True:
        space = lookup_offset > 0 and match.string[lookup_offset] in {' ', '\n', '\t'}
        if not (space and breaks_count < 2):
            break
        if match.string[lookup_offset] == '\n':
            breaks_count += 1
        lookup_offset -= 1
    if lookup_offset > 0 and match.string[lookup_offset] == '|':
        return match.group(0).strip()
    row = match.group(1).strip()
    empty_header = _RE_TABLE_CELL.sub('| ', row.strip())
    separator = _RE_TABLE_CELL.sub('| --- ', row.strip())
    return f'{empty_header}\n{separator}\n{row}'


def _replace_table_no_header(
    src: str,
) -> str:
    return _RE_TABLE_NO_HEADER.sub(_replace_table_no_header_sub, src)


def _replace_table_header_sub(
    match: MatchStr,
) -> str:
    header = match.group(1)
    single_barred = header.replace('||', '|')
    separator = _RE_TABLE_CELL.sub('| --- ', single_barred)
    return f'{single_barred}\n{separator}'


def _replace_table_header(
    src: str,
) -> str:
    return _RE_TABLE_HEADER.sub(_replace_table_header_sub, src)


class _Jira2Markdown:
    _replacement_map: Dict[str, str]
    _replacement_functions: List[_ReplacementProtocol]

    def __init__(self) -> None:
        self._replacement_map = {}
        self._replacement_functions = [
            # order matters!
            self._replace_code_block,
            _replace_quote,
            _replace_list,
            _replace_numbered_list,
            _replace_header,
            _replace_bold,
            _replace_italic,
            _replace_image,
            _replace_monospace,
            _replace_citation,
            _replace_insert,
            _replace_superscript,
            _replace_subscript,
            _replace_strikethrough,
            _replace_noformat,
            _replace_simple_link,
            _replace_named_link,
            _replace_blockquote,
            _replace_color,
            _replace_table_no_header,
            _replace_panel,
            _replace_table_header,
            self._apply_replacement_map,
        ]

    def convert(
        self,
        src: str,
    ) -> str:
        for replacement_function in self._replacement_functions:
            src = replacement_function(
                src=src,
            )
        return src

    def _replace_code_block(  # noqa: WPS210, WPS231
        self,
        src: str,
    ) -> str:
        src_len = len(src)
        result = ''
        current_word = ''
        collecting = False
        index = -1
        for i, c in enumerate(src):
            char = c
            if char not in {' ', '\t', '\n', '\r', '\v'} and i < src_len - 1:
                current_word += char
                continue
            if i == src_len - 1:
                current_word += char
                char = ''
            match = _RE_CODE.match(current_word)
            if match:
                language = match.group(2) or ''
                result = f'{result}```{language}{char}'
                collecting = not collecting  # noqa: WPS434
                if collecting:
                    index += 1
            else:
                if collecting:
                    key = f'@code_({index})_code@'
                    replacement = self._replacement_map.get(key)
                    value = current_word + char
                    if replacement is not None:
                        replacement += value
                    else:
                        replacement = value  # noqa: WPS220
                        result += key
                    self._replacement_map[key] = replacement
                else:
                    result += current_word + char
            current_word = ''
        return result

    def _apply_replacement_map(
        self,
        src: str,
    ) -> str:
        for key, value in self._replacement_map.items():
            src = src.replace(key, value)
        return src


def jira2markdown(
    src: str,
) -> str:
    """
    Convert jira string to markdown.

    Args:
        src: a jira string

    Returns:
        jira string converted to markdown
    """
    return _Jira2Markdown().convert(
        src=src,
    )
