"""
=================================================================================
TIOZIN TEST TEMPLATES
=================================================================================

NAMING CONVENTION:
------------------
Pattern: test_<subject>_should_<expected>(_when_<condition>)?

Examples:
- test_add_should_return_sum()
- test_divide_should_raise_error_when_divisor_is_zero()
- test_user_should_be_active_when_created()

AAA STRUCTURE:
--------------
1. Arrange - Setup test data and dependencies
2. Act - Execute the code being tested
3. Assert - Verify expected behavior using actual/expected pattern

EXAMPLE:
--------
    def test_add_should_return_sum():
        # Arrange
        a = 2
        b = 3

        # Act
        result = add(a, b)

        # Assert
        actual = result
        expected = 5
        assert actual == expected
"""

from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# TEMPLATE 1: Happy Path (without mock)
# =============================================================================


def hello_world(name: str, detail: str = None) -> str:
    """Example function that greets with optional detail."""
    if detail:
        return f"Hello, {name}! {detail}"
    return f"Hello, {name}!"


def test_hello_world_should_return_greeting():
    """
    This is a template for simple tests without mocks.
    Use when testing pure functions or methods without external dependencies.
    Tests the default behavior without 'when' clause.
    """
    # Arrange
    name = "World"

    # Act
    result = hello_world(name)

    # Assert
    actual = result
    expected = "Hello, World!"
    assert actual == expected


def test_hello_world_should_include_detail_when_detail_is_provided():
    """
    This is an example of using 'when' to specify a particular condition.
    Use 'when' when testing edge cases or specific scenarios.
    """
    # Arrange
    name = "Alice"
    detail = "Nice to see you."

    # Act
    result = hello_world(name, detail)

    # Assert
    actual = result
    expected = "Hello, Alice! Nice to see you."
    assert actual == expected


# =============================================================================
# TEMPLATE 2: Teste Parametrizado
# =============================================================================


@pytest.mark.parametrize(
    "name",
    ["World", "Alice", "Bob", "Charlie"],
)
def test_hello_world_should_return_expected_when_parametrized(name: str):
    """
    Tests multiple scenarios at once using parametrization.

    Use this template when you need to test the same logic
    with different sets of input data.
    """
    # Arrange
    # (inputs come from parameters)

    # Act
    result = hello_world(name)

    # Assert
    actual = result
    expected = f"Hello, {name}!"
    assert actual == expected


# =============================================================================
# TEMPLATE 3: Teste com MagicMock
# =============================================================================


def greet_from_source(source) -> str:
    """Example function that uses an external source to get name."""
    name = source.get_name()
    return hello_world(name)


def test_greet_from_source_should_return_greeting():
    """
    Tests function that depends on external object using MagicMock.

    Use MagicMock when you need to simulate external dependencies
    like database connections, API clients, or service objects.
    """
    # Arrange
    mock_source = MagicMock()
    mock_source.get_name = MagicMock(return_value="Alice")

    # Act
    greet_from_source(mock_source)

    # Assert
    mock_source.get_name.assert_called_once()


# =============================================================================
# TEMPLATE 4: Teste com Patch
# =============================================================================


def greet_random_user() -> str:
    """Example function that gets a random name and greets."""
    import random

    names = ["Alice", "Bob", "Charlie"]
    name = random.choice(names)
    return hello_world(name)


@patch("random.choice")
def test_greet_random_user_should_return_greeting(mock_choice):
    """
    Tests function that uses external module using patch.

    Use @patch when you need to replace imports or built-in
    functions during the test.

    IMPORTANT: The path should reference where the function is USED,
    not where it is DEFINED.
    """
    # Arrange
    mock_choice.return_value = "Alice"

    # Act
    result = greet_random_user()

    # Assert
    actual = result
    expected = "Hello, Alice!"
    assert actual == expected
