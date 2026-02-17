import copy
import logging
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from tests.stubs.input import InputStub
from tests.stubs.job import JobStub
from tests.stubs.output import OutputStub
from tests.stubs.runner import RunnerStub
from tests.stubs.transform import StubTransform
from tiozin import Context
from tiozin.compose import TiozinTemplateOverlay
from tiozin.exceptions import InvalidInputError
from tiozin.family.tio_kernel import NoOpInput


# ============================================================================
# Testing TiozinTemplateOverlay - Basic Functionality
# ============================================================================
def test_overlay_should_render_and_restore_single_template():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain}}"
    context = MagicMock(template_vars={"domain": "sales"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/sales",
        "./data/{{domain}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_multiple_templates():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain}}/{{date}}"
    tiozin.name = "{{prefix}}_output"
    context = MagicMock(template_vars={"domain": "sales", "date": "2024-01-15", "prefix": "test"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = (tiozin.path, tiozin.name)
    restored = (tiozin.path, tiozin.name)

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            "./data/sales/2024-01-15",
            "test_output",
        ),
        (
            "./data/{{domain}}/{{date}}",
            "{{prefix}}_output",
        ),
    )
    assert actual == expected


def test_overlay_should_not_modify_non_template_strings():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/sales"
    tiozin.name = "output"
    context = MagicMock(template_vars={"domain": "sales"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = (tiozin.path, tiozin.name)
    restored = (tiozin.path, tiozin.name)

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            "./data/sales",
            "output",
        ),
        (
            "./data/sales",
            "output",
        ),
    )
    assert actual == expected


def test_overlay_should_not_modify_private_attributes():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin._private = "{{domain}}"
    context = MagicMock(template_vars={"domain": "sales"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin._private
    restored = tiozin._private

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "{{domain}}",
        "{{domain}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_nested_dict_templates():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.config = {"path": "./data/{{domain}}", "region": "{{region}}"}
    context = MagicMock(template_vars={"domain": "sales", "region": "us-east"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = dict(tiozin.config)
    restored = tiozin.config

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        {
            "path": "./data/sales",
            "region": "us-east",
        },
        {
            "path": "./data/{{domain}}",
            "region": "{{region}}",
        },
    )
    assert actual == expected


def test_overlay_should_render_and_restore_nested_list_templates():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.paths = [
        "./{{env}}/data",
        "./output/{{domain}}",
    ]
    context = MagicMock(template_vars={"env": "prod", "domain": "sales"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = list(tiozin.paths)
    restored = tiozin.paths

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        [
            "./prod/data",
            "./output/sales",
        ],
        [
            "./{{env}}/data",
            "./output/{{domain}}",
        ],
    )
    assert actual == expected


def test_overlay_should_render_and_restore_nested_tiozins():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.inner = NoOpInput(name="inner")
    tiozin.inner.path = "{{domain}}/inner"
    context = MagicMock(template_vars={"domain": "sales"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin.inner.path
    restored = tiozin.inner.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "sales/inner",
        "{{domain}}/inner",
    )
    assert actual == expected


def test_overlay_should_restore_on_exception():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.name = "{{value}}"
    context = MagicMock(template_vars={"value": "resolved"})

    # Act
    try:
        with TiozinTemplateOverlay(tiozin, context):
            rendered = tiozin.name
            raise ValueError("Simulated error")
    except ValueError:
        pass
    restored = tiozin.name

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "resolved",
        "{{value}}",
    )
    assert actual == expected


def test_overlay_should_raise_error_on_missing_variable():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{missing}}"
    context = MagicMock(template_vars={"other": "value"})

    # Act & Assert
    with pytest.raises(InvalidInputError):
        with TiozinTemplateOverlay(tiozin, context):
            pass


def test_overlay_should_render_and_restore_templates_with_multiple_variables():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain}}/{{year}}-{{month}}-{{day}}/file.txt"
    context = MagicMock(
        template_vars={"domain": "sales", "year": "2024", "month": "01", "day": "15"}
    )

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/sales/2024-01-15/file.txt",
        "./data/{{domain}}/{{year}}-{{month}}-{{day}}/file.txt",
    )
    assert actual == expected


def test_overlay_should_not_modify_strings_when_context_is_empty():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/static"
    context = MagicMock()

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/static",
        "./data/static",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_deeply_nested_structures():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.config = {
        "level1": {
            "level2": ["./{{a}}", "./{{b}}"],
        }
    }
    context = MagicMock(template_vars={"a": "foo", "b": "bar"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = copy.deepcopy(tiozin.config)
    restored = tiozin.config

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        {
            "level1": {
                "level2": ["./foo", "./bar"],
            }
        },
        {
            "level1": {
                "level2": ["./{{a}}", "./{{b}}"],
            }
        },
    )
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    [42, True, False, 3.14, None, datetime.now(), logging.getLogger("test")],
)
def test_overlay_should_not_modify_non_string_values(value):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.value = value
    context = MagicMock()

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin.value
    restored = tiozin.value

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        value,
        value,
    )
    assert actual == expected


def test_overlay_should_not_modify_immutable_tuple_with_templates():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.paths = (
        "./{{env}}/data",
        "./output/{{domain}}",
    )
    context = MagicMock(template_vars={"env": "prod", "domain": "sales"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin.paths
    restored = tiozin.paths

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            "./{{env}}/data",
            "./output/{{domain}}",
        ),
        (
            "./{{env}}/data",
            "./output/{{domain}}",
        ),
    )
    assert actual == expected


def test_overlay_should_not_modify_immutable_frozenset_with_templates():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.tags = frozenset(["{{env}}", "{{domain}}"])
    context = MagicMock(template_vars={"env": "prod", "domain": "sales"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin.tags
    restored = tiozin.tags

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        frozenset(["{{env}}", "{{domain}}"]),
        frozenset(["{{env}}", "{{domain}}"]),
    )
    assert actual == expected


def test_overlay_should_render_and_restore_mutable_objects_inside_immutable_tuple():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.data = (
        {"path": "./data/{{domain}}"},
        ["./{{env}}/data", "./output/{{region}}"],
        "static_value",
    )
    context = MagicMock(template_vars={"domain": "sales", "env": "prod", "region": "us-east"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = copy.deepcopy(tiozin.data)
    restored = tiozin.data

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            {"path": "./data/sales"},
            ["./prod/data", "./output/us-east"],
            "static_value",
        ),
        (
            {"path": "./data/{{domain}}"},
            ["./{{env}}/data", "./output/{{region}}"],
            "static_value",
        ),
    )
    assert actual == expected


def test_overlay_should_restore_templates_after_each_sequential_overlay():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain}}"

    # Act
    with TiozinTemplateOverlay(tiozin, MagicMock(template_vars={"domain": "sales"})):
        rendered_1 = tiozin.path

    with TiozinTemplateOverlay(tiozin, MagicMock(template_vars={"domain": "finance"})):
        rendered_2 = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered_1,
        rendered_2,
        restored,
    )
    expected = (
        "./data/sales",
        "./data/finance",
        "./data/{{domain}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_templates_with_jinja2_filters():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain|upper}}"
    context = MagicMock(template_vars={"domain": "sales"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/SALES",
        "./data/{{domain|upper}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_templates_with_jinja2_expressions():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{ domain ~ '/' ~ date }}"
    context = MagicMock(template_vars={"domain": "sales", "date": "2024-01-15"})

    # Act
    with TiozinTemplateOverlay(tiozin, context):
        rendered = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/sales/2024-01-15",
        "./data/{{ domain ~ '/' ~ date }}",
    )
    assert actual == expected


# ============================================================================
# Testing TiozinTemplateOverlay - rendering across all execution phases.
# ============================================================================


def test_overlay_should_render_job_templates_across_all_phases(fake_taxonomy: dict):
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


def test_overlay_should_render_runner_templates_across_all_phases(job_context: Context):
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


def test_overlay_should_render_input_templates_across_all_phases(
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


def test_overlay_should_render_transform_templates_across_all_phases(
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


def test_overlay_should_render_output_templates_across_all_phases(
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
