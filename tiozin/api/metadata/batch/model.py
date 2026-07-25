from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar, Self

from pydantic import ConfigDict, Field, PrivateAttr

from tiozin import config
from tiozin.api.conventions import RESOURCE_FIELDS
from tiozin.utils import current_context, epoch, isozformat, utcnow

from ...types import Attributes, Bookmarks, Counter, NominalTime, TechnicalTime, TimeOrderedId
from ..model import Metadata
from .enums import BatchStatus

if TYPE_CHECKING:
    from tiozin import BatchRegistry


class Batch(Metadata):
    """
    Stateful physical batch of data.

    A batch is a portion of data delimited by a nominal processing window. It
    may represent either an increment or the full history; the window, not the
    batch, determines which. Typical physical representations include
    partitions, files, offset ranges, or snapshots.

    A batch is not an execution. It remains the same batch regardless of how
    many executions are required to process it.

    Batches are uniquely identified by `(resource, nominal_time)`. Their status
    evolves over time as they are processed, replayed, quarantined, or canceled.

    Collections of batches form backlogs representing data awaiting processing.

    Attributes:
        id:
            Unique identifier of the batch. Generated as a UUIDv7, so ids are
            monotonically increasing and chronologically sortable.

        org:
            Organization that owns the resource.

        region:
            Region associated with the resource.

        domain:
            Domain that owns the resource.

        subdomain:
            Subdomain within the domain.

        layer:
            Data layer associated with the resource.

        product:
            Product associated with the resource.

        model:
            Model associated with the resource.

        nominal_time:
            UTC datetime that uniquely identifies the logical execution time of the run.
            It represents the expected execution time rather than the actual execution time.
            Truncated according to the run cadence (minute precision by default).
            Equivalent to OpenLineage's nominal time concept, see
            https://openlineage.io/docs/1.47.0/spec/facets/run-facets/nominal_time/

        nominal_start_time:
            UTC datetime where the batch's processing window begins.

        nominal_end_time:
            UTC datetime where the batch's processing window ends.

        status:
            Current lifecycle status of the batch.

        attempts:
            Number of attempts to execute the batch since it was started for
            first time or replayed. Incremented on every begin.

        attributes:
            Arbitrary metadata associated with the batch, propagated across the
            pipeline layers of a single execution. Attributes allow jobs to
            propagate progress and resume incremental processing in downstream
            pipeline layers. Typical values include record counts, paths,
            partitions, table names, execution details, or any other
            plugin-defined information.

        bookmarks:
            Arbitrary metadata associated with the batch, propagated across
            pipeline executions. Bookmarks allow jobs to track progress and
            resume incremental processing across executions. Typical values
            include watermarks, checkpoints, API tokens, or any other
            plugin-defined information.

        framework:
            The framework version that created the batch in `{name}/{version}` syntax.

        created_at:
            UTC timestamp when the batch was first registered.

        updated_at:
            UTC timestamp when the batch was last updated.
    """

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        validate_default=True,
    )

    _registry_ref: BatchRegistry = PrivateAttr(default=None)

    resource_fields: ClassVar[tuple[str, ...]] = RESOURCE_FIELDS
    natural_key_fields: ClassVar[tuple[str, ...]] = (*RESOURCE_FIELDS, "nominal_time")

    id: TimeOrderedId = Field(frozen=True)

    org: str = Field(frozen=True)
    region: str = Field(frozen=True)
    domain: str = Field(frozen=True)
    subdomain: str = Field(frozen=True)
    layer: str = Field(frozen=True)
    product: str = Field(frozen=True)
    model: str = Field(frozen=True)

    nominal_time: NominalTime = Field(frozen=True)
    nominal_start_time: NominalTime = Field(frozen=True, default_factory=epoch)
    nominal_end_time: NominalTime = Field(default_factory=utcnow)

    status: BatchStatus = BatchStatus.PENDING
    attempts: Counter

    bookmarks: Bookmarks
    _bookmarks_snapshot: Bookmarks = PrivateAttr(default=None)

    attributes: Attributes
    _attributes_snapshot: Attributes = PrivateAttr(default=None)

    framework: str = Field(default=config.app_identifier, frozen=True)
    created_at: TechnicalTime = Field(default_factory=utcnow, frozen=True)
    updated_at: TechnicalTime = Field(default_factory=utcnow)

    def model_post_init(self, __context) -> None:
        self._attributes_snapshot = MappingProxyType(deepcopy(self.attributes))
        self._bookmarks_snapshot = MappingProxyType(deepcopy(self.bookmarks))

    def _registry(self) -> BatchRegistry:
        return self._registry_ref or current_context().registries.batch

    def register(self) -> Self:
        return self._registry().register(self)

    def begin(self, **attributes) -> Self:
        registry = self._registry()
        self.attempts += 1
        self.status = self.status.transition_to(BatchStatus.RUNNING, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def commit(self, **attributes) -> Self:
        registry = self._registry()
        self.status = self.status.transition_to(BatchStatus.SUCCEEDED, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def rollback(self, error: Exception = None, **attributes) -> Self:
        registry = self._registry()
        self.attributes = deepcopy(dict(self._attributes_snapshot))
        self.bookmarks = deepcopy(dict(self._bookmarks_snapshot))

        if error:
            self.attributes["__error"] = str(error)

        self.status = self.status.transition_to(BatchStatus.FAILED, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def cancel(self, **attributes) -> Self:
        registry = self._registry()
        self.status = self.status.transition_to(BatchStatus.CANCELED, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def quarantine(self, error: Exception = None, **attributes) -> Self:
        registry = self._registry()

        if error:
            self.attributes["__error"] = str(error)

        self.status = self.status.transition_to(BatchStatus.QUARANTINED, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def replay(self, **attributes) -> Self:
        registry = self._registry()

        if self.status.is_terminal():
            self.attempts = 0

        self.status = self.status.transition_to(BatchStatus.PENDING, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    @property
    def retries(self) -> int:
        return max(0, self.attempts - 1)

    @property
    def qualified_resource(self) -> str:
        return ".".join(getattr(self, field) for field in self.resource_fields)

    @property
    def qualified_natural_key(self) -> str:
        return f"{self.qualified_resource}.{isozformat(self.nominal_time)}"

    def __str__(self) -> str:
        return self.qualified_natural_key
