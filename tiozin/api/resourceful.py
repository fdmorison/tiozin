from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, model_validator

from tiozin.api.conventions import DOMAIN_FIELDS, PRODUCT_FIELDS, RESOURCE_FIELDS, SUBDOMAIN_FIELDS
from tiozin.exceptions.misc import RequiredArgumentError

from . import docs


class Resourceful:
    """
    Mixin that adds a canonical resource identity to a class.

    Defines the standard resource fields (org, region, domain, subdomain,
    layer, product, and model) used to identify a Data Mesh resource, and
    provides helpers to expose them as a dictionary or as qualified
    dot-separated identifiers.

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

    __resourceful_required__: ClassVar[bool] = True

    # Domain
    org: Annotated[str, Field(description=docs.ORG)]
    region: Annotated[str, Field(description=docs.REGION)]
    domain: Annotated[str, Field(description=docs.DOMAIN)]
    subdomain: Annotated[str, Field(description=docs.SUBDOMAIN)]
    # Product
    layer: Annotated[str, Field(description=docs.LAYER)]
    product: Annotated[str, Field(description=docs.PRODUCT)]
    model: Annotated[str, Field(description=docs.MODEL)]

    def __init__(self, *args, **options) -> None:
        if not isinstance(self, BaseModel):
            self.org = options.pop("org", None)
            self.region = options.pop("region", None)
            self.domain = options.pop("domain", None)
            self.subdomain = options.pop("subdomain", None)
            self.layer = options.pop("layer", None)
            self.product = options.pop("product", None)
            self.model = options.pop("model", None)
            self._resourceful_validator()

        super().__init__(*args, **options)

    @model_validator(mode="after")
    def _resourceful_validator(self) -> Resourceful:
        """
        Runs on every pydantic validation, not just __init__, so requiredness
        also holds for model_validate, model_copy, and other construction paths.
        """
        RequiredArgumentError.raise_if_missing(
            org=self.org,
            region=self.region,
            domain=self.domain,
            subdomain=self.subdomain,
            layer=self.layer,
            product=self.product,
            model=self.model,
            disable_=not self.__resourceful_required__,
        )
        return self

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

        Fields that are unset are omitted from the result.
        """
        values = (value for field in DOMAIN_FIELDS if (value := getattr(self, field)))
        return ".".join(values)

    @property
    def qualified_subdomain(self) -> str:
        """
        The qualified subdomain identifier, formatted as `org.region.domain.subdomain`.

        Fields that are unset are omitted from the result.
        """
        values = (value for field in SUBDOMAIN_FIELDS if (value := getattr(self, field)))
        return ".".join(values)

    @property
    def qualified_product(self) -> str:
        """
        The qualified product identifier, formatted as `layer.product.model`.

        Fields that are unset are omitted from the result.
        """
        values = (value for field in PRODUCT_FIELDS if (value := getattr(self, field)))
        return ".".join(values)

    @property
    def qualified_resource(self) -> str:
        """
        The fully qualified resource identifier, formatted as
        `org.region.domain.subdomain.layer.product.model`.

        Fields that are unset are omitted from the result.
        """
        values = (value for field in RESOURCE_FIELDS if (value := getattr(self, field)))
        return ".".join(values)


class OptionalResourceful(Resourceful):
    """
    Resourceful variant where the resource fields stay optional.

    Marks classes that don't yet require a full resource identity, so they're
    easy to find and migrate later.
    """

    __resourceful_required__ = False

    org: Annotated[str | None, Field(description=docs.ORG)] = None
    region: Annotated[str | None, Field(description=docs.REGION)] = None
    domain: Annotated[str | None, Field(description=docs.DOMAIN)] = None
    subdomain: Annotated[str | None, Field(description=docs.SUBDOMAIN)] = None
    layer: Annotated[str | None, Field(description=docs.LAYER)] = None
    product: Annotated[str | None, Field(description=docs.PRODUCT)] = None
    model: Annotated[str | None, Field(description=docs.MODEL)] = None


class FrozenResourceful(Resourceful):
    """
    Resourceful variant where the resource fields are required and immutable.

    Use for classes whose resource identity must not change after construction.
    """

    __resourceful_required__ = True

    org: Annotated[str, Field(description=docs.ORG, frozen=True)]
    region: Annotated[str, Field(description=docs.REGION, frozen=True)]
    domain: Annotated[str, Field(description=docs.DOMAIN, frozen=True)]
    subdomain: Annotated[str, Field(description=docs.SUBDOMAIN, frozen=True)]
    layer: Annotated[str, Field(description=docs.LAYER, frozen=True)]
    product: Annotated[str, Field(description=docs.PRODUCT, frozen=True)]
    model: Annotated[str, Field(description=docs.MODEL, frozen=True)]
