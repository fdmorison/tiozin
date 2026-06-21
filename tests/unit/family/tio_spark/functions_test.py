from datetime import datetime

import pytest
from dateutil.parser import isoparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as sf
from pyspark.sql.types import StringType, StructField
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark.functions import get_field, to_auto_timestamp, with_field

D2026_01_16T10_00_00 = isoparse("2026-01-16T10:00:00Z")
S2026_01_16T10_00_00 = "2026-01-16 10:00:00"

S2024_01_15T10_30_00 = "2024-01-15T10:30:00"

D15_01_2024_10_30_00 = "15/01/2024 10:30:00"
DD_MM_YYYY_HH_MM_SS = "dd/MM/yyyy HH:mm:ss"

D2024_01_15T01_30_00_UTC = isoparse("2024-01-15T01:30:00Z")
D2024_01_15T07_30_00_UTC = isoparse("2024-01-15T07:30:00Z")
D2024_01_15T10_30_00_UTC = isoparse("2024-01-15T10:30:00Z")
D2024_01_15T13_30_00_UTC = isoparse("2024-01-15T13:30:00Z")
D2024_01_15T15_30_00_UTC = isoparse("2024-01-15T15:30:00Z")
D2024_01_15T16_30_00_UTC = isoparse("2024-01-15T16:30:00Z")
D2024_01_15T17_30_00_UTC = isoparse("2024-01-15T17:30:00Z")
D2024_01_15T18_30_00_UTC = isoparse("2024-01-15T18:30:00Z")


# ============================================================================
# get_field
# ============================================================================


def test_get_field_should_resolve_top_level_field(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [("John",)],
        schema="name STRING",
    )

    # Act
    actual = get_field(df, "name")

    # Assert
    expected = StructField("name", StringType(), True)
    assert actual == expected


def test_get_field_should_resolve_nested_struct_field(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [{"address": {"city": "New York"}}],
        schema="address STRUCT<city STRING>",
    )

    # Act
    actual = get_field(df, "address.city")

    # Assert
    expected = StructField("city", StringType(), True)
    assert actual == expected


def test_get_field_should_resolve_field_inside_array_of_structs(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [{"events": [{"name": "click"}]}],
        schema="events ARRAY<STRUCT<name STRING>>",
    )

    # Act
    actual = get_field(df, "events.name")

    # Assert
    expected = StructField("name", StringType(), True)
    assert actual == expected


def test_get_field_should_return_none_when_top_level_field_missing(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [("John",)],
        schema="name STRING",
    )

    # Act
    actual = get_field(df, "missing")

    # Assert
    assert actual is None


def test_get_field_should_return_none_when_nested_path_missing(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [{"address": {"city": "New York"}}],
        schema="address STRUCT<city STRING>",
    )

    # Act
    actual = get_field(df, "address.zipcode")

    # Assert
    assert actual is None


def test_get_field_should_return_none_when_descending_past_primitive(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [("John",)],
        schema="name STRING",
    )

    # Act
    actual = get_field(df, "name.first")

    # Assert
    assert actual is None


# ============================================================================
# with_field
# ============================================================================


