from abc import abstractmethod
from typing import Generic, TypeVar

from .. import Context, Plugable, Processor

TData = TypeVar("TData")
TWriter = TypeVar("TWriter")


class Output(Plugable, Processor, Generic[TData, TWriter]):
    """
    Output operators persist data to external systems.

    An Output represents the terminal step of a pipeline, responsible for
    writing data to a destination such as a database, file system, or
    streaming sink.

    The `write()` method may return either:
    - the input data or
    - a writer object whose concrete type is interpreted by the Runner
      to decide how the job is executed.

    This Output/Writer modeling enables lazy execution by separating write
    intent from execution strategy, which is delegated to the Runner. Eager
    execution may be indicated to the Runner by returning TData or `None`.
    """

    @abstractmethod
    def write(self, context: Context, data: TData) -> TData | TWriter:
        """
        Write data to destination. Providers must implement.
        """

    def execute(self, context: Context, data: TData) -> TData | TWriter:
        """Template method that delegates to write()."""
        return self.write(context, data)
