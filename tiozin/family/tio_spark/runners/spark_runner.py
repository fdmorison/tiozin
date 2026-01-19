from __future__ import annotations

from typing import TypeAlias

from pyspark.sql import DataFrame, DataFrameWriter, SparkSession
from pyspark.sql.streaming.readwriter import DataStreamWriter

from tiozin import Context, Runner, config
from tiozin.exceptions import JobError
from tiozin.utils.helpers import as_list

DEFAULT_LOGLEVEL = "WARN"

SparkPlan: TypeAlias = DataFrame | DataFrameWriter | DataStreamWriter | None


class SparkRunner(Runner[SparkPlan]):
    """
    Spark execution backend for tiozin pipelines.

    Manages SparkSession lifecycle and executes Spark DataFrames,
    DataFrameWriters, and DataStreamWriters.
    """

    def __init__(
        self,
        log_level: str = None,
        **options,
    ) -> None:
        super().__init__(**options)
        self.log_level = log_level or DEFAULT_LOGLEVEL
        self._spark: SparkSession = None

    @property
    def session(self) -> SparkSession:
        """Returns the active SparkSession, or None if not started."""
        return self._spark

    def setup(self, context: Context) -> None:
        if self._spark:
            return

        builder: SparkSession.Builder = SparkSession.builder
        builder = (
            builder.appName(context.name)
            .config("spark.sql.session.timeZone", str(config.app_timezone))
            .config("spark.sql.adaptive.enabled", "true")
        )

        for name, value in self.options.items():
            builder = builder.config(name, value)

        self._spark = builder.getOrCreate()
        self._spark.sparkContext.setLogLevel(self.log_level)
        context.session["spark"] = self._spark
        self.info(f"🔥 SparkSession ready for {context.name}")

    def run(self, _: Context, execution_plan: SparkPlan) -> None:
        for result in as_list(execution_plan):
            match result:
                case None:
                    self.warning("Skipping: job was already run.")
                case DataFrame():
                    self.info("Running Spark DataFrame Action")
                    result.count()
                case DataFrameWriter():
                    self.info("Running Spark DataFrameWriter")
                    result.save()
                case DataStreamWriter():
                    self.info("Running Spark Streaming Query")
                    result.start().awaitTermination()
                case _:
                    raise JobError(f"Unsupported Spark plan: {type(result)}")
        return None

    def teardown(self, _: Context) -> None:
        if self._spark:
            self._spark.stop()
            self.info("SparkSession stopped")
            self._spark = None
