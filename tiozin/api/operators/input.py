from abc import abstractmethod
from typing import Generic, TypeVar, Unpack

from .. import Context, Operator, OperatorKwargs, Plugable

TData = TypeVar("TData")


class Input(Plugable, Operator, Generic[TData]):
    """
    Input operators ingest data into a pipeline.

    An Input represents the entry point of a pipeline and is responsible for
    describing how data should be read from an external source, such as a
    database, file system, API, stream, or object storage.

    Depending on the provider, data access may be performed eagerly
    or deferred as part of a lazy execution plan coordinated by the Runner.

    Schema metadata may be provided to describe the expected structure of the
    input data. Schema enforcement and validation, when applicable, are
    provider-specific concerns and may occur eagerly or lazily depending on
    the execution model.

    Attributes:
        schema: Optional data schema definition.
        schema_subject: Optional schema registry subject.
        schema_version: Optional schema version identifier.
        options: Provider-specific configuration parameters.
    """

    def __init__(
        self,
        schema: str | None = None,
        schema_subject: str | None = None,
        schema_version: str | None = None,
        **options: Unpack[OperatorKwargs],
    ) -> None:
        super().__init__(**options)
        self.schema = schema
        self.schema_subject = schema_subject
        self.schema_version = schema_version

    @abstractmethod
    def read(self, context: Context) -> TData:
        """Read data from source. Providers must implement."""

    def execute(self, context: Context) -> TData:
        """Template method that delegates to read()."""
        return self.read(context)
