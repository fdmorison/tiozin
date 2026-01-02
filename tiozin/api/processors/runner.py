from abc import abstractmethod
from typing import Any, Unpack

from .. import Context, Plugable, Processor, ProcessorKwargs


class Runner(Plugable, Processor):
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
        name: str = None,
        streaming: bool = False,
        **options: Unpack[ProcessorKwargs],
    ) -> None:
        super().__init__(
            name=name or type(self).__name__,
            **options,
        )
        self.streaming = streaming

    @abstractmethod
    def run(self, context: Context, job: Any) -> None:
        """Run the job. Providers must implement."""

    def execute(self, context: Context, job: Any) -> None:
        """Template method that delegates to run()."""
        self.run(context, job)
