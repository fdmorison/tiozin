from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.api.resourceful import Resourceful
from tiozin.api.runtime.dataset import Datasets
from tiozin.compose import tioproxy
from tiozin.exceptions import RequiredArgumentError

from ...tiozin import Tiozin
from .proxy import InputProxy

TData = TypeVar("TData")


@tioproxy(InputProxy)
class Input(Resourceful, Tiozin, Generic[TData]):
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
        subdomain: Subdomain within the domain team owning the source data.
        layer: Data layer of the source (e.g., raw, trusted, refined).
        product: Data product being consumed.
        model: Data model being read (e.g., table, topic, collection).
        schema_subject: Schema registry subject name.
        schema_version: Specific schema version.
    """

    def __init__(
        self,
        name: str = None,
        description: str = None,
        schema_subject: str = None,
        schema_version: str = None,
        org: str = None,
        region: str = None,
        domain: str = None,
        subdomain: str = None,
        layer: str = None,
        product: str = None,
        model: str = None,
        **options,
    ) -> None:
        super().__init__(
            name,
            description,
            org=org,
            region=region,
            domain=domain,
            subdomain=subdomain,
            layer=layer,
            product=product,
            model=model,
            **options,
        )

        RequiredArgumentError.raise_if_missing(
            name=name,
        )

        self.schema_subject = schema_subject
        self.schema_version = schema_version

    def setup(self) -> None:
        pass

    @abstractmethod
    def read(self) -> TData:
        """Read data from source. Providers must implement."""

    def teardown(self) -> None:
        pass

    def external_datasets(self) -> Datasets:
        return Datasets()
