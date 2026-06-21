import pytest
from dateutil.parser import parse
from pyspark.sql import SparkSession
from pyspark.sql import functions as sf
from pyspark.sql.types import StringType, StructField
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark.functions import (
    get_field,
    has_timezone,
    to_auto_timestamp,
    with_field,
)

D2026_01_16T10_00_00 = parse("2026-01-16T10:00:00Z")
S2026_01_16T10_00_00 = "2026-01-16 10:00:00"

S2024_01_15T10_30_00 = "2024-01-15T10:30:00"

D15_01_2024_10_30_00 = "15/01/2024 10:30:00"
DD_MM_YYYY_HH_MM_SS = "dd/MM/yyyy HH:mm:ss"
YYYY_MM_DD_HH_MM_SS = "yyyy-MM-dd HH:mm:ss"

D2024_01_15T01_30_00_UTC = parse("2024-01-15T01:30:00Z")
D2024_01_15T07_30_00_UTC = parse("2024-01-15T07:30:00Z")
D2024_01_15T10_30_00_UTC = parse("2024-01-15T10:30:00Z")
D2024_01_15T13_30_00_UTC = parse("2024-01-15T13:30:00Z")
D2024_01_15T15_30_00_UTC = parse("2024-01-15T15:30:00Z")
D2024_01_15T16_30_00_UTC = parse("2024-01-15T16:30:00Z")
D2024_01_15T17_30_00_UTC = parse("2024-01-15T17:30:00Z")
D2024_01_15T18_30_00_UTC = parse("2024-01-15T18:30:00Z")

SUPPORTED_TIMEZONE_CASES = [
    "Z",
    "UTC",
    "GMT",
    "BRT",
    "KST",
    "PST",
    "AEST",
    "NZST",
    "CEST",
    "AKST",
    "-03:00",
    "-0300",
    "+03:00",
    "+0300",
    "-03",
    "+03",
    "GMT-03:00",
    "GMT+8",
    "GMT+08",
    "GMT-08",
    "GMT+08:00",
    "GMT-08:00",
    "America/Sao_Paulo",
]

DATE_DELIMITERS = "_-./"


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


def test_to_auto_timestamp_should_assume_timezone_for_naive_value(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(S2024_01_15T10_30_00,)],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date", timezone="America/Sao_Paulo"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(D2024_01_15T13_30_00_UTC,)],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize(
    "format",
    [
        DD_MM_YYYY_HH_MM_SS,
        [YYYY_MM_DD_HH_MM_SS, DD_MM_YYYY_HH_MM_SS],
    ],
)
def test_to_auto_timestamp_should_accept_custom_format(
    spark: SparkSession, format: str | list
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(D15_01_2024_10_30_00,)],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date", format=format))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(D2024_01_15T10_30_00_UTC,)],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_auto_timestamp_should_accept_column_argument(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(S2024_01_15T10_30_00 + "Z",)],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp(sf.col("date")))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(D2024_01_15T10_30_00_UTC,)],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_auto_timestamp_should_accept_compact_date_as_integer(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(20240115103000,)],
        schema="date LONG",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(D2024_01_15T10_30_00_UTC,)],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_auto_timestamp_should_return_null_for_unparseable_value(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [("not a date",)],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(None,)],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize("d", DATE_DELIMITERS)
def test_to_auto_timestamp_should_parse_naive_iso_datetime(spark: SparkSession, d: str) -> None:
    # Arrange
    df = spark.createDataFrame(
        [
            (f"2023{d}01{d}01",),
            (f"2023{d}01{d}01T10:20",),
            (f"2023{d}01{d}01T10:20:30",),
            (f"2023{d}01{d}01T10:20:30.123456",),
            (f"2023{d}01{d}01 10:20",),
            (f"2023{d}01{d}01 10:20:30",),
            (f"2023{d}01{d}01 10:20:30.123456",),
        ],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (parse("2023-01-01T00:00:00Z"),),
            (parse("2023-01-01T10:20Z"),),
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T10:20:30.123456Z"),),
            (parse("2023-01-01T10:20Z"),),
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T10:20:30.123456Z"),),
        ],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize("d", DATE_DELIMITERS)
def test_to_auto_timestamp_should_parse_aware_iso_datetime(spark: SparkSession, d: str) -> None:
    # Arrange
    df = spark.createDataFrame(
        [
            (f"2023{d}01{d}01Z",),
            (f"2023{d}01{d}01T10:20Z",),
            (f"2023{d}01{d}01T10:20:30Z",),
            (f"2023{d}01{d}01T10:20:30.123456Z",),
            (f"2023{d}01{d}01 10:20Z",),
            (f"2023{d}01{d}01 10:20:30Z",),
            (f"2023{d}01{d}01 10:20:30.123456Z",),
        ],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (parse("2023-01-01T00:00:00Z"),),
            (parse("2023-01-01T10:20Z"),),
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T10:20:30.123456Z"),),
            (parse("2023-01-01T10:20Z"),),
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T10:20:30.123456Z"),),
        ],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize("d", DATE_DELIMITERS)
