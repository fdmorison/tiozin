import time

from .abc.resource import Resource
from .context import Context


class Job(Resource):

    def __init__(self) -> None:
        super().__init__()

    def run(self, context: Context) -> None:
        self.logger.info(f"The job `{self}` is starting.")
        time.sleep(3)
        self.logger.info(f"The job `{self}` has finished with success.")
        return
