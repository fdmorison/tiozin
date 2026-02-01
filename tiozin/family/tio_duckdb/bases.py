from duckdb import DuckDBPyConnection, DuckDBPyRelation

from tiozin import CoTransform, Input, Output, Transform, active_session
from tiozin.assembly import tioproxy

from .proxy import DuckdbStepProxy


class StepMixin:
    """
    Mixin that provides cross-cutting, engine-specific behavior for execution steps.

    This mixin acts as an extension point for features that are common across multiple
    step implementations of the same engine, but should not be handled by individual
    plugins.

    Typical responsibilities include:
    - Capturing and handling generic parameters declared in YAML definitions
    - Applying execution-time behaviors (e.g. debugging, inspection, or logging hooks)
    - Providing access to engine-level execution context when required

    The mixin allows individual step implementations to remain focused on their
    domain logic, while shared concerns are handled in a single, consistent place.
    """

    def __init__(self, **options) -> None:
        super().__init__(**options)

    @property
    def duckdb(self) -> DuckDBPyConnection:
        """
        The active DuckDB connection bound to the current runner execution.

        Returns:
            DuckDBPyConnection: The active DuckDB connection.

        Raises:
            NotInitializedError: If accessed outside of an active runner scope.
        """
        return active_session()


@tioproxy(DuckdbStepProxy)
class DuckdbInput(StepMixin, Input[DuckDBPyRelation]):
    """
    Base class for DuckDB input steps.

    DuckdbInput steps act as data sources that produce ``DuckDBPyRelation`` objects
    and operate within the DuckDB session managed by the active runner.
    """


@tioproxy(DuckdbStepProxy)
class DuckdbTransform(StepMixin, Transform[DuckDBPyRelation]):
    """
    Base class for single-input DuckDB transform steps.

    DuckdbTransform steps consume a single ``DuckDBPyRelation``, apply DuckDB-based
    transformations, and emit a transformed ``DuckDBPyRelation`` within the same
    runner-managed DuckDB session.
    """


@tioproxy(DuckdbStepProxy)
class DuckdbCoTransform(StepMixin, CoTransform[DuckDBPyRelation]):
    """
    Base class for multi-input DuckDB transform steps.

    DuckdbCoTransform steps operate on multiple ``DuckDBPyRelation`` inputs and
    combine or transform them using DuckDB within the active runner session.
    """


@tioproxy(DuckdbStepProxy)
class DuckdbOutput(StepMixin, Output[DuckDBPyRelation]):
    """
    Base class for DuckDB output steps.

    DuckdbOutput steps consume a ``DuckDBPyRelation`` and materialize or export the
    result using the DuckDB session provided by the active runner.
    """
