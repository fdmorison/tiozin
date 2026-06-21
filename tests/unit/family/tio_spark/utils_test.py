import pytest

from tiozin.family.tio_spark import utils as su


def test_split_field_should_split_on_dots() -> None:
    # Act
    actual = su.split_field("address.city")

    # Assert
    expected = ["address", "city"]
    assert actual == expected


def test_split_field_should_keep_single_component() -> None:
    # Act
    actual = su.split_field("name")

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
    actual = su.split_field(field)

    # Assert
    assert actual == expected


def test_join_field_should_join_on_dots() -> None:
    # Act
    actual = su.join_field(["address", "city"])

    # Assert
    assert actual == "address.city"


def test_join_field_should_keep_single_component() -> None:
    # Act
    actual = su.join_field(["name"])

    # Assert
    assert actual == "name"


def test_join_field_should_not_escape_dots_by_default() -> None:
    # Arrange
    fields = ["created.at"]

    # Act
    actual = su.join_field(fields)

    # Assert
    expected = "created.at"
    assert actual == expected


def test_join_field_should_escape_dots_when_enabled() -> None:
    # Arrange
    fields = ["created.at"]

    # Act
    actual = su.join_field(fields, escape=True)

    # Assert
    expected = "created\\.at"
    assert actual == expected


def test_join_field_should_escape_only_components_with_dots() -> None:
    # Act
    actual = su.join_field(["address.city", "name"], escape=True)

    # Assert
    expected = "address\\.city.name"
    assert actual == expected


def test_join_field_should_return_empty_string_for_empty_list() -> None:
    # Act
    actual = su.join_field([])

    # Assert
    expected = ""
    assert actual == expected


def test_join_field_should_return_empty_string_for_single_empty_component() -> None:
    # Act
    actual = su.join_field([""])

    # Assert
    expected = ""
    assert actual == expected


def test_join_field_should_return_null_for_null_list() -> None:
    # Act
    actual = su.join_field(None)

    # Assert
    assert actual is None


def test_join_field_should_round_trip_through_split_field_when_escaping() -> None:
    # Arrange
    fields = ["event", "created.at", "value"]

    # Act
    joined = su.join_field(fields, escape=True)
    actual = su.split_field(joined)

    # Assert
    expected = ["event", "created.at", "value"]
    assert actual == expected
