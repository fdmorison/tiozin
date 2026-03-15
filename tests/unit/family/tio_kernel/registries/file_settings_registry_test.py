from pathlib import Path
from unittest.mock import patch

import pytest

import tiozin.config as config
from tiozin.api import SettingsManifest
from tiozin.exceptions import SettingsNotFoundError, TiozinInternalError
from tiozin.family.tio_kernel import FileSettingRegistry

MOCK_DIR = Path("tests/mocks/settings")


# ============================================================================
# get()
# ============================================================================
def test_get_should_load_manifest_from_file():
    # Arrange
    registry = FileSettingRegistry(path=MOCK_DIR / "default.yaml")

    # Act
    result = registry.get()

    # Assert
    actual = result.registries.job.kind
    expected = "FileJobRegistry"
    assert actual == expected


@patch.object(config, "tiozin_settings_path", str(MOCK_DIR / "default.yaml"))
def test_get_should_load_manifest_from_config():
    # Arrange
    registry = FileSettingRegistry()

    # Act
    result = registry.get()

    # Assert
    actual = result.registries.job.kind
    expected = "FileJobRegistry"
    assert actual == expected


@patch.object(config, "tiozin_settings_search_paths", (MOCK_DIR / "default.yaml",))
def test_get_should_load_manifest_from_search_paths():
    # Arrange
    registry = FileSettingRegistry()

    # Act
    result = registry.get()

    # Assert
    actual = result.registries.job.kind
    expected = "FileJobRegistry"
    assert actual == expected


@patch.object(config, "tiozin_settings_path", None)
@patch.object(config, "tiozin_settings_search_paths", ())
def test_get_should_load_manifest_from_builtin_settings():
    # Arrange
    registry = FileSettingRegistry()

    # Act
    result = registry.get()

    # Assert
    actual = (
        result.kind,
        result.registries.settings.kind,
        result.registries.job.kind,
    )
    expected = (
        "Settings",
        "tio_kernel:FileSettingRegistry",
        "tio_kernel:FileJobRegistry",
    )
    assert actual == expected


def test_get_should_fail_when_path_not_found():
    # Arrange
    registry = FileSettingRegistry(path="missing.yaml")

    # Act / Assert
    with pytest.raises(SettingsNotFoundError):
        registry.get()


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
    with pytest.raises(ValueError, match="Unsupported settings format"):
        registry.register(str(tmp_path / "tiozin.toml"), manifest)


# ============================================================================
# delegate()
# ============================================================================
def test_delegate_should_stop_delegation_when_path_is_missing():
    # Arrange
    registry = FileSettingRegistry(path=MOCK_DIR / "delegate_to_path_missing.yaml")

    # Act
    result = registry.delegate()

    # Assert
    actual = (result.path, result.kind)
    expected = (None, "FileSettingRegistry")
    assert actual == expected


def test_delegate_should_stop_delegation_when_path_is_null():
    # Arrange
    registry = FileSettingRegistry(path=MOCK_DIR / "delegate_to_path_null.yaml")

    # Act
    result = registry.delegate()

    # Assert
    actual = (result.path, result.kind)
    expected = (None, "FileSettingRegistry")
    assert actual == expected


def test_delegate_should_chain_many_files():
    # Arrange
    registry = FileSettingRegistry(path=MOCK_DIR / "delegate_1.yaml")

    # Act
    result = registry.delegate()

    # Assert
    actual = result.kind
    expected = "NoOpSettingRegistry"  # delegate_1.yaml > delegate_2.yaml > delegate_3.yaml
    assert actual == expected


def test_delegate_should_fail_on_circular_reference():
    # Arrange
    registry = FileSettingRegistry(path=MOCK_DIR / "delegate_circular.yaml")

    # Act / Assert
    with pytest.raises(TiozinInternalError, match="Circular settings delegation"):
        registry.delegate()
