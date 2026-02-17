from __future__ import annotations

from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.compose import RunnerProxy, tioproxy

from .. import Tiozin

TPlan = TypeVar("TPlan")
TSession = TypeVar("TSession")
TOutput = TypeVar("TOutput")


@tioproxy(RunnerProxy)
class Runner(Tiozin, Generic[TPlan, TSession, TOutput]):
    """
    Execution backend for Tiozin pipelines.

    A Runner defines the execution engine (e.g., Spark, Flink, DuckDB) and manages
    the lifecycle of job execution: environment setup, pipeline processing, and
    resource cleanup.

    The Runner does not own its own context. It accesses the active execution
    scope via ``Context.current()`` when needed. This keeps the Runner stateless
    and reusable across different execution scopes.

    Lifecycle:
        1. setup(): Called once when the Job initializes the Runner.
           Use this to create sessions, connections, or shared resources.

        2. run(plan): Called to execute work. May be invoked:
           - Lazily by the Job (after all steps complete)
           - Eagerly by each Step (as steps execute)

        3. teardown(): Called once when the Job releases the Runner.
           Use this to close sessions and release resources.

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

    @property
    @abstractmethod
    def session(self) -> TSession:
        """
        Active execution session managed by this runner.

        Exposes the underlying engine session created during `setup`
        (e.g. SparkSession, DuckDBPyConnection).

        The runner owns the session lifecycle; callers must not close or stop it directly.
        Accessing this property before setup raises NotInitializedError.

        For runners without a persistent engine session (e.g. Apache Beam), the session represents
        the execution container used to build and run the pipeline (e.g. beam.Pipeline).
        """

    @abstractmethod
    def setup(self) -> None:
        """Initialize the runner's resources (sessions, connections, etc.)."""
        pass

    @abstractmethod
    def run(self, execution_plan: TPlan, **options) -> TOutput:
        """
        Execute the given plan.

        May be called multiple times during a job's lifecycle—either lazily
        by the Job (after all steps complete) or eagerly by each Step
        (as steps execute). Use ``Context.current()`` to identify the
        active execution scope.
        """

    @abstractmethod
    def teardown(self) -> None:
        """Release the runner's resources (close sessions, connections, etc.)."""
        pass