def test_with_field_should_apply_function_to_top_level_field(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(S2026_01_16T10_00_00,)],
        schema="created_at STRING",
    )

    # Act
    result = with_field(df, "created_at", sf.to_timestamp)

    # Assert
    actual = result.select("created_at")
    expected = spark.createDataFrame(
        [(D2026_01_16T10_00_00,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_with_field_should_apply_prebuilt_column_to_top_level_field(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(S2026_01_16T10_00_00,)],
        schema="created_at STRING",
    )

    # Act
    result = with_field(df, "created_at", sf.to_timestamp("created_at"))

    # Assert
    actual = result.select("created_at")
    expected = spark.createDataFrame(
        [(D2026_01_16T10_00_00,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_with_field_should_forward_kwargs_to_callable(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(D15_01_2024_10_30_00,)],
        schema="created_at STRING",
    )

    # Act
    result = with_field(df, "created_at", sf.to_timestamp, format=DD_MM_YYYY_HH_MM_SS)

    # Assert
    actual = result.select("created_at")
    expected = spark.createDataFrame(
        [(D2024_01_15T10_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_with_field_should_apply_function_to_nested_field(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [{"event": {"created_at": S2026_01_16T10_00_00, "id": "abc"}}],
        schema="event STRUCT<created_at STRING, id STRING>",
    )

    # Act
    result = with_field(df, "event.created_at", sf.to_timestamp)

    # Assert
    actual = result.select("event")
    expected = spark.createDataFrame(
        [{"event": {"created_at": D2026_01_16T10_00_00, "id": "abc"}}],
        schema="event STRUCT<created_at TIMESTAMP, id STRING>",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# to_auto_timestamp
# ============================================================================


@pytest.mark.parametrize(
    "suffix, expected_dt",
    [
        ("Z", D2024_01_15T10_30_00_UTC),
        ("+03:00", D2024_01_15T07_30_00_UTC),
        ("-03:00", D2024_01_15T13_30_00_UTC),
        ("+0300", D2024_01_15T07_30_00_UTC),
        ("-0300", D2024_01_15T13_30_00_UTC),
    ],
)
def test_to_timestamp_should_convert_string_with_timezone(
    spark: SparkSession, suffix: str, expected_dt: datetime
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(S2024_01_15T10_30_00 + suffix,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", to_auto_timestamp("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(expected_dt,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


# EDT, CDT, MDT, PDT, KST are excluded: Spark's to_timestamp_ltz returns null for them.
@pytest.mark.parametrize(
    "suffix, expected_dt",
    [
        (" UTC", D2024_01_15T10_30_00_UTC),
        (" utc", D2024_01_15T10_30_00_UTC),
        (" GMT", D2024_01_15T10_30_00_UTC),
        (" gmt", D2024_01_15T10_30_00_UTC),
        (" EST", D2024_01_15T15_30_00_UTC),
        (" est", D2024_01_15T15_30_00_UTC),
        (" CST", D2024_01_15T16_30_00_UTC),
        (" cst", D2024_01_15T16_30_00_UTC),
        (" MST", D2024_01_15T17_30_00_UTC),
        (" mst", D2024_01_15T17_30_00_UTC),
        (" PST", D2024_01_15T18_30_00_UTC),
        (" pst", D2024_01_15T18_30_00_UTC),
        (" JST", D2024_01_15T01_30_00_UTC),
        (" jst", D2024_01_15T01_30_00_UTC),
    ],
)
def test_to_timestamp_should_convert_string_with_named_timezone(
    suffix: str,
    expected_dt: datetime,
    spark: SparkSession,
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(S2024_01_15T10_30_00 + suffix,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", to_auto_timestamp("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(expected_dt,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_string_without_timezone(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(S2024_01_15T10_30_00,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", to_auto_timestamp("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(D2024_01_15T10_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_string_without_timezone_when_timezone_is_provided(
    spark: SparkSession,
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(S2024_01_15T10_30_00,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn(
        "created_at", to_auto_timestamp("created_at", timezone="America/Sao_Paulo")
    )

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(D2024_01_15T13_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_epoch_string(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [("1705314600",)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", to_auto_timestamp("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(D2024_01_15T10_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_epoch_integer(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(1705314600,)],
        schema="created_at LONG",
    )

    # Act
    result = df.withColumn("created_at", to_auto_timestamp("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(D2024_01_15T10_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_string_with_custom_format(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(D15_01_2024_10_30_00,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn(
        "created_at",
        to_auto_timestamp("created_at", format=DD_MM_YYYY_HH_MM_SS),
    )

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(D2024_01_15T10_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_column_with_mixed_timezones(
    spark: SparkSession,
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [
            (S2024_01_15T10_30_00 + "Z",),
            (S2024_01_15T10_30_00 + "+03:00",),
            (S2024_01_15T10_30_00 + "-03:00",),
            (S2024_01_15T10_30_00 + "+0300",),
            (S2024_01_15T10_30_00 + "-0300",),
            (S2024_01_15T10_30_00 + " UTC",),
            (S2024_01_15T10_30_00 + " GMT",),
            (S2024_01_15T10_30_00 + " EST",),
            (S2024_01_15T10_30_00 + " CST",),
            (S2024_01_15T10_30_00 + " MST",),
            (S2024_01_15T10_30_00 + " PST",),
            (S2024_01_15T10_30_00 + " JST",),
            (S2024_01_15T10_30_00,),
        ],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", to_auto_timestamp("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (D2024_01_15T10_30_00_UTC,),
            (D2024_01_15T07_30_00_UTC,),
            (D2024_01_15T13_30_00_UTC,),
            (D2024_01_15T07_30_00_UTC,),
            (D2024_01_15T13_30_00_UTC,),
            (D2024_01_15T10_30_00_UTC,),
            (D2024_01_15T10_30_00_UTC,),
            (D2024_01_15T15_30_00_UTC,),
            (D2024_01_15T16_30_00_UTC,),
            (D2024_01_15T17_30_00_UTC,),
            (D2024_01_15T18_30_00_UTC,),
            (D2024_01_15T01_30_00_UTC,),
            (D2024_01_15T10_30_00_UTC,),
        ],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)
