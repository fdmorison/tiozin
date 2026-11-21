import pytest

from tiozin.api.metadata.schema.model import Quality
from tiozin.exceptions import SchemaError


@pytest.mark.parametrize(
    "attributes, expected",
    [
        (
            {"type": "library", "metric": "rowCount", "mustBeGreaterThan": 0},
            {"type": "library", "metric": "rowCount", "mustBeGreaterThan": 0},
        ),
        (
            {"type": "sql", "query": "select count(*) from orders", "mustBeGreaterThan": 0},
            {"type": "sql", "query": "select count(*) from orders", "mustBeGreaterThan": 0},
        ),
        (
            {"type": "custom", "engine": "soda", "implementation": "row_count > 0"},
            {"type": "custom", "engine": "soda", "implementation": "row_count > 0"},
        ),
    ],
    ids=["library", "sql", "custom"],
)
def test_quality_should_accept_rule_with_what_its_type_needs(attributes, expected):
    # Act
    result = Quality(**attributes)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    assert actual == expected


def test_quality_should_default_type_to_library():
    # Act
    result = Quality(metric="nullValues", mustBe=0)

    # Assert
    actual = result.type
    expected = "library"
    assert actual == expected


def test_quality_should_accept_rule_with_only_description():
    # Act
    result = Quality(description="Orders are never empty")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"description": "Orders are never empty"}
    assert actual == expected


@pytest.mark.parametrize(
    "attributes, message",
    [
        (
            {"type": "library", "mustBe": 0},
            "A library quality rule needs a `metric`",
        ),
        (
            {"type": "sql", "mustBe": 0},
            "A sql quality rule needs a `query`",
        ),
        (
            {"type": "custom", "implementation": "row_count > 0"},
            "A custom quality rule needs an `engine` and an `implementation`",
        ),
        (
            {"type": "custom", "engine": "soda"},
            "A custom quality rule needs an `engine` and an `implementation`",
        ),
    ],
    ids=[
        "library_without_metric",
        "sql_without_query",
        "custom_without_engine",
        "custom_without_implementation",
    ],
)
def test_quality_should_raise_schema_error_when_rule_misses_what_its_type_needs(
    attributes, message
):
    # Act / Assert
    with pytest.raises(SchemaError, match=message):
        Quality(**attributes)


@pytest.mark.parametrize(
    "attributes",
    [
        {"metric": "rowCount"},
        {"metric": "rowCount", "mustBe": 0, "mustNotBe": 1},
        {"type": "sql", "query": "select count(*) from orders"},
    ],
    ids=["library_without_operator", "library_with_two_operators", "sql_without_operator"],
)
def test_quality_should_raise_schema_error_when_rule_has_not_exactly_one_operator(attributes):
    # Act / Assert
    with pytest.raises(
        SchemaError,
        match="A library or sql quality rule needs exactly one operator",
    ):
        Quality(**attributes)
