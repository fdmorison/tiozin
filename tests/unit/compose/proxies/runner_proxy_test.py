import pytest

from tiozin.compose import RunnerProxy
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.family.tio_kernel import NoOpRunner


def test_proxy_should_forbid_setup_access():
    # Arrange
    runner = NoOpRunner(name="test")
    proxy = RunnerProxy(runner)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.setup(None)


def test_proxy_should_forbid_teardown_access():
    # Arrange
    runner = NoOpRunner(name="test")
    proxy = RunnerProxy(runner)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.teardown(None)
