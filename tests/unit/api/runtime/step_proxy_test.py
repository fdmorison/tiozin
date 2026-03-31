from unittest.mock import MagicMock

import pytest

from tests.stubs import InputStub, JobStub
from tiozin.api.context import Context
from tiozin.api.metadata.bundle import Registries
from tiozin.api.runtime.step_proxy import StepProxy
from tiozin.exceptions import AccessViolationError
from tiozin.family.tio_kernel import NoOpInput, NoOpOutput, NoOpTransform


def input():
    return NoOpInput(
        name="test",
        org="acme",
        region="latam",
        domain="d",
        layer="l",
        product="p",
        model="m",
    )


def output():
    return NoOpOutput(
        name="test",
        org="acme",
        region="latam",
        domain="d",
        layer="l",
        product="p",
        model="m",
    )


def transform():
    return NoOpTransform(
        name="test",
        org="acme",
        region="latam",
        domain="d",
        layer="l",
        product="p",
        model="m",
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
# Testing StepProxy.read — schema
# =============================================================================


def test_read_should_fetch_schema_from_registry(job_stub: JobStub, fake_domain: dict):
    # Arrange
    schema_registry = MagicMock()
    step = InputStub(
        name="orders",
        schema_subject="acme.orders",
        schema_version="v1",
        **fake_domain,
    )

    # Act
    with Context.for_job(job_stub, Registries(schema=schema_registry)):
        step.read()

    # Assert
    schema_registry.try_get.assert_called_with("acme.orders", "v1")


# =============================================================================
# Testing StepProxy — static_datasets template rendering
# =============================================================================


def test_proxy_should_render_template_vars_in_static_datasets_when_step_inherits_job_context(
    job_context: Context,
):
    """
    Verifies that path templates in static_datasets() are rendered using the active
    job context when the step does not define domain or layer itself.
    """
    step = InputStub(name="orders_input", domain=None, layer=None)

    # Act
    step.read()

    # Assert
    inputs = job_context.catalog.get_input_datasets([step])
    actual = (inputs[0].namespace, inputs[0].name)
    expected = ("file", "data/ecommerce/raw")
    assert actual == expected


def test_proxy_should_render_template_vars_in_static_datasets_using_step_own_vars(
    job_context: Context,
):
    """
    Verifies that when a step defines its own domain and layer, those values take
    precedence over the job context when rendering path templates in static_datasets().
    """
    step = InputStub(name="orders_input", domain="finance", layer="trusted")

    # Act
    step.read()

    # Assert
    inputs = job_context.catalog.get_input_datasets([step])
    actual = (inputs[0].namespace, inputs[0].name)
    expected = ("file", "data/finance/trusted")
    assert actual == expected
