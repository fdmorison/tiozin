from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin import config
from tiozin.api.runtime.dataset import Datasets
from tiozin.compose import tioproxy
from tiozin.exceptions import RequiredArgumentError

from ..tiozin import Tiozin
from .step_proxy import StepProxy

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
        subdomain: Subdomain within the domain team owning the source data.
        layer: Data layer of the source (e.g., raw, trusted, refined).
        product: Data product being consumed.
        model: Data model being read (e.g., table, topic, collection).
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
        subdomain: str = None,
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
        self.schema_subject = schema_subject or config.tiozin_schema_subject_template
        self.schema_version = schema_version or config.tiozin_schema_default_version

        self.org = org
        self.region = region
        self.domain = domain
        self.subdomain = subdomain
        self.layer = layer
        self.product = product
        self.model = model

    def setup(self) -> None:
        pass

    @abstractmethod
    def read(self) -> TData:
        """Read data from source. Providers must implement."""

    def teardown(self) -> None:
        pass

    def static_datasets(self) -> Datasets:
        return Datasets()
