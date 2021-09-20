"""Models and functions used for exportable dict GUI."""
from __future__ import annotations

from functools import partial
from typing import Any, List, Optional, Set, cast

from PySide2.QtCore import QAbstractTableModel, QItemSelection, QModelIndex, Qt, Signal
from PySide2.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLayout,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ywh2bt.core.configuration.attribute import ExportableDict
from ywh2bt.gui.widgets import constants
from ywh2bt.gui.widgets.typing import as_signal_instance


class ExportableDictWidget(QWidget):  # noqa: WPS214
    """Exportable dict GUI."""

    dataChanged: Signal = Signal(ExportableDict)  # noqa: WPS115, N815

    _table: QTableView
    _add_button: QPushButton
    _del_button: QPushButton

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
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)

        self._table = self._create_table()

        self._add_button = self._create_add_button()
        self._del_button = self._create_del_button()

        buttons_layout = self._create_buttons_layout(
            self._add_button,
            self._del_button,
        )

        layout.addWidget(self._table)
        layout.addLayout(buttons_layout)
        layout.setMargin(0)

    def _create_table(
        self,
    ) -> QTableView:
        widget = QTableView(self)
        widget.horizontalHeader().hide()
        widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        widget.setEditTriggers(
            QAbstractItemView.AllEditTriggers,
        )
        return widget

    def _create_add_button(
        self,
    ) -> QPushButton:
        widget = QPushButton(
            '+',
            self,
        )
        widget.setFixedSize(constants.SMALL_BUTTON_SIZE)
        as_signal_instance(widget.clicked).connect(
            self._on_add_button_clicked,
        )
        return widget

    def _create_del_button(
        self,
    ) -> QPushButton:
        widget = QPushButton(
            '-',
            self,
        )
        widget.setFixedSize(constants.SMALL_BUTTON_SIZE)
        widget.setEnabled(False)
        as_signal_instance(widget.clicked).connect(
            self._on_del_button_clicked,
        )
        return widget

    def _create_buttons_layout(
        self,
        *buttons: QPushButton,
    ) -> QLayout:
        layout = QVBoxLayout()
        for button in buttons:
            layout.addWidget(button, 1)
        layout.addStretch(1)
        return layout

    def set_model(
        self,
        model: ExportableDictModel,
    ) -> None:
        """
        Set the model.

        Args:
            model: an exportable dict model
        """
        signals = {
            model.dataChanged,
            model.rowsInserted,
            model.rowsRemoved,
        }
        for signal in signals:
            as_signal_instance(signal).connect(
                partial(
                    self._on_model_data_changed,
                    model,
                ),
            )
        self._table.setModel(model)
        selection_model = self._table.selectionModel()
        as_signal_instance(selection_model.selectionChanged).connect(
            self._on_selection_changed,
        )

    def _on_model_data_changed(
        self,
        model: ExportableDictModel,
        top_left: QModelIndex,
        bottom_right: QModelIndex,
        roles: List[int],
    ) -> None:
        as_signal_instance(self.dataChanged).emit(model.get_value())

    def _on_selection_changed(
        self,
        selected: QItemSelection,
        unselected: QItemSelection,
    ) -> None:
        has_selection = selected.count() != 0
        self._del_button.setEnabled(has_selection)

    def _on_add_button_clicked(
        self,
        checked: bool,
    ) -> None:
        model = self._table.model()
        model.insertRow(model.rowCount(model.index(0, 0)))
        row_count = model.rowCount(model.index(0, 0))
        self._table.selectRow(max(0, row_count - 1))

    def _on_del_button_clicked(
        self,
        checked: bool,
    ) -> None:
        selected_rows = sorted(
            self._get_select_row_indices(),
            reverse=True,
        )
        if not selected_rows:
            return
        model = self._table.model()
        for selected_row in selected_rows:
            model.removeRow(selected_row)

        row_count = model.rowCount(model.index(0, 0))
        reselect_row = min(row_count - 1, selected_rows[-1])
        self._table.selectRow(max(0, reselect_row))

    def _get_select_row_indices(
        self,
    ) -> Set[int]:
        selection_model = self._table.selectionModel()
        return set({
            index.row() for index in selection_model.selectedIndexes()
        })


