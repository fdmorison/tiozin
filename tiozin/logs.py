import logging

from . import config

LOG_LEVELS = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "WARN",
    "ERROR": "ERROR",
    "CRITICAL": "FATAL",
}

LogRecordFactory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs) -> logging.LogRecord:
    record = LogRecordFactory(*args, **kwargs)
    record.levelname = LOG_LEVELS.get(record.levelname, record.levelname.upper())
    return record


def setup() -> None:
    logging.basicConfig(
        level=config.log_level,
        format=config.log_format,
        datefmt=config.log_date_format,
    )
    logging.setLogRecordFactory(record_factory)
