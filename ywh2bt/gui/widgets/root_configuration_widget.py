"""Models and functions used for root configuration GUI."""
from datetime import datetime
from io import StringIO
from typing import Any, Optional, Tuple, cast

from PySide2.QtCore import QFileInfo, QSettings, Signal
from PySide2.QtGui import QFontDatabase, QFontMetrics, Qt
from PySide2.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.core import AVAILABLE_FORMATS, get_root_configuration_loader
from ywh2bt.core.error import print_error
from ywh2bt.core.exceptions import CoreException
from ywh2bt.core.loader import RootConfigurationLoader
from ywh2bt.gui.dialog.error import ErrorDialogMixin
from ywh2bt.gui.dialog.file import FileFormatDialogFilters
from ywh2bt.gui.hashing import file_checksum
from ywh2bt.gui.widgets.attribute.attributes_container_widget import AttributesContainerWidget
from ywh2bt.gui.widgets.logs_widget import LogEntry, LogType, LogsWidget
from ywh2bt.gui.widgets.root_configuration_entry import RootConfigurationEntry, RootConfigurationEntryFile
from ywh2bt.gui.widgets.thread.synchronizer import SynchronizerThread
from ywh2bt.gui.widgets.thread.tester import TesterThread
from ywh2bt.gui.widgets.typing import as_signal_instance


