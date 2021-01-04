"""Models and functions used for root configurations GUI."""
from __future__ import annotations

from typing import Any, List, Optional, Tuple, cast

from PySide2.QtCore import QFileInfo, QSettings, Qt, Signal
from PySide2.QtWidgets import QBoxLayout, QFileDialog, QInputDialog, QMessageBox, QTabWidget, QWidget

from ywh2bt.core.core import AVAILABLE_FORMATS
from ywh2bt.core.exceptions import CoreException
from ywh2bt.gui.dialog.error import ErrorDialogMixin
from ywh2bt.gui.dialog.file import FileFormatDialogFilters
from ywh2bt.gui.widgets.root_configuration_entry import RootConfigurationEntry
from ywh2bt.gui.widgets.root_configuration_widget import RootConfigurationWidget
from ywh2bt.gui.widgets.typing import as_signal_instance


class RootConfigurationsWidget(QWidget, ErrorDialogMixin):  # noqa: WPS214
    """
    Root configurations GUI.

    Display and edit multiple configurations in visual tabs.
    """

    entry_modified: Signal = Signal(RootConfigurationEntry)
    entry_saved: Signal = Signal(RootConfigurationEntry)
    current_entry_changed: Signal = Signal(RootConfigurationEntry)

    _file_format_dialog_filters: FileFormatDialogFilters
    _settings: QSettings
    _empty_widget: QWidget
    _tab_widget: QTabWidget

    _entries: List[RootConfigurationEntry]

    def __init__(
        self,
        settings: QSettings,
        empty_widget: QWidget,
        parent: Optional[QWidget] = None,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Initialize self.

        Args:
            settings: application settings
            empty_widget: a widget to display if no configurations are currently being edited
            parent: a parent widget
            args: extra arguments
            kwargs: extra keyword arguments
        """
        super().__init__(
            parent,
            *args,
            **kwargs,
        )
        self._settings = settings
        self._entries = []
        self._file_format_dialog_filters = FileFormatDialogFilters(
            formats=AVAILABLE_FORMATS,
        )
        self._init_ui(
            empty_widget=empty_widget,
        )

    def _init_ui(
        self,
        empty_widget: QWidget,
    ) -> None:
        layout = QBoxLayout(
            QBoxLayout.LeftToRight,
            self,
        )

        self._empty_widget = empty_widget
        self._tab_widget = self._create_tab_widget()

        self._auto_show_hide_tabs()

        layout.addWidget(self._empty_widget, Qt.AlignCenter)
        layout.addWidget(self._tab_widget)
        layout.setMargin(0)

    def _create_tab_widget(
        self,
    ) -> QTabWidget:
        widget = QTabWidget(self)
        widget.setTabsClosable(True)
        as_signal_instance(widget.currentChanged).connect(
            self._on_current_tab_changed,
        )
        as_signal_instance(widget.tabCloseRequested).connect(
            self._on_tab_close_requested,
        )
        return widget

    def _on_current_tab_changed(
        self,
        tab_index: int,
    ) -> None:
        entry = None
        if tab_index >= 0:
            entry = self._entries[tab_index]
        as_signal_instance(self.current_entry_changed).emit(
            entry,
        )

    def _on_tab_close_requested(
        self,
        tab_index: int,
    ) -> None:
        entry = self._entries[tab_index]
        if not entry.has_changed():
            self._on_entry_close_accepted(
                entry=entry,
            )
            return
        reply = QMessageBox.question(
            self,
            f'Close {entry.name}',
            'This configuration has unsaved changes. Close anyway?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._on_entry_close_accepted(
                entry=entry,
            )

    def _on_entry_close_accepted(
        self,
        entry: RootConfigurationEntry,
    ) -> None:
        tab_index = self._get_tab_index_for_entry(
            entry=entry,
        )
        self._tab_widget.removeTab(tab_index)
        self._entries.pop(tab_index)
        self._auto_show_hide_tabs()

    def _auto_show_hide_tabs(
        self,
    ) -> None:
        if self._tab_widget.count() == 0:
            self._tab_widget.hide()
            self._empty_widget.show()
        else:
            self._tab_widget.show()
            self._empty_widget.hide()

    def create_new_configuration(
        self,
    ) -> None:
        """Create a new configuration."""
        selected_format, ok = QInputDialog().getItem(
            self,
            'Select format',
            'Format:',
            list(AVAILABLE_FORMATS.keys()),
            0,
            False,  # noqa: WPS425
        )
        if not ok:
            return
        self.add_entry(
            entry=RootConfigurationEntry(
                name='New configuration',
                raw='',
                original_raw='',
                raw_format=selected_format,
            ),
        )

    def prompt_open_configuration(
        self,
    ) -> None:
        """Prompt for opening an existing configuration."""
        open_file = self._prompt_open_file()
        if not open_file:
            return
        file_path, file_format = open_file
        self._try_open_configuration(
            file_info=QFileInfo(file_path),
            file_format=file_format,
        )

    def reload_current_configuration(
        self,
    ) -> None:
        """Reload the current configuration."""
        entry = self.get_current_entry()
        if not entry.file:
            return
        reply = QMessageBox.question(
            self,
            f'Reload {entry.name}',
            f'Reload {entry.file.info.filePath()} from disk?\nUnsaved changes will be lost.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return
        self._try_open_configuration(
            file_info=entry.file.info,
            file_format=entry.file.file_format,
        )

    def _prompt_open_file(
        self,
    ) -> Optional[Tuple[str, str]]:
        last_opened_dir = self._get_last_opened_dir()
        file_path, chosen_filter = QFileDialog.getOpenFileName(
            self,
            'Open file',
            last_opened_dir,
            self._file_format_dialog_filters.get_filters_string(),
        )
        if not file_path:
            return None
        chosen_format = self._file_format_dialog_filters.get_format_name(
            filter_string=chosen_filter,
        )
        if chosen_format is None:
            return None
        self._settings.setValue('last_opened_file', file_path)
        self._settings.setValue('last_opened_file_format', chosen_format)
        return file_path, chosen_format

    def _try_open_configuration(
        self,
        file_info: QFileInfo,
        file_format: str,
    ) -> None:
        try:
            entry = RootConfigurationEntry.from_file(
                file_info=file_info,
                file_format=file_format,
            )
        except CoreException as e:
            self.show_exception_dialog(
                parent=self,
                text='Open error',
                informative_text='Unable to open configuration',
                exception=e,
            )
            return
        self.add_entry(
            entry=entry,
        )

    def _get_last_opened_dir(
        self,
    ) -> str:
        return QFileInfo(
            cast(str, self._settings.value('last_opened_file')),
        ).dir().path()

    def add_entry(
        self,
        entry: RootConfigurationEntry,
    ) -> None:
        """
        Add a configuration entry to be edited.

        Args:
            entry: a configuration entry
        """
        existing_entry = self._get_same_file_entry(
            entry=entry,
        )
        if existing_entry:
            existing_entry.configuration = entry.configuration
            tab_index = self.refresh_entry(
                entry=existing_entry,
            )
        else:
            widget = RootConfigurationWidget(
                settings=self._settings,
                parent=self,
                entry=entry,
            )
            as_signal_instance(widget.root_configuration_modified).connect(
                self._on_entry_modified,
            )
            as_signal_instance(widget.root_configuration_saved).connect(
                self._on_entry_saved,
            )
            as_signal_instance(widget.root_configuration_saved_as).connect(
                self._on_entry_saved_as,
            )
            self._entries.append(entry)
            tab_index = self._tab_widget.addTab(
                widget,
                _tab_title(
                    entry=entry,
                ),
            )
            self._update_tab_text(
                entry=entry,
            )
        self._tab_widget.setCurrentIndex(tab_index)
        self._auto_show_hide_tabs()

    def has_changed_entries(
        self,
    ) -> bool:
        """
        Check if any opened entry has changed.

        Returns:
            True if any entry has changed.
        """
        return any(entry.has_changed() for entry in self._entries)

    def refresh_entry(
        self,
        entry: RootConfigurationEntry,
    ) -> int:
        """
        Refresh the display of a configuration entry.

        Args:
            entry: a configuration entry

        Returns:
            The index at which this configuration is placed in the edited list
        """
        tab_index = self._get_tab_index_for_entry(
            entry=entry,
        )
        widget = cast(RootConfigurationWidget, self._tab_widget.widget(tab_index))
        widget.set_entry(
            entry=entry,
        )
        self._update_tab_text(
            entry=entry,
        )
        as_signal_instance(self.entry_modified).emit(
            entry,
        )
        return tab_index

    def save_current_entry(
        self,
    ) -> None:
        """Save the current entry configuration."""
        self._get_current_entry_widget().save()

    def save_as_current_entry(
        self,
    ) -> None:
        """Save the current entry configuration in a new file."""
        self._get_current_entry_widget().save_as()

    def test_current_entry(
        self,
    ) -> None:
        """Synchronize the current entry configuration."""
        self._get_current_entry_widget().test()

    def synchronize_current_entry(
        self,
    ) -> None:
        """Synchronize the current entry configuration."""
        self._get_current_entry_widget().synchronize()

    def _get_current_entry_widget(
        self,
    ) -> RootConfigurationWidget:
        return cast(RootConfigurationWidget, self._tab_widget.widget(
            self._tab_widget.currentIndex(),
        ))

    def _get_same_file_entry(
        self,
        entry: RootConfigurationEntry,
    ) -> Optional[RootConfigurationEntry]:
        if not entry.file:
            return None
        for existing_entry in self._entries:
            if existing_entry.file and existing_entry.file.info == entry.file.info:
                return existing_entry
        return None

    def _on_entry_modified(
        self,
        entry: RootConfigurationEntry,
    ) -> None:
        self._update_tab_text(
            entry=entry,
        )
        as_signal_instance(self.entry_modified).emit(
            entry,
        )

    def _on_entry_saved(
        self,
        entry: RootConfigurationEntry,
    ) -> None:
        as_signal_instance(self.entry_saved).emit(
            entry,
        )

    def _on_entry_saved_as(
        self,
        file_path: str,
        file_format: str,
    ) -> None:
        self._try_open_configuration(
            file_info=QFileInfo(file_path),
            file_format=file_format,
        )

    def _update_tab_text(
        self,
        entry: RootConfigurationEntry,
    ) -> None:
        color = Qt.black
        if not entry.configuration or not entry.configuration.is_valid():
            color = Qt.red
        tab_index = self._get_tab_index_for_entry(
            entry=entry,
        )
        self._tab_widget.tabBar().setTabTextColor(
            tab_index,
            color,
        )
        self._tab_widget.setTabText(
            tab_index,
            _tab_title(
                entry=entry,
            ),
        )

    def get_current_entry(
        self,
    ) -> RootConfigurationEntry:
        """
        Get the currently displayed configuration entry.

        Returns:
            The current configuration entry
        """
        tab_index = self._tab_widget.currentIndex()
        return self._entries[tab_index]

    def _get_tab_index_for_entry(
        self,
        entry: RootConfigurationEntry,
    ) -> int:
        return self._entries.index(entry)


def _tab_title(
    entry: RootConfigurationEntry,
) -> str:
    tab_title = entry.name
    if entry.has_changed():
        tab_title = f'* {tab_title}'
    return tab_title
