"""Models and functions used for main GUI window."""
from __future__ import annotations

import sys
from typing import List, Optional, Union, cast

from PySide2.QtCore import QByteArray, QEvent, QSettings, QSize, Qt, Signal
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import (
    QAction,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QStyle,
    QToolBar,
    QWidget,
)

from ywh2bt.core.core import AVAILABLE_FORMATS
from ywh2bt.gui.dialog.file import FileFormatDialogFilters
from ywh2bt.gui.dialog.schema import SchemaDocumentationDialog
from ywh2bt.gui.widgets.logs_widget import LogEntry
from ywh2bt.gui.widgets.root_configuration_entry import RootConfigurationEntry
from ywh2bt.gui.widgets.root_configurations_widget import RootConfigurationsWidget
from ywh2bt.gui.widgets.typing import as_signal_instance
from ywh2bt.version import __VERSION__

__UI_VERSION__ = 1

_MENU_SEPARATOR = '-'
_TOOL_BAR_SEPARATOR = '-'
_TOOL_BAR_SPACER = '<->'


class MainWindow(QMainWindow):  # noqa: WPS214
    """Main window."""

    _log_entry_available: Signal = Signal(LogEntry)

    _file_format_dialog_filters: FileFormatDialogFilters
    _settings: QSettings
    _schema_doc_dialog: Optional[SchemaDocumentationDialog]

    _action_new: QAction
    _action_open: QAction
    _action_save: QAction
    _action_save_as: QAction
    _action_reload: QAction
    _action_test: QAction
    _action_sync: QAction
    _action_exit: QAction
    _action_schema_doc: QAction
    _action_about: QAction

    _root_configurations_widget: RootConfigurationsWidget

    def __init__(
        self,
        settings: QSettings,
    ) -> None:
        """
        Initialize self.

        Args:
            settings: application settings
        """
        super().__init__()
        self._file_format_dialog_filters = FileFormatDialogFilters(
            formats=AVAILABLE_FORMATS,
        )
        self._settings = settings
        self._schema_doc_dialog = None
        self._init_ui()
        self._restore_settings()

    def _init_ui(self) -> None:
        self._create_actions()
        self._create_menus()

        tool_bar = self._create_main_tool_bar()
        self.addToolBar(
            Qt.LeftToolBarArea,
            tool_bar,
        )

        self._root_configurations_widget = self._create_root_configurations_widget()

        self.setCentralWidget(self._root_configurations_widget)

        self.statusBar().show()

    def _create_actions(
        self,
    ) -> None:
        self._action_new = self._create_new_action()
        self._action_open = self._create_open_action()
        self._action_save = self._create_save_action()
        self._action_save_as = self._create_save_as_action()
        self._action_reload = self._create_reload_action()
        self._action_test = self._create_test_action()
        self._action_sync = self._create_sync_action()
        self._action_exit = self._create_exit_action()
        self._action_schema_doc = self._create_schema_doc_action()
        self._action_about = self._create_about_action()

    def _create_menus(
        self,
    ) -> None:
        bar = self.menuBar()

        file_menu = bar.addMenu('&File')
        file_menu.setObjectName('menu_file')
        _add_menu_items(
            menu=file_menu,
            items=[
                self._action_new,
                self._action_open,
                self._action_save,
                self._action_save_as,
                self._action_reload,
                _MENU_SEPARATOR,
                self._action_exit,
            ],
        )

        run_menu = bar.addMenu('&Run')
        run_menu.setObjectName('menu_run')
        _add_menu_items(
            menu=run_menu,
            items=[
                self._action_test,
                self._action_sync,
            ],
        )

        help_menu = bar.addMenu('&Help')
        help_menu.setObjectName('menu_help')
        _add_menu_items(
            menu=help_menu,
            items=[
                self._action_schema_doc,
                self._action_about,
            ],
        )

    def _create_new_action(
        self,
    ) -> QAction:
        action = QAction('&New', self)
        action.setObjectName('action_new')
        action.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        action.setShortcuts(QKeySequence.New)
        action.setStatusTip('Create a new configuration file')
        as_signal_instance(action.triggered).connect(
            self._on_new_file_triggered,
        )
        return action

    def _create_open_action(
        self,
    ) -> QAction:
        action = QAction('&Open...', self)
        action.setObjectName('action_open')
        action.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        action.setShortcuts(QKeySequence.Open)
        action.setStatusTip('Open a configuration file')
        as_signal_instance(action.triggered).connect(
            self._on_open_file_triggered,
        )
        return action

    def _create_save_action(
        self,
    ) -> QAction:
        action = QAction('&Save...', self)
        action.setObjectName('action_save')
        action.setEnabled(False)
        action.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        action.setShortcuts(QKeySequence.Save)
        action.setStatusTip('Save the current configuration file')
        as_signal_instance(action.triggered).connect(
            self._on_save_configuration_triggered,
        )
        return action

    def _create_save_as_action(
        self,
    ) -> QAction:
        action = QAction('&Save as...', self)
        action.setObjectName('action_save_as')
        action.setEnabled(False)
        action.setStatusTip('Save the current configuration in a new file')
        as_signal_instance(action.triggered).connect(
            self._on_save_as_configuration_triggered,
        )
        return action

    def _create_reload_action(
        self,
    ) -> QAction:
        action = QAction('&Reload from disk', self)
        action.setObjectName('action_reload')
        action.setEnabled(False)
        action.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        action.setShortcuts(QKeySequence.Refresh)
        action.setStatusTip('Reload the current configuration file from the disk')
        as_signal_instance(action.triggered).connect(
            self._on_reload_configuration_triggered,
        )
        return action

    def _create_test_action(
        self,
    ) -> QAction:
        action = QAction('&Test...', self)
        action.setObjectName('action_test')
        action.setEnabled(False)
        action.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        action.setStatusTip('Test the connection to the trackers and to YesWeHack programs')
        as_signal_instance(action.triggered).connect(
            self._on_test_configuration_triggered,
        )
        return action

    def _create_sync_action(
        self,
    ) -> QAction:
        action = QAction('&Sync...', self)
        action.setObjectName('action_sync')
        action.setEnabled(False)
        action.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        action.setStatusTip('Synchronize the current configuration file')
        as_signal_instance(action.triggered).connect(
            self._on_sync_configuration_triggered,
        )
        return action

    def _create_about_action(
        self,
    ) -> QAction:
        action = QAction('&About', self)
        action.setObjectName('action_about')
        action.setIcon(QIcon(':/resources/icons/ywh2bt.png'))
        action.setStatusTip('Show information about this application')
        as_signal_instance(action.triggered).connect(
            self._on_about_triggered,
        )
        return action

    def _create_schema_doc_action(
        self,
    ) -> QAction:
        action = QAction('&Schema documentation', self)
        action.setObjectName('action_schema_doc')
        action.setIcon(self.style().standardIcon(QStyle.SP_DialogHelpButton))
        action.setStatusTip('Show configuration schema documentation')
        as_signal_instance(action.triggered).connect(
            self._on_schema_doc_triggered,
        )
        return action

    def _create_exit_action(
        self,
    ) -> QAction:
        action = QAction('E&xit', self)
        action.setObjectName('action_exit')
        action.setShortcuts(QKeySequence.Quit)
        action.setStatusTip('Exit the application')
        as_signal_instance(action.triggered).connect(
            self._on_exit_triggered,
        )
        return action

    def _create_main_tool_bar(
        self,
    ) -> QWidget:
        tool_bar = self.addToolBar('Main tools')
        tool_bar.setObjectName('tools_tool_bar')

        _add_tool_bar_items(
            tool_bar=tool_bar,
            items=[
                self._action_new,
                self._action_open,
                self._action_save,
                self._action_reload,
                _TOOL_BAR_SEPARATOR,
                self._action_test,
                self._action_sync,
                _TOOL_BAR_SPACER,
                _TOOL_BAR_SEPARATOR,
                self._action_schema_doc,
                self._action_about,
            ],
        )

        return tool_bar

    def _create_empty_widget(
        self,
    ) -> QWidget:
        toolbar = QToolBar(self)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        spacer_begin = QWidget(toolbar)
        spacer_begin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer_end = QWidget(toolbar)
        spacer_end.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        toolbar.addWidget(spacer_begin)
        toolbar.addAction(self._action_new)
        toolbar.addAction(self._action_open)
        toolbar.addWidget(spacer_end)

        return toolbar

    def _create_root_configurations_widget(
        self,
    ) -> RootConfigurationsWidget:
        widget = RootConfigurationsWidget(
            parent=self,
            settings=self._settings,
            empty_widget=self._create_empty_widget(),
        )
        as_signal_instance(widget.entry_modified).connect(
            self._on_entry_modified,
        )
        as_signal_instance(widget.current_entry_changed).connect(
            self._on_current_entry_changed,
        )
        as_signal_instance(widget.entry_saved).connect(
            self._on_entry_saved,
        )
        return widget

    def _on_entry_modified(
        self,
        entry: RootConfigurationEntry,
    ) -> None:
        self._update_actions(
            entry=entry,
        )

    def _on_entry_saved(
        self,
        entry: RootConfigurationEntry,
    ) -> None:
        self.statusBar().showMessage(
            f'{entry.name} saved',
        )

    def _on_current_entry_changed(
        self,
        entry: Optional[RootConfigurationEntry],
    ) -> None:
        self._update_actions(
            entry=entry,
        )

    def _update_actions(
        self,
        entry: Optional[RootConfigurationEntry],
    ) -> None:
        self._update_save_action(
            entry=entry,
        )
        self._update_save_as_action(
            entry=entry,
        )
        self._update_reload_action(
            entry=entry,
        )
        self._update_test_action(
            entry=entry,
        )
        self._update_sync_action(
            entry=entry,
        )

    def _update_save_action(
        self,
        entry: Optional[RootConfigurationEntry],
    ) -> None:
        enabled = False
        if entry and not entry.is_empty() and entry.has_changed():
            enabled = True
        self._action_save.setEnabled(enabled)

    def _update_save_as_action(
        self,
        entry: Optional[RootConfigurationEntry],
    ) -> None:
        enabled = False
        if entry and not entry.is_empty():
            enabled = True
        self._action_save_as.setEnabled(enabled)

    def _update_reload_action(
        self,
        entry: Optional[RootConfigurationEntry],
    ) -> None:
        enabled = False
        if entry and entry.file:
            enabled = True
        self._action_reload.setEnabled(enabled)

    def _update_test_action(
        self,
        entry: Optional[RootConfigurationEntry],
    ) -> None:
        enabled = False
        if entry and entry.configuration and entry.configuration.is_valid():
            enabled = True
        self._action_test.setEnabled(enabled)

    def _update_sync_action(
        self,
        entry: Optional[RootConfigurationEntry],
    ) -> None:
        enabled = False
        if entry and entry.configuration and entry.configuration.is_valid():
            enabled = True
        self._action_sync.setEnabled(enabled)

    def _on_new_file_triggered(
        self,
    ) -> None:
        self._root_configurations_widget.create_new_configuration()

    def _on_open_file_triggered(
        self,
    ) -> None:
        self._root_configurations_widget.prompt_open_configuration()

    def _on_save_configuration_triggered(
        self,
    ) -> None:
        self._root_configurations_widget.save_current_entry()

    def _on_save_as_configuration_triggered(
        self,
    ) -> None:
        self._root_configurations_widget.save_as_current_entry()

    def _on_reload_configuration_triggered(
        self,
    ) -> None:
        self._root_configurations_widget.reload_current_configuration()

    def _on_test_configuration_triggered(
        self,
    ) -> None:
        self._root_configurations_widget.test_current_entry()

    def _on_sync_configuration_triggered(
        self,
    ) -> None:
        self._root_configurations_widget.synchronize_current_entry()

    def _on_exit_triggered(
        self,
    ) -> None:
        self.close()

    def _on_about_triggered(
        self,
    ) -> None:
        python_version = '.'.join(map(str, sys.version_info[:3]))
        about_text = [
            f'<b>Core version</b>: {__VERSION__}',
            f'<b>UI version</b>: {__UI_VERSION__}',
            f'Python: {python_version}',
        ]
        QMessageBox.about(
            self,
            'ywh2bt-gui',
            '<br/>\n'.join(about_text),
        )

    def _on_schema_doc_triggered(
        self,
    ) -> None:
        if not self._schema_doc_dialog:
            self._schema_doc_dialog = SchemaDocumentationDialog(
                self,
            )
            self._schema_doc_dialog.resize(
                QSize(600, 600),
            )
            self._restore_schema_doc_geometry_from_settings()
        self._schema_doc_dialog.show()

    def closeEvent(  # noqa: N802
        self,
        event: QEvent,
    ) -> None:
        """
        Handle 'close' event.

        Args:
            event: a close event
        """
        if self._root_configurations_widget.has_changed_entries():
            reply = QMessageBox.question(
                self,
                'Exit',
                'Are you sure you want to exit?\nUnsaved changes might be lost.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        self._save_settings()
        event.accept()
        super().closeEvent(event)

    def _save_settings(
        self,
    ) -> None:
        self._settings.setValue('main_geometry', self.saveGeometry().toBase64())
        self._settings.setValue('main_state', self.saveState(__UI_VERSION__).toBase64())
        if self._schema_doc_dialog:
            self._settings.setValue('schema_doc_geometry', self._schema_doc_dialog.saveGeometry().toBase64())

    def _restore_settings(
        self,
    ) -> None:
        self._restore_geometry_from_settings()
        self._restore_state_from_settings()

    def _restore_geometry_from_settings(
        self,
    ) -> None:
        if not self._settings.contains('main_geometry'):
            return
        geometry = QByteArray.fromBase64(cast(QByteArray, self._settings.value('main_geometry')))
        if geometry:
            self.restoreGeometry(geometry)

    def _restore_state_from_settings(
        self,
    ) -> None:
        if not self._settings.contains('main_state'):
            return
        state = QByteArray.fromBase64(cast(QByteArray, self._settings.value('main_state')))
        if state:
            self.restoreState(state, __UI_VERSION__)

    def _restore_schema_doc_geometry_from_settings(
        self,
    ) -> None:
        if not self._schema_doc_dialog or not self._settings.contains('schema_doc_geometry'):
            return
        geometry = QByteArray.fromBase64(cast(QByteArray, self._settings.value('schema_doc_geometry')))
        if geometry:
            self._schema_doc_dialog.restoreGeometry(geometry)


def _add_menu_items(
    menu: QMenu,
    items: List[Union[str, QAction]],
) -> None:
    for item in items:
        if item == _MENU_SEPARATOR:
            menu.addSeparator()
        elif isinstance(item, QAction):
            menu.addAction(item)


def _add_tool_bar_items(
    tool_bar: QToolBar,
    items: List[Union[str, QAction]],
) -> None:
    for item in items:
        if item == _TOOL_BAR_SEPARATOR:
            tool_bar.addSeparator()
        elif item == _TOOL_BAR_SPACER:
            spacer = QWidget(tool_bar)
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            tool_bar.addWidget(spacer)
        elif isinstance(item, QAction):
            tool_bar.addAction(item)
