"""Models and functions used for line-edits containing sensible data."""
from __future__ import annotations

from functools import partial
from typing import Any, Optional

from PySide2.QtCore import Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from ywh2bt.gui.widgets import constants
from ywh2bt.gui.widgets.typing import as_signal_instance


class SecretLineEditWidget(QWidget):
    """A widget consisting of a line-edit in password echo mode and a button temporarily enables normal echo mode."""

    text_edited: Signal = Signal(str)

    _icon_show: QIcon
    _icon_hide: QIcon

    _line_edit: QLineEdit
    _button: QPushButton

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
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
            **kwargs,
        )
        self._icon_show = QIcon(':/resources/icons/show.png')
        self._icon_hide = QIcon(':/resources/icons/hide.png')

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)

        self._line_edit = self._create_line_edit()

        self._button = self._create_button()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._line_edit)
        layout.addWidget(self._button)

    def _create_line_edit(
        self,
    ) -> QLineEdit:
        widget = QLineEdit(self)
        widget.setEchoMode(QLineEdit.Password)
        as_signal_instance(widget.textEdited[str]).connect(
            as_signal_instance(self.text_edited).emit,
        )
        return widget

    def _create_button(
        self,
    ) -> QPushButton:
        widget = QPushButton(self)
        widget.setIcon(self._icon_hide)
        widget.setToolTip('Reveal secret')
        widget.setFixedWidth(constants.SMALL_BUTTON_WIDTH)
        widget.setIconSize(constants.SMALL_BUTTON_ICON_SIZE)
        as_signal_instance(widget.pressed).connect(
            partial(
                self._update_widget,
                QLineEdit.Normal,
                self._icon_show,
            ),
        )
        as_signal_instance(widget.released).connect(
            partial(
                self._update_widget,
                QLineEdit.Password,
                self._icon_hide,
            ),
        )
        return widget

    def _update_widget(
        self,
        echo_mode: QLineEdit.EchoMode,
        icon: QIcon,
    ) -> None:
        self._line_edit.setEchoMode(echo_mode)
        self._button.setIcon(icon)

    def setText(  # noqa: N802
        self,
        text: str,
    ) -> None:
        """
        Set the text of the line-edit.

        Args:
            text: a text
        """
        self._line_edit.setText(text)
