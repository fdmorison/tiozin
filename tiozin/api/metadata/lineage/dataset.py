from __future__ import annotations

from urllib.parse import urlparse

from tiozin.utils.io import normalize_uri

from ..model import Model


class LineageDataset(Model):
    """
    Represents a dataset in lineage.

    OpenLineage datasets are identified by a `(namespace, name)` pair.

    This class provides convenience helpers for constructing datasets for
    common systems following OpenLineage naming conventions.

    https://openlineage.io/docs/spec/naming/
    """

    namespace: str
    name: str

    @staticmethod
    def from_uri(uri: str) -> LineageDataset:
        uri = normalize_uri(uri, as_absolute=False, strip_glob=True, strip_partitions=True)
        parsed = urlparse(uri)

        if not parsed.scheme:
            return LineageDataset(namespace="file", name=uri)

        if parsed.netloc:
            namespace = f"{parsed.scheme}://{parsed.netloc}"
        else:
            namespace = parsed.scheme

        name = parsed.path.lstrip("/")
        return LineageDataset(namespace=namespace, name=name)

    # --- SQL databases (database.schema.table) ---

    @staticmethod
    def postgres(host: str, port: int, database: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"postgres://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def mssql(host: str, port: int, database: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"mssql://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def cratedb(host: str, port: int, database: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"crate://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def db2(host: str, port: int, database: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"db2://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def trino(host: str, port: int, catalog: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"trino://{host}:{port}",
            name=f"{catalog}.{schema}.{table}",
        )

    @staticmethod
    def oracle(host: str, port: int, service: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"oracle://{host}:{port}",
            name=f"{service}.{schema}.{table}",
        )

    # --- SQL databases (database.table, no schema) ---

    @staticmethod
    def mysql(host: str, port: int, database: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"mysql://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def hive(host: str, port: int, database: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"hive://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def teradata(host: str, port: int, database: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"teradata://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def oceanbase(host: str, port: int, database: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"oceanbase://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def cassandra(host: str, port: int, keyspace: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"cassandra://{host}:{port}", name=f"{keyspace}.{table}")

    # --- cloud warehouses ---

    @staticmethod
    def bigquery(project: str, dataset: str, table: str) -> LineageDataset:
        return LineageDataset(namespace="bigquery", name=f"{project}.{dataset}.{table}")

    @staticmethod
    def snowflake(org: str, account: str, database: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"snowflake://{org}-{account}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def redshift(
        cluster_id: str, region: str, port: int, database: str, schema: str, table: str
    ) -> LineageDataset:
        return LineageDataset(
            namespace=f"redshift://{cluster_id}.{region}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def athena(region: str, catalog: str, database: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"awsathena://athena.{region}.amazonaws.com",
            name=f"{catalog}.{database}.{table}",
        )

    @staticmethod
    def glue(region: str, account: str, database: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"arn:aws:glue:{region}:{account}",
            name=f"table/{database}/{table}",
        )

    @staticmethod
    def spanner(
        project: str, instance: str, database: str, schema: str, table: str
    ) -> LineageDataset:
        return LineageDataset(
            namespace=f"spanner://{project}:{instance}",
            name=f"{database}.{schema}.{table}",
        )

    # --- streaming ---

    @staticmethod
    def kafka(bootstrap_server: str, port: int, topic: str) -> LineageDataset:
        return LineageDataset(namespace=f"kafka://{bootstrap_server}:{port}", name=topic)

    @staticmethod
    def pubsub_topic(project: str, topic: str) -> LineageDataset:
        return LineageDataset(namespace="pubsub", name=f"topic:{project}:{topic}")

    @staticmethod
    def pubsub_subscription(project: str, subscription: str) -> LineageDataset:
        return LineageDataset(namespace="pubsub", name=f"subscription:{project}:{subscription}")

    # --- distributed file systems ---

    @staticmethod
    def hdfs(host: str, port: int, path: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"hdfs://{host}:{port}",
            name=path.lstrip("/"),
        )
