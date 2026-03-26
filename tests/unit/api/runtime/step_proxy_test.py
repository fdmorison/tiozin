import pytest

from tests.stubs import InputStub
from tiozin.api.context import Context
from tiozin.api.runtime.step_proxy import StepProxy
from tiozin.exceptions import AccessViolationError
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
    "tiozin",
    [input(), transform(), output()],
    ids=["Input", "Transform", "Output"],
)
def test_proxy_should_forbid_setup_access(tiozin: NoOpInput | NoOpTransform | NoOpOutput):
    # Arrange
    proxy = StepProxy(tiozin)

    # Act/Assert
    with pytest.raises(AccessViolationError):
        proxy.setup(None)


@pytest.mark.parametrize(
    "tiozin",
    [input(), transform(), output()],
    ids=["Input", "Transform", "Output"],
)
def test_proxy_should_forbid_teardown_access(tiozin: NoOpInput | NoOpTransform | NoOpOutput):
    # Arrange
    proxy = StepProxy(tiozin)

    # Act/Assert
    with pytest.raises(AccessViolationError):
        proxy.teardown(None)


# =============================================================================
# Testing StepProxy.lineage_datasets — template rendering uses step context, not job's
# =============================================================================


def test_proxy_should_render_lineage_templates_when_step_inherits_job_context(
    job_context: Context,
):
    """
    Tests a scenario where a step does not define `domain` or `layer` and relies on
    an active job context. The goal is to verify that the step inherits these values
    from the job and uses them to correctly render lineage templates.

    The `job_context` fixture activates a job with `domain="ecommerce"` and
    `layer="raw"`, so the step's path template is resolved using those values.
    """
    step = InputStub(name="orders_input", domain=None, layer=None)

    # Act
    result = step.lineage_datasets()

    # Assert
    actual = (
        result.inputs[0].namespace,
        result.inputs[0].name,
    )
    expected = (
        "file",
        "./data/ecommerce/raw",
    )
    assert actual == expected


def test_proxy_should_render_lineage_templates_using_step_template_vars(
    job_context: Context,
):
    """
    Tests a scenario where a step explicitly defines `domain` and `layer` that
    differ from the active job context. The goal is to verify that the step's
    own values take precedence over the inherited job values when rendering
    lineage templates.

    The `job_context` fixture activates a job with `domain="ecommerce"` and
    `layer="raw"`, but the step overrides both with `domain="finance"` and
    `layer="trusted"`.
    """
    step = StepProxy(InputStub(name="orders_input", domain="finance", layer="trusted"))

    # Act
    result = step.lineage_datasets()

    # Assert
    actual = (
        result.inputs[0].namespace,
        result.inputs[0].name,
    )
    expected = (
        "file",
        "./data/finance/trusted",
    )
    assert actual == expected
