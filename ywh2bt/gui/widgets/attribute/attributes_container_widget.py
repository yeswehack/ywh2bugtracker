"""Models and functions used for attributes container GUI."""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Any, Dict, Optional, Type, TypeVar, Union, cast

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)
from typing_extensions import Protocol

from ywh2bt.core.configuration.attribute import (
    Attribute,
    AttributesContainer,
    AttributesContainerDict,
    AttributesContainerList,
    ExportableDict,
    ExportableList,
)
from ywh2bt.gui.widgets.attribute.attributes_container_dict_widget import AttributesContainerDictWidget
from ywh2bt.gui.widgets.attribute.attributes_container_list_widget import AttributesContainerListWidget
from ywh2bt.gui.widgets.attribute.exportable_dict_widget import ExportableDictModel, ExportableDictWidget
from ywh2bt.gui.widgets.attribute.exportable_list_widget import ExportableListModel, ExportableListWidget
from ywh2bt.gui.widgets.hinted_check_box_widget import HintedCheckBoxWidget
from ywh2bt.gui.widgets.secret_line_edit_widget import SecretLineEditWidget
from ywh2bt.gui.widgets.typing import as_signal_instance

T = TypeVar('T')


class _WidgetCreationProtocol(Protocol):
    def __call__(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> QWidget:
        ...  # noqa: WPS428


class _WidgetUpdateProtocol(Protocol):
    def __call__(
        self,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> QWidget:
        ...  # noqa: WPS428


@dataclass
class _WidgetProtocols:
    create: _WidgetCreationProtocol
    update: _WidgetUpdateProtocol


class AttributesContainerWidget(QWidget):  # noqa: WPS214
    """A widget for editing AttributesContainer instances."""

    container_changed: Signal = Signal(AttributesContainer)
    _container_class: Type[AttributesContainer]
    _container: Optional[AttributesContainer]

    _widget_types_protocols: Dict[
        Type[Any],
        _WidgetProtocols,
    ]

    def __init__(
        self,
        container_class: Type[AttributesContainer],
        container: Optional[AttributesContainer] = None,
        parent: Optional[QWidget] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize self.

        Args:
            container_class: a class extending AttributesContainer
            container: a container of type container_class
            parent: a parent widget
            args: extra arguments
            kwargs: extra keyword arguments
        """
        super().__init__(
            parent,
            *args,
            **kwargs,
        )
        self._container_class = container_class
        self._container = None
        self._widget_types_protocols = {
            AttributesContainer: _WidgetProtocols(
                create=self._create_attributes_container_widget,
                update=self._update_attributes_container_widget,
            ),
            AttributesContainerDict: _WidgetProtocols(
                create=self._create_attributes_container_dict_widget,
                update=self._update_attributes_container_dict_widget,
            ),
            AttributesContainerList: _WidgetProtocols(
                create=self._create_attributes_container_list_widget,
                update=self._update_attributes_container_list_widget,
            ),
            ExportableDict: _WidgetProtocols(
                create=self._create_exportable_dict_widget,
                update=self._update_exportable_dict_widget,
            ),
            ExportableList: _WidgetProtocols(
                create=self._create_exportable_list_widget,
                update=self._update_exportable_list_widget,
            ),
            str: _WidgetProtocols(
                create=self._create_line_edit_widget,
                update=self._update_line_edit_widget,
            ),
            bool: _WidgetProtocols(
                create=self._create_check_box_widget,
                update=self._update_check_box_widget,
            ),
        }
        self._init_ui()
        self.set_container(
            container=container,
        )

    def set_container(
        self,
        container: Optional[AttributesContainer],
    ) -> None:
        """
        Set the container to be edited.

        Args:
            container: a container
        """
        self._container = container
        for name, attribute in self._container_class.get_attributes().items():
            value = getattr(container, name) if container else None
            self._update_attribute_widget(
                name=name,
                attribute=attribute,
                value=value,
            )

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        form_layout = self._create_form_layout()
        layout.addLayout(form_layout, 1)
        layout.addStretch(1)

    def _create_form_layout(
        self,
    ) -> QFormLayout:
        layout = QFormLayout()
        for name, attribute in self._container_class.get_attributes().items():
            label = self._create_label_widget(
                name=name,
                attribute=attribute,
            )
            field = self._create_field_widget(
                name=name,
                attribute=attribute,
            )
            tool_tip = self._get_tool_tip(
                attribute=attribute,
            )
            if tool_tip:
                label.setToolTip(tool_tip)
                label.setStatusTip(tool_tip)

            layout.addRow(label, field)
        return layout

    def _create_label_widget(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> QLabel:
        widget = QLabel(self)
        widget.setTextFormat(Qt.RichText)
        text = attribute.short_description or name
        text = f'{text}:'
        if attribute.deprecated:
            text = f'<i><s>{text}</s></i>'
        if attribute.required:
            text = f'<b>{text}</b>'
        widget.setText(text)
        widget.setObjectName(f'label_{name}')
        return widget

    def _get_tool_tip(
        self,
        attribute: Attribute[Any],
    ) -> Optional[str]:
        lines = []
        description = ''
        if attribute.description:
            description = attribute.description
        if attribute.deprecated:
            description = f'(Deprecated)\n{description}' if description else '(Deprecated)'
        if description:
            lines.append(description)
        if attribute.default is not None:
            lines.append(f'Default: {repr(attribute.default)}')
        return '\n'.join(lines)

    def _create_field_widget(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> QWidget:
        value_type = attribute.value_type
        widget: Optional[QWidget] = None
        for known_type, protocols in self._widget_types_protocols.items():
            if issubclass(value_type, known_type):
                widget = protocols.create(
                    name=name,
                    attribute=attribute,
                )
                break
        if not widget:
            widget = QLabel(self)
            widget.setWordWrap(True)
            widget.setTextFormat(Qt.RichText)
            widget.setStyleSheet('background-color: rgba(255, 0, 0, 50%);')
            widget.setText(
                f'No field for type <b>{value_type.__name__}</b>',
            )
        widget.setObjectName(f'field_{name}')

        return widget

    def _find_field_widget(
        self,
        name: str,
        widget_type: Type[T],
    ) -> T:
        return cast(T, self.findChild(widget_type, f'field_{name}'))

    def _update_attribute_widget(
        self,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> None:
        value_type = attribute.value_type
        for known_type, protocols in self._widget_types_protocols.items():
            if issubclass(value_type, known_type):
                protocols.update(
                    name=name,
                    attribute=attribute,
                    value=value,
                )
                break

    def _create_attributes_container_widget(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> AttributesContainerWidget:
        widget = AttributesContainerWidget(
            parent=self,
            container_class=attribute.value_type,
        )
        as_signal_instance(widget.container_changed).connect(
            partial(
                self._on_attributes_container_changed,
                widget,
                name,
                attribute,
            ),
        )
        return widget

    def _update_attributes_container_widget(
        self,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> QWidget:
        widget = self._find_field_widget(
            name=name,
            widget_type=AttributesContainerWidget,
        )
        widget.set_container(
            container=value,
        )
        return widget

    def _on_attributes_container_changed(
        self,
        widget: QWidget,
        name: str,
        attribute: Attribute[Any],
        value: AttributesContainer,
    ) -> None:
        self._on_attribute_value_changed(
            widget=widget,
            name=name,
            attribute=attribute,
            value=value,
        )

    def _create_attributes_container_dict_widget(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> AttributesContainerDictWidget:
        widget = AttributesContainerDictWidget(
            parent=self,
            container_dict_class=attribute.value_type,
        )
        as_signal_instance(widget.container_dict_changed).connect(
            partial(
                self._on_attributes_container_dict_changed,
                widget,
                name,
                attribute,
            ),
        )
        return widget

    def _update_attributes_container_dict_widget(
        self,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> QWidget:
        widget = self._find_field_widget(
            name=name,
            widget_type=AttributesContainerDictWidget,
        )
        widget.set_container_dict(
            container_dict=value,
        )
        return widget

    def _on_attributes_container_dict_changed(
        self,
        widget: QWidget,
        name: str,
        attribute: Attribute[Any],
        value: AttributesContainerDict[AttributesContainer],
    ) -> None:
        self._on_attribute_value_changed(
            widget=widget,
            name=name,
            attribute=attribute,
            value=value,
        )

    def _create_attributes_container_list_widget(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> AttributesContainerListWidget:
        widget = AttributesContainerListWidget(
            parent=self,
            container_list_class=attribute.value_type,
        )
        as_signal_instance(widget.container_list_changed).connect(
            partial(
                self._on_attributes_container_list_changed,
                widget,
                name,
                attribute,
            ),
        )
        return widget

    def _update_attributes_container_list_widget(
        self,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> QWidget:
        widget = self._find_field_widget(
            name=name,
            widget_type=AttributesContainerListWidget,
        )
        widget.set_container_list(
            container_list=value,
        )
        return widget

    def _on_attributes_container_list_changed(
        self,
        widget: QWidget,
        name: str,
        attribute: Attribute[Any],
        value: AttributesContainerList[AttributesContainer],
    ) -> None:
        self._on_attribute_value_changed(
            widget=widget,
            name=name,
            attribute=attribute,
            value=value,
        )

    def _create_exportable_dict_widget(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> ExportableDictWidget:
        widget = ExportableDictWidget(
            parent=self,
        )
        widget.set_model(
            model=ExportableDictModel(
                exportable_dict=attribute.value_type(),
            ),
        )
        as_signal_instance(widget.dataChanged).connect(
            partial(
                self._on_exportable_dict_changed,
                widget,
                name,
                attribute,
            ),
        )
        return widget

    def _update_exportable_dict_widget(
        self,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> QWidget:
        widget = self._find_field_widget(
            name=name,
            widget_type=ExportableDictWidget,
        )
        widget.set_model(
            model=ExportableDictModel(
                exportable_dict=value if value is not None else attribute.value_type(),
            ),
        )
        return widget

    def _on_exportable_dict_changed(
        self,
        widget: QWidget,
        name: str,
        attribute: Attribute[Any],
        value: ExportableDict[Any, Any, Any, Any],
    ) -> None:
        self._on_attribute_value_changed(
            widget=widget,
            name=name,
            attribute=attribute,
            value=value,
        )

    def _create_exportable_list_widget(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> ExportableListWidget:
        widget = ExportableListWidget(
            parent=self,
        )
        widget.set_model(
            model=ExportableListModel(
                exportable_list=attribute.value_type(),
            ),
        )
        as_signal_instance(widget.dataChanged).connect(
            partial(
                self._on_exportable_list_changed,
                widget,
                name,
                attribute,
            ),
        )
        return widget

    def _update_exportable_list_widget(
        self,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> QWidget:
        widget = self._find_field_widget(
            name=name,
            widget_type=ExportableListWidget,
        )
        widget.set_model(
            model=ExportableListModel(
                exportable_list=value if value is not None else attribute.value_type(),
            ),
        )
        return widget

    def _on_exportable_list_changed(
        self,
        widget: QWidget,
        name: str,
        attribute: Attribute[Any],
        value: ExportableList[Any, Any],
    ) -> None:
        self._on_attribute_value_changed(
            widget=widget,
            name=name,
            attribute=attribute,
            value=value,
        )

    def _create_line_edit_widget(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> QWidget:
        widget: Union[SecretLineEditWidget, QLineEdit]
        if attribute.secret:
            widget = SecretLineEditWidget(
                parent=self,
            )
            as_signal_instance(widget.text_edited).connect(
                partial(
                    self._on_line_edit_changed,
                    widget,
                    name,
                    attribute,
                ),
            )
        else:
            widget = QLineEdit(self)
            if isinstance(attribute.default, str):
                widget.setPlaceholderText(attribute.default)
            as_signal_instance(widget.textEdited).connect(
                partial(
                    self._on_line_edit_changed,
                    widget,
                    name,
                    attribute,
                ),
            )
        return widget

    def _update_line_edit_widget(
        self,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> QWidget:
        if attribute.secret:
            widget = self._find_field_widget(
                name=name,
                widget_type=SecretLineEditWidget,
            )
        else:
            widget = self._find_field_widget(
                name=name,
                widget_type=QLineEdit,
            )
        if value != attribute.default:
            widget.setText(value)
        return widget

    def _on_line_edit_changed(
        self,
        widget: QWidget,
        name: str,
        attribute: Attribute[Any],
        value: str,
    ) -> None:
        clean_value: Optional[str] = value
        if not clean_value:
            clean_value = None
        self._on_attribute_value_changed(
            widget=widget,
            name=name,
            attribute=attribute,
            value=clean_value,
        )

    def _create_check_box_widget(
        self,
        name: str,
        attribute: Attribute[Any],
    ) -> HintedCheckBoxWidget:
        widget = HintedCheckBoxWidget(self)
        widget.setTristate(True)
        default_hint = 'Yes' if attribute.default else 'No'
        widget.set_state_hint(Qt.PartiallyChecked, f'Default: {default_hint}')
        widget.setCheckState(Qt.PartiallyChecked)
        as_signal_instance(widget.stateChanged).connect(
            partial(
                self._on_check_box_changed,
                widget,
                name,
                attribute,
            ),
        )
        return widget

    def _update_check_box_widget(
        self,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> QWidget:
        state = Qt.Checked if value else Qt.Unchecked
        if value == attribute.default:
            state = Qt.PartiallyChecked
        widget = self._find_field_widget(
            name=name,
            widget_type=HintedCheckBoxWidget,
        )
        widget.setCheckState(state)
        return widget

    def _on_check_box_changed(
        self,
        widget: QWidget,
        name: str,
        attribute: Attribute[Any],
        state: Qt.CheckState,
    ) -> None:
        value = None
        if state != Qt.PartiallyChecked:
            value = state == Qt.Checked
        self._on_attribute_value_changed(
            widget=widget,
            name=name,
            attribute=attribute,
            value=value,
        )

    def _on_attribute_value_changed(
        self,
        widget: QWidget,
        name: str,
        attribute: Attribute[Any],
        value: Any,
    ) -> None:
        if self._container is None:
            self._container = self._container_class()
        setattr(self._container, name, value)
        as_signal_instance(self.container_changed).emit(self._container)
