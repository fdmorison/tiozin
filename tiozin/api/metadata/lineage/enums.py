from enum import auto

from ..model import UpperEnum


class LineageRunEventType(UpperEnum):
    START = auto()
    COMPLETE = auto()
    FAIL = auto()
    ABORT = auto()


class LineageProcessingType(UpperEnum):
    BATCH = auto()
    STREAMING = auto()


class LineageJobType(UpperEnum):
    QUERY = auto()
    COMMAND = auto()
    DAG = auto()
    TASK = auto()
    JOB = auto()
    MODEL = auto()
