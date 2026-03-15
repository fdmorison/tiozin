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
    registry = registry_class()

    # Assert
    actual = registry.location
    expected = registry.tiozin_uri
    assert actual == expected


@pytest.mark.parametrize("registry_class", NOOP_REGISTRY_CLASSES)
def test_noop_registry_should_use_provided_location_when_given(registry_class: type[Registry]):
    # Arrange / Act
    registry = registry_class(location="custom://location")

    # Assert
    actual = registry.location
    expected = "custom://location"
    assert actual == expected


# ============================================================================
# get()
# ============================================================================
@pytest.mark.parametrize("registry_class", NOOP_REGISTRY_CLASSES)
def test_noop_registry_should_return_none_on_get(registry_class: type[Registry]):
    # Arrange
    registry = registry_class()

    # Act
    result = registry.get()

    # Assert
    actual = result
    expected = None
    assert actual == expected
