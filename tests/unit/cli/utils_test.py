import pytest
import typer

from tiozin.cli.utils import parse_params


@pytest.mark.parametrize(
    "item,expected",
    [
        ("foo=1", {"foo": 1}),
        ("bar=true", {"bar": True}),
        ("ratio=0.5", {"ratio": 0.5}),
        ("stage=daily", {"stage": "daily"}),
    ],
)
def test_parse_params_should_load_value_as_yaml_type(item, expected):
    # Act
    result = parse_params([item])

    # Assert
    actual = result
    assert actual == expected


def test_parse_params_should_return_dict_with_all_keys():
    # Act
    result = parse_params(["foo=1", "bar=true", "stage=daily"])

    # Assert
    actual = result
    expected = {"foo": 1, "bar": True, "stage": "daily"}
    assert actual == expected


@pytest.mark.parametrize("attributes", [None, []])
def test_parse_params_should_return_empty_dict_when_no_attributes(attributes):
    # Act
    result = parse_params(attributes)

    # Assert
    actual = result
    expected = {}
    assert actual == expected


def test_parse_params_should_split_on_first_equals_when_value_contains_equals():
    # Act
    result = parse_params(["expr=a=b"])

    # Assert
    actual = result
    expected = {"expr": "a=b"}
    assert actual == expected


def test_parse_params_should_raise_bad_parameter_when_item_has_no_equals():
    # Act / Assert
    with pytest.raises(typer.BadParameter):
        parse_params(["foo"])


def test_parse_params_should_raise_bad_parameter_when_value_is_malformed_yaml():
    # Act / Assert
    with pytest.raises(typer.BadParameter):
        parse_params(["foo=[1, 2"])


def test_parse_params_should_nest_dotted_key():
    # Act
    result = parse_params(["a.b.c=value"])

    # Assert
    actual = result
    expected = {"a": {"b": {"c": "value"}}}
    assert actual == expected


def test_parse_params_should_merge_dotted_keys_with_common_prefix():
    # Act
    result = parse_params(["a.b=1", "a.c=2"])

    # Assert
    actual = result
    expected = {"a": {"b": 1, "c": 2}}
    assert actual == expected


def test_parse_params_should_parse_flat_and_dotted_keys_together():
    # Act
    result = parse_params(["flat=1", "a.b=2"])

    # Assert
    actual = result
    expected = {"flat": 1, "a": {"b": 2}}
    assert actual == expected


def test_parse_params_should_return_nested_value_as_plain_dict():
    # Act
    result = parse_params(["a.b=1"])

    # Assert
    actual = type(result["a"])
    expected = dict
    assert actual == expected


def test_parse_params_should_raise_bad_parameter_with_custom_qualifier():
    # Act / Assert
    with pytest.raises(typer.BadParameter, match="bookmark"):
        parse_params(["foo"], qualifier="bookmark")
