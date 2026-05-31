# Dataset factories

Always use a factory method. Never construct `Dataset(namespace=..., name=...)` directly: the factories encode the correct OpenLineage naming for each system.

Import: `from tiozin import Dataset, Datasets`

| Factory | Use for |
|---------|---------|
| `Dataset.from_uri(uri)` | File paths: `s3://`, `gs://`, `file://`, local paths |
| `Dataset.postgres(host, port, database, schema, table)` | PostgreSQL |
| `Dataset.mysql(host, port, database, table)` | MySQL |
| `Dataset.bigquery(project, dataset, table)` | BigQuery |
| `Dataset.snowflake(org, account, database, schema, table)` | Snowflake |
| `Dataset.redshift(cluster_id, region, port, database, schema, table)` | Redshift |
| `Dataset.athena(region, catalog, database, table)` | Athena |
| `Dataset.glue(region, account, database, table)` | Glue |
| `Dataset.kafka(bootstrap_server, port, topic)` | Kafka |
| `Dataset.hdfs(host, port, path)` | HDFS |
