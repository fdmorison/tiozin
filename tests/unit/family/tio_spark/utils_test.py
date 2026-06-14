from datetime import UTC, datetime

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as sf
from pyspark.sql.types import StringType, StructField
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark.utils import (
    get_field,
    join_field,
    split_field,
    to_timestamp,
    with_field,
)

_2026_01_16T10_00_00 = datetime(2026, 1, 16, 10, 0, 0, tzinfo=UTC)
_2026_01_16T10_00_00_STR = "2026-01-16 10:00:00"
_2026_01_16T00_00_00 = datetime(2026, 1, 16, 0, 0, 0, tzinfo=UTC)
_2026_01_16T00_00_00_STR = "16-01-2026"

# to_timestamp constants (base date: 2024-01-15)
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


def test_split_field_should_split_on_dots() -> None:
    # Act
    actual = split_field("address.city")

    # Assert
    expected = ["address", "city"]
    assert actual == expected


def test_split_field_should_keep_single_component() -> None:
    # Act
    actual = split_field("name")

    # Assert
    expected = ["name"]
    assert actual == expected


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("created\\.at", ["created.at"]),
        ("a\\.b\\.c", ["a.b.c"]),
        ("event.created\\.at.value", ["event", "created.at", "value"]),
    ],
    ids=["escaped_dot", "multiple_escaped_dots", "nested_and_escaped"],
)
def test_split_field_should_keep_escaped_dots(field: str, expected: list[str]) -> None:
    # Act
    actual = split_field(field)

    # Assert
    assert actual == expected


def test_join_field_should_join_on_dots() -> None:
    # Act
    actual = join_field(["address", "city"])

    # Assert
    assert actual == "address.city"


def test_join_field_should_keep_single_component() -> None:
    # Act
    actual = join_field(["name"])

    # Assert
    assert actual == "name"


def test_join_field_should_not_escape_dots_by_default() -> None:
    # Arrange
    fields = ["created.at"]

    # Act
    actual = join_field(fields)

    # Assert
    expected = "created.at"
    assert actual == expected


def test_join_field_should_escape_dots_when_enabled() -> None:
    # Arrange
    fields = ["created.at"]

    # Act
    actual = join_field(fields, escape=True)

    # Assert
    expected = "created\\.at"
    assert actual == expected


def test_join_field_should_round_trip_through_split_field_when_escaping() -> None:
    # Arrange
    fields = ["event", "created.at", "value"]

    # Act
    joined = join_field(fields, escape=True)
    actual = split_field(joined)

    # Assert
    expected = ["event", "created.at", "value"]
    assert actual == expected


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


def test_with_field_should_apply_function_to_top_level_field(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(_2026_01_16T10_00_00_STR,)],
        schema="created_at STRING",
    )

    # Act
    result = with_field(df, "created_at", sf.to_timestamp)

    # Assert
    actual = result.select("created_at")
    expected = spark.createDataFrame(
        [(_2026_01_16T10_00_00,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_with_field_should_apply_prebuilt_column_to_top_level_field(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(_2026_01_16T10_00_00_STR,)],
        schema="created_at STRING",
    )

    # Act
    result = with_field(df, "created_at", sf.to_timestamp("created_at"))

    # Assert
    actual = result.select("created_at")
    expected = spark.createDataFrame(
        [(_2026_01_16T10_00_00,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_with_field_should_forward_kwargs_to_callable(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(_2026_01_16T00_00_00_STR,)],
        schema="created_at STRING",
    )

    # Act
    result = with_field(df, "created_at", sf.to_timestamp, format="dd-MM-yyyy")

    # Assert
    actual = result.select("created_at")
    expected = spark.createDataFrame(
        [(_2026_01_16T00_00_00,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_with_field_should_apply_function_to_nested_field(spark: SparkSession) -> None:
    # Arrange
    df = spark.createDataFrame(
        [{"event": {"created_at": _2026_01_16T10_00_00_STR, "id": "abc"}}],
        schema="event STRUCT<created_at STRING, id STRING>",
    )

    # Act
    result = with_field(df, "event.created_at", sf.to_timestamp)

    # Assert
    actual = result.select("event")
    expected = spark.createDataFrame(
        [{"event": {"created_at": _2026_01_16T10_00_00, "id": "abc"}}],
        schema="event STRUCT<created_at TIMESTAMP, id STRING>",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# to_timestamp
# ============================================================================


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
def test_to_timestamp_should_convert_timestamp_when_string_has_offset(
    spark: SparkSession, suffix: str, expected_dt: datetime
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(_STR_2024_01_15T10_30_00 + suffix,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", to_timestamp("created_at", timezone="UTC"))

    # Assert
    actual = result.select("created_at")
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
def test_to_timestamp_should_convert_timestamp_when_string_has_named_timezone(
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
    result = df.withColumn("created_at", to_timestamp("created_at", timezone="America/Sao_Paulo"))

    # Assert
    actual = result.select("created_at")
    expected = spark.createDataFrame(
        [(expected_dt,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_timestamp_when_string_has_no_offset(
    spark: SparkSession,
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(_STR_2024_01_15T10_30_00,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn("created_at", to_timestamp("created_at", timezone="America/Sao_Paulo"))

    # Assert
    actual = result.select("created_at")
    expected = spark.createDataFrame(
        [(_DT_2024_01_15T13_30_00_UTC,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize(
    "input_str, fmt, expected_dt",
    [
        (_STR_15_01_2024_10_30_00, _FMT_DD_MM_YYYY_HH_MM_SS, _DT_2024_01_15T13_30_00_UTC),
        (_STR_2024_01_15T10_30_00, None, _DT_2024_01_15T13_30_00_UTC),
    ],
)
def test_to_timestamp_should_convert_timestamp_when_format_parameter(
    spark: SparkSession, input_str: str, fmt: str | None, expected_dt: datetime
) -> None:
    # Arrange
    df = spark.createDataFrame(
        [(input_str,)],
        schema="created_at STRING",
    )

    # Act
    result = df.withColumn(
        "created_at",
        to_timestamp("created_at", timezone="America/Sao_Paulo", format=fmt),
    )

    # Assert
    actual = result.select("created_at")
    expected = spark.createDataFrame(
        [(expected_dt,)],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_to_timestamp_should_convert_timestamp_when_column_has_mixed_offsets(
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
    result = df.withColumn("created_at", to_timestamp("created_at", timezone="America/Sao_Paulo"))

    # Assert
    actual = result.select("created_at")
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
            (_DT_2024_01_15T13_30_00_UTC,),
        ],
        schema="created_at TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)
