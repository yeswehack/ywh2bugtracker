"""Models and functions used for the main GUI."""
import os
import platform
import sys

import urllib3  # type: ignore
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

# noinspection PyUnresolvedReferences
import ywh2bt.gui.resources  # noqa: F401, WPS301
from ywh2bt.gui.settings import settings
from ywh2bt.gui.widgets.main_window import MainWindow
from ywh2bt.version import __VERSION__

if platform.system() == 'Windows':
    import ctypes  # noqa: WPS433

urllib3.disable_warnings(
    category=urllib3.exceptions.InsecureRequestWarning,
)


def run(*argv: str) -> None:
    """
    Start the main GUI.

    Args:
        argv: command line arguments
    """
    system = platform.system()
    if system == 'Windows':
        # set explicit AppUserModelID ; allows custom icon in Windows taskbar
        # see https://stackoverflow.com/a/1552105/248343
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(  # type: ignore
            f'yeswehack.ywh2bt.gui.{__VERSION__}'.encode('utf-8'),
        )
    elif system == 'Darwin':
        # https://stackoverflow.com/a/64856281/248343
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
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
