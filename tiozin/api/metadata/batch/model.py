from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, Self

from pydantic import ConfigDict, Field, PrivateAttr

from tiozin import config
from tiozin.api.conventions import INTERNAL_PREFIX, RESOURCE_FIELDS
from tiozin.api.resourceful import FrozenResourceful
from tiozin.utils import current_context, default, epoch, isozformat, utcnow

from ...types import Attributes, Bookmarks, Counter, NominalTime, TechnicalTime, TimeOrderedId
from ..model import Metadata
from .enums import BatchStatus

if TYPE_CHECKING:
    from tiozin import BatchRegistry

_BOOKMARK_PREFIX = INTERNAL_PREFIX + "managed/"
_BOOKMARK_LOWER_KEY = _BOOKMARK_PREFIX + "{key}.lower"
_BOOKMARK_UPPER_KEY = _BOOKMARK_PREFIX + "{key}.upper"


class Batch(FrozenResourceful, Metadata):
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

    The resource a batch belongs to is identified by the fields defined by
    FrozenResourceful: org, region, domain, subdomain, layer, product, and
    model. They are required and frozen on construction, so a batch's
    resource identity never changes.

    Collections of batches form backlogs representing data awaiting processing.

    Attributes:
        id:
            Unique identifier of the batch. Generated as a UUIDv7, so ids are
            monotonically increasing and chronologically sortable.

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

    natural_key_fields: ClassVar[tuple[str, ...]] = (*RESOURCE_FIELDS, "nominal_time")

    id: TimeOrderedId = Field(frozen=True)

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

    def get_managed_bookmark_window(self, key: str) -> tuple[Any, ...]:
        lower = _BOOKMARK_LOWER_KEY.format(key=key)
        upper = _BOOKMARK_UPPER_KEY.format(key=key)
        return self.bookmarks.get(lower), self.bookmarks.get(upper)

    def get_managed_bookmark(self, key: str, fallback: Any = None) -> Any:
        """
        Return where this batch resumes reading.

        Managed bookmarks define a processing window. This method returns the window's
        lower bound, i.e. where the batch starts reading.

        Pair this with `set_managed_bookmark` to freeze the window and make replays
        process the exact same slice.

        Args:
            key:
                Name of the managed bookmark. Eg: updated_at, id, etc.

            fallback:
                Value returned when the bookmark does not exist.

        Returns:
            The window's lower bound, or `fallback` when no mark exists.
        """
        lower = _BOOKMARK_LOWER_KEY.format(key=key)
        lower_value = self.bookmarks.get(lower)
        return default(lower_value, fallback)

    def set_managed_bookmark(self, key: str, next_value: Any) -> Any:
        """
        Freeze this batch's processing window.

        On the first run, records the window's upper bound and returns `next_value`.
        On replay, this method becomes a no-op: it ignores `next_value` and returns
        the previously recorded value, so the batch always processes the same slice.

        Canonical watermark pattern:

            start = batch.get_managed_bookmark("max_updated_at")
            end   = batch.set_managed_bookmark("max_updated_at", source.max())
            data  = source.read(start, end)

        The first run discovers and freezes `end`. On replay, the same code returns
        the frozen value, so `read(start, end)` covers the exact same slice.

        Args:
            key:
                Name of the managed bookmark.

            next_value:
                Candidate upper bound for the processing window.

        Returns:
            The effective upper bound.
        """
        upper = _BOOKMARK_UPPER_KEY.format(key=key)
        if upper in self.bookmarks:
            return self.bookmarks[upper]

        lower = _BOOKMARK_LOWER_KEY.format(key=key)
        self.bookmarks.setdefault(lower, None)
        self.bookmarks[upper] = next_value
        return next_value

    def get_bookmark(self, key: str, fallback: Any = None) -> Any:
        """
        Return a free-form bookmark.

        Free-form bookmarks are plain progress markers with no processing window,
        freeze, or replay semantics. This reads the stored value.

        Args:
            key:
                Name of the bookmark.

            fallback:
                Value returned when the bookmark does not exist. Stored values such
                as `0` or `False` are returned unchanged.

        Returns:
            The stored value, or `fallback` when absent.
        """
        key = key.removeprefix(_BOOKMARK_PREFIX)
        return default(self.bookmarks.get(key), fallback)

    def set_bookmark(self, key: str, next_value: Any) -> Any:
        """
        Store a free-form bookmark.

        Unlike managed bookmarks, free-form bookmarks are simple key-value pairs
        with no processing window, freeze, or replay semantics. This stores the
        value, overwriting any previous one under the same key.

        Args:
            key:
                Name of the bookmark.

            next_value:
                Value to store.

        Returns:
            The stored value.
        """
        key = key.removeprefix(_BOOKMARK_PREFIX)
        self.bookmarks[key] = next_value
        return next_value

    def next_bookmarks(self) -> Bookmarks:
        bookmarks = deepcopy(self.bookmarks)
        for key in self.bookmarks:
            if key.startswith(_BOOKMARK_PREFIX):
                key = key.removeprefix(_BOOKMARK_PREFIX)
                upper = _BOOKMARK_UPPER_KEY.format(key=key)
                lower = _BOOKMARK_LOWER_KEY.format(key=key)
                if upper in bookmarks:
                    bookmarks[lower] = bookmarks.pop(upper)
        return bookmarks

    @property
    def retries(self) -> int:
        return max(0, self.attempts - 1)

    @property
    def qualified_natural_key(self) -> str:
        return f"{self.qualified_resource}.{isozformat(self.nominal_time)}"

    def __str__(self) -> str:
        return self.qualified_natural_key
