from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.exceptions import RequiredArgumentError

from .. import Context, Executable, Plugable, Resource

T = TypeVar("T")


class Transform(Plugable, Executable, Resource, Generic[T]):
    """
    Transform operators apply business logic to produce new data.

    Applies transformations like filtering, enrichment, aggregation, or
    type conversions to a single input dataset. Execution may be eager
    or lazy, depending on the Runner's strategy.

    For operations requiring multiple datasets (joins, unions), use CoTransform.
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

    @abstractmethod
    def transform(self, context: Context, data: T) -> T:
        """Apply transformation logic. Providers must implement."""

    def execute(self, context: Context, data: T) -> T:
        """Template method that delegates to transform()."""
        return self.transform(context, data)

    def setup(self) -> None:
        return None

    def teardown(self) -> None:
        return None


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
