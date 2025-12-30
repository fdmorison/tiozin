from abc import abstractmethod
from typing import Generic, TypeVar

from .. import Context, Operator, Plugable

TData = TypeVar("TData")


class Transform(Plugable, Operator, Generic[TData]):
    """
    Transform operators apply business logic to produce new data.

    A Transform represents a processing step within a pipeline and is
    responsible for describing how input data should be transformed through
    business logic such as filtering, enrichment, aggregation, or joins.

    Depending on the provider, data transformation may be performed eagerly
    or deferred as part of a lazy execution plan coordinated by the Runner.

    By default, Transforms process each dataset individually. For operations
    that need to work with multiple datasets simultaneously (joins, unions,
    cross-dataset aggregations), use CombineTransform instead.
    """

    @abstractmethod
    def transform(self, context: Context, *data: TData) -> TData:
        """Apply transformation logic. Providers must implement."""

    def execute(self, context: Context, *data: TData) -> TData:
        """Template method that delegates to transform()."""
        return self.transform(context, *data)


class CombineTransform(Transform[TData]):
    """
    Transform that operates on many datasets at once.

    Unlike regular Transforms that process datasets individually,
    CombineTransforms receive many datasets simultaneously, enabling
    operations like joins, unions, or cross-dataset aggregations.

    Example:
        class JoinTransform(CombineTransform):
            def transform(self, context: Context, main: DataFrame, other: DataFrame) -> DataFrame:
                # Receive multiple dataframes and join them
                return main.join(other, on="key")
    """

    @abstractmethod
    def transform(self, context: Context, data: TData, *others: TData) -> TData:
        pass
