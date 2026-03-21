import logging
import sys

import structlog
import wrapt

from tiozin import config

from .redactor import SecretRedactor


class LogService:
    """
    Singleton service responsible for configuring structured logging.

    Provides an isolated logging pipeline for Tiozin using structlog,
    without interfering with the host application's logging configuration
    (e.g. Airflow).

    Supports both JSON and console rendering.
    """

    def __init__(self, propagate: bool = False) -> None:
        self._propagate = propagate
        self._ready = False
        self._redactor = SecretRedactor()
        self._console_renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            sort_keys=False,
            exception_formatter=structlog.dev.RichTracebackFormatter(
                show_locals=config.log_show_locals
            ),
        )
        self._json_renderer = structlog.processors.JSONRenderer(
            ensure_ascii=config.log_json_ensure_ascii,
        )

    @wrapt.synchronized
    def setup(self) -> None:
        if self._ready:
            return

        logger = logging.getLogger("tiozin")
        logger.setLevel(config.log_level)
        logger.propagate = self._propagate

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)

        structlog.reset_defaults()

        structlog.configure(
            processors=[
                self._redactor,
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.TimeStamper(fmt=config.log_date_format, utc=True),
                structlog.dev.set_exc_info,
                self._json_renderer if config.log_json else self._console_renderer,
            ],
            wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        self._ready = True

    def get_logger(self, name: str) -> logging.Logger:
        return structlog.get_logger(f"tiozin.{name}")

    def register_sensitive(self, value: str) -> None:
        self._redactor.add(value)


log_service = LogService()
log_service.setup()
