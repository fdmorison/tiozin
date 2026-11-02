from __future__ import annotations

from typing import Any

from pyspark.sql import DataFrame, SparkSession

from tiozin import OutputMetrics, logs
from tiozin.exceptions import TiozinInputError

ICEBERG_ACCEPT_ANY_SCHEMA = "write.spark.accept-any-schema"
SCHEMA_EVOLUTION_FORMATS = ("iceberg", "delta")

logger = logs.get_logger("table_utils")


def output_metrics(spark: SparkSession, format: str, table: str, mode: str) -> OutputMetrics:
    """
    Returns the metrics of the latest write to a catalog table. A metric is None
    when the format does not record it or when it cannot be read.
    """
    format = format.lower()

    try:
        match format:
            case "iceberg":
                metrics = _iceberg_metrics(spark, table)
            case "delta":
                metrics = _delta_metrics(spark, table)
            case _:
                metrics = {}
        return OutputMetrics(dataset=table, mode=mode, format=format, **metrics)
    except Exception as e:
        logger.warning(f"Could not read the metrics of the write to {table}: {e}")

    return OutputMetrics(dataset=table, mode=mode, format=format)


def evolve_schema(df: DataFrame, table: str, format: str) -> None:
    """
    Adds the new DataFrame columns to a catalog table.

    Raises:
        TiozinInputError: If the format does not support schema evolution.
    """
    format = format.lower()

    TiozinInputError.raise_if(
        format not in SCHEMA_EVOLUTION_FORMATS,
        f"Schema evolution is not supported for format: '{format}'",
    )

    if df.schema == df.sparkSession.table(table).schema:
        return

    match format:
        case "iceberg":
            _evolve_iceberg_schema(df, table)
        case "delta":
            _evolve_delta_schema(df, table)


def _iceberg_metrics(spark: SparkSession, table: str) -> dict[str, Any]:
    snapshot = spark.sql(
        f"SELECT summary FROM {table}.snapshots ORDER BY committed_at DESC LIMIT 1"
    ).first()
    if not snapshot:
        return {}
    return {
        "rows_written": snapshot.summary.get("added-records", 0),
        "rows_total": snapshot.summary.get("total-records"),
        "bytes_written": snapshot.summary.get("added-files-size", 0),
        "bytes_total": snapshot.summary.get("total-files-size"),
    }


def _delta_metrics(spark: SparkSession, table: str) -> dict[str, Any]:
    history = spark.sql(f"DESCRIBE HISTORY {table} LIMIT 1").first()
    detail = spark.sql(f"DESCRIBE DETAIL {table}").first()
    metrics = history.operationMetrics
    return {
        "rows_written": metrics.get("numOutputRows"),
        "bytes_written": metrics.get("numTargetBytesAdded") or metrics.get("numOutputBytes"),
        "bytes_total": detail.sizeInBytes,
    }


def _evolve_iceberg_schema(df: DataFrame, table: str) -> None:
    spark = df.sparkSession
    accepts_any_schema = bool(
        spark.sql(f"SHOW TBLPROPERTIES {table}")
        .filter(f"key = '{ICEBERG_ACCEPT_ANY_SCHEMA}' AND value = 'true'")
        .first()
    )

    if not accepts_any_schema:
        spark.sql(f"ALTER TABLE {table} SET TBLPROPERTIES ('{ICEBERG_ACCEPT_ANY_SCHEMA}'='true')")
    try:
        (
            spark.createDataFrame([], df.schema)
            .writeTo(table)
            .option("mergeSchema", "true")
            .option("check-ordering", "false")
            .append()
        )
    finally:
        if not accepts_any_schema:
            spark.sql(f"ALTER TABLE {table} UNSET TBLPROPERTIES ('{ICEBERG_ACCEPT_ANY_SCHEMA}')")


def _evolve_delta_schema(df: DataFrame, table: str) -> None:
    (
        df.sparkSession.createDataFrame([], df.schema)
        .writeTo(table)
        .option("mergeSchema", "true")
        .append()
    )
