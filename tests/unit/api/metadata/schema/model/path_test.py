import pytest

from tiozin.api.metadata.schema.model import PropertyPath
from tiozin.exceptions import SchemaError


def test_path_should_split_dotted_string_into_names():
    # Act
    result = PropertyPath("friends.name")

    # Assert
    actual = result
    expected = ("friends", "name")
    assert actual == expected


def test_path_should_accept_sequence_of_names():
    # Act
    result = PropertyPath(["friends", "name"])

    # Assert
    actual = result
    expected = ("friends", "name")
    assert actual == expected


def test_name_should_return_last_name():
    # Arrange
    path = PropertyPath("profile.address.city")

    # Act
    result = path.name

    # Assert
    actual = result
    expected = "city"
    assert actual == expected


def test_parents_should_return_path_without_last_name():
    # Arrange
    path = PropertyPath("profile.address.city")

    # Act
    result = path.parents

    # Assert
    actual = result
    expected = ("profile", "address")
    assert actual == expected


def test_parents_should_be_empty_for_top_level_name():
    # Arrange
    path = PropertyPath("city")

    # Act
    result = path.parents

    # Assert
    actual = result
    expected = ()
    assert actual == expected


def test_str_should_join_names_with_dots():
    # Arrange
    path = PropertyPath(["profile", "address", "city"])

    # Act
    result = str(path)

    # Assert
    actual = result
    expected = "profile.address.city"
    assert actual == expected


@pytest.mark.parametrize(
    "path",
    [
        "",
        "a..b",
        ".a",
        "a.",
        [],
        ["a", ""],
    ],
)
def test_path_should_raise_schema_error_when_a_name_is_empty(path):
    # Act / Assert
    with pytest.raises(SchemaError):
        PropertyPath(path)
