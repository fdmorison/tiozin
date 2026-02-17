from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.compose import StepProxy, tioproxy

from ...exceptions import RequiredArgumentError
from .. import Tiozin
from .context import Context

TData = TypeVar("TData")


@tioproxy(StepProxy)
class Output(Tiozin, Generic[TData]):
    """
    Defines a data destination that persists processed data.

    Specifies where and how data is written to external systems such as
    databases, file systems, or streaming sinks. Outputs represent the
    terminal step of a pipeline and produce data products in their
    destination layer.

    The write() method may return the input data, a writer object, or None.
    Writer objects enable lazy execution by separating write intent from
    execution strategy, which is delegated to the Runner.

    Attributes:
        name: Unique identifier for this output within the job.
        description: Short description of the data destination.
        org: Organization owning the destination data.
        domain: Domain team owning the destination.
        product: Data product being produced.
        model: Data model being written (e.g., table, topic, collection).
        layer: Data layer of the destination (e.g., raw, trusted, refined).
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

    def setup(self, context: Context, data: TData) -> None:
        return None

    @abstractmethod
    def write(self, context: Context, data: TData) -> TData:
        """
        Write data to destination. Providers must implement.
        """

    def teardown(self, context: Context, data: TData) -> None:
        return None
