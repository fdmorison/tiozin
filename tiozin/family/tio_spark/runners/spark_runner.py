from __future__ import annotations

from pyspark.sql import DataFrame, DataFrameWriter, SparkSession
from pyspark.sql.streaming.readwriter import DataStreamWriter

from tiozin import Context, Runner, config
from tiozin.exceptions import JobError, NotInitializedError
from tiozin.utils.helpers import as_list

from ..typehints import SparkPlan

DEFAULT_LOGLEVEL = "WARN"


class SparkRunner(Runner[SparkPlan]):
    """
    Executes Tiozin pipelines using Apache Spark.

    This runner is responsible for creating and managing a SparkSession and
    executing Spark execution plans produced by inputs, transforms, and
    outputs. It supports batch and streaming execution transparently.

    The runner executes:
        - Spark DataFrames (actions)
        - DataFrameWriters (file outputs)
        - DataStreamWriters (streaming queries)

    Spark configuration is provided via runner options and applied during
    session initialization.

    For details about Spark execution and configuration, refer to the official
    Spark documentation at:

    https://spark.apache.org/docs/latest/

    Attributes:
        master:
            Spark master URL for cluster connection (e.g. ``local[*]``,
            ``spark://host:7077``, ``yarn``). If not provided, Spark will
            use the default configuration.

        endpoint:
            Spark Connect server endpoint for remote session (e.g.
            ``sc://localhost:15002``). Enables client-server architecture
            introduced in Spark 3.4+. Mutually exclusive with ``master``.

        enable_hive_support:
            When ``True``, enables Hive metastore integration for reading
            and writing Hive tables. Defaults to ``False``.

        log_level:
            Spark log level applied to the SparkContext (e.g. ``WARN``,
            ``INFO``). Defaults to ``WARN``.

        jars_packages:
            List of Maven coordinates to be downloaded and added to the
            Spark classpath (e.g.
            ``org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0``).
            This is equivalent to setting ``spark.jars.packages``.

        **options:
            Spark configuration options passed directly to the
            ``SparkSession.builder`` (e.g. ``spark.executor.memory``).

    Examples:

        ```python
        SparkRunner(
            master="local[*]",
            enable_hive_support=True,
            log_level="WARN",
            jars_packages=[
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0"
            ],
        )
        ```

        ```yaml
        runner:
          kind: SparkRunner
          master: local[*]
          enable_hive_support: true
          log_level: WARN
          jars_packages:
            - org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0
          spark.executor.memory: 4g
          spark.sql.shuffle.partitions: 200
        ```

        Using Spark Connect:

        ```yaml
        runner:
          kind: SparkRunner
          endpoint: sc://localhost:15002
        ```
    """

    def __init__(
        self,
        master: str = None,
        endpoint: str = None,
        enable_hive_support: bool = False,
        log_level: str = None,
        jars_packages: list[str] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        self.master = master
        self.endpoint = endpoint
        self.enable_hive_support = enable_hive_support
        self.log_level = log_level or DEFAULT_LOGLEVEL
        self.jars_packages = as_list(jars_packages, [])
        self._spark: SparkSession = None

    @property
    def session(self) -> SparkSession:
        """Returns the active SparkSession.

        Raises:
            NotInitializedError: If accessed before ``setup()`` has been called.
        """
        NotInitializedError.raise_if(
            self._spark is None,
            message="Spark session not initialized for {tiozin}",
            tiozin=self,
        )
        return self._spark

    def setup(self, context: Context) -> None:
        if self._spark:
            return

        builder: SparkSession.Builder = SparkSession.builder
        builder = (
            builder.appName(context.name)
            .config("spark.sql.session.timeZone", str(config.app_timezone))
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.jars.packages", ",".join(self.jars_packages))
        )

        if self.enable_hive_support:
            self.info("🐝 Hive Support is enabled")
            builder = builder.enableHiveSupport()

        if self.master:
            self.info(f"🔌 Connecting to the Spark Master at {self.master}")
            builder = builder.master(self.master)

        if self.endpoint:
            self.info(f"🔌 Connecting to the Spark Connect server at {self.endpoint}")
            builder = builder.remote(self.endpoint)

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
