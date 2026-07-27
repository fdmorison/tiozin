import logging
from typing import Unpack

from tiozin import config, logs

from .typehint import LogKwargs

BLUE = "\033[34m"
RESET = "\033[0m"

PADDING_MAX_LENGTH = 15


class Loggable:
    """
    Mixin that provides logging capabilities to any class.

    Classes using this mixin gain access to convenience logging methods
    (debug, info, warning, error, exception, critical) that delegate
    to a logger instance scoped to the class name.
    """

    @property
    def __logger_name(self) -> str:
        if name := getattr(self, "name", None):
            return name
        return type(self).__name__

    @property
    def logger(self) -> logging.Logger:
        return logs.get_logger(self.__logger_name)

    def debug(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.debug(self._fmt(msg), *args, **kwargs)

    def info(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.info(self._fmt(msg), *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.warning(self._fmt(msg), *args, **kwargs)

    def error(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.error(self._fmt(msg), *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.exception(self._fmt(msg), *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.critical(self._fmt(msg), *args, **kwargs)

    def _fmt(self, msg: str) -> str:
        if config.log_json:
            return msg
        name = self.__logger_name.ljust(PADDING_MAX_LENGTH)
        return f"[{BLUE}{name}{RESET}] {msg}"
