from tiozin.exceptions import NotFoundError, RequiredArgumentError
from tiozin.utils import trim, trim_lower

from ..typehints import SparkIcebergCatalogType, SparkIcebergClass
from .spark_runner import SparkRunner


class SparkIcebergRunner(SparkRunner):
    """
    Spark runner for Apache Iceberg.

    This runner configures Spark to work with Iceberg tables by wiring the
    required Spark extensions and catalog-specific settings automatically.

    You only need to declare the catalog name and provide the corresponding
    configuration parameters. The runner translates these high-level arguments
    into the appropriate Spark SQL options.

    For details about Iceberg execution and configuration, refer to the official
    documentation:

    https://iceberg.apache.org/docs/latest/spark-configuration/#spark-sql-options

    Examples:

        # Hadoop catalog (filesystem-based)
        SparkIcebergRunner(
            catalog_name="local",
            catalog_type="hadoop",
            catalog_warehouse="s3://my-bucket/warehouse"
        )

        # Hive catalog
        SparkIcebergRunner(
            catalog_name="hive",
            catalog_type="hive",
            catalog_uri="thrift://hive-metastore:9083"
        )

        # AWS Glue catalog
        SparkIcebergRunner(
            catalog_name="glue",
            catalog_type="glue",
            catalog_warehouse="s3://my-bucket/warehouse"
        )

        # REST catalog
        SparkIcebergRunner(
            catalog_name="rest",
            catalog_type="rest",
            catalog_uri="http://catalog:8181"
        )

        # Nessie (or any custom REST-based catalog)
        SparkIcebergRunner(
            catalog_name="nessie",
            catalog_type="nessie",
            catalog_uri="http://nessie:19120/api/v1"
        )
    """

    _CATALOG_TYPES = {"hive", "hadoop", "rest", "glue", "nessie", "jdbc"}
    _SPARK_SQL_EXTENSIONS = "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
    _DEFAULT_SPARK_ICEBERG_CLASS = "org.apache.iceberg.spark.SparkSessionCatalog"

    def __init__(
        self,
        *,
        catalog_name: str,
        catalog_type: SparkIcebergCatalogType = None,
        catalog_impl: str = None,
        catalog_uri: str = None,
        catalog_warehouse: str = None,
        iceberg_class: SparkIcebergClass = None,
        **options,
    ) -> None:
        super().__init__(**options)

        RequiredArgumentError.raise_if_missing(
            catalog_name=catalog_name,
        ).raise_if(
            not catalog_type and not catalog_impl,
            "One of `catalog_type` or `catalog_impl` must be provided",
        )

        NotFoundError.raise_if(
            catalog_type and catalog_type not in self._CATALOG_TYPES,
            f"Unsupported Iceberg catalog type: '{catalog_type}'. "
            f"Supported: {', '.join(self._CATALOG_TYPES)}",
        )

        self.catalog_name = trim(catalog_name)
        self.catalog_type = trim_lower(catalog_type)
        self.catalog_impl = trim(catalog_impl)
        self.catalog_warehouse = trim(catalog_warehouse)
        self.catalog_uri = trim(catalog_uri)
        self.iceberg_class = trim(iceberg_class or self._DEFAULT_SPARK_ICEBERG_CLASS)

    def setup(self) -> None:
        if self.session:
            return

        self.info(f"Setting up Iceberg catalog: {self.catalog_name}")

        catalog = f"spark.sql.catalog.{self.catalog_name}"

        # --- Base Iceberg wiring ---
        self.options["spark.sql.extensions"] = self._SPARK_SQL_EXTENSIONS
        self.options[catalog] = self.iceberg_class

        # --- Apply catalog config ---
        if self.catalog_type:
            self.options[f"{catalog}.type"] = self.catalog_type

        if self.catalog_warehouse:
            self.options[f"{catalog}.warehouse"] = self.catalog_warehouse

        if self.catalog_uri:
            self.options[f"{catalog}.uri"] = self.catalog_uri

        if self.catalog_impl:
            self.options[f"{catalog}.catalog-impl"] = self.catalog_impl

        super().setup()
