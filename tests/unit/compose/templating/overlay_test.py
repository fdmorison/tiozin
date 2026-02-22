import copy
import logging
from datetime import datetime

import pytest

from tests.stubs import InputStub, JobStub, OutputStub, RunnerStub, TransformStub
from tiozin import Context
from tiozin.compose import TiozinTemplateOverlay
from tiozin.exceptions import TiozinInputError
from tiozin.family.tio_kernel import NoOpInput


# ============================================================================
# Testing TiozinTemplateOverlay - Basic Functionality
# ============================================================================
def test_overlay_should_render_and_restore_single_template(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain}}"

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/ecommerce",
        "./data/{{domain}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_multiple_templates(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain}}/{{layer}}"
    tiozin.name = "{{product}}_output"

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = (tiozin.path, tiozin.name)
    restored = (tiozin.path, tiozin.name)

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            "./data/ecommerce/raw",
            "sales_output",
        ),
        (
            "./data/{{domain}}/{{layer}}",
            "{{product}}_output",
        ),
    )
    assert actual == expected


def test_overlay_should_not_modify_non_template_strings(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/sales"
    tiozin.name = "output"

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
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


def test_overlay_should_not_modify_private_attributes(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin._private = "{{domain}}"

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
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


def test_overlay_should_render_and_restore_nested_dict_templates(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.config = {"path": "./data/{{domain}}", "region": "{{region}}"}

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = dict(tiozin.config)
    restored = tiozin.config

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        {
            "path": "./data/ecommerce",
            "region": "latam",
        },
        {
            "path": "./data/{{domain}}",
            "region": "{{region}}",
        },
    )
    assert actual == expected


def test_overlay_should_render_and_restore_nested_list_templates(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.paths = [
        "./{{layer}}/data",
        "./output/{{domain}}",
    ]

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = list(tiozin.paths)
    restored = tiozin.paths

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        [
            "./raw/data",
            "./output/ecommerce",
        ],
        [
            "./{{layer}}/data",
            "./output/{{domain}}",
        ],
    )
    assert actual == expected


def test_overlay_should_render_and_restore_nested_tiozins(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.inner = NoOpInput(name="inner")
    tiozin.inner.path = "{{domain}}/inner"

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = tiozin.inner.path
    restored = tiozin.inner.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "ecommerce/inner",
        "{{domain}}/inner",
    )
    assert actual == expected


def test_overlay_should_restore_on_exception(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.name = "{{domain}}"

    # Act
    try:
        with TiozinTemplateOverlay(tiozin, fake_domain):
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
        "ecommerce",
        "{{domain}}",
    )
    assert actual == expected


def test_overlay_should_raise_error_on_missing_variable(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{missing}}"

    # Act & Assert
    with pytest.raises(TiozinInputError):
        with TiozinTemplateOverlay(tiozin, fake_domain):
            pass


def test_overlay_should_render_and_restore_templates_with_multiple_variables(
    fake_domain: dict,
):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain}}/{{layer}}/{{product}}/file.txt"

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/ecommerce/raw/sales/file.txt",
        "./data/{{domain}}/{{layer}}/{{product}}/file.txt",
    )
    assert actual == expected


def test_overlay_should_not_modify_strings_when_no_template_vars():
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/static"

    # Act
    with TiozinTemplateOverlay(tiozin):
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


def test_overlay_should_render_and_restore_deeply_nested_structures(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.config = {
        "level1": {
            "level2": ["./{{domain}}", "./{{layer}}"],
        }
    }

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
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
                "level2": ["./ecommerce", "./raw"],
            }
        },
        {
            "level1": {
                "level2": ["./{{domain}}", "./{{layer}}"],
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

    # Act
    with TiozinTemplateOverlay(tiozin):
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


def test_overlay_should_not_modify_immutable_tuple_with_templates(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.paths = (
        "./{{layer}}/data",
        "./output/{{domain}}",
    )

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = tiozin.paths
    restored = tiozin.paths

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            "./{{layer}}/data",
            "./output/{{domain}}",
        ),
        (
            "./{{layer}}/data",
            "./output/{{domain}}",
        ),
    )
    assert actual == expected


def test_overlay_should_not_modify_immutable_frozenset_with_templates(fake_domain: dict):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.tags = frozenset(["{{layer}}", "{{domain}}"])

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = tiozin.tags
    restored = tiozin.tags

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        frozenset(["{{layer}}", "{{domain}}"]),
        frozenset(["{{layer}}", "{{domain}}"]),
    )
    assert actual == expected


def test_overlay_should_render_and_restore_mutable_objects_inside_immutable_tuple(
    fake_domain: dict,
):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.data = (
        {"path": "./data/{{domain}}"},
        ["./{{layer}}/data", "./output/{{region}}"],
        "static_value",
    )

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = copy.deepcopy(tiozin.data)
    restored = tiozin.data

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            {"path": "./data/ecommerce"},
            ["./raw/data", "./output/latam"],
            "static_value",
        ),
        (
            {"path": "./data/{{domain}}"},
            ["./{{layer}}/data", "./output/{{region}}"],
            "static_value",
        ),
    )
    assert actual == expected


def test_overlay_should_restore_templates_after_each_sequential_overlay(
    fake_domain: dict,
):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain}}"
    other_domain = {**fake_domain, "domain": "finance"}

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered_1 = tiozin.path

    with TiozinTemplateOverlay(tiozin, other_domain):
        rendered_2 = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered_1,
        rendered_2,
        restored,
    )
    expected = (
        "./data/ecommerce",
        "./data/finance",
        "./data/{{domain}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_templates_with_jinja2_filters(
    fake_domain: dict,
):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{domain|upper}}"

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/ECOMMERCE",
        "./data/{{domain|upper}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_templates_with_jinja2_expressions(
    fake_domain: dict,
):
    # Arrange
    tiozin = NoOpInput(name="test")
    tiozin.path = "./data/{{ domain ~ '/' ~ layer }}"

    # Act
    with TiozinTemplateOverlay(tiozin, fake_domain):
        rendered = tiozin.path
    restored = tiozin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/ecommerce/raw",
        "./data/{{ domain ~ '/' ~ layer }}",
    )
    assert actual == expected


# ============================================================================
# Testing TiozinTemplateOverlay - rendering across all execution phases.
# ============================================================================


def test_overlay_should_render_job_templates_across_all_phases(fake_domain: dict):
    # Arrange
    job = JobStub(
        name="test",
        **fake_domain,
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
    with job_context, runner():
        runner.run(execution_plan="SELECT 1")

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


def test_overlay_should_render_input_templates_across_all_phases(fake_domain: dict):
    # Arrange
    step = InputStub(name="test", **fake_domain)

    # Act
    step.read()

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


def test_overlay_should_render_transform_templates_across_all_phases(fake_domain: dict):
    # Arrange
    step = TransformStub(name="test", **fake_domain)
    data = {}

    # Act
    step.transform(data)

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


def test_overlay_should_render_output_templates_across_all_phases(fake_domain: dict):
    # Arrange
    step = OutputStub(name="test", **fake_domain)
    data = {}

    # Act
    step.write(data)

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
