# SparkIcebergRunner

A Spark runner pre-configured for Apache Iceberg. Extends [SparkRunner](runner.md) and wires the required Spark SQL extensions and catalog configuration automatically. Use this instead of [SparkRunner](runner.md) when your job reads or writes Iceberg tables.

```yaml
runner:
  kind: SparkIcebergRunner
  master: local[*]
  catalog_name: local
  catalog_type: hadoop
  catalog_warehouse: s3://my-bucket/warehouse
```

## All available options

Inherits all [SparkRunner](runner.md) options, plus:

| Property | Description | Default |
|---|---|---|
| `catalog_name` | Name of the Iceberg catalog. Used as a prefix in SQL (`catalog_name.db.table`). Required | |
| `catalog_type` | Catalog backend type. Required unless `catalog_impl` is set | |
| `catalog_impl` | Fully qualified custom catalog class name. Required unless `catalog_type` is set | |
| `catalog_uri` | Catalog URI (Hive metastore `thrift://`, REST endpoint, etc.) | |
| `catalog_warehouse` | Warehouse path for the catalog | |
| `iceberg_class` | Spark catalog class used to register the Iceberg catalog | `org.apache.iceberg.spark.SparkSessionCatalog` |

## Catalog types

`catalog_type` selects the Iceberg catalog backend. Accepted values:

| Value | Description |
|---|---|
| `hadoop` | Filesystem-based catalog. Runs entirely on the filesystem and works with local paths, S3, GCS, etc. |
| `hive` | Uses the Hive metastore. Requires `catalog_uri` pointing to the metastore |
| `rest` | REST catalog API (Project Nessie, Polaris, Unity Catalog, etc.). Requires `catalog_uri` |
| `glue` | AWS Glue Data Catalog. Resolves the catalog endpoint and credentials from the AWS SDK credential chain |
| `jdbc` | JDBC-backed catalog. Requires `catalog_uri` with the JDBC connection string |
| `nessie` | Project Nessie catalog. Requires `catalog_uri` pointing to the Nessie server |

For custom catalog implementations not covered by `catalog_type`, use `catalog_impl` with the fully qualified class name instead.

## AWS Glue

The Glue catalog integrates Iceberg with the AWS Glue Data Catalog. AWS credentials are picked up from the environment (instance profile, environment variables, or `~/.aws/credentials`). Set `catalog_warehouse` to the S3 path where Iceberg data files are stored.

The Iceberg AWS bundle must be on the classpath. Add it via `jars_packages`:

```yaml
runner:
  kind: SparkIcebergRunner
  master: local[*]
  catalog_name: glue
  catalog_type: glue
  catalog_warehouse: s3://my-bucket/warehouse
  jars_packages:
    - org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0
    - org.apache.iceberg:iceberg-aws-bundle:1.5.0
```

To query an Iceberg table registered in Glue:

```sql
SELECT * FROM glue.my_database.my_table
```

## Other catalog examples

```yaml
# Hive metastore
runner:
  kind: SparkIcebergRunner
  master: local[*]
  catalog_name: hive_catalog
  catalog_type: hive
  catalog_uri: thrift://hive-metastore:9083

# REST catalog
runner:
  kind: SparkIcebergRunner
  master: local[*]
  catalog_name: rest_catalog
  catalog_type: rest
  catalog_uri: http://catalog:8181
```

## Choosing an iceberg_class

`iceberg_class` controls which Spark catalog class Iceberg registers under `catalog_name`.

| Value | Use when |
|---|---|
| `org.apache.iceberg.spark.SparkSessionCatalog` (default) | Replacing the default Spark `spark_catalog`. Allows using unqualified table names |
| `org.apache.iceberg.spark.SparkCatalog` | Adding a new named catalog alongside the existing Spark catalog |
