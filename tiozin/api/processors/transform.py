from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.exceptions import RequiredArgumentError

from .. import Context, Executable, PlugIn

TData = TypeVar("TData")


class Transform(Executable, PlugIn, Generic[TData]):
    """
    Defines a data transformation that modifies or enriches data.

    Specifies operations that transform a single input dataset through
    business logic such as filtering, enrichment, aggregation, or type
    conversions. Transforms own the transformation logic and produce
    transformed data products.

    Execution may be eager or lazy, depending on the Runner's strategy.
    For operations requiring multiple datasets (joins, unions), use CoTransform.

    Attributes:
        name: Unique identifier for this transform within the job.
        description: Short description of the transformation logic.
        org: Organization owning the transformation logic.
        domain: Domain team owning the transformation.
        product: Data product being transformed.
        model: Data model being transformed.
        layer: Data layer of the transformation output.
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
    def transform(self, context: Context, data: TData) -> TData:
        """Apply transformation logic. Providers must implement."""

    def execute(self, context: Context, data: TData) -> TData:
        """Template method that delegates to transform()."""
        return self.transform(context, data)


class CoTransform(Transform[TData]):
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
    def transform(self, context: Context, data: TData, other: TData, *others: TData) -> TData:
        """Apply cooperative transformation logic. Providers must implement."""
