"""Models and functions used in error dialogs."""
from PySide2.QtWidgets import QMessageBox, QWidget

from ywh2bt.core.error import error_to_string


class ErrorDialogMixin:
    """Mixin for error and exception dialogs."""

    def show_exception_dialog(
        self,
        parent: QWidget,
        text: str,
        informative_text: str,
        exception: Exception,
    ) -> None:
        """
        Show an error dialog describing an exception.

        Args:
            parent: a parent widget
            text: a main text
            informative_text: an informative text
            exception: an exception
        """
        self.show_error_dialog(
            parent=parent,
            text=text,
            informative_text=informative_text,
            detailed_text=error_to_string(
                error=exception,
            ),
        )

    def show_error_dialog(
        self,
        parent: QWidget,
        text: str,
        informative_text: str,
        detailed_text: str,
    ) -> None:
        """
        Show an error dialog.

        Args:
            parent: a parent widget
            text: a main text
            informative_text: an informative text
            detailed_text: a detailed text
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setText(f'<b>{text}</b>')
        dialog.setInformativeText(informative_text)
        dialog.setDetailedText(detailed_text)
        dialog.show()
