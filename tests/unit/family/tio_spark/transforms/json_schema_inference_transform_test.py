from datetime import UTC, datetime

import pytest
from py4j.protocol import Py4JJavaError
from pyspark.sql import SparkSession
from pyspark.sql.types import _parse_datatype_string
from pyspark.sql.utils import AnalysisException
from pyspark.testing import assertDataFrameEqual, assertSchemaEqual

from tiozin.family.tio_spark import SparkJsonSchemaInferenceTransform

STR_2024_01_15T10_30_00Z = "2024-01-15T10:30:00Z"
OBJ_2024_01_15T10_30_00Z = datetime.fromisoformat("2024-01-15T10:30:00Z")

STR_2024_01_15T10_30_00 = "2024-01-15T10:30:00"
OBJ_2024_01_15T10_30_00 = datetime.fromisoformat("2024-01-15T10:30:00")

STR_15_01_2024_10_30_00Z = "15/01/2024 10:30:00Z"
FMT_DD_MM_YYYY_HH_MM_SSX = "dd/MM/yyyy HH:mm:ssX"

STR_15_01_2024_10_30_00 = "15/01/2024 10:30:00"
FMT_DD_MM_YYYY_HH_MM_SS = "dd/MM/yyyy HH:mm:ss"

STR_2024_01_15 = "2024-01-15"
FMT_YYYY_MM_DD = "yyyy-MM-dd"

OBJ_2024_01_15T00_00_00Z = datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC)


# ============================================================================
# Testing SparkJsonSchemaInferenceTransform - Schema Inference
# ============================================================================


def test_transform_should_infer_schema(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [
            {"value": '{"name": "John", "age": 30}'},
            {"value": '{"name": "Mary", "age": 45}'},
        ],
        schema="value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields="value",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            {"value": {"name": "John", "age": 30}},
            {"value": {"name": "Mary", "age": 45}},
        ],
        schema="value STRUCT<age LONG, name STRING>",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_infer_schema_of_multiple_columns(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [
            {
                "user": '{"name": "John", "age": 30}',
                "address": '{"street": "Main St", "city": "New York"}',
            },
            {
                "user": '{"name": "Mary", "age": 45}',
                "address": '{"street": "Main St", "city": "New York"}',
            },
        ],
        schema="user STRING, address STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields=["user", "address"],
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            {
                "user": {"name": "John", "age": 30},
                "address": {"street": "Main St", "city": "New York"},
            },
            {
                "user": {"name": "Mary", "age": 45},
                "address": {"street": "Main St", "city": "New York"},
            },
        ],
        schema="""
            user STRUCT<age LONG, name STRING>,
            address STRUCT<city STRING, street STRING>
        """,
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_infer_schema_when_sample_is_empty(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [
            {"value": '{"name": "John", "age": 30}'},
            {"value": '{"name": "Mary", "age": 45}'},
        ],
        schema="value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields="value",
        sampling_ratio=0.001,  # force empty sample
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            {"value": {"name": "John", "age": 30}},
            {"value": {"name": "Mary", "age": 45}},
        ],
        schema="value STRUCT<age LONG, name STRING>",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_do_nothing_when_json_columns_is_empty(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [
            {"value": '{"name": "John", "age": 30}'},
            {"value": '{"name": "Mary", "age": 45}'},
        ],
        schema="value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
    ).transform(input)

    # Assert
    expected = input
    assertDataFrameEqual(actual, expected)


def test_transform_should_raise_error_when_json_is_malformed(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"value": "{broken}"}],
        schema="value STRING",
    )

    # Act / Assert
    with pytest.raises(Py4JJavaError, match="FAILFAST"):
        SparkJsonSchemaInferenceTransform(
            name="test",
            json_fields="value",
        ).transform(input)


@pytest.mark.parametrize(
    "json_fields",
    [
        "nonexistent",
        "root.nonexistent",
    ],
)
def test_transform_should_raise_error_when_json_field_does_not_exist(
    spark: SparkSession,
    json_fields: str,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"root": {"fullname": "John Doe"}}],
        schema="root STRUCT<fullname STRING>",
    )

    # Act / Assert
    with pytest.raises(AnalysisException):
        SparkJsonSchemaInferenceTransform(
            name="test",
            json_fields=json_fields,
        ).transform(input)


# ============================================================================
# Testing SparkJsonSchemaInferenceTransform - Flattening
# ============================================================================


def test_transform_should_flatten_json_columns(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [
            {"value": '{"name": "John", "age": 30}'},
            {"value": '{"name": "Mary", "age": 45}'},
        ],
        schema="value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields="value",
        flatten=True,
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            {"name": "John", "age": 30},
            {"name": "Mary", "age": 45},
        ],
        schema="age LONG, name STRING",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_preserve_columns_not_in_json_columns(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [
            {"id": 1, "value": '{"name": "John", "age": 30}'},
            {"id": 2, "value": '{"name": "Mary", "age": 45}'},
        ],
        schema="id INT, value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields="value",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            {"id": 1, "value": {"name": "John", "age": 30}},
            {"id": 2, "value": {"name": "Mary", "age": 45}},
        ],
        schema="id INT, value STRUCT<age LONG, name STRING>",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# Testing SparkJsonSchemaInferenceTransform - Reader Options
# ============================================================================


