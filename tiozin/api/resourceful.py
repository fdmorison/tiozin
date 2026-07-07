from tiozin.api.conventions import DOMAIN_FIELDS, PRODUCT_FIELDS, RESOURCE_FIELDS


class Resourceful:
    """
    Mixin that adds a canonical resource identity to a class.

    Defines the standard resource fields (org, region, domain, subdomain,
    layer, product, and model) used to identify a Data Mesh resource, and
    provides helpers to expose them as a dictionary or as qualified
    dot-separated identifiers.
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
        **kwargs,
    ) -> None:
        self.org = org
        self.region = region
        self.domain = domain
        self.subdomain = subdomain
        self.layer = layer
        self.product = product
        self.model = model
        super().__init__(*args, **kwargs)

    def to_resource_dict(self) -> dict:
        return {field: getattr(self, field) for field in RESOURCE_FIELDS}

    @property
    def qualified_domain(self) -> str:
        return ".".join(getattr(self, field) for field in DOMAIN_FIELDS)

    @property
    def qualified_product(self) -> str:
        return ".".join(getattr(self, field) for field in PRODUCT_FIELDS)

    @property
    def qualified_resource(self) -> str:
        return ".".join(getattr(self, field) for field in RESOURCE_FIELDS)
