from __future__ import annotations

from urllib.parse import urlparse

import wrapt
from openlineage.client.run import InputDataset, OutputDataset

from tiozin.utils.io import normalize_uri


class Datasets:
    def __init__(self, inputs: list[Dataset] = None, outputs: Dataset = None) -> None:
        self.inputs = inputs or []
        self.outputs = outputs or []


class Dataset(wrapt.ObjectProxy):
    def __init__(self, data=None, schema=None, namespace=None, name=None):
        super().__init__(data)
        self._self_schema = schema
        self._self_namespace = namespace
        self._self_name = name

    # --- factory ---

    @classmethod
    def wrap(cls, obj):
        return obj if isinstance(obj, cls) else cls(obj)

    # --- accessors ---

    @property
    def data(self):
        return self.__wrapped__

    @property
    def schema(self):
        return self._self_schema

    @property
    def namespace(self):
        return self._self_namespace

    @property
    def name(self):
        return self._self_name

    # --- enrichment (first-write-wins) ---

    def with_schema(self, schema):
        self._self_schema = self._self_schema or schema
        return self

    def with_namespace(self, namespace):
        self._self_namespace = self._self_namespace or namespace
        return self

    def with_name(self, name):
        self._self_name = self._self_name or name
        return self

    def merge(self, other: Dataset):
        if other:
            self.with_schema(other.schema)
            self.with_namespace(other.namespace)
            self.with_name(other.name)
        return self

    # --- openlineage ---

    def as_input(self):
        return InputDataset(
            namespace=self.namespace,
            name=self.name,
            facets=self._facets(),
        )

    def as_output(self):
        return OutputDataset(
            namespace=self.namespace,
            name=self.name,
            facets=self._facets(),
        )

    def _facets(self):
        return {"schema": self.schema.export("openlineage")} if self.schema is not None else {}

    # --- open lineage factories ---

    @staticmethod
    def from_uri(uri: str) -> Dataset:
        uri = normalize_uri(uri, as_absolute=False, strip_glob=True, strip_partitions=True)
        parsed = urlparse(uri)

        if not parsed.scheme:
            return Dataset(namespace="file", name=uri)

        if parsed.netloc:
            namespace = f"{parsed.scheme}://{parsed.netloc}"
        else:
            namespace = parsed.scheme

        name = parsed.path.lstrip("/")
        return Dataset(namespace=namespace, name=name)

    # --- SQL databases (database.schema.table) ---

    @staticmethod
    def postgres(host: str, port: int, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            namespace=f"postgres://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def mssql(host: str, port: int, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            namespace=f"mssql://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def cratedb(host: str, port: int, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            namespace=f"crate://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def db2(host: str, port: int, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            namespace=f"db2://{host}:{port}",
            name=f"{database}.{schema}.{table}",
        )

    @staticmethod
    def trino(host: str, port: int, catalog: str, schema: str, table: str) -> Dataset:
        return Dataset(
            namespace=f"trino://{host}:{port}",
            name=f"{catalog}.{schema}.{table}",
        )

    @staticmethod
    def oracle(host: str, port: int, service: str, schema: str, table: str) -> Dataset:
        return Dataset(
            namespace=f"oracle://{host}:{port}",
            name=f"{service}.{schema}.{table}",
        )

    # --- SQL databases (database.table, no schema) ---

    @staticmethod
    def mysql(host: str, port: int, database: str, table: str) -> Dataset:
        return Dataset(namespace=f"mysql://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def hive(host: str, port: int, database: str, table: str) -> Dataset:
        return Dataset(namespace=f"hive://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def teradata(host: str, port: int, database: str, table: str) -> Dataset:
        return Dataset(namespace=f"teradata://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def oceanbase(host: str, port: int, database: str, table: str) -> Dataset:
        return Dataset(namespace=f"oceanbase://{host}:{port}", name=f"{database}.{table}")

    @staticmethod
    def cassandra(host: str, port: int, keyspace: str, table: str) -> Dataset:
        return Dataset(namespace=f"cassandra://{host}:{port}", name=f"{keyspace}.{table}")

    # --- cloud warehouses ---

    @staticmethod
    def bigquery(project: str, dataset: str, table: str) -> Dataset:
        return Dataset(namespace="bigquery", name=f"{project}.{dataset}.{table}")

    @staticmethod
    def snowflake(org: str, account: str, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
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
            namespace=f"awsathena://athena.{region}.amazonaws.com",
            name=f"{catalog}.{database}.{table}",
        )

    @staticmethod
    def glue(region: str, account: str, database: str, table: str) -> Dataset:
        return Dataset(
            namespace=f"arn:aws:glue:{region}:{account}",
            name=f"table/{database}/{table}",
        )

    @staticmethod
    def spanner(project: str, instance: str, database: str, schema: str, table: str) -> Dataset:
        return Dataset(
            namespace=f"spanner://{project}:{instance}",
            name=f"{database}.{schema}.{table}",
        )

    # --- streaming ---

    @staticmethod
    def kafka(bootstrap_server: str, port: int, topic: str) -> Dataset:
        return Dataset(namespace=f"kafka://{bootstrap_server}:{port}", name=topic)

    @staticmethod
    def pubsub_topic(project: str, topic: str) -> Dataset:
        return Dataset(namespace="pubsub", name=f"topic:{project}:{topic}")

    @staticmethod
    def pubsub_subscription(project: str, subscription: str) -> Dataset:
        return Dataset(namespace="pubsub", name=f"subscription:{project}:{subscription}")

    # --- distributed file systems ---

    @staticmethod
    def hdfs(host: str, port: int, path: str) -> Dataset:
        return Dataset(
            namespace=f"hdfs://{host}:{port}",
            name=path.lstrip("/"),
        )
