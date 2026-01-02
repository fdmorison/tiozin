from abc import abstractmethod
from typing import Generic, TypeVar

from .. import Context, Plugable, Processor

T = TypeVar("T")


class Transform(Plugable, Processor, Generic[T]):
    """
    Transform operators apply business logic to produce new data.

    Applies transformations like filtering, enrichment, aggregation, or
    type conversions to a single input dataset. Execution may be eager
    or lazy, depending on the Runner's strategy.

    For operations requiring multiple datasets (joins, unions), use CoTransform.
    """

    @abstractmethod
    def transform(self, context: Context, data: T) -> T:
        """Apply transformation logic. Providers must implement."""

    def execute(self, context: Context, data: T) -> T:
        """Template method that delegates to transform()."""
        return self.transform(context, data)


class CoTransform(Transform[T]):
    """
    Transforms multiple datasets cooperatively.

    Enables operations that require multiple inputs working together:
    joins, unions, merges, or cross-dataset transformations. The "Co-" prefix
    indicates cooperative processing, inspired by Flink's CoProcessFunction.

    Examples:
            class JoinCustomers(CoTransform):
                def transform(self, context, orders, customers):
                    return orders.join(customers, on='customer_id', how='inner')

            class UnionAll(CoTransform):
                def transform(self, context, *datasets):
                    return datasets[0].unionByName(*datasets[1:])

            class EnrichOrders(CoTransform):
                def transform(self, context, orders, products, customers):
                    return orders.join(products, on='product_id')
                                 .join(customers, on='customer_id')

    Note:
        Requires at least 2 inputs. For single-dataset transforms, use Transform.
    """

    @abstractmethod
    def transform(self, context: Context, data: T, other: T, *others: T) -> T:
        """Apply cooperative transformation logic. Providers must implement."""