class RootConfigurationWidget(QWidget, ErrorDialogMixin):
    """Root configuration GUI."""

    root_configuration_modified: Signal = Signal(RootConfigurationEntry)
    root_configuration_saved: Signal = Signal(RootConfigurationEntry)
    root_configuration_saved_as: Signal = Signal(str, str)

    _log_entry_available: Signal = Signal(LogEntry)

    _file_format_dialog_filters: FileFormatDialogFilters
    _settings: QSettings

    _entry: RootConfigurationEntry

    _tab_widget: QTabWidget
    _edit_tab_widget: AttributesContainerWidget
    _raw_widget: QPlainTextEdit

    _logs_widget: LogsWidget
    _progress_bar: QProgressBar
    _thread_running: bool

    def __init__(
        self,
        settings: QSettings,
        entry: RootConfigurationEntry,
        parent: Optional[QWidget] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize self.

        Args:
            settings: application settings
            entry: a root configuration entry
            parent: a parent widget
            args: extra arguments
            kwargs: extra keyword arguments
        """
        super().__init__(
            parent,
            *args,
            **kwargs,
        )
        self._entry = entry
        self._settings = settings
        self._file_format_dialog_filters = FileFormatDialogFilters(
            formats=AVAILABLE_FORMATS,
        )
        self._init_ui()
        self._on_entry_changed()
        as_signal_instance(self._log_entry_available).connect(
            self._on_log_entry_available,
        )
        self._thread_running = False

    def set_entry(
        self,
        entry: RootConfigurationEntry,
    ) -> None:
        """
        Set the entry.

        Args:
            entry: an entry
        """
        self._entry = entry
        self._on_entry_changed()

    def _on_entry_changed(
        self,
        update_raw: bool = True,
    ) -> None:
        self._edit_tab_widget.set_container(
            container=self._entry.configuration,
        )
        self._edit_tab_widget.setEnabled(self._entry.configuration is not None)
        self._validate_entry()
        if update_raw:
            self._update_raw_widget()

    def _init_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(self)

        self._tab_widget = QTabWidget(self)

        self._edit_tab_widget = self._create_edit_tab_widget()
        self._tab_widget.addTab(
            self._wrap_in_scroll_area(
                widget=self._edit_tab_widget,
            ),
            'Configuration',
        )
        raw_tab_widget = self._create_raw_tab_widget()
        self._tab_widget.addTab(
            raw_tab_widget,
            f'Raw ({self._entry.raw_format})',
        )

        self._logs_widget = LogsWidget(self)

        self._progress_bar = self._create_progress_bar()

        splitter = self._create_splitter()

        layout.addWidget(splitter)

    def _create_edit_tab_widget(
        self,
    ) -> AttributesContainerWidget:
        widget = AttributesContainerWidget(
            parent=self,
            container_class=RootConfiguration,
            container=self._entry.configuration,
        )
        as_signal_instance(widget.container_changed).connect(
            self._on_root_configuration_modified,
        )
        return widget

    def _create_progress_bar(
        self,
    ) -> QProgressBar:
        widget = QProgressBar(self)
        widget.setRange(0, 100)
        widget.setFixedHeight(15)
        return widget

    def _create_splitter(
        self,
    ) -> QSplitter:
        splitter = QSplitter(
            Qt.Vertical,
            self,
        )
        splitter.addWidget(self._tab_widget)
        splitter.addWidget(self._logs_widget)
        splitter.addWidget(self._progress_bar)
        splitter.setCollapsible(0, False)  # noqa: WPS425
        splitter.setCollapsible(1, False)  # noqa: WPS425
        splitter.setCollapsible(2, False)  # noqa: WPS425
        splitter.setStretchFactor(0, 98)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        return splitter

    def _wrap_in_scroll_area(
        self,
        widget: QWidget,
    ) -> QScrollArea:
        scroll_area = QScrollArea(self)
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)
        return scroll_area

    def _on_root_configuration_modified(
        self,
        configuration: RootConfiguration,
    ) -> None:
        self._entry.configuration = configuration
        self._validate_entry()
        self._update_raw_widget()
        as_signal_instance(self.root_configuration_modified).emit(
            self._entry,
        )

    def _create_raw_tab_widget(
        self,
    ) -> QWidget:
        layout = QVBoxLayout()
        self._raw_widget = self._create_raw_widget()
        layout.addWidget(self._raw_widget, 1)

        widget = QWidget(self)
        widget.setLayout(layout)
        return widget

    def _create_raw_widget(
        self,
    ) -> QWidget:
        widget = QPlainTextEdit(self)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setFixedPitch(True)
        metrics = QFontMetrics(font)
        widget.setFont(font)
        widget.setTabStopDistance(2 * metrics.width(' '))
        as_signal_instance(widget.textChanged).connect(
            self._on_raw_changed,
        )
        return widget

    def _on_raw_changed(
        self,
    ) -> None:
        raw = self._raw_widget.toPlainText()
        try:
            self._entry.raw = raw
        except CoreException as e:
            self._log(
                log_type=LogType.error,
                message=_format_error(
                    error=e,
                ),
            )
        self._on_entry_changed(
            update_raw=False,
        )
        as_signal_instance(self.root_configuration_modified).emit(
            self._entry,
        )

    def _validate_entry(
        self,
    ) -> None:
        if not self._entry.configuration:
            return
        try:
            self._entry.configuration.validate()
        except CoreException as e:
            self._log(
                log_type=LogType.error,
                message=_format_error(
                    error=e,
                ),
            )
        else:
            self._log(
                log_type=LogType.success,
                message='Valid',
            )

    def _on_log_entry_available(
        self,
        log_entry: LogEntry,
    ) -> None:
        self._logs_widget.add_log_entry(
            entry=log_entry,
        )

    def _log(
        self,
        message: str,
        log_type: LogType = LogType.standard,
    ) -> None:
        self._logs_widget.add_log_entry(
            entry=LogEntry(
                date_time=datetime.now(),
                context=self._entry.name,
                message=message,
                log_type=log_type,
            ),
        )

    def _get_loader(
        self,
    ) -> RootConfigurationLoader:
        return get_root_configuration_loader(
            file_format=self._entry.raw_format,
        )

    def _update_raw_widget(
        self,
    ) -> None:
        plain_text = self._entry.raw
        self._raw_widget.blockSignals(True)
        cursor = self._raw_widget.textCursor()
        position = cursor.position()
        self._raw_widget.setPlainText(plain_text)
        cursor.setPosition(min(position, len(plain_text)))
        self._raw_widget.setTextCursor(cursor)
        self._raw_widget.blockSignals(False)

    def _get_last_opened_dir(
        self,
    ) -> str:
        return QFileInfo(
            cast(str, self._settings.value('last_opened_file')),
        ).dir().path()

    def save(
        self,
    ) -> None:
        """Engage the saving process."""
        entry = self._entry
        save_invalid = self._prompt_save_invalid_entry(
            entry=entry,
        )
        if not save_invalid:
            return
        path_format = self._prompt_save_path_format(
            entry=entry,
        )
        if not path_format:
            return
        file_path, file_format = path_format
        if entry.configuration is None:
            entry.configuration = RootConfiguration()
        saved = self._save_to_file(
            entry=entry,
            file_path=file_path,
            file_format=file_format,
        )
        if not saved:
            return
        self._setup_entry_from_saved_file(
            file_info=QFileInfo(file_path),
            file_format=file_format,
        )
        self._log(
            log_type=LogType.success,
            message=f'{self._entry.name} saved',
        )

    def save_as(
        self,
    ) -> None:
        """Engage the saving process into a new file."""
        entry = self._entry
        save_invalid = self._prompt_save_invalid_entry(
            entry=entry,
        )
        if not save_invalid:
            return
        path_format = self._prompt_new_file(
            format_filters=self._file_format_dialog_filters.get_filters_string(),
        )
        if not path_format:
            return
        file_path, file_format = path_format
        if entry.configuration is None:
            entry.configuration = RootConfiguration()
        saved = self._save_to_file(
            entry=entry,
            file_path=file_path,
            file_format=file_format,
        )
        if not saved:
            return
        as_signal_instance(self.root_configuration_saved_as).emit(
            file_path,
            file_format,
        )

    def _setup_entry_from_saved_file(
        self,
        file_info: QFileInfo,
        file_format: str,
    ) -> None:
        self._entry.file = RootConfigurationEntryFile(
            info=file_info,
            file_format=file_format,
            checksum=file_checksum(file_info.filePath()),
        )
        self._entry.name = file_info.fileName()
        self._entry.original_raw = self._entry.raw
        as_signal_instance(self.root_configuration_modified).emit(
            self._entry,
        )
        as_signal_instance(self.root_configuration_saved).emit(
            self._entry,
        )

    def test(
        self,
    ) -> None:
        """Test the configuration."""
        entry = self._entry
        if self._thread_running or not entry.configuration or not entry.configuration.is_valid():
            return
        thread = TesterThread(
            parent=self,
            entry=entry,
            log_entry_available_signal=as_signal_instance(self._log_entry_available),
        )
        as_signal_instance(thread.test_started).connect(
            self._on_thread_started,
        )
        as_signal_instance(thread.test_ended).connect(
            self._on_thread_ended,
        )
        thread.start()

    def synchronize(
        self,
    ) -> None:
        """Synchronize the configuration."""
        entry = self._entry
        if self._thread_running or not entry.configuration or not entry.configuration.is_valid():
            return
        thread = SynchronizerThread(
            parent=self,
            entry=entry,
            log_entry_available_signal=as_signal_instance(self._log_entry_available),
        )
        as_signal_instance(thread.synchronization_started).connect(
            self._on_thread_started,
        )
        as_signal_instance(thread.synchronization_ended).connect(
            self._on_thread_ended,
        )
        thread.start()

    def _on_thread_started(
        self,
    ) -> None:
        self._thread_running = True
        self._progress_bar.setRange(0, 0)

    def _on_thread_ended(
        self,
    ) -> None:
        self._progress_bar.setRange(0, 100)
        self._progress_bar.reset()
        self._thread_running = False

    def _prompt_save_invalid_entry(
        self,
        entry: RootConfigurationEntry,
    ) -> bool:
        error_message = None
        if entry.configuration is None:
            error_message = 'Are you sure you want to save an empty configuration?'
        elif not entry.configuration.is_valid():
            error_message = 'Are you sure you want to save an invalid configuration?'
        if error_message:
            reply = QMessageBox.question(
                self,
                f'Save {entry.name}',
                error_message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return False
        return True

    def _prompt_save_path_format(
        self,
        entry: RootConfigurationEntry,
    ) -> Optional[Tuple[str, str]]:
        if entry.file:
            exists = entry.file.info.exists()
            changed = entry.file.checksum != file_checksum(entry.file.info.filePath())
            if exists and changed:
                overwrite = self._prompt_overwrite_changed_file(
                    entry=entry,
                )
                if not overwrite:
                    return None
            file_path = entry.file.info.filePath()
            file_format = entry.file.file_format
        else:
            new_file = self._prompt_new_file(
                format_filters=self._file_format_dialog_filters.get_filters_string_for(
                    format_name=self._entry.raw_format,
                ) or '',
            )
            if not new_file:
                return None
            file_path, file_format = new_file
        return file_path, file_format

    def _prompt_overwrite_changed_file(
        self,
        entry: RootConfigurationEntry,
    ) -> bool:
        if not entry.file:
            return False
        reply = QMessageBox.question(
            self,
            f'Overwrite {entry.name}',
            f'{entry.file.info.filePath()} has changed on the disk.\nOverwrite?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def _prompt_new_file(
        self,
        format_filters: str,
    ) -> Optional[Tuple[str, str]]:
        last_opened_dir = self._get_last_opened_dir()
        file_path, chosen_filter = QFileDialog.getSaveFileName(
            self,
            'New file',
            last_opened_dir,
            format_filters or '',
        )
        if not file_path or not chosen_filter:
            return None
        file_format = self._file_format_dialog_filters.get_format_name(
            filter_string=chosen_filter,
        )
        if not file_format:
            return None
        return file_path, file_format

    def _save_to_file(
        self,
        entry: RootConfigurationEntry,
        file_path: str,
        file_format: str,
    ) -> bool:
        if not entry.configuration:
            return False
        loader = self._get_root_configuration_loader(
            file_format=file_format,
        )
        if not loader:
            return False
        try:
            with open(file_path, 'w') as destination_file:
                loader.save(
                    data=entry.configuration,
                    stream=destination_file,
                )
        except (IOError, CoreException) as save_error:
            self.show_exception_dialog(
                parent=self,
                text='Save error',
                informative_text=f'Unable to save file:\n{file_path}',
                exception=save_error,
            )
            return False
        return True

    def _get_root_configuration_loader(
        self,
        file_format: str,
    ) -> Optional[RootConfigurationLoader]:
        try:
            return get_root_configuration_loader(
                file_format=file_format,
            )
        except CoreException as loader_error:
            self.show_exception_dialog(
                parent=self,
                text='Loader error',
                informative_text=f'Unable to get loader for {file_format}',
                exception=loader_error,
            )
        return None


def _format_error(
    error: Exception,
) -> str:
    error_stream = StringIO()
    print_error(
        stream=error_stream,
        error=error,
    )
    return error_stream.getvalue()
