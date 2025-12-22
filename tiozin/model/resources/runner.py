from abc import abstractmethod
from typing import Any, Optional, Unpack

from ..context import Context
from ..plugable import Plugable
from ..resource import Resource
from ..typehint import ResourceKwargs


class Runner(Plugable, Resource):
    """
    Execution engine responsible for running jobs.

    Runners orchestrate the full job execution lifecycle, including
    preparing the runtime context, executing the pipeline, and handling
    teardown and cleanup. They abstract the execution environment so that
    jobs can run on different backends without code changes.

    Attributes:
        streaming: Indicates whether this runner executes streaming workloads.
        options: All extra initialization parameters of the component flow into
            this attribute. Use it to pass provider-specific configurations like
            Spark session configs (e.g., spark.executor.memory="4g").

    Providers implement the execution logic for a specific engine
    (e.g. Spark, Dataflow, Flink, Pandas, Tensorflow, etc).
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        streaming: bool = False,
        **options: Unpack[ResourceKwargs],
    ) -> None:
        super().__init__(name, description, **options)
        self.streaming = streaming

    @abstractmethod
    def run(self, context: Context, job: Any) -> None:
        """Run the job. Providers must implement."""

    def execute(self, context: Context, job: Any) -> None:
        """Template method that delegates to run()."""
        self.run(context, job)
