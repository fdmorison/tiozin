import logging
import sys
import warnings
from typing import Any

import structlog
from structlog.dev import Column, ConsoleRenderer, KeyValueColumnFormatter
from structlog.typing import EventDict, Processor

from tiozin import config, utils

from .redactor import SecretRedactor

CONTEXT_WIDTH = 15
ROOT_CONTEXT_NAME = "tiozin_app"


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
                self._context_tagger,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.TimeStamper(fmt=config.log_date_format, utc=True),
                structlog.dev.set_exc_info,
                *self._renderer_chain,
            ],
            wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # schema is a legitimate tiozin domain field; renaming it to dodge pydantic's deprecated
        # schema() compatibility warning would be unnecessary churn.
        warnings.filterwarnings(
            "ignore",
            message=r'Field name "schema" in .* shadows an attribute in parent .*',
            category=UserWarning,
        )

        self._ready = True

    def get_logger(self, name: str) -> logging.Logger:
        return structlog.get_logger(f"tiozin.{name}")

    def register_sensitive(self, value: str) -> None:
        self._redactor.add(value)

    @property
    def _renderer_chain(self) -> list[Processor]:
        if config.log_json:
            return [
                structlog.processors.format_exc_info,
                self._json_renderer,
            ]
        return [self._console_renderer]

    @property
    def _json_renderer(self) -> structlog.processors.JSONRenderer:
        return structlog.processors.JSONRenderer(
            ensure_ascii=config.log_json_ensure_ascii,
        )

    @property
    def _console_renderer(self) -> ConsoleRenderer:
        renderer = ConsoleRenderer(
            colors=True,
            sort_keys=False,
            exception_formatter=structlog.dev.RichTracebackFormatter(
                show_locals=config.log_show_locals
            ),
        )
        styles = ConsoleRenderer.get_default_column_styles(colors=True)
        extras, timestamp, level, *_ = renderer.columns
        context = Column(
            "context",
            KeyValueColumnFormatter(
                key_style=None,
                value_style=styles.logger_name,
                reset_style=styles.reset,
                width=CONTEXT_WIDTH,
                prefix="[",
                postfix="]",
                value_repr=str,
            ),
        )
        message = Column(
            "event",
            KeyValueColumnFormatter(
                key_style=None,
                value_style="",
                reset_style=styles.reset,
                value_repr=str,
            ),
        )
        renderer.columns = [extras, timestamp, level, context, message]
        return renderer

    @property
    def _context_tagger(self) -> Processor:
        def add_context_tags(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
            context = utils.try_current_context()

            if context is None:
                event_dict["context"] = ROOT_CONTEXT_NAME
                return event_dict

            event_dict["context"] = context.runner.slug if context.is_job else context.slug

            if config.log_json:
                event_dict["run_id"] = context.run_id
                event_dict["job"] = context.job.slug if context.job else None

                if context.is_step:
                    event_dict["step"] = context.slug

                event_dict["owner"] = context.owner
                event_dict["maintainer"] = context.maintainer
                event_dict["cost_center"] = context.cost_center
                event_dict.update(context.labels)
                event_dict.update(context.to_resource_dict())

            return event_dict

        return add_context_tags


log_service = LogService()
log_service.setup()
