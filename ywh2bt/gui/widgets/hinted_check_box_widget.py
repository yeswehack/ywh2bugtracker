"""Models and functions used for check box with hint."""
from typing import Any, Dict, Optional

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QWidget

from ywh2bt.gui.widgets.typing import as_signal_instance


class HintedCheckBoxWidget(QWidget):
    """A widget consisting of a checkbox with a hint."""

    stateChanged: Signal = Signal(Qt.CheckState)  # noqa: WPS115, N815

    _check_box: QCheckBox
    _label: QLabel

    _state_hints: Dict[Qt.CheckState, str]

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
        self._state_hints = {}
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)

        self._check_box = self._create_check_box()

        self._label = self._create_label()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._check_box)
        layout.addWidget(self._label)
        layout.addStretch(1)

    def _create_check_box(
        self,
    ) -> QCheckBox:
        widget = QCheckBox(self)
        as_signal_instance(widget.stateChanged).connect(
            self._on_check_box_state_changed,
        )
        return widget

    def _on_check_box_state_changed(
        self,
        state: int,
    ) -> None:
        states = {
            0: Qt.Unchecked,
            1: Qt.PartiallyChecked,
            2: Qt.Checked,
        }
        self._update_label_for_state(
            state=states[state],
        )
        as_signal_instance(self.stateChanged).emit(states[state])

    def set_state_hint(
        self,
        state: Qt.CheckState,
        hint: str,
    ) -> None:
        """
        Set a hint for a CheckState.

        Args:
            state: a state
            hint: a hint
        """
        self._state_hints[state] = hint

    def _update_label_for_state(
        self,
        state: Qt.CheckState,
    ) -> None:
        self._label.setText(self._state_hints.get(state, ''))

    def _create_label(
        self,
    ) -> QLabel:
        return QLabel(self)

    def setTristate(  # noqa: N802
        self,
        tristate: bool,
    ) -> None:
        """
        Set whether the checkbox is a tri-state checkbox.

        Args:
            tristate: a flag indicating if the checkbox is a tri-state checkbox
        """
        self._check_box.setTristate(tristate)

    def setCheckState(  # noqa: N802
        self,
        state: Qt.CheckState,
    ) -> None:
        """
        Set the checkbox's check state.

        Args:
            state: a state
        """
        self._check_box.setCheckState(state)
