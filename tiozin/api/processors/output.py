from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.exceptions import RequiredArgumentError

from .. import Context, Executable, Plugable, Resource

TData = TypeVar("TData")
TWriter = TypeVar("TWriter")


class Output(Plugable, Executable, Resource, Generic[TData, TWriter]):
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

    def __init__(
        self,
        name: str = None,
        description: str = None,
        org: str = None,
        region: str = None,
        domain: str = None,
        layer: str = None,
        product: str = None,
        model: str = None,
        **options,
    ) -> None:
        super().__init__(name, description, **options)

        RequiredArgumentError.raise_if_missing(
            name=name,
        )
        self.org = org
        self.region = region
        self.domain = domain
        self.layer = layer
        self.product = product
        self.model = model

    @abstractmethod
    def write(self, context: Context, data: TData) -> TData | TWriter:
        """
        Write data to destination. Providers must implement.
        """

    def execute(self, context: Context, data: TData) -> TData | TWriter:
        """Template method that delegates to write()."""
        return self.write(context, data)

    def setup(self) -> None:
        return None

    def teardown(self) -> None:
        return None
