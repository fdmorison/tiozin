import time

from .context import Context
from .resource import Resource


class Job(Resource):
    """
    Represents a complete ETL process.

    Combines Inputs, Transforms, Outputs, and a Runner into a single execution unit.
    Built from manifests (YAML, JSON, or Python) and executed by TiozinApp.
    """

    def __init__(self) -> None:
        super().__init__()

    def run(self, context: Context) -> None:
        self.logger.info("The job is starting.")
        time.sleep(3)
        self.logger.info("The job has finished with success.")
        return

    def stop(self) -> None:
        self.logger.warning("The job received a stop request.")
