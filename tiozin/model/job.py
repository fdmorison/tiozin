import time
from typing import Unpack

from .context import Context
from .resource import Resource
from .typehint import Taxonomy


class Job(Resource):
    """
    Represents a complete ETL process.

    Combines Inputs, Transforms, Outputs, and a Runner into a single execution unit.
    Built from manifests (YAML, JSON, or Python) and executed by TiozinApp.
    """

    def __init__(self, **kwargs: Unpack[Taxonomy]) -> None:
        super().__init__(**kwargs)

    def run(self, context: Context) -> None:
        self.info("The job is starting.")
        time.sleep(3)
        self.info("The job has finished with success.")
        return

    def stop(self) -> None:
        self.warning("The job received a stop request.")
