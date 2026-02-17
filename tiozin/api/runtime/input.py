from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.compose import StepProxy, tioproxy
from tiozin.exceptions import RequiredArgumentError

from .. import Tiozin

TData = TypeVar("TData")


@tioproxy(StepProxy)
class Input(Tiozin, Generic[TData]):
    """
    Defines a data source that ingests data into the pipeline.

    Specifies how and where data is read from external sources such as
    databases, file systems, APIs, streams, or object storage. Inputs
    represent the entry point of a pipeline and consume data products
    from their source layer.

    Data access may be eager or lazy, depending on the Runner's execution
    strategy. Schema metadata can be provided to describe the expected
    structure of the input data.

    Attributes:
        name: Unique identifier for this input within the job.
        description: Short description of the data source.
        org: Organization owning the source data.
        domain: Domain team owning the source data.
        product: Data product being consumed.
        model: Data model being read (e.g., table, topic, collection).
        layer: Data layer of the source (e.g., raw, trusted, refined).
        schema: The schema definition of input data.
        schema_subject: Schema registry subject name.
        schema_version: Specific schema version.
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

    def setup(self) -> None:
        return None

    @abstractmethod
    def read(self) -> TData:
        """Read data from source. Providers must implement."""

    def teardown(self) -> None:
        return None
