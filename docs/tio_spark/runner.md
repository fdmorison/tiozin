# SparkRunner

Runs a Tiozin pipeline on Apache Spark. During setup, it creates a `SparkSession` with the job slug as the app name. During teardown, it stops the session.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  log_level: WARN
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `master` | Spark master URL (`local[*]`, `yarn`, `spark://host:7077`, etc.) | |
| `endpoint` | Spark Connect server endpoint (`sc://host:port`), requires Spark 3.4+, mutually exclusive with `master` | |
| `enable_hive_support` | Enable Hive metastore integration | `false` |
| `log_level` | Spark context log level | `WARN` |
| `jars_packages` | Maven coordinates to add to the Spark classpath | `[]` |
| `streaming` | Enable streaming execution mode | `false` |
| `**options` | Spark config options passed directly to `SparkSession.builder` | |

## Spark config options

Any key not listed above is forwarded to `SparkSession.builder.config()`. The full list of supported options is in the [Spark configuration reference](https://spark.apache.org/docs/latest/configuration.html).

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  spark.executor.memory: 4g
  spark.sql.shuffle.partitions: 200
```

## JAR packages

Use `jars_packages` to add Maven-coordinated dependencies to the Spark classpath. This is equivalent to setting `spark.jars.packages`.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  jars_packages:
    - org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0
    - io.delta:delta-spark_2.12:3.2.0
```

## Hive support

Set `enable_hive_support: true` to connect to a Hive metastore and read or write Hive tables. Requires a Hive-compatible environment with `hive-site.xml` on the classpath.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  enable_hive_support: true
```

## Spark Connect

To connect to a remote Spark Connect server instead of creating a local session, use `endpoint`. `master` and `endpoint` are mutually exclusive.

```yaml
runner:
  kind: SparkRunner
  endpoint: sc://localhost:15002
```

## Streaming mode

Set `streaming: true` to enable streaming execution. When streaming is enabled, `SparkFileInput` uses `spark.readStream` instead of `spark.read`, and each input must point to exactly one directory path.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  streaming: true
```
