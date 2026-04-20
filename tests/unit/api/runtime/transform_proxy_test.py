from unittest.mock import MagicMock

import pytest

from tests.stubs import JobStub, TransformStub
from tiozin import Dataset
from tiozin.api.context import Context
from tiozin.api.metadata.bundle import Registries
from tiozin.api.runtime.transform_proxy import TransformProxy
from tiozin.exceptions import AccessViolationError


def test_proxy_should_forbid_setup_and_teardown_access():
    # Arrange
    # Arrange
    step = TransformStub(name="orders").__wrapped__
    proxy = TransformProxy(step)

    # Act/Assert
    with pytest.raises(AccessViolationError):
        proxy.setup()

    with pytest.raises(AccessViolationError):
        proxy.teardown()


def test_transform_should_return_dataset(job_context: Context):
    # Arrange
    step = TransformStub(name="orders").__wrapped__
    proxy = TransformProxy(step)
    data = Dataset("SELECT 1")

    # Act
    result = proxy.transform(data)

    # Assert
    assert isinstance(result, Dataset)


def test_transform_should_fetch_schema_from_registry(job_stub: JobStub, fake_domain: dict):
    # Arrange
    schema_registry = MagicMock()
    schema_registry.get.return_value = None
    step = TransformStub(
        name="orders",
        schema_subject="acme.orders",
        schema_version="v1",
        **fake_domain,
    )
    data = Dataset("SELECT 1")

    # Act
    with Context.for_job(job_stub, Registries(schema=schema_registry)):
        step.transform(data)

    # Assert
    schema_registry.get.assert_called_with("acme.orders", "v1")


def test_proxy_should_render_templates_at_external_datasets_with_job_attributes(
    job_context: Context,
):
    """
    Verifies that path templates in external_datasets() are rendered using the active
    job context when the step does not define domain or layer itself.
    """
    step = TransformStub(name="orders", domain=None, layer=None)
    data = Dataset("SELECT 1")

    # Act
    step.transform(data)

    # Assert
    inputs = job_context.catalog.get_inputs(step)
    actual = (
        inputs[0].tiozin_namespace,
        inputs[0].tiozin_name,
    )
    expected = (
        "file",
        "data/ecommerce/raw",
    )
    assert actual == expected


def test_proxy_should_render_templates_at_external_datasets_with_step_attributes(
    job_context: Context,
):
    """
    Verifies that when a step defines its own domain and layer, those values take
    precedence over the job context when rendering path templates in external_datasets().
    """
    step = TransformStub(name="orders", domain="finance", layer="trusted")
    data = Dataset("SELECT 1")

    # Act
    step.transform(data)

    # Assert
    inputs = job_context.catalog.get_inputs(step)
    actual = (
        inputs[0].tiozin_namespace,
        inputs[0].tiozin_name,
    )
    expected = (
        "file",
        "data/finance/trusted",
    )
    assert actual == expected
