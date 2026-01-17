import logging

import structlog

from . import config

CONSOLE_RENDERER = structlog.dev.ConsoleRenderer(colors=True)
JSON_RENDERER = structlog.processors.JSONRenderer(ensure_ascii=config.log_json_ensure_ascii)


def get_logger(name: str) -> logging.Logger:
    return structlog.get_logger(name)


def setup() -> None:
    logging.basicConfig(
        level=config.log_level,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt=config.log_date_format, utc=True),
            structlog.dev.set_exc_info,
            JSON_RENDERER if config.log_json else CONSOLE_RENDERER,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
