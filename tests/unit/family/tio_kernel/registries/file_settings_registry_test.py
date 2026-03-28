from pathlib import Path
from unittest.mock import patch

import pytest

import tiozin.config as config
from tiozin.api import SettingsManifest
from tiozin.exceptions import SettingsNotFoundError
from tiozin.family.tio_kernel import FileSettingRegistry

MOCK_DIR = Path("tests/mocks/settings")


# ============================================================================
# get()
# ============================================================================
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


# ============================================================================
# register()
# ============================================================================
@pytest.mark.parametrize("extension", [".yaml", ".yml"])
def test_register_should_write_yaml_file(tmp_path, extension):
    # Arrange
    registry = FileSettingRegistry()
    manifest = SettingsManifest()
    path = tmp_path / f"tiozin{extension}"

    # Act
    registry.register(str(path), manifest)

    # Assert
    assert path.exists()


def test_register_should_write_json_file(tmp_path):
    # Arrange
    registry = FileSettingRegistry()
    manifest = SettingsManifest()
    path = tmp_path / "tiozin.json"

    # Act
    registry.register(str(path), manifest)

    # Assert
    assert path.exists()


def test_register_should_fail_on_unsupported_extension(tmp_path):
    # Arrange
    registry = FileSettingRegistry()
    manifest = SettingsManifest()

    # Act / Assert
    with pytest.raises(ValueError, match="Unsupported file format"):
        registry.register(str(tmp_path / "tiozin.toml"), manifest)
