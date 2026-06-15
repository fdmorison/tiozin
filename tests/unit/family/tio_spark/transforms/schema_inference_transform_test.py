from datetime import UTC, datetime

import pytest
from py4j.protocol import Py4JJavaError
from pyspark.sql import SparkSession
from pyspark.sql.utils import AnalysisException
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark import SparkSchemaInferenceTransform

STR_2024_01_15T10_30_00_UTC = "2024-01-15T10:30:00Z"
STR_2024_01_15T10_30_00_BRT = "2024-01-15T10:30:00-03:00"
STR_2024_01_15T10_30_00_NTZ = "2024-01-15T10:30:00"
OBJ_2024_01_15T10_30_00_UTC = datetime.fromisoformat(STR_2024_01_15T10_30_00_UTC)
OBJ_2024_01_15T10_30_00_NTZ = datetime.fromisoformat(STR_2024_01_15T10_30_00_NTZ)

OBJ_2024_01_15T13_30_00_UTC = datetime(2024, 1, 15, 13, 30, 0, tzinfo=UTC)
OBJ_2024_01_15T14_30_00_UTC = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

# ============================================================================
# Testing SparkSchemaInferenceTransform - Schema Inference
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
    actual = SparkSchemaInferenceTransform(
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
    actual = SparkSchemaInferenceTransform(
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
    actual = SparkSchemaInferenceTransform(
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
    actual = SparkSchemaInferenceTransform(
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
        SparkSchemaInferenceTransform(
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
        SparkSchemaInferenceTransform(
            name="test",
            json_fields=json_fields,
        ).transform(input)


# ============================================================================
# Testing SparkSchemaInferenceTransform - Flattening
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
    actual = SparkSchemaInferenceTransform(
        name="test",
        json_fields="value",
        unnest_fields=["value"],
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
    actual = SparkSchemaInferenceTransform(
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
# Testing SparkSchemaInferenceTransform - Reader Options
# ============================================================================


def test_transform_should_not_infer_primitive_as_string(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"value": '{"age": 30}'}],
        schema="value STRING",
    )

    # Act
    actual = SparkSchemaInferenceTransform(
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
    actual = SparkSchemaInferenceTransform(
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
    actual = SparkSchemaInferenceTransform(
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
    actual = SparkSchemaInferenceTransform(
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
    result = SparkSchemaInferenceTransform(
        name="test",
        json_fields=["user", "address"],
        unnest_fields=["user", "address"],
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [(30, "John", "New York", "Home")],
        schema="age BIGINT, name STRING, city STRING, name STRING",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# Testing SparkSchemaInferenceTransform - Auto Timestamp Enforcement
# ============================================================================


def test_transform_should_enforce_auto_timestamp_fields(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [
            (STR_2024_01_15T10_30_00_UTC,),
            (STR_2024_01_15T10_30_00_BRT,),
            (STR_2024_01_15T10_30_00_NTZ,),
            ("1705314600",),
        ],
        schema="ts STRING",
    )

    # Act
    actual = SparkSchemaInferenceTransform(
        name="test",
        auto_timestamp_fields="ts",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            (OBJ_2024_01_15T10_30_00_UTC,),
            (OBJ_2024_01_15T13_30_00_UTC,),
            (OBJ_2024_01_15T10_30_00_UTC,),
            (OBJ_2024_01_15T10_30_00_UTC,),
        ],
        schema="ts TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_enforce_nested_auto_timestamp_fields(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": {"created_at": STR_2024_01_15T10_30_00_UTC}}],
        schema="ts STRUCT<created_at STRING>",
    )

    # Act
    actual = SparkSchemaInferenceTransform(
        name="test",
        auto_timestamp_fields="ts.created_at",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"ts": {"created_at": OBJ_2024_01_15T10_30_00_UTC}}],
        schema="ts STRUCT<created_at TIMESTAMP>",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_enforce_timezone_for_naive_auto_timestamp_fields(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"ts": STR_2024_01_15T10_30_00_NTZ}],
        schema="ts STRING",
    )

    # Act
    actual = SparkSchemaInferenceTransform(
        name="test",
        auto_timestamp_fields="ts",
        timezone="America/Sao_Paulo",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [{"ts": OBJ_2024_01_15T13_30_00_UTC}],
        schema="ts TIMESTAMP",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_raise_error_when_auto_timestamp_field_is_missing(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"root": {"fullname": "John Doe"}}],
        schema="root STRUCT<fullname STRING>",
    )

    # Act / Assert
    with pytest.raises(AnalysisException):
        SparkSchemaInferenceTransform(
            name="test",
            auto_timestamp_fields="fullname",
        ).transform(input)


def test_transform_should_raise_error_when_nested_auto_timestamp_field_is_missing(
    spark: SparkSession,
) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"root": {"fullname": "John Doe"}}],
        schema="root STRUCT<fullname STRING>",
    )

    # Act / Assert
    with pytest.raises(AnalysisException):
        SparkSchemaInferenceTransform(
            name="test",
            auto_timestamp_fields="root.first_name",
        ).transform(input)
