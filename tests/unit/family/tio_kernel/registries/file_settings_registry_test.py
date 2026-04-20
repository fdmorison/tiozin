from pathlib import Path
from unittest.mock import patch

import pytest

import tiozin.config as config
from tiozin.api import SettingsManifest
from tiozin.exceptions import SettingsNotFoundError
from tiozin.family.tio_kernel import FileSettingRegistry

MOCK_DIR = Path("tests/mocks/settings")


def test_get_should_load_manifest_from_file(default_settings_manifest):
    # Arrange
    registry = FileSettingRegistry(location=MOCK_DIR / "default.yaml")

    # Act
    result = registry.get()

    # Assert
    actual = result
    expected = default_settings_manifest
    assert actual == expected


@patch.object(config, "tiozin_settings_search_paths", (MOCK_DIR / "default.yaml",))
def test_get_should_load_manifest_from_search_paths(default_settings_manifest):
    # Arrange
    registry = FileSettingRegistry()
    registry.setup()

    # Act
    result = registry.get()

    # Assert
    actual = result
    expected = default_settings_manifest
    assert actual == expected


@patch.object(config, "tiozin_settings_search_paths", ())
def test_get_should_load_manifest_from_builtin_settings():
    # Arrange
    registry = FileSettingRegistry()

    # Act
    result = registry.get()

    # Assert
    actual = result
    expected = SettingsManifest()
    assert actual == expected


def test_setup_should_fail_when_path_not_found():
    # Arrange
    registry = FileSettingRegistry(location="missing.yaml")

    # Act / Assert
    with pytest.raises(SettingsNotFoundError):
        registry.setup()
