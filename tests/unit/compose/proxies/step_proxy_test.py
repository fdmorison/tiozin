import pytest

from tiozin.compose import StepProxy
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.family.tio_kernel import NoOpInput, NoOpOutput, NoOpTransform


def input():
    return NoOpInput(
        name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
    )


def output():
    return NoOpOutput(
        name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
    )


def transform():
    return NoOpTransform(
        name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
    )


@pytest.mark.parametrize(
    "plugin",
    [input(), transform(), output()],
    ids=["Input", "Transform", "Output"],
)
def test_proxy_should_forbid_setup_access(plugin: NoOpInput | NoOpTransform | NoOpOutput):
    # Arrange
    proxy = StepProxy(plugin)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.setup(None)


@pytest.mark.parametrize(
    "plugin",
    [input(), transform(), output()],
    ids=["Input", "Transform", "Output"],
)
def test_proxy_should_forbid_teardown_access(plugin: NoOpInput | NoOpTransform | NoOpOutput):
    # Arrange
    proxy = StepProxy(plugin)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.teardown(None)
