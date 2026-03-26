from enum import auto

from ...domain import UppercaseEnum


class LineageRunEventType(UppercaseEnum):
    START = auto()
    COMPLETE = auto()
    FAIL = auto()
    ABORT = auto()


class LineageProcessingType(UppercaseEnum):
    BATCH = auto()
    STREAMING = auto()


class LineageJobType(UppercaseEnum):
    QUERY = auto()
    COMMAND = auto()
    DAG = auto()
    TASK = auto()
    JOB = auto()
    MODEL = auto()
