from dataclasses import fields
from pathlib import Path
from unittest.mock import ANY

import pendulum
import pytest
from freezegun import freeze_time

from tests.stubs import InputStub, JobStub
from tiozin import Context
from tiozin.compose import TemplateDate

FAKE_UUID = "01968e6a-0000-7000-8000-000000000001"
FROZEN_TIME = "2026-06-15T12:00:00+00:00"
FROZEN_TIME_OBJ = pendulum.parse(FROZEN_TIME)


# =============================================================================
# Testing Factories
# =============================================================================


@freeze_time(FROZEN_TIME)
def test_for_job_should_create_job_context(
    job_stub: JobStub, fake_domain: dict, fake_governance: dict
):
    # Job
    job = job_stub

    # Act
    with Context.for_job(job_stub) as context:
        # Assert
        actual = {
            f.name: getattr(context, f.name) for f in fields(context) if not f.name.startswith("_")
        }
        expected = {
            # Root reference
            "job": context,
            # Identity
            "name": job.name,
            "slug": job.slug,
            "kind": job.kind,
            "tiozin_role": job.tiozin_role,
            # Domain / Governance
            **fake_domain,
            "namespace": "acme.latam.ecommerce.checkout",
            **fake_governance,
            # Tiozin arguments
            "options": job.options,
            # Runtime Identity
            "run_id": ANY,
            "run_attempt": 1,
            "nominal_time": FROZEN_TIME_OBJ,
            # Runtime Lifecycle
            "runner": job.runner,
            "setup_at": None,
            "executed_at": None,
            "teardown_at": None,
            "finished_at": None,
            # Metadata
            "registries": ANY,
            "output_schema": None,
            # Infra
            "catalog": ANY,
            "temp_workdir": Path(f"/tmp/tiozin/{job.slug}/{context.run_id}"),
            "template_vars": ANY,
            "shared": {},
        }
        assert actual == expected


@freeze_time(FROZEN_TIME)
def test_for_step_should_create_step_context(input_stub: InputStub, fake_domain: dict):
    # Arrange
    step = input_stub

    # Act
    context = Context.for_step(input_stub)

    # Assert
    actual = {
        f.name: getattr(context, f.name) for f in fields(context) if not f.name.startswith("_")
    }
    expected = {
        # Root reference
        "job": None,
        # Identity
        "name": step.name,
        "slug": step.slug,
        "kind": step.kind,
        "tiozin_role": step.tiozin_role,
        # Domain / Governance
        **fake_domain,
        "namespace": None,
        # Governance inheritance
        "maintainer": None,
        "cost_center": None,
        "owner": None,
        "labels": {},
        # Tiozin arguments
        "options": step.options,
        # Runtime Identity
        "run_id": ANY,
        "run_attempt": 1,
        "nominal_time": FROZEN_TIME_OBJ,
        # Runtime Lifecycle
        "runner": None,
        "setup_at": None,
        "executed_at": None,
        "teardown_at": None,
        "finished_at": None,
        # Metadata
        "registries": ANY,
        "output_schema": None,
        # Infra
        "catalog": ANY,
        "temp_workdir": Path(f"/tmp/tiozin/{step.slug}/{context.run_id}"),
        "template_vars": ANY,
        "shared": {},
    }
    assert actual == expected


