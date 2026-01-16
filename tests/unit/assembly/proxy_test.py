import pytest

from tiozin.assembly.job_proxy import JobProxy
from tiozin.assembly.runner_proxy import RunnerProxy
from tiozin.assembly.step_proxy import StepProxy
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.family.tio_kernel import LinearJob, NoOpInput, NoOpOutput, NoOpRunner, NoOpTransform


# ============================================================================
# Testing StepProxy - Lifecycle Access Control
# ============================================================================
@pytest.mark.parametrize(
    "plugin",
    [
        NoOpInput(
            name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
        ),
        NoOpOutput(
            name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
        ),
        NoOpTransform(
            name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
        ),
    ],
    ids=["Input", "Output", "Transform"],
)
def test_step_proxy_should_block_direct_setup_access(plugin):
    # Arrange
    proxy = StepProxy(plugin)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.setup(None)


@pytest.mark.parametrize(
    "plugin",
    [
        NoOpInput(
            name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
        ),
        NoOpOutput(
            name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
        ),
        NoOpTransform(
            name="test", org="acme", region="latam", domain="d", layer="l", product="p", model="m"
        ),
    ],
    ids=["Input", "Output", "Transform"],
)
def test_step_proxy_should_block_direct_teardown_access(plugin):
    # Arrange
    proxy = StepProxy(plugin)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.teardown(None)


# ============================================================================
# Testing RunnerProxy - Lifecycle Access Control
# ============================================================================
def test_runner_proxy_should_block_direct_setup_access():
    # Arrange
    runner = NoOpRunner(name="test")
    proxy = RunnerProxy(runner)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.setup(None)


def test_runner_proxy_should_block_direct_teardown_access():
    # Arrange
    runner = NoOpRunner(name="test")
    proxy = RunnerProxy(runner)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.teardown(None)


# ============================================================================
# Testing JobProxy - Lifecycle Access Control
# ============================================================================
def test_job_proxy_should_block_direct_setup_access():
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
        inputs=[
            NoOpInput(
                name="input",
                org="acme",
                region="latam",
                domain="d",
                layer="l",
                product="p",
                model="m",
            )
        ],
    )
    proxy = JobProxy(job)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.setup(None)


def test_job_proxy_should_block_direct_teardown_access():
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
        inputs=[
            NoOpInput(
                name="input",
                org="acme",
                region="latam",
                domain="d",
                layer="l",
                product="p",
                model="m",
            )
        ],
    )
    proxy = JobProxy(job)

    # Act/Assert
    with pytest.raises(PluginAccessForbiddenError):
        proxy.teardown(None)
