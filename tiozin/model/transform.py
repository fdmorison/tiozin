from abc import abstractmethod
from typing import Generic, Optional, TypeVar, Unpack

from .context import Context
from .plugable import Plugable
from .resource import Resource
from .typehint import Taxonomy

TData = TypeVar("TData")


class Transform(Plugable, Resource, Generic[TData]):
    """
    Transforms are the core processing units in Tiozin pipelines. They take data
    from inputs, apply business logic (filtering, enrichment, aggregation, joins,
    etc), and produce transformed data for outputs.

    Transforms are extensible and can leverage any processing engine. Providers
    implement the transform() method with their specific logic while the framework
    handles orchestration, lifecycle, and context management.

    Examples of transforms:
        - SparkWordCountTransform: Count word occurrences using Spark
        - SQLJoinTransform: Join datasets using SQL engine
        - FlinkStreamTransform: Real-time stream processing with Flink
        - PandasEnrichTransform: Data enrichment using Pandas
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        **kwargs: Unpack[Taxonomy],
    ) -> None:
        super().__init__(name, description, **kwargs)

    @abstractmethod
    def transform(self, context: Context, *data: TData) -> TData:
        """Apply transformation logic. Providers must implement."""

    def execute(self, context: Context, *data: TData) -> TData:
        """Template method that delegates to transform()."""
        return self.transform(context, *data)
