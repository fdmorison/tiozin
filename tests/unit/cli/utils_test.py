import pytest
import typer

from tiozin.cli.utils import parse_attributes


@pytest.mark.parametrize(
    "item,expected",
    [
        ("foo=1", {"foo": 1}),
        ("bar=true", {"bar": True}),
        ("ratio=0.5", {"ratio": 0.5}),
        ("stage=daily", {"stage": "daily"}),
    ],
)
def test_parse_attributes_should_load_value_as_yaml_type(item, expected):
    # Act
    result = parse_attributes([item])

    # Assert
    actual = result
    assert actual == expected


def test_parse_attributes_should_return_dict_with_all_keys():
    # Act
    result = parse_attributes(["foo=1", "bar=true", "stage=daily"])

    # Assert
    actual = result
    expected = {"foo": 1, "bar": True, "stage": "daily"}
    assert actual == expected


@pytest.mark.parametrize("attributes", [None, []])
def test_parse_attributes_should_return_empty_dict_when_no_attributes(attributes):
    # Act
    result = parse_attributes(attributes)

    # Assert
    actual = result
    expected = {}
    assert actual == expected


def test_parse_attributes_should_split_on_first_equals_when_value_contains_equals():
    # Act
    result = parse_attributes(["expr=a=b"])

    # Assert
    actual = result
    expected = {"expr": "a=b"}
    assert actual == expected


def test_parse_attributes_should_raise_bad_parameter_when_item_has_no_equals():
    # Act / Assert
    with pytest.raises(typer.BadParameter):
        parse_attributes(["foo"])


def test_parse_attributes_should_raise_bad_parameter_when_value_is_malformed_yaml():
    # Act / Assert
    with pytest.raises(typer.BadParameter):
        parse_attributes(["foo=[1, 2"])
