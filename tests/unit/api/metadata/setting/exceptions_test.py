import pytest

from tiozin.exceptions import SettingsError, SettingsNotFoundError


def test_settings_not_found_error_should_show_location():
    # Arrange
    location = "/etc/tiozin/settings.yaml"

    # Act
    error = SettingsNotFoundError(location=location)

    # Assert
    actual = error.message
    expected = f"Settings not found: '{location}'."
    assert actual == expected


def test_settings_not_found_error_raise_if_should_raise_when_condition_is_true():
    with pytest.raises(SettingsNotFoundError, match="/missing/settings.yaml"):
        SettingsNotFoundError.raise_if(True, "/missing/settings.yaml")


@pytest.mark.parametrize(
    "error",
    [
        SettingsNotFoundError(location="x"),
    ],
)
def test_settings_errors_should_be_catchable_as_settings_error(error):
    with pytest.raises(SettingsError):
        raise error