def test_for_child_step_should_create_step_context_with_job_information(
    job_context: Context, input_stub: InputStub
):
    # Arrange
    step = input_stub

    # Act
    context = job_context.for_child_step(input_stub)

    # Assert
    actual = {
        f.name: getattr(context, f.name) for f in fields(context) if not f.name.startswith("_")
    }
    expected = {
        # Root reference
        "job": job_context,
        # Identity
        "name": step.name,
        "slug": step.slug,
        "kind": step.kind,
        "tiozin_role": step.tiozin_role,
        # Domain / Governance
        "org": job_context.org,
        "region": job_context.region,
        "domain": job_context.domain,
        "subdomain": job_context.subdomain,
        "layer": job_context.layer,
        "product": job_context.product,
        "model": job_context.model,
        "namespace": job_context.namespace,
        # Governance inheritance
        "maintainer": job_context.maintainer,
        "cost_center": job_context.cost_center,
        "owner": job_context.owner,
        "labels": job_context.labels,
        # Tiozin arguments
        "options": step.options,
        # Runtime Identity
        "run_id": ANY,
        "run_attempt": 1,
        "nominal_time": job_context.nominal_time,
        # Runtime Lifecycle
        "runner": job_context.runner,
        "setup_at": None,
        "executed_at": None,
        "teardown_at": None,
        "finished_at": None,
        # Metadata
        "registries": job_context.registries,
        "output_schema": None,
        # Infra
        "catalog": job_context.catalog,
        "temp_workdir": Path(f"/tmp/tiozin/{job_context.slug}/{job_context.run_id}/{step.slug}"),
        "template_vars": ANY,
        "shared": job_context.shared,
    }
    assert actual == expected


# =============================================================================
# Testing Context.qualified_slug
# =============================================================================


def test_qualified_slug_should_return_slug_when_context_is_root(job_context: Context):
    # Assert
    actual = job_context.qualified_slug
    expected = job_context.slug
    assert actual == expected


def test_qualified_slug_should_return_job_slug_and_step_slug_when_context_is_child(
    job_context: Context, input_context: Context
):
    # Assert
    actual = input_context.qualified_slug
    expected = f"{job_context.slug}.{input_context.slug}"
    assert actual == expected


# =============================================================================
# Testing Context - Lifecycle Delays
# =============================================================================


def test_context_should_calculate_lifecycle_delays(job_context: Context):
    # Arrange
    job_context.setup_at = pendulum.parse("2026-01-15T10:00:00+00:00")
    job_context.executed_at = pendulum.parse("2026-01-15T10:00:02+00:00")
    job_context.teardown_at = pendulum.parse("2026-01-15T10:00:10+00:00")
    job_context.finished_at = pendulum.parse("2026-01-15T10:00:11+00:00")

    # Act
    result = (
        job_context.delay,
        job_context.setup_delay,
        job_context.execution_delay,
        job_context.teardown_delay,
    )

    # Assert
    actual = result
    expected = (
        11.0,
        2.0,
        8.0,
        1.0,
    )
    assert actual == expected


# =============================================================================
# Testing Context._build_template_vars
# =============================================================================


def test_build_template_vars_should_exclude_fields_with_template_false(job_context: Context):
    # Act
    job_context._build_template_vars()

    # Assert
    excluded = {
        "runner",
        "registries",
        "schema",
        "shared",
        "template_vars",
        "setup_at",
        "executed_at",
        "teardown_at",
        "finished_at",
    }
    actual = excluded.intersection(job_context.template_vars.keys())
    expected = set()
    assert actual == expected


def test_build_template_vars_should_include_day(
    job_context: Context,
):
    # Act
    job_context._build_template_vars()

    # Assert
    actual = isinstance(job_context.template_vars["DAY"], TemplateDate)
    expected = True
    assert actual == expected


@freeze_time(FROZEN_TIME)
def test_build_template_vars_should_expose_day_values(
    job_context: Context,
):
    # Act
    job_context._build_template_vars()

    # Assert
    actual = {
        "ds": str(job_context.template_vars["ds"]),
        "iso": str(job_context.template_vars["iso"]),
        "YYYY": str(job_context.template_vars["YYYY"]),
        "MM": str(job_context.template_vars["MM"]),
        "DD": str(job_context.template_vars["DD"]),
    }
    expected = {
        "ds": FROZEN_TIME_OBJ.format("YYYY-MM-DD"),
        "iso": FROZEN_TIME_OBJ.format("YYYY-MM-DD[T]HH:mm:ssZ"),
        "YYYY": FROZEN_TIME_OBJ.format("YYYY"),
        "MM": FROZEN_TIME_OBJ.format("MM"),
        "DD": FROZEN_TIME_OBJ.format("DD"),
    }
    assert actual == expected