def test_transform_should_not_infer_primitive_as_string(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"value": '{"age": 30}'}],
        schema="value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields="value",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"value": {"age": 30}}],
        schema="value STRUCT<age LONG>",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_accept_json_with_single_quotes(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"value": "{'name': 'John'}"}],
        schema="value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields="value",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"value": {"name": "John"}}],
        schema="value STRUCT<name STRING>",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_accept_json_with_comments(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"value": '// comment\n{"name": "John"}'}],
        schema="value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields="value",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"value": {"name": "John"}}],
        schema="value STRUCT<name STRING>",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_accept_json_numbers_with_leading_zeros(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"value": '{"code": 007}'}],
        schema="value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields="value",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"value": {"code": 7}}],
        schema="value STRUCT<code BIGINT>",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_not_handle_duplicated_columns_when_flattening(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [
            {
                "user": '{"name": "John", "age": 30}',
                "address": '{"name": "Home", "city": "New York"}',
            },
        ],
        schema="user STRING, address STRING",
    )

    # Act
    result = SparkJsonSchemaInferenceTransform(
        name="test",
        json_fields=["user", "address"],
        flatten=True,
    ).transform(input)

    # Assert
    actual = result.schema
    expected = _parse_datatype_string("age BIGINT, name STRING, city STRING, name STRING")
    assertSchemaEqual(actual, expected)


# ============================================================================
# Testing SparkJsonSchemaInferenceTransform - Timestamp with timezone Enforcement
# ============================================================================


def test_transform_should_enforce_timestamp_with_timezone_fields(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": STR_2024_01_15T10_30_00Z}],
        schema="ts STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        timestamp_with_timezone_fields="ts",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"ts": OBJ_2024_01_15T10_30_00Z}],
        schema="ts TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_enforce_nested_timestamp_with_timezone_fields(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": {"created_at": STR_2024_01_15T10_30_00Z}}],
        schema="ts STRUCT<created_at STRING>",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        timestamp_with_timezone_fields="ts.created_at",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"ts": {"created_at": OBJ_2024_01_15T10_30_00Z}}],
        schema="ts STRUCT<created_at TIMESTAMP>",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_accept_custom_timestamp_with_timezone_format(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": STR_15_01_2024_10_30_00Z}],
        schema="ts STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        timestamp_with_timezone_fields="ts",
        timestamp_format=FMT_DD_MM_YYYY_HH_MM_SSX,
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"ts": OBJ_2024_01_15T10_30_00Z}],
        schema="ts TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.xfail(reason="to_timestamp silently returns null on format mismatch")
def test_transform_should_raise_error_when_timestamp_with_timezone_format_does_not_match(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": {"created_at": STR_2024_01_15T10_30_00Z}}],
        schema="ts STRUCT<created_at STRING>",
    )

    # Act / Assert
    with pytest.raises(ValueError):
        SparkJsonSchemaInferenceTransform(
            name="test",
            timestamp_with_timezone_fields="ts.created_at",
            timestamp_format=FMT_DD_MM_YYYY_HH_MM_SSX,
        ).transform(input)


def test_transform_should_raise_error_when_timestamp_with_timezone_field_does_not_exist(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"root": {"fullname": "John Doe"}}],
        schema="root STRUCT<fullname STRING>",
    )

    # Act / Assert
    with pytest.raises(AnalysisException):
        SparkJsonSchemaInferenceTransform(
            name="test",
            timestamp_with_timezone_fields="fullname",
        ).transform(input)


def test_transform_should_raise_error_when_nested_timestamp_with_timezone_field_does_not_exist(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"root": {"fullname": "John Doe"}}],
        schema="root STRUCT<fullname STRING>",
    )

    # Act / Assert
    with pytest.raises(AnalysisException):
        SparkJsonSchemaInferenceTransform(
            name="test",
            timestamp_with_timezone_fields="root.first_name",
        ).transform(input)


# ============================================================================
# Testing SparkJsonSchemaInferenceTransform - Timestamp without timezone Enforcement
# ============================================================================


def test_transform_should_enforce_timestamp_without_timezone_fields(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": "2024-01-15T10:30:00"}],
        schema="ts STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        timestamp_without_timezone_fields="ts",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"ts": OBJ_2024_01_15T10_30_00Z}],
        schema="ts TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_enforce_nested_timestamp_without_timezone_fields(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": {"created_at": STR_2024_01_15T10_30_00}}],
        schema="ts STRUCT<created_at STRING>",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        timestamp_without_timezone_fields="ts.created_at",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"ts": {"created_at": OBJ_2024_01_15T10_30_00Z}}],
        schema="ts STRUCT<created_at TIMESTAMP>",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_accept_custom_timestamp_without_timezone_format(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": STR_15_01_2024_10_30_00}],
        schema="ts STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        timestamp_without_timezone_fields="ts",
        timestamp_format=FMT_DD_MM_YYYY_HH_MM_SS,
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"ts": OBJ_2024_01_15T10_30_00Z}],
        schema="ts TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_truncate_time_when_timestamp_field_contains_date_only(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": STR_2024_01_15}],
        schema="ts STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        timestamp_without_timezone_fields="ts",
        timestamp_format=FMT_YYYY_MM_DD,
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"ts": OBJ_2024_01_15T00_00_00Z}],
        schema="ts TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_raise_error_when_timestamp_without_timezone_field_does_not_exist(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"root": {"fullname": "John Doe"}}],
        schema="root STRUCT<fullname STRING>",
    )

    # Act / Assert
    with pytest.raises(AnalysisException):
        SparkJsonSchemaInferenceTransform(
            name="test",
            timestamp_without_timezone_fields="fullname",
        ).transform(input)


def test_transform_should_raise_error_when_nested_timestamp_without_timezone_field_does_not_exist(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"root": {"fullname": "John Doe"}}],
        schema="root STRUCT<fullname STRING>",
    )

    # Act / Assert
    with pytest.raises(AnalysisException):
        SparkJsonSchemaInferenceTransform(
            name="test",
            timestamp_without_timezone_fields="root.first_name",
        ).transform(input)
