from datetime import UTC, datetime

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as sf
from pyspark.sql.types import StringType, StructField
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark.utils import get_field, join_field, split_field, with_field

_2026_01_16T10_00_00 = datetime(2026, 1, 16, 10, 0, 0, tzinfo=UTC)
_2026_01_16T10_00_00_STR = "2026-01-16 10:00:00"
_2026_01_16T00_00_00 = datetime(2026, 1, 16, 0, 0, 0, tzinfo=UTC)
_2026_01_16T00_00_00_STR = "16-01-2026"


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
