"""
Integration tests for PluginTemplateOverlay affecting setup and teardown in proxies.

This is a regression test for a bug where PluginTemplateOverlay was not
applied to setup and teardown methods in JobProxy and StepProxy.
"""

from tests.stubs.input import InputStub
from tests.stubs.job import JobStub
from tests.stubs.output import OutputStub
from tests.stubs.runner import RunnerStub
from tests.stubs.transform import StubTransform
from tiozin import Context


def test_job_lifecycle_methods_should_receive_rendered_templates(fake_taxonomy: dict):
    # Arrange
    job = JobStub(
        name="test",
        **fake_taxonomy,
        runner=RunnerStub(),
        inputs=[InputStub(name="test")],
    )

    # Act
    job.submit()

    # Assert
    actual = (
        job.captured_setup,
        job.captured_submit,
        job.captured_teardown,
    )
    expected = (
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
    )
    assert actual == expected


def test_runner_lifecycle_methods_should_receive_rendered_templates(job_context: Context):
    # Arrange
    runner = RunnerStub()

    # Act
    with runner(job_context):
        runner.run(job_context, execution_plan="SELECT 1")

    # Assert
    actual = (
        runner.captured_setup,
        runner.captured_run,
        runner.captured_teardown,
    )
    expected = (
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
    )
    assert actual == expected


def test_input_lifecycle_methods_should_receive_rendered_templates(
    fake_taxonomy: dict, job_context: Context
):
    # Arrange
    step = InputStub(name="test", **fake_taxonomy)

    # Act
    step.read(job_context)

    # Assert
    actual = (
        step.captured_setup,
        step.captured_read,
        step.captured_teardown,
    )
    expected = (
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
    )
    assert actual == expected


def test_transform_lifecycle_methods_should_receive_rendered_templates(
    fake_taxonomy: dict, job_context: Context
):
    # Arrange
    step = StubTransform(name="test", **fake_taxonomy)
    data = {}

    # Act
    step.transform(job_context, data)

    # Assert
    actual = (
        step.captured_setup,
        step.captured_transform,
        step.captured_teardown,
    )
    expected = (
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
    )
    assert actual == expected


def test_output_lifecycle_methods_should_receive_rendered_templates(
    fake_taxonomy: dict, job_context: Context
):
    # Arrange
    step = OutputStub(name="test", **fake_taxonomy)
    data = {}

    # Act
    step.write(job_context, data)

    # Assert
    actual = (
        step.captured_setup,
        step.captured_write,
        step.captured_teardown,
    )
    expected = (
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
        "./data/ecommerce/raw",
    )
    assert actual == expected