def test_to_auto_timestamp_should_parse_naive_european_datetime(
    spark: SparkSession, d: str
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [
            (f"01{d}01{d}2023",),
            (f"01{d}01{d}2023T10:20",),
            (f"01{d}01{d}2023T10:20:30",),
            (f"01{d}01{d}2023T10:20:30.123456",),
            (f"01{d}01{d}2023 10:20",),
            (f"01{d}01{d}2023 10:20:30",),
            (f"01{d}01{d}2023 10:20:30.123456",),
        ],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (parse("2023-01-01T00:00:00Z"),),
            (parse("2023-01-01T10:20Z"),),
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T10:20:30.123456Z"),),
            (parse("2023-01-01T10:20Z"),),
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T10:20:30.123456Z"),),
        ],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize("d", DATE_DELIMITERS)
def test_to_auto_timestamp_should_parse_aware_european_datetime(
    spark: SparkSession, d: str
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [
            (f"01{d}01{d}2023Z",),
            (f"01{d}01{d}2023T10:20Z",),
            (f"01{d}01{d}2023T10:20:30Z",),
            (f"01{d}01{d}2023T10:20:30.123456Z",),
            (f"01{d}01{d}2023 10:20Z",),
            (f"01{d}01{d}2023 10:20:30Z",),
            (f"01{d}01{d}2023 10:20:30.123456Z",),
        ],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (parse("2023-01-01T00:00:00Z"),),
            (parse("2023-01-01T10:20Z"),),
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T10:20:30.123456Z"),),
            (parse("2023-01-01T10:20Z"),),
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T10:20:30.123456Z"),),
        ],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_auto_timestamp_should_parse_compact_datetime(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [
            ("20230101",),
            ("20230101102030",),
            ("20230101Z",),
            ("20230101102030Z",),
        ],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (parse("2023-01-01T00:00:00Z"),),
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T00:00:00Z"),),
            (parse("2023-01-01T10:20:30Z"),),
        ],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_auto_timestamp_should_parse_rfc2822_datetime(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [
            ("01 Jan 2023 10:20:30",),
            ("01 Jan 2023 10:20:30Z",),
        ],
        schema="date STRING",
    )

    # Act
    result = df.withColumn("date", to_auto_timestamp("date"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (parse("2023-01-01T10:20:30Z"),),
            (parse("2023-01-01T10:20:30Z"),),
        ],
        schema="date TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# has_timezone
# ============================================================================
@pytest.mark.parametrize(
    "value",
    [
        "2024-01-15",
        "2024-01-15 ",
        "2024/01/15",
        "2024.01.15",
        "20240115",
    ],
)
def test_has_timezone_should_return_true_when_aware_date(spark: SparkSession, value: str) -> None:
    # Arrange
    sample = [tz for tz in SUPPORTED_TIMEZONE_CASES if tz not in ["+03", "+0300", "-03", "-0300"]]
    df = spark.createDataFrame(
        [(f"{value}{tz}",) for tz in sample],
        schema="value STRING",
    )

    # Act
    result = df.withColumn("has_timezone", has_timezone("value"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(f"{value}{tz}", True) for tz in sample],
        schema="value STRING, has_timezone BOOLEAN",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize(
    "value",
    [
        "2024-01-15T10:30:00",
        "2024-01-15T10:30:00 ",
    ],
)
def test_has_timezone_should_return_true_when_aware_timestamp(
    spark: SparkSession, value: str
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(f"{value}{tz}",) for tz in SUPPORTED_TIMEZONE_CASES],
        schema="value STRING",
    )

    # Act
    result = df.withColumn("has_timezone", has_timezone("value"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(f"{value}{tz}", True) for tz in SUPPORTED_TIMEZONE_CASES],
        schema="value STRING, has_timezone BOOLEAN",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize(
    "value",
    [
        "2024-01-15",
        "2024/01/15",
        "2024.01.15",
        "20240115",
    ],
)
def test_has_timezone_should_return_false_when_naive_date(spark: SparkSession, value: str) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(value,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", has_timezone("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(False,)],
        schema="created_at BOOLEAN",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize(
    "value",
    [
        "2024-01-15T10",
        "2024-01-15T10:30",
        "2024-01-15T10:30:00",
        "2024-01-15T10:30:00.123456",
        "20240115103000",
        "15 Jan 2024 10:30:00",
    ],
)
def test_has_timezone_should_return_false_when_naive_timestamp(
    spark: SparkSession, value: str
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(value,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", has_timezone("created_at"))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(False,)],
        schema="created_at BOOLEAN",
    )
    assertDataFrameEqual(actual, expected)


def test_has_timezone_should_accept_column_argument(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(S2024_01_15T10_30_00 + " +03:00",)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", has_timezone(sf.col("created_at")))

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(True,)],
        schema="created_at BOOLEAN",
    )
    assertDataFrameEqual(actual, expected)
