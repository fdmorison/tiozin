from importlib.metadata import EntryPoint

import pytest

from tiozin.compose import PluginScanner
from tiozin.family import tio_kernel
from tiozin.family.tio_kernel import (
    FileJobRegistry,
    NoOpInput,
    NoOpOutput,
    NoOpRunner,
    NoOpTransform,
)


@pytest.fixture
def scanner():
    return PluginScanner()


# ============================================================================
# _scan_providers()
# ============================================================================
def test_scan_providers_should_find_providers(scanner: PluginScanner):
    # Arrange
    entrypoint = EntryPoint(
        name="tio_kernel",
        value="tiozin.family.tio_kernel",
        group="tiozin.family",
    )

    # Act
    providers = scanner._scan_providers()

    # Assert
    actual = providers
    expected = (entrypoint, tio_kernel)
    assert expected in actual


# ============================================================================
# _scan_plugins()
# ============================================================================
def test_scan_plugins_should_find_tio_kernel_plugins(scanner: PluginScanner):
    # Act
    plugins = scanner._scan_plugins(tio_kernel)

    # Assert
    actual = set(plugins)
    expected = {
        NoOpInput,
        NoOpOutput,
        NoOpTransform,
        NoOpRunner,
        FileJobRegistry,
    }
    assert expected.issubset(actual)


# ============================================================================
# scan()
# ============================================================================
def test_scan_should_return_plugins_grouped_by_provider(scanner: PluginScanner):
    # Act
    result = scanner.scan()

    # Assert
    actual = set(result.get("tio_kernel"))
    expected = {
        NoOpInput,
        NoOpOutput,
        NoOpTransform,
        NoOpRunner,
        FileJobRegistry,
    }
    assert expected.issubset(actual)
