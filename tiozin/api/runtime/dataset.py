from __future__ import annotations

from typing import Generic, Self, TypeVar
from urllib.parse import urlparse

import wrapt

from tiozin.exceptions import RequiredArgumentError
from tiozin.utils.io import normalize_uri

from ..metadata.schema.model import Schema

TData = TypeVar("TData")


class Datasets:
    def __init__(self, inputs: list[Dataset] = None, outputs: Dataset = None) -> None:
        self.inputs = inputs or []
        self.outputs = outputs or []


class Dataset(wrapt.ObjectProxy, Generic[TData]):
    """
    Wraps a data object (DataFrame, Relation, etc.) with identity and schema metadata.

    Datasets are identified by a `(namespace, name)` pair following OpenLineage naming
    conventions, and carry an optional `Schema` for lineage facet emission.

    Factory methods cover the most common systems out of the box:

        Dataset.from_uri("s3://bucket/path/")
        Dataset.postgres(host, port, database, schema, table)
        Dataset.kafka(bootstrap_server, port, topic)

    https://openlineage.io/docs/spec/naming/
    """

    def __init__(
        self, data: TData, namespace: str = None, name: str = None, schema: Schema = None
    ) -> None:
        RequiredArgumentError.raise_if(
            data is None,
            "Dataset cannot be null. If there is no data, return an empty dataset instead, "
            "for example [] or Dataset.wrap([]), or an empty dataset in Spark or DuckDB.",
        )
        super().__init__(data)
        self._self_schema = schema
        self._self_namespace = namespace
        self._self_name = name

    def __repr__(self) -> str:
        return (
            f"Dataset("
            f"namespace={self.tiozin_namespace}, "
            f"name={self.tiozin_name}, "
            f"data={type(self.tiozin_data) if self.tiozin_data is not None else None}, "
            f"schema={self.tiozin_schema})"
        )

    # --- wrapping ---

    @classmethod
    def wrap(cls, obj: object) -> Dataset:
        return obj if isinstance(obj, cls) else cls(obj)

    @staticmethod
    def unwrap(obj: object) -> object:
        return obj.__wrapped__ if isinstance(obj, Dataset) else obj

    # --- accessors ---

    @property
    def tiozin_data(self) -> TData:
        return self.__wrapped__

    @property
    def tiozin_namespace(self) -> str:
        return self._self_namespace

    @property
    def tiozin_name(self) -> str:
        return self._self_name

    @property
    def tiozin_schema(self) -> Schema:
        return self._self_schema

    # --- enrichment (first-write-wins) ---

    def with_schema(self, schema: Schema | None) -> Self:
        self._self_schema = self._self_schema or schema
        return self

    def with_namespace(self, namespace: str | None) -> Self:
        self._self_namespace = self._self_namespace or namespace
        return self

    def with_name(self, name: str | None) -> Self:
        self._self_name = self._self_name or name
        return self

    def merge(self, other: Dataset) -> Self:
        if other is not None:
            self.with_schema(other.tiozin_schema).with_namespace(other.tiozin_namespace).with_name(
                other.tiozin_name
            )
        return self

    # --- open lineage factories ---

    @staticmethod
    def from_uri(uri: str) -> Dataset:
        uri = normalize_uri(uri, as_absolute=False, strip_glob=True, strip_partitions=True)
        parsed = urlparse(uri)

        if not parsed.scheme:
            return Dataset(data=[], namespace="file", name=uri)

        if parsed.netloc:
            namespace = f"{parsed.scheme}://{parsed.netloc}"
        else:
            namespace = parsed.scheme

        name = parsed.path.lstrip("/")
        return Dataset(data=[], namespace=namespace, name=name)

    # --- SQL databases (database.schema.table) ---

    @staticmethod
    def postgres(host: str, port: int, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"postgres://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def mssql(host: str, port: int, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"mssql://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def cratedb(host: str, port: int, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"crate://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def db2(host: str, port: int, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"db2://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def trino(host: str, port: int, catalog: str, schema: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"trino://{host}:{port}",
            name=f"{catalog}.{schema}.{table}",
        )

    @staticmethod
    def oracle(host: str, port: int, service: str, schema: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"oracle://{host}:{port}",
            name=f"{service}.{schema}.{table}",
        )

    # --- SQL databases (database.table, no schema) ---

    @staticmethod
    def mysql(host: str, port: int, database: str, table: str) -> Dataset:
        return Dataset(data=[], namespace=f"mysql://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def hive(host: str, port: int, database: str, table: str) -> Dataset:
        return Dataset(data=[], namespace=f"hive://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def teradata(host: str, port: int, database: str, table: str) -> Dataset:
        return Dataset(data=[], namespace=f"teradata://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def cassandra(host: str, port: int, keyspace: str, table: str) -> Dataset:
        return Dataset(data=[], namespace=f"cassandra://{host}:{port}", name=f"{keyspace}.{table}")

    # --- cloud warehouses ---

    @staticmethod
    def bigquery(project: str, dataset: str, table: str) -> Dataset:
        return Dataset(data=[], namespace="bigquery", name=f"{project}.{dataset}.{table}")

    @staticmethod
    def snowflake(org: str, account: str, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"snowflake://{org}-{account}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def redshift(
        cluster_id: str, region: str, port: int, database: str, schema: str, table: str
    ) -> Dataset:
        return Dataset(
            namespace=f"redshift://{cluster_id}.{region}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def athena(region: str, catalog: str, database: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"awsathena://athena.{region}.amazonaws.com",
            name=f"{catalog}.{database}.{table}",
        )

    @staticmethod
    def glue(region: str, account: str, database: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"arn:aws:glue:{region}:{account}",
            name=f"table/{database}/{table}",
        )

    @staticmethod
    def spanner(project: str, instance: str, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"spanner://{project}:{instance}",
            name=f"{database}.{schema}.{table}",
        )

    # --- streaming ---

    @staticmethod
    def kafka(bootstrap_server: str, port: int, topic: str) -> Dataset:
        return Dataset(data=[], namespace=f"kafka://{bootstrap_server}:{port}", name=topic)

    @staticmethod
    def pubsub_topic(project: str, topic: str) -> Dataset:
        return Dataset(data=[], namespace="pubsub", name=f"topic:{project}:{topic}")

    @staticmethod
    def pubsub_subscription(project: str, subscription: str) -> Dataset:
        return Dataset(data=[], namespace="pubsub", name=f"subscription:{project}:{subscription}")

    # --- distributed file systems ---

    @staticmethod
    def hdfs(host: str, port: int, path: str) -> Dataset:
        return Dataset(
            data=[],
            namespace=f"hdfs://{host}:{port}",
            name=path.lstrip("/"),
        )
