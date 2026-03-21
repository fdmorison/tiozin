import logging

from .service import log_service


def setup() -> None:
    log_service.setup()


def get_logger(name: str) -> logging.Logger:
    return log_service.get_logger(name)


def register_sensitive(value: str) -> None:
    log_service.register_sensitive(value)
