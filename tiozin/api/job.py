import time
from typing import Unpack

from .context import Context
from .operator import Operator
from .typehint import OperatorKwargs


class Job(Operator):
    """
    Represents a complete ETL process.

    Combines Inputs, Transforms, Outputs, and a Runner into a single execution unit.
    Built from manifests (YAML, JSON, or Python) and executed by TiozinApp.
    """

    def __init__(self, **options: Unpack[OperatorKwargs]) -> None:
        super().__init__(**options)

    def run(self, context: Context) -> None:
        self.info("The job is starting.")
        time.sleep(3)
        self.info("The job has finished with success.")
        return

    def stop(self) -> None:
        self.warning("The job received a stop request.")
