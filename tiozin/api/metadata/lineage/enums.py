from enum import auto

from ..model import UpperEnum


class RunEventType(UpperEnum):
    START = auto()
    COMPLETE = auto()
    FAIL = auto()
    ABORT = auto()


class ProcessingType(UpperEnum):
    BATCH = auto()
    STREAMING = auto()


class JobType(UpperEnum):
    QUERY = auto()
    COMMAND = auto()
    DAG = auto()
    TASK = auto()
    JOB = auto()
    MODEL = auto()


class EmitLevel(UpperEnum):
    JOB = auto()
    STEP = auto()
    ALL = auto()
