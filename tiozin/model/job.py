import time

from .abc.resource import Resource
from .context import Context


class Job(Resource):
    """
    Represents a complete ETL process within a TioApp.

    A Job is composed of one or more Inputs, one or more Transforms, one or more Outputs,
    and a Runner, forming the major execution step inside a TioApp. It encapsulates all the
    logic needed to extract, transform, and load data according to the job manifest.

    Jobs are built from manifests, whose most basic form is YAML files stored on the
    filesystem, in a bucket, or in a database.

    Jobs are executed within the TioApp, which is responsible for managing registries,
    configuration, and other runtime information.
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
