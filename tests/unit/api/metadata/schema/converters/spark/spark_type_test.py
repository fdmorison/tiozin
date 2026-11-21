import pytest

from tiozin.api.metadata.schema.converters.spark.spark_type import SparkType


@pytest.mark.parametrize(
    "json_value, expected",
    [
        ("long", "long"),
        ("string", "string"),
        ("decimal(10,2)", "decimal(10,2)"),
        ("varchar(10)", "varchar(10)"),
        ("char(3)", "char(3)"),
        ("timestamp_ntz", "timestamp_ntz"),
        (
            {"type": "array", "elementType": "string", "containsNull": True},
            '{"type": "array", "elementType": "string", "containsNull": true}',
        ),
    ],
)
def test_physical_type_should_be_type_as_written(json_value, expected):
    # Act
    result = SparkType(json_value).physical_type

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        ("long", []),
        (
            "decimal(10,2)",
            [{"property": "precision", "value": 10}, {"property": "scale", "value": 2}],
        ),
        (
            "decimal",
            [{"property": "precision", "value": 10}, {"property": "scale", "value": 0}],
        ),
        ("timestamp", [{"property": "timeUnit", "value": "micros"}]),
        ("timestamp_ntz", [{"property": "timeUnit", "value": "micros"}]),
        ("binary", [{"property": "binary", "value": True}]),
        ("time(3)", [{"property": "timeUnit", "value": "millis"}]),
        ("time(6)", [{"property": "timeUnit", "value": "micros"}]),
        ("time", [{"property": "timeUnit", "value": "micros"}]),
    ],
)
def test_type_parameters_should_hold_parameters_the_type_implies(json_value, expected):
    # Act
    result = SparkType(json_value).type_parameters

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        ("time(3)", "time"),
        ("time(6)", "time"),
        ("time", "time"),
        ("timestamp", "timestamp"),
        ({"type": "struct", "fields": []}, "object"),
    ],
)
def test_logical_type_should_map_spark_type_to_logical_type(json_value, expected):
    # Act
    result = SparkType(json_value).logical_type

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        ("varchar(10)", {"maxLength": 10}),
        ("char(3)", {"minLength": 3, "maxLength": 3}),
        ("byte", {"format": "i8"}),
        ("short", {"format": "i16"}),
        ("integer", {"format": "i32"}),
        ("long", {"format": "i64"}),
        ("float", {"format": "f32"}),
        ("double", {"format": "f64"}),
        ("timestamp", {"timezone": True}),
        ("timestamp_ntz", {"timezone": False}),
    ],
)
def test_logical_type_options_should_hold_options_the_type_implies(json_value, expected):
    # Act
    result = SparkType(json_value).logical_type_options

    # Assert
    actual = result
    assert actual == expected


def test_logical_type_options_should_be_none_when_type_implies_none():
    # Act
    result = SparkType("string").logical_type_options

    # Assert
    assert result is None


@pytest.mark.parametrize(
    "json_value, expected",
    [
        ("decimal(10,2)", (10, 2)),
        ("varchar(10)", (10,)),
        ("long", ()),
        ({"type": "array", "elementType": "string"}, ()),
    ],
)
def test_type_arguments_should_hold_numbers_between_parentheses(json_value, expected):
    # Act
    result = SparkType(json_value).type_arguments

    # Assert
    actual = result
    assert actual == expected