class ExportableDictModel(QAbstractTableModel):
    """Exportable dict model."""

    _exportable_dict: ExportableDict[Any, Any, Any, Any]

    def __init__(
        self,
        exportable_dict: ExportableDict[Any, Any, Any, Any],
    ) -> None:
        """
        Initialize self.

        Args:
            exportable_dict: an exportable dict
        """
        super().__init__()
        self._exportable_dict = exportable_dict

    def get_value(
        self,
    ) -> Optional[ExportableDict[Any, Any, Any, Any]]:
        """
        Get the underlying exportable dict.

        Returns:
            The exportable dict
        """
        return self._exportable_dict

    def data(  # type: ignore
        self,
        index: QModelIndex,
        role: int,
    ) -> Any:
        """
        Get data at the given index for the given role.

        Args:
            index: a data index
            role: a data role

        Returns:
            The data
        """
        return_conditions = (
            self._exportable_dict is None,
            not index.isValid(),
            index.column() not in {0, 1},
        )
        if any(return_conditions):
            return None
        if role in {Qt.DisplayRole, Qt.EditRole}:
            data = [
                list(self._exportable_dict.keys()),
                list(self._exportable_dict.values()),
            ]
            return data[index.column()][index.row()]
        return None

    def setData(  # type: ignore # noqa: N802
        self,
        index: QModelIndex,
        value: Any,
        role: int,
    ) -> bool:
        """
        Set data at the given index for the given role.

        Args:
            index: a data index
            value: a value
            role: a role

        Returns:
            True if the data has been set, otherwise False
        """
        if self._exportable_dict is None or not index.isValid() or role != Qt.EditRole:
            return False
        existing_keys = list(self._exportable_dict.keys())
        key = existing_keys[index.row()]
        if index.column() == 0:
            if value in existing_keys:
                return False
            self._exportable_dict.swap_key(
                old=key,
                new=value,
            )
            self.dataChanged.emit(index, index)
            return True
        elif index.column() == 1:
            self._exportable_dict[key] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def rowCount(  # type: ignore # noqa: N802
        self,
        index: QModelIndex,
    ) -> int:
        """
        Get the number of rows/entries in the underlying exportable dict.

        Args:
            index: a data index for the parent data, if any

        Returns:
            The number of rows
        """
        return len(self._exportable_dict) if self._exportable_dict is not None else 0

    def columnCount(  # type: ignore # noqa: N802
        self,
        index: QModelIndex,
    ) -> int:
        """
        Get the number of columns in the underlying exportable dict, which is always 2 (key and value).

        Args:
            index: a data index for the parent data, if any

        Returns:
            The number of columns
        """
        return 2

    def flags(
        self,
        index: QModelIndex,
    ) -> Qt.ItemFlags:
        """
        Get the flags for the given index.

        Args:
            index: a data index

        Returns:
            The flags
        """
        if not index.isValid():
            return Qt.ItemIsEnabled

        return cast(Qt.ItemFlags, super().flags(index) | Qt.ItemIsEditable)

    def insertRows(  # type: ignore # noqa: N802
        self,
        row: int,
        count: int,
        parent: QModelIndex,
    ) -> bool:
        """
        Insert a number of rows before a given row.

        If row is 0, the rows are prepended to any existing rows in the parent.

        If row is rowCount(), the rows are appended to any existing rows in the parent.

        If parent has no children, a single column with count rows is inserted.

        Args:
            row: a row number
            count: a number of rows to be inserted
            parent: a parent index

        Returns:
            True if the rows where successfully inserted, otherwise False
        """
        self.beginInsertRows(
            parent,
            row,
            row + count - 1,
        )
        for i in range(count):
            key = self._get_next_new_available_key(
                base_index=i,
            )
            self._exportable_dict[key] = ''
        self.endInsertRows()
        return True

    def _get_next_new_available_key(
        self,
        base_index: int,
    ) -> str:
        n = 1
        while True:
            value = f'New entry {base_index + n}'
            if value not in self._exportable_dict.keys():
                return value
            n += 1

    def removeRows(  # type: ignore # noqa: N802
        self,
        row: int,
        count: int,
        parent: QModelIndex,
    ) -> bool:
        """
        Remove count rows starting with the given row under parent.

        Args:
            row: a row number
            count: a number of rows
            parent: a parent index

        Returns:
            True if the rows were successfully removed; otherwise False.
        """
        self.beginRemoveRows(
            parent,
            row,
            row + count - 1,
        )
        key = list(self._exportable_dict.keys())[row]
        self._exportable_dict = self._exportable_dict.__class__(
            {
                k: v for k, v in self._exportable_dict.items() if k != key
            },
        )
        self.endRemoveRows()
        return True
