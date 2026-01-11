import logging
from typing import Any, Self, Unpack

import structlog

from tiozin import config

from .typehint import LogKwargs

BLUE = "\033[34m"
RESET = "\033[0m"

PADDING_MAX_LENGTH = 15


class TiozinLogger:
    """
    Logger abstraction owned by Tiozin to control how logs are emitted.

    It adds Tiozin-specific behavior, such as rich structured logs, field
    filtering, and structured JSON output, on top of a replaceable logging
    backend (currently structlog).
    """

    def __init__(
        self,
        name: str,
        *,
        hide_none: bool = False,
        hide_fields: set[str] | None = None,
    ) -> None:
        self._name = name
        self._logger = structlog.get_logger(name)
        self._hide_none = hide_none
        self._hide_fields = hide_fields or set()

    def hide_fields(self, *fields: str) -> Self:
        self._hide_fields.update(fields)
        return self

    def hide_none(self, enabled: bool = True) -> Self:
        self._hide_none = enabled
        return self

    def debug(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        if config.log_level > logging.DEBUG:
            return
        self._logger.debug(self._format(msg), *args, **self._filter(kwargs))

    def info(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        if config.log_level > logging.INFO:
            return
        self._logger.info(self._format(msg), *args, **self._filter(kwargs))

    def warning(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        if config.log_level > logging.WARNING:
            return
        self._logger.warning(self._format(msg), *args, **self._filter(kwargs))

    def error(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        if config.log_level > logging.ERROR:
            return
        self._logger.error(self._format(msg), *args, **self._filter(kwargs))

    def critical(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        if config.log_level > logging.CRITICAL:
            return
        self._logger.critical(self._format(msg), *args, **self._filter(kwargs))

    def exception(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        if config.log_level > logging.ERROR:
            return
        self._logger.exception(self._format(msg), *args, **self._filter(kwargs))

    def _format(self, msg: str) -> str:
        if config.log_json:
            return msg
        name = self._name.ljust(PADDING_MAX_LENGTH)
        return f"[{BLUE}{name}{RESET}] {msg}"

    def _filter(self, fields: dict[str, Any]) -> dict[str, Any]:
        filtered: dict[str, Any] = {}

        for key, value in fields.items():
            if key in self._hide_fields:
                continue
            if self._hide_none and value is None:
                continue
            filtered[key] = value

        return filtered
