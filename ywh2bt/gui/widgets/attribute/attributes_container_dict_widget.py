"""Models and functions used for attributes container dict GUI."""
import re
from dataclasses import dataclass
from functools import partial
from string import Template
from typing import Any, Dict, List, Optional, Tuple, Type, cast

from PySide2.QtCore import QFile, QSize, Qt, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QHBoxLayout,
    QLayout,
    QTabWidget,
    QToolButton,
    QWidget,
)

from ywh2bt.core.configuration.attribute import AttributesContainer, AttributesContainerDict
from ywh2bt.core.configuration.subtypable import SubtypableMetaclass
from ywh2bt.gui.widgets import constants
from ywh2bt.gui.widgets.attribute.attributes_container_dict_entry import AttributesContainerDictEntry
from ywh2bt.gui.widgets.typing import as_signal_instance

T_AC = AttributesContainer
T_ACD = AttributesContainerDict[T_AC]

ICON_PATH_TEMPLATES: Tuple[Template, ...] = (
    Template(':/resources/icons/types/${type_name}-2x.png'),
    Template(':/resources/icons/types/${type_name}.png'),
)


@dataclass
class _ButtonDescription:
    type_name: str
    icon_type_name: str
    entry_args: Dict[str, Any]


class AttributesContainerDictWidget(QWidget):
    """Attributes container dict GUI."""

    container_dict_changed: Signal = Signal(AttributesContainerDict)
    _container_dict_class: Type[T_ACD]
    _container_dict: Optional[T_ACD]

    _empty_widget: QWidget
    _tab_widget: QTabWidget

    def __init__(
        self,
        container_dict_class: Type[T_ACD],
        container_dict: Optional[T_ACD] = None,
        parent: Optional[QWidget] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize self.

        Args:
            container_dict_class: a concrete class extending AttributesContainerDict
            container_dict: an attributes container dict
            parent: a parent widget
            args: extra arguments
            kwargs: extra keyword arguments
        """
        super().__init__(
            parent,
            *args,
            **kwargs,
        )
        self._container_dict_class = container_dict_class
        self._container_dict = None
        self._init_ui()
        self.set_container_dict(
            container_dict=container_dict,
        )

    def set_container_dict(
        self,
        container_dict: Optional[T_ACD],
    ) -> None:
        """
        Set the container dict.

        Args:
            container_dict: a container dict
        """
        self._container_dict = container_dict
        self._remove_all_tabs()
        if container_dict is None or not isinstance(container_dict, dict):
            return
        for name, container in container_dict.items():
            entry = AttributesContainerDictEntry(
                key=name,
                value=container,
            )
            self._add_tab(
                entry=entry,
            )

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)

        self._tab_widget = self._create_tab_widget()
        self._empty_widget = self._create_empty_widget()

        self._auto_show_hide_tabs()

        layout.addWidget(self._empty_widget)
        layout.addWidget(self._tab_widget)
        layout.setMargin(0)

    def _create_empty_widget(
        self,
    ) -> QWidget:
        return self._create_buttons_widget(
            text_template=Template('Add'),
            tool_tip_template=Template('Add ${type_name}'),
            buttons_size=constants.BIG_BUTTON_SIZE,
            icons_size=constants.BIG_BUTTON_ICON_SIZE,
        )

    def _create_tab_widget(
        self,
    ) -> QTabWidget:
        corner_widget = self._create_buttons_widget(
            text_template=Template(''),
            tool_tip_template=Template('Add ${type_name}'),
            buttons_size=constants.TAB_WIDGET_CORNER_BUTTON_SIZE,
            icons_size=constants.SMALL_BUTTON_ICON_SIZE,
        )

        widget = QTabWidget(self)
        widget.setCornerWidget(corner_widget)
        widget.setTabsClosable(True)
        as_signal_instance(widget.tabCloseRequested).connect(
            self._on_tab_close_requested,
        )
        return widget

    def _create_buttons_widget(
        self,
        text_template: Template,
        tool_tip_template: Template,
        buttons_size: QSize,
        icons_size: QSize,
    ) -> QWidget:
        layout = self._create_buttons_layout(
            text_template=text_template,
            tool_tip_template=tool_tip_template,
            buttons_size=buttons_size,
            icons_size=icons_size,
        )
        margin_left, margin_top, margin_right, margin_bottom = layout.getContentsMargins()
        layout.setContentsMargins(0, margin_top, margin_right, margin_bottom)
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget

    def _create_add_button(
        self,
        icon: Optional[QIcon],
        text: Optional[str],
        tool_tip: Optional[str],
        entry_args: Dict[str, Any],
        size: QSize,
        icon_size: QSize,
    ) -> QToolButton:
        widget = QToolButton(self)
        widget.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if text:
            widget.setText(text)
        if icon:
            widget.setIcon(icon)
        if tool_tip:
            widget.setToolTip(tool_tip)
        widget.setFixedSize(size)
        widget.setIconSize(icon_size)
        as_signal_instance(widget.clicked).connect(
            partial(
                self._on_add_button_clicked,
                entry_args,
            ),
        )
        return widget

    def _get_button_descriptions(
        self,
    ) -> List[_ButtonDescription]:
        button_descriptions: List[_ButtonDescription] = []
        item_values_type = self._container_dict_class().values_type  # type: ignore
        if isinstance(item_values_type, SubtypableMetaclass):
            values_type = cast(SubtypableMetaclass, item_values_type)
            types = values_type.get_registered_subtypes()
            for type_name, type_class in types.items():
                button_descriptions.append(
                    _ButtonDescription(
                        type_name=type_name,
                        icon_type_name=f'{values_type.__name__}/{type_class.__name__}',
                        entry_args={
                            'type': type_name,
                        },
                    ),
                )
        else:
            button_descriptions.append(
                _ButtonDescription(
                    type_name=item_values_type.__name__,
                    icon_type_name=item_values_type.__name__,
                    entry_args={},
                ),
            )
        return button_descriptions

    def _create_buttons_layout(
        self,
        text_template: Template,
        tool_tip_template: Template,
        buttons_size: QSize,
        icons_size: QSize,
    ) -> QLayout:
        layout = QHBoxLayout()
        descriptions = self._get_button_descriptions()
        for description in descriptions:
            button = self._create_add_button(
                icon=self._get_type_icon(
                    type_name=description.icon_type_name,
                ),
                text=text_template.substitute(
                    type_name=description.type_name,
                ),
                tool_tip=tool_tip_template.substitute(
                    type_name=description.type_name,
                ),
                entry_args=description.entry_args,
                size=buttons_size,
                icon_size=icons_size,
            )
            layout.addWidget(button, 1)
        layout.addStretch(1)
        return layout

    def _get_type_icon(
        self,
        type_name: str,
    ) -> Optional[QIcon]:
        paths = [
            template.substitute(
                type_name=type_name,
            )
            for template in ICON_PATH_TEMPLATES
        ]
        return _try_get_icon(
            try_paths=paths,
        )

    def _on_add_button_clicked(
        self,
        entry_args: Dict[str, Any],
    ) -> None:
        entry = self._create_container_dict_entry(
            entry_args=entry_args,
        )
        new_tab_index = self._add_tab(
            entry=entry,
        )
        self._tab_widget.setCurrentIndex(new_tab_index)

    def _remove_all_tabs(
        self,
    ) -> None:
        self._tab_widget.blockSignals(True)
        while self._tab_widget.count():
            self._tab_widget.removeTab(0)
        self._tab_widget.blockSignals(False)
        self._auto_show_hide_tabs()

    def _add_tab(
        self,
        entry: AttributesContainerDictEntry,
    ) -> int:
        from ywh2bt.gui.widgets.attribute.attributes_container_dict_entry_widget import \
            AttributesContainerDictEntryWidget  # noqa: WPS433, N400

        widget = AttributesContainerDictEntryWidget(
            entry=entry,
        )
        as_signal_instance(widget.key_changed).connect(
            self._on_container_dict_entry_key_changed,
        )
        as_signal_instance(widget.value_changed).connect(
            self._on_container_dict_entry_value_changed,
        )
        tab_index = self._tab_widget.addTab(
            widget,
            entry.key,
        )
        self._auto_show_hide_tabs()
        return tab_index

    def _on_tab_close_requested(
        self,
        tab_index: int,
    ) -> None:
        if self._container_dict:
            keys = list(self._container_dict.keys())
            self._delete_container_dict_entry(
                key=keys[tab_index],
            )
            self._tab_widget.removeTab(tab_index)
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

    def _on_container_dict_entry_key_changed(
        self,
        entry: AttributesContainerDictEntry,
    ) -> None:
        if self._container_dict is None:
            return
        key_index = None
        for index, item in enumerate(self._container_dict.items()):
            key, value = item
            if value == entry.value:
                key_index = (key, index)
                break
        if not key_index:
            raise KeyError(f'Could not find old key for {entry}')
        self._container_dict.swap_key(
            old=key_index[0],
            new=entry.key,
        )
        self._tab_widget.setTabText(
            key_index[1],
            entry.key,
        )
        self._emit_container_dict_changed_signal()

    def _on_container_dict_entry_value_changed(
        self,
        entry: AttributesContainerDictEntry,
    ) -> None:
        if self._container_dict is None:
            return
        self._container_dict[entry.key] = entry.value
        self._emit_container_dict_changed_signal()

    def _create_container_dict_entry(
        self,
        entry_args: Dict[str, Any],
    ) -> AttributesContainerDictEntry:
        if not self._container_dict:
            self._container_dict = self._container_dict_class()  # type: ignore
        item_values_type = self._container_dict.values_type
        value = item_values_type(**entry_args)
        key = _get_next_available_key(
            container_dict=self._container_dict,
            value=value,
        )
        self._container_dict[key] = value
        self._emit_container_dict_changed_signal()
        return AttributesContainerDictEntry(
            key=key,
            value=value,
        )

    def _delete_container_dict_entry(
        self,
        key: str,
    ) -> None:
        if self._container_dict is None:
            return
        self._container_dict.pop(key)
        self._emit_container_dict_changed_signal()

    def _emit_container_dict_changed_signal(
        self,
    ) -> None:
        as_signal_instance(self.container_dict_changed).emit(
            self._container_dict,
        )


def _get_icon(
    path: str,
) -> Optional[QIcon]:
    if QFile.exists(path):
        return QIcon(path)
    return None


def _value_class_to_snake_case(
    value: Any,
) -> str:
    pattern = re.compile('(?<!^)(?=[A-Z])')
    return pattern.sub('_', value.__class__.__name__).lower()


def _try_get_icon(
    try_paths: List[str],
) -> Optional[QIcon]:
    for try_path in try_paths:
        icon = _get_icon(
            path=try_path,
        )
        if icon:
            return icon
    return None


def _get_next_available_key(
    container_dict: Optional[T_ACD],
    value: AttributesContainer,
) -> str:
    i = 1
    while True:
        snake = _value_class_to_snake_case(
            value=value,
        )
        key = f'{snake}_{i}'
        if not container_dict or key not in container_dict:
            return key
        i += 1
