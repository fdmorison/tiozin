import pytest

from tiozin.exceptions import PluginConflictError, PluginError, PluginNotFoundError


def test_plugin_not_found_error_should_format_plugin_name_in_message():
    # Act
    error = PluginNotFoundError(name="my_plugin")

    # Assert
    assert error.message == "Tiozin `my_plugin` not found."


def test_ambiguous_plugin_error_should_format_plugin_name_and_candidates_in_message():
    # Arrange
    plugin_name = "my_plugin"
    candidates = ["provider1.my_plugin", "provider2.my_plugin"]

    # Act
    error = PluginConflictError(name=plugin_name, candidates=candidates)

    # Assert
    actual = error.message
    expected = (
        "The Tiozin name 'my_plugin' matches multiple registered Tiozin plugins. "
        "Available provider-qualified options are: provider1.my_plugin and provider2.my_plugin. "
        "You can disambiguate by specifying the provider-qualified name "
        "or the fully qualified Python class path."
    )
    assert actual == expected


def test_ambiguous_plugin_error_should_handle_empty_candidates_list():
    # Arrange
    plugin_name = "my_plugin"

    # Act
    error = PluginConflictError(name=plugin_name, candidates=[])

    # Assert
    actual = "" in error.message
    expected = True
    assert actual == expected


@pytest.mark.parametrize(
    "error",
    [
        PluginNotFoundError(name="x"),
        PluginConflictError(name="x"),
    ],
)
def test_plugin_errors_should_be_catchable_as_plugin_error(error):
    with pytest.raises(PluginError):
        raise error
