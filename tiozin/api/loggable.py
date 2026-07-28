import logging
from typing import Unpack

from tiozin import logs

from .typehint import LogKwargs


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
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.exception(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.critical(msg, *args, **kwargs)
