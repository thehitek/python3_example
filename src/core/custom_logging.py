import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
import os
from xml.sax import handler

from src.core.config import Settings

logger_app = logging.getLogger("app")  # создать логгер приложения


def logs_init(settings: Settings):
    log_dir_path = "logs"
    log_level = settings.LOG_LEVEL.upper()
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path)

    # handler = TimedRotatingFileHandler(
    #     log_dir_path + "/current.log",
    #     backupCount=7,
    #     when="midnight",
    #     utc=True,
    #     encoding="utf-8",
    # )

    handler = RotatingFileHandler(
        os.path.join(log_dir_path, "app.log"),
        backupCount=10,
        maxBytes=1024*1024*100,
        encoding="utf-8"
    )

    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    logger_access_uvicorn = logging.getLogger("uvicorn.access")
    if logger_access_uvicorn is not None:
        logger_access_uvicorn.setLevel(log_level)
        logger_access_uvicorn.addHandler(handler)

    logger_error_uvicorn = logging.getLogger("uvicorn.error")
    if logger_error_uvicorn is not None:
        logger_error_uvicorn.setLevel(log_level)
        logger_error_uvicorn.addHandler(handler)

    logger_sqlalchemy = logging.getLogger("sqlalchemy")
    if logger_sqlalchemy is not None:
        logger_sqlalchemy.setLevel(log_level)
        logger_sqlalchemy.addHandler(handler)

    if logger_app is not None:
        logger_app.setLevel(log_level)
        logger_app.addHandler(handler)


def debug(msg, *args, **kwargs):
    logger_app.debug(msg=msg)


def info(msg, *args, **kwargs):
    logger_app.info(msg=msg)


def warning(msg, *args, **kwargs):
    logger_app.warning(msg=msg)


def warn(msg, *args, **kwargs):
    logger_app.warn(msg=msg)


def error(msg, *args, **kwargs):
    logger_app.error(msg=msg)


def critical(msg, *args, **kwargs):
    logger_app.critical(msg=msg)


def exception(msg, *args, **kwargs):
    logger_app.exception(msg=msg)
