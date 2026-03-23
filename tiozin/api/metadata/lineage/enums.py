from enum import StrEnum, auto


class LineageEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name: str, *_) -> str:
        return name.upper()

    def __repr__(self) -> str:
        return self.value


class LineageRunEventType(LineageEnum):
    START = auto()
    COMPLETE = auto()
    FAIL = auto()
    ABORT = auto()


class LineageProcessingType(LineageEnum):
    BATCH = auto()
    STREAMING = auto()


class LineageJobType(LineageEnum):
    QUERY = auto()
    COMMAND = auto()
    DAG = auto()
    TASK = auto()
    JOB = auto()
    MODEL = auto()
