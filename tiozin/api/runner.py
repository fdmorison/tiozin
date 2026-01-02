from abc import abstractmethod
from typing import Any, Unpack

from . import Context, ProcessorKwargs, Resource
from .executable import Executable
from .plugable import Plugable


class Runner(Plugable, Executable, Resource):
    """
    Runners execute and coordinate pipelines within a specific backend.

    A Runner defines the execution backend (e.g., Spark, Flink, Dataflow, DuckDB, BigQuery)
    and is responsible for managing the execution lifecycle of a job, including
    environment setup, pipeline execution, and resource cleanup.

    Unlike Processors (Job, Input, Transform, Output) which define the data
    processing logic, Runners are execution engines that coordinate how and
    where processors run, interpreting values produced by processors or
    invoking them directly in eager execution scenarios.

    Processors used in a pipeline must be compatible with the Runner's
    execution backend.

    Attributes:
        streaming: Indicates whether this runner executes streaming workloads.
        options: Provider-specific configuration parameters.
    """

    def __init__(
        self,
        name: str = None,
        description: str = None,
        streaming: bool = False,
        **options: Unpack[ProcessorKwargs],
    ) -> None:
        super().__init__(name, description, **options)
        self.streaming = streaming

    @abstractmethod
    def run(self, context: Context, job: Any) -> None:
        """Run the job. Providers must implement."""

    def execute(self, context: Context, job: Any) -> None:
        """Template method that delegates to run()."""
        self.run(context, job)

    def setup(self) -> None:
        return None

    def teardown(self) -> None:
        return None
