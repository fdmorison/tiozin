from enum import auto

from tiozin.api.metadata.model import UpperEnum


class StateStatus(UpperEnum):
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILURE = auto()
    CANCELED = auto()
    QUARANTINE = auto()
