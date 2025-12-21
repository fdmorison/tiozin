from abc import abstractmethod
from typing import Any, Optional, Unpack

from .context import Context
from .plugable import Plugable
from .resource import Resource
from .typehint import ResourceKwargs


class Runner(Plugable, Resource):
    """
    Runners are execution engines that orchestrate and run Jobs.

    They manage the complete execution lifecycle from preparing the runtime
    context, executing the pipeline, to handling teardown and cleanup. Runners
    abstract the execution environment, allowing Jobs to run on different
    backends (local, distributed, cloud) without code changes.

    Providers implement run() for their specific execution engine.

    Examples of runners:
        - SparkRunner: Execute Jobs using Apache Spark
        - DataflowRunner: Run on Google Cloud Dataflow
        - FlinkRunner: Stream processing with Apache Flink
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        streaming: bool = False,
        **kwargs: Unpack[ResourceKwargs],
    ) -> None:
        super().__init__(name, description, **kwargs)
        self.streaming = streaming

    @abstractmethod
    def run(self, context: Context, job: Any) -> None:
        """Run the job. Providers must implement."""

    def execute(self, context: Context, job: Any) -> None:
        """Template method that delegates to run()."""
        self.run(context, job)
