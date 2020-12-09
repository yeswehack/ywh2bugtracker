"""Models and functions used for attributes container dict entry GUI."""
from typing import Any, Optional

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QFormLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from ywh2bt.core.configuration.attribute import AttributesContainer
from ywh2bt.gui.widgets.attribute.attributes_container_dict_entry import AttributesContainerDictEntry
from ywh2bt.gui.widgets.attribute.attributes_container_widget import AttributesContainerWidget
from ywh2bt.gui.widgets.typing import as_signal_instance


class AttributesContainerDictEntryWidget(QWidget):
    """Attributes container dict entry GUI."""

    key_changed: Signal = Signal(AttributesContainerDictEntry)
    value_changed: Signal = Signal(AttributesContainerDictEntry)

    _entry: AttributesContainerDictEntry
    _key_line_edit: QLineEdit
    _value_widget: AttributesContainerWidget

    def __init__(
        self,
        entry: AttributesContainerDictEntry,
        parent: Optional[QWidget] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize self.

        Args:
            entry: an entry
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
        self._init_ui()

    def _init_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        key_label = QLabel(
            'Key:',
            self,
        )
        self._key_line_edit = self._create_key_widget()
        self._key_line_edit.setText(self._entry.key)
        self._value_widget = self._create_value_widget()

        form_layout.addRow(key_label, self._key_line_edit)
        form_layout.addRow(self._value_widget)

        layout.addLayout(form_layout, 1)
        layout.addStretch(1)

    def _create_key_widget(
        self,
    ) -> QLineEdit:
        widget = QLineEdit(self)
        as_signal_instance(widget.textEdited).connect(
            self._on_key_changed,
        )
        return widget

    def _on_key_changed(
        self,
        value: str,
    ) -> None:
        self._entry.key = value
        as_signal_instance(self.key_changed).emit(
            self._entry,
        )

    def _create_value_widget(
        self,
    ) -> AttributesContainerWidget:
        widget = AttributesContainerWidget(
            parent=self,
            container_class=self._entry.value.__class__,
            container=self._entry.value,
        )
        as_signal_instance(widget.container_changed).connect(
            self._on_value_changed,
        )
        return widget

    def _on_value_changed(
        self,
        value: AttributesContainer,
    ) -> None:
        self._entry.value = value
        as_signal_instance(self.value_changed).emit(
            self._entry,
        )
