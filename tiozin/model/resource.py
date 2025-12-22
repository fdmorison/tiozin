from tiozin.model.component import Component


class Resource(Component):
    """
    Base class for all Tiozin ETL resources.

    Following Data Mesh principles, resources are identified by business metadata
    that enables discovery, governance, and lineage tracking across domains.

    Attributes:
        name: Unique identifier for the resource instance.
        description: Human-readable description of the resource purpose.
        org: Organization owning the resource (top-level business unit).
        region: Geographic region where the resource operates or data resides.
        domain: Business domain in Data Mesh architecture (e.g., 'sales', 'finance').
        layer: Data architecture layer (e.g., 'raw', 'staging', 'refined', 'curated').
        product: Data product within the domain, representing a cohesive data asset.
        model: Specific data model or entity within the product (e.g., 'customer', 'transaction').

    Example:
        job = Job(
            name="daily_revenue_etl",
            description="Aggregates daily revenue from transactions",
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
        name: str,
        description: str,
        org: str,
        region: str,
        domain: str,
        layer: str,
        product: str,
        model: str,
    ) -> None:
        super().__init__(name, description)
        self.org = org
        self.region = region
        self.domain = domain
        self.layer = layer
        self.product = product
        self.model = model

    @property
    def uri(self) -> str:
        return f"{self.kind}:{self.name}"

    @property
    def instance_uri(self) -> str:
        return f"{self.uri}:{self.id}"
