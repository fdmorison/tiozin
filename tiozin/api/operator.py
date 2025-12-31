from tiozin.api.resource import Resource
from tiozin.exceptions import RequiredArgumentError
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
        name: str = None,
        org: str = None,
        region: str = None,
        domain: str = None,
        layer: str = None,
        product: str = None,
        model: str = None,
        _require_taxonomy: bool = False,
        **options,
    ) -> None:
        super().__init__(name, **options)

        RequiredArgumentError.raise_if_missing(
            name=name,
        ).raise_if_missing(
            org=org,
            region=region,
            domain=domain,
            layer=layer,
            product=product,
            model=model,
            disable_=not _require_taxonomy,
        )

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
