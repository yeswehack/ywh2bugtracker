"""Models and functions used for attributes container list GUI."""
from typing import Any, Optional, Type

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QHBoxLayout, QLayout, QPushButton, QTabWidget, QVBoxLayout, QWidget

from ywh2bt.core.configuration.attribute import AttributesContainer, AttributesContainerList
from ywh2bt.gui.widgets import constants
from ywh2bt.gui.widgets.tab_widget_helper import object_to_tab_title
from ywh2bt.gui.widgets.typing import as_signal_instance

T_AC = AttributesContainer
T_ACL = AttributesContainerList[T_AC]


class AttributesContainerListWidget(QWidget):
    """Attributes container list GUI."""

    container_list_changed: Signal = Signal(AttributesContainerList)
    _container_list_class: Type[T_ACL]
    _container_list: Optional[T_ACL]

    _empty_widget: QWidget
    _tab_widget: QTabWidget

    def __init__(
        self,
        container_list_class: Type[T_ACL],
        container_list: Optional[T_ACL] = None,
        parent: Optional[QWidget] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize self.

        Args:
            container_list_class: a concrete class extending AttributesContainerList
            container_list: an attributes container list
            parent: a parent widget
            args: extra arguments
            kwargs: extra keyword arguments
        """
        super().__init__(
            parent,
            *args,
            **kwargs,
        )
        self._container_list_class = container_list_class
        self._container_list = None
        self._init_ui()
        self.set_container_list(
            container_list=container_list,
        )

    def set_container_list(
        self,
        container_list: Optional[T_ACL],
    ) -> None:
        """
        Set the container list.

        Args:
            container_list: a container list
        """
        self._container_list = container_list
        if container_list is None:
            return
        for container in container_list:
            self._add_tab(
                container=container,
            )

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)

        self._tab_widget = self._create_tab_widget()
        self._empty_widget = self._create_empty_widget()

        layout.addWidget(self._empty_widget)
        layout.addWidget(self._tab_widget)
        layout.setMargin(0)

        self._auto_show_hide_tabs()

    def _create_empty_widget(
        self,
    ) -> QTabWidget:
        return self._create_buttons_widget()

    def _create_tab_widget(
        self,
    ) -> QTabWidget:
        widget = QTabWidget(self)
        widget.setTabsClosable(True)
        widget.setCornerWidget(self._create_buttons_widget())
        as_signal_instance(widget.tabCloseRequested).connect(
            self._on_tab_close_requested,
        )
        return widget

    def _create_buttons_widget(
        self,
    ) -> QPushButton:
        button = QPushButton(
            '+',
            self,
        )
        button.setFixedSize(constants.SMALL_BUTTON_SIZE)
        as_signal_instance(button.clicked).connect(
            self._on_add_button_clicked,
        )
        layout = QHBoxLayout()
        layout.addWidget(button, 1)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget(self)
        widget.setLayout(layout)
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

    def _on_add_button_clicked(
        self,
        checked: bool,
    ) -> None:
        new_entry = self._create_container_list_entry()
        new_tab_index = self._add_tab(
            container=new_entry,
        )
        self._tab_widget.setCurrentIndex(new_tab_index)

    def _auto_show_hide_tabs(
        self,
    ) -> None:
        if self._tab_widget.count() == 0:
            self._tab_widget.hide()
            self._empty_widget.show()
        else:
            self._tab_widget.show()
            self._empty_widget.hide()

    def _add_tab(
        self,
        container: AttributesContainer,
    ) -> int:
        from ywh2bt.gui.widgets.attribute.attributes_container_widget import AttributesContainerWidget  # noqa: WPS433
        widget = AttributesContainerWidget(
            parent=self,
            container_class=container.__class__,
            container=container,
        )
        as_signal_instance(widget.container_changed).connect(
            self._on_attributes_container_widget_changed,
        )
        title = self._attributes_container_to_tab_title(
            container=container,
        )
        tab_index = self._tab_widget.addTab(
            widget,
            title,
        )
        self._auto_show_hide_tabs()
        return tab_index

    def _on_tab_close_requested(
        self,
        tab_index: int,
    ) -> None:
        self._delete_container_list_entry(
            index=tab_index,
        )
        self._tab_widget.removeTab(tab_index)

        self._auto_show_hide_tabs()

    def _attributes_container_to_tab_title(
        self,
        container: AttributesContainer,
    ) -> str:
        if self._container_list is None:
            return 'Tab'
        title = object_to_tab_title(
            obj=container,
        )
        if not title:
            index = self._container_list.index(container)
            class_name = self._container_list.values_type.__name__
            position = index + 1
            title = f'{class_name} #{position}'
        return title

    def _on_attributes_container_widget_changed(
        self,
        container: AttributesContainer,
    ) -> None:
        if self._container_list is None:
            return
        index = self._container_list.index(container)
        self._tab_widget.setTabText(
            index,
            self._attributes_container_to_tab_title(
                container=container,
            ),
        )
        self._emit_container_list_changed_signal()

    def _create_container_list_entry(
        self,
    ) -> AttributesContainer:
        if self._container_list is None:
            self._container_list = self._container_list_class()  # type: ignore
        item_values_type = self._container_list.values_type
        entry = item_values_type()
        self._container_list.append(entry)
        self._emit_container_list_changed_signal()
        return entry

    def _delete_container_list_entry(
        self,
        index: int,
    ) -> None:
        if self._container_list is None:
            return
        self._container_list.pop(index)
        self._emit_container_list_changed_signal()

    def _emit_container_list_changed_signal(
        self,
    ) -> None:
        as_signal_instance(self.container_list_changed).emit(
            self._container_list,
        )
