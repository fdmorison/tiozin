from pathlib import Path
from unittest.mock import patch

import pytest

import tiozin.config as config
from tiozin.api import SettingsManifest
from tiozin.api.metadata.settings_manifest import (
    JobRegistryManifest,
    LineageRegistryManifest,
    MetricRegistryManifest,
    SchemaRegistryManifest,
    SecretRegistryManifest,
    TransactionRegistryManifest,
)
from tiozin.exceptions import SettingsNotFoundError
from tiozin.family.tio_kernel import FileSettingRegistry

MOCK_DIR = Path("tests/mocks/settings")


def manifest_mock(n: int = 1) -> SettingsManifest:
    return SettingsManifest(
        registries=dict(
            job=JobRegistryManifest(
                kind="FileJobRegistry",
                name=f"my-job-registry-{n}",
            ),
            schema=SchemaRegistryManifest(
                kind="NoOpSchemaRegistry",
                name=f"my-schema-registry-{n}",
            ),
            secret=SecretRegistryManifest(
                kind="NoOpSecretRegistry",
                name=f"my-secret-registry-{n}",
            ),
            transaction=TransactionRegistryManifest(
                kind="NoOpTransactionRegistry",
                name=f"my-transaction-registry-{n}",
            ),
            lineage=LineageRegistryManifest(
                kind="NoOpLineageRegistry",
                name=f"my-lineage-registry-{n}",
            ),
            metric=MetricRegistryManifest(
                kind="NoOpMetricRegistry",
                name=f"my-metric-registry-{n}",
            ),
        )
    )


# ============================================================================
# get()
# ============================================================================
def test_get_should_load_manifest_from_file():
    # Arrange
    registry = FileSettingRegistry(location=MOCK_DIR / "default.yaml")

    # Act
    result = registry.get()

    # Assert
    actual = result
    expected = manifest_mock(1)
    assert actual == expected


@patch.object(config, "tiozin_settings_search_paths", (MOCK_DIR / "default.yaml",))
def test_get_should_load_manifest_from_search_paths():
    # Arrange
    registry = FileSettingRegistry()
    registry.setup()

    # Act
    result = registry.get()

    # Assert
    actual = result
    expected = manifest_mock(1)
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
    with pytest.raises(ValueError, match="Unsupported settings format"):
        registry.register(str(tmp_path / "tiozin.toml"), manifest)
