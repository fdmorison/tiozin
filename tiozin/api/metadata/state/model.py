from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import NAMESPACE_OID, uuid5

from pendulum import DateTime
from pydantic import Field, field_validator, model_validator

from tiozin.utils import utcnow

from ..model import Metadata
from .status import StateStatus

if TYPE_CHECKING:
    from tiozin.api.metadata.state.registry import StateRegistry


class State(Metadata):
    """
    Tracks the state of a pipeline partition.

    Supports two usage patterns:
    - Watermark: one record per taxonomy, partition holds the current position.
    - Pending events: many records per taxonomy, one per partition to process.

    The natural key is the composite (org, region, domain, subdomain, layer,
    product, model, partition).
    """

    id: str | None = None

    org: str
    region: str
    domain: str
    subdomain: str
    layer: str
    product: str
    model: str

    cursor: str
    status: StateStatus = StateStatus.PENDING
    attributes: dict = Field(default_factory=dict)

    created_at: DateTime = Field(default_factory=utcnow)
    updated_at: DateTime = Field(default_factory=utcnow)

    @field_validator("attributes", mode="before")
    @classmethod
    def _init_attributes(cls, v: dict | None) -> dict:
        return v or {}

    def _registry(self) -> StateRegistry:
        from tiozin.api.context import Context

        return Context.current().registries.state

    def register(self) -> State:
        return self._registry().register(self)

    def start(self, attributes: dict = None) -> State:
        return self._registry().start(self, attributes)

    def commit(self, attributes: dict = None) -> State:
        return self._registry().commit(self, attributes)

    def rollback(self, attributes: dict = None) -> State:
        return self._registry().rollback(self, attributes)

    def cancel(self, attributes: dict = None) -> State:
        return self._registry().cancel(self, attributes)

    def quarantine(self, attributes: dict = None) -> State:
        return self._registry().quarantine(self, attributes)

    def replay(self, attributes: dict = None) -> State:
        return self._registry().replay(self, attributes)

    @property
    def taxonomy(self) -> str:
        return ".".join(self.taxonomy_key())

    @property
    def taxonomy_key(self) -> tuple[str, ...]:
        return (
            self.org,
            self.region,
            self.domain,
            self.subdomain,
            self.layer,
            self.product,
            self.model,
        )

    @property
    def natural_key(self) -> tuple[str, ...]:
        return (
            self.org,
            self.region,
            self.domain,
            self.subdomain,
            self.layer,
            self.product,
            self.model,
            self.cursor,
        )

    @model_validator(mode="after")
    def _generate_id(self) -> State:
        if self.id is None:
            self.id = str(uuid5(NAMESPACE_OID, ".".join(self.natural_key)))
        return self
