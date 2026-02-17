from pyspark.sql import DataFrame, SparkSession

from tiozin import CoTransform, Input, Output, Transform, active_session, tioproxy

from .compose.proxies.step_proxy import SparkStepProxy


class SparkStepMixin:
    """
    Mixin that provides cross-cutting, engine-specific behavior for Spark execution steps.

    This mixin acts as an extension point for features that are common across multiple
    Spark step implementations, but should not be handled by individual Tiozin plugins.

    Typical responsibilities include:
    - Capturing and handling generic parameters declared in YAML definitions
    - Applying execution-time behaviors shared across Spark steps
    - Providing access to the Spark execution context when required

    The mixin allows individual Spark step implementations to remain focused on their
    domain logic, while shared concerns are handled in a single, consistent place.
    """

    def __init__(self, **options) -> None:
        super().__init__(**options)

    @property
    def spark(self) -> SparkSession:
        """
        The active Spark session bound to the current runner execution.

        Returns:
            SparkSession: The active Spark session.

        Raises:
            NotInitializedError: If accessed outside of an active runner scope.
        """
        return active_session()


@tioproxy(SparkStepProxy)
class SparkInput(SparkStepMixin, Input[DataFrame]):
    """
    Base class for Spark input steps.

    SparkInput steps act as data sources that produce Spark ``DataFrame`` objects
    and operate within the Spark session managed by the active runner.
    """


@tioproxy(SparkStepProxy)
class SparkTransform(SparkStepMixin, Transform[DataFrame]):
    """
    Base class for single-input Spark transform steps.

    SparkTransform steps consume a single Spark ``DataFrame``, apply Spark-based
    transformations, and emit a transformed ``DataFrame`` within the same
    runner-managed Spark session.
    """


@tioproxy(SparkStepProxy)
class SparkCoTransform(SparkStepMixin, CoTransform[DataFrame]):
    """
    Base class for multi-input Spark transform steps.

    SparkCoTransform steps operate on multiple Spark ``DataFrame`` inputs and
    combine or transform them using Spark within the active runner session.
    """


@tioproxy(SparkStepProxy)
class SparkOutput(SparkStepMixin, Output[DataFrame]):
    """
    Base class for Spark output steps.

    SparkOutput steps consume a Spark ``DataFrame`` and materialize, persist,
    or export the result using the Spark session provided by the active runner.
    """
