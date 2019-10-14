import logging
import coloredlogs
import os
def _setup_logger(level='INFO'):
    logger = logging.getLogger(__name__)
    os.environ['COLOREDLOGS_LOG_FORMAT'] = os.environ.get('COLOREDLOGS_LOG_FORMAT', '[%(levelname)s] %(asctime)s %(message)s')
    os.environ['COLOREDLOGS_DATE_FORMAT'] = os.environ.get('COLOREDLOGS_DATE_FORMAT', '%m/%d/%Y %H:%M:%S')
    coloredlogs.install(level=level, logger=logger, reconfigure=False)
    logger.propagate = False
    return logger

if not locals().get('logger', None):
    logger = _setup_logger()
