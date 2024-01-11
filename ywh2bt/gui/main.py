"""Models and functions used for the main GUI."""
import argparse
import platform
import sys

import urllib3


try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    print(
        "PySide6 package not found. Did you forget to install 'gui' extra?\n -> pip install 'ywh2bt[gui]'",
        file=sys.stderr,
    )
    sys.exit(1)

# noinspection PyUnresolvedReferences
import ywh2bt.gui.resources  # noqa: F401
from ywh2bt.core.core import AVAILABLE_FORMATS
from ywh2bt.gui.settings import settings
from ywh2bt.gui.widgets.main_window import MainWindow
from ywh2bt.version import __VERSION__


if platform.system() == "Windows":
    import ctypes

urllib3.disable_warnings(
    category=urllib3.exceptions.InsecureRequestWarning,
)

DEFAULT_FORMATTER_CLASS = argparse.ArgumentDefaultsHelpFormatter
CONFIGURATION_FORMATS = list(AVAILABLE_FORMATS.keys())


def run(*args: str) -> None:
    """
    Start the main GUI.

    Args:
        args: command line arguments
    """
    if not args:
        args = tuple(sys.argv[1:])
    parsed = _parse_args(*args)

    argv = [
        "ywh2bt-gui",
        "-qwindowtitle",
        "ywh2bt",
    ]
    app = QApplication(argv)

    main_icon = QIcon(":/resources/icons/ywh2bt.png")
    app.setWindowIcon(main_icon)

    system = platform.system()
    if system == "Windows":
        # set explicit AppUserModelID ; allows custom icon in Windows taskbar
        # see https://stackoverflow.com/a/1552105/248343
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(  # type: ignore
            f"yeswehack.ywh2bt.gui.{__VERSION__}".encode("utf-8"),
        )

    main_window = MainWindow(
        settings=settings,
    )
    main_window.setObjectName("main_window")
    main_window.setWindowIcon(main_icon)
    main_window.setWindowTitle("ywh2bt")
    main_window.show()

    if parsed.config_file:
        main_window.open_file(
            file_path=parsed.config_file,
            file_format=parsed.config_format,
        )

    sys.exit(app.exec())


def _parse_args(
    *args: str,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open ywh2bt GUI",
        formatter_class=DEFAULT_FORMATTER_CLASS,
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {__VERSION__} (python {'.'.join(map(str, sys.version_info[:3]))})",  # noqa: C812
    )
    parser.add_argument(
        "--config-file",
        "-c",
        dest="config_file",
        help="path to configuration file to be opened at GUI start-up",
        required=False,
        type=str,
    )
    parser.add_argument(
        "--config-format",
        "-f",
        dest="config_format",
        help="format of configuration file",
        type=str,
        required=False,
        default="yaml",
        choices=CONFIGURATION_FORMATS,
    )

    return parser.parse_args(
        args,
    )


if __name__ == "__main__":
    run(*sys.argv[1:])
