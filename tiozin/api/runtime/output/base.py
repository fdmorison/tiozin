from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.api.resourceful import OptionalResourceful
from tiozin.api.runtime.dataset import Datasets
from tiozin.compose import tioproxy
from tiozin.exceptions import RequiredArgumentError

from ...tiozin import Tiozin
from .proxy import OutputProxy

TData = TypeVar("TData")


@tioproxy(OutputProxy)
class Output(OptionalResourceful, Tiozin, Generic[TData]):
    """
    Defines a data destination that persists processed data.

    Specifies where and how data is written to external systems such as
    databases, file systems, or streaming sinks. Outputs represent the
    terminal step of a pipeline and produce data products in their
    destination layer.

    The write() method may return the input data, a writer object, or None.
    Writer objects enable lazy execution by separating write intent from
    execution strategy, which is delegated to the Runner.

    The data product an output produces is identified by the resource fields
    defined by OptionalResourceful: org, region, domain, subdomain, layer,
    product, and model. Each one is optional and falls back to the job's
    corresponding field when the job assembles its steps.

    Attributes:
        name: Unique identifier for this output within the job.
        description: Short description of the data destination.
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
    def write(self, data: TData) -> TData:
        """
        Write data to destination. Providers must implement.
        """

    def teardown(self) -> None:
        pass

    def external_datasets(self) -> Datasets:
        return Datasets()
