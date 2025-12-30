from tiozin.api.resource import Resource
from tiozin.utils.helpers import utcnow


class Operator(Resource):
    """
    Base class for all Tiozin ETL operators.

    Following Data Mesh principles, operators are identified by business metadata
    that enables discovery, governance, and lineage tracking across domains.

    Attributes:
        name: Unique identifier for the operator instance.
        description: Human-readable description of the operator purpose.
        org: Organization owning the operator (top-level business unit).
        region: Geographic region where the operator operates or data resides.
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
        **options,
    ) -> None:
        super().__init__(name, description, **options)

        self.org = org
        self.region = region
        self.domain = domain
        self.layer = layer
        self.product = product
        self.model = model

        self.run_id = self.id
        self.created_at = utcnow()
        self.started_at = None
        self.finished_at = None

    def setup(self, **kwargs) -> None:
        return None

    def teardown(self, **kwargs) -> None:
        return None
