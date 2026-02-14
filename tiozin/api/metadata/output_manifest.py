from __future__ import annotations

from pydantic import Field

from . import docs
from .manifest import Manifest


class OutputManifest(Manifest):
    """
    Declarative data destination definition.

    Specifies where and how processed data is written.
    """

    # Identity
    kind: str = Field(description=docs.KIND)
    name: str = Field(description=docs.OUTPUT_NAME)
    description: str | None = Field(None, description=docs.OUTPUT_DESCRIPTION)

    # Business Taxonomy
    org: str | None = Field(None, description=docs.OUTPUT_ORG)
    region: str | None = Field(None, description=docs.OUTPUT_REGION)
    domain: str | None = Field(None, description=docs.OUTPUT_DOMAIN)
    product: str | None = Field(None, description=docs.OUTPUT_PRODUCT)
    model: str | None = Field(None, description=docs.OUTPUT_MODEL)
    layer: str | None = Field(None, description=docs.OUTPUT_LAYER)

    @classmethod
    def for_kind(cls) -> type:
        from tiozin import Output

        return Output
