"""Models and functions used in schema documentation dialogs."""
from typing import Any, Optional

import markdown
from PySide2.QtGui import QKeySequence
from PySide2.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PySide2.QtWidgets import QAction, QMainWindow, QWidget

from ywh2bt.core.schema.markdown import root_configuration_as_markdown
from ywh2bt.gui.widgets.typing import as_signal_instance


class SchemaDocumentationDialog(QMainWindow):
    """A window that display the schema documentation."""

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
        )
        self._init_ui()

    def _init_ui(
        self,
    ) -> None:
        self._create_menus()
        self.setCentralWidget(self._create_view())
        self.statusBar().show()

    def _create_menus(
        self,
    ) -> None:
        bar = self.menuBar()

        file_menu = bar.addMenu('&File')
        file_menu.setObjectName('menu_file')
        file_menu.addAction(self._create_close_action())

    def _create_close_action(
        self,
    ) -> QAction:
        action = QAction('&Close', self)
        action.setObjectName('action_close')
        action.setShortcuts(QKeySequence.Close)
        action.setStatusTip('Close')
        as_signal_instance(action.triggered).connect(
            self._on_close_triggered,
        )
        return action

    def _on_close_triggered(
        self,
    ) -> None:
        self.close()

    def _create_view(
        self,
    ) -> QWebEngineView:
        page = QWebEnginePage(self)
        page.setHtml(
            markdown.markdown(
                root_configuration_as_markdown(),
            ),
        )
        view = QWebEngineView(self)
        view.setPage(page)
        return view
