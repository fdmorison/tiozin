import pytest

from tiozin.api.metadata.schema.model import Case


@pytest.mark.parametrize(
    "case, expected",
    [
        (Case.SNAKE, "first_name"),
        (Case.CAMEL, "firstName"),
        (Case.PASCAL, "FirstName"),
        (Case.MACRO, "FIRST_NAME"),
        (Case.KEBAB, "first-name"),
        (Case.COBOL, "FIRST-NAME"),
        (Case.FLAT, "firstname"),
        (Case.UPPERFLAT, "FIRSTNAME"),
    ],
)
def test_convert_should_write_name_in_case(case, expected):
    # Act
    result = case.convert("first_name")

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "name",
    [
        "firstName",
        "FirstName",
        "FIRST_NAME",
        "first-name",
        "First Name",
        "first.name",
        "first@name!",
    ],
)
def test_convert_should_split_words_of_any_case_and_separator(name):
    # Act
    result = Case.SNAKE.convert(name)

    # Assert
    actual = result
    expected = "first_name"
    assert actual == expected


def test_convert_should_split_acronym_from_next_word():
    # Act
    result = Case.SNAKE.convert("HTTPServer")

    # Assert
    actual = result
    expected = "http_server"
    assert actual == expected


def test_convert_should_replace_accents_with_plain_letters():
    # Act
    result = Case.CAMEL.convert("São Paulo")

    # Assert
    actual = result
    expected = "saoPaulo"
    assert actual == expected


@pytest.mark.parametrize(
    "case, expected",
    [
        (Case.SNAKE, "_1st_place"),
        (Case.CAMEL, "_1stPlace"),
        (Case.PASCAL, "_1stPlace"),
        (Case.MACRO, "_1ST_PLACE"),
        (Case.KEBAB, "_1st-place"),
        (Case.COBOL, "_1ST-PLACE"),
        (Case.FLAT, "_1stplace"),
        (Case.UPPERFLAT, "_1STPLACE"),
    ],
)
def test_convert_should_prefix_underscore_when_name_starts_with_digit(case, expected):
    # Act
    result = case.convert("1st place")

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize("case", list(Case))
@pytest.mark.parametrize("name", ["%", "$$$"])
def test_convert_should_write_underscore_when_name_has_only_special_characters(case, name):
    # Act
    result = case.convert(name)

    # Assert
    actual = result
    expected = "_"
    assert actual == expected
