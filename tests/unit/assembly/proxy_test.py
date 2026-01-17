import pytest
import wrapt

from tiozin.assembly.job_proxy import JobProxy
from tiozin.assembly.proxying import TIOPROXY, ProxyMeta, tioproxy
from tiozin.assembly.runner_proxy import RunnerProxy
from tiozin.assembly.step_proxy import StepProxy
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.family.tio_kernel import LinearJob, NoOpInput, NoOpOutput, NoOpRunner, NoOpTransform


class ParentProxy(wrapt.ObjectProxy):
    pass


class ChildProxy(wrapt.ObjectProxy):
    pass


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


# ============================================================================
# Testing StepProxy - Lifecycle Access Control
# ============================================================================
@pytest.mark.parametrize(
    "plugin",
    [input(), transform(), output()],
    ids=["Input", "Output", "Transform"],
)
def test_step_proxy_should_forbid_setup_access(plugin: NoOpInput | NoOpTransform | NoOpOutput):
    # Arrange
    proxy = StepProxy(plugin)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.setup(None)


@pytest.mark.parametrize(
    "plugin",
    [input(), transform(), output()],
    ids=["Input", "Output", "Transform"],
)
def test_step_proxy_should_forbid_teardown_access(plugin: NoOpInput | NoOpTransform | NoOpOutput):
    # Arrange
    proxy = StepProxy(plugin)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.teardown(None)


# ============================================================================
# Testing RunnerProxy - Lifecycle Access Control
# ============================================================================
def test_runner_proxy_should_forbid_setup_access():
    # Arrange
    runner = NoOpRunner(name="test")
    proxy = RunnerProxy(runner)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.setup(None)


def test_runner_proxy_should_forbid_teardown_access():
    # Arrange
    runner = NoOpRunner(name="test")
    proxy = RunnerProxy(runner)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.teardown(None)


# ============================================================================
# Testing JobProxy - Lifecycle Access Control
# ============================================================================
def test_job_proxy_should_forbid_setup_access():
    # Arrange
    job = LinearJob(
        name="test",
        org="acme",
        region="latam",
        domain="d",
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


def test_job_proxy_should_forbid_teardown_access():
    # Arrange
    job = LinearJob(
        name="test",
        org="acme",
        region="latam",
        domain="d",
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


# ============================================================================
# Testing tioproxy - Proxy List Isolation
# ============================================================================
def test_tioproxy_should_not_modify_parent_proxy_list_when_child_is_decorated():
    # Arrange
    @tioproxy(ParentProxy)
    class Parent(metaclass=ProxyMeta):
        pass

    parent_proxies = list(getattr(Parent, TIOPROXY, []))

    # Act
    @tioproxy(ChildProxy)
    class Child(Parent):
        pass

    # Assert
    expected = parent_proxies
    actual = getattr(Parent, TIOPROXY, [])
    assert actual == expected


def test_tioproxy_should_include_parent_proxies_when_child_is_decorated():
    # Arrange
    @tioproxy(ParentProxy)
    class Parent(metaclass=ProxyMeta):
        pass

    # Act
    @tioproxy(ChildProxy)
    class Child(Parent):
        pass

    # Assert
    actual = set(getattr(Child, TIOPROXY, []))
    expected = {ParentProxy, ChildProxy}
    assert actual == expected
