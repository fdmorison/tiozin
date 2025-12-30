from abc import abstractmethod
from typing import Any, Optional, Unpack

from .. import Context, Operator, OperatorKwargs, Plugable


class Runner(Plugable, Operator):
    """
    Runners coordinate the execution of a pipeline.

    A Runner defines the execution backend and is responsible for managing
    the execution lifecycle of a job, including environment setup, pipeline
    execution, and resource cleanup.

    Runners coordinate execution either by interpreting values produced by
    operators or by being invoked directly by operators in eager execution
    scenarios, depending on the execution model.

    Operators used in a pipeline are expected to be compatible with the
    Runner's execution backend.

    Attributes:
        streaming: Indicates whether this runner executes streaming workloads.
        options: Provider-specific configuration parameters.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        streaming: bool = False,
        **options: Unpack[OperatorKwargs],
    ) -> None:
        super().__init__(name, description, **options)
        self.streaming = streaming

    @abstractmethod
    def run(self, context: Context, job: Any) -> None:
        """Run the job. Providers must implement."""

    def execute(self, context: Context, job: Any) -> None:
        """Template method that delegates to run()."""
        self.run(context, job)
