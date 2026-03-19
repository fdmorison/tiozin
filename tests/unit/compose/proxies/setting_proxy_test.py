from pathlib import Path

import pytest

from tiozin.api import SettingsManifest
from tiozin.api.metadata.settings_manifest import (
    JobRegistryManifest,
    LineageRegistryManifest,
    MetricRegistryManifest,
    SchemaRegistryManifest,
    SecretRegistryManifest,
    TransactionRegistryManifest,
)
from tiozin.exceptions import TiozinInternalError
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
# SettingRegistryProxy - delegation
# ============================================================================
def test_setup_should_resolve_delegation_to_target():
    # Arrange
    registry = FileSettingRegistry(location=MOCK_DIR / "delegate_to_default.yaml")

    # Act
    registry.setup()

    # Assert
    actual = registry.get().model_dump()
    expected = manifest_mock(1).model_dump()
    assert actual == expected


@pytest.mark.parametrize(
    "tiozin_yaml",
    [
        "delegate_1.yaml",
        "delegate_2.yaml",
        "delegate_3.yaml",
    ],
)
def test_setup_should_resolve_multiple_delegation_hops(tiozin_yaml: str):
    # Arrange
    registry = FileSettingRegistry(location=MOCK_DIR / tiozin_yaml)

    # Act
    registry.setup()

    # Assert
    actual = (
        registry.kind,
        registry.name,
    )
    expected = (
        "NoOpSettingRegistry",
        "my-job-registry-3",
    )
    assert actual == expected


@pytest.mark.parametrize(
    "tiozin_yaml",
    [
        "delegate_to_location_empty.yaml",
        "delegate_to_location_missing.yaml",
        "delegate_to_location_null.yaml",
    ],
)
def test_setup_should_fail_when_declared_registry_has_no_location(tiozin_yaml: str):
    # Arrange
    registry = FileSettingRegistry(location=MOCK_DIR / tiozin_yaml)

    # Act / Assert
    with pytest.raises(TiozinInternalError):
        registry.setup()


def test_setup_should_fail_on_circular_reference():
    # Arrange
    registry = FileSettingRegistry(location=MOCK_DIR / "delegate_circular.yaml")

    # Act / Assert
    with pytest.raises(TiozinInternalError, match="Circular settings delegation"):
        registry.setup()
