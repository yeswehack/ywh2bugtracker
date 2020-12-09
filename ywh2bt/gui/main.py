"""Models and functions used for the main GUI."""
import sys

import urllib3  # type: ignore
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

# noinspection PyUnresolvedReferences
import ywh2bt.gui.resources  # noqa: F401, WPS301
from ywh2bt.gui.settings import settings
from ywh2bt.gui.widgets.main_window import MainWindow

urllib3.disable_warnings(
    category=urllib3.exceptions.InsecureRequestWarning,
)


def run(*argv: str) -> None:
    """
    Start the main GUI.

    Args:
        argv: command line arguments
    """
    args = [
        'ywh2bt-gui',
        *argv[1:],
    ]
    app = QApplication(args)

    main_window = MainWindow(
        settings=settings,
    )
    main_window.setObjectName('main_window')
    main_window.setWindowIcon(QIcon(':/resources/icons/ywh2bt.png'))
    main_window.setWindowTitle('ywh2bt-gui')
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run(*sys.argv)
