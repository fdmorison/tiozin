import pytest

from tiozin.compose import JobProxy
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.family.tio_kernel import LinearJob, NoOpInput, NoOpRunner


def input():
    return NoOpInput(
        name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
    )


def test_proxy_should_forbid_setup_access():
    # Arrange
    job = LinearJob(
        name="test",
        org="acme",
        region="latam",
        domain="d",
        subdomain="d",
        layer="l",
        product="p",
        model="m",
        runner=NoOpRunner(name="runner"),
        inputs=[input()],
    )
    proxy = JobProxy(job)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.setup(None)


def test_proxy_should_forbid_teardown_access():
    # Arrange
    job = LinearJob(
        name="test",
        org="acme",
        region="latam",
        domain="d",
        subdomain="d",
        layer="l",
        product="p",
        model="m",
        runner=NoOpRunner(name="runner"),
        inputs=[input()],
    )
    proxy = JobProxy(job)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.teardown(None)
