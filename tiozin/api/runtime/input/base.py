from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.api.resourceful import OptionalResourceful
from tiozin.api.runtime.dataset import Datasets
from tiozin.compose import tioproxy
from tiozin.exceptions import RequiredArgumentError

from ...tiozin import Tiozin
from .proxy import InputProxy

TData = TypeVar("TData")


@tioproxy(InputProxy)
class Input(OptionalResourceful, Tiozin, Generic[TData]):
    """
    Defines a data source that ingests data into the pipeline.

    Specifies how and where data is read from external sources such as
    databases, file systems, APIs, streams, or object storage. Inputs
    represent the entry point of a pipeline and consume data products
    from their source layer.

    Data access may be eager or lazy, depending on the Runner's execution
    strategy. Schema metadata can be provided to describe the expected
    structure of the input data.

    The data product an input consumes is identified by the resource fields
    defined by OptionalResourceful: org, region, domain, subdomain, layer,
    product, and model. Each one is optional and falls back to the job's
    corresponding field when the job assembles its steps.

    Attributes:
        name: Unique identifier for this input within the job.
        description: Short description of the data source.
        schema_subject: Schema registry subject name.
        schema_version: Specific schema version.
    """

    def __init__(
        self,
        name: str = None,
        description: str = None,
        schema_subject: str = None,
        schema_version: str = None,
        **options,
    ) -> None:
        super().__init__(name, description, **options)

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
