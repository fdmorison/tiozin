import logging
from typing import Any

import structlog

from . import config

BLUE = "\033[34m"
CYAN = "\033[36m"
RESET = "\033[0m"
BOLD = "\033[1m"

CONSOLE_RENDERER = structlog.dev.ConsoleRenderer(colors=True)
JSON_RENDERER = structlog.processors.JSONRenderer(ensure_ascii=config.log_json_ensure_ascii)
PADDING_MAX_LENGTH = 15


def get_logger(name: str) -> logging.Logger:
    return structlog.getLogger(logname=name)


def custom_tiozin_renderer(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    if config.log_json:
        return event_dict
    logname: str = event_dict.pop("logname", "root")
    logname = f"{BLUE}{logname.ljust(PADDING_MAX_LENGTH)}{RESET}"
    event_dict["event"] = f"[{logname}] {event_dict['event']}"
    return event_dict


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
            custom_tiozin_renderer,
            JSON_RENDERER if config.log_json else CONSOLE_RENDERER,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
