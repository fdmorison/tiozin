from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class LineageDataset:
    namespace: str
    name: str

    @staticmethod
    def from_uri(uri: str) -> LineageDataset:
        # ref: https://openlineage.io/docs/spec/naming/
        parsed = urlparse(str(uri))

        if not parsed.scheme:
            # local path without scheme — keep as-is, do not resolve to absolute
            return LineageDataset(namespace="file", name=str(uri).strip("/"))

        if parsed.netloc:
            namespace = f"{parsed.scheme}://{parsed.netloc}"
        else:
            namespace = parsed.scheme

        name = parsed.path.strip("/")
        return LineageDataset(namespace=namespace, name=name)

    # --- SQL databases (database.schema.table) ---

    @staticmethod
    def from_postgres(
        host: str, port: int, database: str, schema: str, table: str
    ) -> LineageDataset:
        return LineageDataset(
            namespace=f"postgres://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def from_mssql(host: str, port: int, database: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"mssql://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def from_cratedb(
        host: str, port: int, database: str, schema: str, table: str
    ) -> LineageDataset:
        return LineageDataset(
            namespace=f"crate://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def from_db2(host: str, port: int, database: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"db2://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def from_trino(host: str, port: int, catalog: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"trino://{host}:{port}",
            name=f"{catalog}.{schema}.{table}",
        )

    @staticmethod
    def from_oracle(host: str, port: int, service: str, schema: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"oracle://{host}:{port}",
            name=f"{service}.{schema}.{table}",
        )

    # --- SQL databases (database.table, no schema) ---

    @staticmethod
    def from_mysql(host: str, port: int, database: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"mysql://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def from_hive(host: str, port: int, database: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"hive://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def from_teradata(host: str, port: int, database: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"teradata://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def from_oceanbase(host: str, port: int, database: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"oceanbase://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def from_cassandra(host: str, port: int, keyspace: str, table: str) -> LineageDataset:
        return LineageDataset(namespace=f"cassandra://{host}:{port}", name=f"{keyspace}.{table}")

    # --- cloud warehouses ---

    @staticmethod
    def from_bigquery(project: str, dataset: str, table: str) -> LineageDataset:
        return LineageDataset(namespace="bigquery", name=f"{project}.{dataset}.{table}")

    @staticmethod
    def from_snowflake(
        org: str, account: str, database: str, schema: str, table: str
    ) -> LineageDataset:
        return LineageDataset(
            namespace=f"snowflake://{org}-{account}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def from_redshift(
        cluster_id: str, region: str, port: int, database: str, schema: str, table: str
    ) -> LineageDataset:
        return LineageDataset(
            namespace=f"redshift://{cluster_id}.{region}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def from_athena(region: str, catalog: str, database: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"awsathena://athena.{region}.amazonaws.com",
            name=f"{catalog}.{database}.{table}",
        )

    @staticmethod
    def from_glue(region: str, account: str, database: str, table: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"arn:aws:glue:{region}:{account}",
            name=f"table/{database}/{table}",
        )

    @staticmethod
    def from_spanner(
        project: str, instance: str, database: str, schema: str, table: str
    ) -> LineageDataset:
        return LineageDataset(
            namespace=f"spanner://{project}:{instance}",
            name=f"{database}.{schema}.{table}",
        )

    # --- streaming ---

    @staticmethod
    def from_kafka(bootstrap_server: str, port: int, topic: str) -> LineageDataset:
        return LineageDataset(namespace=f"kafka://{bootstrap_server}:{port}", name=topic)

    @staticmethod
    def from_pubsub_topic(project: str, topic: str) -> LineageDataset:
        return LineageDataset(namespace="pubsub", name=f"topic:{project}:{topic}")

    @staticmethod
    def from_pubsub_subscription(project: str, subscription: str) -> LineageDataset:
        return LineageDataset(namespace="pubsub", name=f"subscription:{project}:{subscription}")

    # --- distributed file systems ---

    @staticmethod
    def from_hdfs(host: str, port: int, path: str) -> LineageDataset:
        return LineageDataset(
            namespace=f"hdfs://{host}:{port}",
            name=path.lstrip("/"),
        )
