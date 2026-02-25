import pytest

from tiozin.exceptions import TiozinInputError
from tiozin.utils.runtime import bind_data_tokens

# ============================================================================
# Testing bind_data_tokens() - Token Resolution
# ============================================================================


def test_bind_data_tokens_should_resolve_at_data_to_first_input():
    # Act
    result = bind_data_tokens("SELECT * FROM @data", ["my_view"])

    # Assert
    actual = result
    expected = "SELECT * FROM my_view"
    assert actual == expected


def test_bind_data_tokens_should_resolve_at_data0_to_first_input():
    # Act
    result = bind_data_tokens("SELECT * FROM @data0", ["my_view"])

    # Assert
    actual = result
    expected = "SELECT * FROM my_view"
    assert actual == expected


def test_bind_data_tokens_should_resolve_at_data1_to_second_input():
    # Act
    result = bind_data_tokens("SELECT * FROM @data1", ["first", "second"])

    # Assert
    actual = result
    expected = "SELECT * FROM second"
    assert actual == expected


def test_bind_data_tokens_should_resolve_at_data2_to_third_input():
    # Act
    result = bind_data_tokens("SELECT * FROM @data2", ["first", "second", "third"])

    # Assert
    actual = result
    expected = "SELECT * FROM third"
    assert actual == expected


def test_bind_data_tokens_should_resolve_multiple_tokens_in_single_query():
    # Act
    result = bind_data_tokens(
        "SELECT * FROM @data c JOIN @data1 o ON c.id = o.customer_id",
        ["customers", "orders"],
    )

    # Assert
    actual = result
    expected = "SELECT * FROM customers c JOIN orders o ON c.id = o.customer_id"
    assert actual == expected


def test_bind_data_tokens_should_resolve_same_token_multiple_times():
    # Act
    result = bind_data_tokens(
        "SELECT * FROM @data WHERE @data.id > 0",
        ["my_view"],
    )

    # Assert
    actual = result
    expected = "SELECT * FROM my_view WHERE my_view.id > 0"
    assert actual == expected


def test_bind_data_tokens_should_pass_through_sql_without_tokens():
    # Arrange
    sql = "SELECT * FROM customers JOIN orders ON customers.id = orders.customer_id"

    # Act
    result = bind_data_tokens(sql, ["ignored_input"])

    # Assert
    actual = result
    expected = sql
    assert actual == expected


# ============================================================================
# Testing bind_data_tokens() - Boundary Safety
# ============================================================================


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM @database",
        "SELECT * FROM @dataset",
        "SELECT * FROM @dataframe",
        "SELECT * FROM @datastore",
        "SELECT * FROM @data_something",
    ],
)
def test_bind_data_tokens_should_not_replace_tokens_with_word_suffix(sql: str):
    """
    Validates that @data followed by letters, digits, or underscores is NOT
    treated as a token. This prevents false positives in SQL dialects that use
    @variable syntax (e.g. @database, @dataset).
    """
    # Act
    result = bind_data_tokens(sql, ["my_view"])

    # Assert — the SQL must be unchanged
    actual = result
    expected = sql
    assert actual == expected


@pytest.mark.parametrize(
    "sql,expected",
    [
        ("SELECT * FROM (@data)", "SELECT * FROM (my_view)"),
        ("SELECT * FROM @data, orders", "SELECT * FROM my_view, orders"),
        ("SELECT * FROM @data WHERE id > 1", "SELECT * FROM my_view WHERE id > 1"),
        ("SELECT * FROM @data;", "SELECT * FROM my_view;"),
    ],
)
def test_bind_data_tokens_should_replace_token_adjacent_to_punctuation(sql: str, expected: str):
    # Act
    result = bind_data_tokens(sql, ["my_view"])

    # Assert
    actual = result
    assert actual == expected


# ============================================================================
# Testing bind_data_tokens() - Failure Scenarios
# ============================================================================


def test_bind_data_tokens_should_fail_when_inputs_are_empty():
    # Act / Assert
    with pytest.raises(TiozinInputError):
        bind_data_tokens("SELECT * FROM @data", [])


def test_bind_data_tokens_should_fail_when_referenced_index_is_out_of_range():
    # Act / Assert
    with pytest.raises(TiozinInputError, match="@data1"):
        bind_data_tokens("SELECT * FROM @data1", ["only_one"])


def test_bind_data_tokens_should_fail_when_referenced_input_is_none():
    # Act / Assert
    with pytest.raises(TiozinInputError, match="@data0"):
        bind_data_tokens("SELECT * FROM @data", [None])
