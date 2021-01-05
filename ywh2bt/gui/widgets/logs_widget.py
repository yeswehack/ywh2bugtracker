"""Models and functions used for the LogsWidget."""
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from html import escape as html_escape
from string import Template
from typing import Any, Dict, Optional, OrderedDict

from PySide2.QtCore import QPoint, QUrl, Qt, Signal
from PySide2.QtGui import QDesktopServices, QMouseEvent
from PySide2.QtWidgets import (
    QMenu,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ywh2bt.gui.widgets.typing import as_signal_instance


class LogType(Enum):
    """Log type."""

    standard = 'normal'
    success = 'success'
    warning = 'warning'
    error = 'error'


LEVEL_COLORS: Dict[LogType, str] = OrderedDict[LogType, str]({
    LogType.standard: 'black',
    LogType.success: 'green',
    LogType.warning: 'orange',
    LogType.error: 'red',
})


@dataclass
class LogEntry:
    """A log entry."""

    date_time: datetime
    context: str
    message: str
    log_type: LogType = LogType.standard


class _PlainTextEdit(QPlainTextEdit):
    link_clicked: Signal = Signal(str)
    _clicked_anchor: Optional[str]

    def mousePressEvent(  # noqa: N802
        self,
        event: QMouseEvent,
    ) -> None:
        anchor = None
        if event.button() & Qt.LeftButton:
            anchor = self.anchorAt(
                event.pos(),
            )
        self._clicked_anchor = anchor
        super().mousePressEvent(
            event,
        )

    def mouseReleaseEvent(  # noqa: N802
        self,
        event: QMouseEvent,
    ) -> None:
        if event.button() & Qt.LeftButton:
            anchor = self.anchorAt(
                event.pos(),
            )
            if anchor and anchor == self._clicked_anchor:
                as_signal_instance(self.link_clicked).emit(
                    anchor,
                )
        super().mouseReleaseEvent(
            event,
        )


class LogsWidget(QWidget):
    """A widget to display log messages."""

    _text_edit: _PlainTextEdit

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Initialize self.

        Args:
            parent: a parent widget
            args: extra arguments
            kwargs: extra keyword arguments
        """
        super().__init__(
            parent,
            *args,
            *kwargs,
        )
        self._init_ui()

    def _init_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text_edit = self._create_text_edit()
        layout.addWidget(self._text_edit)

    def _create_text_edit(
        self,
    ) -> QPlainTextEdit:
        widget = _PlainTextEdit(self)
        widget.setLineWrapMode(QPlainTextEdit.NoWrap)
        widget.setReadOnly(True)
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        as_signal_instance(widget.customContextMenuRequested).connect(
            self._on_context_menu_requested,
        )
        as_signal_instance(widget.link_clicked).connect(
            self._on_link_clicked,
        )
        return widget

    def _on_context_menu_requested(
        self,
        position: QPoint,
    ) -> None:
        menu = QMenu(self)
        action_clear = menu.addAction('Clear')
        as_signal_instance(action_clear.triggered).connect(
            self._on_clear_action_triggered,
        )
        menu.popup(
            self.mapToGlobal(position),
        )

    def _on_clear_action_triggered(
        self,
    ) -> None:
        self._text_edit.setPlainText('')

    def _on_link_clicked(
        self,
        link: str,
    ) -> None:
        url = QUrl(link)
        QDesktopServices.openUrl(url)

    def add_log_entry(
        self,
        entry: LogEntry,
    ) -> None:
        """
        Add a new entry to the log.

        Args:
            entry: an entry
        """
        self._add_log_entry_html(
            entry=entry,
        )

    def _add_log_entry_html(
        self,
        entry: LogEntry,
    ) -> None:
        new_log_html = _format_log_entry_html(
            entry=entry,
        )
        self._text_edit.appendHtml(
            new_log_html,
        )


log_html_template_contents = """
<p style="color: ${type_color}"><b>[${date_time}]</b>: ${context}</p>
<p style="color: ${type_color}; white-space: pre">${message}</p>
<p></p>
"""
log_html_template = Template(log_html_template_contents)
log_html_link_template = Template('<a href="${url}">${url}</a>')

url_re = re.compile(r'(https?://[^\s]+)')


def _format_log_entry_html(
    entry: LogEntry,
) -> str:
    date_time = entry.date_time.strftime('%Y-%m-%d %H:%M:%S')  # noqa: WPS323
    context = html_escape(entry.context.strip())
    message = html_escape(entry.message.strip())
    urls = url_re.findall(message)
    for url in set(urls):
        link = log_html_link_template.substitute(
            url=url,
        )
        message = message.replace(
            url,
            link,
        )
    return log_html_template.substitute(
        date_time=date_time,
        context=context,
        message=message,
        type_color=_log_type_to_color(
            log_type=entry.log_type,
        ),
    )


def _log_type_to_color(
    log_type: LogType,
) -> str:
    return LEVEL_COLORS.get(
        log_type,
        'black',
    )