def test_build_template_vars_should_override_base_with_context_fields(job_context: Context):
    # Arrange
    base = {
        "name": "overridden_name",
        "custom_key": "custom_value",
    }

    # Act
    job_context._build_template_vars(base=base)

    # Assert
    actual = (
        job_context.template_vars["name"],
        job_context.template_vars["custom_key"],
    )
    expected = (
        job_context.name,
        "custom_value",
    )
    assert actual == expected


@freeze_time(FROZEN_TIME)
def test_build_template_vars_should_override_base_with_day(
    job_context: Context,
):
    # Arrange
    base = {
        "ds": "base_value",
        "YYYY": "9999",
    }

    # Act
    job_context._build_template_vars(base=base)

    # Assert
    actual = {
        "ds": str(job_context.template_vars["ds"]),
        "YYYY": str(job_context.template_vars["YYYY"]),
    }
    expected = {
        "ds": FROZEN_TIME_OBJ.format("YYYY-MM-DD"),
        "YYYY": FROZEN_TIME_OBJ.format("YYYY"),
    }
    assert actual == expected


def test_build_template_vars_should_store_immutable_result(job_context: Context):
    # Act
    job_context._build_template_vars()

    # Assert
    with pytest.raises(TypeError):
        job_context.template_vars["new_key"] = "value"


# =============================================================================
# Testing Context._build_template_vars - ENV Namespace
# =============================================================================


def test_build_template_vars_should_include_env_from_os(
    monkeypatch: pytest.MonkeyPatch,
    job_context: Context,
):
    # Arrange
    monkeypatch.setenv("TIOZIN_BUILD_TEST", "hello")

    # Act
    job_context._build_template_vars()

    # Assert
    actual = job_context.template_vars["ENV"]["TIOZIN_BUILD_TEST"]
    expected = "hello"
    assert actual == expected


def test_build_template_vars_should_isolate_env_from_context_fields(
    monkeypatch: pytest.MonkeyPatch,
    job_context: Context,
):
    # Arrange
    monkeypatch.setenv("name", "from_os")

    # Act
    job_context._build_template_vars()

    # Assert
    actual = (
        job_context.template_vars["name"],
        job_context.template_vars["ENV"]["name"],
    )
    expected = (
        job_context.name,
        "from_os",
    )
    assert actual == expected


# =============================================================================
# Testing Context.render
# =============================================================================


def test_render_should_resolve_context_variable_when_variable_is_in_template(job_context: Context):
    # Arrange
    template = "{{ name }}"

    # Act
    actual = job_context.render(template)

    # Assert
    expected = job_context.name
    assert actual == expected


# =============================================================================
# Testing Context.is_job / Context.is_step
# =============================================================================


def test_is_job_should_be_true_when_context_is_job(job_context: Context):
    # Act
    result = job_context.is_job

    # Assert
    actual = result
    expected = True
    assert actual == expected


@pytest.mark.parametrize(
    "context_name",
    ["input_context", "transform_context", "output_context"],
    ids=["Input", "Transform", "Output"],
)
def test_is_job_should_be_false_when_context_is_step(
    context_name: str, request: pytest.FixtureRequest
):
    # Arrange
    ctx: Context = request.getfixturevalue(context_name)

    # Act
    result = ctx.is_job

    # Assert
    actual = result
    expected = False
    assert actual == expected


@pytest.mark.parametrize(
    "context_name",
    ["input_context", "transform_context", "output_context"],
    ids=["Input", "Transform", "Output"],
)
def test_is_step_should_be_true_when_context_is_step(
    context_name: str, request: pytest.FixtureRequest
):
    # Arrange
    ctx: Context = request.getfixturevalue(context_name)

    # Act
    result = ctx.is_step

    # Assert
    actual = result
    expected = True
    assert actual == expected


def test_is_step_should_be_false_when_context_is_job(job_context: Context):
    # Act
    result = job_context.is_step

    # Assert
    actual = result
    expected = False
    assert actual == expected
