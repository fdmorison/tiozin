from tiozin.api.executable import Executable
from tiozin.api.resource import Resource
from tiozin.exceptions import RequiredArgumentError


class Processor(Executable, Resource):
    """
    Base class for all Tiozin data processors.

    A Processor represents a data processing component in an ETL pipeline.
    Following Data Mesh principles, processors are identified by business metadata
    that enables discovery, governance, and lineage tracking across domains.

    Processors include Job, Input, Transform, and Output components that handle
    data ingestion, transformation, and persistence operations.

    Attributes:
        name: Unique identifier for the processor instance.
        org: Organization owning the processor (top-level business unit).
        region: Geographic region where the processor operates or data resides.
        domain: Business domain in Data Mesh architecture (e.g., 'sales', 'finance').
        layer: Data architecture layer (e.g., 'raw', 'staging', 'refined', 'curated').
        product: Data product within the domain, representing a cohesive data asset.
        model: Specific data model or entity within the product (e.g., 'customer', 'transaction').

    Example:
        job = Job(
            name="daily_revenue_etl",
            org="acme_corp",
            region="us_east",
            domain="finance",
            layer="refined",
            product="revenue_analytics",
            model="daily_summary"
        )
    """

    def __init__(
        self,
        name: str = None,
        org: str = None,
        region: str = None,
        domain: str = None,
        layer: str = None,
        product: str = None,
        model: str = None,
        **options,
    ) -> None:
        super().__init__(name, **options)

        RequiredArgumentError.raise_if_missing(
            name=name,
        )
        self.org = org
        self.region = region
        self.domain = domain
        self.layer = layer
        self.product = product
        self.model = model

    def setup(self, **kwargs) -> None:
        return None

    def teardown(self, **kwargs) -> None:
        return None
