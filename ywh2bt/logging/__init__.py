import logging
import coloredlogs
import os
import urllib3

__all__ = ["_setup_logger", "logger"]
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

"""
Logging Module.
"""


def _setup_logger(level="INFO"):
    """
    Setup a Color Logger.

    :param str level: Logging level.
    """
    logging.getLogger().setLevel("ERROR")

    logger = logging.getLogger(__name__)

    fmt = "[%(levelname)s] %(asctime)s %(message)s"
    datefmt = "%m/%d/%Y %H:%M:%S"

    FIELD_STYLES = dict(
        asctime=dict(color="green"),
        levelname=dict(color="magenta", bold=coloredlogs.CAN_USE_BOLD_FONT),
    )

    LEVEL_STYLES = dict(
        debug=dict(color="green"),
        info=dict(color="cyan"),
        verbose=dict(color="blue"),
        warning=dict(color="yellow"),
        error=dict(color="red"),
        critical=dict(color="red", bold=coloredlogs.CAN_USE_BOLD_FONT),
    )
    coloredlogs.install(
        level=level,
        logger=logger,
        reconfigure=False,
        fmt=fmt,
        datefmt=datefmt,
        level_styles=LEVEL_STYLES,
        field_styles=FIELD_STYLES,
    )
    logger.propagate = False
    return logger


if not locals().get("logger", None):
    logger = _setup_logger()
