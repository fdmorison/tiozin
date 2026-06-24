from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import NAMESPACE_OID, uuid5

from pydantic import Field, field_validator, model_validator

from tiozin.utils import utcnow

from ..model import Metadata
from .status import StateStatus

if TYPE_CHECKING:
    from tiozin.api.metadata.state.registry import StateRegistry


class State(Metadata):
    """
    Represents the execution state of a pipeline partition.

    A state records the progress and lifecycle of incremental processing
    for a specific taxonomy and cursor.

    States support two common patterns:

    - Watermarks, where a single state stores the latest processed cursor.
    - Pending events, where multiple states represent cursors awaiting
      processing and track their execution lifecycle independently.

    Attributes:
        id:
            Deterministic UUID derived from the natural key (taxonomy + cursor). Stable across
            updates to the same pair; the registry uses it to upsert rather than insert duplicates.

        org:
            Organization that owns the state.

        region:
            Region associated with the state.

        domain:
            Domain that owns the pipeline.

        subdomain:
            Subdomain within the domain.

        layer:
            Data layer associated with the pipeline.

        product:
            Product associated with the pipeline.

        model:
            Model associated with the pipeline.

        cursor:
            Processing position tracked by the state, such as a watermark, an incremental date
            partition, an offset, or any other job-defined value. Advances with each successful
            execution. Tiozin treats cursor values as opaque strings; interpretation and ownership
            belong to the job.

        status:
            Current lifecycle status of the cursor. Controls which transitions the registry will
            accept. See ``StateStatus`` for valid values and allowed transitions.

        attributes:
            Arbitrary job-specific metadata persisted alongside the state. Jobs can write values
            such as record counts, source file paths, checksums, or execution details and read them
            back on the next run. Tiozin does not interpret this field.

        created_at:
            UTC timestamp set once when the state is first registered.

        updated_at:
            UTC timestamp refreshed by the registry on every write.
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

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @model_validator(mode="after")
    def _init_id(self) -> State:
        if self.id is None:
            self.id = str(uuid5(NAMESPACE_OID, ".".join(self.natural_key)))
        return self

    @field_validator("attributes", mode="before")
    @classmethod
    def _init_attributes(cls, v: dict | None) -> dict:
        return v or {}

    def _registry(self) -> StateRegistry:
        from tiozin.api.context import Context

        return Context.current().registries.state

    def register(self) -> State:
        """Persists this state in the registry for the first time."""
        return self._registry().register(self)

    def begin(self, attributes: dict = None) -> State:
        """Transitions the state to in-progress, indicating processing has begun."""
        return self._registry().begin(self, attributes)

    def commit(self, attributes: dict = None) -> State:
        """Marks the state as successfully completed."""
        return self._registry().commit(self, attributes)

    def fail(self, attributes: dict = None) -> State:
        """Marks the state as failed. Does not guarantee any data rollback."""
        return self._registry().fail(self, attributes)

    def cancel(self, attributes: dict = None) -> State:
        """Marks the state as cancelled, permanently abandoning this cursor."""
        return self._registry().cancel(self, attributes)

    def quarantine(self, attributes: dict = None) -> State:
        """Isolates the state after an unrecoverable error, preventing further processing."""
        return self._registry().quarantine(self, attributes)

    def replay(self, attributes: dict = None) -> State:
        """Resets the state to pending, forcing reprocessing regardless of current status."""
        return self._registry().replay(self, attributes)

    @property
    def taxonomy(self) -> str:
        """Single key that identifies the job within the platform hierarchy."""
        return ".".join(self.taxonomy_key())

    @property
    def taxonomy_key(self) -> tuple[str, ...]:
        """Composite key that identifies the job within the platform hierarchy."""
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
        """Composite key that uniquely identifies a state within a job context."""
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
