import pytest

from tiozin import Registry
from tiozin.family.tio_kernel import (
    NoOpLineageRegistry,
    NoOpMetricRegistry,
    NoOpSchemaRegistry,
    NoOpSecretRegistry,
    NoOpSettingRegistry,
    NoOpTransactionRegistry,
)

NOOP_REGISTRY_CLASSES = [
    NoOpSettingRegistry,
    NoOpLineageRegistry,
    NoOpMetricRegistry,
    NoOpSchemaRegistry,
    NoOpSecretRegistry,
    NoOpTransactionRegistry,
]


# ============================================================================
# location
# ============================================================================
@pytest.mark.parametrize("registry_class", NOOP_REGISTRY_CLASSES)
def test_noop_registry_should_use_tiozin_uri_as_location_when_none_provided(
    registry_class: type[Registry],
):
    # Arrange / Act
    registry = registry_class().__wrapped__

    # Assert
    actual = registry.location
    expected = registry.tiozin_uri
    assert actual == expected


@pytest.mark.parametrize("registry_class", NOOP_REGISTRY_CLASSES)
def test_noop_registry_should_use_provided_location_when_given(registry_class: type[Registry]):
    # Arrange / Act
    registry = registry_class(location="custom://location").__wrapped__

    # Assert
    actual = registry.location
    expected = "custom://location"
    assert actual == expected


# ============================================================================
# get()
# ============================================================================
def test_noop_schema_registry_should_return_none_on_get():
    # Arrange
    registry = NoOpSchemaRegistry().__wrapped__.__wrapped__

    # Act
    result = registry.get("acme.eu.sales.orders.raw.crm.order")

    # Assert
    actual = result
    expected = None
    assert actual == expected


def test_noop_setting_registry_should_return_empty_manifest_on_get():
    from tiozin.api import SettingsManifest

    # Arrange
    registry = NoOpSettingRegistry().__wrapped__

    # Act
    result = registry.get()

    # Assert
    actual = isinstance(result, SettingsManifest)
    expected = True
    assert actual == expected
