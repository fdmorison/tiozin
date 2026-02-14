from pydantic import Field

from . import docs
from .manifest import Manifest


class TransformManifest(Manifest):
    """
    Declarative transformation definition.

    Specifies operations that modify or enrich data.
    """

    # Identity
    kind: str = Field(description=docs.KIND)
    name: str = Field(description=docs.TRANSFORM_NAME)
    description: str | None = Field(None, description=docs.TRANSFORM_DESCRIPTION)

    # Business Taxonomy
    org: str | None = Field(None, description=docs.TRANSFORM_ORG)
    region: str | None = Field(None, description=docs.TRANSFORM_REGION)
    domain: str | None = Field(None, description=docs.TRANSFORM_DOMAIN)
    product: str | None = Field(None, description=docs.TRANSFORM_PRODUCT)
    model: str | None = Field(None, description=docs.TRANSFORM_MODEL)
    layer: str | None = Field(None, description=docs.TRANSFORM_LAYER)

    @classmethod
    def for_kind(cls) -> type:
        from tiozin import Transform

        return Transform
