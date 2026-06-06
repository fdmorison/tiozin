import pytest
from py4j.protocol import Py4JJavaError
from pyspark.sql import SparkSession
from pyspark.sql.types import _parse_datatype_string
from pyspark.testing import assertDataFrameEqual, assertSchemaEqual

from tiozin.family.tio_spark import SparkJsonSchemaInferenceTransform


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
        json_columns="value",
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
        json_columns=["user", "address"],
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
        json_columns="value",
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
        json_columns="value",
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
        json_columns="value",
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


def test_transform_should_not_infer_primitive_as_string(spark: SparkSession) -> None:
    # Arrange
    input = spark.createDataFrame(
        [{"value": '{"age": 30}'}],
        schema="value STRING",
    )

    # Act
    actual = SparkJsonSchemaInferenceTransform(
        name="test",
        json_columns="value",
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
        json_columns="value",
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
        json_columns="value",
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
        json_columns="value",
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
        json_columns=["user", "address"],
        flatten=True,
    ).transform(input)

    # Assert
    actual = result.schema
    expected = _parse_datatype_string("age BIGINT, name STRING, city STRING, name STRING")
    assertSchemaEqual(actual, expected)


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
            json_columns="value",
        ).transform(input)
