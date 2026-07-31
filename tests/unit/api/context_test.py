from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import ANY

import pendulum
import pytest
from freezegun import freeze_time

from tests.stubs import BatchRegistryStub, InputStub, JobStub, RunnerStub
from tiozin import Batch, Context
from tiozin.api import BacklogPolicy, Cadence
from tiozin.compose import TemplateDate

FAKE_UUID = "01968e6a-0000-7000-8000-000000000001"
FROZEN_TIME = "2026-06-15T12:00:00+00:00"
FROZEN_TIME_OBJ = pendulum.parse(FROZEN_TIME)

_2026_01_15T01_00_00 = datetime(2026, 1, 15, 1, tzinfo=UTC)
_2026_01_15T07_00_00 = datetime(2026, 1, 15, 7, tzinfo=UTC)
_2026_01_15T09_00_00 = datetime(2026, 1, 15, 9, tzinfo=UTC)


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
        actual = {name: getattr(context, name) for name in Context.model_fields}
        expected = {
            # Root reference
            "job": context,
            # Identity
            "name": job.name,
            "display_name": job.display_name,
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
            "cadence": job.cadence,
            "backlog_policy": job.backlog_policy,
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
            "temp_workdir": Path(f"/tmp/tiozin/{job.name}/{context.run_id}"),
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
    actual = {name: getattr(context, name) for name in Context.model_fields}
    expected = {
        # Root reference
        "job": None,
        # Identity
        "name": step.name,
        "display_name": step.display_name,
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
        "cadence": Cadence.MINUTELY,
        "backlog_policy": BacklogPolicy.STATELESS,
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
        "temp_workdir": Path(f"/tmp/tiozin/{step.name}/{context.run_id}"),
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
    actual = {name: getattr(context, name) for name in Context.model_fields}
    expected = {
        # Root reference
        "job": job_context,
        # Identity
        "name": step.name,
        "display_name": step.display_name,
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
        "cadence": job_context.cadence,
        "backlog_policy": job_context.backlog_policy,
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
        "temp_workdir": Path(f"/tmp/tiozin/{job_context.name}/{job_context.run_id}/{step.name}"),
        "template_vars": ANY,
        "shared": job_context.shared,
    }
    assert actual == expected


def test_for_job_should_keep_the_original_job_name_as_display_name(job_stub: JobStub):
    # Arrange
    job_stub.display_name = "My Test Job"

    # Act
    result = Context.for_job(job_stub)

    # Assert
    actual = (
        result.display_name,
        result.name,
    )
    expected = (
        "My Test Job",
        "test_job",
    )
    assert actual == expected


# =============================================================================
# Testing Context.for_job - nominal time truncation
# =============================================================================


@freeze_time("2026-06-15T12:30:45.123456+00:00")
def test_for_job_should_truncate_nominal_time_to_current_minute_by_default(job_stub: JobStub):
    # Act
    result = Context.for_job(job_stub)

    # Assert
    actual = result.nominal_time
    expected = pendulum.parse("2026-06-15T12:30:00+00:00")
    assert actual == expected


@freeze_time("2026-06-15T12:30:45.123456+00:00")
def test_for_job_should_truncate_nominal_time_to_cadence_slot(
    fake_domain: dict,
    fake_governance: dict,
    runner_stub: RunnerStub,
    input_stub: InputStub,
):
    # Arrange
    job = JobStub(
        name="test_job",
        cadence=Cadence.DAILY,
        runner=runner_stub,
        inputs=[input_stub],
        **fake_domain,
        **fake_governance,
    )

    # Act
    result = Context.for_job(job)

    # Assert
    actual = result.nominal_time
    expected = pendulum.parse("2026-06-15T00:00:00+00:00")
    assert actual == expected


# =============================================================================
# Testing Context.qualified_name
# =============================================================================


def test_qualified_name_should_return_name_when_context_is_root(job_context: Context):
    # Assert
    actual = job_context.qualified_name
    expected = "test_job"
    assert actual == expected


def test_qualified_name_should_join_job_and_step_names_when_context_is_child(
    input_context: Context,
):
    # Assert
    actual = input_context.qualified_name
    expected = "test_job.test_input"
    assert actual == expected


# =============================================================================
# Testing Context.qualified_slug
# =============================================================================


def test_qualified_slug_should_return_name_when_context_is_root(job_context: Context):
    # Assert
    actual = job_context.qualified_slug
    expected = "test_job"
    assert actual == expected


def test_qualified_slug_should_join_job_and_step_names_when_context_is_child(
    input_context: Context,
):
    # Assert
    actual = input_context.qualified_slug
    expected = "test_job_test_input"
    assert actual == expected


# =============================================================================
# Testing Context.get_job_backlog
# =============================================================================


def test_get_job_backlog_should_load_backlog_from_batch_registry(
    job_context: Context, batch_registry_stub: BatchRegistryStub, fake_domain: dict
):
    # Arrange
    backlog = [
        Batch(**fake_domain, nominal_time=_2026_01_15T01_00_00),
    ]
    batch_registry_stub.backlog = backlog

    # Act
    result = job_context.get_job_backlog()

    # Assert
    actual = result
    expected = backlog
    assert actual == expected


def test_get_job_backlog_should_return_cached_backlog_without_querying_the_registry(
    job_context: Context, batch_registry_stub: BatchRegistryStub, fake_domain: dict
):
    # Arrange
    backlog = [
        Batch(**fake_domain, nominal_time=_2026_01_15T01_00_00),
    ]
    batch_registry_stub.backlog = backlog
    cached = [
        Batch(**fake_domain, nominal_time=_2026_01_15T09_00_00),
    ]
    job_context.catalog.register(job_context.job, backlog=cached)

    # Act
    result = job_context.get_job_backlog()

    # Assert
    actual = result
    expected = cached
    assert actual == expected


def test_get_job_backlog_should_return_the_job_backlog_from_a_step_context(
    job_context: Context, input_context: Context, fake_domain: dict
):
    # Arrange
    backlog = [Batch(**fake_domain, nominal_time=_2026_01_15T07_00_00)]
    job_context.catalog.register(job_context.job, backlog=backlog)

    # Act
    result = input_context.get_job_backlog()

    # Assert
    actual = result
    expected = backlog
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
# Testing Context._init_template_vars
# =============================================================================


def test_init_template_vars_should_exclude_fields_with_skip_template(job_context: Context):
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


def test_init_template_vars_should_include_day(job_context: Context):
    # Assert
    actual = isinstance(job_context.template_vars["DAY"], TemplateDate)
    expected = True
    assert actual == expected


@freeze_time(FROZEN_TIME)
def test_init_template_vars_should_expose_day_values(fake_domain: dict):
    # Act
    result = Context(
        name="test_job",
        display_name="test_job",
        kind="job",
        tiozin_role="Job",
        **fake_domain,
    )

    # Assert
    actual = {
        "ds": str(result.template_vars["ds"]),
        "iso": str(result.template_vars["iso"]),
        "YYYY": str(result.template_vars["YYYY"]),
        "MM": str(result.template_vars["MM"]),
        "DD": str(result.template_vars["DD"]),
    }
    expected = {
        "ds": FROZEN_TIME_OBJ.format("YYYY-MM-DD"),
        "iso": FROZEN_TIME_OBJ.format("YYYY-MM-DD[T]HH:mm:ssZ"),
        "YYYY": FROZEN_TIME_OBJ.format("YYYY"),
        "MM": FROZEN_TIME_OBJ.format("MM"),
        "DD": FROZEN_TIME_OBJ.format("DD"),
    }
    assert actual == expected


def test_init_template_vars_should_override_base_with_context_fields(fake_domain: dict):
    # Arrange
    base = {
        "name": "overridden_name",
        "custom_key": "custom_value",
    }

    # Act
    result = Context(
        name="test_job",
        display_name="test_job",
        kind="job",
        tiozin_role="Job",
        template_vars=base,
        **fake_domain,
    )

    # Assert
    actual = (
        result.template_vars["name"],
        result.template_vars["custom_key"],
    )
    expected = (
        "test_job",
        "custom_value",
    )
    assert actual == expected


@freeze_time(FROZEN_TIME)
def test_init_template_vars_should_override_base_with_day(fake_domain: dict):
    # Arrange
    base = {
        "ds": "base_value",
        "YYYY": "9999",
    }

    # Act
    result = Context(
        name="test_job",
        display_name="test_job",
        kind="job",
        tiozin_role="Job",
        template_vars=base,
        **fake_domain,
    )

    # Assert
    actual = {
        "ds": str(result.template_vars["ds"]),
        "YYYY": str(result.template_vars["YYYY"]),
    }
    expected = {
        "ds": FROZEN_TIME_OBJ.format("YYYY-MM-DD"),
        "YYYY": FROZEN_TIME_OBJ.format("YYYY"),
    }
    assert actual == expected


def test_init_template_vars_should_store_immutable_result(job_context: Context):
    # Assert
    with pytest.raises(TypeError):
        job_context.template_vars["new_key"] = "value"


# =============================================================================
# Testing Context._init_template_vars - ENV Namespace
# =============================================================================


def test_init_template_vars_should_include_env_from_os(
    monkeypatch: pytest.MonkeyPatch,
    job_context: Context,
):
    # Arrange
    monkeypatch.setenv("TIOZIN_BUILD_TEST", "hello")

    # Assert
    actual = job_context.template_vars["ENV"]["TIOZIN_BUILD_TEST"]
    expected = "hello"
    assert actual == expected


def test_init_template_vars_should_isolate_env_from_context_fields(
    monkeypatch: pytest.MonkeyPatch,
    job_context: Context,
):
    # Arrange
    monkeypatch.setenv("name", "from_os")

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
