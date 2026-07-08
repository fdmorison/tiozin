from tiozin.api.conventions import DOMAIN_FIELDS, PRODUCT_FIELDS, RESOURCE_FIELDS, SUBDOMAIN_FIELDS


class Resourceful:
    """
    Mixin that adds a canonical resource identity to a class.

    Defines the standard resource fields (org, region, domain, subdomain,
    layer, product, and model) used to identify a Data Mesh resource, and
    provides helpers to expose them as a dictionary or as qualified
    dot-separated identifiers.

    Attributes:
        org: Organization that owns the domains and data products.
        region: Unique name of the business regional domain, not the cloud region.
        domain: Unique name of the business domain.
        subdomain: Subdivision within the business domain.
        layer: Refinement level of the data product.
        product: Unique name of the data product.
        model: Model within the data product, a.k.a. asset, relation, entity, etc.

    Example:
        >>> class Table(Resourceful):
        ...     pass
        >>> table = Table(
        ...     org="acme",
        ...     region="latam",
        ...     domain="sales",
        ...     subdomain="b2b",
        ...     layer="gold",
        ...     product="sales_cube",
        ...     model="fact_orders",
        ... )
        >>> table.qualified_domain
        'acme.latam.sales'
        >>> table.qualified_subdomain
        'acme.latam.sales.b2b'
        >>> table.qualified_product
        'gold.sales_cube.fact_orders'
        >>> table.qualified_resource
        'acme.latam.sales.b2b.gold.sales_cube.fact_orders'
    """

    def __init__(
        self,
        *args,
        org: str = None,
        region: str = None,
        domain: str = None,
        subdomain: str = None,
        layer: str = None,
        product: str = None,
        model: str = None,
        **options,
    ) -> None:
        self.org = org
        self.region = region
        self.domain = domain
        self.subdomain = subdomain
        self.layer = layer
        self.product = product
        self.model = model
        super().__init__(*args, **options)

    def to_resource_dict(self) -> dict:
        """
        Return the resource fields as a dictionary.

        Returns:
            A dictionary mapping each resource field name to its value.
        """
        return {field: getattr(self, field) for field in RESOURCE_FIELDS}

    @property
    def qualified_domain(self) -> str:
        """
        The qualified domain identifier, formatted as `org.region.domain`.
        """
        return ".".join(getattr(self, field) for field in DOMAIN_FIELDS)

    @property
    def qualified_subdomain(self) -> str:
        """
        The qualified subdomain identifier, formatted as `org.region.domain.subdomain`.
        """
        return ".".join(getattr(self, field) for field in SUBDOMAIN_FIELDS)

    @property
    def qualified_product(self) -> str:
        """
        The qualified product identifier, formatted as `layer.product.model`.
        """
        return ".".join(getattr(self, field) for field in PRODUCT_FIELDS)

    @property
    def qualified_resource(self) -> str:
        """
        The fully qualified resource identifier, formatted as
        `org.region.domain.subdomain.layer.product.model`.
        """
        return ".".join(getattr(self, field) for field in RESOURCE_FIELDS)
