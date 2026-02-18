from __future__ import annotations

from pydantic import Field

from . import docs
from .manifest import Manifest


class InputManifest(Manifest):
    """
    Declarative data source definition.

    Specifies how and where data is read into the pipeline.
    """

    # Identity
    kind: str = Field(description=docs.KIND)
    name: str = Field(description=docs.INPUT_NAME)
    description: str | None = Field(None, description=docs.INPUT_DESCRIPTION)

    # Business Taxonomy
    org: str | None = Field(None, description=docs.INPUT_ORG)
    region: str | None = Field(None, description=docs.INPUT_REGION)
    domain: str | None = Field(None, description=docs.INPUT_DOMAIN)
    subdomain: str | None = Field(None, description=docs.INPUT_SUBDOMAIN)
    layer: str | None = Field(None, description=docs.INPUT_LAYER)
    product: str | None = Field(None, description=docs.INPUT_PRODUCT)
    model: str | None = Field(None, description=docs.INPUT_MODEL)

    # Specific
    schema: str | None = Field(None, description=docs.INPUT_SCHEMA)
    schema_subject: str | None = Field(None, description=docs.INPUT_SCHEMA_SUBJECT)
    schema_version: str | None = Field(None, description=docs.INPUT_SCHEMA_VERSION)
