from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.api.resourceful import OptionalResourceful
from tiozin.api.runtime.dataset import Datasets
from tiozin.compose import tioproxy
from tiozin.exceptions import RequiredArgumentError

from ...tiozin import Tiozin
from .proxy import TransformProxy

TData = TypeVar("TData")


@tioproxy(TransformProxy)
class Transform(OptionalResourceful, Tiozin, Generic[TData]):
    """
    Defines a data transformation that modifies or enriches data.

    Specifies operations that transform a single input dataset through
    business logic such as filtering, enrichment, aggregation, or type
    conversions. Transforms own the transformation logic and produce
    transformed data products.

    Execution may be eager or lazy, depending on the Runner's strategy.
    For operations requiring multiple datasets (joins, unions), use CoTransform.

    The data product a transform produces is identified by the resource fields
    defined by OptionalResourceful: org, region, domain, subdomain, layer,
    product, and model. Each one is optional and falls back to the job's
    corresponding field when the job assembles its steps.

    Attributes:
        name: Unique identifier for this transform within the job.
        description: Short description of the transformation logic.
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
    def transform(self, data: TData) -> TData:
        """Apply transformation logic. Providers must implement."""

    def teardown(self) -> None:
        pass

    def external_datasets(self) -> Datasets:
        return Datasets()


class CoTransform(Transform[TData]):
    """
    Transforms multiple datasets cooperatively.

    Enables operations that require multiple inputs working together:
    joins, unions, merges, or cross-dataset transformations. The "Co-" prefix
    indicates cooperative processing, inspired by Flink's CoProcessFunction.

    Examples:
            class JoinCustomers(CoTransform):
                def transform(self, orders, customers):
                    return orders.join(customers, on='customer_id', how='inner')

            class UnionAll(CoTransform):
                def transform(self, *datasets):
                    return datasets[0].unionByName(*datasets[1:])

            class EnrichOrders(CoTransform):
                def transform(self, orders, products, customers):
                    return orders.join(products, on='product_id')
                                 .join(customers, on='customer_id')

    Note:
        Requires at least 2 inputs. For single-dataset transforms, use Transform.
    """

    @abstractmethod
    def transform(self, data: TData, *others: TData) -> TData:
        """Apply cooperative transformation logic. Providers must implement."""
