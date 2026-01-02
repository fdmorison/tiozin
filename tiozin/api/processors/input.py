from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.exceptions import RequiredArgumentError

from .. import Context, Executable, Plugable, Resource

T = TypeVar("T")


class Input(Plugable, Executable, Resource, Generic[T]):
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
        name: str = None,
        description: str = None,
        schema: str = None,
        schema_subject: str = None,
        schema_version: str = None,
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
        self.schema = schema
        self.schema_subject = schema_subject
        self.schema_version = schema_version

        self.org = org
        self.region = region
        self.domain = domain
        self.layer = layer
        self.product = product
        self.model = model

    @abstractmethod
    def read(self, context: Context) -> T:
        """Read data from source. Providers must implement."""

    def execute(self, context: Context) -> T:
        """Template method that delegates to read()."""
        return self.read(context)

    def setup(self) -> None:
        return None

    def teardown(self) -> None:
        return None
