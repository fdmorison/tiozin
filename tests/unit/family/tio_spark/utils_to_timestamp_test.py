from datetime import UTC, datetime

import pytest
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark.utils import to_auto_timestamp

_STR_2024_01_15T10_30_00 = "2024-01-15T10:30:00"
_STR_15_01_2024_10_30_00 = "15/01/2024 10:30:00"
_FMT_DD_MM_YYYY_HH_MM_SS = "dd/MM/yyyy HH:mm:ss"
_DT_2024_01_15T01_30_00_UTC = datetime(2024, 1, 15, 1, 30, 0, tzinfo=UTC)
_DT_2024_01_15T07_30_00_UTC = datetime(2024, 1, 15, 7, 30, 0, tzinfo=UTC)
_DT_2024_01_15T10_30_00_UTC = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
_DT_2024_01_15T13_30_00_UTC = datetime(2024, 1, 15, 13, 30, 0, tzinfo=UTC)
_DT_2024_01_15T15_30_00_UTC = datetime(2024, 1, 15, 15, 30, 0, tzinfo=UTC)
_DT_2024_01_15T16_30_00_UTC = datetime(2024, 1, 15, 16, 30, 0, tzinfo=UTC)
_DT_2024_01_15T17_30_00_UTC = datetime(2024, 1, 15, 17, 30, 0, tzinfo=UTC)
_DT_2024_01_15T18_30_00_UTC = datetime(2024, 1, 15, 18, 30, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "suffix, expected_dt",
    [
        ("Z", _DT_2024_01_15T10_30_00_UTC),
        ("+03:00", _DT_2024_01_15T07_30_00_UTC),
        ("-03:00", _DT_2024_01_15T13_30_00_UTC),
        ("+0300", _DT_2024_01_15T07_30_00_UTC),
        ("-0300", _DT_2024_01_15T13_30_00_UTC),
    ],
)
def test_to_timestamp_should_convert_string_with_timezone(
    spark: SparkSession, suffix: str, expected_dt: datetime
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(_STR_2024_01_15T10_30_00 + suffix,)],
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
        (" UTC", _DT_2024_01_15T10_30_00_UTC),
        (" utc", _DT_2024_01_15T10_30_00_UTC),
        (" GMT", _DT_2024_01_15T10_30_00_UTC),
        (" gmt", _DT_2024_01_15T10_30_00_UTC),
        (" EST", _DT_2024_01_15T15_30_00_UTC),
        (" est", _DT_2024_01_15T15_30_00_UTC),
        (" CST", _DT_2024_01_15T16_30_00_UTC),
        (" cst", _DT_2024_01_15T16_30_00_UTC),
        (" MST", _DT_2024_01_15T17_30_00_UTC),
        (" mst", _DT_2024_01_15T17_30_00_UTC),
        (" PST", _DT_2024_01_15T18_30_00_UTC),
        (" pst", _DT_2024_01_15T18_30_00_UTC),
        (" JST", _DT_2024_01_15T01_30_00_UTC),
        (" jst", _DT_2024_01_15T01_30_00_UTC),
    ],
)
def test_to_timestamp_should_convert_string_with_named_timezone(
    suffix: str,
    expected_dt: datetime,
    spark: SparkSession,
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(_STR_2024_01_15T10_30_00 + suffix,)],
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
        [(_STR_2024_01_15T10_30_00,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", to_auto_timestamp("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(_DT_2024_01_15T10_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_string_without_timezone_when_timezone_is_provided(
    spark: SparkSession,
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(_STR_2024_01_15T10_30_00,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn(
        "created_at", to_auto_timestamp("created_at", timezone="America/Sao_Paulo")
    )

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(_DT_2024_01_15T13_30_00_UTC,)],
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
        [(_DT_2024_01_15T10_30_00_UTC,)],
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
        [(_DT_2024_01_15T10_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_string_with_custom_format(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(_STR_15_01_2024_10_30_00,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn(
        "created_at",
        to_auto_timestamp("created_at", format=_FMT_DD_MM_YYYY_HH_MM_SS),
    )

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(_DT_2024_01_15T10_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_column_with_mixed_timezones(
    spark: SparkSession,
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [
            (_STR_2024_01_15T10_30_00 + "Z",),
            (_STR_2024_01_15T10_30_00 + "+03:00",),
            (_STR_2024_01_15T10_30_00 + "-03:00",),
            (_STR_2024_01_15T10_30_00 + "+0300",),
            (_STR_2024_01_15T10_30_00 + "-0300",),
            (_STR_2024_01_15T10_30_00 + " UTC",),
            (_STR_2024_01_15T10_30_00 + " GMT",),
            (_STR_2024_01_15T10_30_00 + " EST",),
            (_STR_2024_01_15T10_30_00 + " CST",),
            (_STR_2024_01_15T10_30_00 + " MST",),
            (_STR_2024_01_15T10_30_00 + " PST",),
            (_STR_2024_01_15T10_30_00 + " JST",),
            (_STR_2024_01_15T10_30_00,),
        ],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", to_auto_timestamp("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (_DT_2024_01_15T10_30_00_UTC,),
            (_DT_2024_01_15T07_30_00_UTC,),
            (_DT_2024_01_15T13_30_00_UTC,),
            (_DT_2024_01_15T07_30_00_UTC,),
            (_DT_2024_01_15T13_30_00_UTC,),
            (_DT_2024_01_15T10_30_00_UTC,),
            (_DT_2024_01_15T10_30_00_UTC,),
            (_DT_2024_01_15T15_30_00_UTC,),
            (_DT_2024_01_15T16_30_00_UTC,),
            (_DT_2024_01_15T17_30_00_UTC,),
            (_DT_2024_01_15T18_30_00_UTC,),
            (_DT_2024_01_15T01_30_00_UTC,),
            (_DT_2024_01_15T10_30_00_UTC,),
        ],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)
