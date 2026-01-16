from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from ..assembly import tioproxy
from ..assembly.runner_proxy import RunnerProxy
from . import PlugIn

if TYPE_CHECKING:
    from tiozin import RunnerContext

T = TypeVar("T")


@tioproxy(RunnerProxy)
class Runner(PlugIn, Generic[T]):
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
    def setup(self, context: RunnerContext) -> None:
        pass

    @abstractmethod
    def run(self, context: RunnerContext, execution_plan: T) -> Any:
        """Run the job. Providers must implement."""

    @abstractmethod
    def teardown(self, context: RunnerContext) -> None:
        pass
