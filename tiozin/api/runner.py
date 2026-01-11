from abc import abstractmethod
from typing import Any, Generic, Self, TypeVar

from ..assembly import tioproxy
from ..assembly.executable_proxy import ExecutableProxy
from . import Context, Executable, PlugIn

T = TypeVar("T")


@tioproxy(ExecutableProxy)
class Runner(Executable, PlugIn, Generic[T]):
    """
    Runners execute and coordinate pipelines within a specific backend.

    A Runner defines the execution backend (e.g., Spark, Flink, Dataflow, DuckDB, BigQuery)
    and is responsible for managing the execution lifecycle of a job, including
    environment setup, pipeline execution, and resource cleanup.

    Unlike data processing components (Job, Input, Transform, Output) which
    define the processing logic, Runners are execution engines that coordinate
    how and where these components run, interpreting values they produce or
    invoking them directly in eager execution scenarios.

    Data processing components used in a pipeline must be compatible with
    the Runner's execution backend.

    Attributes:
        streaming: Indicates whether this runner executes streaming workloads.
        options: Provider-specific configuration parameters.
    """

    def __init__(
        self,
        name: str = None,
        description: str = None,
        streaming: bool = False,
        **options,
    ) -> None:
        super().__init__(name, description, **options)
        self.streaming = streaming

    @abstractmethod
    def run(self, context: Context, execution_plan: T) -> Any:
        """Run the job. Providers must implement."""

    def execute(self, context: Context, execution_plan: T) -> Any:
        """Template method that delegates to run()."""
        self.run(context, execution_plan)

    def __enter__(self) -> Self:
        """
        Enters the Runner execution context and triggers setup.
        """
        self.setup()
        return self

    def __exit__(self, clazz, error, trace) -> None:
        """
        Exits the Runner execution context and triggers teardown.
        """
        self.teardown()
